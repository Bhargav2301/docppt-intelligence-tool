import logging
import math
from typing import Dict, Any

from runtime.fallback import safe_perplexity

logger = logging.getLogger(__name__)

import difflib

def calculate_similarity(source_text: str, generated_text: str) -> float:
    """
    Computes sequence similarity between source and generated text using difflib.SequenceMatcher.
    """
    if not source_text and not generated_text:
        return 1.0
    if not source_text or not generated_text:
        return 0.0
    s1 = source_text.strip()
    s2 = generated_text.strip()
    if s1 == s2:
        return 1.0
    return difflib.SequenceMatcher(None, s1, s2).ratio()

@safe_perplexity
def calculate_perplexity(text: str) -> Dict[str, Any]:
    """
    Computes the perplexity of the generated text. Always returns fallback as the model is removed.
    """
    return {"perplexity": None, "fallback": True}

