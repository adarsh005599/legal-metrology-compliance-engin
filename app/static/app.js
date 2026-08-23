// Legal Metrology Compliance-Assist Engine Frontend Logic

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

  const resultsSection = document.getElementById('resultsSection');
  const scanMetaText = document.getElementById('scanMetaText');
  const complianceSummaryBar = document.getElementById('complianceSummaryBar');
  const summaryBarTitle = document.getElementById('summaryBarTitle');
  const summaryBarPct = document.getElementById('summaryBarPct');
  const summaryFill = document.getElementById('summaryFill');
  const summaryHint = document.getElementById('summaryHint');

  const statusBanner = document.getElementById('statusBanner');
  const statusIcon = document.getElementById('statusIcon');
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

  // Preset definitions for fast hackathon demo testing
  const PRESETS = {
    compliant: {
      title: "Standard Compliant Pack",
      text: "ORGANIC CASHEW NUTS\nNet Wt: 500 g\nMRP Rs. 650.00 (Incl. of all taxes)\nMFD: 10/2024\nManufactured & Packed by: Green Agro Foods Pvt Ltd, Plot 42, GIDC, Ahmedabad, Gujarat 382330\nConsumer Care Helpline: 1800-200-4567 | Email: care@greenagro.com"
    },
    nutrition_panel: {
      title: "Nutrition Panel (Not Exempt)",
      text: "HIGH PROTEIN PEANUT BUTTER\nNutrition Facts per 100g: Protein 25g, Total Fat 6g, Sugars 4g, Sodium 50mg\nNet Weight: 350 g\nMRP Rs. 280.00\nMFD: 10/2024\nManufactured by: NutriFoods India Ltd, Pune 411001\nConsumer Care: 1800-222-1111 | support@nutrifoods.in"
    },
    non_std_unit: {
      title: "Non-Standard Unit ('gm')",
      text: "ROYAL CHAI MASALA\nNet Wt: 100 gm\nMRP Rs. 85.00\nMFD: 08/2024\nManufactured by: Spice Wonders Ltd, Andheri East, Mumbai 400069\nCustomer Care: 9820012345"
    },
    dual_mrp: {
      title: "Dual MRP Anomaly",
      text: "CRUNCHY CHOCO COOKIES 200g\nMRP Rs. 100.00 (Incl. of all taxes)\nSpecial Price Sticker MRP Rs. 125.00 (revised mrp)\nMFD: 09/2024\nPacked by: Sweet Bakes Ltd, Okhla Phase 3, New Delhi 110020\nConsumer Helpline: care@sweetbakes.in"
    },
    missing_fields: {
      title: "Missing Consumer Care Details",
      text: "EXTRA VIRGIN MUSTARD OIL\nNet Volume: 1 L\nMRP Rs. 210.00\nMFD: 07/2024\nManufactured by: Shudh Oil Mills, Industrial Area, Jaipur, Rajasthan 302013\n(Consumer care details missing on label)"
    },
    exempt_bulk: {
      title: "Exempt Bulk 30kg Pack",
      text: "WHOLE WHEAT ATTA - 30 kg\nNot for retail sale - Institutional & Commercial Supply\nMRP Rs. 1150.00\nMFD: 06/2024\nManufactured by: Bharat Flour Mills Ltd, Ludhiana 141001"
    },
    exempt_small: {
      title: "Exempt Small Non-Tobacco Pack (5g)",
      text: "NATURAL CARDAMOM MOUTH FRESHENER\nNet Wt: 5 g\nMRP Rs. 10.00\nMFD: 10/2024\nMfd by: Fresh Herbs Ltd, Haridwar, Uttarakhand"
    },
    tobacco_small: {
      title: "Small Tobacco Pack (5g - Never Exempt)",
      text: "PREMIUM TOBACCO KHAINI\nNet Wt: 5 g\nMRP Rs. 20.00\nMFD: 09/2024\nManufactured by: Desi Tobacco Products, Kanpur, UP 208001\nConsumer Helpline: 9876543210"
    }
  };

  // Drag and drop handlers
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
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
      handleFileSelection(files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
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
  });

  function handleFileSelection(file) {
    if (!file.type.startsWith('image/')) {
      alert('Please upload an image file (PNG, JPG, JPEG).');
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

      // Generate a canvas dummy preview showing the label text
      const canvas = document.createElement('canvas');
      canvas.width = 600;
      canvas.height = 340;
      const ctx = canvas.getContext('2d');
      
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.strokeStyle = "#cbd5e1";
      ctx.lineWidth = 4;
      ctx.strokeRect(8, 8, canvas.width - 16, canvas.height - 16);

      ctx.fillStyle = "#1e293b";
      ctx.font = "bold 16px Inter, sans-serif";
      ctx.fillText(`[PRESET DEMO LABEL] ${preset.title}`, 24, 38);

      ctx.font = "14px 'JetBrains Mono', monospace";
      ctx.fillStyle = "#334155";
      const lines = preset.text.split('\n');
      lines.forEach((l, idx) => {
        ctx.fillText(l, 24, 75 + (idx * 26));
      });

      imagePreview.src = canvas.toDataURL('image/png');
      dropzonePrompt.classList.add('hidden');
      previewContainer.classList.remove('hidden');
      btnAnalyze.disabled = false;
    });
  });

  function clearActivePreset() {
    presetButtons.forEach(b => b.classList.remove('active'));
  }

  // Check Compliance Button
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
    } catch (err) {
      console.error('Scan error:', err);
      alert(`Error scanning label: ${err.message}`);
    } finally {
      setLoading(false);
    }
  });

  function setLoading(isLoading) {
    if (isLoading) {
      btnAnalyze.disabled = true;
      btnAnalyzeText.textContent = "Screening In Progress...";
      if (scanningProgressCard) scanningProgressCard.classList.remove('hidden');
      if (resultsSection) resultsSection.classList.add('hidden');
    } else {
      btnAnalyze.disabled = false;
      btnAnalyzeText.textContent = "🔍 Check Compliance";
      if (scanningProgressCard) scanningProgressCard.classList.add('hidden');
    }
  }

  // Render screening results
  function renderResults(report) {
    scanMetaText.innerHTML = `<strong>Scan Reference ID:</strong> ${report.scan_id} &bull; <strong>Evaluated on:</strong> ${report.timestamp}`;
    
    // 1. Compliance Summary Progress Bar (Above status banner)
    if (report.is_exempt) {
      if (summaryBarTitle) summaryBarTitle.textContent = "Statutory Exemption Applied (Rule 3 / Rule 26)";
      if (summaryBarPct) summaryBarPct.textContent = "EXEMPT";
      if (summaryFill) {
        summaryFill.style.width = "100%";
        summaryFill.className = "summary-fill summary-fill-exempt";
      }
      if (summaryHint) summaryHint.textContent = "Package meets statutory exemption criteria under Rule 3 / Rule 26. Standard retail declaration rules are waived.";
    } else {
      const totalFields = 5;
      const passedFields = (report.fields || []).filter(f => f.status === 'PASS').length;
      const hasUncertain = (report.fields || []).some(f => f.status === 'UNCERTAIN');
      const hasWarning = (report.fields || []).some(f => f.status === 'WARNING');
      const pct = Math.round((passedFields / totalFields) * 100);

      if (summaryBarTitle) summaryBarTitle.textContent = `Compliance Score: ${passedFields} of ${totalFields} Mandatory Declarations Passed`;
      if (summaryBarPct) summaryBarPct.textContent = `${pct}%`;
      if (summaryFill) {
        summaryFill.style.width = `${pct}%`;
        if (passedFields === totalFields) {
          summaryFill.className = 'summary-fill';
        } else if (hasWarning || hasUncertain) {
          summaryFill.className = 'summary-fill summary-fill-warning';
        } else {
          summaryFill.className = 'summary-fill summary-fill-danger';
        }
      }
      if (summaryHint) {
        if (passedFields === totalFields) {
          summaryHint.textContent = "All 5 mandatory declarations meet Legal Metrology (Packaged Commodities) Rules, 2011 specifications.";
        } else {
          summaryHint.textContent = `${totalFields - passedFields} mandatory declaration(s) are missing or non-compliant under Rule 6.`;
        }
      }
    }

    // 2. Status Banner Styling
    statusBanner.className = 'status-banner';
    const overall = (report.overall_status || '').toUpperCase();

    if (overall === 'COMPLIANT') {
      statusBanner.classList.add('compliant');
      statusIcon.textContent = '✓';
      statusTitle.textContent = 'COMPLIANT';
      statusDesc.textContent = 'All 5 mandatory declarations meet Legal Metrology (Packaged Commodities) Rules, 2011 specifications.';
    } else if (overall === 'EXEMPT') {
      statusBanner.classList.add('exempt');
      statusIcon.textContent = '🛡️';
      statusTitle.textContent = 'EXEMPT FROM PACKAGED COMMODITY RULES';
      statusDesc.textContent = 'Package meets statutory exemption criteria under Rule 3 / Rule 26. Standard retail declaration rules are waived.';
    } else if (overall === 'UNCERTAIN') {
      statusBanner.classList.add('uncertain');
      statusIcon.textContent = '⚠️';
      statusTitle.textContent = 'UNCERTAIN — LOW OCR CONFIDENCE';
      statusDesc.textContent = 'One or more fields have low OCR confidence (< 60%). Manual pre-inspection review is recommended.';
    } else {
      statusBanner.classList.add('non_compliant');
      statusIcon.textContent = '✕';
      statusTitle.textContent = 'NON-COMPLIANT / ANOMALY FLAGGED';
      statusDesc.textContent = 'One or more mandatory declarations are missing, non-compliant, or have price/unit anomalies.';
    }

    // 3. Exemption box
    if (report.is_exempt && report.exemption_details) {
      exemptionBox.classList.remove('hidden');
      exemptionReasonText.textContent = report.exemption_details.reason || 'Package meets exemption conditions.';
      exemptionRefText.textContent = `Reference: ${report.exemption_details.rule_reference || 'Rule 3 & Rule 26'}`;
      fieldsContainer.innerHTML = '';
    } else {
      exemptionBox.classList.add('hidden');
      renderFieldCards(report.fields);
    }

    // 4. OCR Raw text
    const lines = report.extracted_lines || [];
    ocrLineCount.textContent = lines.length > 0 ? lines.length : (report.raw_text ? report.raw_text.split('\n').length : 0);
    rawOcrText.textContent = report.raw_text || lines.map(l => l.text).join('\n') || "(No text detected)";

    resultsSection.classList.remove('hidden');
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function renderFieldCards(fields) {
    fieldsContainer.innerHTML = '';
    if (!fields || fields.length === 0) return;

    fields.forEach(field => {
      const card = document.createElement('div');
      card.className = 'field-card';

      let statusBadgeClass = 'badge-pass';
      let statusCardClass = 'status-pass';
      let icon = '✓';
      const statusUpper = (field.status || '').toUpperCase();

      if (statusUpper === 'FAIL') {
        statusBadgeClass = 'badge-fail';
        statusCardClass = 'status-fail';
        icon = '✕';
      } else if (statusUpper === 'WARNING') {
        statusBadgeClass = 'badge-warning';
        statusCardClass = 'status-warning';
        icon = '⚠️';
      } else if (statusUpper === 'UNCERTAIN') {
        statusBadgeClass = 'badge-uncertain';
        statusCardClass = 'status-uncertain';
        icon = '⚠️';
      }

      card.classList.add(statusCardClass);

      let confTagHtml = '';
      if (field.confidence_score !== null && field.confidence_score !== undefined) {
        const pct = Math.round(field.confidence_score * 100);
        const lowClass = field.confidence_score < 0.60 ? 'field-confidence-low' : '';
        confTagHtml = `<span class="field-confidence-tag ${lowClass}">OCR: ${pct}%</span>`;
      }

      const matchedHtml = field.matched_text 
        ? `<div class="field-matched-text">${escapeHtml(field.matched_text)} ${confTagHtml}</div>` 
        : `<div class="field-desc-text"><em>No matching declaration detected on label</em></div>`;

      const flagHtml = field.flag 
        ? `<div class="field-flag-warning">⚠️ ${escapeHtml(field.flag)}</div>` 
        : '';

      const detailsHtml = `<div class="field-desc-text">${escapeHtml(field.details)}</div>`;

      card.innerHTML = `
        <div class="field-name-block">
          <span class="field-name">${escapeHtml(field.field_name)}</span>
          <span class="field-rule">${escapeHtml(field.rule_reference)}</span>
        </div>
        <div>
          <span class="badge ${statusBadgeClass}">${icon} ${statusUpper}</span>
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
    const originalText = btnExportPdf.textContent;
    btnExportPdf.textContent = 'Generating PDF...';

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
    } catch (err) {
      console.error('PDF export error:', err);
      alert(`Could not export PDF report: ${err.message}`);
    } finally {
      btnExportPdf.disabled = false;
      btnExportPdf.textContent = originalText;
    }
  });

  function escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
