// Legal Metrology Compliance-Assist Engine Dashboard Logic — "Liquid Glass & Calibration" Edition

let breakdownChartInstance = null;
let volumeBarChartInstance = null;
let allFetchedScans = [];
let activeFilter = 'all';
let searchQuery = '';

const PALETTE = {
  inkNavy: '#101D33',
  brass: '#B4833E',
  pass: '#059669',
  fail: '#DC2626',
  warning: '#D97706',
  exempt: '#2563EB',
  uncertain: '#B4833E',
  textPrimary: '#111827',
  textSecondary: '#4B5563',
  border: '#E5E7EB'
};

document.addEventListener('DOMContentLoaded', () => {
  const btnRefresh = document.getElementById('btnRefresh');
  const refreshIconSvg = document.getElementById('refreshIconSvg');
  const scanSearchInput = document.getElementById('scanSearchInput');
  const filterPills = document.querySelectorAll('.filter-pill');

  loadDashboardData();

  if (btnRefresh) {
    btnRefresh.addEventListener('click', async () => {
      if (refreshIconSvg) refreshIconSvg.classList.add('rotating');
      btnRefresh.disabled = true;
      showToast('Refreshing live telemetry...', 'info');
      await loadDashboardData();
      setTimeout(() => {
        if (refreshIconSvg) refreshIconSvg.classList.remove('rotating');
        btnRefresh.disabled = false;
        showToast('Dashboard telemetry synchronized', 'success');
      }, 450);
    });
  }

  if (scanSearchInput) {
    scanSearchInput.addEventListener('input', (e) => {
      searchQuery = e.target.value.toLowerCase().trim();
      applyFiltersAndRender();
    });
  }

  filterPills.forEach(pill => {
    pill.addEventListener('click', () => {
      filterPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      activeFilter = pill.getAttribute('data-filter') || 'all';
      applyFiltersAndRender();
    });
  });
});


async function loadDashboardData() {
  try {
    const [summaryRes, recentRes] = await Promise.all([
      fetch('/api/scans/summary').catch(() => null),
      fetch('/api/scans/recent').catch(() => null)
    ]);

    let summary = { total: 0, compliant: 0, non_compliant: 0, exempt: 0, uncertain: 0 };
    if (summaryRes && summaryRes.ok) {
      summary = await summaryRes.json();
    }

    if (recentRes && recentRes.ok) {
      allFetchedScans = await recentRes.json();
    } else {
      allFetchedScans = [];
    }

    updateMetricCards(summary);
    renderCharts(summary);
    applyFiltersAndRender();

  } catch (err) {
    console.error('Error loading dashboard data:', err);
    updateMetricCards({ total: 0, compliant: 0, non_compliant: 0, exempt: 0, uncertain: 0 });
    applyFiltersAndRender();
  }
}


function updateMetricCards(summary) {
  const totalEl = document.getElementById('metricTotal');
  const compliantEl = document.getElementById('metricCompliant');
  const compliantPctEl = document.getElementById('metricCompliantPct');
  const nonCompliantEl = document.getElementById('metricNonCompliant');
  const exemptEl = document.getElementById('metricExempt');

  const total = summary.total || 0;
  const compliant = summary.compliant || 0;
  const nonCompliant = (summary.non_compliant || 0) + (summary.uncertain || 0);
  const exempt = summary.exempt || 0;

  if (totalEl) totalEl.textContent = total.toLocaleString();
  if (compliantEl) compliantEl.textContent = compliant.toLocaleString();
  if (nonCompliantEl) nonCompliantEl.textContent = nonCompliant.toLocaleString();
  if (exemptEl) exemptEl.textContent = exempt.toLocaleString();

  if (compliantPctEl) {
    const nonExemptTotal = total - exempt;
    if (nonExemptTotal > 0) {
      const pct = Math.round((compliant / nonExemptTotal) * 100);
      compliantPctEl.textContent = `${pct}% compliance rate (${compliant}/${nonExemptTotal})`;
    } else {
      compliantPctEl.textContent = `0% compliance rate`;
    }
  }
}


function renderCharts(summary) {
  const total = summary.total || 0;
  const compliant = summary.compliant || 0;
  const nonCompliant = summary.non_compliant || 0;
  const exempt = summary.exempt || 0;
  const uncertain = summary.uncertain || 0;

  // 1. Doughnut Breakdown Chart
  const breakdownCtx = document.getElementById('breakdownChart');
  if (breakdownCtx) {
    if (breakdownChartInstance) {
      breakdownChartInstance.destroy();
    }

    const dataValues = total > 0 ? [compliant, nonCompliant, exempt, uncertain] : [1, 0, 0, 0];
    const dataLabels = total > 0 
      ? ['Compliant (Pass)', 'Non-Compliant (Flagged)', 'Statutory Exempt', 'Uncertain (Low OCR)']
      : ['No Inspection Data Recorded', '', '', ''];
    const bgColors = total > 0 
      ? [PALETTE.pass, PALETTE.fail, PALETTE.exempt, PALETTE.warning]
      : ['#E5E7EB', '#E5E7EB', '#E5E7EB', '#E5E7EB'];

    breakdownChartInstance = new Chart(breakdownCtx, {
      type: 'doughnut',
      data: {
        labels: dataLabels,
        datasets: [{
          data: dataValues,
          backgroundColor: bgColors,
          borderWidth: 3,
          borderColor: '#FFFFFF',
          hoverOffset: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              boxWidth: 12,
              font: { family: "'IBM Plex Sans', sans-serif", size: 11 },
              color: PALETTE.textSecondary,
              padding: 14
            }
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                if (total === 0) return ' No scan data recorded';
                const label = context.label || '';
                const val = context.parsed || 0;
                const pct = total > 0 ? Math.round((val / total) * 100) : 0;
                return ` ${label}: ${val} (${pct}%)`;
              }
            }
          }
        },
        cutout: '68%'
      }
    });
  }

  // 2. Bar Chart
  const barCtx = document.getElementById('volumeBarChart');
  if (barCtx) {
    if (volumeBarChartInstance) {
      volumeBarChartInstance.destroy();
    }

    volumeBarChartInstance = new Chart(barCtx, {
      type: 'bar',
      data: {
        labels: ['Compliant', 'Non-Compliant', 'Exempt', 'Uncertain'],
        datasets: [{
          label: 'Scan Volume',
          data: [compliant, nonCompliant, exempt, uncertain],
          backgroundColor: [PALETTE.pass, PALETTE.fail, PALETTE.exempt, PALETTE.warning],
          borderRadius: 4,
          maxBarThickness: 44
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => ` Verified: ${context.parsed.y} labels`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              precision: 0,
              font: { family: "'IBM Plex Mono', monospace", size: 11 },
              color: PALETTE.textSecondary
            },
            grid: { color: 'rgba(229, 231, 235, 0.7)' }
          },
          x: {
            ticks: { 
              font: { family: "'IBM Plex Sans', sans-serif", size: 11, weight: '600' },
              color: PALETTE.textPrimary
            },
            grid: { display: false }
          }
        }
      }
    });
  }
}


function applyFiltersAndRender() {
  let filtered = [...allFetchedScans];

  // 1. Status Filter
  if (activeFilter === 'compliant') {
    filtered = filtered.filter(s => (s.status || '').toLowerCase() === 'compliant');
  } else if (activeFilter === 'non-compliant') {
    filtered = filtered.filter(s => {
      const st = (s.status || '').toLowerCase();
      return st === 'non-compliant' || st === 'fail' || st === 'warning' || st === 'uncertain';
    });
  } else if (activeFilter === 'exempt') {
    filtered = filtered.filter(s => (s.status || '').toLowerCase() === 'exempt');
  }

  // 2. Search Query Filter
  if (searchQuery) {
    filtered = filtered.filter(s => {
      const fn = (s.filename || '').toLowerCase();
      const ref = (s.scan_ref_id || '').toLowerCase();
      const status = (s.status || '').toLowerCase();
      return fn.includes(searchQuery) || ref.includes(searchQuery) || status.includes(searchQuery);
    });
  }

  renderRecentTable(filtered);
}


function renderRecentTable(scans) {
  const tableBody = document.getElementById('scansTableBody');
  const tableContainer = document.getElementById('tableContainer');
  const emptyState = document.getElementById('emptyState');
  const recordCountEl = document.getElementById('tableRecordCount');

  if (!tableBody) return;

  tableBody.innerHTML = '';

  if (!scans || scans.length === 0) {
    if (tableContainer) tableContainer.classList.add('hidden');
    if (emptyState) emptyState.classList.remove('hidden');
    if (recordCountEl) recordCountEl.textContent = 'Showing 0 records';
    return;
  }

  if (tableContainer) tableContainer.classList.remove('hidden');
  if (emptyState) emptyState.classList.add('hidden');
  if (recordCountEl) recordCountEl.textContent = `Showing ${scans.length} of ${allFetchedScans.length} record${allFetchedScans.length === 1 ? '' : 's'}`;

  scans.forEach(scan => {
    const tr = document.createElement('tr');

    let timeStr = scan.timestamp || '';
    if (timeStr) {
      try {
        const d = new Date(timeStr);
        timeStr = d.toLocaleString('en-IN', {
          day: '2-digit',
          month: 'short',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false
        });
      } catch (e) {
        timeStr = scan.timestamp;
      }
    }

    const rawStatus = (scan.status || 'unknown').toLowerCase();
    let tagClass = 'tag-pass';
    let tagIcon = '<svg class="stamp-tag-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';
    let statusText = 'COMPLIANT';

    if (rawStatus === 'non-compliant' || rawStatus === 'fail') {
      tagClass = 'tag-fail';
      tagIcon = '<svg class="stamp-tag-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
      statusText = 'NON-COMPLIANT';
    } else if (rawStatus === 'exempt') {
      tagClass = 'tag-exempt';
      tagIcon = '<svg class="stamp-tag-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>';
      statusText = 'EXEMPT';
    } else if (rawStatus === 'uncertain') {
      tagClass = 'tag-uncertain';
      tagIcon = '<svg class="stamp-tag-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>';
      statusText = 'UNCERTAIN';
    }

    let fieldsDisplay = `${scan.fields_passed || 0}/${scan.fields_total || 5}`;
    if (rawStatus === 'exempt') {
      fieldsDisplay = '<span style="color: var(--color-text-muted);">N/A (Exempt)</span>';
    } else if (scan.fields_passed === scan.fields_total && scan.fields_total > 0) {
      fieldsDisplay = `<span class="text-pass font-semibold">${fieldsDisplay} (100%)</span>`;
    } else {
      fieldsDisplay = `<span class="text-fail font-semibold">${fieldsDisplay}</span>`;
    }

    let findingSummary = 'All 5 mandatory declarations verified';
    if (rawStatus === 'exempt') {
      findingSummary = 'Statutory exemption applied (Rule 3 / 26)';
    } else if (rawStatus === 'uncertain') {
      findingSummary = 'Low OCR confidence region detected (<60%)';
    } else if (rawStatus === 'non-compliant') {
      const results = scan.field_results || [];
      const failed = results.filter(f => f.status === 'FAIL' || f.status === 'WARNING' || f.status === 'FLAGGED').map(f => f.field_name);
      if (failed.length > 0) {
        findingSummary = `Flagged: ${failed.join(', ')}`;
      } else {
        findingSummary = 'Mandatory declaration missing or flagged';
      }
    }

    tr.innerHTML = `
      <td class="cell-time">${escapeHtml(timeStr)}</td>
      <td><code class="ref-code">${escapeHtml(scan.scan_ref_id || 'N/A')}</code></td>
      <td class="cell-filename" title="${escapeHtml(scan.filename || '')}">${escapeHtml(scan.filename || 'uploaded_image.png')}</td>
      <td><span class="stamp-tag ${tagClass}">${tagIcon} ${statusText}</span></td>
      <td class="cell-fields">${fieldsDisplay}</td>
      <td class="cell-summary">${escapeHtml(findingSummary)}</td>
    `;

    tableBody.appendChild(tr);
  });
}


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
