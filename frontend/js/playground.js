/**
 * Playground Query Handlers
 */
const Playground = {
  init() {
    this.bindEvents();
  },

  bindEvents() {
    const queryForm = document.getElementById('playground-query-form');
    if (queryForm) {
      queryForm.addEventListener('submit', (e) => this.handleQuery(e));
    }

    const clearChatBtn = document.getElementById('btn-clear-chat');
    if (clearChatBtn) {
      clearChatBtn.addEventListener('click', () => this.clearChat());
    }
  },

  async handleQuery(e) {
    e.preventDefault();
    const queryInput = document.getElementById('query-input');
    const namespaceSelect = document.getElementById('query-namespace');
    const modelSelect = document.getElementById('query-model');
    const topKInput = document.getElementById('query-top-k');

    const queryText = queryInput.value.trim();
    const namespace = namespaceSelect.value;
    const model = modelSelect.value;
    const topK = parseInt(topKInput.value) || 5;

    if (!queryText) return;

    if (!namespace) {
      alert('Please select a namespace to query against.');
      return;
    }

    // Append user message
    this.appendMessage('user', queryText);
    queryInput.value = '';

    // Create a temporary placeholder for assistant
    const placeholderId = 'msg-' + Date.now();
    this.appendMessage('assistant', `<div class="spinner"></div> Retrieval pipeline processing...`, null, placeholderId);

    const submitBtn = e.target.querySelector('button[type="submit"]');
    submitBtn.disabled = true;

    try {
      const result = await window.api.query(namespace, queryText, topK, model);
      
      // Update assistant response bubble
      const bubble = document.getElementById(placeholderId);
      if (bubble) {
        let content = result.answer;
        
        // Add latency and tokens info
        content += `
          <div style="margin-top: 0.75rem; font-size: 0.75rem; color: var(--text-muted); display: flex; gap: 1rem; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 0.5rem;">
            <span>⏱️ Latency: <strong>${result.latency_ms} ms</strong></span>
            <span>🪙 Tokens: <strong>${result.tokens_used}</strong></span>
            <span>📂 Namespace: <strong>${namespace}</strong></span>
          </div>
        `;

        // Add sources if available
        if (result.sources && result.sources.length > 0) {
          content += `
            <div class="sources-list">
              <div style="font-weight: 600; margin-bottom: 0.25rem;">🔍 Retrieved Chunks (${result.sources.length}):</div>
              ${result.sources.map((src, idx) => `
                <div class="source-item">
                  <div class="source-meta">
                    <span>Source ${idx + 1}: ${src.filename}</span>
                    <span class="source-score">Match: ${(src.score * 100).toFixed(1)}%</span>
                  </div>
                  <div class="source-text">"${src.chunk}"</div>
                </div>
              `).join('')}
            </div>
          `;
        } else {
          content += `
            <div class="sources-list" style="color: var(--text-muted); font-style: italic;">
              ⚠️ No source references returned.
            </div>
          `;
        }

        bubble.innerHTML = content;
      }
    } catch (error) {
      const bubble = document.getElementById(placeholderId);
      if (bubble) {
        bubble.innerHTML = `<span style="color: var(--color-error)">❌ Error: ${error.message}</span>`;
      }
    } finally {
      submitBtn.disabled = false;
      this.scrollToBottom();
    }
  },

  appendMessage(sender, text, data = null, id = null) {
    const chatHistory = document.getElementById('chat-history');
    if (!chatHistory) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}`;

    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble';
    bubbleDiv.innerHTML = text;
    if (id) {
      bubbleDiv.id = id;
    }

    messageDiv.appendChild(bubbleDiv);
    chatHistory.appendChild(messageDiv);
    this.scrollToBottom();
  },

  clearChat() {
    const chatHistory = document.getElementById('chat-history');
    if (chatHistory) {
      chatHistory.innerHTML = `
        <div class="chat-message assistant">
          <div class="message-bubble">
            👋 Welcome to the RAGaaS Playground. Select a namespace on the left, type a query below, and see retrieve-and-generate responses in real-time!
          </div>
        </div>
      `;
    }
  },

  scrollToBottom() {
    const chatHistory = document.getElementById('chat-history');
    if (chatHistory) {
      chatHistory.scrollTop = chatHistory.scrollHeight;
    }
  }
};

window.Playground = Playground;
