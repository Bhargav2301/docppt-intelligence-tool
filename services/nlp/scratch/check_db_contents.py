import sys
import os
import uuid as uuid_mod

# Add services/nlp to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import SessionLocal
from models import Session, PptOutput, PptSegment

db = SessionLocal()
try:
    sessions = db.query(Session).filter(Session.session_type == "ppt").all()
    print(f"Total sessions: {len(sessions)}")
    for s in sessions:
        out = db.query(PptOutput).filter(PptOutput.session_id == s.id).first()
        seg_count = 0
        if out:
            seg_count = db.query(PptSegment).filter(PptSegment.ppt_output_id == out.id).count()
        print(f"Session {s.id}: label={s.input_label}, status={s.status}, segments={seg_count}")
finally:
    db.close()
