"""Upload validation helpers: enforce extension, MIME-by-magic-bytes, and size limits."""
import os
from fastapi import HTTPException, UploadFile

MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(50 * 1024 * 1024)))  # 50 MB default

# .docx and .pptx are both ZIP-based (OOXML); both start with PK\x03\x04.
_OOXML_MAGIC = b"PK\x03\x04"

_ALLOWED = {
    "docx": {
        "extensions": (".docx",),
        "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    },
    "pptx": {
        "extensions": (".pptx",),
        "mime": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    },
}


def validate_upload(file: UploadFile, file_bytes: bytes, kind: str) -> None:
    """Validate an uploaded file by extension, magic bytes, and size.

    Raises HTTPException on failure. Returns None on success.
    """
    spec = _ALLOWED.get(kind)
    if spec is None:
        raise HTTPException(status_code=500, detail=f"Unknown upload kind: {kind}")

    filename = (file.filename or "").lower()
    if not filename.endswith(spec["extensions"]):
        raise HTTPException(
            status_code=400,
            detail=f"Only {', '.join(spec['extensions'])} files are supported.",
        )

    size = len(file_bytes)
    if size == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if size > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {size} bytes exceeds {MAX_UPLOAD_BYTES} bytes.",
        )

    if not file_bytes.startswith(_OOXML_MAGIC):
        raise HTTPException(
            status_code=400,
            detail="File does not look like a valid OOXML (.docx/.pptx) archive.",
        )
