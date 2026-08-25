// MetraSetu Assistant Chatbot Widget (Comrade AI Integration)

(function () {
  const CHATBOT_URL = 'https://comrade-ai.vercel.app/';

  function initChatbot() {
    if (document.getElementById('metrasetuChatbotWidget')) return;

    // Create Container
    const widget = document.createElement('div');
    widget.id = 'metrasetuChatbotWidget';
    widget.className = 'chatbot-widget-container';

    widget.innerHTML = `
      <!-- Floating Trigger Button -->
      <button type="button" id="chatbotTriggerBtn" class="chatbot-trigger-btn" aria-label="Open AI Assistant" title="Ask Legal Metrology AI">
        <div class="chatbot-trigger-icon-wrap">
          <svg class="chatbot-icon-closed" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            <path d="M12 7v2"/>
            <path d="M9 11h6"/>
          </svg>
          <svg class="chatbot-icon-opened hidden" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </div>
        <span class="chatbot-trigger-badge">AI</span>
        <span class="chatbot-trigger-tooltip" data-i18n="assistantBotTooltip">Ask AI Inspector</span>
      </button>

      <!-- Floating Chatbot Window -->
      <div id="chatbotWindow" class="chatbot-window hidden" role="dialog" aria-modal="false" aria-label="Legal Metrology Assistant">
        <!-- Header -->
        <div class="chatbot-header">
          <div class="chatbot-header-info">
            <div class="chatbot-avatar">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 2a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2 2 2 0 0 1-2-2V4a2 2 0 0 1 2-2z"/>
                <rect x="3" y="8" width="18" height="12" rx="3"/>
                <circle cx="9" cy="13" r="1" fill="currentColor"/>
                <circle cx="15" cy="13" r="1" fill="currentColor"/>
                <path d="M9 17h6"/>
              </svg>
              <span class="chatbot-live-status-dot"></span>
            </div>
            <div>
              <h4 class="chatbot-header-title" data-i18n="assistantBotTitle">MetraSetu Inspector Assistant</h4>
              <p class="chatbot-header-sub" data-i18n="assistantBotSubtitle">Comrade AI • Legal Guidance</p>
            </div>
          </div>
          <div class="chatbot-header-actions">
            <a href="${CHATBOT_URL}" target="_blank" rel="noopener noreferrer" class="chatbot-action-btn" title="Open in new window" data-i18n-title="assistantBotOpenTab" aria-label="Open in new window">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                <polyline points="15 3 21 3 21 9"/>
                <line x1="10" y1="14" x2="21" y2="3"/>
              </svg>
            </a>
            <button type="button" id="chatbotCloseBtn" class="chatbot-action-btn chatbot-close-btn" title="Close" data-i18n-title="assistantBotClose" aria-label="Close">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- Body / Iframe -->
        <div class="chatbot-body">
          <div class="chatbot-loader" id="chatbotLoader">
            <div class="chatbot-spinner"></div>
            <span>Connecting to Comrade AI...</span>
          </div>
          <iframe 
            id="chatbotIframe"
            data-src="${CHATBOT_URL}" 
            class="chatbot-iframe"
            title="Comrade AI Legal Metrology Assistant"
            allow="clipboard-write; microphone"
            loading="lazy">
          </iframe>
        </div>
      </div>
    `;

    document.body.appendChild(widget);

    const triggerBtn = document.getElementById('chatbotTriggerBtn');
    const closeBtn = document.getElementById('chatbotCloseBtn');
    const chatbotWindow = document.getElementById('chatbotWindow');
    const iconClosed = triggerBtn.querySelector('.chatbot-icon-closed');
    const iconOpened = triggerBtn.querySelector('.chatbot-icon-opened');
    const iframe = document.getElementById('chatbotIframe');
    const loader = document.getElementById('chatbotLoader');

    let isOpen = false;
    let isIframeLoaded = false;

    function openChatbot() {
      isOpen = true;
      chatbotWindow.classList.remove('hidden');
      requestAnimationFrame(() => {
        chatbotWindow.classList.add('is-open');
      });
      iconClosed.classList.add('hidden');
      iconOpened.classList.remove('hidden');
      triggerBtn.classList.add('is-active');

      // Lazy load iframe on first open
      if (!isIframeLoaded) {
        iframe.src = iframe.getAttribute('data-src');
        iframe.onload = () => {
          isIframeLoaded = true;
          if (loader) loader.classList.add('hidden');
        };
      }
    }

    function closeChatbot() {
      isOpen = false;
      chatbotWindow.classList.remove('is-open');
      setTimeout(() => {
        if (!isOpen) {
          chatbotWindow.classList.add('hidden');
        }
      }, 250);
      iconClosed.classList.remove('hidden');
      iconOpened.classList.add('hidden');
      triggerBtn.classList.remove('is-active');
    }

    triggerBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (isOpen) {
        closeChatbot();
      } else {
        openChatbot();
      }
    });

    closeBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      closeChatbot();
    });

    // Close on Escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && isOpen) {
        closeChatbot();
      }
    });

    // Language change handler
    if (typeof applyLanguage === 'function') {
      window.addEventListener('languageChanged', () => {
        applyLanguage(document.documentElement.lang || 'en');
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initChatbot);
  } else {
    initChatbot();
  }
})();
