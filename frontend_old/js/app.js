/**
 * Main Application Controller
 */
const App = {
  activeTab: 'overview',

  init() {
    this.checkAuth();
    this.bindEvents();
    this.route();
    
    // Check API Health
    this.checkApiHealth();
  },

  checkAuth() {
    const isAuthPage = window.location.pathname.endsWith('auth.html');
    const hasKey = window.api.isAuthenticated();

    if (!hasKey && !isAuthPage) {
      window.location.href = 'auth.html';
    } else if (hasKey && isAuthPage) {
      window.location.href = 'dashboard.html';
    }
  },

  bindEvents() {
    // Tab switching event listeners
    const menuLinks = document.querySelectorAll('.menu-link[data-tab]');
    menuLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const tab = link.getAttribute('data-tab');
        this.switchTab(tab);
      });
    });

    // Logout trigger
    const logoutBtn = document.getElementById('btn-logout');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', (e) => {
        e.preventDefault();
        window.api.clearApiKey();
        window.location.href = 'auth.html';
      });
    }

    // Modal close overlay and buttons
    const overlays = document.querySelectorAll('.modal-overlay');
    overlays.forEach(overlay => {
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
          this.closeModal(overlay.id);
        }
      });
    });

    const closeBtns = document.querySelectorAll('.modal-close, .btn-close-modal');
    closeBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const modal = btn.closest('.modal-overlay');
        if (modal) {
          this.closeModal(modal.id);
        }
      });
    });
  },

  route() {
    // Check URL hash for routing
    const hash = window.location.hash.substring(1);
    const tabs = ['overview', 'namespaces', 'keys', 'playground', 'settings'];
    if (tabs.includes(hash)) {
      this.switchTab(hash);
    } else {
      this.switchTab('overview');
    }
  },

  switchTab(tabId) {
    this.activeTab = tabId;
    window.location.hash = tabId;

    // Toggle menu active state
    const links = document.querySelectorAll('.menu-link[data-tab]');
    links.forEach(link => {
      if (link.getAttribute('data-tab') === tabId) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });

    // Toggle content visibility
    const contents = document.querySelectorAll('.tab-content');
    contents.forEach(content => {
      if (content.id === `tab-${tabId}`) {
        content.classList.remove('hidden');
      } else {
        content.classList.add('hidden');
      }
    });

    // Trigger tab-specific loading logic
    if (tabId === 'namespaces') {
      window.Namespaces.showListView();
    } else if (tabId === 'keys') {
      window.Keys.loadKeys();
    } else if (tabId === 'overview') {
      window.Namespaces.loadNamespaces();
    } else if (tabId === 'settings') {
      if (window.Settings) window.Settings.init();
    }
  },

  // == Modals ==
  openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('active');
    }
  },

  closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove('active');
    }
  },

  // == Alerts ==
  showAlert(containerId, message, type = 'success') {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = `
      <div class="alert alert-${type} animate-fade-in">
        <span>${type === 'success' ? '✓' : '⚠️'}</span>
        <div>${message}</div>
      </div>
    `;

    // Autohide after 5 seconds
    setTimeout(() => {
      container.innerHTML = '';
    }, 5000);
  },

  // == Api Health Check ==
  async checkApiHealth() {
    const statusText = document.getElementById('api-health-status');
    const statusDot = document.getElementById('api-health-dot');
    
    if (!statusText || !statusDot) return;

    try {
      const data = await window.api.getHealth();
      if (data.status === 'ok') {
        statusText.textContent = 'API Connected';
        statusDot.style.backgroundColor = 'var(--color-success)';
      } else {
        statusText.textContent = 'Degraded';
        statusDot.style.backgroundColor = 'var(--color-warning)';
      }
    } catch (err) {
      statusText.textContent = 'Disconnected';
      statusDot.style.backgroundColor = 'var(--color-error)';
    }
  }
};

window.App = App;

// Initializer
document.addEventListener('DOMContentLoaded', () => {
  // Init modular parts
  if (window.Namespaces) window.Namespaces.init();
  if (window.Keys) window.Keys.init();
  if (window.Playground) window.Playground.init();
  if (window.Settings) window.Settings.init();

  // Init App
  window.App.init();
});
