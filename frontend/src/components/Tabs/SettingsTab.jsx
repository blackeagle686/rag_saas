import React, { useState, useEffect } from 'react';
import api from '../../api/client';
import Alert from '../Alert';

const SettingsTab = () => {
  const [provider, setProvider] = useState('openai');
  const [model, setModel] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [baseUrl, setBaseUrl] = useState('');
  const [alert, setAlert] = useState(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await api.getSettings();
      if (data) {
        setProvider(data.llm_provider || 'openai');
        setModel(data.llm_model || '');
        setBaseUrl(data.llm_base_url || '');
      }
    } catch (error) {
      console.error('Failed to load settings', error);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setAlert(null);
    try {
      const payload = {
        llm_provider: provider,
        llm_model: model,
        llm_base_url: baseUrl,
      };
      if (apiKey) {
        payload.llm_api_key = apiKey;
      }
      
      await api.updateSettings(payload);
      setAlert({ type: 'success', message: 'Settings saved successfully' });
      setApiKey(''); // Clear the key field after saving
    } catch (error) {
      setAlert({ type: 'error', message: error.message || 'Failed to save settings' });
    }
  };

  return (
    <section className="tab-content">
      <div className="glass-card" style={{ maxWidth: '600px' }}>
        <header className="header" style={{ marginBottom: '1.5rem', padding: '0' }}>
          <h1 style={{ fontSize: '1.5rem', fontFamily: 'var(--font-display)' }}>LLM Configuration</h1>
        </header>

        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
          Configure your custom Large Language Model (LLM) credentials. The RAG query engine will use these settings to generate answers based on your documents.
        </p>

        <Alert {...alert} onClose={() => setAlert(null)} />

        <form onSubmit={handleSave}>
          <div className="form-group">
            <label htmlFor="settings-provider" className="form-label">LLM Provider</label>
            <select 
              id="settings-provider" 
              className="form-input" 
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              required
            >
              <option value="openai">OpenAI (or OpenAI Compatible)</option>
              <option value="anthropic">Anthropic Claude</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="settings-model" className="form-label">Model Name</label>
            <input 
              type="text" 
              id="settings-model" 
              className="form-input" 
              placeholder="e.g. LongCat-Flash-Lite" 
              value={model}
              onChange={(e) => setModel(e.target.value)}
              required 
            />
          </div>

          <div className="form-group">
            <label htmlFor="settings-api-key" className="form-label">API Key</label>
            <input 
              type="text" 
              id="settings-api-key" 
              className="form-input" 
              placeholder="Enter new API key (or leave empty to keep existing)"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label htmlFor="settings-base-url" className="form-label">Base URL (Endpoint)</label>
            <input 
              type="url" 
              id="settings-base-url" 
              className="form-input" 
              placeholder="e.g. https://api.longcat.chat/openai" 
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              required 
            />
          </div>

          <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '1rem' }}>
            Save Configuration
          </button>
        </form>
      </div>
    </section>
  );
};

export default SettingsTab;
