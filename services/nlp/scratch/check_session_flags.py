import sys
import os
import uuid as uuid_mod

# Add services/nlp to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import SessionLocal
from models import Session, PptOutput, PptSegment

db = SessionLocal()
try:
    session_id = uuid_mod.UUID("a74efe1c-700e-40e4-b2f2-0cd8be33b794")
    ppt_out = db.query(PptOutput).filter(PptOutput.session_id == session_id).first()
    if not ppt_out:
        print("PptOutput not found.")
        sys.exit()
        
    print(f"Checking session output ID: {ppt_out.id}")
    segments = db.query(PptSegment).filter(PptSegment.ppt_output_id == ppt_out.id).all()
    
    sim_flags_count = 0
    all_flags_count = 0
    for seg in segments:
        flags = seg.flags or []
        all_flags_count += len(flags)
        for flag in flags:
            if flag.get("type") == "template_similarity_risk":
                sim_flags_count += 1
                print(f"Slide {seg.slide_index + 1}: flagged '{flag.get('type')}'")
                print(f"  Explanation: {flag.get('explanation')}")
                
    print(f"\nTotal segment flags in DB: {all_flags_count}")
    print(f"Total template similarity flags in DB: {sim_flags_count}")
finally:
    db.close()
