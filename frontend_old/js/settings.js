/**
 * Settings tab controller — handles loading and updating custom LLM configuration.
 */
class SettingsController {
  constructor() {
    this.form = document.getElementById('llm-settings-form');
    this.providerSelect = document.getElementById('settings-provider');
    this.modelInput = document.getElementById('settings-model');
    this.apiKeyInput = document.getElementById('settings-api-key');
    this.apiKeyMasked = document.getElementById('settings-api-key-masked');
    this.baseUrlInput = document.getElementById('settings-base-url');
    this.alertContainer = document.getElementById('settings-alert');
    
    if (this.form) {
      this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    }
  }

  async init() {
    if (!this.form) return;
    this.clearAlert();
    await this.loadSettings();
  }

  showAlert(message, type = 'success') {
    const alertClass = type === 'success' ? 'alert-success' : 'alert-error';
    this.alertContainer.innerHTML = `
      <div class="alert ${alertClass} animate-fade-in">
        ${message}
      </div>
    `;
  }

  clearAlert() {
    this.alertContainer.innerHTML = '';
  }

  async loadSettings() {
    try {
      const settings = await window.api.getSettings();
      this.providerSelect.value = settings.llm_provider || 'openai';
      this.modelInput.value = settings.llm_model || '';
      this.baseUrlInput.value = settings.llm_base_url || '';
      
      // Clear key input since we don't show the raw key
      this.apiKeyInput.value = '';
      
      if (settings.llm_api_key) {
        this.apiKeyMasked.textContent = `Current key: ${settings.llm_api_key}`;
      } else {
        this.apiKeyMasked.textContent = 'Current key: None';
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
      this.showAlert(error.message || 'Failed to load settings', 'error');
    }
  }

  async handleSubmit(e) {
    e.preventDefault();
    this.clearAlert();

    const provider = this.providerSelect.value.trim();
    const model = this.modelInput.value.trim();
    const apiKey = this.apiKeyInput.value.trim();
    const baseUrl = this.baseUrlInput.value.trim();

    const payload = {
      llm_provider: provider,
      llm_model: model,
      llm_base_url: baseUrl
    };

    // Only send API key if user typed something new
    if (apiKey) {
      payload.llm_api_key = apiKey;
    }

    try {
      const btn = document.getElementById('btn-save-settings');
      const originalText = btn.textContent;
      btn.textContent = 'Saving...';
      btn.disabled = true;

      const updated = await window.api.updateSettings(payload);
      
      btn.textContent = originalText;
      btn.disabled = false;

      this.showAlert('LLM configuration saved successfully!');
      
      // Update key text and clear input
      this.apiKeyInput.value = '';
      if (updated.llm_api_key) {
        this.apiKeyMasked.textContent = `Current key: ${updated.llm_api_key}`;
      }
      
      // Also update models option in the playground if applicable
      if (window.Playground) {
        window.Playground.updateModelOptions(updated.llm_model);
      }
    } catch (error) {
      this.showAlert(error.message || 'Failed to save settings', 'error');
      const btn = document.getElementById('btn-save-settings');
      btn.disabled = false;
      btn.textContent = 'Save Configuration';
    }
  }
}

// Export controller
window.Settings = new SettingsController();
