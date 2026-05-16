import logging
from typing import Optional
from runtime.registry import registry
from runtime.config import MODEL_MODE

logger = logging.getLogger(__name__)

def generate_rewrite(text: str, tone: str = "professional") -> Optional[str]:
    """
    Rewrites the input text using the configured instruction model.
    Returns None if the generation fails or if running in extractive_only mode.
    """
    if not text.strip():
        return None
        
    if MODEL_MODE == "extractive_only":
        logger.info("Skipping rewrite generation because MODEL_MODE is extractive_only.")
        return None
        
    instruction_model = registry.get_instruction_model()
    if not instruction_model:
        logger.warning("Instruction model not available for rewrite.")
        return None
        
    try:
        # Construct the prompt
        prompt = f"Rewrite the following text to be more {tone} and clear, but keep the original meaning: {text}"
        
        # Max new tokens roughly scales with input text size to allow for slight expansion
        input_words = len(text.split())
        max_tokens = max(50, int(input_words * 2))
        
        result = instruction_model(prompt, max_new_tokens=max_tokens, do_sample=True, temperature=0.7)
        rewritten = result[0]['generated_text'].strip()
        
        return rewritten
    except Exception as e:
        logger.error(f"Failed to generate rewrite: {str(e)}")
        return None
