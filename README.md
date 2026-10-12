# AccessAble AI — Digital Accessibility Assistant
> A privacy-first, local-AI-powered digital accessibility assistant and WCAG evaluation platform.

AccessAble AI empowers individuals with visual impairments, cognitive/learning differences, dyslexia, hearing challenges, and motor limitations to access, understand, and navigate digital documents with ease. Built with 100% offline-capable local intelligence via Ollama, AccessAble AI eliminates third-party cloud API costs, subscriptions, and data leaks.

---

## 🌟 Key Application Features

- 📄 **Accessible Document Reader:** Extracts text and structural metadata from native and scanned PDF files using PyMuPDF and local Tesseract OCR. Computes readability scores on the fly without storing files.
- 🧠 **Real Local AI Text Simplification:** Uses your local instruction-following language model (e.g., `llama3.2` or `phi3`) to rewrite complex academic and legal language into simple English while preserving facts, dates, numbers, and warnings.
- 🛡️ **Explicit Non-AI Rule Fallback:** When Ollama is offline or no model is loaded, an explicitly labeled deterministic plain-English helper replaces jargon and breaks long sentences without pretending to be AI.
- 🎙️ **Speech Studio (TTS & STT):** Natural Text-to-Speech with pause/resume, speed, pitch, and voice controls, plus intelligent sentence chunking to eliminate browser speech timeouts. Native voice dictation transcribes speech in real time.
- 🖼️ **Image Accessibility & Alt-Text:** Generates concise, screen-reader-ready alt-text and detailed visual descriptions using compatible local vision models (e.g., `llama3.2-vision` or `moondream`).
- 🔍 **WCAG 2.1 Accessibility Checker:** Audits HTML snippets, uploaded files, and live URLs for Level A/AA violations (missing alt text, unlabelled inputs, skipped headings, missing landmarks, removed focus outlines) with multi-hop SSRF security defenses.
- 📚 **Accessible Learning Support:** Converts complex textbook notes into plain-English study summaries, terminology glossaries, and interactive practice review quizzes.
- ⚙️ **Instant Accessibility Toolbar:** Real-time font scaling (90%-160%), 4 color themes (including high-contrast dark and yellow-on-black), line height, letter spacing, dyslexia-friendly fonts, and reduced motion toggles that persist across sessions.

---

## 🚀 Quickstart Guide (Windows & PowerShell)

### Prerequisites
- **Python 3.11 or newer** (tested with Python 3.13 on Windows)
- **Windows PowerShell** or Command Prompt
- **Ollama** (optional for AI features; non-AI features work 100% without Ollama)

### 1. Clone or Open Workspace
```powershell
Set-Location "C:\Users\Joshna\.gemini\antigravity\scratch\AccessAble-AI"
```

### 2. Set Up Virtual Environment & Dependencies
```powershell
# Create virtual environment
py -3.13 -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. (Optional) Set Up Local AI with Ollama
Ollama runs AI models 100% locally on your computer with zero API keys and zero cloud data leaks.
```powershell
# 1. Verify Ollama is installed (or run: winget install Ollama.Ollama)
ollama --version

# 2. Download the installed text simplification model (1.3 GB)
ollama pull llama3.2:1b

# 3. Download the installed lightweight vision model for image descriptions (1.7 GB)
ollama pull moondream

# Optional alternative vision model for high-RAM machines:
# ollama pull llama3.2-vision
```

### 4. Run the Application
```powershell
# Start the Flask web application
python app.py
```
Open your browser and navigate to:
👉 **`http://127.0.0.1:5000`**

---

## 🧪 Running Automated Tests

Run the complete 47-test suite with pytest:
```powershell
.\venv\Scripts\python.exe -m pytest -v
```

All 47 unit, integration, and security tests run offline and pass with a 100% success rate without requiring cloud APIs or downloaded weights.

---

## 📂 Project Structure

```
AccessAble-AI/
│
├── app.py                      # Main Flask application & REST endpoints
├── config.py                   # Central configuration & hardware profiles
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable configuration template
├── .gitignore                  # Git ignore rules
├── README.md                   # Project overview & documentation
│
├── services/                   # Modular business logic services
│   ├── __init__.py             # Service package exports
│   ├── pdf_service.py          # PyMuPDF document extraction & scanned PDF detection
│   ├── ocr_service.py          # Local Tesseract OCR with Windows setup instructions
│   ├── text_service.py         # Readability metrics & non-AI rule-based fallback
│   ├── speech_service.py       # Web Speech API sentence chunking & capabilities
│   ├── image_service.py        # Image validation, dimension check & base64 encoding
│   ├── accessibility_service.py# WCAG 2.1 auditor & SSRF security filter
│   └── ollama_service.py       # Dedicated Ollama integration & guardrails
│
├── templates/
│   └── index.html              # Accessible, semantic single-page dashboard
│
├── static/
│   ├── style.css               # WCAG AA/AAA CSS styling, themes & scaling
│   └── script.js               # Client-side controller, ARIA live announcer & speech
│
├── tests/                      # Automated test suite (37 tests, 100% pass)
│   ├── conftest.py             # Pytest fixtures & in-memory test PDF generator
│   ├── test_app.py             # Route integration & error handling tests
│   ├── test_pdf_service.py     # PDF text extraction & scanned detection tests
│   ├── test_text_service.py    # Readability formulas & rule fallback tests
│   ├── test_accessibility_service.py # WCAG rules & SSRF security tests
│   ├── test_image_service.py   # Image validation & boundary tests
│   └── test_ollama_service.py  # Mocked local AI inference & timeout tests
│
└── docs/                       # Comprehensive documentation
    ├── project_report.md       # 25-section college tinkering report
    ├── architecture.md         # System architecture & sequence diagrams
    ├── testing_report.md       # Test matrix & verification report
    └── user_guide.md           # End-user operations & keyboard manual
```

---

## 🔒 Security & Privacy Guarantees

1. **Zero Data Exfiltration:** Uploaded files, pasted text, and microphone transcripts never leave your machine.
2. **SSRF Guard:** The URL accessibility checker strictly prohibits loopback (`127.0.0.1`), private RFC 1918 subnets, cloud metadata (`169.254.169.254`), and re-validates each redirect hop.
3. **Prompt Injection Guardrails:** User text submitted for simplification is strictly handled as passive data to rewrite, not instructions to execute.
4. **No Hidden Cloud Fallbacks:** The platform never secretly falls back to paid third-party APIs. If local AI is offline, it offers an explicitly labeled deterministic rule-based helper.

---

## 🎓 College Tinkering Project Evaluation Guide

See [`docs/project_report.md`](docs/project_report.md) for the full 25-section academic and engineering evaluation report, including literature reviews, system architecture, data flow diagrams, and testing methodologies.
