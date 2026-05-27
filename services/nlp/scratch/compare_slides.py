import json
import os
import sys

# Add services/nlp to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analysis.template_similarity import get_slide_fingerprint

json_path = r"c:\Projects\Samtool\docppt-intelligence-tool\services\nlp\scratch\ppt_eval_results.json"
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

f1 = "6-Seafood.pptx"
f2 = "9-FMCG-and-Food-business.pptx"

if f1 not in data or f2 not in data:
    print("Files not found in JSON.")
    sys.exit()

s1 = data[f1]["slides"]
s2 = data[f2]["slides"]

print(f"Comparing slides of {f1} and {f2}:")
for idx1, slide1 in enumerate(s1):
    t1 = [seg.strip() for seg in slide1["text_content"].split(" | ") if seg.strip()]
    c1 = "".join(t1)
    if len(c1) < 30:
        continue
    fp1 = get_slide_fingerprint(t1)
    
    for idx2, slide2 in enumerate(s2):
        t2 = [seg.strip() for seg in slide2["text_content"].split(" | ") if seg.strip()]
        c2 = "".join(t2)
        if len(c2) < 30:
            continue
        fp2 = get_slide_fingerprint(t2)
        
        if fp1 == fp2:
            print(f"Match found! {f1} Slide {idx1+1} matches {f2} Slide {idx2+1}")
            print(f"  Fingerprint: {fp1}")
            print(f"  Text 1: {slide1['text_content'][:200]}...")
            print(f"  Text 2: {slide2['text_content'][:200]}...")
            print()
