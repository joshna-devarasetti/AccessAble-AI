/**
 * AccessAble AI — Digital Accessibility Assistant
 * Client-Side Application Controller
 * WCAG 2.1 Compliant, Modular Architecture
 */

document.addEventListener("DOMContentLoaded", () => {
  "use strict";

  // =========================================================================
  // STATE MANAGEMENT
  // =========================================================================
  const State = {
    theme: localStorage.getItem("accessable_theme") || "light",
    fontScale: parseFloat(localStorage.getItem("accessable_font_scale")) || 1.0,
    lineHeight: localStorage.getItem("accessable_line_height") || "1.6",
    letterSpacing: localStorage.getItem("accessable_letter_spacing") || "normal",
    fontFamily: localStorage.getItem("accessable_font_family") || "system",
    reducedMotion: localStorage.getItem("accessable_reduced_motion") === "true",
    maxWidth: localStorage.getItem("accessable_max_width") || "1200px",
    
    // System Status
    ollamaRunning: false,
    installedModels: [],
    textModelReady: false,
    visionModelReady: false,
    currentTextModel: "llama3.2:1b",
    currentVisionModel: "moondream",

    // Speech State
    synth: window.speechSynthesis || null,
    voices: [],
    currentUtterance: null,
    speechChunks: [],
    currentChunkIndex: 0,
    isSpeaking: false,
    isPaused: false,

    // Speech Recognition State
    recognition: null,
    isRecording: false,

    // Audit State
    lastAuditIssues: []
  };

  // =========================================================================
  // SCREEN READER LIVE REGION ANNOUNCER
  // =========================================================================
  function announce(message, assertive = false) {
    const regionId = assertive ? "sr-alert" : "sr-announcer";
    const el = document.getElementById(regionId);
    if (el) {
      el.textContent = "";
      setTimeout(() => {
        el.textContent = message;
      }, 50);
    }
  }

  // =========================================================================
  // ACCESSIBILITY & DISPLAY SETTINGS CONTROLLER
  // =========================================================================
  const SettingsController = {
    init() {
      this.applyAll();
      this.bindEvents();
    },

    applyAll() {
      // Apply theme
      document.documentElement.setAttribute("data-theme", State.theme);
      const themeSelect = document.getElementById("setting-theme");
      if (themeSelect) themeSelect.value = State.theme;

      // Apply font scale
      document.documentElement.style.setProperty("--font-scale", State.fontScale);
      const fontDisplay = document.getElementById("font-size-display");
      const fontSlider = document.getElementById("setting-font-size");
      const fontSliderVal = document.getElementById("setting-font-size-val");
      const pct = Math.round(State.fontScale * 100);
      if (fontDisplay) fontDisplay.textContent = `${pct}%`;
      if (fontSlider) fontSlider.value = pct;
      if (fontSliderVal) fontSliderVal.textContent = `${pct}%`;

      // Apply line height
      document.documentElement.style.setProperty("--line-height", State.lineHeight);
      const lhSelect = document.getElementById("setting-line-height");
      if (lhSelect) lhSelect.value = State.lineHeight;

      // Apply letter spacing
      document.documentElement.style.setProperty("--letter-spacing", State.letterSpacing);
      const lsSelect = document.getElementById("setting-letter-spacing");
      if (lsSelect) lsSelect.value = State.letterSpacing;

      // Apply font family
      document.body.classList.remove("font-dyslexic", "font-serif", "font-mono");
      if (State.fontFamily !== "system") {
        document.body.classList.add(`font-${State.fontFamily}`);
      }
      const fontFamSelect = document.getElementById("setting-font-family");
      if (fontFamSelect) fontFamSelect.value = State.fontFamily;

      // Apply reduced motion
      if (State.reducedMotion) {
        document.body.classList.add("reduced-motion");
      } else {
        document.body.classList.remove("reduced-motion");
      }
      const motionCheckbox = document.getElementById("setting-reduced-motion");
      if (motionCheckbox) motionCheckbox.checked = State.reducedMotion;

      // Apply max width
      document.documentElement.style.setProperty("--content-max-width", State.maxWidth);
      const mwSelect = document.getElementById("setting-max-width");
      if (mwSelect) mwSelect.value = State.maxWidth;
    },

    setFontScale(newScale) {
      State.fontScale = Math.min(1.6, Math.max(0.9, Math.round(newScale * 100) / 100));
      localStorage.setItem("accessable_font_scale", State.fontScale);
      this.applyAll();
      announce(`Text size adjusted to ${Math.round(State.fontScale * 100)} percent`);
    },

    toggleTheme() {
      const themes = ["light", "dark", "high-contrast-dark", "high-contrast-yellow"];
      let nextIndex = (themes.indexOf(State.theme) + 1) % themes.length;
      State.theme = themes[nextIndex];
      localStorage.setItem("accessable_theme", State.theme);
      this.applyAll();
      announce(`Theme changed to ${State.theme}`);
    },

    toggleHighContrast() {
      if (State.theme.startsWith("high-contrast")) {
        State.theme = "light";
      } else {
        State.theme = "high-contrast-dark";
      }
      localStorage.setItem("accessable_theme", State.theme);
      this.applyAll();
      announce(`High contrast ${State.theme === 'light' ? 'disabled' : 'enabled'}`);
    },

    resetDefaults() {
      State.theme = "light";
      State.fontScale = 1.0;
      State.lineHeight = "1.6";
      State.letterSpacing = "normal";
      State.fontFamily = "system";
      State.reducedMotion = false;
      State.maxWidth = "1200px";

      localStorage.removeItem("accessable_theme");
      localStorage.removeItem("accessable_font_scale");
      localStorage.removeItem("accessable_line_height");
      localStorage.removeItem("accessable_letter_spacing");
      localStorage.removeItem("accessable_font_family");
      localStorage.removeItem("accessable_reduced_motion");
      localStorage.removeItem("accessable_max_width");

      this.applyAll();
      announce("All display preferences reset to default settings.");
    },

    bindEvents() {
      // Header Quick Buttons
      document.getElementById("font-increase-btn")?.addEventListener("click", () => this.setFontScale(State.fontScale + 0.1));
      document.getElementById("font-decrease-btn")?.addEventListener("click", () => this.setFontScale(State.fontScale - 0.1));
      document.getElementById("quick-theme-btn")?.addEventListener("click", () => this.toggleTheme());
      document.getElementById("quick-contrast-btn")?.addEventListener("click", () => this.toggleHighContrast());

      // Settings Page Controls
      document.getElementById("setting-font-size")?.addEventListener("input", (e) => this.setFontScale(e.target.value / 100));
      document.getElementById("setting-theme")?.addEventListener("change", (e) => {
        State.theme = e.target.value;
        localStorage.setItem("accessable_theme", State.theme);
        this.applyAll();
      });
      document.getElementById("setting-line-height")?.addEventListener("change", (e) => {
        State.lineHeight = e.target.value;
        localStorage.setItem("accessable_line_height", State.lineHeight);
        this.applyAll();
      });
      document.getElementById("setting-letter-spacing")?.addEventListener("change", (e) => {
        State.letterSpacing = e.target.value;
        localStorage.setItem("accessable_letter_spacing", State.letterSpacing);
        this.applyAll();
      });
      document.getElementById("setting-font-family")?.addEventListener("change", (e) => {
        State.fontFamily = e.target.value;
        localStorage.setItem("accessable_font_family", State.fontFamily);
        this.applyAll();
      });
      document.getElementById("setting-reduced-motion")?.addEventListener("change", (e) => {
        State.reducedMotion = e.target.checked;
        localStorage.setItem("accessable_reduced_motion", State.reducedMotion);
        this.applyAll();
      });
      document.getElementById("setting-max-width")?.addEventListener("change", (e) => {
        State.maxWidth = e.target.value;
        localStorage.setItem("accessable_max_width", State.maxWidth);
        this.applyAll();
      });
      document.getElementById("reset-settings-btn")?.addEventListener("click", () => this.resetDefaults());
    }
  };

  // =========================================================================
  // ACCESSIBLE TAB CONTROLLER (WCAG Tablist Pattern)
  // =========================================================================
  const TabController = {
    tabs: [],
    panels: [],

    init() {
      this.tabs = Array.from(document.querySelectorAll('.app-nav [role="tab"]'));
      this.panels = Array.from(document.querySelectorAll('main [role="tabpanel"]'));

      this.tabs.forEach((tab, index) => {
        tab.addEventListener("click", () => this.activateTab(tab));
        tab.addEventListener("keydown", (e) => this.handleKeydown(e, index));
      });

      // Sub-tabs in Checker
      const subTabs = Array.from(document.querySelectorAll('.sub-tab-nav [role="tab"]'));
      subTabs.forEach(subTab => {
        subTab.addEventListener("click", () => this.activateSubTab(subTab));
      });
    },

    activateTab(targetTab) {
      this.tabs.forEach(tab => {
        tab.classList.remove("active");
        tab.setAttribute("aria-selected", "false");
        tab.setAttribute("tabindex", "-1");
      });

      this.panels.forEach(panel => {
        panel.classList.remove("active");
        panel.setAttribute("hidden", "true");
      });

      targetTab.classList.add("active");
      targetTab.setAttribute("aria-selected", "true");
      targetTab.setAttribute("tabindex", "0");

      const panelId = targetTab.getAttribute("aria-controls");
      const activePanel = document.getElementById(panelId);
      if (activePanel) {
        activePanel.classList.add("active");
        activePanel.removeAttribute("hidden");
      }

      announce(`Navigated to ${targetTab.textContent.trim()} module`);
    },

    activateTabById(tabId) {
      const tab = document.getElementById(tabId);
      if (tab) this.activateTab(tab);
    },

    activateSubTab(targetSubTab) {
      const parent = targetSubTab.closest(".card");
      if (!parent) return;

      const subTabs = Array.from(parent.querySelectorAll('.sub-tab-nav [role="tab"]'));
      const subPanels = Array.from(parent.querySelectorAll(".sub-panel"));

      subTabs.forEach(t => {
        t.classList.remove("active");
        t.setAttribute("aria-selected", "false");
      });
      subPanels.forEach(p => {
        p.classList.remove("active");
        p.setAttribute("hidden", "true");
      });

      targetSubTab.classList.add("active");
      targetSubTab.setAttribute("aria-selected", "true");

      const targetPanelId = targetSubTab.getAttribute("aria-controls");
      const panel = document.getElementById(targetPanelId);
      if (panel) {
        panel.classList.add("active");
        panel.removeAttribute("hidden");
      }
    },

    handleKeydown(event, index) {
      let targetIndex = -1;
      if (event.key === "ArrowRight") {
        targetIndex = (index + 1) % this.tabs.length;
      } else if (event.key === "ArrowLeft") {
        targetIndex = (index - 1 + this.tabs.length) % this.tabs.length;
      } else if (event.key === "Home") {
        targetIndex = 0;
      } else if (event.key === "End") {
        targetIndex = this.tabs.length - 1;
      }

      if (targetIndex !== -1) {
        event.preventDefault();
        this.tabs[targetIndex].focus();
        this.activateTab(this.tabs[targetIndex]);
      }
    }
  };

  // =========================================================================
  // SYSTEM HEALTH & STATUS CONTROLLER
  // =========================================================================
  const SystemStatusController = {
    async check() {
      const badge = document.getElementById("system-status-badge");
      const badgeText = document.getElementById("status-badge-text");

      try {
        const res = await fetch(`/api/status?text_model=${encodeURIComponent(State.currentTextModel)}&vision_model=${encodeURIComponent(State.currentVisionModel)}`);
        if (!res.ok) throw new Error("Status query failed");

        const data = await res.json();
        State.ollamaRunning = data.ollama.running;
        State.installedModels = data.ollama.installed_models || [];
        State.textModelReady = data.ollama.text_model_ready;
        State.visionModelReady = data.ollama.vision_model_ready;
        if (data.ollama.configured_vision_model) {
          State.currentVisionModel = data.ollama.configured_vision_model;
        }

        // Update Header Badge
        if (badge && badgeText) {
          badge.className = "status-pill";
          if (State.ollamaRunning && State.textModelReady) {
            badge.classList.add("status-active");
            badgeText.textContent = `AI Active (${State.currentTextModel})`;
          } else if (State.ollamaRunning) {
            badge.classList.add("status-warning");
            badgeText.textContent = `Model Missing (${State.currentTextModel})`;
          } else {
            badge.classList.add("status-offline");
            badgeText.textContent = "Local AI Offline";
          }
        }

        // Update Simplification Module Banner
        const simplifyDisplay = document.getElementById("simplify-model-display");
        if (simplifyDisplay) {
          if (State.ollamaRunning && State.textModelReady) {
            simplifyDisplay.innerHTML = `<span style="color:#10b981;font-weight:700;">Online & Ready</span> (${State.currentTextModel} loaded)`;
          } else if (State.ollamaRunning) {
            simplifyDisplay.innerHTML = `<span style="color:#f59e0b;font-weight:700;">Model Not Found</span> — ${data.ollama.text_model_error || `Model '${State.currentTextModel}' is not installed.`}`;
          } else {
            simplifyDisplay.innerHTML = `<span style="color:#ef4444;font-weight:700;">Offline</span> — Ollama service not running on port 11434.`;
          }
        }

        // Sync dropdown with active model
        const modelSelect = document.getElementById("simplify-model-select");
        if (modelSelect && modelSelect.value !== State.currentTextModel) {
          const hasOption = Array.from(modelSelect.options).some(o => o.value === State.currentTextModel);
          if (hasOption) {
            modelSelect.value = State.currentTextModel;
          }
        }

        // Update Diagnostic Card in Help tab
        const diagService = document.getElementById("diag-ollama-service");
        const diagModels = document.getElementById("diag-installed-models");
        const diagText = document.getElementById("diag-text-model");
        const diagVision = document.getElementById("diag-vision-model");
        const diagOcr = document.getElementById("diag-ocr-status");

        if (diagService) diagService.textContent = State.ollamaRunning ? "Running (127.0.0.1:11434)" : "Stopped / Not Running";
        if (diagModels) diagModels.textContent = State.installedModels.length > 0 ? State.installedModels.join(", ") : "None downloaded yet";
        if (diagText) diagText.textContent = `${State.currentTextModel} (${State.textModelReady ? 'Ready' : 'Not Found'})`;
        if (diagVision) diagVision.textContent = `${State.currentVisionModel} (${State.visionModelReady ? 'Ready' : 'Not Found'})`;
        if (diagOcr) diagOcr.textContent = data.ocr.available ? `Available (${data.ocr.version})` : "Not detected (Requires Tesseract)";

      } catch (err) {
        if (badge && badgeText) {
          badge.className = "status-pill status-offline";
          badgeText.textContent = "AI Status Error";
        }
      }
    },

    init() {
      this.check();
      document.getElementById("system-status-badge")?.addEventListener("click", () => {
        TabController.activateTabById("tab-help");
      });
      document.getElementById("refresh-status-btn")?.addEventListener("click", () => {
        this.check();
        announce("System diagnostic refreshed.");
      });

      // Model selector dropdown change
      document.getElementById("simplify-model-select")?.addEventListener("change", (e) => {
        State.currentTextModel = e.target.value;
        this.check();
      });

      // Copy buttons in PowerShell guide
      document.querySelectorAll(".copy-cmd-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
          const cmd = e.currentTarget.getAttribute("data-cmd");
          if (cmd) {
            navigator.clipboard.writeText(cmd);
            const orig = e.currentTarget.textContent;
            e.currentTarget.textContent = "Copied!";
            setTimeout(() => e.currentTarget.textContent = orig, 1500);
            announce("Command copied to clipboard");
          }
        });
      });
    }
  };

  // =========================================================================
  // MODULE B: PDF UPLOAD & DOCUMENT READER CONTROLLER
  // =========================================================================
  const PDFReaderController = {
    currentFile: null,

    init() {
      const dropZone = document.getElementById("pdf-drop-zone");
      const fileInput = document.getElementById("pdf-file-input");
      const clearBtn = document.getElementById("pdf-clear-btn");
      const simplifyBtn = document.getElementById("pdf-send-to-simplify-btn");
      const speakBtn = document.getElementById("reader-speak-btn");
      const copyBtn = document.getElementById("reader-copy-btn");

      // File selection
      dropZone?.addEventListener("click", () => fileInput?.click());
      dropZone?.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          fileInput?.click();
        }
      });

      // Drag and drop events
      ["dragenter", "dragover"].forEach(evt => {
        dropZone?.addEventListener(evt, (e) => {
          e.preventDefault();
          dropZone.classList.add("dragover");
        });
      });
      ["dragleave", "drop"].forEach(evt => {
        dropZone?.addEventListener(evt, (e) => {
          e.preventDefault();
          dropZone.classList.remove("dragover");
        });
      });

      dropZone?.addEventListener("drop", (e) => {
        if (e.dataTransfer.files?.length > 0) {
          this.processFile(e.dataTransfer.files[0]);
        }
      });

      fileInput?.addEventListener("change", (e) => {
        if (e.target.files?.length > 0) {
          this.processFile(e.target.files[0]);
        }
      });

      clearBtn?.addEventListener("click", () => this.clear());
      simplifyBtn?.addEventListener("click", () => this.sendToSimplify());
      speakBtn?.addEventListener("click", () => this.speakDocument());
      copyBtn?.addEventListener("click", () => this.copyText());
    },

    async processFile(file) {
      if (!file || !file.name.toLowerCase().endsWith(".pdf")) {
        alert("Please select a valid PDF file (.pdf).");
        return;
      }

      if (file.size > 20 * 1024 * 1024) {
        alert("File size exceeds 20 MB limit.");
        return;
      }

      this.currentFile = file;
      const progress = document.getElementById("pdf-upload-progress");
      const progressBar = progress?.querySelector(".progress-bar-fill");
      const progressText = progress?.querySelector(".progress-text");
      const scannedAlert = document.getElementById("reader-scanned-alert");
      const enableOcr = document.getElementById("enable-ocr-checkbox")?.checked;

      if (progress) progress.classList.remove("hidden");
      if (progressBar) progressBar.style.width = "40%";
      if (progressText) progressText.textContent = "Uploading & extracting text...";
      if (scannedAlert) scannedAlert.classList.add("hidden");

      announce("Processing PDF document, please wait...");

      const formData = new FormData();
      formData.append("file", file);
      if (enableOcr) formData.append("run_ocr", "1");

      try {
        const res = await fetch("/api/pdf/extract", {
          method: "POST",
          body: formData
        });

        if (progressBar) progressBar.style.width = "100%";
        const data = await res.json();

        if (!data.success) {
          throw new Error(data.error || "Failed to process PDF.");
        }

        // Populate Text
        const textarea = document.getElementById("pdf-extracted-text");
        if (textarea) textarea.value = data.text || "";

        // Update Metadata
        const metaBox = document.getElementById("pdf-meta-box");
        if (metaBox) metaBox.classList.remove("hidden");
        document.getElementById("meta-filename").textContent = data.filename;
        document.getElementById("meta-pages").textContent = data.page_count;
        document.getElementById("meta-words").textContent = data.total_words;

        if (data.readability) {
          document.getElementById("meta-ease").textContent = `${data.readability.reading_ease}/100`;
          document.getElementById("meta-grade").textContent = `Grade ${data.readability.grade_level}`;
        } else {
          document.getElementById("meta-ease").textContent = "N/A";
          document.getElementById("meta-grade").textContent = "N/A";
        }

        // Scanned Warning
        if (data.is_scanned && !data.ocr_performed) {
          if (scannedAlert) {
            scannedAlert.classList.remove("hidden");
            const details = document.getElementById("scanned-alert-details");
            if (details) details.textContent = "This document appears to be scanned images. Check 'Enable Local OCR' or see AI Setup Guide for Tesseract installation.";
          }
        }

        // Enable Action Buttons
        document.getElementById("pdf-clear-btn")?.removeAttribute("disabled");
        document.getElementById("pdf-send-to-simplify-btn")?.removeAttribute("disabled");
        document.getElementById("reader-speak-btn")?.removeAttribute("disabled");
        document.getElementById("reader-copy-btn")?.removeAttribute("disabled");
        document.getElementById("reader-stats-badge").textContent = `${data.total_words} words`;

        announce(`PDF loaded successfully. ${data.page_count} pages and ${data.total_words} words extracted.`);

      } catch (err) {
        alert(`Error: ${err.message}`);
        announce(`PDF processing failed: ${err.message}`, true);
      } finally {
        setTimeout(() => {
          if (progress) progress.classList.add("hidden");
        }, 600);
      }
    },

    clear() {
      this.currentFile = null;
      document.getElementById("pdf-file-input").value = "";
      document.getElementById("pdf-extracted-text").value = "";
      document.getElementById("pdf-meta-box")?.classList.add("hidden");
      document.getElementById("reader-scanned-alert")?.classList.add("hidden");
      document.getElementById("pdf-clear-btn")?.setAttribute("disabled", "true");
      document.getElementById("pdf-send-to-simplify-btn")?.setAttribute("disabled", "true");
      document.getElementById("reader-speak-btn")?.setAttribute("disabled", "true");
      document.getElementById("reader-copy-btn")?.setAttribute("disabled", "true");
      document.getElementById("reader-stats-badge").textContent = "0 words";
      announce("Document cleared.");
    },

    sendToSimplify() {
      const text = document.getElementById("pdf-extracted-text")?.value;
      if (!text) return;

      const simplifyInput = document.getElementById("simplify-input-text");
      if (simplifyInput) {
        simplifyInput.value = text;
      }
      TabController.activateTabById("tab-simplify");
      TextSimplifierController.updateOriginalStats();
      announce("Document text transferred to simplification workspace.");
    },

    speakDocument() {
      const text = document.getElementById("pdf-extracted-text")?.value;
      if (!text) return;
      TTSController.speak(text);
    },

    copyText() {
      const text = document.getElementById("pdf-extracted-text")?.value;
      if (!text) return;
      navigator.clipboard.writeText(text);
      announce("Extracted document text copied to clipboard.");
    }
  };

  // =========================================================================
  // MODULE E: AI TEXT SIMPLIFICATION CONTROLLER
  // =========================================================================
  const TextSimplifierController = {
    sampleTexts: [
      "Pursuant to the aforementioned regulatory framework, all designated operational personnel shall strictly implement preventative safeguards whereby unintended data exfiltration is systematically ameliorated. Furthermore, any subsequent modifications necessitating architecture realignment must commence optimal verification prior to operational deployment.",
      "The cardiovascular examination demonstrated substantial hypertension, necessitating immediate pharmacological intervention with antihypertensive agents to facilitate optimal arterial pressure amelioration. Consequently, the patient was prescribed an angiotensin-converting enzyme inhibitor."
    ],

    init() {
      document.getElementById("simplify-trigger-btn")?.addEventListener("click", () => this.simplify(false));
      document.getElementById("run-fallback-btn")?.addEventListener("click", () => this.simplify(true));
      document.getElementById("load-sample-text-btn")?.addEventListener("click", () => this.loadSample());
      document.getElementById("simplify-input-text")?.addEventListener("input", () => this.updateOriginalStats());
      document.getElementById("simplify-copy-btn")?.addEventListener("click", () => this.copySimplified());
      document.getElementById("simplify-speak-btn")?.addEventListener("click", () => this.speakSimplified());
    },

    loadSample() {
      const input = document.getElementById("simplify-input-text");
      const sample = this.sampleTexts[Math.floor(Math.random() * this.sampleTexts.length)];
      if (input) {
        input.value = sample;
        this.updateOriginalStats();
      }
      announce("Sample complex text loaded.");
    },

    async updateOriginalStats() {
      const text = document.getElementById("simplify-input-text")?.value || "";
      const wordsEl = document.getElementById("orig-stat-words");
      const easeEl = document.getElementById("orig-stat-ease");
      const gradeEl = document.getElementById("orig-stat-grade");

      if (!text.trim()) {
        if (wordsEl) wordsEl.textContent = "0";
        if (easeEl) easeEl.textContent = "-";
        if (gradeEl) gradeEl.textContent = "-";
        return;
      }

      try {
        const res = await fetch("/api/text/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text })
        });
        const data = await res.json();
        if (data.success && data.readability) {
          if (wordsEl) wordsEl.textContent = data.readability.word_count;
          if (easeEl) easeEl.textContent = `${data.readability.reading_ease}/100`;
          if (gradeEl) gradeEl.textContent = `Grade ${data.readability.grade_level}`;
        }
      } catch (e) {
        // Silently skip live preview error
      }
    },

    async simplify(forceRuleBased = false) {
      const text = document.getElementById("simplify-input-text")?.value?.trim();
      if (!text) {
        alert("Please enter or paste text to simplify.");
        return;
      }

      const loadingBox = document.getElementById("simplify-loading-state");
      const outputArea = document.getElementById("simplify-output-text");
      const fallbackAlert = document.getElementById("simplify-fallback-alert");
      const fallbackRow = document.getElementById("fallback-trigger-row");
      const originBadge = document.getElementById("simplify-origin-badge");
      const copyBtn = document.getElementById("simplify-copy-btn");
      const speakBtn = document.getElementById("simplify-speak-btn");

      if (loadingBox) loadingBox.classList.remove("hidden");
      if (fallbackAlert) fallbackAlert.classList.add("hidden");
      if (fallbackRow) fallbackRow.classList.add("hidden");
      if (originBadge) originBadge.classList.add("hidden");
      if (outputArea) outputArea.innerHTML = "";

      announce("Simplifying text with local AI model, please wait...");

      try {
        let endpoint = "/api/text/simplify";
        let payload = {
          text,
          model: State.currentTextModel,
          allow_fallback: forceRuleBased
        };

        if (forceRuleBased) {
          endpoint = "/api/text/fallback-simplify";
        }

        const res = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (res.status === 503) {
          // Ollama model is offline or not installed
          if (loadingBox) loadingBox.classList.add("hidden");
          if (outputArea) {
            outputArea.innerHTML = `
              <div class="alert alert-warning" role="alert">
                <strong>Local AI Unavailable:</strong> ${data.error}<br><br>
                <em>You can use the built-in non-AI plain English rule-based helper below, or open the AI Setup Guide tab for PowerShell instructions to start Ollama.</em>
              </div>
            `;
          }
          if (fallbackRow) fallbackRow.classList.remove("hidden");
          announce(`Local AI unavailable: ${data.error}`, true);
          return;
        }

        if (!data.success && !data.simplified_text) {
          throw new Error(data.error || "Simplification failed.");
        }

        // Render result
        if (outputArea) {
          outputArea.textContent = data.simplified_text;
        }

        // Show explicit badges & disclaimers
        if (data.is_ai_generated) {
          if (originBadge) {
            originBadge.className = "badge badge-success";
            originBadge.textContent = `AI Simplified (${data.model_used})`;
            originBadge.classList.remove("hidden");
          }
        } else {
          // Rule-based fallback was used
          if (originBadge) {
            originBadge.className = "badge badge-warning";
            originBadge.textContent = "Rule-Based Helper (Non-AI)";
            originBadge.classList.remove("hidden");
          }
          if (fallbackAlert) {
            fallbackAlert.classList.remove("hidden");
            const alertText = document.getElementById("fallback-alert-text");
            if (alertText) alertText.textContent = data.disclaimer || "Generated using deterministic pattern matching because local Ollama model was not active.";
          }
        }

        // Update original and simplified readability stats from actual output
        if (data.before_readability) {
          const origWords = document.getElementById("orig-stat-words");
          const origEase = document.getElementById("orig-stat-ease");
          const origGrade = document.getElementById("orig-stat-grade");
          if (origWords) origWords.textContent = data.before_readability.word_count;
          if (origEase) origEase.textContent = `${data.before_readability.reading_ease}/100`;
          if (origGrade) origGrade.textContent = `Grade ${data.before_readability.grade_level}`;
        }

        if (data.after_readability) {
          const simpWords = document.getElementById("simp-stat-words");
          const simpEase = document.getElementById("simp-stat-ease");
          const simpGrade = document.getElementById("simp-stat-grade");
          if (simpWords) simpWords.textContent = data.after_readability.word_count;
          if (simpEase) simpEase.textContent = `${data.after_readability.reading_ease}/100`;
          if (simpGrade) simpGrade.textContent = `Grade ${data.after_readability.grade_level}`;
        }

        if (copyBtn) copyBtn.removeAttribute("disabled");
        if (speakBtn) speakBtn.removeAttribute("disabled");

        announce("Text simplification complete.");

      } catch (err) {
        alert(`Simplification Error: ${err.message}`);
        announce(`Error: ${err.message}`, true);
      } finally {
        if (loadingBox) loadingBox.classList.add("hidden");
      }
    },

    copySimplified() {
      const text = document.getElementById("simplify-output-text")?.textContent;
      if (text) {
        navigator.clipboard.writeText(text);
        announce("Simplified text copied to clipboard.");
      }
    },

    speakSimplified() {
      const text = document.getElementById("simplify-output-text")?.textContent;
      if (text) {
        TTSController.speak(text);
      }
    }
  };

  // =========================================================================
  // MODULE C: TEXT-TO-SPEECH (TTS) CONTROLLER
  // =========================================================================
  const TTSController = {
    init() {
      if (!State.synth) {
        const statusBox = document.getElementById("tts-status-box");
        if (statusBox) statusBox.textContent = "Web Speech API is not supported in this browser.";
        return;
      }

      this.populateVoices();
      if (speechSynthesis.onvoiceschanged !== undefined) {
        speechSynthesis.onvoiceschanged = () => this.populateVoices();
      }

      document.getElementById("tts-play-btn")?.addEventListener("click", () => {
        const text = document.getElementById("tts-input-text")?.value;
        this.speak(text);
      });

      document.getElementById("tts-pause-btn")?.addEventListener("click", () => this.pause());
      document.getElementById("tts-resume-btn")?.addEventListener("click", () => this.resume());
      document.getElementById("tts-stop-btn")?.addEventListener("click", () => this.stop());

      // Sliders
      document.getElementById("tts-rate-slider")?.addEventListener("input", (e) => {
        document.getElementById("tts-rate-val").textContent = `${e.target.value}x`;
      });
      document.getElementById("tts-pitch-slider")?.addEventListener("input", (e) => {
        document.getElementById("tts-pitch-val").textContent = e.target.value;
      });
    },

    populateVoices() {
      if (!State.synth) return;
      State.voices = State.synth.getVoices();
      const select = document.getElementById("tts-voice-select");
      if (!select || State.voices.length === 0) return;

      select.innerHTML = "";
      State.voices.forEach((voice, index) => {
        const option = document.createElement("option");
        option.value = index;
        option.textContent = `${voice.name} (${voice.lang})${voice.default ? ' — Default' : ''}`;
        select.appendChild(option);
      });
    },

    async speak(text) {
      if (!State.synth) {
        alert("Speech synthesis is not supported on this device/browser.");
        return;
      }

      if (!text || !text.trim()) {
        alert("Please enter text to read aloud.");
        return;
      }

      // Stop any existing speech to prevent overlapping voices
      this.stop();

      // Chunk text via backend to prevent Chrome 15s truncation bug
      try {
        const res = await fetch("/api/speech/chunk", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text })
        });
        const data = await res.json();
        State.speechChunks = data.chunks || [text];
      } catch (e) {
        // Fallback to simple split
        State.speechChunks = text.match(/[^.!?]+[.!?]+/g) || [text];
      }

      State.currentChunkIndex = 0;
      this.updateStatus("Speaking...");
      this.setButtonsState(true, true, false, true);

      this.playNextChunk();
      announce("Starting text-to-speech playback.");
    },

    playNextChunk() {
      if (!State.synth || State.currentChunkIndex >= State.speechChunks.length) {
        this.stop();
        this.updateStatus("Finished reading aloud.");
        announce("Finished reading aloud.");
        return;
      }

      const chunk = State.speechChunks[State.currentChunkIndex];
      const utterance = new SpeechSynthesisUtterance(chunk);

      // Voice
      const voiceIndex = document.getElementById("tts-voice-select")?.value;
      if (voiceIndex && State.voices[voiceIndex]) {
        utterance.voice = State.voices[voiceIndex];
      }

      // Rate & Pitch
      const rate = parseFloat(document.getElementById("tts-rate-slider")?.value) || 1.0;
      const pitch = parseFloat(document.getElementById("tts-pitch-slider")?.value) || 1.0;
      utterance.rate = rate;
      utterance.pitch = pitch;

      utterance.onend = () => {
        State.currentChunkIndex++;
        this.playNextChunk();
      };

      utterance.onerror = (e) => {
        this.updateStatus(`Speech error: ${e.error || 'Playback issue'}`);
        this.setButtonsState(true, false, false, false);
      };

      State.currentUtterance = utterance;
      State.synth.speak(utterance);
    },

    pause() {
      if (State.synth && State.synth.speaking) {
        State.synth.pause();
        this.updateStatus("Paused.");
        this.setButtonsState(false, false, true, true);
        announce("Speech paused.");
      }
    },

    resume() {
      if (State.synth && State.synth.paused) {
        State.synth.resume();
        this.updateStatus("Speaking...");
        this.setButtonsState(true, true, false, true);
        announce("Speech resumed.");
      }
    },

    stop() {
      if (State.synth) {
        State.synth.cancel();
      }
      State.currentChunkIndex = 0;
      State.speechChunks = [];
      this.updateStatus("Ready to speak.");
      this.setButtonsState(true, false, false, false);
    },

    updateStatus(msg) {
      const box = document.getElementById("tts-status-box");
      if (box) box.textContent = msg;
    },

    setButtonsState(play, pause, resume, stop) {
      const p = document.getElementById("tts-play-btn");
      const pa = document.getElementById("tts-pause-btn");
      const r = document.getElementById("tts-resume-btn");
      const s = document.getElementById("tts-stop-btn");

      if (p) play ? p.removeAttribute("disabled") : p.setAttribute("disabled", "true");
      if (pa) pause ? pa.removeAttribute("disabled") : pa.setAttribute("disabled", "true");
      if (r) resume ? r.removeAttribute("disabled") : r.setAttribute("disabled", "true");
      if (s) stop ? s.removeAttribute("disabled") : s.setAttribute("disabled", "true");
    }
  };

  // =========================================================================
  // MODULE D: SPEECH-TO-TEXT (STT) CONTROLLER
  // =========================================================================
  const STTController = {
    init() {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const alertBox = document.getElementById("stt-support-alert");

      if (!SpeechRecognition) {
        if (alertBox) {
          alertBox.className = "alert alert-warning";
          alertBox.textContent = "Speech recognition is not supported in this browser. Chrome, Edge, and Safari provide native support.";
          alertBox.classList.remove("hidden");
        }
        document.getElementById("stt-record-btn")?.setAttribute("disabled", "true");
        return;
      }

      State.recognition = new SpeechRecognition();
      State.recognition.continuous = true;
      State.recognition.interimResults = true;
      State.recognition.lang = "en-US";

      const recordBtn = document.getElementById("stt-record-btn");
      const stopBtn = document.getElementById("stt-stop-btn");
      const clearBtn = document.getElementById("stt-clear-btn");
      const liveIndicator = document.getElementById("stt-live-indicator");
      const transcriptArea = document.getElementById("stt-transcript-text");

      recordBtn?.addEventListener("click", () => this.start());
      stopBtn?.addEventListener("click", () => this.stop());
      clearBtn?.addEventListener("click", () => {
        if (transcriptArea) transcriptArea.value = "";
        this.updateButtons();
        announce("Transcript cleared.");
      });

      document.getElementById("stt-copy-btn")?.addEventListener("click", () => {
        if (transcriptArea && transcriptArea.value) {
          navigator.clipboard.writeText(transcriptArea.value);
          announce("Transcript copied to clipboard.");
        }
      });

      document.getElementById("stt-transfer-simplify-btn")?.addEventListener("click", () => {
        const text = transcriptArea?.value;
        if (!text) return;
        const input = document.getElementById("simplify-input-text");
        if (input) input.value = text;
        TabController.activateTabById("tab-simplify");
        TextSimplifierController.updateOriginalStats();
        announce("Transferred transcript to text simplification.");
      });

      document.getElementById("stt-read-back-btn")?.addEventListener("click", () => {
        const text = transcriptArea?.value;
        if (text) TTSController.speak(text);
      });

      // Events
      State.recognition.onstart = () => {
        State.isRecording = true;
        if (liveIndicator) liveIndicator.classList.remove("hidden");
        recordBtn?.setAttribute("disabled", "true");
        stopBtn?.removeAttribute("disabled");
        announce("Microphone listening. Speak into your microphone.", true);
      };

      State.recognition.onresult = (event) => {
        let finalTranscript = "";
        let interimTranscript = "";

        for (let i = 0; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript + " ";
          } else {
            interimTranscript += event.results[i][0].transcript;
          }
        }

        if (transcriptArea) {
          transcriptArea.value = (finalTranscript + interimTranscript).trim();
        }
        this.updateButtons();
      };

      State.recognition.onerror = (event) => {
        if (event.error === "not-allowed") {
          alert("Microphone access was denied. Please allow microphone permission in your browser address bar.");
        }
        this.stop();
        announce(`Speech recognition error: ${event.error}`, true);
      };

      State.recognition.onend = () => {
        State.isRecording = false;
        if (liveIndicator) liveIndicator.classList.add("hidden");
        recordBtn?.removeAttribute("disabled");
        stopBtn?.setAttribute("disabled", "true");
        this.updateButtons();
      };
    },

    start() {
      if (!State.recognition) return;
      try {
        State.recognition.start();
      } catch (e) {
        // Recognition might already be running
      }
    },

    stop() {
      if (!State.recognition) return;
      try {
        State.recognition.stop();
      } catch (e) {}
      State.isRecording = false;
      document.getElementById("stt-live-indicator")?.classList.add("hidden");
      document.getElementById("stt-record-btn")?.removeAttribute("disabled");
      document.getElementById("stt-stop-btn")?.setAttribute("disabled", "true");
      announce("Microphone stopped.");
    },

    updateButtons() {
      const hasText = !!document.getElementById("stt-transcript-text")?.value?.trim();
      const copyBtn = document.getElementById("stt-copy-btn");
      const transferBtn = document.getElementById("stt-transfer-simplify-btn");
      const readBtn = document.getElementById("stt-read-back-btn");

      if (copyBtn) hasText ? copyBtn.removeAttribute("disabled") : copyBtn.setAttribute("disabled", "true");
      if (transferBtn) hasText ? transferBtn.removeAttribute("disabled") : transferBtn.setAttribute("disabled", "true");
      if (readBtn) hasText ? readBtn.removeAttribute("disabled") : readBtn.setAttribute("disabled", "true");
    }
  };

  // =========================================================================
  // MODULE F: AI IMAGE ACCESSIBILITY CONTROLLER
  // =========================================================================
  const ImageAccessibilityController = {
    selectedFile: null,

    init() {
      const dropZone = document.getElementById("image-drop-zone");
      const fileInput = document.getElementById("image-file-input");
      const describeBtn = document.getElementById("image-describe-btn");
      const clearBtn = document.getElementById("image-clear-btn");
      const copyAltBtn = document.getElementById("image-copy-alt-btn");
      const copyAllBtn = document.getElementById("image-copy-all-btn");
      const speakBtn = document.getElementById("image-speak-btn");

      dropZone?.addEventListener("click", () => fileInput?.click());
      dropZone?.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          fileInput?.click();
        }
      });

      ["dragenter", "dragover"].forEach(evt => {
        dropZone?.addEventListener(evt, (e) => {
          e.preventDefault();
          dropZone.classList.add("dragover");
        });
      });
      ["dragleave", "drop"].forEach(evt => {
        dropZone?.addEventListener(evt, (e) => {
          e.preventDefault();
          dropZone.classList.remove("dragover");
        });
      });

      dropZone?.addEventListener("drop", (e) => {
        if (e.dataTransfer.files?.length > 0) {
          this.previewImage(e.dataTransfer.files[0]);
        }
      });

      fileInput?.addEventListener("change", (e) => {
        if (e.target.files?.length > 0) {
          this.previewImage(e.target.files[0]);
        }
      });

      describeBtn?.addEventListener("click", () => this.generateDescription());
      clearBtn?.addEventListener("click", () => this.clear());
      copyAltBtn?.addEventListener("click", () => {
        const alt = document.getElementById("image-alt-result")?.value;
        if (alt) {
          navigator.clipboard.writeText(alt);
          announce("Suggested alt-text copied to clipboard.");
        }
      });
      copyAllBtn?.addEventListener("click", () => {
        const alt = document.getElementById("image-alt-result")?.value || "";
        const desc = document.getElementById("image-detailed-result")?.value || "";
        const combined = `Suggested Alt-Text:\n${alt}\n\nDetailed Description:\n${desc}`.trim();
        if (combined) {
          navigator.clipboard.writeText(combined);
          announce("All image accessibility descriptions copied to clipboard.");
        }
      });
      speakBtn?.addEventListener("click", () => {
        const alt = document.getElementById("image-alt-result")?.value;
        const desc = document.getElementById("image-detailed-result")?.value;
        if (alt || desc) {
          TTSController.speak(`${alt}. ${desc}`);
        }
      });
    },

    previewImage(file) {
      if (!file || !file.type.startsWith("image/")) {
        alert("Please select a valid image file (PNG, JPEG, WebP, BMP).");
        return;
      }

      this.selectedFile = file;
      const reader = new FileReader();
      reader.onload = (e) => {
        const previewImg = document.getElementById("image-preview");
        const wrapper = document.getElementById("image-preview-wrapper");
        const metaTag = document.getElementById("image-meta-tag");

        if (previewImg) previewImg.src = e.target.result;
        if (wrapper) wrapper.classList.remove("hidden");
        if (metaTag) metaTag.textContent = `${(file.size / 1024).toFixed(1)} KB`;

        document.getElementById("image-describe-btn")?.removeAttribute("disabled");
        document.getElementById("image-clear-btn")?.removeAttribute("disabled");
        announce(`Image ${file.name} loaded and ready for analysis.`);
      };
      reader.readAsDataURL(file);
    },

    async generateDescription() {
      if (!this.selectedFile) return;

      const loadingBox = document.getElementById("image-loading-state");
      const altResult = document.getElementById("image-alt-result");
      const descResult = document.getElementById("image-detailed-result");
      const mode = document.getElementById("image-mode-select")?.value || "standard";

      if (loadingBox) loadingBox.classList.remove("hidden");
      if (altResult) altResult.value = "";
      if (descResult) descResult.value = "";

      announce("Analyzing image with local vision model, please wait...");

      const formData = new FormData();
      formData.append("file", this.selectedFile);
      formData.append("mode", mode);
      formData.append("model", State.currentVisionModel);

      try {
        const res = await fetch("/api/image/describe", {
          method: "POST",
          body: formData
        });

        const data = await res.json();

        if (res.status === 503) {
          // Vision model is offline
          alert(`Vision Model Unavailable: ${data.error}\n\nPlease check the AI Setup Guide tab for setup instructions.`);
          TabController.activateTabById("tab-help");
          return;
        }

        if (!data.success) {
          throw new Error(data.error || "Image analysis failed.");
        }

        if (altResult) altResult.value = data.suggested_alt_text;
        if (descResult) descResult.value = data.description;

        document.getElementById("image-copy-alt-btn")?.removeAttribute("disabled");
        document.getElementById("image-speak-btn")?.removeAttribute("disabled");
        document.getElementById("image-copy-all-btn")?.removeAttribute("disabled");

        announce("Alt-text and visual description generated successfully.");

      } catch (err) {
        alert(`Error: ${err.message}`);
        announce(`Image description error: ${err.message}`, true);
      } finally {
        if (loadingBox) loadingBox.classList.add("hidden");
      }
    },

    clear() {
      this.selectedFile = null;
      document.getElementById("image-file-input").value = "";
      document.getElementById("image-preview").src = "";
      document.getElementById("image-preview-wrapper")?.classList.add("hidden");
      document.getElementById("image-alt-result").value = "";
      document.getElementById("image-detailed-result").value = "";
      document.getElementById("image-describe-btn")?.setAttribute("disabled", "true");
      document.getElementById("image-clear-btn")?.setAttribute("disabled", "true");
      document.getElementById("image-copy-alt-btn")?.setAttribute("disabled", "true");
      document.getElementById("image-copy-all-btn")?.setAttribute("disabled", "true");
      document.getElementById("image-speak-btn")?.setAttribute("disabled", "true");
      announce("Image cleared.");
    }
  };

  // =========================================================================
  // MODULE H: ACCESSIBILITY CHECKER CONTROLLER (WCAG 2.1)
  // =========================================================================
  const AccessibilityCheckerController = {
    problematicSample: `<!DOCTYPE html>
<html>
<head>
  <!-- Missing <title> and missing lang on <html> -->
</head>
<body style="outline: none;">
  <header>
    <h3>Skipped heading straight to H3</h3>
    <img src="banner.jpg">
  </header>
  <div>
    <!-- Missing <main> landmark -->
    <a href="#">Read More</a>
    <button><i class="icon-search"></i></button>
    <input type="text" placeholder="Enter full name">
    <table>
      <tr><td>Product</td><td>Price</td></tr>
    </table>
  </div>
</body>
</html>`,

    init() {
      document.getElementById("checker-sample-btn")?.addEventListener("click", () => {
        const input = document.getElementById("checker-html-input");
        if (input) input.value = this.problematicSample;
        announce("Problematic HTML sample loaded.");
      });

      document.getElementById("checker-run-snippet-btn")?.addEventListener("click", () => this.auditSnippet());
      document.getElementById("checker-run-file-btn")?.addEventListener("click", () => this.auditFile());
      document.getElementById("checker-run-url-btn")?.addEventListener("click", () => this.auditUrl());

      document.getElementById("checker-file-input")?.addEventListener("change", (e) => {
        const btn = document.getElementById("checker-run-file-btn");
        if (e.target.files?.length > 0) {
          btn?.removeAttribute("disabled");
        }
      });

      document.getElementById("issues-filter-select")?.addEventListener("change", (e) => {
        this.renderFilteredIssues(e.target.value);
      });
    },

    async auditSnippet() {
      const html = document.getElementById("checker-html-input")?.value?.trim();
      if (!html) {
        alert("Please paste an HTML snippet to audit.");
        return;
      }
      this.executeAudit("/api/accessibility/check-html", { html, source_name: "Pasted HTML Snippet" });
    },

    async auditFile() {
      const file = document.getElementById("checker-file-input")?.files?.[0];
      if (!file) return;

      const formData = new FormData();
      formData.append("file", file);

      announce("Auditing HTML file for WCAG barriers...");
      try {
        const res = await fetch("/api/accessibility/check-html", {
          method: "POST",
          body: formData
        });
        const data = await res.json();
        this.handleAuditResponse(data);
      } catch (err) {
        alert(`Audit error: ${err.message}`);
      }
    },

    async auditUrl() {
      const url = document.getElementById("checker-url-input")?.value?.trim();
      if (!url) {
        alert("Please enter a webpage URL to scan.");
        return;
      }
      this.executeAudit("/api/accessibility/check-url", { url });
    },

    async executeAudit(endpoint, payload) {
      announce("Auditing content for WCAG barriers, please wait...");
      try {
        const res = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        this.handleAuditResponse(data);
      } catch (err) {
        alert(`Scan error: ${err.message}`);
      }
    },

    handleAuditResponse(data) {
      if (!data.success) {
        alert(`Audit Failed: ${data.error}`);
        announce(`Audit failed: ${data.error}`, true);
        return;
      }

      State.lastAuditIssues = data.issues || [];

      // Update Score Badge
      const scoreBadge = document.getElementById("audit-score-badge");
      if (scoreBadge) {
        scoreBadge.className = `score-badge score-${data.score_color}`;
        scoreBadge.textContent = `Score: ${data.score}/100`;
      }

      // Update Metric Tallies
      document.getElementById("count-critical").textContent = data.severity_counts.Critical;
      document.getElementById("count-serious").textContent = data.severity_counts.Serious;
      document.getElementById("count-moderate").textContent = data.severity_counts.Moderate;
      document.getElementById("count-minor").textContent = data.severity_counts.Minor;

      // Update Rating Text
      const ratingText = document.getElementById("audit-rating-text");
      if (ratingText) {
        ratingText.textContent = `${data.score_rating} — Found ${data.total_issues} accessibility barrier(s) in '${data.source_name}'.`;
      }

      this.renderFilteredIssues("all");
      announce(`Audit complete. Score: ${data.score} out of 100. ${data.total_issues} issues identified.`);
    },

    renderFilteredIssues(severityFilter) {
      const container = document.getElementById("issues-list-container");
      if (!container) return;

      const filtered = severityFilter === "all"
        ? State.lastAuditIssues
        : State.lastAuditIssues.filter(i => i.severity === severityFilter);

      if (filtered.length === 0) {
        container.innerHTML = `
          <div class="empty-state-box">
            <p>No issues matching severity "${severityFilter}".</p>
          </div>
        `;
        return;
      }

      container.innerHTML = "";
      filtered.forEach((issue, idx) => {
        const item = document.createElement("div");
        item.className = "issue-item";

        let severityBadgeClass = "badge-neutral";
        if (issue.severity === "Critical") severityBadgeClass = "badge-warning";
        else if (issue.severity === "Serious") severityBadgeClass = "badge-warning";

        item.innerHTML = `
          <div class="issue-header" tabindex="0" role="button" aria-expanded="false" id="issue-header-${idx}">
            <div class="issue-title-group">
              <span class="badge ${severityBadgeClass}">${issue.severity}</span>
              <span class="issue-name">${issue.name}</span>
              <span class="issue-wcag">${issue.wcag_sc}</span>
            </div>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="chevron"><polyline points="6 9 12 15 18 9"></polyline></svg>
          </div>
          <div class="issue-body hidden" id="issue-body-${idx}">
            <p><strong>Why it matters:</strong> ${issue.description}</p>
            <div>
              <strong>Violating Element:</strong>
              <div class="issue-code-snippet">${this.escapeHtml(issue.element)}</div>
            </div>
            <div class="issue-suggestion">
              <strong>Recommended Correction:</strong> ${issue.suggestion}
            </div>
          </div>
        `;

        const header = item.querySelector(".issue-header");
        const body = item.querySelector(".issue-body");

        header.addEventListener("click", () => {
          const isOpen = !body.classList.contains("hidden");
          body.classList.toggle("hidden", isOpen);
          header.setAttribute("aria-expanded", (!isOpen).toString());
        });

        header.addEventListener("keydown", (e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            header.click();
          }
        });

        container.appendChild(item);
      });
    },

    escapeHtml(str) {
      return (str || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    }
  };

  // =========================================================================
  // MODULE I: ACCESSIBLE LEARNING SUPPORT CONTROLLER
  // =========================================================================
  const LearningSupportController = {
    sampleStudyNote: `Photosynthesis is the fundamental biological process by which autotrophic botanical organisms, predominantly chlorophyll-containing green flora, synthesize chemical carbohydrates from atmospheric carbon dioxide and subterranean water utilizing solar electromagnetic radiation. The light-dependent reactions transpire within the thylakoid membranes, generating adenosine triphosphate (ATP) and NADPH, while the Calvin Cycle catalyzes carbon fixation within the stroma.`,

    init() {
      document.getElementById("learning-sample-btn")?.addEventListener("click", () => {
        const input = document.getElementById("learning-input-text");
        if (input) input.value = this.sampleStudyNote;
        announce("Sample study material loaded.");
      });

      document.getElementById("learning-generate-btn")?.addEventListener("click", () => this.generate());
      document.getElementById("learning-speak-btn")?.addEventListener("click", () => {
        const container = document.getElementById("learning-output-container");
        if (container) TTSController.speak(container.textContent);
      });
    },

    async generate() {
      const text = document.getElementById("learning-input-text")?.value?.trim();
      if (!text) {
        alert("Please enter educational notes or text.");
        return;
      }

      const loadingBox = document.getElementById("learning-loading-state");
      const outputContainer = document.getElementById("learning-output-container");
      const speakBtn = document.getElementById("learning-speak-btn");

      if (loadingBox) loadingBox.classList.remove("hidden");
      if (outputContainer) outputContainer.innerHTML = "";

      announce("Generating accessible study guide with local AI, please wait...");

      try {
        const res = await fetch("/api/learning/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            text,
            model: State.currentTextModel
          })
        });

        const data = await res.json();

        if (res.status === 503) {
          alert(`Local AI Unavailable: ${data.error}\n\nPlease check the AI Setup Guide tab.`);
          TabController.activateTabById("tab-help");
          return;
        }

        if (!data.success) throw new Error(data.error || "Generation failed.");

        const guide = data.data;
        let html = `
          <div class="study-section">
            <h4>Plain English Study Summary</h4>
            <p>${guide.summary || "Summary generated."}</p>
          </div>
        `;

        if (guide.key_terms && guide.key_terms.length > 0) {
          html += `
            <div class="study-section">
              <h4>Key Terminology Glossary</h4>
              <div class="glossary-list">
          `;
          guide.key_terms.forEach(term => {
            html += `
              <div class="glossary-card">
                <strong>${term.term}:</strong> ${term.definition}
              </div>
            `;
          });
          html += `</div></div>`;
        }

        if (guide.practice_questions && guide.practice_questions.length > 0) {
          html += `
            <div class="study-section">
              <h4>Practice Comprehension Check</h4>
          `;
          guide.practice_questions.forEach((q, qIndex) => {
            html += `
              <div class="quiz-card" id="quiz-card-${qIndex}">
                <p><strong>Q${qIndex + 1}: ${q.question}</strong></p>
                <div class="quiz-options-list">
            `;
            (q.options || []).forEach(opt => {
              html += `
                <button class="quiz-option-btn" data-correct="${q.correct_answer === opt}">
                  ${opt}
                </button>
              `;
            });
            html += `
                </div>
                <div class="quiz-explanation-box hidden" id="quiz-exp-${qIndex}">
                  <strong>Answer: ${q.correct_answer}</strong> — ${q.explanation || ''}
                </div>
              </div>
            `;
          });
          html += `</div>`;
        }

        if (outputContainer) {
          outputContainer.innerHTML = html;

          // Bind quiz options click
          outputContainer.querySelectorAll(".quiz-option-btn").forEach(btn => {
            btn.addEventListener("click", (e) => {
              const parent = e.target.closest(".quiz-card");
              const expBox = parent?.querySelector(".quiz-explanation-box");
              if (expBox) expBox.classList.remove("hidden");
              const isCorrect = e.target.getAttribute("data-correct") === "true";
              if (isCorrect) {
                e.target.style.borderColor = "#10b981";
                e.target.style.backgroundColor = "#ecfdf5";
                announce("Correct answer!");
              } else {
                e.target.style.borderColor = "#ef4444";
                e.target.style.backgroundColor = "#fef2f2";
                announce("Incorrect answer. See explanation.");
              }
            });
          });
        }

        if (speakBtn) speakBtn.removeAttribute("disabled");
        announce("Study guide generated successfully.");

      } catch (err) {
        alert(`Error: ${err.message}`);
        announce(`Learning generation error: ${err.message}`, true);
      } finally {
        if (loadingBox) loadingBox.classList.add("hidden");
      }
    }
  };

  // =========================================================================
  // BOOTSTRAP APPLICATION CONTROLLERS
  // =========================================================================
  SettingsController.init();
  TabController.init();
  SystemStatusController.init();
  PDFReaderController.init();
  TextSimplifierController.init();
  TTSController.init();
  STTController.init();
  ImageAccessibilityController.init();
  AccessibilityCheckerController.init();
  LearningSupportController.init();

  announce("AccessAble AI loaded and ready.");
});
