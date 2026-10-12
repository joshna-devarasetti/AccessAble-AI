"""
Unit tests for Ollama Local AI Service (Mocked AI communication).
Ensures test suite runs reliably offline without downloading huge weights.
"""

from unittest.mock import patch, MagicMock
import pytest
import requests
from services.ollama_service import OllamaService, OllamaServiceError


def test_health_check_connection_error():
    with patch("requests.get", side_effect=requests.exceptions.ConnectionError("Offline")):
        status = OllamaService.check_health("http://127.0.0.1:11434")
        assert status["running"] is False
        assert "not reachable" in status["error"]
        assert "setup_guide" in status


def test_health_check_running_models():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "models": [{"name": "llama3.2:1b"}, {"name": "moondream:latest"}]
    }

    with patch("requests.get", return_value=mock_resp):
        status = OllamaService.check_health("http://127.0.0.1:11434")
        assert status["running"] is True
        assert "llama3.2:1b" in status["models"]
        assert "moondream:latest" in status["models"]
        assert status["models_count"] == 2


def test_verify_model_available():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"models": [{"name": "llama3.2:1b"}, {"name": "moondream:latest"}]}

    with patch("requests.get", return_value=mock_resp):
        # 1. Exact match for installed model llama3.2:1b
        ready, err = OllamaService.verify_model_available("http://127.0.0.1:11434", "llama3.2:1b")
        assert ready is True
        assert err is None

        # 2. Canonical latest match for moondream
        ready_vision, err_vision = OllamaService.verify_model_available("http://127.0.0.1:11434", "moondream")
        assert ready_vision is True
        assert err_vision is None

        # 3. Model 'llama3.2' is NOT installed when only 'llama3.2:1b' is present
        ready_missing, err_missing = OllamaService.verify_model_available("http://127.0.0.1:11434", "llama3.2")
        assert ready_missing is False
        assert "not installed" in err_missing
        assert "llama3.2:1b" in err_missing

        # 4. Completely nonexistent model
        ready_none, err_none = OllamaService.verify_model_available("http://127.0.0.1:11434", "nonexistent-model")
        assert ready_none is False
        assert "not installed" in err_none


def test_simplify_text_mocked_success():
    mock_get = MagicMock()
    mock_get.status_code = 200
    mock_get.json.return_value = {"models": [{"name": "llama3.2:1b"}]}

    mock_post = MagicMock()
    mock_post.status_code = 200
    mock_post.json.return_value = {
        "message": {"content": "This is plain and simple English."},
        "total_duration": 500000000,
        "eval_count": 12
    }

    with patch("requests.get", return_value=mock_get), patch("requests.post", return_value=mock_post):
        res = OllamaService.simplify_text("Complex academic text here.", model_name="llama3.2:1b")
        assert res["success"] is True
        assert res["simplified_text"] == "This is plain and simple English."
        assert res["is_ai_generated"] is True
        assert res["model_used"] == "llama3.2:1b"


def test_simplify_text_strips_preamble_and_quotes():
    mock_get = MagicMock()
    mock_get.status_code = 200
    mock_get.json.return_value = {"models": [{"name": "llama3.2:1b"}]}

    mock_post = MagicMock()
    mock_post.status_code = 200
    mock_post.json.return_value = {
        "message": {
            "content": "Here is the simplified text:\n\n\"The heart works hard to pump blood.\"\n\nNote: Preserved medical facts."
        },
        "total_duration": 400000000,
        "eval_count": 10
    }

    with patch("requests.get", return_value=mock_get), patch("requests.post", return_value=mock_post):
        res = OllamaService.simplify_text("Complex medical text.", model_name="llama3.2:1b")
        assert res["success"] is True
        assert res["simplified_text"] == "The heart works hard to pump blood."
        assert "Here is" not in res["simplified_text"]
        assert "Note:" not in res["simplified_text"]
        assert not res["simplified_text"].startswith('"')


def test_simplify_text_missing_model_raises_error():
    mock_get = MagicMock()
    mock_get.status_code = 200
    mock_get.json.return_value = {"models": [{"name": "llama3.2:1b"}]}

    with patch("requests.get", return_value=mock_get):
        # Requesting uninstalled 'llama3.2' must raise MODEL_UNAVAILABLE error
        with pytest.raises(OllamaServiceError) as exc_info:
            OllamaService.simplify_text("Some text", model_name="llama3.2")
        assert exc_info.value.error_code == "MODEL_UNAVAILABLE"
        assert "llama3.2" in str(exc_info.value)


def test_simplify_text_timeout():
    mock_get = MagicMock()
    mock_get.status_code = 200
    mock_get.json.return_value = {"models": [{"name": "llama3.2:1b"}]}

    with patch("requests.get", return_value=mock_get), patch("requests.post", side_effect=requests.exceptions.Timeout):
        with pytest.raises(OllamaServiceError) as exc_info:
            OllamaService.simplify_text("Some text", model_name="llama3.2:1b")
        assert exc_info.value.error_code == "TIMEOUT"


def test_describe_image_success_standard():
    mock_get = MagicMock()
    mock_get.status_code = 200
    mock_get.json.return_value = {"models": [{"name": "moondream:latest"}]}

    mock_post = MagicMock()
    mock_post.status_code = 200
    mock_post.json.return_value = {
        "message": {"content": "A red apple sits on a wooden table. The background is softly blurred."}
    }

    with patch("requests.get", return_value=mock_get), patch("requests.post", return_value=mock_post):
        res = OllamaService.describe_image(image_b64="fake_b64_data", model_name="moondream", mode="standard")
        assert res["success"] is True
        assert res["model_used"] == "moondream"
        assert res["suggested_alt_text"] == "A red apple sits on a wooden table."
        assert "The background is softly blurred" in res["raw_description"]


def test_describe_image_success_concise():
    mock_get = MagicMock()
    mock_get.status_code = 200
    mock_get.json.return_value = {"models": [{"name": "moondream:latest"}]}

    mock_post = MagicMock()
    mock_post.status_code = 200
    mock_post.json.return_value = {
        "message": {"content": "A golden retriever sitting in a sunny grassy park."}
    }

    with patch("requests.get", return_value=mock_get), patch("requests.post", return_value=mock_post):
        res = OllamaService.describe_image(image_b64="fake_b64_data", model_name="moondream", mode="concise")
        assert res["success"] is True
        assert res["suggested_alt_text"] == "A golden retriever sitting in a sunny grassy park."
        assert res["raw_description"] == "A golden retriever sitting in a sunny grassy park."


def test_describe_image_cleans_token_artifacts():
    mock_get = MagicMock()
    mock_get.status_code = 200
    mock_get.json.return_value = {"models": [{"name": "moondream:latest"}]}

    mock_post = MagicMock()
    mock_post.status_code = 200
    mock_post.json.return_value = {
        "message": {"content": "!!!IMAGE!!! A diagram showing photosynthesis stages."}
    }

    with patch("requests.get", return_value=mock_get), patch("requests.post", return_value=mock_post):
        res = OllamaService.describe_image(image_b64="fake_b64_data", model_name="moondream")
        assert res["success"] is True
        assert "!!!IMAGE!!!" not in res["raw_description"]
        assert "photosynthesis stages" in res["suggested_alt_text"]


def test_describe_image_missing_vision_model():
    mock_get = MagicMock()
    mock_get.status_code = 200
    mock_get.json.return_value = {"models": [{"name": "llama3.2:1b"}]}

    with patch("requests.get", return_value=mock_get):
        with pytest.raises(OllamaServiceError) as exc_info:
            OllamaService.describe_image(image_b64="fake_b64", model_name="moondream")
        assert exc_info.value.error_code == "VISION_MODEL_UNAVAILABLE"
        assert "moondream" in str(exc_info.value)


def test_describe_image_empty_response():
    mock_get = MagicMock()
    mock_get.status_code = 200
    mock_get.json.return_value = {"models": [{"name": "moondream:latest"}]}

    mock_post = MagicMock()
    mock_post.status_code = 200
    mock_post.json.return_value = {"message": {"content": ""}}

    with patch("requests.get", return_value=mock_get), patch("requests.post", return_value=mock_post):
        with pytest.raises(OllamaServiceError) as exc_info:
            OllamaService.describe_image(image_b64="fake_b64", model_name="moondream")
        assert exc_info.value.error_code == "EMPTY_RESPONSE"

