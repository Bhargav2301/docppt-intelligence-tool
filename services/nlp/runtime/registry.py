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
    def _is_extractive_mode(cls) -> bool:
        return MODEL_MODE == "extractive_only"

    @classmethod
    def get_summarization_pipeline(cls):
        if cls._is_extractive_mode():
            return None
            
        cache_key = f"summarization_{SUMMARIZATION_MODEL}"
        if cache_key not in cls._cache:
            logger.info(f"Loading summarization model: {SUMMARIZATION_MODEL}")
            from transformers import pipeline
            # Fallback to CPU by default or specific local GPU settings
            device = -1 if MODEL_MODE == "local_cpu" else 0
            cls._cache[cache_key] = pipeline("summarization", model=SUMMARIZATION_MODEL, device=device)
        return cls._cache[cache_key]

    @classmethod
    def get_embedding_model(cls):
        if cls._is_extractive_mode():
            return None
            
        cache_key = f"embedding_{EMBEDDING_MODEL}"
        if cache_key not in cls._cache:
            logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
            from sentence_transformers import SentenceTransformer
            device = "cpu" if MODEL_MODE == "local_cpu" else "cuda"
            cls._cache[cache_key] = SentenceTransformer(EMBEDDING_MODEL, device=device)
        return cls._cache[cache_key]

    @classmethod
    def get_instruction_model(cls):
        if cls._is_extractive_mode():
            return None
            
        cache_key = f"instruction_{INSTRUCTION_MODEL}"
        if cache_key not in cls._cache:
            logger.info(f"Loading instruction model: {INSTRUCTION_MODEL}")
            from transformers import pipeline
            device = -1 if MODEL_MODE == "local_cpu" else 0
            cls._cache[cache_key] = pipeline("text2text-generation", model=INSTRUCTION_MODEL, device=device)
        return cls._cache[cache_key]

    @classmethod
    def get_perplexity_model(cls):
        if cls._is_extractive_mode():
            return None
            
        cache_key = f"perplexity_{PERPLEXITY_MODEL}"
        if cache_key not in cls._cache:
            logger.info(f"Loading perplexity model: {PERPLEXITY_MODEL}")
            from transformers import AutoModelForCausalLM, AutoTokenizer
            device = "cpu" if MODEL_MODE == "local_cpu" else "cuda"
            tokenizer = AutoTokenizer.from_pretrained(PERPLEXITY_MODEL)
            model = AutoModelForCausalLM.from_pretrained(PERPLEXITY_MODEL).to(device)
            cls._cache[cache_key] = (tokenizer, model)
        return cls._cache[cache_key]

    @classmethod
    def get_loaded_models_status(cls):
        return {
            "mode": MODEL_MODE,
            "loaded_models": list(cls._cache.keys())
        }

# Global registry instance
registry = ModelRegistry()
