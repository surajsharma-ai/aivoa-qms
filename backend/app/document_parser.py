"""Small, auditable document-ingestion layer for complaint source evidence.

Text-native PDFs are extracted with pypdf. Scanned PDFs and images use Tesseract OCR
when the optional OCR runtime is installed. The parser returns metadata so the UI can
show whether the source was parsed natively or OCR'd instead of silently claiming success.
"""
from __future__ import annotations

import io
from typing import Any


TEXT_EXTENSIONS = {".txt", ".eml", ".csv", ".md", ".json"}


def _decode(raw: bytes) -> str:
    return raw.decode("utf-8", errors="ignore").replace("\x00", " ").strip()


def _ocr_image(image: Any) -> str:
    try:
        import pytesseract
        return pytesseract.image_to_string(image).strip()
    except Exception:
        return ""


def parse_document(raw: bytes, filename: str | None, content_type: str | None = None) -> tuple[str, dict[str, Any]]:
    """Return extracted text and explicit parser metadata.

    This function never raises for an unsupported or malformed upload. The complaint
    can still be logged with a follow-up item asking QA to review the original evidence.
    """
    name = (filename or "upload").lower()
    suffix = "." + name.rsplit(".", 1)[-1] if "." in name else ""
    metadata: dict[str, Any] = {
        "filename": filename,
        "content_type": content_type or "application/octet-stream",
        "method": "unsupported",
        "pages": 0,
        "characters": 0,
        "ocr_used": False,
        "warning": None,
    }

    if suffix in TEXT_EXTENSIONS or (content_type or "").startswith("text/"):
        text = _decode(raw)
        metadata.update(method="text extraction", characters=len(text))
        return text, metadata

    if suffix == ".pdf" or content_type == "application/pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(raw))
            pages = len(reader.pages)
            text_parts = [(page.extract_text() or "").strip() for page in reader.pages]
            text = "\n\n".join(part for part in text_parts if part).strip()
            metadata.update(method="PDF text extraction", pages=pages, characters=len(text))
            if text:
                return text, metadata
        except Exception as exc:
            metadata["warning"] = f"Native PDF extraction failed: {type(exc).__name__}"
            pages = metadata.get("pages", 0)

        # Scanned PDFs have no text layer. Render pages and OCR them when the runtime
        # is available. PyMuPDF is intentionally optional so text-only deployments stay lean.
        try:
            import fitz
            import PIL.Image
            import pytesseract  # noqa: F401 - availability check
            document = fitz.open(stream=raw, filetype="pdf")
            ocr_parts: list[str] = []
            for page in document:
                pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                image = PIL.Image.open(io.BytesIO(pixmap.tobytes("png")))
                page_text = _ocr_image(image)
                if page_text:
                    ocr_parts.append(page_text)
            text = "\n\n".join(ocr_parts).strip()
            metadata.update(method="PDF OCR", pages=len(document), characters=len(text), ocr_used=True)
            if text:
                return text, metadata
            metadata["warning"] = "PDF contained no readable text and OCR returned no content."
        except Exception as exc:
            metadata.update(method="PDF upload", warning=f"Scanned PDF OCR unavailable: {type(exc).__name__}")
        return "", metadata

    if (content_type or "").startswith("image/") or suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}:
        try:
            from PIL import Image
            image = Image.open(io.BytesIO(raw))
            text = _ocr_image(image)
            metadata.update(method="Image OCR", pages=1, characters=len(text), ocr_used=True)
            if text:
                return text, metadata
            metadata["warning"] = "OCR returned no readable content."
        except Exception as exc:
            metadata["warning"] = f"Image OCR unavailable: {type(exc).__name__}"
        return "", metadata

    metadata["warning"] = "Unsupported file type; upload TXT, EML, CSV, PDF or an image."
    return _decode(raw), {**metadata, "method": "best-effort text decode", "characters": len(_decode(raw))}
