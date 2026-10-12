# AccessAble AI — End-User Guide & Operational Manual

Welcome to **AccessAble AI**! This guide walks you through every feature of your digital accessibility assistant.

---

## 1. Quick Navigation & Keyboard Shortcuts

AccessAble AI is completely operable using only your keyboard:

| Action | Keystroke | Description |
| :--- | :--- | :--- |
| **Skip to Main Content** | `Tab` (on initial page load) + `Enter` | Skips navigation directly to the workspace |
| **Navigate Tabs** | `Left Arrow` / `Right Arrow` | Cycles between feature modules |
| **First / Last Tab** | `Home` / `End` | Jumps to Document Reader or AI Setup Guide |
| **Activate Button / Control** | `Enter` or `Space` | Triggers the focused button or toggle |
| **Toggle High Contrast** | Click "High Contrast" or navigate in header | Switches between Standard and High-Contrast Black |
| **Increase / Decrease Font** | Click `A+` or `A-` in header | Scales text from 90% to 160% in real-time |

---

## 2. Using the Document Reader

1. Click on the **Document Reader** tab.
2. Drag and drop your `.pdf` file into the upload zone, or click **browse files**.
3. The application will extract all text and calculate:
   - Total pages and word count.
   - Flesch Reading Ease score (0 to 100).
   - Estimated U.S. reading grade level.
4. If your PDF is a scanned document (image-only), AccessAble AI will alert you. Enable the **"Enable Local OCR"** checkbox to read scanned pages if you have Tesseract installed.
5. Click **Read Aloud** to listen to the extracted text immediately, or **Simplify in AI** to send the document into the AI Text Simplifier.

---

## 3. Simplifying Complex Text

1. Click the **Text Simplification** tab.
2. Paste complex legal, academic, or technical text, or click **Load Sample Text**.
3. Choose your local AI model from the dropdown (default: `llama3.2`).
4. Click **Simplify Text with Local AI**.
5. Once complete, view the simplified text side-by-side with the original, alongside before-and-after reading levels.
6. Click the **Copy** or **Read Aloud** button to use the result.
7. *If your local AI model is offline:* A friendly notification appears offering the built-in **Rule-Based Text Helper (Non-AI Fallback)**, allowing you to simplify text with deterministic dictionary matching without any AI running.

---

## 4. Using the Speech Studio

### Text-to-Speech (Read Aloud)
1. Navigate to the **Speech Studio** tab.
2. Type or paste any text into the "Text to Read Aloud" box.
3. Select your preferred voice from the dropdown.
4. Adjust speech speed (0.5x to 2.0x) and pitch.
5. Click **Read Aloud**. You can pause, resume, or stop playback at any time.

### Speech-to-Text (Voice Dictation)
1. Under the Speech-to-Text section, click **Start Listening**.
2. Allow microphone access when prompted by your browser.
3. Speak clearly into your microphone. Words appear in real-time in the transcript area.
4. Click **Stop** when finished.
5. Click **Send to Simplification** to simplify your dictated notes, or **Read Back** to hear them.

---

## 5. Generating Image Alt-Text & Descriptions

1. Navigate to the **Image Accessibility** tab.
2. Drag and drop an image (PNG, JPEG, WebP, BMP) into the drop zone.
3. Choose your desired detail level:
   - **Standard:** Recommended alt-text, visual composition, and visible signs/text.
   - **Concise:** 1-sentence screen reader alternative.
   - **Comprehensive:** Deep accessibility breakdown of visual elements.
4. Click **Generate Alt-Text**.
5. Copy the generated alt-text directly into your HTML `<img alt="...">` attribute.

---

## 6. Auditing Webpages with the Accessibility Checker

1. Navigate to the **Accessibility Checker** tab.
2. Select your input method:
   - **HTML Snippet:** Paste code directly (or click **Load Problematic Sample** to test).
   - **Upload HTML File:** Select an `.html` file from your computer.
   - **Safe URL Scan:** Enter any public `https://` webpage address.
3. Click **Audit**.
4. Review your Accessibility Score (0-100) and severity breakdown:
   - **Critical:** Missing alt text, form inputs lacking labels, empty buttons, removed focus rings.
   - **Serious:** Missing `<main>` landmark, missing `<title>`, missing `<html lang>`.
   - **Moderate:** Skipped heading levels (H1 to H3), empty links, missing table headers.
   - **Minor:** Multiple H1 headings.
5. Click any issue to expand the offending code snippet, an explanation of why it harms accessibility, and the exact suggested code correction.

---

## 7. Display & Accessibility Settings

Customize your viewing experience in the **Display Settings** tab:
- **Font Scale:** Scalable from 90% up to 160%.
- **Color Themes:**
  - *Light Theme:* Modern calm slate and blue.
  - *Dark Theme:* Low-glare night palette.
  - *High Contrast Dark:* Pure black and stark white (WCAG AAA).
  - *High Contrast Yellow on Black:* Maximum readability for low-vision users.
- **Line Height:** 1.5 (Standard), 1.8 (Relaxed), or 2.1 (Dyslexia-friendly).
- **Letter Spacing:** Standard, Slight (+0.05em), or Wide (+0.12em).
- **Typography:** Choose between System Sans, Dyslexia-Optimized, Serif, or Monospace.
- **Reduced Motion:** Eliminates all transition animations for vestibular comfort.
- **Enhanced Focus Rings:** Thick, high-contrast outlines on all active controls.
- **Reset to Defaults:** Instantly restores standard settings.

All settings persist across browser sessions in `localStorage`.
