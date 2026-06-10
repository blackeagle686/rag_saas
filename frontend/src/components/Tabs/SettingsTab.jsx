import React, { useState, useEffect } from 'react';
import api from '../../api/client';
import Alert from '../Alert';

const SettingsTab = () => {
  const [plan, setPlan] = useState('free');
  
  // LLM State
  const [provider, setProvider] = useState('longcat2-preview');
  const [model, setModel] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [baseUrl, setBaseUrl] = useState('');
  
  // Embeddings State
  const [embedProvider, setEmbedProvider] = useState('local');
  const [embedModel, setEmbedModel] = useState('');
  const [embedApiKey, setEmbedApiKey] = useState('');
  const [embedBaseUrl, setEmbedBaseUrl] = useState('');

  const [alert, setAlert] = useState(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await api.getSettings();
      if (data) {
        setPlan(data.plan || 'free');
        
        setProvider(data.llm_provider || 'longcat2-preview');
        setModel(data.llm_model || '');
        setBaseUrl(data.llm_base_url || '');
        
        setEmbedProvider(data.embedding_provider || 'local');
        setEmbedModel(data.embedding_model || '');
        setEmbedBaseUrl(data.embedding_base_url || '');
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
        embedding_provider: embedProvider,
        embedding_model: embedModel,
        embedding_base_url: embedBaseUrl,
      };
      if (apiKey) payload.llm_api_key = apiKey;
      if (embedApiKey) payload.embedding_api_key = embedApiKey;
      
      await api.updateSettings(payload);
      setAlert({ type: 'success', message: 'Settings saved successfully' });
      setApiKey(''); 
      setEmbedApiKey('');
    } catch (error) {
      setAlert({ type: 'error', message: error.message || 'Failed to save settings' });
    }
  };

  // Helper function to check plan privileges
  const isAllowed = (requiredPlan) => {
    const tiers = { free: 0, start: 1, mid: 2, prime: 3, enterprise: 4 };
    const currentTier = tiers[(plan || 'free').toLowerCase()] || 0;
    return currentTier >= tiers[requiredPlan];
  };

  return (
    <section className="tab-content" style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
      <div className="glass-card" style={{ flex: '1 1 45%', minWidth: '300px' }}>
        <header className="header" style={{ marginBottom: '1.5rem', padding: '0' }}>
          <h1 style={{ fontSize: '1.5rem', fontFamily: 'var(--font-display)' }}>LLM Configuration</h1>
        </header>

        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
          Select the model used for generating answers.
        </p>

        <Alert {...alert} onClose={() => setAlert(null)} />

        <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">LLM Provider</label>
            <select 
              className="form-input" 
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              required
            >
              <option value="longcat2-preview">LongCat 2 Preview (Free)</option>
              <option value="openai" disabled={!isAllowed('start')}>
                OpenAI GPT-4o {!isAllowed('start') && '🔒 (Upgrade to Start)'}
              </option>
              <option value="anthropic" disabled={!isAllowed('mid')}>
                Anthropic Claude {!isAllowed('mid') && '🔒 (Upgrade to Mid)'}
              </option>
              <option value="gemini" disabled={!isAllowed('mid')}>
                Google Gemini {!isAllowed('mid') && '🔒 (Upgrade to Mid)'}
              </option>
            </select>
          </div>

          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">Model Name</label>
            <input 
              type="text" 
              className="form-input" 
              placeholder="e.g. gpt-4o-mini" 
              value={model}
              onChange={(e) => setModel(e.target.value)}
            />
          </div>

          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">API Key</label>
            <input 
              type="password" 
              className="form-input" 
              placeholder="Enter new API key (or leave empty)"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              disabled={provider === 'longcat2-preview'}
            />
          </div>

          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">Base URL (Optional)</label>
            <input 
              type="url" 
              className="form-input" 
              placeholder="https://api.openai.com/v1" 
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              disabled={provider === 'longcat2-preview'}
            />
          </div>
        </form>
      </div>

      <div className="glass-card" style={{ flex: '1 1 45%', minWidth: '300px' }}>
        <header className="header" style={{ marginBottom: '1.5rem', padding: '0' }}>
          <h1 style={{ fontSize: '1.5rem', fontFamily: 'var(--font-display)' }}>Embeddings Configuration</h1>
        </header>

        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
          Select the model used for vectorizing your proprietary documents.
        </p>

        <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">Embedding Provider</label>
            <select 
              className="form-input" 
              value={embedProvider}
              onChange={(e) => setEmbedProvider(e.target.value)}
              required
            >
              <option value="local">Local (Sentence-Transformers) (Free)</option>
              <option value="dashscope">DashScope (Free)</option>
              <option value="openai" disabled={!isAllowed('mid')}>
                OpenAI Embeddings {!isAllowed('mid') && '🔒 (Upgrade to Mid)'}
              </option>
              <option value="cohere" disabled={!isAllowed('mid')}>
                Cohere {!isAllowed('mid') && '🔒 (Upgrade to Mid)'}
              </option>
              <option value="voyage" disabled={!isAllowed('prime')}>
                Voyage AI {!isAllowed('prime') && '🔒 (Upgrade to Prime)'}
              </option>
            </select>
          </div>

          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">Embedding Model</label>
            <input 
              type="text" 
              className="form-input" 
              placeholder="e.g. text-embedding-3-small" 
              value={embedModel}
              onChange={(e) => setEmbedModel(e.target.value)}
            />
          </div>

          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">API Key</label>
            <input 
              type="password" 
              className="form-input" 
              placeholder="Enter new API key (or leave empty)"
              value={embedApiKey}
              onChange={(e) => setEmbedApiKey(e.target.value)}
              disabled={embedProvider === 'local'}
            />
          </div>

          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">Base URL (Optional)</label>
            <input 
              type="url" 
              className="form-input" 
              placeholder="https://api.openai.com/v1" 
              value={embedBaseUrl}
              onChange={(e) => setEmbedBaseUrl(e.target.value)}
              disabled={embedProvider === 'local'}
            />
          </div>
        </form>
      </div>

      {/* Global Save Button spanning both columns */}
      <div style={{ width: '100%', display: 'flex', justifyContent: 'flex-end', marginTop: '1rem' }}>
        <button 
          onClick={handleSave} 
          className="btn btn-primary" 
          style={{ padding: '0.8rem 3rem', fontSize: '1.1rem' }}
        >
          Save All Configurations
        </button>
      </div>
    </section>
  );
};

export default SettingsTab;
