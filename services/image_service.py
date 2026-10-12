"""
Image Processing Service
Validates image files (format, size, dimensions), prevents malicious uploads,
and encodes images for local vision-language models.
"""

import io
import base64
import logging
from typing import Dict, Any, Tuple
from PIL import Image

logger = logging.getLogger(__name__)


class ImageValidationError(Exception):
    """Exception raised for invalid or unsafe images."""
    pass


class ImageService:
    ALLOWED_FORMATS = {"PNG", "JPEG", "JPG", "WEBP", "BMP"}
    MAX_DIMENSION = 6000  # pixels
    MIN_DIMENSION = 10    # pixels

    @classmethod
    def validate_and_prepare(
        cls,
        image_bytes: bytes,
        filename: str = "upload.png",
        max_size_mb: int = 10
    ) -> Dict[str, Any]:
        """
        Validates image bytes, checks headers, dimensions, and converts to base64.
        """
        if not image_bytes:
            raise ImageValidationError("Image payload is empty (0 bytes).")

        size_mb = len(image_bytes) / (1024 * 1024)
        if size_mb > max_size_mb:
            raise ImageValidationError(f"Image exceeds size limit of {max_size_mb} MB (received {size_mb:.2f} MB).")

        try:
            stream = io.BytesIO(image_bytes)
            with Image.open(stream) as img:
                img_format = (img.format or "").upper()
                if img_format not in cls.ALLOWED_FORMATS:
                    raise ImageValidationError(
                        f"Unsupported image format: '{img_format}'. Allowed formats are PNG, JPEG, WEBP, BMP."
                    )

                width, height = img.size
                if width < cls.MIN_DIMENSION or height < cls.MIN_DIMENSION:
                    raise ImageValidationError(f"Image is too small ({width}x{height} px). Minimum size is 10x10 px.")

                if width > cls.MAX_DIMENSION or height > cls.MAX_DIMENSION:
                    raise ImageValidationError(f"Image dimensions ({width}x{height} px) exceed maximum permitted {cls.MAX_DIMENSION}px.")

                # Verify image can be decoded without decompression bombs or corruption
                img.verify()

        except ImageValidationError:
            raise
        except Exception as e:
            logger.error("Image verification failed: %s", str(e))
            raise ImageValidationError(f"Corrupted or invalid image file: {str(e)}")

        # Re-open image stream to read clean bytes for base64 encoding
        b64_encoded = base64.b64encode(image_bytes).decode("utf-8")
        mime_type = "image/png"
        if img_format in ("JPEG", "JPG"):
            mime_type = "image/jpeg"
        elif img_format == "WEBP":
            mime_type = "image/webp"
        elif img_format == "BMP":
            mime_type = "image/bmp"

        data_uri = f"data:{mime_type};base64,{b64_encoded}"

        return {
            "success": True,
            "filename": filename,
            "format": img_format,
            "width": width,
            "height": height,
            "mime_type": mime_type,
            "size_kb": round(len(image_bytes) / 1024, 1),
            "base64_data": b64_encoded,
            "data_uri": data_uri
        }
