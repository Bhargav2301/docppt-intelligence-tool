import sys
import os
import json
import re

# Add services/nlp to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from extraction.ppt_parser import extract_ppt_text
from analysis.artifact_detector import detect_artifacts

FOLDER = r"C:\Projects\Samtool\OneDrive_1_5-22-2026"
files = [f for f in os.listdir(FOLDER) if f.endswith(".pptx")]

all_evaluations = {}

print("Starting programmatic analysis of the PPT suite...")

for idx, file in enumerate(sorted(files)):
    path = os.path.join(FOLDER, file)
    print(f"[{idx+1}/{len(files)}] Processing {file}...")
    try:
        # Extract text using backend parser
        extracted = extract_ppt_text(path)
        slides = extracted.get("slides", [])
        
        slide_results = []
        total_segments = 0
        total_flagged = 0
        flagged_slides_count = 0
        
        for slide_idx, slide in enumerate(slides):
            # Group paragraphs for context
            paragraph_texts = {}
            for seg in slide.get("segments", []):
                pi = seg.get("paragraph_index", 0)
                if pi not in paragraph_texts:
                    paragraph_texts[pi] = ""
                paragraph_texts[pi] += seg.get("original_text", "") + " "
            
            slide_flags = []
            slide_text_segments = []
            
            for seg in slide.get("segments", []):
                norm = seg.get("normalized_text", "").strip()
                if not norm:
                    continue
                total_segments += 1
                slide_text_segments.append(norm)
                
                context = paragraph_texts.get(seg.get("paragraph_index", 0), norm)
                # Run the backend detector
                flags = detect_artifacts(norm, paragraph_context=context)
                if flags:
                    total_flagged += len(flags)
                    slide_flags.append({
                        "text": norm,
                        "flags": flags
                    })
            
            if slide_flags:
                flagged_slides_count += 1
                
            slide_results.append({
                "slide_index": slide_idx,
                "text_content": " | ".join(slide_text_segments),
                "flags": slide_flags
            })
            
        all_evaluations[file] = {
            "total_slides": len(slides),
            "total_segments": total_segments,
            "total_flagged_segments": total_flagged,
            "flagged_slides_count": flagged_slides_count,
            "slides": slide_results
        }
    except Exception as e:
        print(f"  Error processing {file}: {e}")

# Save findings to json for downstream reporting
output_json_path = os.path.join(os.path.dirname(__file__), "ppt_eval_results.json")
with open(output_json_path, "w", encoding="utf-8") as f:
    json.dump(all_evaluations, f, indent=2)

print(f"\nEvaluations completed. Results saved to {output_json_path}")
