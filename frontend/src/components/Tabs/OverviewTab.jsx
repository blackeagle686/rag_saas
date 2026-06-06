import React, { useState, useEffect } from 'react';
import api from '../../api/client';

const OverviewTab = () => {
  const [namespaces, setNamespaces] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const nsData = await api.getNamespaces();
      setNamespaces(nsData?.namespaces || []);
    } catch (error) {
      console.error('Failed to load overview data', error);
    } finally {
      setLoading(false);
    }
  };

  const totalNamespaces = namespaces.length;
  const totalDocs = namespaces.reduce((acc, ns) => acc + (ns.files_count || 0), 0);

  return (
    <section className="tab-content">
      <header className="header">
        <div className="header-title">
          <h1>Console Overview</h1>
          <p>Monitor your active indices and document statistics.</p>
        </div>
      </header>

      <div className="stats-grid">
        <div className="glass-card stat-card">
          <div className="stat-icon">📂</div>
          <div className="stat-info">
            <span className="stat-value">{loading ? '—' : totalNamespaces}</span>
            <span className="stat-label">Namespaces</span>
          </div>
        </div>
        <div className="glass-card stat-card">
          <div className="stat-icon">📄</div>
          <div className="stat-info">
            <span className="stat-value">{loading ? '—' : totalDocs}</span>
            <span className="stat-label">Ingested Files</span>
          </div>
        </div>
      </div>

      <div className="glass-card">
        <h2 className="section-title">Recent Namespaces</h2>
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Documents</th>
                <th>Token Volume</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="3" className="loader-container">
                    <div className="spinner"></div> Loading recent namespaces...
                  </td>
                </tr>
              ) : namespaces.length === 0 ? (
                <tr>
                  <td colSpan="3" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No namespaces created yet.</td>
                </tr>
              ) : (
                namespaces.slice(0, 5).map(ns => (
                  <tr key={ns.name}>
                    <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{ns.name}</td>
                    <td>{ns.files_count}</td>
                    <td>~{ns.tokens_count.toLocaleString()}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
};

export default OverviewTab;
