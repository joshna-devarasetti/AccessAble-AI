"""
Unit tests for Image Processing Service.
"""

import io
import pytest
from PIL import Image
from services.image_service import ImageService, ImageValidationError


def test_validate_and_prepare_valid_png():
    img = Image.new("RGB", (100, 100), color="blue")
    b = io.BytesIO()
    img.save(b, format="PNG")
    data = b.getvalue()

    result = ImageService.validate_and_prepare(data, filename="sample.png")
    assert result["success"] is True
    assert result["format"] == "PNG"
    assert result["width"] == 100
    assert result["height"] == 100
    assert result["mime_type"] == "image/png"
    assert len(result["base64_data"]) > 0
    assert result["data_uri"].startswith("data:image/png;base64,")


def test_reject_empty_image():
    with pytest.raises(ImageValidationError) as exc_info:
        ImageService.validate_and_prepare(b"", filename="empty.png")
    assert "empty" in str(exc_info.value).lower()


def test_reject_unsupported_format():
    # Write text bytes
    fake_img = b"<svg><circle cx='5' cy='5' r='5'/></svg>"
    with pytest.raises(ImageValidationError):
        ImageService.validate_and_prepare(fake_img, filename="vector.svg")


def test_reject_oversized_image():
    img = Image.new("RGB", (100, 100), color="green")
    b = io.BytesIO()
    img.save(b, format="JPEG")
    data = b.getvalue()

    # Pass max_size_mb = 0.0001 (0.1 KB limit)
    with pytest.raises(ImageValidationError) as exc_info:
        ImageService.validate_and_prepare(data, max_size_mb=0.0001)
    assert "exceeds size limit" in str(exc_info.value).lower()
