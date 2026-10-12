"""
Unit tests for PDF Service (PyMuPDF integration).
"""

import pytest
import io
from services.pdf_service import PDFService, PDFProcessingError


def test_pdf_service_available():
    assert PDFService.is_available() is True


def test_extract_text_valid_pdf(sample_pdf_bytes):
    result = PDFService.extract_text_from_bytes(sample_pdf_bytes, filename="test_doc.pdf")
    assert result["success"] is True
    assert result["page_count"] == 1
    assert "AccessAble AI is an accessible digital platform" in result["text"]
    assert result["total_words"] > 0
    assert result["is_scanned"] is False
    assert result["requires_ocr"] is False


def test_extract_empty_bytes():
    with pytest.raises(PDFProcessingError) as exc_info:
        PDFService.extract_text_from_bytes(b"", filename="empty.pdf")
    assert "empty" in str(exc_info.value).lower()


def test_extract_invalid_pdf_header():
    with pytest.raises(PDFProcessingError) as exc_info:
        PDFService.extract_text_from_bytes(b"This is not a pdf file at all.", filename="corrupt.pdf")
    assert "not appear to be a valid pdf" in str(exc_info.value).lower()


def test_scanned_pdf_heuristic():
    import fitz
    from PIL import Image

    # Create a PDF containing an image but no text
    img = Image.new("RGB", (200, 200), color=(255, 0, 0))
    img_bytes_io = io.BytesIO()
    img.save(img_bytes_io, format="PNG")
    img_bytes = img_bytes_io.getvalue()

    doc = fitz.open()
    page = doc.new_page()
    rect = fitz.Rect(50, 50, 150, 150)
    page.insert_image(rect, stream=img_bytes)
    pdf_bytes = doc.tobytes()
    doc.close()

    result = PDFService.extract_text_from_bytes(pdf_bytes, filename="scanned_test.pdf")
    assert result["success"] is True
    assert result["is_scanned"] is True
    assert result["requires_ocr"] is True
