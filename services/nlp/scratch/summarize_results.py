import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

json_path = os.path.join(os.path.dirname(__file__), "ppt_eval_results.json")
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

print("| File Name | Total Slides | Total Segments | Flagged Segments | Flagged Slides | Flagged Ratio (Slides) | Flagged Ratio (Segs) |")
print("|---|---|---|---|---|---|---|")

total_s = 0
total_seg = 0
total_fl_seg = 0
total_fl_s = 0

for file, stats in sorted(data.items()):
    ts = stats["total_slides"]
    tseg = stats["total_segments"]
    tfl_seg = stats["total_flagged_segments"]
    tfl_s = stats["flagged_slides_count"]
    
    total_s += ts
    total_seg += tseg
    total_fl_seg += tfl_seg
    total_fl_s += tfl_s
    
    ratio_s = f"{(tfl_s / ts * 100):.1f}%" if ts > 0 else "0.0%"
    ratio_seg = f"{(tfl_seg / tseg * 100):.1f}%" if tseg > 0 else "0.0%"
    
    print(f"| {file} | {ts} | {tseg} | {tfl_seg} | {tfl_s} | {ratio_s} | {ratio_seg} |")

print(f"| **TOTAL** | **{total_s}** | **{total_seg}** | **{total_fl_seg}** | **{total_fl_s}** | **{(total_fl_s / total_s * 100):.1f}%** | **{(total_fl_seg / total_seg * 100):.1f}%** |")

print("\n\n=== Flagged Types breakdown ===")
flag_types = {}
for file, stats in data.items():
    for slide in stats["slides"]:
        for item in slide["flags"]:
            for flag in item["flags"]:
                ftype = flag["type"]
                flag_types[ftype] = flag_types.get(ftype, 0) + 1

for ftype, count in sorted(flag_types.items(), key=lambda x: x[1], reverse=True):
    print(f"- {ftype}: {count}")

print("\n\n=== Sample Flagged items ===")
count = 0
for file, stats in sorted(data.items()):
    for slide in stats["slides"]:
        for item in slide["flags"]:
            for flag in item["flags"]:
                if count < 15:
                    print(f"File: {file} (Slide {slide['slide_index']+1})")
                    print(f"  Text: {item['text']}")
                    print(f"  Flag: {flag['type']} - {flag['matched_text']}")
                    print(f"  Explanation: {flag['explanation']}")
                    print()
                    count += 1
