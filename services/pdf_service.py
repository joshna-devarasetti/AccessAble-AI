"""
PDF Processing Service using PyMuPDF (fitz)
Extracts text, metadata, page breakdown, and detects scanned/empty/encrypted PDFs.
"""

import io
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


class PDFProcessingError(Exception):
    """Custom exception for PDF processing issues."""
    pass


class PDFService:
    @staticmethod
    def is_available() -> bool:
        return fitz is not None

    @classmethod
    def extract_text_from_bytes(cls, file_bytes: bytes, filename: str = "document.pdf") -> Dict[str, Any]:
        """
        Extract text and structure from raw PDF bytes.
        Returns a dictionary with full text, page breakdown, and metadata.
        """
        if not cls.is_available():
            raise PDFProcessingError("PyMuPDF engine is not available on this server.")

        if not file_bytes:
            raise PDFProcessingError("The provided file is empty (0 bytes).")

        # Basic magic bytes check for PDF
        if not file_bytes.startswith(b"%PDF"):
            raise PDFProcessingError("The uploaded file does not appear to be a valid PDF format (missing %PDF header).")

        try:
            stream = io.BytesIO(file_bytes)
            doc = fitz.open(stream=stream, filetype="pdf")
        except Exception as e:
            logger.error("Failed to parse PDF stream: %s", str(e))
            raise PDFProcessingError(f"Corrupted or unreadable PDF: {str(e)}")

        try:
            if doc.is_encrypted:
                # Try default empty password
                auth = doc.authenticate("")
                if not auth:
                    raise PDFProcessingError("This PDF is password-protected. Please remove the password and re-upload.")

            page_count = len(doc)
            if page_count == 0:
                raise PDFProcessingError("The uploaded PDF contains zero pages.")

            extracted_pages: List[Dict[str, Any]] = []
            full_text_parts: List[str] = []
            total_chars = 0
            has_any_images = False

            for page_index in range(page_count):
                page = doc[page_index]
                text = page.get_text("text").strip()
                images = page.get_images()
                page_has_images = len(images) > 0
                if page_has_images:
                    has_any_images = True

                char_count = len(text)
                word_count = len(text.split()) if text else 0
                total_chars += char_count

                if text:
                    full_text_parts.append(text)

                extracted_pages.append({
                    "page_number": page_index + 1,
                    "text": text,
                    "char_count": char_count,
                    "word_count": word_count,
                    "has_images": page_has_images,
                    "image_count": len(images)
                })

            full_text = "\n\n".join(full_text_parts).strip()
            total_words = len(full_text.split()) if full_text else 0

            # Scanned detection heuristic:
            # If total text is very small (e.g. < 40 chars per page average) and pages have images,
            # it is almost certainly a scanned or image-only document.
            is_scanned = (total_chars < 50 and has_any_images) or (total_chars == 0 and page_count > 0)
            requires_ocr = is_scanned

            metadata = doc.metadata or {}
            clean_metadata = {
                "title": metadata.get("title") or filename,
                "author": metadata.get("author") or "Unknown",
                "creation_date": metadata.get("creationDate") or "",
                "producer": metadata.get("producer") or ""
            }

            return {
                "success": True,
                "filename": filename,
                "page_count": page_count,
                "total_words": total_words,
                "total_chars": total_chars,
                "text": full_text,
                "pages": extracted_pages,
                "is_scanned": is_scanned,
                "requires_ocr": requires_ocr,
                "metadata": clean_metadata,
                "ocr_performed": False
            }

        finally:
            doc.close()
