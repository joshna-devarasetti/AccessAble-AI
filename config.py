import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    # Flask settings
    SECRET_KEY = os.getenv("SECRET_KEY", "accessable-ai-local-dev-secret-key-change-in-production")
    DEBUG = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    TESTING = False

    # Uploads & Storage limits
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 25 * 1024 * 1024))  # 25 MB max request
    MAX_PDF_SIZE_MB = int(os.getenv("MAX_PDF_SIZE_MB", 20))
    MAX_IMAGE_SIZE_MB = int(os.getenv("MAX_IMAGE_SIZE_MB", 10))
    MAX_HTML_SIZE_MB = int(os.getenv("MAX_HTML_SIZE_MB", 5))
    MAX_TEXT_INPUT_CHARS = int(os.getenv("MAX_TEXT_INPUT_CHARS", 25000))

    ALLOWED_PDF_EXTENSIONS = {".pdf"}
    ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
    ALLOWED_HTML_EXTENSIONS = {".html", ".htm", ".txt"}

    # Temporary upload cache directory (cleared automatically after processing)
    UPLOAD_FOLDER = BASE_DIR / "temp_uploads"
    UPLOAD_FOLDER.mkdir(exist_ok=True)

    # Local Ollama AI settings
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    OLLAMA_TEXT_MODEL = os.getenv("OLLAMA_TEXT_MODEL", "llama3.2:1b")
    OLLAMA_VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "moondream")
    OLLAMA_REQUEST_TIMEOUT = int(os.getenv("OLLAMA_REQUEST_TIMEOUT", 90))  # seconds

    # Alternative lightweight models suggested for low-resource machines
    SUGGESTED_TEXT_MODELS = [
        {"name": "llama3.2:1b", "size": "1.3 GB", "ram": "4 GB", "description": "Ultra-lightweight, fast text simplification (Installed / Default)"},
        {"name": "llama3.2", "size": "2.0 GB", "ram": "6 GB", "description": "Recommended balanced local model for simplification"},
        {"name": "phi3:mini", "size": "2.3 GB", "ram": "6 GB", "description": "Strong reasoning & simplification in small footprint"},
        {"name": "mistral:7b", "size": "4.1 GB", "ram": "8 GB+", "description": "High quality text processing"},
        {"name": "qwen2.5:3b", "size": "1.9 GB", "ram": "4-6 GB", "description": "Multilingual and highly capable small model"}
    ]

    SUGGESTED_VISION_MODELS = [
        {"name": "moondream", "size": "1.7 GB", "ram": "4 GB", "description": "Fast, lightweight vision model for image descriptions & alt-text (Installed / Default)"},
        {"name": "llama3.2-vision:11b", "size": "7.9 GB", "ram": "12 GB+ / GPU", "description": "High quality image descriptions & alt-text"},
        {"name": "llava:7b", "size": "4.5 GB", "ram": "8 GB+", "description": "Widely supported vision model for image reading"},
        {"name": "llava:13b", "size": "8.0 GB", "ram": "16 GB+", "description": "Detailed image accessibility parsing"}
    ]

    # OCR Settings
    TESSERACT_CMD = os.getenv("TESSERACT_CMD", "")

    # SSRF Protection for URL Scanner
    SSRF_MAX_REDIRECTS = 3
    SSRF_REQUEST_TIMEOUT = 10  # seconds
    SSRF_MAX_RESPONSE_SIZE = 1 * 1024 * 1024  # 1 MB max for fetched HTML
