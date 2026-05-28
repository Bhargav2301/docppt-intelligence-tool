import logging
import math
from typing import Dict, Any

from runtime.fallback import safe_perplexity

logger = logging.getLogger(__name__)

def calculate_similarity(source_text: str, generated_text: str) -> float:
    """
    Computes cosine similarity between source and generated text using the embedding model.
    Returns 0.0 since embedding model is unavailable.
    """
    return 0.0

@safe_perplexity
def calculate_perplexity(text: str) -> Dict[str, Any]:
    """
    Computes the perplexity of the generated text. Always returns fallback as the model is removed.
    """
    return {"perplexity": None, "fallback": True}

