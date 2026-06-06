/**
 * API Key View Handlers
 */
const Keys = {
  init() {
    this.bindEvents();
  },

  bindEvents() {
    const createForm = document.getElementById('create-key-form');
    if (createForm) {
      createForm.addEventListener('submit', (e) => this.handleCreateKey(e));
    }

    const openCreateBtn = document.getElementById('btn-open-create-key');
    if (openCreateBtn) {
      openCreateBtn.addEventListener('click', () => {
        window.App.openModal('modal-create-key');
      });
    }

    const copyBtn = document.getElementById('btn-copy-raw-key');
    if (copyBtn) {
      copyBtn.addEventListener('click', () => this.copyToClipboard());
    }
  },

  async loadKeys() {
    const listBody = document.getElementById('keys-list-body');
    if (!listBody) return;

    listBody.innerHTML = `<tr><td colspan="5" class="loader-container"><div class="spinner"></div> Loading keys...</td></tr>`;

    try {
      const data = await window.api.getKeys();
      const keys = data.keys || [];

      if (keys.length === 0) {
        listBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No API keys found. Generate one to start accessing the API!</td></tr>`;
        return;
      }

      listBody.innerHTML = keys.map(key => {
        const lastUsed = key.last_used 
          ? new Date(key.last_used).toLocaleString() 
          : '<span style="color: var(--text-muted)">Never used</span>';
        
        const badge = key.is_active 
          ? '<span class="badge badge-success">Active</span>' 
          : '<span class="badge badge-error">Revoked</span>';

        const actionBtn = key.is_active 
          ? `<button class="btn btn-danger btn-sm" onclick="Keys.revokeKey('${key.id}')">Revoke</button>`
          : `<span style="color: var(--text-muted)">—</span>`;

        return `
          <tr>
            <td style="font-family: monospace; font-weight: 500;">${key.prefix}</td>
            <td style="font-weight: 600;">${key.label || 'dev-key'}</td>
            <td>${badge}</td>
            <td>${lastUsed}</td>
            <td style="text-align: right;">
              ${actionBtn}
            </td>
          </tr>
        `;
      }).join('');

    } catch (error) {
      window.App.showAlert('keys-alert', error.message, 'error');
    }
  },

  async handleCreateKey(e) {
    e.preventDefault();
    const labelInput = document.getElementById('key-label-input');
    const label = labelInput.value.trim() || 'dev-key';

    const btn = e.target.querySelector('button[type="submit"]');
    const originalText = btn.textContent;
    btn.innerHTML = `<div class="spinner"></div> Generating...`;
    btn.disabled = true;

    try {
      const result = await window.api.createKey(label);
      labelInput.value = '';
      
      // Close the key creation prompt modal
      window.App.closeModal('modal-create-key');
      
      // Display generated API key in our one-time view modal
      document.getElementById('raw-key-display').textContent = result.key;
      window.App.openModal('modal-show-raw-key');

      // Reload lists
      await this.loadKeys();
    } catch (error) {
      alert(`Error generating API Key: ${error.message}`);
    } finally {
      btn.textContent = originalText;
      btn.disabled = false;
    }
  },

  async revokeKey(keyId) {
    if (!confirm('Are you absolutely sure you want to revoke this API key? Any applications currently using this key will immediately receive 401 Unauthorized errors.')) return;

    try {
      await window.api.revokeKey(keyId);
      await this.loadKeys();
      window.App.showAlert('keys-alert', 'API key has been revoked.', 'success');
    } catch (error) {
      alert(`Failed to revoke key: ${error.message}`);
    }
  },

  copyToClipboard() {
    const text = document.getElementById('raw-key-display').textContent;
    navigator.clipboard.writeText(text).then(() => {
      const copyBtn = document.getElementById('btn-copy-raw-key');
      const originalText = copyBtn.textContent;
      copyBtn.textContent = 'Copied! ✓';
      copyBtn.style.color = 'var(--color-success)';
      setTimeout(() => {
        copyBtn.textContent = originalText;
        copyBtn.style.color = '';
      }, 2000);
    }).catch(err => {
      console.error('Failed to copy to clipboard', err);
    });
  }
};

window.Keys = Keys;
