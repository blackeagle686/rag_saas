import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api/client';
import Alert from '../Alert';

const NamespacesTab = () => {
  const [llmProvider, setLlmProvider] = useState('openai');
  const [llmModel, setLlmModel] = useState('LongCat-2.0-Preview');
  const [llmApiKey, setLlmApiKey] = useState('ak_2yp3Xw1Ny7ky2pF7er9x93ZO9jj6G');
  const [llmBaseUrl, setLlmBaseUrl] = useState('https://api.longcat.chat/openai');
  const [namespaces, setNamespaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [alert, setAlert] = useState(null);
  const [plan, setPlan] = useState('free');
  const [isCreating, setIsCreating] = useState(false);
  const navigate = useNavigate();
  
  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Create Form State
  const [newNsName, setNewNsName] = useState('');
  const [ragType, setRagType] = useState('standard');

  useEffect(() => {
    loadNamespaces();
    fetchPlan();
  }, []);

  const fetchPlan = async () => {
    try {
      const data = await api.getSettings();
      if (data) setPlan(data.plan || 'free');
    } catch (err) {}
  };

  const loadNamespaces = async () => {
    setLoading(true);
    try {
      const data = await api.getNamespaces();
      setNamespaces(data?.namespaces || []);
    } catch (error) {
      setAlert({ type: 'error', message: 'Failed to load namespaces' });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNamespace = async (e) => {
    e.preventDefault();
    setIsCreating(true);
    try {
      await api.createNamespace(newNsName, {
        rag_type: ragType,
      });
      setAlert({ type: 'success', message: `Namespace '${newNsName}' created.` });
      setShowCreateModal(false);
      setNewNsName('');
      setRagType('standard');
      loadNamespaces();
    } catch (error) {
      setAlert({ type: 'error', message: error.message || 'Failed to create namespace' });
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <section className="tab-content">
      <div className="glass-card">
        <header className="header" style={{ marginBottom: '1.5rem', padding: '0' }}>
          <h1 style={{ fontSize: '1.5rem', fontFamily: 'var(--font-display)' }}>Namespaces</h1>
          <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
            <span>+</span> Create Namespace
          </button>
        </header>
        
        <Alert {...alert} onClose={() => setAlert(null)} />

        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>RAG Architecture</th>
                <th>Files Count</th>
                <th>Tokens Volume</th>
                <th>Created At</th>
                <th style={{ textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="6" className="loader-container"><div className="spinner"></div> Loading namespaces...</td>
                </tr>
              ) : namespaces.length === 0 ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No namespaces found.</td>
                </tr>
              ) : (
                namespaces.map(ns => (
                  <tr key={ns.name}>
                    <td style={{ fontWeight: 500 }}>{ns.name}</td>
                    <td>
                      <span className="status-badge" style={{textTransform:'uppercase', opacity: 0.8}}>{ns.rag_type || 'standard'}</span>
                    </td>
                    <td>{ns.doc_count || 0}</td>
                    <td>~{(ns.token_count || 0).toLocaleString()}</td>
                    <td>{new Date(ns.created_at).toLocaleDateString()}</td>
                    <td style={{ textAlign: 'right' }}>
                      <button className="btn btn-secondary btn-sm" onClick={() => navigate(`/namespaces/${ns.name}`)}>Manage</button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {showCreateModal && (
        <div className="modal-overlay active" onClick={(e) => { if (e.target.className.includes('modal-overlay')) setShowCreateModal(false) }}>
          <div className="modal-content animate-fade-in" style={{ maxWidth: '600px' }}>
            <header className="modal-header">
              <h2 className="modal-title">Create Namespace</h2>
              <button className="modal-close" onClick={() => setShowCreateModal(false)}>&times;</button>
            </header>
            <form onSubmit={handleCreateNamespace}>
              <div className="form-group">
                <label className="form-label">Namespace Name</label>
                <input 
                  type="text" 
                  className="form-input" 
                  placeholder="e.g. legal-docs" 
                  pattern="^[a-zA-Z0-9][a-zA-Z0-9\-_]{0,63}$" 
                  title="Alphanumeric, hyphens and underscores only, max 64 characters."
                  value={newNsName}
                  onChange={e => setNewNsName(e.target.value)}
                  required
                />
              </div>

              <div className="form-group" style={{ marginTop: '1.5rem' }}>
                <label className="form-label">RAG System Type</label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '0.5rem' }}>
                  {(() => {
                    const isAllowed = (requiredPlan) => {
                        const tiers = { free: 0, start: 1, mid: 2, prime: 3, enterprise: 4 };
                        return tiers[plan] >= tiers[requiredPlan];
                      };
                      return [
                        { id: 'standard', name: 'Standard RAG', desc: 'Best for general queries and simple retrieval.', req: 'free' },
                        { id: 'cag', name: 'Cache-Augmented (CAG)', desc: 'Best for repetitive queries. Ultra fast.', req: 'mid' },
                        { id: 'agentic', name: 'Agentic RAG', desc: 'Best for complex reasoning and self-correction.', req: 'prime' },
                        { id: 'multimodal', name: 'MultiModal RAG', desc: 'Best for images, audio, and mixed media.', req: 'prime' },
                      ].map(type => {
                        const allowed = isAllowed(type.req);
                        return (
                          <div 
                            key={type.id} 
                            onClick={() => { if (allowed) setRagType(type.id); }}
                            style={{
                              padding: '1rem',
                              borderRadius: 'var(--radius-md)',
                              border: ragType === type.id ? '2px solid var(--primary-color)' : '1px solid rgba(255,255,255,0.1)',
                              backgroundColor: ragType === type.id ? 'rgba(var(--primary-rgb), 0.1)' : 'var(--bg-card)',
                              cursor: allowed ? 'pointer' : 'not-allowed',
                              opacity: allowed ? 1 : 0.5,
                              transition: 'all 0.2s ease',
                              position: 'relative'
                            }}
                          >
                            {!allowed && <div style={{position: 'absolute', top: 10, right: 10}}>🔒</div>}
                            <div style={{ fontWeight: 600, marginBottom: '0.25rem', color: ragType === type.id ? 'var(--primary-color)' : 'inherit' }}>{type.name}</div>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{type.desc}</div>
                            {!allowed && <div style={{ fontSize: '0.75rem', color: 'var(--color-warning)', marginTop: '0.5rem' }}>Upgrade to {type.req.charAt(0).toUpperCase() + type.req.slice(1)}</div>}
                          </div>
                        );
                      });
                    })()
                  }
                </div>
              </div>

              <div className="modal-footer" style={{ marginTop: '2rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateModal(false)} disabled={isCreating}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={isCreating}>
                  {isCreating ? <div className="spinner" style={{width:'1rem', height:'1rem', borderWidth:'2px'}}></div> : 'Create Namespace'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  );
};

export default NamespacesTab;
