import io
import docx

def extract_from_docx(file_bytes: bytes) -> str:
    """
    Parses a DOCX file from bytes and extracts all text, 
    preserving paragraph boundaries and newlines.
    """
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        full_text = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                full_text.append(text)
        return "\n\n".join(full_text)
    except Exception as e:
        raise ValueError(f"Failed to parse DOCX file: {str(e)}")
