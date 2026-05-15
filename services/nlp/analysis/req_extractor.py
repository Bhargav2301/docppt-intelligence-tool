import re
import spacy
import logging
from typing import List, Dict, Any
from runtime.registry import registry
from runtime.config import MODEL_MODE

logger = logging.getLogger(__name__)

# Fallback spaCy loading logic
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("spacy en_core_web_sm not found, downloading...")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def extract_requirements(text: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extracts and classifies requirements from document text.
    If MODEL_MODE permits, uses a local generative model to classify requirements and priority.
    Otherwise, uses spaCy and keyword heuristics.
    """
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.split()) > 4]

    requirements = {
        "functional": [],
        "technical": [],
        "ui_ux": [],
        "integrations": [],
        "data": [],
        "security_privacy": [],
        "non_functional": []
    }

    use_generative = MODEL_MODE != "extractive_only"
    instruction_model = registry.get_instruction_model() if use_generative else None

    req_id_counter = 1

    for sentence in sentences:
        is_req = False
        priority = "P2"
        category = "functional"

        if use_generative and instruction_model:
            try:
                # Ask the model if it's a requirement
                prompt_is_req = f"Is this a product requirement? Answer yes or no: {sentence}"
                res = instruction_model(prompt_is_req, max_new_tokens=3)[0]['generated_text'].strip().lower()
                is_req = "yes" in res

                if is_req:
                    prompt_priority = f"Classify the priority of this requirement as P0, P1, or P2: {sentence}"
                    res_pri = instruction_model(prompt_priority, max_new_tokens=5)[0]['generated_text'].strip().upper()
                    if "P0" in res_pri: priority = "P0"
                    elif "P1" in res_pri: priority = "P1"
            except Exception as e:
                logger.warning(f"Generative classification failed for sentence, falling back: {str(e)}")
                is_req, priority, category = _heuristic_classification(sentence)
        else:
            is_req, priority, category = _heuristic_classification(sentence)

        if is_req:
            req_obj = {
                "id": f"REQ-{req_id_counter:03d}",
                "requirement": sentence,
                "priority": priority,
                "confidence": 0.85 if (use_generative and instruction_model) else 0.60
            }
            requirements[category].append(req_obj)
            req_id_counter += 1

    return requirements

def _heuristic_classification(sentence: str):
    """Fallback logic using regex/keywords to classify requirements."""
    modal_verbs = ["must", "shall", "will", "should", "needs to", "required"]
    lower_sent = sentence.lower()
    
    is_req = any(verb in lower_sent for verb in modal_verbs)
    priority = "P2"
    category = "functional"
    
    if "must" in lower_sent or "shall" in lower_sent or "critical" in lower_sent:
        priority = "P0"
    elif "should" in lower_sent:
        priority = "P1"
        
    if "api" in lower_sent or "database" in lower_sent or "server" in lower_sent:
        category = "technical"
    elif "ui" in lower_sent or "screen" in lower_sent or "button" in lower_sent or "user" in lower_sent:
        category = "ui_ux"
    elif "integrate" in lower_sent or "third-party" in lower_sent:
        category = "integrations"
        
    return is_req, priority, category
