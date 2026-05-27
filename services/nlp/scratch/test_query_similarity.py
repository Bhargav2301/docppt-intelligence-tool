import sys
import os

# Add services/nlp to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import SessionLocal
from models import User, Session, PptOutput, PptSegment
from analysis.template_similarity import check_template_similarity, get_slide_fingerprint

db = SessionLocal()
try:
    user = db.query(User).filter(User.email == "local_user@example.com").first()
    if not user:
        print("User not found.")
        sys.exit()
    
    # Let's mock a simple current slides array representing Slide 14 of 9-FMCG-and-Food-business.pptx
    # We will get the actual slide 14 segments from the database of a previous run of 9-FMCG-and-Food-business.pptx
    run9 = db.query(Session).filter(
        Session.user_id == user.id, 
        Session.input_label == "9-FMCG-and-Food-business.pptx",
        Session.status == "completed"
    ).first()
    
    run6 = db.query(Session).filter(
        Session.user_id == user.id,
        Session.input_label == "6-Seafood.pptx",
        Session.status == "completed"
    ).first()
    
    if not run9 or not run6:
        print("Required sessions not found.")
        sys.exit()

    out9 = db.query(PptOutput).filter(PptOutput.session_id == run9.id).first()
    out6 = db.query(PptOutput).filter(PptOutput.session_id == run6.id).first()
    
    seg9_texts = [seg.normalized_text for seg in db.query(PptSegment).filter(PptSegment.ppt_output_id == out9.id, PptSegment.slide_index == 13).all() if seg.normalized_text]
    seg6_texts = [seg.normalized_text for seg in db.query(PptSegment).filter(PptSegment.ppt_output_id == out6.id, PptSegment.slide_index == 13).all() if seg.normalized_text]
    
    print("--- SLIDE 14 SEGMENTS ---")
    print("6-Seafood segments count:", len(seg6_texts))
    print("9-FMCG segments count:", len(seg9_texts))
    
    fp6 = get_slide_fingerprint(seg6_texts)
    fp9 = get_slide_fingerprint(seg9_texts)
    print(f"Fingerprint 6-Seafood: {fp6}")
    print(f"Fingerprint 9-FMCG: {fp9}")
    
    print("Are fingerprints equal?", fp6 == fp9)
    
    # Now let's print the actual check_template_similarity outputs for these slides
    current_slides = [
        {
            "slide_index": 13,
            "segments": [{"normalized_text": t} for t in seg9_texts]
        }
    ]
    matches = check_template_similarity(db, user.id, current_slides)
    print("Matches returned by check_template_similarity:", matches)
    
finally:
    db.close()
