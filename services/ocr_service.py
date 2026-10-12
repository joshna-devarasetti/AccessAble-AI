"""
OCR Processing Service
Provides local Optical Character Recognition for scanned PDFs and images.
Detects local Tesseract installations and provides friendly Windows setup instructions when unavailable.
"""

import io
import os
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None
    Image = None

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


class OCRService:
    _cached_tesseract_path: Optional[str] = None
    _checked_availability: bool = False
    _is_available: bool = False

    COMMON_WINDOWS_PATHS = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
        os.path.expandvars(r"%USERPROFILE%\AppData\Local\Programs\Tesseract-OCR\tesseract.exe")
    ]

    @classmethod
    def check_availability(cls) -> Dict[str, Any]:
        """
        Check if pytesseract library and system Tesseract binary are installed.
        """
        if pytesseract is None:
            return {
                "available": False,
                "reason": "Python 'pytesseract' library is not imported.",
                "tesseract_path": None,
                "instructions": cls.get_windows_install_instructions()
            }

        # Check if tesseract binary exists in PATH or common Windows directories
        tess_bin = shutil.which("tesseract")
        if not tess_bin:
            for path in cls.COMMON_WINDOWS_PATHS:
                if Path(path).is_file():
                    tess_bin = path
                    break

        if tess_bin:
            try:
                pytesseract.pytesseract.tesseract_cmd = tess_bin
                version = pytesseract.get_tesseract_version()
                cls._cached_tesseract_path = tess_bin
                cls._is_available = True
                return {
                    "available": True,
                    "version": str(version),
                    "tesseract_path": tess_bin,
                    "instructions": None
                }
            except Exception as e:
                logger.warning("Found tesseract at %s but check failed: %s", tess_bin, str(e))

        cls._is_available = False
        return {
            "available": False,
            "reason": "Tesseract OCR binary was not detected on this Windows system.",
            "tesseract_path": None,
            "instructions": cls.get_windows_install_instructions()
        }

    @classmethod
    def is_available(cls) -> bool:
        res = cls.check_availability()
        return res["available"]

    @staticmethod
    def get_windows_install_instructions() -> Dict[str, Any]:
        return {
            "title": "Local Tesseract OCR Setup for Windows",
            "message": "This document contains scanned image pages without selectable text. To extract text locally without cloud APIs, install Tesseract OCR on Windows.",
            "steps": [
                "Option 1 (PowerShell / WinGet): Run 'winget install UB-Mannheim.TesseractOCR' in an Administrator terminal.",
                "Option 2 (Direct Installer): Download the Windows installer from https://github.com/UB-Mannheim/tesseract/wiki (e.g. tesseract-ocr-w64-setup-5.x.exe).",
                "Default install path is usually 'C:\\Program Files\\Tesseract-OCR\\'.",
                "Add 'C:\\Program Files\\Tesseract-OCR' to your system PATH or configure TESSERACT_CMD in your .env file.",
                "Restart the AccessAble AI application to enable automated scanned document extraction."
            ]
        }

    @classmethod
    def ocr_pdf_bytes(cls, file_bytes: bytes, max_pages: int = 20) -> Dict[str, Any]:
        """
        Perform OCR on scanned PDF pages by rendering them via PyMuPDF and running Tesseract.
        """
        status = cls.check_availability()
        if not status["available"]:
            return {
                "success": False,
                "error": "OCR engine is not installed on this system.",
                "instructions": status["instructions"],
                "text": ""
            }

        if fitz is None or Image is None:
            return {
                "success": False,
                "error": "PyMuPDF or Pillow is missing.",
                "instructions": None,
                "text": ""
            }

        try:
            stream = io.BytesIO(file_bytes)
            doc = fitz.open(stream=stream, filetype="pdf")
            total_pages = min(len(doc), max_pages)

            ocr_text_parts = []
            page_results = []

            for i in range(total_pages):
                page = doc[i]
                # Render page at 200 DPI for reliable OCR readability
                pix = page.get_pixmap(dpi=200)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                page_text = pytesseract.image_to_string(img).strip()

                if page_text:
                    ocr_text_parts.append(page_text)

                page_results.append({
                    "page_number": i + 1,
                    "text": page_text,
                    "char_count": len(page_text),
                    "word_count": len(page_text.split())
                })

            doc.close()
            full_text = "\n\n".join(ocr_text_parts).strip()

            return {
                "success": True,
                "text": full_text,
                "pages": page_results,
                "total_pages_processed": total_pages,
                "total_words": len(full_text.split()),
                "ocr_performed": True
            }

        except Exception as e:
            logger.error("OCR extraction failed: %s", str(e))
            return {
                "success": False,
                "error": f"OCR processing failed: {str(e)}",
                "instructions": None,
                "text": ""
            }
