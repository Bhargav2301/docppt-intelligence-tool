import re
from typing import Any, Dict, List
from .editorial_rules import apply_all_editorial_rules, BRITISH_TO_AMERICAN, _EMOJI_PATTERN
from analysis.evaluator import calculate_similarity

# Hallucination threshold
SIMILARITY_THRESHOLD = 0.65

def _get_entities(text: str) -> set:
    """Helper to extract named entities (capitalized words that are not the first word of a sentence)."""
    sentences = re.split(r'[.!?]+', text)
    entities = set()
    for sent in sentences:
        sent_words = re.findall(r'\b[A-Z][a-zA-Z0-9]*\b', sent.strip())
        if len(sent_words) > 1:
            # Exclude the first capitalized word in the sentence (as it could just be capitalized by grammar rules)
            entities.update(w.lower() for w in sent_words[1:])
    return entities

def _has_british_spelling(text: str) -> bool:
    """Helper to detect if text contains any British English spelling keys."""
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    for word in words:
        if word in BRITISH_TO_AMERICAN:
            return True
    return False

def judge_candidates(
    candidates: List[Dict[str, Any]],
    original_text: str,
    constraints: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Selects the best candidate rewrite.
    
    Returns:
        Dict: {
            'selected_text': str,
            'decision': 'accepted' | 'manual_review',
            'change_notes': List[str],
            'safety': 'safe_replace' | 'needs_shorter_option' | 'manual_review'
        }
    """
    max_chars = constraints.get("max_chars", 0)
    slide_role = constraints.get("slide_role", "body")
    
    # Extract original numbers & entities for strict comparison
    original_numbers = set(re.findall(r'\d+', original_text))
    original_entities = _get_entities(original_text)
    
    scored_candidates = []
    
    for cand in candidates:
        text = cand["text"]
        
        # 1. Length constraint check
        if max_chars > 0 and len(text) > max_chars:
            continue
            
        # 2. Minimum length check (to avoid trivial/empty rewrites)
        if not text or len(text.split()) < 2:
            continue
            
        # 3. Emojis check: Reject if candidate contains any emojis
        if _EMOJI_PATTERN.search(text):
            continue
            
        # 4. British spelling check: Reject if candidate contains any British spellings
        if _has_british_spelling(text):
            continue
            
        # 5. Number preservation check: Reject if numbers were modified, added, or deleted
        candidate_numbers = set(re.findall(r'\d+', text))
        if original_numbers != candidate_numbers:
            continue
            
        # 6. Entity preservation check: Reject if new named entities/facts were introduced
        candidate_entities = _get_entities(text)
        new_entities = candidate_entities - original_entities
        if new_entities:
            continue
            
        # 7. Semantic similarity check
        similarity = calculate_similarity(original_text, text)
        if similarity > 0.0 and similarity < SIMILARITY_THRESHOLD:
            # Reject if similarity is too low (high risk of semantic drift/hallucination)
            continue
            
        # Helper score: favor candidates with negative likeness delta (more human)
        likeness_delta = cand.get("estimated_ai_likeness_delta", 0.0)
        
        # Score computation:
        # - Penalty for excessive length changes (too long or too short)
        len_ratio = len(text) / max(len(original_text), 1)
        length_penalty = abs(1.0 - len_ratio) * 0.1
        
        score = 1.0 - likeness_delta - length_penalty
        
        scored_candidates.append({
            "candidate": cand,
            "score": score,
            "similarity": similarity
        })
        
    # Sort candidates by score descending
    scored_candidates.sort(key=lambda x: x["score"], reverse=True)
    
    if not scored_candidates:
        # Fallback if all candidates are invalid or rejected
        return {
            "selected_text": apply_all_editorial_rules(original_text),
            "decision": "manual_review",
            "change_notes": ["All generated rewrite options were rejected by constraints."],
            "safety": "manual_review"
        }
        
    best = scored_candidates[0]["candidate"]
    
    # Check safety level
    safety = "safe_replace"
    decision = "accepted"
    
    # If the text is still relatively long for a title or bullet, mark as needs_shorter_option
    if slide_role == "title" and len(best["text"]) > 80:
        safety = "needs_shorter_option"
        decision = "manual_review"
    elif slide_role == "bullet" and len(best["text"]) > 120:
        safety = "needs_shorter_option"
        decision = "manual_review"
        
    return {
        "selected_text": best["text"],
        "decision": decision,
        "change_notes": [best.get("notes", "Rewritten for clarity")],
        "safety": safety
    }
