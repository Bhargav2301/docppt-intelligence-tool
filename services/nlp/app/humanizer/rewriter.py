"""Candidate rewrite generation.

Generates candidate rewrites using Gemini LLM (when API key is available)
or rule-based fallback transforms.
"""

import json
import logging
import re
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional
from .editorial_rules import apply_all_editorial_rules, BRITISH_TO_AMERICAN

logger = logging.getLogger(__name__)

TONE_PRESETS: Dict[str, str] = {
    "presentation_concise": "Highly concise, punchy, bulleted presentation format. Focus on key metrics and action points. Strip filler words and narrative prose.",
    "executive_polished": "Executive-level communication: polished, outcome-driven, highlighting high-level strategic and financial results. Avoid operational weeds or excessive jargon.",
    "founder_clear": "Founder tone: clear, modern, passionate but direct. Focused on the vision, product value proposition, and user benefit. Avoid legacy corporate jargon.",
    "product_manager_direct": "Product Manager style: direct, feature-impact oriented, data-driven, and highly user-centric. Connect features to specific user value.",
    "consulting_professional": "Consulting style: structured, precise, objective, operational, formal. Focus on business processes, control points, data consistency, and professional business metrics.",
}

def generate_candidates(
    text: str,
    rewrite_plan: Dict[str, Any],
    tone_preset: str = "consulting_professional",
    gemini_api_key: Optional[str] = None,
    model_mode: str = "local_cpu",
    model_name: Optional[str] = None,
    endpoint: Optional[str] = None,
    intensity: str = "balanced"
) -> List[Dict[str, Any]]:
    """
    Generates a list of candidate rewrites based on the plan and tone.
    
    Each candidate is a dict:
        {'text': str, 'notes': str, 'estimated_ai_likeness_delta': float}
    """
    action = rewrite_plan.get("action", "pass_through")
    constraints = rewrite_plan.get("constraints", {})
    slide_role = constraints.get("slide_role", "body")
    max_chars = constraints.get("max_chars", 0)
    
    # Clean mechanical artifacts if action is pass_through or remove_mechanical_artifacts strategy is set
    cleaned_text = text
    from app.detector.rules import detect_artifacts, clean_text_by_rules
    art_res = detect_artifacts(text)
    if action == "pass_through" or any(s == "remove_mechanical_artifacts" for s in rewrite_plan.get("strategy", [])):
        cleaned_text = clean_text_by_rules(text, art_res.artifact_flags)
        
    # Apply editorial rules to base text
    base_cleaned = apply_all_editorial_rules(cleaned_text)
    
    if action == "pass_through":
        return [{
            "text": base_cleaned,
            "notes": "Passed through and cleaned via editorial rules.",
            "estimated_ai_likeness_delta": 0.0
        }]
        
    candidates = []
    
    # 1. Attempt Gemini BYOK rewrite if API key is provided or model_mode is gemini_byok
    if gemini_api_key or model_mode == "gemini_byok":
        llm_candidates = _generate_llm_candidates(text, tone_preset, slide_role, max_chars, gemini_api_key or "", intensity=intensity)
        if llm_candidates:
            for cand in llm_candidates:
                cand_text = apply_all_editorial_rules(cand.get("text", ""))
                if cand_text:
                    candidates.append({
                        "text": cand_text,
                        "notes": cand.get("notes", "Generative rewrite"),
                        "estimated_ai_likeness_delta": -0.3
                    })
    # 2. Attempt other LLM candidate generation modes (managed_endpoint, user_hosted_endpoint, local CPU/GPU)
    else:
        llm_candidates = _generate_other_llm_candidates(text, tone_preset, slide_role, max_chars, model_mode, model_name, endpoint, intensity=intensity)
        if llm_candidates:
            for cand in llm_candidates:
                cand_text = apply_all_editorial_rules(cand.get("text", ""))
                if cand_text:
                    candidates.append({
                        "text": cand_text,
                        "notes": cand.get("notes", "Generative rewrite"),
                        "estimated_ai_likeness_delta": cand.get("estimated_ai_likeness_delta", -0.2)
                    })
                    
    # 3. Fallback to Rule-Based transforms if no LLM candidates were successfully generated
    if not candidates:
        logger.info("Using rule-based candidate rewrite fallback.")
        candidates = _generate_rule_based_candidates(text, base_cleaned, slide_role, max_chars)
        
    # Deduplicate candidates by text
    seen = set()
    unique_candidates = []
    for cand in candidates:
        norm_t = cand["text"].strip().lower()
        if norm_t not in seen:
            seen.add(norm_t)
            unique_candidates.append(cand)
            
    # Always ensure at least one candidate
    if not unique_candidates:
        unique_candidates.append({
            "text": base_cleaned,
            "notes": "Editorial rules baseline.",
            "estimated_ai_likeness_delta": -0.05
        })
        
    return unique_candidates

def _generate_other_llm_candidates(
    text: str,
    tone: str,
    slide_role: str,
    max_chars: int,
    model_mode: str,
    model_name: Optional[str],
    endpoint: Optional[str],
    intensity: str = "balanced"
) -> Optional[List[Dict[str, Any]]]:
    """Generates rewrite candidates using non-Gemini instruction models or endpoints."""
    from runtime.registry import registry
    tone_desc = TONE_PRESETS.get(tone, TONE_PRESETS["consulting_professional"])
    
    intensity_instruction = ""
    if intensity == "strong":
        intensity_instruction = (
            "CRITICAL: Aggressively compress the text. Remove all sloganized contrasts (e.g. 'not just X, but Y'), "
            "generic certainty, abstract absolutes, rhythm-heavy triads (e.g. three parallel phrases or sentences), and unsupported outcome claims. "
            "Rewrite them into factual, specific, high-density, professional business/consultant statements. "
            "Remove all marketing/hype language and replace it with direct, concrete descriptions."
        )
    elif intensity == "minimal":
        intensity_instruction = (
            "Keep edits minimal. Only correct clear AI-authored artifacts or grammar issues. Preserve the original structure and meaning."
        )
    else:  # balanced
        intensity_instruction = (
            "Improve readability and rhythm. Moderate compression. Reduce generic business phrasing and overly polished AI-like patterns."
        )
    
    prompt = (
        f"You are an expert presentation editor. Rewrite the following slide text.\n"
        f"Original text: {text}\n"
        f"Slide role: {slide_role}\n"
        f"Tone style: {tone_desc}\n"
        f"Constraint: Keep it under {max_chars} characters.\n"
        f"{intensity_instruction}\n"
        f"Make it sound natural, specific, and presentation-ready in American English.\n"
        f"Avoid generic business phrases and emojis. Respond with the rewritten text only."
    )
    
    rewritten = None
    if model_mode == "managed_endpoint" and endpoint:
        try:
            rewritten = registry.call_user_hosted_endpoint(
                endpoint=endpoint,
                model_name=model_name or "llama3",
                prompt=prompt
            )
        except Exception as e:
            logger.error(f"Managed hosted LLM failed for candidates: {e}")
    elif model_mode == "user_hosted_endpoint" and endpoint:
        try:
            rewritten = registry.call_user_hosted_endpoint(
                endpoint=endpoint,
                model_name=model_name or "llama3",
                prompt=prompt
            )
        except Exception as e:
            logger.error(f"User-hosted model failed for candidates: {e}")
    else:  # local_cpu, local_gpu, or generic fallback
        try:
            instruction_model = registry.get_instruction_model()
            if instruction_model:
                input_words = len(text.split())
                max_tokens = max(50, int(input_words * 2))
                result = instruction_model(prompt, max_new_tokens=max_tokens, do_sample=True, temperature=0.7)
                rewritten = result[0]['generated_text'].strip()
        except Exception as e:
            logger.error(f"Local instruction model failed for candidates: {e}")
            
    if rewritten:
        # Clean it up from potential prompt wrapping
        cleaned = rewritten.replace("Original text:", "").replace("Rewritten text:", "").strip()
        return [{"text": cleaned, "notes": "Generative rewrite", "estimated_ai_likeness_delta": -0.2}]
        
    return None

def _generate_llm_candidates(
    text: str,
    tone: str,
    slide_role: str,
    max_chars: int,
    api_key: str,
    intensity: str = "balanced"
) -> Optional[List[Dict[str, Any]]]:
    """Calls Gemini API directly using urllib to avoid heavy external dependencies."""
    tone_desc = TONE_PRESETS.get(tone, TONE_PRESETS["consulting_professional"])
    
    intensity_rules = {
        "strong": (
            "Transform aggressively. You MUST change the sentence structure, replace every generic phrase, "
            "and compress vague claims into specific ones. If the original uses 'scale', replace with the actual "
            "capability it describes. If it uses 'not just X but Y', rewrite as a single declarative. "
            "The output MUST read differently from the original — a word-for-word match is a failure."
        ),
        "balanced": (
            "Edit meaningfully. Replace buzzwords and vague modifiers with specific alternatives. "
            "Adjust sentence rhythm. Preserve the core meaning but change enough that the text reads as "
            "a human draft, not a polished AI output."
        ),
        "minimal": (
            "Make only the minimum changes needed to remove mechanical artifacts and AI framing. "
            "Preserve the original structure and voice as closely as possible."
        )
    }

    identity_guard = (
        "CRITICAL: If you cannot meaningfully improve the text given these constraints, return the original "
        "text unchanged in the 'text' field and set 'unchanged': true in the JSON object. "
        "Do NOT return a subtly altered version that adds or removes only punctuation — that is worse than unchanged. "
        "Do NOT truncate or cut the sentence. Return the FULL rewritten text."
    )

    skip_guard = (
        "DO NOT REWRITE if the text is any of the following: a URL, an email address, a phone number, "
        "a standalone percentage or metric (e.g. '99.9%', '280 businesses'), a brand name, "
        "slide metadata, or an internal instruction to the team. For these, return the original unchanged."
    )

    prompt = (
        f"You are a senior B2B sales copywriter specializing in ERP and SaaS product decks for Indian MSMEs. "
        f"Your job is to humanize AI-generated slide text while preserving factual accuracy.\n\n"
        f"SLIDE ROLE: {slide_role}\n"
        f"TONE: {tone_desc}\n"
        f"MAX CHARACTERS: {max_chars}\n"
        f"INTENSITY: {intensity}\n\n"
        f"INTENSITY INSTRUCTION:\n{intensity_rules.get(intensity, intensity_rules['balanced'])}\n\n"
        f"{skip_guard}\n\n"
        f"{identity_guard}\n\n"
        f"ORIGINAL TEXT:\n\"\"\"\n{text}\n\"\"\"\n\n"
        f"Return a JSON array of exactly 3 distinct rewrites. Each item must be a JSON object with keys:\n"
        f"  - 'text': the rewritten string (full, not truncated)\n"
        f"  - 'notes': one sentence explaining what you changed and why\n"
        f"  - 'unchanged': true/false\n"
        f"  - 'change_type': one of ['structural', 'lexical', 'compression', 'unchanged']\n\n"
        f"No markdown blocks, no ```json formatting, no preamble. Return strictly a raw JSON array of objects."
    )
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            
            # Extract text from Gemini structure
            candidates_text = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
            
            # Strip potential JSON wrapper markdown ticks
            if candidates_text.startswith("```"):
                lines = candidates_text.splitlines()
                if lines[0].startswith("```json") or lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                candidates_text = "\n".join(lines).strip()
                
            parsed = json.loads(candidates_text)
            if isinstance(parsed, list):
                return parsed
    except Exception as e:
        logger.error(f"Failed to fetch rewrite candidates from Gemini: {e}")
        
    return None

def _generate_rule_based_candidates(
    original_text: str,
    base_cleaned: str,
    slide_role: str,
    max_chars: int
) -> List[Dict[str, Any]]:
    """Generates rule-based fallback candidates using local heuristics."""
    candidates = []
    
    # Candidate 1: Base cleaned (editorial rules only)
    candidates.append({
        "text": base_cleaned,
        "notes": "Spelling, punctuation, and grammar normalized.",
        "estimated_ai_likeness_delta": -0.05
    })
    
    # Candidate 2: Buzzword removal (specificity transform)
    from app.detector.features import GENERIC_PHRASES
    generic_cleaned = base_cleaned
    for phrase in GENERIC_PHRASES:
        # Simple case-insensitive replacement with blank or simpler word
        pattern = re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)
        # Try replacing common business fluff with simpler words
        replacement = ""
        if phrase == "streamline workflows":
            replacement = "simplify work"
        elif phrase == "enhance productivity":
            replacement = "increase output"
        elif phrase == "drive efficiency":
            replacement = "reduce time"
        elif phrase == "leverage":
            replacement = "use"
        elif phrase == "synergy":
            replacement = "collaboration"
        generic_cleaned = pattern.sub(replacement, generic_cleaned)
        
    generic_cleaned = re.sub(r"\s+", " ", generic_cleaned).strip()
    if generic_cleaned and generic_cleaned != base_cleaned:
        candidates.append({
            "text": apply_all_editorial_rules(generic_cleaned),
            "notes": "Redundant corporate jargon removed.",
            "estimated_ai_likeness_delta": -0.15
        })
        
    # Candidate 3: Compression transform (rhythm/compression)
    words = base_cleaned.split()
    if len(words) > 8:
        # Strip common filler phrases
        fillers = [
            r"\bin order to\b", r"\bas well as\b", r"\bfor the purpose of\b",
            r"\bwith reference to\b", r"\bplease note that\b", r"\bwe can see that\b"
        ]
        compressed = base_cleaned
        for f in fillers:
            compressed = re.sub(f, "to" if "order" in f else "and" if "well" in f else "", compressed, flags=re.IGNORECASE)
        compressed = re.sub(r"\s+", " ", compressed).strip()
        if compressed != base_cleaned:
            candidates.append({
                "text": apply_all_editorial_rules(compressed),
                "notes": "Filler words removed for layout safety.",
                "estimated_ai_likeness_delta": -0.1
            })
            
    return candidates
