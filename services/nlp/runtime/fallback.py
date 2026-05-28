import logging
from functools import wraps

from .config import MODEL_MODE, EXTRACTIVE_SUMMARY_SENTENCE_COUNT

logger = logging.getLogger(__name__)

def generate_extractive_summary(text: str, sentence_count: int = EXTRACTIVE_SUMMARY_SENTENCE_COUNT) -> str:
    """Fallback extractive summarizer. Simply returns a sliced version of the text since nltk/sumy are removed."""
    return text[:500] + "..." if len(text) > 500 else text

def with_summarization_fallback(func):
    """
    Decorator to wrap summarization calls. If generative models fail or are disabled,
    it falls back to the extractive summarizer.
    """
    @wraps(func)
    def wrapper(text, *args, **kwargs):
        if MODEL_MODE == "extractive_only":
            logger.info("MODEL_MODE is extractive_only. Skipping generative model.")
            return generate_extractive_summary(text)
            
        try:
            return func(text, *args, **kwargs)
        except Exception as e:
            logger.warning(f"Generative summarization failed: {str(e)}. Falling back to extractive.")
            return generate_extractive_summary(text)
            
    return wrapper

def safe_perplexity(func):
    """
    Decorator to wrap perplexity calculations.
    Returns a neutral score if the model fails.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if MODEL_MODE == "extractive_only":
            return {"perplexity": None, "fallback": True}
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Perplexity calculation failed: {str(e)}")
            return {"perplexity": None, "fallback": True}
            
    return wrapper
