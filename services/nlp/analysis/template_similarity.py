import re
import hashlib
from typing import List, Dict, Any, Union
from sqlalchemy.orm import Session as DBSession
from models import PptSegment, PptOutput, Session

def get_slide_fingerprint(texts: List[str]) -> str:
    """
    Computes a structural MD5 fingerprint of a slide based on its segment text.
    It cleans each segment to ignore specific numbers, placeholders/brackets,
    and non-alphanumeric styling, then sorts the cleaned blocks to ensure
    robustness against extraction ordering differences.
    """
    cleaned_blocks = []
    for text in texts:
        if not text:
            continue
        # Normalize whitespace and lowercase
        cleaned = text.lower().strip()
        # Remove bracketed placeholders e.g., [City], [X%], [Proof pending...]
        cleaned = re.sub(r'\[.*?\]', '', cleaned)
        # Remove digits to avoid metric/date differences
        cleaned = re.sub(r'\d+', '', cleaned)
        # Remove non-alphanumeric characters
        cleaned = re.sub(r'[^a-z0-9\s]', '', cleaned)
        cleaned = " ".join(cleaned.split())
        if cleaned:
            cleaned_blocks.append(cleaned)
    
    # Sort to be invariant to shape layout/extraction order within the slide
    combined = "|".join(sorted(cleaned_blocks))
    return hashlib.md5(combined.encode('utf-8')).hexdigest()

def check_template_similarity(
    db: DBSession, 
    user_id: Any, 
    current_slides: List[Dict[str, Any]],
    current_filename: str = None
) -> Dict[int, Dict[str, Any]]:
    """
    Compares the current slide decks structure against past completed slides
    for the same user. Excludes trivial slides (under 30 characters of text)
    and slides from the same filename to avoid version self-matching.
    Returns a dict mapping slide_index (int) -> match_info (dict).
    """
    matches_found = {}
    
    # 1. Fetch completed past slide segments for this user
    query = db.query(
        PptSegment.slide_index,
        PptSegment.normalized_text,
        Session.id.label("session_id"),
        Session.input_label.label("filename")
    ).join(
        PptOutput, PptSegment.ppt_output_id == PptOutput.id
    ).join(
        Session, PptOutput.session_id == Session.id
    ).filter(
        Session.user_id == user_id,
        Session.status == "completed"
    )
    
    # Exclude past sessions of the same file to prevent self-matching
    if current_filename:
        query = query.filter(Session.input_label != current_filename)
        
    rows = query.all()
    
    if not rows:
        return matches_found

    # 2. Group past segments by (session_id, filename, slide_index)
    past_slides_data = {}
    for row in rows:
        key = (row.session_id, row.filename, row.slide_index)
        if key not in past_slides_data:
            past_slides_data[key] = []
        past_slides_data[key].append(row.normalized_text or "")

    # 3. Compute past fingerprints
    past_fingerprints = {}
    for (sess_id, filename, s_idx), texts in past_slides_data.items():
        # Safeguard: check total length to avoid matching blank or short trivial slides
        combined_text = "".join(t for t in texts if t)
        if len(combined_text) < 30:
            continue
            
        fp = get_slide_fingerprint(texts)
        if fp not in past_fingerprints:
            past_fingerprints[fp] = []
        past_fingerprints[fp].append({
            "session_id": str(sess_id),
            "filename": filename,
            "slide_index": s_idx
        })

    # 4. Compute and match current slide fingerprints
    for slide in current_slides:
        slide_idx = slide.get("slide_index", 0)
        segments = slide.get("segments", [])
        
        texts = [seg.get("normalized_text", "") for seg in segments if seg.get("normalized_text")]
        combined_text = "".join(t for t in texts if t)
        
        # Skip checking short/empty slides
        if len(combined_text) < 30:
            continue
            
        current_fp = get_slide_fingerprint(texts)
        
        if current_fp in past_fingerprints:
            # Pick the first match from history (which is from a different file)
            match = past_fingerprints[current_fp][0]
            matches_found[slide_idx] = {
                "matched_filename": match["filename"],
                "matched_slide_idx": match["slide_index"]
            }

    return matches_found
