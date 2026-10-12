"""
AccessAble AI - Digital Accessibility Assistant
Main Flask Application Server
"""

import os
import io
import logging
from typing import Dict, Any
from flask import Flask, render_template, request, jsonify, make_response
from werkzeug.exceptions import RequestEntityTooLarge

from config import Config
from services import (
    PDFService, PDFProcessingError,
    OCRService,
    TextService,
    SpeechService,
    ImageService, ImageValidationError,
    AccessibilityService, SSRFValidationError,
    OllamaService, OllamaServiceError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("accessable_ai")


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Security Headers
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    # -------------------------------------------------------------
    # Page Routes
    # -------------------------------------------------------------
    @app.route("/")
    def index():
        return render_template("index.html")

    # -------------------------------------------------------------
    # System Status & Health Endpoint
    # -------------------------------------------------------------
    @app.route("/api/status", methods=["GET"])
    def get_system_status():
        ollama_status = OllamaService.check_health(app.config["OLLAMA_BASE_URL"])
        ocr_status = OCRService.check_availability()
        speech_caps = SpeechService.get_speech_capabilities()

        # Check configured model statuses
        text_model = request.args.get("text_model", app.config["OLLAMA_TEXT_MODEL"])
        vision_model = request.args.get("vision_model", app.config["OLLAMA_VISION_MODEL"])

        text_model_ready, text_err = OllamaService.verify_model_available(
            app.config["OLLAMA_BASE_URL"], text_model
        )
        vision_model_ready, vision_err = OllamaService.verify_model_available(
            app.config["OLLAMA_BASE_URL"], vision_model
        )

        return jsonify({
            "success": True,
            "application": "AccessAble AI",
            "version": "1.0.0",
            "ollama": {
                "running": ollama_status["running"],
                "base_url": app.config["OLLAMA_BASE_URL"],
                "installed_models": ollama_status["models"],
                "configured_text_model": text_model,
                "text_model_ready": text_model_ready,
                "text_model_error": text_err,
                "configured_vision_model": vision_model,
                "vision_model_ready": vision_model_ready,
                "vision_model_error": vision_err,
                "suggested_text_models": app.config["SUGGESTED_TEXT_MODELS"],
                "suggested_vision_models": app.config["SUGGESTED_VISION_MODELS"],
                "setup_guide": OllamaService.get_setup_instructions(text_model)
            },
            "ocr": {
                "available": ocr_status["available"],
                "version": ocr_status.get("version"),
                "instructions": ocr_status.get("instructions")
            },
            "speech": speech_caps,
            "limits": {
                "max_pdf_mb": app.config["MAX_PDF_SIZE_MB"],
                "max_image_mb": app.config["MAX_IMAGE_SIZE_MB"],
                "max_text_chars": app.config["MAX_TEXT_INPUT_CHARS"]
            }
        })

    # -------------------------------------------------------------
    # Document Processing (PDF & OCR)
    # -------------------------------------------------------------
    @app.route("/api/pdf/extract", methods=["POST"])
    def extract_pdf():
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file uploaded. Please select a PDF file."}), 400

        file = request.files["file"]
        if not file or not file.filename:
            return jsonify({"success": False, "error": "No file selected."}), 400

        filename = file.filename
        ext = os.path.splitext(filename)[1].lower()
        if ext not in app.config["ALLOWED_PDF_EXTENSIONS"]:
            return jsonify({
                "success": False,
                "error": f"Invalid file format '{ext}'. Only PDF documents (.pdf) are supported."
            }), 400

        try:
            file_bytes = file.read()
            size_mb = len(file_bytes) / (1024 * 1024)
            if size_mb > app.config["MAX_PDF_SIZE_MB"]:
                return jsonify({
                    "success": False,
                    "error": f"File size ({size_mb:.1f} MB) exceeds limit of {app.config['MAX_PDF_SIZE_MB']} MB."
                }), 413

            # Extract standard selectable text
            pdf_result = PDFService.extract_text_from_bytes(file_bytes, filename=filename)

            # Check if user requested OCR for scanned documents
            run_ocr = request.form.get("run_ocr", "0").lower() in ("1", "true", "yes")

            if pdf_result["requires_ocr"]:
                if run_ocr:
                    ocr_res = OCRService.ocr_pdf_bytes(file_bytes)
                    if ocr_res["success"] and ocr_res["text"]:
                        pdf_result["text"] = ocr_res["text"]
                        pdf_result["ocr_performed"] = True
                        pdf_result["total_words"] = ocr_res["total_words"]
                        pdf_result["total_chars"] = len(ocr_res["text"])
                    else:
                        pdf_result["ocr_error"] = ocr_res.get("error")
                        pdf_result["ocr_instructions"] = ocr_res.get("instructions")
                else:
                    pdf_result["ocr_instructions"] = OCRService.get_windows_install_instructions()

            # Analyze readability of extracted text
            if pdf_result["text"]:
                readability = TextService.analyze_readability(pdf_result["text"])
                pdf_result["readability"] = readability
            else:
                pdf_result["readability"] = None

            return jsonify(pdf_result)

        except PDFProcessingError as e:
            return jsonify({"success": False, "error": str(e)}), 400
        except Exception as e:
            logger.exception("Unexpected error processing PDF: %s", str(e))
            return jsonify({"success": False, "error": "Internal error processing the PDF."}), 500

    # -------------------------------------------------------------
    # Text Analysis & Simplification
    # -------------------------------------------------------------
    @app.route("/api/text/analyze", methods=["POST"])
    def analyze_text():
        data = request.get_json(silent=True) or {}
        text = data.get("text", "")
        if not text or not text.strip():
            return jsonify({"success": False, "error": "Text cannot be empty."}), 400

        metrics = TextService.analyze_readability(text)
        return jsonify({"success": True, "readability": metrics})

    @app.route("/api/text/simplify", methods=["POST"])
    def simplify_text():
        data = request.get_json(silent=True) or {}
        text = data.get("text", "").strip()
        model_name = data.get("model") or app.config["OLLAMA_TEXT_MODEL"]
        allow_fallback = data.get("allow_fallback", False)

        if not text:
            return jsonify({"success": False, "error": "Please provide text to simplify."}), 400

        if len(text) > app.config["MAX_TEXT_INPUT_CHARS"]:
            return jsonify({
                "success": False,
                "error": f"Text length ({len(text)} characters) exceeds maximum allowed {app.config['MAX_TEXT_INPUT_CHARS']} characters."
            }), 400

        try:
            ai_result = OllamaService.simplify_text(
                text=text,
                base_url=app.config["OLLAMA_BASE_URL"],
                model_name=model_name,
                timeout=app.config["OLLAMA_REQUEST_TIMEOUT"]
            )

            # Analyze reading level before & after
            before_metrics = TextService.analyze_readability(text)
            after_metrics = TextService.analyze_readability(ai_result["simplified_text"])

            ai_result["before_readability"] = before_metrics
            ai_result["after_readability"] = after_metrics
            return jsonify(ai_result)

        except OllamaServiceError as e:
            # If AI is unavailable and fallback was explicitly requested
            if allow_fallback:
                fallback_result = TextService.rule_based_simplify(text)
                fallback_result["warning"] = f"Local AI model was not available ({e.message}). Generated using non-AI rule-based plain English helper."
                fallback_result["setup_guide"] = e.setup_instructions or OllamaService.get_setup_instructions(model_name)
                return jsonify(fallback_result)

            return jsonify({
                "success": False,
                "error": e.message,
                "error_code": e.error_code,
                "setup_guide": e.setup_instructions or OllamaService.get_setup_instructions(model_name),
                "can_use_rule_based_fallback": True
            }), 503

        except Exception as e:
            logger.exception("Text simplification error: %s", str(e))
            return jsonify({"success": False, "error": f"Simplification failed: {str(e)}"}), 500

    @app.route("/api/text/fallback-simplify", methods=["POST"])
    def rule_based_fallback():
        """Explicitly labeled non-AI rule-based simplification."""
        data = request.get_json(silent=True) or {}
        text = data.get("text", "").strip()
        if not text:
            return jsonify({"success": False, "error": "Please provide text to simplify."}), 400

        result = TextService.rule_based_simplify(text)
        return jsonify(result)

    # -------------------------------------------------------------
    # Image Accessibility & Descriptions
    # -------------------------------------------------------------
    @app.route("/api/image/describe", methods=["POST"])
    def describe_image():
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No image file uploaded."}), 400

        file = request.files["file"]
        if not file or not file.filename:
            return jsonify({"success": False, "error": "No image selected."}), 400

        mode = request.form.get("mode", "standard")
        vision_model = request.form.get("model") or app.config["OLLAMA_VISION_MODEL"]

        try:
            image_bytes = file.read()
            prep_result = ImageService.validate_and_prepare(
                image_bytes,
                filename=file.filename,
                max_size_mb=app.config["MAX_IMAGE_SIZE_MB"]
            )

            # Call local vision model
            vision_result = OllamaService.describe_image(
                image_b64=prep_result["base64_data"],
                base_url=app.config["OLLAMA_BASE_URL"],
                model_name=vision_model,
                mode=mode,
                timeout=app.config["OLLAMA_REQUEST_TIMEOUT"]
            )

            response_data = {
                "success": True,
                "image_meta": {
                    "filename": prep_result["filename"],
                    "width": prep_result["width"],
                    "height": prep_result["height"],
                    "mime_type": prep_result["mime_type"],
                    "size_kb": prep_result["size_kb"]
                },
                "data_uri": prep_result["data_uri"],
                "suggested_alt_text": vision_result["suggested_alt_text"],
                "description": vision_result["raw_description"],
                "model_used": vision_result["model_used"],
                "is_ai_generated": True,
                "disclaimer": vision_result["disclaimer"]
            }
            return jsonify(response_data)

        except ImageValidationError as e:
            return jsonify({"success": False, "error": str(e)}), 400
        except OllamaServiceError as e:
            return jsonify({
                "success": False,
                "error": e.message,
                "error_code": e.error_code,
                "setup_guide": e.setup_instructions or OllamaService.get_setup_instructions(vision_model)
            }), 503
        except Exception as e:
            logger.exception("Image description error: %s", str(e))
            return jsonify({"success": False, "error": f"Image processing failed: {str(e)}"}), 500

    # -------------------------------------------------------------
    # Speech Synthesis Helper (Chunking)
    # -------------------------------------------------------------
    @app.route("/api/speech/chunk", methods=["POST"])
    def chunk_speech():
        data = request.get_json(silent=True) or {}
        text = data.get("text", "")
        chunks = SpeechService.chunk_text_for_speech(text)
        return jsonify({
            "success": True,
            "chunks": chunks,
            "total_chunks": len(chunks)
        })

    # -------------------------------------------------------------
    # Website & HTML Accessibility Checker
    # -------------------------------------------------------------
    @app.route("/api/accessibility/check-html", methods=["POST"])
    def check_html():
        html_content = ""
        source_name = "HTML Input"

        if "file" in request.files:
            file = request.files["file"]
            if file and file.filename:
                source_name = file.filename
                html_bytes = file.read()
                html_content = html_bytes.decode("utf-8", errors="replace")
        else:
            data = request.get_json(silent=True) or {}
            html_content = data.get("html", "")
            source_name = data.get("source_name", "Pasted Code Snippet")

        if not html_content or not html_content.strip():
            return jsonify({"success": False, "error": "Please provide HTML content or upload an HTML file."}), 400

        result = AccessibilityService.analyze_html(html_content, source_name=source_name)
        return jsonify(result)

    @app.route("/api/accessibility/check-url", methods=["POST"])
    def check_url():
        data = request.get_json(silent=True) or {}
        url = data.get("url", "").strip()

        if not url:
            return jsonify({"success": False, "error": "URL cannot be empty."}), 400

        # Prepend https:// if omitted
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"

        try:
            fetched_html = AccessibilityService.fetch_url_safely(
                url,
                max_size_bytes=app.config["SSRF_MAX_RESPONSE_SIZE"],
                timeout_sec=app.config["SSRF_REQUEST_TIMEOUT"]
            )
            result = AccessibilityService.analyze_html(fetched_html, source_name=url)
            result["scanned_url"] = url
            return jsonify(result)

        except SSRFValidationError as e:
            return jsonify({
                "success": False,
                "error": f"Security restriction: {str(e)}",
                "is_security_block": True
            }), 400
        except Exception as e:
            logger.exception("Error checking URL: %s", str(e))
            return jsonify({"success": False, "error": f"Failed to scan URL: {str(e)}"}), 500

    # -------------------------------------------------------------
    # Accessible Learning Support Module
    # -------------------------------------------------------------
    @app.route("/api/learning/generate", methods=["POST"])
    def generate_learning():
        data = request.get_json(silent=True) or {}
        text = data.get("text", "").strip()
        model_name = data.get("model") or app.config["OLLAMA_TEXT_MODEL"]

        if not text:
            return jsonify({"success": False, "error": "Please provide educational material to process."}), 400

        try:
            result = OllamaService.generate_learning_materials(
                text=text,
                base_url=app.config["OLLAMA_BASE_URL"],
                model_name=model_name,
                timeout=app.config["OLLAMA_REQUEST_TIMEOUT"]
            )
            return jsonify(result)
        except OllamaServiceError as e:
            return jsonify({
                "success": False,
                "error": e.message,
                "error_code": e.error_code,
                "setup_guide": e.setup_instructions or OllamaService.get_setup_instructions(model_name)
            }), 503
        except Exception as e:
            logger.exception("Learning module error: %s", str(e))
            return jsonify({"success": False, "error": str(e)}), 500

    # -------------------------------------------------------------
    # Error Handlers
    # -------------------------------------------------------------
    @app.errorhandler(RequestEntityTooLarge)
    def handle_oversized_request(e):
        return jsonify({
            "success": False,
            "error": "The uploaded file or request exceeds the maximum allowed payload size."
        }), 413

    @app.errorhandler(404)
    def handle_404(e):
        if request.path.startswith("/api/"):
            return jsonify({"success": False, "error": "Endpoint not found."}), 404
        return render_template("index.html"), 404

    @app.errorhandler(500)
    def handle_500(e):
        logger.error("Unhandled 500 error: %s", str(e))
        return jsonify({"success": False, "error": "An internal server error occurred."}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    logger.info("Starting AccessAble AI server on http://127.0.0.1:%s", port)
    app.run(host="127.0.0.1", port=port, debug=False)
