"""
Integration tests for Flask application routes and endpoints.
"""

import io
from unittest.mock import patch, MagicMock


def test_index_route(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"AccessAble" in response.data
    assert b"Digital Accessibility Assistant" in response.data


def test_system_status_endpoint(client):
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "ollama" in data
    assert "ocr" in data
    assert "speech" in data


def test_text_analyze_endpoint(client):
    response = client.post("/api/text/analyze", json={"text": "This is a simple test sentence."})
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["readability"]["word_count"] == 6


def test_text_analyze_empty_input(client):
    response = client.post("/api/text/analyze", json={"text": ""})
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False


def test_speech_chunk_endpoint(client):
    long_text = "First sentence. Second sentence. Third sentence."
    response = client.post("/api/speech/chunk", json={"text": long_text})
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert len(data["chunks"]) > 0


def test_fallback_simplify_endpoint(client):
    response = client.post(
        "/api/text/fallback-simplify",
        json={"text": "We shall utilize preventative methods to terminate risks."}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["is_ai_generated"] is False
    assert "use" in data["simplified_text"].lower()


def test_pdf_upload_endpoint(client, sample_pdf_bytes):
    data = {
        "file": (io.BytesIO(sample_pdf_bytes), "test_doc.pdf")
    }
    response = client.post("/api/pdf/extract", data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    result = response.get_json()
    assert result["success"] is True
    assert result["page_count"] == 1
    assert "AccessAble AI is an accessible digital platform" in result["text"]


def test_pdf_upload_invalid_extension(client):
    data = {
        "file": (io.BytesIO(b"Hello world"), "test.txt")
    }
    response = client.post("/api/pdf/extract", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    result = response.get_json()
    assert result["success"] is False
    assert "Invalid file format" in result["error"]


def test_accessibility_checker_snippet(client):
    snippet = """
    <html lang="en">
    <head><title>Test Title</title></head>
    <body>
      <main>
        <h1>Heading 1</h1>
        <img src="pic.jpg">
      </main>
    </body>
    </html>
    """
    response = client.post("/api/accessibility/check-html", json={"html": snippet})
    assert response.status_code == 200
    result = response.get_json()
    assert result["success"] is True
    assert result["total_issues"] > 0
    assert result["severity_counts"]["Critical"] >= 1


def test_accessibility_checker_ssrf_block_localhost(client):
    response = client.post("/api/accessibility/check-url", json={"url": "http://127.0.0.1:8080"})
    assert response.status_code == 400
    result = response.get_json()
    assert result["success"] is False
    assert result["is_security_block"] is True


def test_404_api_endpoint(client):
    response = client.get("/api/nonexistent-endpoint")
    assert response.status_code == 404
    result = response.get_json()
    assert result["success"] is False
