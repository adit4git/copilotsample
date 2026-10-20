"""
files.py
========
Turn an uploaded file (statement, screenshot, CSV, PDF) into text the resolver
can mine for entities.

Strategy by type:
  - .txt/.csv/.md/.json  -> read directly
  - .pdf                 -> pdfplumber text if available, else note
  - images (.png/.jpg)   -> send to the LLM vision model for OCR/description
                            when a key is present; otherwise a stub placeholder.

Kept deliberately small; production would use a proper document-AI service.
"""

from __future__ import annotations
import base64
import os
from pathlib import Path

TEXT_EXT = {".txt", ".csv", ".md", ".json", ".tsv"}
IMG_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def extract_text(path: str) -> str:
    p = Path(path)
    ext = p.suffix.lower()
    if ext in TEXT_EXT:
        return p.read_text(errors="ignore")[:8000]
    if ext == ".pdf":
        return _pdf_text(p)
    if ext in IMG_EXT:
        return _image_text(p)
    return f"[unsupported file type: {ext}]"


def _pdf_text(p: Path) -> str:
    try:
        import pdfplumber
        out = []
        with pdfplumber.open(str(p)) as pdf:
            for page in pdf.pages[:5]:
                out.append(page.extract_text() or "")
        return ("\n".join(out))[:8000] or "[pdf had no extractable text]"
    except Exception as e:
        return f"[pdf read failed: {e}]"


def _image_text(p: Path) -> str:
    """OCR/describe an image via the LLM vision model, if configured."""
    key = os.getenv("ANTHROPIC_API_KEY")
    if key and os.getenv("PROVIDER", "anthropic").lower() == "anthropic":
        try:
            import anthropic
            data = base64.standard_b64encode(p.read_bytes()).decode()
            media = f"image/{p.suffix.lower().lstrip('.').replace('jpg','jpeg')}"
            client = anthropic.Anthropic()
            resp = client.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
                max_tokens=1024,
                messages=[{"role": "user", "content": [
                    {"type": "image", "source": {"type": "base64",
                     "media_type": media, "data": data}},
                    {"type": "text", "text":
                     "Transcribe every account number, holding, ticker, balance, "
                     "and dollar figure visible in this financial screenshot/statement. "
                     "Return as plain labelled text."},
                ]}],
            )
            return resp.content[0].text[:8000]
        except Exception as e:
            return f"[image OCR failed, continuing without it: {e}]"
    # Offline stub so the flow still demonstrates file-assisted resolution.
    return ("[OFFLINE STUB OCR] Held-away 401(k) statement — "
            "Account ****7731 — Balance $284,500 — Holdings: VTSAX 62%, VBTLX 28%, "
            "cash 10%. Owner: Henderson, J.")
