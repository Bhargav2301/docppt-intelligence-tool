import logging
import torch
import math
from typing import Dict, Any
from sklearn.metrics.pairwise import cosine_similarity

from runtime.registry import registry
from runtime.fallback import safe_perplexity

logger = logging.getLogger(__name__)

def calculate_similarity(source_text: str, generated_text: str) -> float:
    """
    Computes cosine similarity between source and generated text using the embedding model.
    Returns 0.0 if the embedding model is unavailable (e.g. in extractive_only mode).
    """
    if not source_text or not generated_text:
        return 0.0

    embedder = registry.get_embedding_model()
    if not embedder:
        logger.info("Embedding model not available. Returning default similarity.")
        return 0.0

    try:
        embeddings = embedder.encode([source_text, generated_text])
        sim_matrix = cosine_similarity([embeddings[0]], [embeddings[1]])
        return float(sim_matrix[0][0])
    except Exception as e:
        logger.error(f"Error computing similarity: {str(e)}")
        return 0.0

@safe_perplexity
def calculate_perplexity(text: str) -> Dict[str, Any]:
    """
    Computes the perplexity of the generated text to measure fluency/readability.
    """
    if not text.strip():
        return {"perplexity": None, "fallback": False}

    model_tuple = registry.get_perplexity_model()
    if not model_tuple:
        return {"perplexity": None, "fallback": True}

    tokenizer, model = model_tuple
    
    # Tokenize input
    encodings = tokenizer(text, return_tensors="pt")
    
    # Handle potentially long sequences by truncating to model max length
    max_length = model.config.n_positions
    input_ids = encodings.input_ids[:, :max_length]
    
    # If using GPU, move tensors
    device = next(model.parameters()).device
    input_ids = input_ids.to(device)

    target_ids = input_ids.clone()

    with torch.no_grad():
        outputs = model(input_ids, labels=target_ids)
        neg_log_likelihood = outputs.loss
        
    try:
        ppl = math.exp(neg_log_likelihood.item())
        return {"perplexity": float(ppl), "fallback": False}
    except OverflowError:
        return {"perplexity": float('inf'), "fallback": False}
