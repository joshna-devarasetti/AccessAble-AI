"""
Unit tests for Accessibility Service (WCAG 2.1 checks and SSRF security).
"""

import pytest
from services.accessibility_service import AccessibilityService, SSRFValidationError


def test_missing_alt_image_detection():
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head><title>Test Page</title></head>
    <body>
      <main>
        <h1>Welcome</h1>
        <img src="chart.png">
      </main>
    </body>
    </html>
    """
    res = AccessibilityService.analyze_html(html)
    assert res["success"] is True
    issue_ids = [i["id"] for i in res["issues"]]
    assert "img-missing-alt" in issue_ids
    assert res["severity_counts"]["Critical"] >= 1


def test_missing_form_label_detection():
    html = """
    <html lang="en">
    <head><title>Test</title></head>
    <body>
      <main>
        <h1>Form</h1>
        <input type="text" name="username">
      </main>
    </body>
    </html>
    """
    res = AccessibilityService.analyze_html(html)
    issue_ids = [i["id"] for i in res["issues"]]
    assert "form-control-missing-label" in issue_ids


def test_heading_hierarchy_check():
    html = """
    <html lang="en">
    <head><title>Test</title></head>
    <body>
      <main>
        <h1>Main Title</h1>
        <h3>Skipped to H3</h3>
      </main>
    </body>
    </html>
    """
    res = AccessibilityService.analyze_html(html)
    issue_ids = [i["id"] for i in res["issues"]]
    assert "heading-skipped-level" in issue_ids


def test_missing_lang_and_title():
    html = """
    <html>
    <body>
      <main>
        <h1>Hello</h1>
      </main>
    </body>
    </html>
    """
    res = AccessibilityService.analyze_html(html)
    issue_ids = [i["id"] for i in res["issues"]]
    assert "missing-lang-attr" in issue_ids
    assert "missing-page-title" in issue_ids


def test_ssrf_ip_blocklist():
    # Loopback
    assert AccessibilityService.is_safe_ip("127.0.0.1") is False
    assert AccessibilityService.is_safe_ip("::1") is False

    # Private ranges
    assert AccessibilityService.is_safe_ip("192.168.1.1") is False
    assert AccessibilityService.is_safe_ip("10.0.0.5") is False
    assert AccessibilityService.is_safe_ip("172.16.0.1") is False

    # Link-local / Cloud metadata IP
    assert AccessibilityService.is_safe_ip("169.254.169.254") is False

    # Carrier-grade NAT
    assert AccessibilityService.is_safe_ip("100.64.0.1") is False

    # Public IP
    assert AccessibilityService.is_safe_ip("8.8.8.8") is True
    assert AccessibilityService.is_safe_ip("1.1.1.1") is True


def test_ssrf_url_validation_blocks_localhost():
    with pytest.raises(SSRFValidationError):
        AccessibilityService.validate_and_resolve_url("http://localhost:8080/admin")

    with pytest.raises(SSRFValidationError):
        AccessibilityService.validate_and_resolve_url("http://127.0.0.1:5000/api")
