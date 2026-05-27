import sys
import os
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add services/nlp to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import Base
from models import User, Session, PptOutput, PptSegment
from analysis.artifact_detector import detect_artifacts
from analysis.template_similarity import get_slide_fingerprint, check_template_similarity

class TestPptHumanizerImprovements(unittest.TestCase):
    def test_bracketed_placeholders(self):
        # 1. Test case-sensitive parameter labels & uppercase tokens
        texts_to_flag = [
            "We operate in [City].",
            "Variance is [X]%.",
            "This will take [N] days.",
            "[Proof pending — to be updated before prospect delivery]",
            "Welcome [Company] team!",
            "Meet [Client] demands.",
            "Live in [Region / Country]."
        ]
        for t in texts_to_flag:
            flags = detect_artifacts(t)
            flag_types = [f["type"] for f in flags]
            self.assertIn("placeholder_text", flag_types, f"Failed to flag '{t}' as placeholder_text")

        # 2. Test case-insensitive common keywords
        lowercase_texts = [
            "Contact [city / region] office.",
            "Run for [x] weeks.",
            "Need to [insert] details.",
            "Check [todo] list."
        ]
        for t in lowercase_texts:
            flags = detect_artifacts(t)
            flag_types = [f["type"] for f in flags]
            self.assertIn("placeholder_text", flag_types, f"Failed to flag lowercase '{t}' as placeholder_text")

        # 3. Test citation numbers are NOT flagged as placeholders but as citation artifacts
        citation_text = "See details in [1]."
        flags = detect_artifacts(citation_text)
        flag_types = [f["type"] for f in flags]
        self.assertIn("citation_artifact", flag_types)
        self.assertNotIn("placeholder_text", flag_types)

    def test_citation_whitelist(self):
        # Test Source: ABSOLIN is whitelisted
        whitelist_text = "Source: ABSOLIN field observation across kraft paper mills, 2023–25."
        flags = detect_artifacts(whitelist_text)
        self.assertEqual(len(flags), 0, f"Source: ABSOLIN was flagged: {flags}")

        # Test normal Source: is still flagged
        normal_source = "Source: External research report, 2025."
        flags = detect_artifacts(normal_source)
        flag_types = [f["type"] for f in flags]
        self.assertIn("citation_artifact", flag_types)

    def test_template_similarity(self):
        # Setup in-memory DB
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        try:
            # Seed user
            user = User(email="test@example.com")
            db.add(user)
            db.commit()

            # Seed completed past session & output
            past_session = Session(
                user_id=user.id,
                session_type="ppt",
                input_type="pptx",
                input_label="Old_Presentation.pptx",
                status="completed"
            )
            db.add(past_session)
            db.commit()

            past_output = PptOutput(session_id=past_session.id, total_slides=1, total_flags=0)
            db.add(past_output)
            db.commit()

            # The past slide segments
            past_segment1 = PptSegment(
                ppt_output_id=past_output.id,
                slide_index=0,
                shape_id="1",
                paragraph_index=0,
                run_index=0,
                original_text="Core Seafood Processing Platform Capabilities.",
                normalized_text="Core Seafood Processing Platform Capabilities."
            )
            past_segment2 = PptSegment(
                ppt_output_id=past_output.id,
                slide_index=0,
                shape_id="2",
                paragraph_index=1,
                run_index=0,
                original_text="Yield improvements of 3-5% using real-time batch weight analytics.",
                normalized_text="Yield improvements of 3-5% using real-time batch weight analytics."
            )
            db.add_all([past_segment1, past_segment2])
            db.commit()

            # Let's verify fingerprint computation
            texts = [
                "Core Seafood Processing Platform Capabilities.",
                "Yield improvements of 3-5% using real-time batch weight analytics."
            ]
            fp = get_slide_fingerprint(texts)
            self.assertTrue(len(fp) > 0)

            # Test similarity checker
            current_slides = [
                {
                    "slide_index": 0,
                    "segments": [
                        {
                            "shape_id": "1",
                            "paragraph_index": 0,
                            "run_index": 0,
                            "original_text": "Core Seafood Processing Platform Capabilities.",
                            "normalized_text": "Core Seafood Processing Platform Capabilities."
                        },
                        {
                            "shape_id": "2",
                            "paragraph_index": 1,
                            "run_index": 0,
                            "original_text": "Yield improvements of 3-5% using real-time batch weight analytics.",
                            "normalized_text": "Yield improvements of 3-5% using real-time batch weight analytics."
                        }
                    ]
                }
            ]

            matches = check_template_similarity(db, user.id, current_slides)
            self.assertIn(0, matches)
            self.assertEqual(matches[0]["matched_filename"], "Old_Presentation.pptx")
            self.assertEqual(matches[0]["matched_slide_idx"], 0)

            # Test trivial slide filter (less than 30 characters should not match)
            short_slides = [
                {
                    "slide_index": 1,
                    "segments": [
                        {
                            "shape_id": "3",
                            "original_text": "Short slide.",
                            "normalized_text": "Short slide."
                        }
                    ]
                }
            ]
            matches_short = check_template_similarity(db, user.id, short_slides)
            self.assertEqual(len(matches_short), 0)

        finally:
            db.close()

if __name__ == "__main__":
    unittest.main()
