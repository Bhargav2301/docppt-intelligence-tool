import re
import ftfy

def normalize_text(text: str) -> str:
    """
    Normalizes pasted or extracted text by fixing broken encodings, 
    standardizing whitespace, and cleaning up smart quotes, while
    preserving intentional paragraph breaks.
    """
    if not text:
        return ""

    # Fix unicode issues (mojibake)
    text = ftfy.fix_text(text)

    # Standardize whitespace but preserve newlines
    # Replace carriage returns with standard newlines
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Collapse multiple spaces
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Collapse more than 3 newlines into exactly 2 newlines (paragraph boundary)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Trim each line and the whole document
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines).strip()
    
    return text
