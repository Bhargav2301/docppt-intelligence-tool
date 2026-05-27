import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import SessionLocal
from models import Session, PptOutput, PptSegment

db = SessionLocal()
try:
    s = db.query(Session).filter(Session.input_label == "6-Seafood.pptx").first()
    print("Session 6-Seafood:", s.id if s else "Not found")
    if s:
        out = db.query(PptOutput).filter(PptOutput.session_id == s.id).first()
        print("PptOutput ID:", out.id if out else "Not found")
        if out:
            # Let's count segments where normalized_text is not null/empty
            non_empty_norms = db.query(PptSegment).filter(
                PptSegment.ppt_output_id == out.id,
                PptSegment.normalized_text != None,
                PptSegment.normalized_text != ""
            ).count()
            print("Segments with normalized text:", non_empty_norms)
            
            # Print a few segments for Slide 13/14
            segs = db.query(PptSegment).filter(
                PptSegment.ppt_output_id == out.id,
                PptSegment.slide_index == 13
            ).all()
            for seg in segs:
                print(f"Slide 14 seg (original): {repr(seg.original_text)}")
                print(f"Slide 14 seg (normalized): {repr(seg.normalized_text)}")
                print(f"Slide 14 seg (flags): {repr(seg.flags)}")
finally:
    db.close()
