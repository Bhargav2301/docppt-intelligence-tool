import json
import os
import sys

# Ensure UTF-8 stdout on Windows
sys.stdout.reconfigure(encoding='utf-8')

json_path = r"c:\Projects\Samtool\docppt-intelligence-tool\services\nlp\scratch\ppt_eval_results.json"
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

targets = [
    "12-Automotive-Manufacturing.pptx",
    "2-Kraft-Paper-and-Packaging-Manufacturing.pptx",
    "6-Seafood.pptx",
    "9-FMCG-and-Food-business.pptx"
]

print("=== SUBSET BASELINE INSPECTION ===")

for target in targets:
    if target not in data:
        print(f"File {target} not found in eval results.")
        continue
    
    file_info = data[target]
    print(f"\nFile: {target}")
    print(f"Total Slides: {file_info['total_slides']}, Total Segments: {file_info['total_segments']}, Total Flagged: {file_info['total_flagged_segments']}")
    
    # Let's inspect slide by slide
    for slide in file_info["slides"]:
        slide_idx = slide["slide_index"]
        text = slide["text_content"]
        flags = slide["flags"]
        
        # Look for brackets or Source:
        has_brackets = "[" in text or "]" in text or "{" in text or "}" in text
        has_source = "Source:" in text
        
        if has_brackets or has_source or flags:
            print(f"  Slide {slide_idx}:")
            print(f"    Text: {text[:250]}...")
            if flags:
                # Format flags nicely as text
                print(f"    Flags detected: {len(flags)}")
                for flag in flags:
                    print(f"      - Text matched: {flag.get('text')}")
                    for sub_flag in flag.get("flags", []):
                        print(f"        Type: {sub_flag.get('type')}, Matched: '{sub_flag.get('matched_text')}', Rec: {sub_flag.get('recommendation')}")
            if has_brackets and not flags:
                print("    [WARNING] Brackets present but NO flags detected!")
