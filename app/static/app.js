// Legal Metrology Compliance-Assist Engine Frontend Logic — "Liquid Glass & Bilingual" Edition

document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  const dropzonePrompt = document.getElementById('dropzonePrompt');
  const previewContainer = document.getElementById('previewContainer');
  const imagePreview = document.getElementById('imagePreview');
  const btnChangeImage = document.getElementById('btnChangeImage');
  const btnAnalyze = document.getElementById('btnAnalyze');
  const btnAnalyzeText = document.getElementById('btnAnalyzeText');
  const scanningProgressCard = document.getElementById('scanningProgressCard');

  // Input Mode Elements
  const btnModeUpload = document.getElementById('btnModeUpload');
  const btnModeCamera = document.getElementById('btnModeCamera');
  const uploadViewContainer = document.getElementById('uploadViewContainer');
  const cameraViewContainer = document.getElementById('cameraViewContainer');
  const cameraVideo = document.getElementById('cameraVideo');
  const cameraCanvas = document.getElementById('cameraCanvas');
  const btnCapturePhoto = document.getElementById('btnCapturePhoto');
  const btnSwitchCamera = document.getElementById('btnSwitchCamera');
  const btnCancelCamera = document.getElementById('btnCancelCamera');

  const resultsSection = document.getElementById('resultsSection');
  const scanMetaText = document.getElementById('scanMetaText');
  const complianceSummaryBar = document.getElementById('complianceSummaryBar');
  const summaryBarTitle = document.getElementById('summaryBarTitle');
  const summaryBarPct = document.getElementById('summaryBarPct');
  const summaryFill = document.getElementById('summaryFill');
  const summaryHint = document.getElementById('summaryHint');

  const statusBanner = document.getElementById('statusBanner');
  const statusIconBox = document.getElementById('statusIconBox');
  const statusTitle = document.getElementById('statusTitle');
  const statusDesc = document.getElementById('statusDesc');
  const exemptionBox = document.getElementById('exemptionBox');
  const exemptionReasonText = document.getElementById('exemptionReasonText');
  const exemptionRefText = document.getElementById('exemptionRefText');
  const fieldsContainer = document.getElementById('fieldsContainer');
  const btnExportPdf = document.getElementById('btnExportPdf');

  const btnToggleOcr = document.getElementById('btnToggleOcr');
  const ocrContent = document.getElementById('ocrContent');
  const accordionArrow = document.getElementById('accordionArrow');
  const ocrLineCount = document.getElementById('ocrLineCount');
  const rawOcrText = document.getElementById('rawOcrText');

  const presetButtons = document.querySelectorAll('.btn-chip');

  // State
  let currentFile = null;
  let currentPresetText = null;
  let currentReport = null;
  let mediaStream = null;
  let currentFacingMode = 'environment';

  // Auto-Scan State
  let autoScanInterval = null;
  let autoScanActive = false;
  let autoScanDebounceUntil = 0;
  const AUTO_SCAN_INTERVAL_MS = 2200;   // Sample a frame every 2.2 seconds
  const AUTO_SCAN_MIN_CHARS = 15;       // Minimum OCR text chars to trigger scan
  const AUTO_SCAN_DEBOUNCE_MS = 6000;   // Wait 6s after each successful scan

  const autoScanBadge = document.getElementById('autoScanBadge');
  const autoScanStatusText = document.getElementById('autoScanStatusText');
  const cameraViewport = document.querySelector('.camera-viewport');

  // SVG Line Icons
  const ICONS = {
    check: '<svg class="status-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    cross: '<svg class="status-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
    shield: '<svg class="status-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    warning: '<svg class="status-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    uncertain: '<svg class="status-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
    stampCheck: '<svg class="stamp-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    stampCross: '<svg class="stamp-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
    stampWarning: '<svg class="stamp-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    stampUncertain: '<svg class="stamp-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>'
  };

  // Presets
  const PRESETS = {
    compliant: {
      key: "presetCompliant",
      title: "Standard Compliant Pack",
      text: "ORGANIC CASHEW NUTS\nNet Wt: 500 g\nMRP Rs. 650.00 (Incl. of all taxes)\nMFD: 10/2024\nManufactured & Packed by: Green Agro Foods Pvt Ltd, Plot 42, GIDC, Ahmedabad, Gujarat 382330\nConsumer Care Helpline: 1800-200-4567 | Email: care@greenagro.com"
    },
    dual_mrp: {
      key: "presetDualMrp",
      title: "Dual MRP Anomaly",
      text: "CRUNCHY CHOCO COOKIES 200g\nMRP Rs.20 MRPRs.25*\nMFD: 09/2024\nPacked by: Sweet Bakes Ltd, Okhla Phase 3, New Delhi 110020\nConsumer Helpline: 1800-222-3333 | care@sweetbakes.in"
    },
    crunchy_bites: {
      key: "presetCrunchyBites",
      title: "Crunchy Bites (Dual MRP Anomaly)",
      text: "CRUNCHY BITES CORN CHIPS\nNet Wt: 200 g\nMRP Rs.20 / MRPRs.25*\nMFD: 09/2024\nManufactured by: Sweet Bakes Ltd, Okhla Phase 3, New Delhi 110020\nCustomer Care: 1800-111-2222 | care@sweetbakes.in"
    },
    nutrition_panel: {
      key: "presetNutrition",
      title: "Nutrition Panel (Not Exempt)",
      text: "HIGH PROTEIN PEANUT BUTTER\nNutrition Facts per 100g: Protein 25g, Total Fat 6g, Sugars 4g, Sodium 50mg\nNet Weight: 350 g\nMRP Rs. 280.00\nMFD: 10/2024\nManufactured by: NutriFoods India Ltd, Pune 411001\nConsumer Care: 1800-222-1111 | support@nutrifoods.in"
    },
    non_std_unit: {
      key: "presetNonStdUnit",
      title: "Non-Standard Unit ('gm')",
      text: "ROYAL CHAI MASALA\nNet Wt: 100 gm\nMRP Rs. 85.00\nMFD: 08/2024\nManufactured by: Spice Wonders Ltd, Andheri East, Mumbai 400069\nCustomer Care: 9820012345"
    },
    missing_fields: {
      key: "presetMissingFields",
      title: "Missing Consumer Care Details",
      text: "EXTRA VIRGIN MUSTARD OIL\nNet Volume: 1 L\nMRP Rs. 210.00\nMFD: 07/2024\nManufactured by: Shudh Oil Mills, Industrial Area, Jaipur, Rajasthan 302013"
    },
    exempt_bulk: {
      key: "presetExemptBulk",
      title: "Exempt Bulk 30kg Pack",
      text: "WHOLE WHEAT ATTA - 30 kg\nNot for retail sale - Institutional & Commercial Supply\nMRP Rs. 1150.00\nMFD: 06/2024\nManufactured by: Bharat Flour Mills Ltd, Ludhiana 141001"
    },
    exempt_small: {
      key: "presetExemptSmall",
      title: "Exempt Small Non-Tobacco Pack (5g)",
      text: "NATURAL CARDAMOM MOUTH FRESHENER\nNet Wt: 5 g\nMRP Rs. 10.00\nMFD: 10/2024\nMfd by: Fresh Herbs Ltd, Haridwar, Uttarakhand"
    },
    tobacco_small: {
      key: "presetTobaccoSmall",
      title: "Small Tobacco Pack (5g - Never Exempt)",
      text: "PREMIUM TOBACCO KHAINI\nNet Wt: 5 g\nMRP Rs. 20.00\nMFD: 09/2024\nManufactured by: Desi Tobacco Products, Kanpur, UP 208001\nConsumer Helpline: 9876543210"
    }
  };

  // Re-render when language is switched
  window.addEventListener('languageChanged', () => {
    if (currentReport) {
      renderResults(currentReport);
    }
  });

  // ==============================================================================
  // INPUT MODE SWITCHING & CAMERA WORKFLOW
  // ==============================================================================

  btnModeUpload.addEventListener('click', () => {
    btnModeUpload.classList.add('active');
    btnModeCamera.classList.remove('active');
    stopAutoScan();
    stopCamera();
    cameraViewContainer.classList.add('hidden');
    uploadViewContainer.classList.remove('hidden');
  });

  btnModeCamera.addEventListener('click', () => {
    btnModeCamera.classList.add('active');
    btnModeUpload.classList.remove('active');
    uploadViewContainer.classList.add('hidden');
    cameraViewContainer.classList.remove('hidden');
    startCamera();
  });

  async function startCamera() {
    stopCamera();
    try {
      const constraints = {
        video: {
          facingMode: currentFacingMode,
          width: { ideal: 1280 },
          height: { ideal: 720 }
        },
        audio: false
      };
      mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
      cameraVideo.srcObject = mediaStream;
      cameraVideo.addEventListener('loadeddata', () => {
        startAutoScan();
      }, { once: true });
      showToast(t('toastCameraReady', 'Live camera scanner ready — auto-scanning active'), 'info');
    } catch (err) {
      console.error('Camera access error:', err);
      showToast(t('toastCameraError', 'Camera access unavailable. Switching to file upload.'), 'warning');
      btnModeUpload.click();
    }
  }

  function stopCamera() {
    stopAutoScan();
    if (mediaStream) {
      mediaStream.getTracks().forEach(track => track.stop());
      mediaStream = null;
    }
    if (cameraVideo) {
      cameraVideo.srcObject = null;
    }
  }

  // ==============================================================================
  // AUTO-SCAN ENGINE
  // ==============================================================================

  function startAutoScan() {
    if (autoScanInterval) clearInterval(autoScanInterval);
    autoScanActive = true;
    setAutoScanBadge(true, 'Auto-Scanning…');
    autoScanInterval = setInterval(autoScanTick, AUTO_SCAN_INTERVAL_MS);
  }

  function stopAutoScan() {
    autoScanActive = false;
    if (autoScanInterval) {
      clearInterval(autoScanInterval);
      autoScanInterval = null;
    }
    setAutoScanBadge(false);
    if (cameraViewport) cameraViewport.classList.remove('auto-scanning');
  }

  function setAutoScanBadge(visible, text) {
    if (!autoScanBadge) return;
    if (visible) {
      autoScanBadge.classList.remove('hidden');
      if (autoScanStatusText && text) autoScanStatusText.textContent = text;
    } else {
      autoScanBadge.classList.add('hidden');
    }
  }

  /**
   * Auto-scan frame tick — called every AUTO_SCAN_INTERVAL_MS.
   * 1. Checks debounce (skip if a scan was recently completed).
   * 2. Captures current frame from the live video stream.
   * 3. Checks frame brightness (reject if too dark/blank).
   * 4. Sends frame to /api/scan backend.
   * 5. If backend returns ≥ AUTO_SCAN_MIN_CHARS of extracted text, shows compliance results.
   */
  async function autoScanTick() {
    if (!autoScanActive) return;
    if (!cameraVideo || !cameraVideo.videoWidth || !cameraVideo.videoHeight) return;
    if (Date.now() < autoScanDebounceUntil) return;

    // Capture current frame
    cameraCanvas.width = cameraVideo.videoWidth;
    cameraCanvas.height = cameraVideo.videoHeight;
    const ctx = cameraCanvas.getContext('2d');
    ctx.drawImage(cameraVideo, 0, 0, cameraCanvas.width, cameraCanvas.height);

    // Basic brightness check — skip very dark or uniform frames
    const imageData = ctx.getImageData(0, 0, Math.min(cameraCanvas.width, 120), Math.min(cameraCanvas.height, 120));
    const pixels = imageData.data;
    let brightness = 0;
    for (let i = 0; i < pixels.length; i += 4) {
      brightness += (pixels[i] + pixels[i + 1] + pixels[i + 2]) / 3;
    }
    brightness /= (pixels.length / 4);
    if (brightness < 25 || brightness > 245) return; // Too dark or blown out

    if (cameraViewport) cameraViewport.classList.add('auto-scanning');
    setAutoScanBadge(true, 'Detecting text…');

    try {
      const blob = await new Promise((resolve, reject) => {
        cameraCanvas.toBlob(b => b ? resolve(b) : reject(new Error('Blob failed')), 'image/jpeg', 0.88);
      });

      const formData = new FormData();
      formData.append('file', new File([blob], `auto_scan_${Date.now()}.jpg`, { type: 'image/jpeg' }));

      const response = await fetch('/api/scan', { method: 'POST', body: formData });
      if (!response.ok) return;

      const data = await response.json();

      // Only show results if enough text was actually detected
      const textLength = (data.raw_text || (data.extracted_lines || []).map(l => l.text).join(' ')).trim().length;
      if (textLength < AUTO_SCAN_MIN_CHARS) {
        setAutoScanBadge(true, 'No label detected…');
        if (cameraViewport) cameraViewport.classList.remove('auto-scanning');
        return;
      }

      // ✅ Label detected — stop auto-scan, show result like a normal scan
      stopAutoScan();
      stopCamera();
      cameraViewContainer.classList.add('hidden');
      uploadViewContainer.classList.remove('hidden');
      btnModeUpload.classList.add('active');
      btnModeCamera.classList.remove('active');

      // Show captured frame as preview
      imagePreview.src = cameraCanvas.toDataURL('image/jpeg');
      dropzonePrompt.classList.add('hidden');
      previewContainer.classList.remove('hidden');

      currentReport = data;
      renderResults(data);
      autoScanDebounceUntil = Date.now() + AUTO_SCAN_DEBOUNCE_MS;

      if (data.is_exempt) {
        showToast(t('toastExemptApplied', 'Auto-scan: Statutory Exemption Applied (Rule 3/26)'), 'info');
      } else if (data.overall_status === 'COMPLIANT') {
        showToast(t('toastScanComplete', 'Auto-scan: Label is COMPLIANT ✓'), 'success');
      } else {
        showToast(t('toastFlaggedAlert', 'Auto-scan: Non-compliant declarations found — review results'), 'warning');
      }

      resultsSection.classList.remove('hidden');
      resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

    } catch (err) {
      console.warn('Auto-scan frame error:', err);
      setAutoScanBadge(true, 'Auto-Scanning…');
      if (cameraViewport) cameraViewport.classList.remove('auto-scanning');
    }
  }

  // ==============================================================================

  btnSwitchCamera.addEventListener('click', () => {
    currentFacingMode = (currentFacingMode === 'environment') ? 'user' : 'environment';
    startCamera();
  });

  btnCancelCamera.addEventListener('click', () => {
    btnModeUpload.click();
  });

  btnCapturePhoto.addEventListener('click', () => {
    if (!cameraVideo.videoWidth || !cameraVideo.videoHeight) {
      showToast(t('toastCameraError', 'Camera video stream is not ready yet'), 'warning');
      return;
    }

    cameraCanvas.width = cameraVideo.videoWidth;
    cameraCanvas.height = cameraVideo.videoHeight;
    const ctx = cameraCanvas.getContext('2d');
    ctx.drawImage(cameraVideo, 0, 0, cameraCanvas.width, cameraCanvas.height);

    cameraCanvas.toBlob((blob) => {
      if (!blob) {
        showToast(t('toastCameraError', 'Failed to capture snapshot'), 'error');
        return;
      }
      const capturedFile = new File([blob], `camera_scan_${Date.now()}.png`, { type: 'image/png' });
      stopCamera();
      cameraViewContainer.classList.add('hidden');
      uploadViewContainer.classList.remove('hidden');
      btnModeUpload.classList.add('active');
      btnModeCamera.classList.remove('active');

      handleFileSelection(capturedFile);
      showToast(t('toastPhotoCaptured', 'Photo captured from camera'), 'success');
    }, 'image/png');
  });


  // ==============================================================================
  // FILE UPLOAD WORKFLOW
  // ==============================================================================

  dropzone.addEventListener('click', (e) => {
    if (e.target.closest('#btnChangeImage')) return;
    fileInput.click();
  });

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('dragover');
    });
  });

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove('dragover');
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files && files.length > 0) {
      handleFileSelection(files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelection(e.target.files[0]);
    }
  });

  btnChangeImage.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.value = '';
    currentFile = null;
    currentPresetText = null;
    previewContainer.classList.add('hidden');
    dropzonePrompt.classList.remove('hidden');
    btnAnalyze.disabled = true;
    clearActivePreset();
    fileInput.click();
  });

  function handleFileSelection(file) {
    if (!file.type.startsWith('image/')) {
      showToast(t('toastInvalidImage', 'Please upload a valid image file (PNG, JPG, JPEG, WEBP)'), 'warning');
      return;
    }
    currentFile = file;
    currentPresetText = null;
    clearActivePreset();

    const reader = new FileReader();
    reader.onload = (e) => {
      imagePreview.src = e.target.result;
      dropzonePrompt.classList.add('hidden');
      previewContainer.classList.remove('hidden');
      btnAnalyze.disabled = false;
      showToast(`${t('toastImageSelected', 'Selected image:')} ${file.name}`, 'info');
    };
    reader.readAsDataURL(file);
  }

  // Preset button clicks
  presetButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const presetKey = btn.getAttribute('data-preset');
      const preset = PRESETS[presetKey];
      if (!preset) return;

      clearActivePreset();
      btn.classList.add('active');

      currentFile = null;
      currentPresetText = preset.text;

      // Draw crisp instrument canvas preview
      const canvas = document.createElement('canvas');
      canvas.width = 640;
      canvas.height = 340;
      const ctx = canvas.getContext('2d');
      
      ctx.fillStyle = "#F6F7F5";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.strokeStyle = "#D8DBD4";
      ctx.lineWidth = 2;
      ctx.strokeRect(10, 10, canvas.width - 20, canvas.height - 20);

      ctx.fillStyle = "#101D33";
      ctx.font = "bold 15px 'IBM Plex Sans', sans-serif";
      ctx.fillText(`[PRESET] ${t(preset.key, preset.title)}`, 26, 38);

      ctx.font = "13px 'IBM Plex Mono', monospace";
      ctx.fillStyle = "#1B2430";
      const lines = preset.text.split('\n');
      lines.forEach((l, idx) => {
        ctx.fillText(l, 26, 75 + (idx * 26));
      });

      imagePreview.src = canvas.toDataURL('image/png');
      dropzonePrompt.classList.add('hidden');
      previewContainer.classList.remove('hidden');
      btnAnalyze.disabled = false;
      showToast(`${t('toastPresetLoaded', 'Loaded preset:')} ${t(preset.key, preset.title)}`, 'info');
    });
  });

  function clearActivePreset() {
    presetButtons.forEach(b => b.classList.remove('active'));
  }

  // ==============================================================================
  // SCAN & ANALYSIS TRIGGER
  // ==============================================================================

  btnAnalyze.addEventListener('click', async () => {
    if (!currentFile && !currentPresetText) return;

    setLoading(true);

    try {
      let response;
      if (currentFile) {
        const formData = new FormData();
        formData.append('file', currentFile);
        response = await fetch('/api/scan', {
          method: 'POST',
          body: formData
        });
      } else if (currentPresetText) {
        response = await fetch('/api/scan-text', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: currentPresetText,
            filename: "demo_preset_label.png"
          })
        });
      }

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Server responded with status ${response.status}`);
      }

      const data = await response.json();
      currentReport = data;
      renderResults(data);

      if (data.is_exempt) {
        showToast(t('toastExemptApplied', 'Statutory Exemption Applied (Rule 3/26)'), 'info');
      } else if (data.overall_status === 'COMPLIANT') {
        showToast(t('toastScanComplete', 'Screening Passed: 100% Compliant'), 'success');
      } else if (data.overall_status === 'NON_COMPLIANT') {
        const hasDual = (data.fields || []).some(f => (f.flag || '').includes('Dual pricing'));
        if (hasDual) {
          showToast(t('toastDualMrpAlert', 'Dual pricing anomaly detected (Rule 32)'), 'warning');
        } else {
          showToast(t('toastFlaggedAlert', 'Screening Flagged: Review Rule 6 findings'), 'warning');
        }
      }
    } catch (err) {
      console.error('Scan error:', err);
      showToast(`${t('toastPdfError', 'Error')}: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  });

  function setLoading(isLoading) {
    if (isLoading) {
      btnAnalyze.disabled = true;
      btnAnalyzeText.textContent = t('btnScanningAction', 'Calibrating & Screening...');
      if (scanningProgressCard) scanningProgressCard.classList.remove('hidden');
      if (resultsSection) resultsSection.classList.add('hidden');
    } else {
      btnAnalyze.disabled = false;
      btnAnalyzeText.textContent = t('btnScanAction', 'Scan Label & Check Compliance');
      if (scanningProgressCard) scanningProgressCard.classList.add('hidden');
    }
  }

  // ==============================================================================
  // RENDER SCREENING RESULTS (Bilingual)
  // ==============================================================================

  function renderResults(report) {
    scanMetaText.innerHTML = `<strong>${t('scanRefLabel', 'Scan Ref ID:')}</strong> <span class="ref-code">${escapeHtml(report.scan_id)}</span> &bull; <strong>${t('evaluatedOnLabel', 'Evaluated on:')}</strong> ${escapeHtml(report.timestamp)}`;
    
    // 1. Compliance Summary Progress Bar
    if (report.is_exempt) {
      if (summaryBarTitle) summaryBarTitle.textContent = t('statusExempt', 'Statutory Exemption Applied (Rule 3 / Rule 26)');
      if (summaryBarPct) summaryBarPct.textContent = t('stampExempt', 'EXEMPT');
      if (summaryFill) {
        summaryFill.className = "summary-fill summary-fill-exempt";
        summaryFill.style.width = "0%";
        requestAnimationFrame(() => {
          setTimeout(() => { summaryFill.style.width = "100%"; }, 50);
        });
      }
      if (summaryHint) summaryHint.textContent = t('statusExemptDesc', 'Package meets statutory exemption criteria under Rule 3 / Rule 26. Standard retail declaration rules are waived.');
    } else {
      const totalFields = 5;
      const passedFields = (report.fields || []).filter(f => f.status === 'PASS').length;
      const hasUncertain = (report.fields || []).some(f => f.status === 'UNCERTAIN');
      const hasWarning = (report.fields || []).some(f => f.status === 'WARNING' || f.status === 'FLAGGED');
      const pct = Math.round((passedFields / totalFields) * 100);

      if (summaryBarTitle) summaryBarTitle.textContent = `${t('complianceScoreLabel', 'Compliance Score:')} ${passedFields} / ${totalFields} ${t('declarationsPassed', 'Mandatory Declarations Passed')}`;
      if (summaryBarPct) summaryBarPct.textContent = `${pct}%`;
      if (summaryFill) {
        summaryFill.style.width = "0%";
        if (passedFields === totalFields) {
          summaryFill.className = 'summary-fill';
        } else if (hasWarning || hasUncertain) {
          summaryFill.className = 'summary-fill summary-fill-warning';
        } else {
          summaryFill.className = 'summary-fill summary-fill-danger';
        }
        requestAnimationFrame(() => {
          setTimeout(() => { summaryFill.style.width = `${pct}%`; }, 50);
        });
      }
      if (summaryHint) {
        if (passedFields === totalFields) {
          summaryHint.textContent = t('allMandatoryMet', 'All 5 mandatory statutory declarations satisfy Legal Metrology (Packaged Commodities) Rules, 2011 specifications.');
        } else {
          summaryHint.textContent = `${totalFields - passedFields} ${t('declarationsMissing', 'mandatory declaration(s) are missing, flagged, or non-compliant under Rule 6.')}`;
        }
      }
    }

    // 2. Primary Compliance Verdict Banner
    statusBanner.className = 'status-banner';
    const overall = (report.overall_status || '').toUpperCase();

    if (overall === 'COMPLIANT') {
      statusBanner.classList.add('compliant');
      statusIconBox.innerHTML = ICONS.check;
      statusTitle.textContent = t('statusCompliant', 'COMPLIANT');
      statusDesc.textContent = t('statusCompliantDesc', 'All 5 mandatory declarations meet Legal Metrology (Packaged Commodities) Rules, 2011 requirements.');
    } else if (overall === 'EXEMPT') {
      statusBanner.classList.add('exempt');
      statusIconBox.innerHTML = ICONS.shield;
      statusTitle.textContent = t('statusExempt', 'STATUTORY EXEMPTION APPLIED');
      statusDesc.textContent = t('statusExemptDesc', 'Package meets statutory exemption criteria under Rule 3 / Rule 26. Standard retail declaration rules are waived.');
    } else if (overall === 'UNCERTAIN') {
      statusBanner.classList.add('uncertain');
      statusIconBox.innerHTML = ICONS.uncertain;
      statusTitle.textContent = t('statusUncertain', 'UNCERTAIN — LOW OCR CONFIDENCE');
      statusDesc.textContent = t('statusUncertainDesc', 'One or more text fields returned low OCR confidence (< 60%). Physical pre-inspection review is recommended.');
    } else {
      statusBanner.classList.add('non_compliant');
      statusIconBox.innerHTML = ICONS.cross;
      statusTitle.textContent = t('statusNonCompliant', 'NON-COMPLIANT / ANOMALY DETECTED');
      statusDesc.textContent = t('statusNonCompliantDesc', 'One or more mandatory declarations are missing, non-compliant, or have price/unit anomalies.');
    }

    // 3. Exemption box
    if (report.is_exempt && report.exemption_details) {
      exemptionBox.classList.remove('hidden');
      exemptionReasonText.textContent = report.exemption_details.reason || t('statusExemptDesc', 'Package meets statutory exemption criteria.');
      exemptionRefText.textContent = report.exemption_details.rule_reference || t('exemptionRuleRef', 'Rule 3 & Rule 26');
      fieldsContainer.innerHTML = '';
    } else {
      exemptionBox.classList.add('hidden');
      renderFieldCards(report.fields);
    }

    // 4. OCR Raw text (Never translate actual OCR output)
    const lines = report.extracted_lines || [];
    ocrLineCount.textContent = lines.length > 0 ? lines.length : (report.raw_text ? report.raw_text.split('\n').length : 0);
    rawOcrText.textContent = report.raw_text || lines.map(l => l.text).join('\n') || t('noTextDetected', '(No text detected)');

    resultsSection.classList.remove('hidden');
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function getFieldI18nNames(fieldOrName) {
    const raw = typeof fieldOrName === 'object' ? (fieldOrName.field_id || fieldOrName.field_name || '') : (fieldOrName || '');
    const fid = (typeof fieldOrName === 'object' && fieldOrName.field_id) ? fieldOrName.field_id.toLowerCase() : raw.toLowerCase();
    
    // 1. MRP
    if (fid === 'mrp' || fid.includes('mrp') || fid.includes('retail price')) {
      return { name: t('fieldMrpName', 'Maximum Retail Price (MRP)'), rule: t('fieldMrpRule', 'Rule 6(1)(e) — Price declaration including all taxes') };
    }
    // 2. Net Quantity
    if (fid === 'net_quantity' || fid.includes('quantity') || fid.includes('net')) {
      return { name: t('fieldNetQtyName', 'Net Quantity'), rule: t('fieldNetQtyRule', 'Rule 6(1)(b) — Standard SI units (g, kg, ml, l)') };
    }
    // 3. Manufacturer / Packer Address (Checked before date to avoid 'manufacture' keyword overlap)
    if (fid === 'address' || fid === 'manufacturer_address' || fid.includes('address') || fid.includes('packer') || fid.includes('importer') || (fid.includes('manufacturer') && !fid.includes('date'))) {
      return { name: t('fieldMfgAddressName', 'Manufacturer / Packer Name & Address'), rule: t('fieldMfgAddressRule', 'Rule 6(1)(a) — Complete identification & address') };
    }
    // 4. Date of Manufacture / Packing
    if (fid === 'mfg_date' || fid.includes('date') || fid.includes('mfg') || fid.includes('packing') || fid.includes('pkd')) {
      return { name: t('fieldMfgDateName', 'Date of Manufacture / Packing'), rule: t('fieldMfgDateRule', 'Rule 6(1)(d) — Month & Year of packing') };
    }
    // 5. Consumer Care Details
    if (fid === 'consumer_care' || fid.includes('consumer') || fid.includes('care') || fid.includes('contact') || fid.includes('helpline')) {
      return { name: t('fieldConsumerCareName', 'Consumer Care Contact Details'), rule: t('fieldConsumerCareRule', 'Rule 6(1)(f) — Name, address, phone or email') };
    }
    return { name: raw, rule: 'Rule 6' };
  }

  function translateFinding(flagText) {
    if (!flagText) return '';
    if (flagText.includes('Dual pricing') || flagText.includes('Rule 32(2)')) {
      return t('dualPricingDetected', flagText);
    }
    if (flagText.includes('Non-standard unit') || flagText.includes('standard SI')) {
      return t('nonStandardUnitDetected', flagText);
    }
    if (flagText.includes('missing') || flagText.includes('Missing')) {
      return t('missingFieldGeneric', flagText);
    }
    return flagText;
  }

  function renderFieldCards(fields) {
    fieldsContainer.innerHTML = '';
    if (!fields || fields.length === 0) return;

    fields.forEach(field => {
      const card = document.createElement('div');
      card.className = 'field-card';

      let stampClass = 'stamp-pass';
      let statusCardClass = 'status-pass';
      let stampIconSvg = ICONS.stampCheck;
      let stampText = t('stampPass', 'PASS');
      const statusUpper = (field.status || '').toUpperCase();

      if (statusUpper === 'FAIL') {
        stampClass = 'stamp-fail';
        statusCardClass = 'status-fail';
        stampIconSvg = ICONS.stampCross;
        stampText = t('stampFail', 'FAIL');
      } else if (statusUpper === 'WARNING' || statusUpper === 'FLAGGED') {
        stampClass = 'stamp-warning';
        statusCardClass = 'status-warning';
        stampIconSvg = ICONS.stampWarning;
        stampText = t('stampFlagged', 'FLAGGED');
      } else if (statusUpper === 'UNCERTAIN') {
        stampClass = 'stamp-uncertain';
        statusCardClass = 'status-uncertain';
        stampIconSvg = ICONS.stampUncertain;
        stampText = t('stampUncertain', 'UNCERTAIN');
      }

      card.classList.add(statusCardClass);

      let confTagHtml = '';
      if (field.confidence_score !== null && field.confidence_score !== undefined) {
        const pct = Math.round(field.confidence_score * 100);
        const lowClass = field.confidence_score < 0.60 ? 'field-confidence-low' : '';
        confTagHtml = `<span class="field-confidence-tag ${lowClass}">OCR: ${pct}%</span>`;
      }

      // Keep raw detected values intact
      const matchedHtml = field.matched_text 
        ? `<div class="field-matched-text"><strong>${t('detectedValueLabel', 'Detected Value:')}</strong> <code>${escapeHtml(field.matched_text)}</code> ${confTagHtml}</div>` 
        : `<div class="field-desc-text"><em>${t('noDeclarationDetected', 'No matching declaration detected on label')}</em></div>`;

      const translatedFlag = translateFinding(field.flag);
      const flagHtml = translatedFlag 
        ? `<div class="field-flag-warning">${ICONS.warning} <strong>${t('findingLabel', 'Finding:')}</strong> ${escapeHtml(translatedFlag)}</div>` 
        : '';

      const translatedDetails = translateFinding(field.details) || field.details;
      const detailsHtml = `<div class="field-desc-text"><strong>${t('explanationLabel', 'Explanation / Guidance:')}</strong> ${escapeHtml(translatedDetails)}</div>`;

      const { name: i18nFieldName, rule: i18nFieldRule } = getFieldI18nNames(field);

      card.innerHTML = `
        <div class="field-name-block">
          <span class="field-name">${escapeHtml(i18nFieldName)}</span>
          <span class="field-rule">${escapeHtml(i18nFieldRule)}</span>
        </div>
        <div class="badge-stamp-wrapper">
          <div class="badge-stamp ${stampClass}">
            ${stampIconSvg}
            <span class="stamp-text">${stampText}</span>
          </div>
        </div>
        <div class="field-details-block">
          ${matchedHtml}
          ${flagHtml}
          ${detailsHtml}
        </div>
      `;

      fieldsContainer.appendChild(card);
    });
  }

  // Toggle OCR Accordion
  btnToggleOcr.addEventListener('click', () => {
    ocrContent.classList.toggle('hidden');
    accordionArrow.classList.toggle('rotated');
  });

  // Download PDF Report
  btnExportPdf.addEventListener('click', async () => {
    if (!currentReport) return;

    btnExportPdf.disabled = true;
    const originalText = btnExportPdf.innerHTML;
    btnExportPdf.innerHTML = `<span>${t('toastPdfExporting', 'Generating PDF Report...')}</span>`;
    showToast(t('toastPdfExporting', 'Generating formal compliance screening PDF...'), 'info');

    try {
      const response = await fetch('/api/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(currentReport)
      });

      if (!response.ok) {
        throw new Error('Failed to generate PDF report from server.');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Compliance_Assist_Report_${currentReport.scan_id}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
      showToast(t('toastPdfSuccess', 'Compliance report PDF downloaded successfully'), 'success');
    } catch (err) {
      console.error('PDF export error:', err);
      showToast(`${t('toastPdfError', 'Could not export PDF report')}: ${err.message}`, 'error');
    } finally {
      btnExportPdf.disabled = false;
      btnExportPdf.innerHTML = originalText;
    }
  });

  function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const iconMap = {
      success: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>',
      warning: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
      error: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
      info: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'
    };

    toast.innerHTML = `
      <div class="toast-icon-box">${iconMap[type] || iconMap.info}</div>
      <div class="toast-message">${escapeHtml(message)}</div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
      toast.classList.add('toast-out');
      setTimeout(() => toast.remove(), 250);
    }, 3500);
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
