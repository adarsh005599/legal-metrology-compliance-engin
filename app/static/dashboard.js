// Legal Metrology Compliance-Assist Engine Dashboard Logic

let breakdownChartInstance = null;
let volumeBarChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
  const btnRefresh = document.getElementById('btnRefresh');
  const refreshIcon = document.getElementById('refreshIcon');

  loadDashboardData();

  if (btnRefresh) {
    btnRefresh.addEventListener('click', async () => {
      refreshIcon.classList.add('rotating');
      btnRefresh.disabled = true;
      await loadDashboardData();
      setTimeout(() => {
        refreshIcon.classList.remove('rotating');
        btnRefresh.disabled = false;
      }, 400);
    });
  }
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

    let recentScans = [];
    if (recentRes && recentRes.ok) {
      recentScans = await recentRes.json();
    }

    updateMetricCards(summary);
    renderCharts(summary);
    renderRecentTable(recentScans);

  } catch (err) {
    console.error('Error loading dashboard data:', err);
    updateMetricCards({ total: 0, compliant: 0, non_compliant: 0, exempt: 0, uncertain: 0 });
    renderRecentTable([]);
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
      ? ['Compliant (Pass)', 'Non-Compliant (Fail)', 'Statutory Exempt', 'Uncertain (Low OCR)']
      : ['No Data Yet', '', '', ''];
    const bgColors = total > 0
      ? ['#16a34a', '#dc2626', '#2563eb', '#f59e0b']
      : ['#e2e8f0', '#e2e8f0', '#e2e8f0', '#e2e8f0'];

    breakdownChartInstance = new Chart(breakdownCtx, {
      type: 'doughnut',
      data: {
        labels: dataLabels,
        datasets: [{
          data: dataValues,
          backgroundColor: bgColors,
          borderWidth: 2,
          borderColor: '#ffffff',
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
              font: { family: 'Inter', size: 11 },
              padding: 12
            }
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                if (total === 0) return 'No scan data recorded';
                const label = context.label || '';
                const val = context.parsed || 0;
                const pct = total > 0 ? Math.round((val / total) * 100) : 0;
                return ` ${label}: ${val} (${pct}%)`;
              }
            }
          }
        },
        cutout: '65%'
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
          backgroundColor: ['#22c55e', '#ef4444', '#3b82f6', '#f59e0b'],
          borderRadius: 6,
          maxBarThickness: 45
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => ` Volume: ${context.parsed.y} labels`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              precision: 0,
              font: { family: 'Inter', size: 11 }
            },
            grid: { color: '#f1f5f9' }
          },
          x: {
            ticks: { font: { family: 'Inter', size: 11, weight: '500' } },
            grid: { display: false }
          }
        }
      }
    });
  }
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
  if (recordCountEl) recordCountEl.textContent = `Showing ${scans.length} recent record${scans.length === 1 ? '' : 's'}`;

  scans.forEach(scan => {
    const tr = document.createElement('tr');

    // Format timestamp
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

    // Status badge formatting
    const rawStatus = (scan.status || 'unknown').toLowerCase();
    let badgeClass = 'badge-pass';
    let badgeIcon = '✓';
    let statusText = 'COMPLIANT';

    if (rawStatus === 'non-compliant' || rawStatus === 'fail') {
      badgeClass = 'badge-fail';
      badgeIcon = '✕';
      statusText = 'NON-COMPLIANT';
    } else if (rawStatus === 'exempt') {
      badgeClass = 'badge-exempt';
      badgeIcon = '🛡️';
      statusText = 'EXEMPT';
    } else if (rawStatus === 'uncertain') {
      badgeClass = 'badge-uncertain';
      badgeIcon = '⚠️';
      statusText = 'UNCERTAIN';
    }

    // Fields passed display
    let fieldsDisplay = `${scan.fields_passed || 0}/${scan.fields_total || 5}`;
    if (rawStatus === 'exempt') {
      fieldsDisplay = '<span class="text-muted">N/A (Exempt)</span>';
    } else if (scan.fields_passed === scan.fields_total && scan.fields_total > 0) {
      fieldsDisplay = `<span class="text-success font-semibold">${fieldsDisplay} (100%)</span>`;
    } else {
      fieldsDisplay = `<span class="text-danger font-semibold">${fieldsDisplay}</span>`;
    }

    // Summary Finding Text
    let findingSummary = 'All 5 mandatory declarations verified';
    if (rawStatus === 'exempt') {
      findingSummary = 'Statutory exemption applied (Rule 3 / 26)';
    } else if (rawStatus === 'uncertain') {
      findingSummary = 'Low OCR confidence region detected (<60%)';
    } else if (rawStatus === 'non-compliant') {
      const results = scan.field_results || [];
      const failed = results.filter(f => f.status === 'FAIL' || f.status === 'WARNING').map(f => f.field_name);
      if (failed.length > 0) {
        findingSummary = `Flagged: ${failed.join(', ')}`;
      } else {
        findingSummary = 'Mandatory declaration missing or flagged';
      }
    }

    tr.innerHTML = `
      <td class="cell-time">${escapeHtml(timeStr)}</td>
      <td class="cell-ref"><code class="ref-code">${escapeHtml(scan.scan_ref_id || 'N/A')}</code></td>
      <td class="cell-filename">${escapeHtml(scan.filename || 'uploaded_image.png')}</td>
      <td><span class="badge ${badgeClass}">${badgeIcon} ${statusText}</span></td>
      <td>${fieldsDisplay}</td>
      <td class="cell-summary">${escapeHtml(findingSummary)}</td>
    `;

    tableBody.appendChild(tr);
  });
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
