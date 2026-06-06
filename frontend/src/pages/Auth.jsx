import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

const Auth = () => {
  const [key, setKey] = useState('');
  const { login } = useAuth();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (key.trim()) {
      login(key.trim());
    }
  };

  return (
    <div className="auth-page">
      <main className="glass-card auth-card animate-fade-in" id="auth-card">
        <div className="auth-header">
          <div className="auth-logo">
            <div className="logo-icon">R</div>
          </div>
          <h1>RAG-as-a-Service</h1>
          <p>Developer Console Login</p>
        </div>

        <form id="auth-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="api-key-input" className="form-label">Developer API Key</label>
            <input 
              type="password" 
              id="api-key-input" 
              className="form-input" 
              placeholder="rgs_live_..." 
              required 
              autoComplete="current-password"
              value={key}
              onChange={(e) => setKey(e.target.value)}
            />
          </div>

          <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '1rem' }}>
            Authenticate Key
          </button>
        </form>

        <div style={{ marginTop: '1.5rem', textAlign: 'center', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Don't have a key? Seed the database locally with <br />
          <code style={{ backgroundColor: 'rgba(255,255,255,0.05)', padding: '2px 4px', borderRadius: '4px', color: 'var(--accent-secondary)' }}>
            python -m scripts.seed
          </code>
        </div>
      </main>
    </div>
  );
};

export default Auth;
