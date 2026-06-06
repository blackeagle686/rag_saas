import React, { useState, useEffect, useRef } from 'react';
import api from '../../api/client';
import Alert from '../Alert';

const NamespacesTab = () => {
  const [namespaces, setNamespaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [alert, setAlert] = useState(null);
  
  // Detail View State
  const [activeNamespace, setActiveNamespace] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [docsLoading, setDocsLoading] = useState(false);
  
  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newNsName, setNewNsName] = useState('');
  const [showUrlModal, setShowUrlModal] = useState(false);
  const [newUrl, setNewUrl] = useState('');

  // Upload State
  const [uploadStatus, setUploadStatus] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (!activeNamespace) {
      loadNamespaces();
    }
  }, [activeNamespace]);

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

  const loadDocuments = async (nsName) => {
    setDocsLoading(true);
    try {
      const data = await api.listDocuments(nsName);
      setDocuments(data?.documents || []);
    } catch (error) {
      setAlert({ type: 'error', message: 'Failed to load documents' });
    } finally {
      setDocsLoading(false);
    }
  };

  const handleCreateNamespace = async (e) => {
    e.preventDefault();
    try {
      await api.createNamespace(newNsName);
      setAlert({ type: 'success', message: `Namespace '${newNsName}' created.` });
      setShowCreateModal(false);
      setNewNsName('');
      loadNamespaces();
    } catch (error) {
      setAlert({ type: 'error', message: error.message || 'Failed to create namespace' });
    }
  };

  const handleDeleteNamespace = async () => {
    if (!confirm(`Are you sure you want to delete the namespace '${activeNamespace}' and all its documents? This cannot be undone.`)) return;
    try {
      await api.deleteNamespace(activeNamespace);
      setAlert({ type: 'success', message: 'Namespace deleted' });
      setActiveNamespace(null);
    } catch (error) {
      setAlert({ type: 'error', message: error.message || 'Failed to delete namespace' });
    }
  };

  const handleDeleteDocument = async (docId) => {
    if (!confirm('Delete this document?')) return;
    try {
      await api.deleteDocument(docId);
      loadDocuments(activeNamespace);
    } catch (error) {
      setAlert({ type: 'error', message: error.message || 'Failed to delete document' });
    }
  };

  const handleFileUpload = async (file) => {
    if (!file || !activeNamespace) return;
    setUploadStatus({ type: 'info', message: `Uploading ${file.name}...` });
    try {
      await api.uploadDocument(activeNamespace, file);
      setUploadStatus({ type: 'success', message: `${file.name} successfully ingested!` });
      loadDocuments(activeNamespace);
    } catch (error) {
      setUploadStatus({ type: 'error', message: `Upload failed: ${error.message}` });
    }
    setTimeout(() => setUploadStatus(null), 5000);
  };

  const onFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileUpload(e.target.files[0]);
    }
    // reset input
    e.target.value = '';
  };

  const handleUrlIngest = async (e) => {
    e.preventDefault();
    if (!newUrl || !activeNamespace) return;
    setShowUrlModal(false);
    setUploadStatus({ type: 'info', message: `Ingesting URL: ${newUrl}...` });
    try {
      await api.uploadDocumentByUrl(activeNamespace, newUrl);
      setUploadStatus({ type: 'success', message: `URL successfully ingested!` });
      loadDocuments(activeNamespace);
      setNewUrl('');
    } catch (error) {
      setUploadStatus({ type: 'error', message: `URL ingest failed: ${error.message}` });
    }
    setTimeout(() => setUploadStatus(null), 5000);
  };

  if (activeNamespace) {
    return (
      <section className="tab-content">
        <div className="glass-card">
          <header className="header" style={{ marginBottom: '2rem', padding: '0' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <button className="btn btn-secondary btn-sm" onClick={() => setActiveNamespace(null)}>← Back</button>
              <h1 style={{ fontSize: '1.5rem', fontFamily: 'var(--font-display)' }}>{activeNamespace}</h1>
            </div>
            <button className="btn btn-danger btn-sm" onClick={handleDeleteNamespace}>Delete Namespace</button>
          </header>

          <Alert {...alert} onClose={() => setAlert(null)} />

          <div className="ns-details-container">
            {/* Left Pane: Documents */}
            <div>
              <h3 className="section-title">Ingested Documents</h3>
              <div className="table-wrapper">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Filename</th>
                      <th>Type</th>
                      <th>Status</th>
                      <th>Chunks</th>
                      <th style={{ textAlign: 'right' }}>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {docsLoading ? (
                      <tr><td colSpan="5" className="loader-container"><div className="spinner"></div> Loading documents...</td></tr>
                    ) : documents.length === 0 ? (
                      <tr><td colSpan="5" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No documents.</td></tr>
                    ) : (
                      documents.map(doc => (
                        <tr key={doc.id}>
                          <td style={{ maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={doc.filename}>{doc.filename}</td>
                          <td>{doc.content_type || 'text/plain'}</td>
                          <td>
                            <span className={`status-badge ${doc.status === 'completed' ? 'active' : doc.status === 'failed' ? 'revoked' : ''}`}>
                              {doc.status || 'unknown'}
                            </span>
                          </td>
                          <td>{doc.chunk_count || 0}</td>
                          <td style={{ textAlign: 'right' }}>
                            <button className="btn btn-danger btn-sm" onClick={() => handleDeleteDocument(doc.id)}>Delete</button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Right Pane: Upload */}
            <div>
              <h3 className="section-title">Ingest Data</h3>
              
              <div 
                className="uploader-dropzone" 
                onClick={() => fileInputRef.current?.click()}
                onDragOver={e => e.preventDefault()}
                onDrop={e => { e.preventDefault(); if(e.dataTransfer.files?.length) handleFileUpload(e.dataTransfer.files[0]); }}
              >
                <div className="uploader-icon">📤</div>
                <div className="uploader-title">Drag & drop files here</div>
                <div className="uploader-desc">or click to browse local files</div>
                <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>PDF, DOCX, TXT, MD, HTML (Max 50MB)</div>
                <input 
                  type="file" 
                  ref={fileInputRef} 
                  className="file-input" 
                  accept=".pdf,.docx,.txt,.md,.html" 
                  onChange={onFileChange} 
                />
              </div>

              {uploadStatus && (
                <div style={{ marginTop: '1rem' }}>
                  <Alert {...uploadStatus} onClose={() => setUploadStatus(null)} />
                </div>
              )}

              <button className="btn btn-secondary" style={{ width: '100%', marginTop: '1rem' }} onClick={() => setShowUrlModal(true)}>
                🌐 Import via URL
              </button>
            </div>
          </div>
        </div>

        {/* URL Modal */}
        {showUrlModal && (
          <div className="modal-overlay active" onClick={(e) => { if (e.target.className.includes('modal-overlay')) setShowUrlModal(false) }}>
            <div className="modal-content animate-fade-in">
              <header className="modal-header">
                <h2 className="modal-title">Import File from Web</h2>
                <button className="modal-close" onClick={() => setShowUrlModal(false)}>&times;</button>
              </header>
              <form onSubmit={handleUrlIngest}>
                <div className="form-group">
                  <label className="form-label">File HTTP URL</label>
                  <input 
                    type="url" 
                    className="form-input" 
                    placeholder="https://example.com/agreement.pdf" 
                    value={newUrl}
                    onChange={e => setNewUrl(e.target.value)}
                    required
                  />
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={() => setShowUrlModal(false)}>Cancel</button>
                  <button type="submit" className="btn btn-primary">Start Ingestion</button>
                </div>
              </form>
            </div>
          </div>
        )}
      </section>
    );
  }

  // List View
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
                <th>Files Count</th>
                <th>Tokens Volume</th>
                <th>Created At</th>
                <th style={{ textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="5" className="loader-container"><div className="spinner"></div> Loading namespaces...</td>
                </tr>
              ) : namespaces.length === 0 ? (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No namespaces found.</td>
                </tr>
              ) : (
                namespaces.map(ns => (
                  <tr key={ns.name}>
                    <td style={{ fontWeight: 500 }}>{ns.name}</td>
                    <td>{ns.doc_count || 0}</td>
                    <td>~{(ns.token_count || 0).toLocaleString()}</td>
                    <td>{new Date(ns.created_at).toLocaleDateString()}</td>
                    <td style={{ textAlign: 'right' }}>
                      <button className="btn btn-secondary btn-sm" onClick={() => { setActiveNamespace(ns.name); loadDocuments(ns.name); }}>Manage</button>
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
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Create</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  );
};

export default NamespacesTab;
