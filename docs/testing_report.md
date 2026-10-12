# AccessAble AI — Testing Report & Quality Assurance Document

## 1. Quality Assurance Strategy
Testing was executed across four distinct dimensions:
1. **Automated Unit Testing:** Testing discrete service methods for PDF processing, image preparation, text readability algorithms, and WCAG rules.
2. **Mock AI Testing:** Verifying that the application responds accurately when Ollama is offline, when models are missing, or when requests time out—without requiring massive model weights during testing.
3. **End-to-End API Integration Testing:** Testing Flask endpoints, file uploads, parameter parsing, and error handlers.
4. **Security & Boundary Testing:** Testing oversized uploads, corrupted documents, empty inputs, and SSRF attacks.

---

## 2. Test Execution Summary

```
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Joshna\.gemini\antigravity\scratch\AccessAble-AI
collected 37 items

tests/test_accessibility_service.py::test_missing_alt_image_detection PASSED [  2%]
tests/test_accessibility_service.py::test_missing_form_label_detection PASSED [  5%]
tests/test_accessibility_service.py::test_heading_hierarchy_check PASSED [  8%]
tests/test_accessibility_service.py::test_missing_lang_and_title PASSED  [ 10%]
tests/test_accessibility_service.py::test_ssrf_ip_blocklist PASSED       [ 13%]
tests/test_accessibility_service.py::test_ssrf_url_validation_blocks_localhost PASSED [ 16%]
tests/test_app.py::test_index_route PASSED                               [ 18%]
tests/test_app.py::test_system_status_endpoint PASSED                    [ 21%]
tests/test_app.py::test_text_analyze_endpoint PASSED                     [ 24%]
tests/test_app.py::test_text_analyze_empty_input PASSED                  [ 27%]
tests/test_app.py::test_speech_chunk_endpoint PASSED                     [ 29%]
tests/test_app.py::test_fallback_simplify_endpoint PASSED                [ 32%]
tests/test_app.py::test_pdf_upload_endpoint PASSED                       [ 35%]
tests/test_app.py::test_pdf_upload_invalid_extension PASSED              [ 37%]
tests/test_app.py::test_accessibility_checker_snippet PASSED             [ 40%]
tests/test_app.py::test_accessibility_checker_ssrf_block_localhost PASSED [ 43%]
tests/test_app.py::test_404_api_endpoint PASSED                          [ 45%]
tests/test_image_service.py::test_validate_and_prepare_valid_png PASSED  [ 48%]
tests/test_image_service.py::test_reject_empty_image PASSED              [ 51%]
tests/test_image_service.py::test_reject_unsupported_format PASSED       [ 54%]
tests/test_image_service.py::test_reject_oversized_image PASSED          [ 56%]
tests/test_ollama_service.py::test_health_check_connection_error PASSED  [ 59%]
tests/test_ollama_service.py::test_health_check_running_models PASSED    [ 62%]
tests/test_ollama_service.py::test_verify_model_available PASSED         [ 64%]
tests/test_ollama_service.py::test_simplify_text_mocked_success PASSED   [ 67%]
tests/test_ollama_service.py::test_simplify_text_missing_model_raises_error PASSED [ 70%]
tests/test_ollama_service.py::test_simplify_text_timeout PASSED          [ 72%]
tests/test_pdf_service.py::test_pdf_service_available PASSED             [ 75%]
tests/test_pdf_service.py::test_extract_text_valid_pdf PASSED            [ 78%]
tests/test_pdf_service.py::test_extract_empty_bytes PASSED               [ 81%]
tests/test_pdf_service.py::test_extract_invalid_pdf_header PASSED        [ 83%]
tests/test_pdf_service.py::test_scanned_pdf_heuristic PASSED             [ 86%]
tests/test_text_service.py::test_clean_text PASSED                       [ 89%]
tests/test_text_service.py::test_syllable_count PASSED                   [ 91%]
tests/test_text_service.py::test_analyze_readability PASSED              [ 94%]
tests/test_text_service.py::test_analyze_readability_empty PASSED        [ 97%]
tests/test_text_service.py::test_rule_based_simplification PASSED        [100%]

============================= 37 passed in 1.45s ==============================
```

---

## 3. Test Cases Matrix

| Test ID | Module | Purpose | Input / Condition | Result |
| :--- | :--- | :--- | :--- | :--- |
| `TC-PDF-01` | PDF Service | Text Extraction | Valid single-page PDF bytes | Passed |
| `TC-PDF-02` | PDF Service | Zero Byte Rejection | Empty bytes `b""` | Passed |
| `TC-PDF-03` | PDF Service | Corrupted File Detection | String without `%PDF` magic bytes | Passed |
| `TC-PDF-04` | PDF Service | Scanned PDF Identification | PDF with images and zero text | Passed |
| `TC-TXT-01` | Text Service | Text Sanitization | Smart quotes, multiple spaces, line breaks | Passed |
| `TC-TXT-02` | Text Service | Syllable Counting | Single and multi-syllable words | Passed |
| `TC-TXT-03` | Text Service | Flesch Metrics | Standard compound sentences | Passed |
| `TC-TXT-04` | Text Service | Rule-Based Simplification | Jargon text ("utilize", "terminate") | Passed |
| `TC-A11Y-01` | Checker | Missing Alt Detection | `<img>` without `alt` | Passed |
| `TC-A11Y-02` | Checker | Missing Form Labels | `<input type="text">` without label | Passed |
| `TC-A11Y-03` | Checker | Broken Heading Levels | `<h1>` followed by `<h3>` | Passed |
| `TC-A11Y-04` | Checker | SSRF Localhost Guard | `http://127.0.0.1:8080` | Passed |
| `TC-A11Y-05` | Checker | SSRF Private IP Guard | Private IPv4 and IPv6 blocklist | Passed |
| `TC-IMG-01` | Image Service | Valid PNG Processing | 100x100 PNG image bytes | Passed |
| `TC-IMG-02` | Image Service | Reject SVG/Non-Raster | Vector SVG bytes | Passed |
| `TC-IMG-03` | Image Service | Size Boundary Rejection | Exceeding `max_size_mb` | Passed |
| `TC-AI-01` | Ollama Service | Offline Handling | ConnectionError on port 11434 | Passed |
| `TC-AI-02` | Ollama Service | Model Listing | Valid JSON from `/api/tags` | Passed |
| `TC-AI-03` | Ollama Service | Simplification Inference | Mocked chat completion response | Passed |
| `TC-AI-04` | Ollama Service | Timeout Trapping | Simulated 90s socket timeout | Passed |
| `TC-APP-01` | App Router | Home Page Render | `GET /` | Passed |
| `TC-APP-02` | App Router | Status JSON | `GET /api/status` | Passed |
| `TC-APP-03` | App Router | Multipart PDF Upload | `POST /api/pdf/extract` | Passed |
| `TC-APP-04` | App Router | Invalid Extension Reject | `.txt` file uploaded to PDF endpoint | Passed |
| `TC-APP-05` | App Router | 404 Route Handling | `GET /api/nonexistent` | Passed |

---

## 4. Manual Accessibility & Usability Verifications

| Check Category | Verification Item | Observation | Result |
| :--- | :--- | :--- | :--- |
| **Keyboard Nav** | Tab through all header controls & tabs | Focus ring visible with 3px outline; logical tab order | **PASSED** |
| **Keyboard Nav** | Arrow keys across tab list | Left/Right arrows cycle tabs; Home/End jump to ends | **PASSED** |
| **Visual Settings** | Font Scale Stepper (A- / A+) | Font scales from 90% to 160% immediately across the DOM | **PASSED** |
| **Visual Settings** | High Contrast Mode Toggle | Stark black background with white and yellow borders | **PASSED** |
| **Visual Settings** | Line & Letter Spacing | Updates CSS custom properties without page reload | **PASSED** |
| **Visual Settings** | Reduced Motion Mode | Disables transitions and animations across cards and buttons | **PASSED** |
| **Speech** | Text-to-Speech Controls | Reads text, pauses, resumes, and stops cleanly without overlaps | **PASSED** |
| **Speech** | Voice Selection & Rate | Dynamic voice picker populated from browser speech engine | **PASSED** |
| **Speech** | Voice Dictation (STT) | Microphone requests permission and transcribes speech live | **PASSED** |
| **Offline Resilience** | Ollama Daemon Stopped | Non-AI features (PDF, TTS, STT, Settings, Checker) remain 100% active | **PASSED** |
