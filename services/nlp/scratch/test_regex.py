import re
text = "AI Strategy 2026 [Artifact: 123]"
pattern = r'\[Artifact:\s*.*?\]'
match = re.search(pattern, text)
print(f"Match: {match}")
if match:
    print(f"Matched text: {match.group(0)}")
