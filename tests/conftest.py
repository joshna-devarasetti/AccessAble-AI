"""
Pytest fixtures and test client setup for AccessAble AI.
"""

import pytest
import io
from app import create_app
from config import Config

class TestConfig(Config):
    TESTING = True
    DEBUG = False
    OLLAMA_BASE_URL = "http://127.0.0.1:11434"
    MAX_TEXT_INPUT_CHARS = 10000

@pytest.fixture
def app():
    app = create_app(TestConfig)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def sample_pdf_bytes():
    """Generates a small in-memory valid PDF using PyMuPDF."""
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), "AccessAble AI is an accessible digital platform designed to facilitate inclusive reading.")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes
