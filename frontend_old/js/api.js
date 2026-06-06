/**
 * RAGaaS API Client for communication with the FastAPI backend.
 */
class RAGaaSApiClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
    this.apiKeyKey = 'ragaas_api_key';
  }

  setApiKey(apiKey) {
    localStorage.setItem(this.apiKeyKey, apiKey);
  }

  getApiKey() {
    return localStorage.getItem(this.apiKeyKey);
  }

  clearApiKey() {
    localStorage.removeItem(this.apiKeyKey);
  }

  isAuthenticated() {
    return !!this.getApiKey();
  }

  /**
   * General fetch wrapper that injects API key and handles errors.
   */
  async request(path, options = {}) {
    const url = `${this.baseUrl}${path}`;
    const apiKey = this.getApiKey();

    const headers = {
      ...(options.headers || {}),
    };

    if (apiKey) {
      headers['Authorization'] = `Bearer ${apiKey}`;
    }

    // Set JSON content-type if we aren't sending FormData
    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    const config = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json().catch(() => null);

      if (!response.ok) {
        const errorMsg = data?.error?.message || response.statusText || 'An error occurred';
        const err = new Error(errorMsg);
        err.statusCode = response.status;
        err.code = data?.error?.code;
        throw err;
      }

      return data;
    } catch (error) {
      console.error(`API Request failed on ${path}:`, error);
      throw error;
    }
  }

  // == Health Checks ==
  async getHealth() {
    return this.request('/health');
  }

  // == Namespace Management ==
  async getNamespaces() {
    return this.request('/v1/namespaces');
  }

  async createNamespace(name) {
    return this.request('/v1/namespaces', {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
  }

  async deleteNamespace(name, confirm = true) {
    return this.request(`/v1/namespaces/${name}`, {
      method: 'DELETE',
      body: JSON.stringify({ confirm }),
    });
  }

  async listDocuments(namespaceName, limit = 50, offset = 0) {
    return this.request(`/v1/namespaces/${namespaceName}/docs?limit=${limit}&offset=${offset}`);
  }

  async deleteDocument(docId) {
    return this.request(`/v1/documents/${docId}`, {
      method: 'DELETE',
    });
  }

  // == Ingestion (Upload) ==
  async uploadDocument(namespace, file, metadata = null) {
    const formData = new FormData();
    formData.append('namespace', namespace);
    formData.append('file', file);
    if (metadata) {
      formData.append('metadata', JSON.stringify(metadata));
    }

    return this.request('/v1/ingest', {
      method: 'POST',
      body: formData,
    });
  }

  async uploadDocumentByUrl(namespace, fileUrl, metadata = null) {
    return this.request('/v1/ingest', {
      method: 'POST',
      body: JSON.stringify({
        namespace,
        file_url: fileUrl,
        metadata: metadata || {},
      }),
    });
  }

  // == Retrieval/Query ==
  async query(namespace, queryText, topK = 5, model = null, filters = null) {
    const body = {
      namespace,
      query: queryText,
      top_k: topK,
    };
    if (model) body.model = model;
    if (filters) body.filters = filters;

    return this.request('/v1/query', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  // == API Key Management ==
  async getKeys() {
    return this.request('/v1/keys');
  }

  async createKey(label = null) {
    const body = {};
    if (label) body.label = label;
    return this.request('/v1/keys', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  async rotateKey(keyId, label = null) {
    const body = { key_id: keyId };
    if (label) body.label = label;
    return this.request('/v1/keys/rotate', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  async revokeKey(keyId) {
    return this.request(`/v1/keys/${keyId}`, {
      method: 'DELETE',
    });
  }

  // == Tenant Settings Management ==
  async getSettings() {
    return this.request('/v1/tenant/settings');
  }

  async updateSettings(settings) {
    return this.request('/v1/tenant/settings', {
      method: 'PATCH',
      body: JSON.stringify(settings),
    });
  }
}

// Export global instance
window.api = new RAGaaSApiClient();
