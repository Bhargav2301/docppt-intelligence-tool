import sys
import os
import shutil
import asyncio
import uuid as uuid_mod

# Add services/nlp to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import SessionLocal
from models import User, Session as DbSession, PptSegment
from routers.ppt import process_single_ppt_internal

def main():
    db = SessionLocal()
    try:
        # Find default user
        user = db.query(User).filter(User.email == "local_user@example.com").first()
        if not user:
            # Seed user if doesn't exist
            user = User(email="local_user@example.com", full_name="Local Developer")
            db.add(user)
            db.commit()
            db.refresh(user)
        
        print(f"Using User: {user.email} ({user.id})")
        
        # We will process 6-Seafood.pptx as a first run
        src_path = r"C:\Projects\Samtool\OneDrive_1_5-22-2026\6-Seafood.pptx"
        if not os.path.exists(src_path):
            print(f"Source PPT not found at {src_path}")
            return
            
        print("\n--- RUN 1: Uploading 6-Seafood.pptx (First time) ---")
        res1 = db.query(DbSession).filter(
            DbSession.user_id == user.id, 
            DbSession.input_label == "6-Seafood.pptx",
            DbSession.status == "completed"
        ).first()
        
        if not res1:
            # Copy to a temporary location to process
            tmp_ppt = "temp_run1.pptx"
            shutil.copy2(src_path, tmp_ppt)
            try:
                result1 = asyncio.run(process_single_ppt_internal(
                    file_path=tmp_ppt,
                    filename="6-Seafood.pptx",
                    sensitivity="conservative",
                    db=db,
                    current_user=user
                ))
                print(f"Run 1 completed. Session ID: {result1['session']['id']}")
            finally:
                if os.path.exists(tmp_ppt):
                    os.remove(tmp_ppt)
        else:
            print(f"6-Seafood.pptx already processed in completed session {res1.id}")

        # Now, process 9-FMCG-and-Food-business.pptx as Run 2
        src_path_2 = r"C:\Projects\Samtool\OneDrive_1_5-22-2026\9-FMCG-and-Food-business.pptx"
        print("\n--- RUN 2: Uploading 9-FMCG-and-Food-business.pptx ---")
        tmp_ppt_2 = "temp_run2.pptx"
        shutil.copy2(src_path_2, tmp_ppt_2)
        try:
            result2 = asyncio.run(process_single_ppt_internal(
                file_path=tmp_ppt_2,
                filename="9-FMCG-and-Food-business.pptx",
                sensitivity="conservative",
                db=db,
                current_user=user
            ))
            session_id = result2['session']['id']
            print(f"Run 2 completed. Session ID: {session_id}")
            
            # Let's inspect the results to see if template_similarity_risk flags were added!
            session_uuid = uuid_mod.UUID(session_id)
            from models import PptOutput
            ppt_out = db.query(PptOutput).filter(PptOutput.session_id == session_uuid).first()
            segments = db.query(PptSegment).filter(PptSegment.ppt_output_id == ppt_out.id).all()
            
            flagged_count = 0
            for seg in segments:
                flags = seg.flags or []
                for flag in flags:
                    if flag.get("type") == "template_similarity_risk":
                        flagged_count += 1
                        print(f"  [MATCHED] Slide {seg.slide_index + 1} flagged as template similarity risk:")
                        print(f"    Text: {seg.original_text[:120]}...")
                        print(f"    Explanation: {flag.get('explanation')}")
            
            print(f"\nTotal template similarity flags found in Run 2: {flagged_count}")
        finally:
            if os.path.exists(tmp_ppt_2):
                os.remove(tmp_ppt_2)

    finally:
        db.close()

if __name__ == "__main__":
    main()
