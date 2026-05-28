import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ModelRegistry:
    """
    Registry for models. Restructured to only support gemini_byok and avoid importing heavy ML libraries.
    """
    _cache: Dict[str, Any] = {}

    @classmethod
    def _get_active_mode(cls) -> str:
        return "gemini_byok"

    @classmethod
    def get_summarization_pipeline(cls):
        return None

    @classmethod
    def get_embedding_model(cls):
        return None

    @classmethod
    def get_instruction_model(cls):
        return None

    @classmethod
    def get_perplexity_model(cls):
        return None

    @classmethod
    def get_loaded_models_status(cls):
        return {
            "mode": "gemini_byok",
            "loaded_models": []
        }

    @classmethod
    def call_user_hosted_endpoint(cls, endpoint: str, model_name: str, prompt: str) -> str:
        raise NotImplementedError("User hosted endpoints are disabled. Only gemini_byok is allowed.")

# Global registry instance
registry = ModelRegistry()

