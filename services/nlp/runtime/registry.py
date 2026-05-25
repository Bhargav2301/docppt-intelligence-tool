import logging
from typing import Dict, Any

from .config import MODEL_MODE, SUMMARIZATION_MODEL, INSTRUCTION_MODEL, EMBEDDING_MODEL, PERPLEXITY_MODEL

logger = logging.getLogger(__name__)

class ModelRegistry:
    """
    Lazy loader for heavy ML models.
    """
    _cache: Dict[str, Any] = {}

    @classmethod
    def _get_active_mode(cls) -> str:
        import os
        env = os.getenv("ENV", "development")
        if env in ("local_dev", "development"):
            try:
                from database import SessionLocal
                from models import User, UserSettings
                db = SessionLocal()
                try:
                    user = db.query(User).filter(User.email == "local_user@example.com").first()
                    if user:
                        settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
                        if settings and settings.model_mode:
                            return settings.model_mode
                except Exception:
                    pass
                finally:
                    db.close()
            except Exception:
                pass
        return MODEL_MODE

    @classmethod
    def _get_device_for_pipeline(cls, mode: str) -> int:
        try:
            import torch
            if mode == "local_gpu" and torch.cuda.is_available():
                return 0
        except Exception:
            pass
        return -1

    @classmethod
    def _get_device_for_sentence_transformer(cls, mode: str) -> str:
        try:
            import torch
            if mode == "local_gpu" and torch.cuda.is_available():
                return "cuda"
        except Exception:
            pass
        return "cpu"

    @classmethod
    def get_summarization_pipeline(cls):
        cache_key = f"summarization_{SUMMARIZATION_MODEL}"
        if cache_key not in cls._cache:
            logger.info(f"Loading summarization model: {SUMMARIZATION_MODEL}")
            from transformers import pipeline
            mode = cls._get_active_mode()
            device = cls._get_device_for_pipeline(mode)
            cls._cache[cache_key] = pipeline("summarization", model=SUMMARIZATION_MODEL, device=device)
        return cls._cache[cache_key]

    @classmethod
    def get_embedding_model(cls):
        cache_key = f"embedding_{EMBEDDING_MODEL}"
        if cache_key not in cls._cache:
            logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
            from sentence_transformers import SentenceTransformer
            mode = cls._get_active_mode()
            device = cls._get_device_for_sentence_transformer(mode)
            cls._cache[cache_key] = SentenceTransformer(EMBEDDING_MODEL, device=device)
        return cls._cache[cache_key]

    @classmethod
    def get_instruction_model(cls):
        cache_key = f"instruction_{INSTRUCTION_MODEL}"
        if cache_key not in cls._cache:
            logger.info(f"Loading instruction model: {INSTRUCTION_MODEL}")
            from transformers import pipeline
            mode = cls._get_active_mode()
            device = cls._get_device_for_pipeline(mode)
            cls._cache[cache_key] = pipeline("text2text-generation", model=INSTRUCTION_MODEL, device=device)
        return cls._cache[cache_key]

    @classmethod
    def get_perplexity_model(cls):
        cache_key = f"perplexity_{PERPLEXITY_MODEL}"
        if cache_key not in cls._cache:
            logger.info(f"Loading perplexity model: {PERPLEXITY_MODEL}")
            from transformers import AutoModelForCausalLM, AutoTokenizer
            mode = cls._get_active_mode()
            device = cls._get_device_for_sentence_transformer(mode)
            tokenizer = AutoTokenizer.from_pretrained(PERPLEXITY_MODEL)
            model = AutoModelForCausalLM.from_pretrained(PERPLEXITY_MODEL).to(device)
            cls._cache[cache_key] = (tokenizer, model)
        return cls._cache[cache_key]

    @classmethod
    def get_loaded_models_status(cls):
        return {
            "mode": cls._get_active_mode(),
            "loaded_models": list(cls._cache.keys())
        }


    @classmethod
    def call_user_hosted_endpoint(cls, endpoint: str, model_name: str, prompt: str) -> str:
        """
        Sends a completion request to a user-hosted OpenAI-compatible chat API (e.g. Ollama, vLLM, LocalAI).
        """
        import json
        import urllib.request
        from urllib.error import URLError

        # Construct endpoint URL
        url = endpoint.rstrip("/")
        if not url.endswith("/chat/completions"):
            url = f"{url}/chat/completions"

        # Payload
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "You are a professional corporate content writer and presentation specialist. Keep sentences concise, clear, and direct. Retain the original meaning perfectly."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }

        logger.info(f"Posting completion request to user endpoint: {url} (model: {model_name})")
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=12) as response:
                res_body = json.loads(response.read().decode("utf-8"))
                content = res_body["choices"][0]["message"]["content"].strip()
                return content
        except Exception as e:
            logger.error(f"Failed calling user hosted endpoint at {url}: {str(e)}")
            raise e

# Global registry instance
registry = ModelRegistry()
