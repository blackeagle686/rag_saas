/**
 * Namespace and Document Ingestion Handlers
 */
const Namespaces = {
  activeNamespace: null,
  pollIntervals: {},

  init() {
    this.bindEvents();
  },

  bindEvents() {
    const createForm = document.getElementById('create-ns-form');
    if (createForm) {
      createForm.addEventListener('submit', (e) => this.handleCreateNamespace(e));
    }

    const urlForm = document.getElementById('upload-url-form');
    if (urlForm) {
      urlForm.addEventListener('submit', (e) => this.handleUploadUrl(e));
    }

    const dropzone = document.getElementById('uploader-dropzone');
    const fileInput = document.getElementById('file-input');

    if (dropzone && fileInput) {
      dropzone.addEventListener('click', () => fileInput.click());
      fileInput.addEventListener('change', (e) => this.handleFileSelect(e));

      // Drag and drop event listeners
      ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
          e.preventDefault();
          dropzone.classList.add('dragover');
        }, false);
      });

      ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
          e.preventDefault();
          dropzone.classList.remove('dragover');
        }, false);
      });

      dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
          this.uploadFile(files[0]);
        }
      });
    }

    // Modal Triggers
    const openCreateBtn = document.getElementById('btn-open-create-ns');
    if (openCreateBtn) {
      openCreateBtn.addEventListener('click', () => {
        window.App.openModal('modal-create-namespace');
      });
    }

    const deleteNsBtn = document.getElementById('btn-delete-active-ns');
    if (deleteNsBtn) {
      deleteNsBtn.addEventListener('click', () => this.handleDeleteNamespace());
    }

    const backToNsBtn = document.getElementById('btn-back-to-ns');
    if (backToNsBtn) {
      backToNsBtn.addEventListener('click', () => this.showListView());
    }
  },

  async loadNamespaces() {
    const listBody = document.getElementById('namespaces-list-body');
    const overviewListBody = document.getElementById('overview-namespaces-list');
    const playgroundSelect = document.getElementById('query-namespace');

    if (!listBody) return;

    listBody.innerHTML = `<tr><td colspan="5" class="loader-container"><div class="spinner"></div> Loading namespaces...</td></tr>`;

    try {
      const data = await window.api.getNamespaces();
      const list = data.namespaces || [];

      // Update Dashboard Overview Counts
      document.getElementById('stat-namespaces-count').textContent = list.length;
      const totalDocs = list.reduce((sum, ns) => sum + ns.doc_count, 0);
      document.getElementById('stat-documents-count').textContent = totalDocs;

      // Populate list view table
      if (list.length === 0) {
        listBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No namespaces found. Create one to get started!</td></tr>`;
      } else {
        listBody.innerHTML = list.map(ns => `
          <tr>
            <td style="font-weight: 600; color: var(--text-primary); cursor: pointer;" onclick="Namespaces.showDetailView('${ns.name}')">${ns.name}</td>
            <td>${ns.doc_count} docs</td>
            <td>${this.formatTokens(ns.token_count)}</td>
            <td>${new Date(ns.created_at).toLocaleDateString()}</td>
            <td style="text-align: right;">
              <button class="btn btn-secondary btn-sm" onclick="Namespaces.showDetailView('${ns.name}')">Manage</button>
            </td>
          </tr>
        `).join('');
      }

      // Populate Dashboard Overview table
      if (overviewListBody) {
        if (list.length === 0) {
          overviewListBody.innerHTML = `<tr><td colspan="3" style="text-align: center; color: var(--text-muted); font-size: 0.85rem;">No namespaces.</td></tr>`;
        } else {
          overviewListBody.innerHTML = list.slice(0, 5).map(ns => `
            <tr>
              <td style="font-weight: 500;">${ns.name}</td>
              <td>${ns.doc_count}</td>
              <td>${this.formatTokens(ns.token_count)}</td>
            </tr>
          `).join('');
        }
      }

      // Populate Playground Select Box
      if (playgroundSelect) {
        const currentVal = playgroundSelect.value;
        playgroundSelect.innerHTML = `<option value="" disabled selected>Select a namespace...</option>` + 
          list.map(ns => `<option value="${ns.name}">${ns.name}</option>`).join('');
        if (list.some(ns => ns.name === currentVal)) {
          playgroundSelect.value = currentVal;
        }
      }

    } catch (error) {
      window.App.showAlert('namespaces-alert', error.message, 'error');
    }
  },

  async handleCreateNamespace(e) {
    e.preventDefault();
    const nameInput = document.getElementById('ns-name-input');
    const name = nameInput.value.trim();

    if (!name) return;

    const btn = e.target.querySelector('button[type="submit"]');
    const originalText = btn.textContent;
    btn.innerHTML = `<div class="spinner"></div> Creating...`;
    btn.disabled = true;

    try {
      await window.api.createNamespace(name);
      nameInput.value = '';
      window.App.closeModal('modal-create-namespace');
      await this.loadNamespaces();
      window.App.showAlert('namespaces-alert', `Namespace "${name}" created successfully.`, 'success');
    } catch (error) {
      alert(`Error creating namespace: ${error.message}`);
    } finally {
      btn.textContent = originalText;
      btn.disabled = false;
    }
  },

  async showDetailView(name) {
    this.activeNamespace = name;
    document.getElementById('ns-list-card').classList.add('hidden');
    document.getElementById('ns-detail-card').classList.remove('hidden');
    document.getElementById('ns-detail-title').textContent = `Namespace: ${name}`;
    
    // Clear any active document status polling on entry
    this.clearAllPolling();

    await this.loadDocuments();
  },

  showListView() {
    this.activeNamespace = null;
    this.clearAllPolling();
    document.getElementById('ns-detail-card').classList.add('hidden');
    document.getElementById('ns-list-card').classList.remove('hidden');
    this.loadNamespaces();
  },

  async loadDocuments() {
    if (!this.activeNamespace) return;

    const listBody = document.getElementById('documents-list-body');
    if (!listBody) return;

    listBody.innerHTML = `<tr><td colspan="5" class="loader-container"><div class="spinner"></div> Loading documents...</td></tr>`;

    try {
      const data = await window.api.listDocuments(this.activeNamespace);
      const docs = data.documents || [];

      if (docs.length === 0) {
        listBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 2rem;">No documents in this namespace yet. Upload a file above!</td></tr>`;
        return;
      }

      listBody.innerHTML = docs.map(doc => {
        let statusBadge = '';
        if (doc.status === 'ready') {
          statusBadge = `<span class="badge badge-success">Ready</span>`;
        } else if (doc.status === 'processing' || doc.status === 'pending') {
          statusBadge = `<span class="badge badge-warning"><div class="spinner" style="width: 10px; height: 10px; border-width: 1px; margin-right: 4px;"></div> Processing</span>`;
          this.schedulePoll(doc.id);
        } else {
          statusBadge = `<span class="badge badge-error" title="${doc.error_message || ''}">Failed</span>`;
        }

        return `
          <tr>
            <td style="font-weight: 500; color: var(--text-primary);" title="${doc.filename}">${doc.filename}</td>
            <td>${doc.file_type.toUpperCase()}</td>
            <td>${statusBadge}</td>
            <td>${doc.chunk_count || 0} chunks</td>
            <td style="text-align: right;">
              <button class="btn btn-icon" onclick="Namespaces.deleteDocument('${doc.id}')" title="Delete Document">
                🗑️
              </button>
            </td>
          </tr>
        `;
      }).join('');

    } catch (error) {
      listBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--color-error); padding: 2rem;">Error: ${error.message}</td></tr>`;
    }
  },

  schedulePoll(docId) {
    if (this.pollIntervals[docId]) return;

    this.pollIntervals[docId] = setInterval(async () => {
      try {
        // Query status through our helper endpoint if available, or just reload the document list
        // Reloading document list is safer and updates all elements in one shot.
        await this.loadDocuments();
      } catch (err) {
        console.error("Polling error for", docId, err);
      }
    }, 3000);
  },

  clearAllPolling() {
    Object.values(this.pollIntervals).forEach(interval => clearInterval(interval));
    this.pollIntervals = {};
  },

  async deleteDocument(docId) {
    if (!confirm('Are you sure you want to delete this document? This will remove all its chunks and index vectors permanently.')) return;

    try {
      await window.api.deleteDocument(docId);
      await this.loadDocuments();
    } catch (error) {
      alert(`Failed to delete document: ${error.message}`);
    }
  },

  async handleDeleteNamespace() {
    const name = this.activeNamespace;
    if (!name) return;

    const confirmation = confirm(`WARNING: Are you absolutely sure you want to delete namespace "${name}"? This will delete ALL documents and vectors inside it. This action CANNOT be undone.`);
    if (!confirmation) return;

    try {
      await window.api.deleteNamespace(name, true);
      this.showListView();
      window.App.showAlert('namespaces-alert', `Namespace "${name}" has been deleted.`, 'success');
    } catch (error) {
      alert(`Failed to delete namespace: ${error.message}`);
    }
  },

  handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
      this.uploadFile(files[0]);
    }
  },

  async uploadFile(file) {
    const statusDiv = document.getElementById('upload-status');
    statusDiv.innerHTML = `<div class="alert alert-success"><div class="spinner"></div> Uploading and parsing "${file.name}"...</div>`;

    try {
      await window.api.uploadDocument(this.activeNamespace, file);
      statusDiv.innerHTML = `<div class="alert alert-success">Successfully uploaded "${file.name}". Starting processing pipeline.</div>`;
      setTimeout(() => statusDiv.innerHTML = '', 3000);
      await this.loadDocuments();
    } catch (error) {
      statusDiv.innerHTML = `<div class="alert alert-error">Upload failed: ${error.message}</div>`;
    }
  },

  async handleUploadUrl(e) {
    e.preventDefault();
    const urlInput = document.getElementById('ns-url-input');
    const url = urlInput.value.trim();

    if (!url) return;

    const btn = e.target.querySelector('button[type="submit"]');
    const originalText = btn.textContent;
    btn.innerHTML = `<div class="spinner"></div> Ingesting...`;
    btn.disabled = true;

    const statusDiv = document.getElementById('upload-status');
    statusDiv.innerHTML = '';

    try {
      await window.api.uploadDocumentByUrl(this.activeNamespace, url);
      urlInput.value = '';
      window.App.closeModal('modal-upload-url');
      statusDiv.innerHTML = `<div class="alert alert-success">Successfully scheduled URL ingestion. Starting processing pipeline.</div>`;
      setTimeout(() => statusDiv.innerHTML = '', 3000);
      await this.loadDocuments();
    } catch (error) {
      alert(`Ingestion failed: ${error.message}`);
    } finally {
      btn.textContent = originalText;
      btn.disabled = false;
    }
  },

  formatTokens(count) {
    if (count < 1000) return `${count} tokens`;
    if (count < 1000000) return `${(count / 1000).toFixed(1)}k tokens`;
    return `${(count / 1000000).toFixed(1)}M tokens`;
  }
};

window.Namespaces = Namespaces;
