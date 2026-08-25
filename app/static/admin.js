// MetraSetu: Admin & Statutory Compliance Panel Controller

document.addEventListener('DOMContentLoaded', () => {
  // State
  let violationsData = [];
  let rulesData = [];
  let amendmentsData = [];
  let currentFilter = 'ALL';

  // Auth Elements & State
  const STORAGE_AUTH_KEY = 'metrasetu_admin_session';
  const adminLoginSection = document.getElementById('adminLoginSection');
  const adminConsoleSection = document.getElementById('adminConsoleSection');
  const adminLoginForm = document.getElementById('adminLoginForm');
  const adminEmailInput = document.getElementById('adminEmail');
  const adminPasswordInput = document.getElementById('adminPassword');
  const btnAutofillDemo = document.getElementById('btnAutofillDemo');
  const btnLogoutAdmin = document.getElementById('btnLogoutAdmin');
  const officerNameDisplay = document.getElementById('officerNameDisplay');
  const officerRoleDisplay = document.getElementById('officerRoleDisplay');

  // Elements
  const kpiViolationCount = document.getElementById('kpiViolationCount');
  const kpiPendingCount = document.getElementById('kpiPendingCount');
  const kpiActiveRulesCount = document.getElementById('kpiActiveRulesCount');

  const violationsTableBody = document.getElementById('violationsTableBody');
  const violationSearchInput = document.getElementById('violationSearchInput');
  const filterButtons = document.querySelectorAll('#violationStatusFilter .btn-pill');

  const rulesGridContainer = document.getElementById('rulesGridContainer');
  const amendmentsTimeline = document.getElementById('amendmentsTimeline');

  const tabButtons = document.querySelectorAll('.admin-tab-btn');
  const tabContents = document.querySelectorAll('.admin-tab-content');

  // Modals
  const modalEditRule = document.getElementById('modalEditRule');
  const formEditRule = document.getElementById('formEditRule');
  const btnAddNewRule = document.getElementById('btnAddNewRule');
  const btnCloseRuleModal = document.getElementById('btnCloseRuleModal');
  const btnCancelEditRule = document.getElementById('btnCancelEditRule');

  const modalPublishAmd = document.getElementById('modalPublishAmd');
  const formPublishAmd = document.getElementById('formPublishAmd');
  const btnPublishAmd = document.getElementById('btnPublishAmd');
  const btnCloseAmdModal = document.getElementById('btnCloseAmdModal');
  const btnCancelAmd = document.getElementById('btnCancelAmd');

  // ==============================================================================
  // AUTHENTICATION LOGIC
  // ==============================================================================
  function checkAuthState() {
    try {
      const raw = sessionStorage.getItem(STORAGE_AUTH_KEY);
      if (raw) {
        const session = JSON.parse(raw);
        if (session && session.token) {
          showAdminConsole(session);
          return true;
        }
      }
    } catch (e) {
      console.warn('Session parse error:', e);
    }
    showLoginForm();
    return false;
  }

  function showLoginForm() {
    if (adminLoginSection) adminLoginSection.classList.remove('hidden');
    if (adminConsoleSection) adminConsoleSection.classList.add('hidden');
  }

  function showAdminConsole(session) {
    if (adminLoginSection) adminLoginSection.classList.add('hidden');
    if (adminConsoleSection) adminConsoleSection.classList.remove('hidden');

    if (officerNameDisplay) officerNameDisplay.textContent = session.name || 'Senior Metrology Officer';
    if (officerRoleDisplay) officerRoleDisplay.textContent = `${session.role || 'State Controller'} (${session.badge_id || 'LM-OFFICER'})`;

    loadAllData();
  }

  // Handle Login Submit
  if (adminLoginForm) {
    adminLoginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = adminEmailInput.value.trim();
      const password = adminPasswordInput.value;

      try {
        const resp = await fetch('/api/admin/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });

        if (!resp.ok) {
          const errData = await resp.json().catch(() => ({}));
          throw new Error(errData.detail || 'Invalid email or password');
        }

        const data = await resp.json();
        sessionStorage.setItem(STORAGE_AUTH_KEY, JSON.stringify(data.session));
        showToast(`Officer authenticated: ${data.session.name}`, 'success');
        showAdminConsole(data.session);
      } catch (err) {
        console.error('Login error:', err);
        showToast(err.message, 'error');
      }
    });
  }

  // Handle Demo Autofill
  if (btnAutofillDemo) {
    btnAutofillDemo.addEventListener('click', () => {
      adminEmailInput.value = 'admin@metrasetu.gov.in';
      adminPasswordInput.value = 'MetraAdmin@2026';
      showToast('Demo Officer credentials filled! Click Sign In.', 'info');
    });
  }

  // Handle Logout
  if (btnLogoutAdmin) {
    btnLogoutAdmin.addEventListener('click', () => {
      sessionStorage.removeItem(STORAGE_AUTH_KEY);
      showToast('Signed out of Admin Compliance Terminal', 'info');
      showLoginForm();
    });
  }


  // SVG Icons
  const ICONS = {
    warning: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    check: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    fileText: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
    pdf: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
    edit: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>'
  };

  // ==============================================================================
  // TAB NAVIGATION
  // ==============================================================================
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.getAttribute('data-tab');
      tabButtons.forEach(b => b.classList.remove('active'));
      tabContents.forEach(c => {
        c.classList.remove('active');
        c.classList.add('hidden');
      });

      btn.classList.add('active');
      const targetContent = document.getElementById(targetTab);
      if (targetContent) {
        targetContent.classList.remove('hidden');
        targetContent.classList.add('active');
      }
    });
  });

  // ==============================================================================
  // DATA FETCHING & INITIALIZATION
  // ==============================================================================
  async function loadAllData() {
    try {
      await Promise.all([
        fetchViolations(),
        fetchRules(),
        fetchAmendments()
      ]);
    } catch (e) {
      console.error('Error loading admin data:', e);
      showToast('Error loading compliance data', 'error');
    }
  }

  async function fetchViolations() {
    try {
      const resp = await fetch('/api/admin/violations');
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      violationsData = await resp.json();
      updateViolationsKPIs();
      renderViolationsTable();
    } catch (e) {
      console.error('Failed to load violations:', e);
      violationsTableBody.innerHTML = `<tr><td colspan="7" class="loading-cell text-danger">Failed to load violations registry: ${e.message}</td></tr>`;
    }
  }

  async function fetchRules() {
    try {
      const resp = await fetch('/api/admin/rules');
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      rulesData = await resp.json();
      if (kpiActiveRulesCount) {
        const activeCount = rulesData.filter(r => r.is_active !== false).length;
        kpiActiveRulesCount.textContent = activeCount;
      }
      renderRulesGrid();
    } catch (e) {
      console.error('Failed to load rules:', e);
    }
  }

  async function fetchAmendments() {
    try {
      const resp = await fetch('/api/admin/amendments');
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      amendmentsData = await resp.json();
      renderAmendmentsTimeline();
    } catch (e) {
      console.error('Failed to load amendments:', e);
    }
  }

  function updateViolationsKPIs() {
    if (kpiViolationCount) kpiViolationCount.textContent = violationsData.length;
    if (kpiPendingCount) {
      const pending = violationsData.filter(v => v.action_status === 'PENDING_REVIEW').length;
      kpiPendingCount.textContent = pending;
    }
  }

  // ==============================================================================
  // VIOLATIONS REGISTRY RENDERING & ACTIONS
  // ==============================================================================
  function renderViolationsTable() {
    const searchTerm = (violationSearchInput.value || '').toLowerCase().trim();

    let filtered = violationsData.filter(v => {
      // Status Filter
      if (currentFilter !== 'ALL' && v.action_status !== currentFilter) {
        return false;
      }
      // Search Filter
      if (searchTerm) {
        const matchId = (v.scan_id || '').toLowerCase().includes(searchTerm);
        const matchTypes = (v.violation_types || []).some(t => t.toLowerCase().includes(searchTerm));
        const matchSection = (v.section_code || '').toLowerCase().includes(searchTerm);
        return matchId || matchTypes || matchSection;
      }
      return true;
    });

    if (filtered.length === 0) {
      violationsTableBody.innerHTML = `
        <tr>
          <td colspan="7" class="loading-cell text-muted">
            No raised violations matching current filter criteria.
          </td>
        </tr>
      `;
      return;
    }

    violationsTableBody.innerHTML = '';
    filtered.forEach(v => {
      const tr = document.createElement('tr');

      // Severity Badge
      let sevClass = 'sev-high';
      if (v.severity === 'CRITICAL') sevClass = 'sev-critical';
      else if (v.severity === 'MEDIUM') sevClass = 'sev-medium';

      // Violation Tags HTML
      const tagsHtml = (v.violation_types || []).map(t => 
        `<span class="violation-tag">${escapeHtml(t)}</span>`
      ).join(' ') || '<span class="text-muted">Statutory declaration discrepancy</span>';

      // Status select options
      const statuses = [
        { val: 'PENDING_REVIEW', label: 'Pending Review' },
        { val: 'DRAFT_NOTICE', label: 'Notice Drafted' },
        { val: 'ESCALATED_TO_OFFICER', label: 'Escalated to Officer' },
        { val: 'RESOLVED', label: 'Resolved / Compounded' }
      ];

      const selectOptions = statuses.map(s => 
        `<option value="${s.val}" ${v.action_status === s.val ? 'selected' : ''}>${s.label}</option>`
      ).join('');

      tr.innerHTML = `
        <td class="scan-id-cell">
          <span class="ref-badge-mono">${escapeHtml(v.scan_id)}</span>
        </td>
        <td class="timestamp-cell">
          <span class="text-muted-sm">${escapeHtml(v.timestamp || 'N/A')}</span>
        </td>
        <td class="violation-cell">
          <div class="violation-tags-wrap">${tagsHtml}</div>
        </td>
        <td>
          <span class="severity-badge ${sevClass}">${v.severity}</span>
        </td>
        <td>
          <span class="section-badge">${escapeHtml(v.section_code || 'Section 36(1)')}</span>
        </td>
        <td>
          <select class="form-select-sm status-dropdown" data-scanid="${escapeHtml(v.scan_id)}">
            ${selectOptions}
          </select>
        </td>
        <td class="action-cell">
          <button type="button" class="btn btn-secondary btn-xs btn-pdf-export" data-scanid="${escapeHtml(v.scan_id)}" title="Download Stamped PDF Inspection Report">
            ${ICONS.pdf}
            <span>PDF</span>
          </button>
        </td>
      `;

      violationsTableBody.appendChild(tr);
    });

    // Wire status dropdown change handlers
    document.querySelectorAll('.status-dropdown').forEach(sel => {
      sel.addEventListener('change', async (e) => {
        const scanId = sel.getAttribute('data-scanid');
        const newStatus = sel.value;
        await updateViolationAction(scanId, newStatus);
      });
    });

    // Wire PDF download buttons
    document.querySelectorAll('.btn-pdf-export').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const scanId = btn.getAttribute('data-scanid');
        await downloadViolationPdf(scanId);
      });
    });
  }

  async function updateViolationAction(scanId, newStatus) {
    try {
      const resp = await fetch(`/api/admin/violations/${encodeURIComponent(scanId)}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      
      // Update local state
      const item = violationsData.find(v => v.scan_id === scanId);
      if (item) item.action_status = newStatus;
      updateViolationsKPIs();
      showToast(`Violation ${scanId} status updated to ${newStatus}`, 'success');
    } catch (e) {
      console.error('Error updating status:', e);
      showToast(`Failed to update status: ${e.message}`, 'error');
    }
  }

  async function downloadViolationPdf(scanId) {
    try {
      showToast(`Preparing inspection PDF for ${scanId}...`, 'info');
      // Fetch scan details from recent scans
      const recentResp = await fetch('/api/scans/recent?limit=100');
      const recent = await recentResp.json();
      const match = recent.find(s => s.scan_id === scanId);
      if (!match) {
        throw new Error("Full scan details not found in cache.");
      }

      const pdfResp = await fetch('/api/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(match)
      });
      if (!pdfResp.ok) throw new Error("PDF generator failed");

      const blob = await pdfResp.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `MetraSetu_Enforcement_Notice_${scanId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      showToast("PDF report downloaded successfully", "success");
    } catch (e) {
      console.error('PDF error:', e);
      showToast(`Failed to export PDF: ${e.message}`, 'error');
    }
  }

  // Filter Buttons
  filterButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      filterButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentFilter = btn.getAttribute('data-filter');
      renderViolationsTable();
    });
  });

  if (violationSearchInput) {
    violationSearchInput.addEventListener('input', () => {
      renderViolationsTable();
    });
  }

  // ==============================================================================
  // STATUTORY RULES & LAWS MANAGER RENDERING
  // ==============================================================================
  function renderRulesGrid() {
    rulesGridContainer.innerHTML = '';
    rulesData.forEach(rule => {
      const card = document.createElement('div');
      card.className = `rule-card ${rule.is_active === false ? 'rule-inactive' : ''}`;

      card.innerHTML = `
        <div class="rule-card-header">
          <div class="rule-title-group">
            <span class="rule-code-badge">${escapeHtml(rule.rule_code || 'Rule')}</span>
            <h4 class="rule-title">${escapeHtml(rule.title)}</h4>
          </div>
          <span class="rule-status-badge ${rule.is_active !== false ? 'status-active' : 'status-inactive'}">
            ${rule.is_active !== false ? 'ACTIVE' : 'SUSPENDED'}
          </span>
        </div>
        <p class="rule-statute-sub">${escapeHtml(rule.statute || 'Legal Metrology Rules, 2011')}</p>
        <p class="rule-desc">${escapeHtml(rule.description)}</p>
        
        <div class="rule-penalty-box">
          <strong>Prescribed Penalty:</strong>
          <span>${escapeHtml(rule.section_penalty || 'Section 36(1)')}</span>
        </div>

        <div class="rule-card-footer">
          <span class="rule-gazette-tag">${escapeHtml(rule.gazette_reference || 'Statutory Ref')}</span>
          <button type="button" class="btn btn-secondary btn-xs btn-edit-rule" data-ruleid="${escapeHtml(rule.id)}">
            ${ICONS.edit}
            <span>Edit Rule</span>
          </button>
        </div>
      `;

      rulesGridContainer.appendChild(card);
    });

    // Wire edit rule buttons
    document.querySelectorAll('.btn-edit-rule').forEach(btn => {
      btn.addEventListener('click', () => {
        const ruleId = btn.getAttribute('data-ruleid');
        openEditRuleModal(ruleId);
      });
    });
  }

  function openEditRuleModal(ruleId) {
    const rule = rulesData.find(r => r.id === ruleId);
    if (!rule) return;

    document.getElementById('editRuleId').value = rule.id;
    document.getElementById('editRuleCode').value = rule.rule_code || '';
    document.getElementById('editStatute').value = rule.statute || '';
    document.getElementById('editRuleName').value = rule.title || '';
    document.getElementById('editDescription').value = rule.description || '';
    document.getElementById('editPenalty').value = rule.section_penalty || '';
    document.getElementById('editGazetteRef').value = rule.gazette_reference || '';
    document.getElementById('editIsActive').value = rule.is_active !== false ? 'true' : 'false';

    document.getElementById('modalRuleTitle').textContent = `Edit Rule: ${rule.rule_code || rule.title}`;
    modalEditRule.classList.remove('hidden');
  }

  if (btnAddNewRule) {
    btnAddNewRule.addEventListener('click', () => {
      formEditRule.reset();
      document.getElementById('editRuleId').value = '';
      document.getElementById('modalRuleTitle').textContent = 'Add New Statutory Rule';
      modalEditRule.classList.remove('hidden');
    });
  }

  if (btnCloseRuleModal) btnCloseRuleModal.addEventListener('click', () => modalEditRule.classList.add('hidden'));
  if (btnCancelEditRule) btnCancelEditRule.addEventListener('click', () => modalEditRule.classList.add('hidden'));

  if (formEditRule) {
    formEditRule.addEventListener('submit', async (e) => {
      e.preventDefault();
      const ruleId = document.getElementById('editRuleId').value;
      const payload = {
        rule_code: document.getElementById('editRuleCode').value.trim(),
        statute: document.getElementById('editStatute').value.trim(),
        title: document.getElementById('editRuleName').value.trim(),
        description: document.getElementById('editDescription').value.trim(),
        section_penalty: document.getElementById('editPenalty').value.trim(),
        gazette_reference: document.getElementById('editGazetteRef').value.trim(),
        is_active: document.getElementById('editIsActive').value === 'true'
      };

      try {
        let resp;
        if (ruleId) {
          resp = await fetch(`/api/admin/rules/${encodeURIComponent(ruleId)}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
        } else {
          resp = await fetch('/api/admin/rules', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
        }

        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        modalEditRule.classList.add('hidden');
        showToast('Statutory rule successfully saved!', 'success');
        await fetchRules();
      } catch (err) {
        console.error('Error saving rule:', err);
        showToast(`Failed to save rule: ${err.message}`, 'error');
      }
    });
  }

  // ==============================================================================
  // GAZETTE AMENDMENTS FEED & PUBLISHING
  // ==============================================================================
  function renderAmendmentsTimeline() {
    amendmentsTimeline.innerHTML = '';
    if (amendmentsData.length === 0) {
      amendmentsTimeline.innerHTML = '<p class="text-muted">No published circulars found.</p>';
      return;
    }

    amendmentsData.forEach(amd => {
      const item = document.createElement('div');
      item.className = 'amendment-item';

      item.innerHTML = `
        <div class="amendment-dot"></div>
        <div class="amendment-content-box">
          <div class="amendment-meta-row">
            <span class="amendment-notif-badge">${escapeHtml(amd.notification_no || 'Notification')}</span>
            <span class="amendment-date">${escapeHtml(amd.gazette_date || '')}</span>
            <span class="amendment-status-tag status-enforced">${escapeHtml(amd.status || 'ENFORCED')}</span>
          </div>
          <h4 class="amendment-title">${escapeHtml(amd.title)}</h4>
          <p class="amendment-summary">${escapeHtml(amd.summary)}</p>
          <div class="amendment-footer">
            <span class="amendment-auth">🏛️ ${escapeHtml(amd.authority || 'Ministry of Consumer Affairs')}</span>
          </div>
        </div>
      `;

      amendmentsTimeline.appendChild(item);
    });
  }

  if (btnPublishAmd) {
    btnPublishAmd.addEventListener('click', () => {
      formPublishAmd.reset();
      document.getElementById('amdDate').value = new Date().toISOString().split('T')[0];
      modalPublishAmd.classList.remove('hidden');
    });
  }

  if (btnCloseAmdModal) btnCloseAmdModal.addEventListener('click', () => modalPublishAmd.classList.add('hidden'));
  if (btnCancelAmd) btnCancelAmd.addEventListener('click', () => modalPublishAmd.classList.add('hidden'));

  if (formPublishAmd) {
    formPublishAmd.addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = {
        notification_no: document.getElementById('amdNotifNo').value.trim(),
        gazette_date: document.getElementById('amdDate').value,
        title: document.getElementById('amdTitle').value.trim(),
        summary: document.getElementById('amdSummary').value.trim(),
        authority: document.getElementById('amdAuthority').value.trim(),
        status: 'ENFORCED'
      };

      try {
        const resp = await fetch('/api/admin/amendments', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

        modalPublishAmd.classList.add('hidden');
        showToast('Gazette amendment published successfully!', 'success');
        await fetchAmendments();
      } catch (err) {
        console.error('Error publishing amendment:', err);
        showToast(`Failed to publish: ${err.message}`, 'error');
      }
    });
  }

  // Toast Helper
  function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <div class="toast-content">
        <span class="toast-icon">${type === 'success' ? ICONS.check : ICONS.warning}</span>
        <span class="toast-message">${escapeHtml(message)}</span>
      </div>
    `;
    container.appendChild(toast);
    setTimeout(() => {
      toast.classList.add('toast-fade-out');
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  function escapeHtml(text) {
    if (!text) return '';
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return String(text).replace(/[&<>"']/g, m => map[m]);
  }

  // Language Change Listener
  window.addEventListener('languageChanged', () => {
    renderViolationsTable();
    renderRulesGrid();
    renderAmendmentsTimeline();
  });

  // Start initialization by checking auth state
  checkAuthState();
});
