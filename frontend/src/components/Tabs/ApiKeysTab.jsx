import React, { useState, useEffect } from 'react';
import api from '../../api/client';
import Alert from '../Alert';

const ApiKeysTab = () => {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [alert, setAlert] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newKeyLabel, setNewKeyLabel] = useState('');
  const [newKeyRole, setNewKeyRole] = useState('admin');
  const [newKeyNamespace, setNewKeyNamespace] = useState('');
  const [rawKey, setRawKey] = useState(null);
  const [namespaces, setNamespaces] = useState([]);

  useEffect(() => {
    loadKeys();
    loadNamespaces();
  }, []);

  const loadNamespaces = async () => {
    try {
      const data = await api.getNamespaces();
      setNamespaces(data?.namespaces || []);
    } catch (e) {
      console.error(e);
    }
  };

  const loadKeys = async () => {
    setLoading(true);
    try {
      const data = await api.getKeys();
      setKeys(data?.keys || []);
    } catch (error) {
      setAlert({ type: 'error', message: 'Failed to load API keys' });
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const data = await api.createKey(newKeyLabel, newKeyNamespace || null, newKeyRole);
      setRawKey(data.key);
      setShowCreateModal(false);
      setNewKeyLabel('');
      setNewKeyRole('admin');
      setNewKeyNamespace('');
      loadKeys();
    } catch (error) {
      setAlert({ type: 'error', message: error.message || 'Failed to create key' });
    }
  };

  const handleRevoke = async (keyId) => {
    if (!confirm('Are you sure you want to revoke this API key? This cannot be undone.')) return;
    try {
      await api.revokeKey(keyId);
      setAlert({ type: 'success', message: 'API key revoked' });
      loadKeys();
    } catch (error) {
      setAlert({ type: 'error', message: error.message || 'Failed to revoke key' });
    }
  };

  const copyToClipboard = () => {
    if (rawKey) {
      navigator.clipboard.writeText(rawKey).then(() => {
        setAlert({ type: 'success', message: 'Copied to clipboard' });
      });
    }
  };

  return (
    <section className="tab-content">
      <div className="glass-card">
        <header className="header" style={{ marginBottom: '1.5rem', padding: '0' }}>
          <h1 style={{ fontSize: '1.5rem', fontFamily: 'var(--font-display)' }}>API Keys</h1>
          <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
            <span>+</span> Generate API Key
          </button>
        </header>

        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
          Use API keys to authenticate your server side queries and document uploads against RAGaaS.
        </p>

        <Alert {...alert} onClose={() => setAlert(null)} />

        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>Key Prefix</th>
                <th>Label</th>
                <th>Role</th>
                <th>Scope</th>
                <th>Status</th>
                <th>Last Used</th>
                <th style={{ textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="5" className="loader-container"><div className="spinner"></div> Loading keys...</td>
                </tr>
              ) : keys.length === 0 ? (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No API keys found.</td>
                </tr>
              ) : (
                keys.map(k => (
                  <tr key={k.id}>
                    <td><code>{k.prefix}...</code></td>
                    <td>{k.label || '-'}</td>
                    <td><span style={{ fontSize: '0.8rem', padding: '2px 6px', background: 'var(--bg-card)', borderRadius: '4px' }}>{k.role === 'chat_only' ? 'Chat Only' : 'Admin'}</span></td>
                    <td><span style={{ fontSize: '0.8rem', opacity: 0.8 }}>{k.namespace_id ? 'Single Namespace' : 'All Namespaces'}</span></td>
                    <td>
                      <span className={`status-badge ${k.is_active ? 'active' : 'revoked'}`}>
                        {k.is_active ? 'Active' : 'Revoked'}
                      </span>
                    </td>
                    <td>{k.last_used_at ? new Date(k.last_used_at).toLocaleDateString() : 'Never'}</td>
                    <td style={{ textAlign: 'right' }}>
                      {k.is_active && (
                        <button className="btn btn-danger btn-sm" onClick={() => handleRevoke(k.id)}>Revoke</button>
                      )}
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
          <div className="modal-content animate-fade-in">
            <header className="modal-header">
              <h2 className="modal-title">Generate API Key</h2>
              <button className="modal-close" onClick={() => setShowCreateModal(false)}>&times;</button>
            </header>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label className="form-label">Key Label / Description</label>
                <input 
                  type="text" 
                  className="form-input" 
                  placeholder="e.g. production-backend" 
                  maxLength="100"
                  value={newKeyLabel}
                  onChange={(e) => setNewKeyLabel(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Key Role</label>
                <select className="form-input" value={newKeyRole} onChange={(e) => setNewKeyRole(e.target.value)}>
                  <option value="admin">Admin (Full Access)</option>
                  <option value="chat_only">Chat Only (Cannot Ingest)</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Namespace Scope</label>
                <select className="form-input" value={newKeyNamespace} onChange={(e) => setNewKeyNamespace(e.target.value)}>
                  <option value="">All Namespaces</option>
                  {namespaces.map(ns => (
                    <option key={ns.id} value={ns.id}>{ns.name}</option>
                  ))}
                </select>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Generate</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {rawKey && (
        <div className="modal-overlay active">
          <div className="modal-content animate-fade-in" style={{ maxWidth: '600px' }}>
            <header className="modal-header">
              <h2 className="modal-title">API Key Generated</h2>
            </header>
            <div style={{ backgroundColor: 'var(--color-warning-bg)', border: '1px solid rgba(245, 158, 11, 0.2)', padding: '1rem', borderRadius: 'var(--radius-md)', fontSize: '0.85rem', color: 'var(--color-warning)', lineHeight: '1.4', marginBottom: '1.5rem' }}>
              ⚠️ <strong>Store this key securely!</strong> For security reasons, we will only show this secret token once. If you lose it, you will need to revoke it and generate a new key.
            </div>
            
            <div className="copy-box">
              <span className="copy-text">{rawKey}</span>
              <button className="btn btn-secondary btn-sm" onClick={copyToClipboard}>Copy Key</button>
            </div>

            <div className="modal-footer">
              <button type="button" className="btn btn-primary" style={{ width: '100%' }} onClick={() => setRawKey(null)}>I have saved my key</button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};

export default ApiKeysTab;
