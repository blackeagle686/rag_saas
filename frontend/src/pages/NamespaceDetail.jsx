import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { BarChartFill, FolderFill, ChatDotsFill, KeyFill, RocketTakeoffFill, GearFill } from 'react-bootstrap-icons';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import api from '../api/client';
import Alert from '../components/Alert';
import Header from '../components/Header';

const NamespaceDetail = () => {
  const { name } = useParams();
  const navigate = useNavigate();

  const [activeNamespace, setActiveNamespace] = useState(null);
  const [loading, setLoading] = useState(true);
  const [alert, setAlert] = useState(null);
  const [plan, setPlan] = useState('free');

  const [documents, setDocuments] = useState([]);
  const [docsLoading, setDocsLoading] = useState(false);
  const [showUrlModal, setShowUrlModal] = useState(false);
  const [newUrl, setNewUrl] = useState('');
  
  // Namespace Dashboard State
  const [nsTab, setNsTab] = useState('overview');
  
  // Settings Form State
  const [ragType, setRagType] = useState('standard');
  const [llmProvider, setLlmProvider] = useState('longcat2-preview');
  const [llmModel, setLlmModel] = useState('LongCat-2.0-Preview');
  const [llmApiKey, setLlmApiKey] = useState('ak_2yp3Xw1Ny7ky2pF7er9x93ZO9jj6G');
  const [llmBaseUrl, setLlmBaseUrl] = useState('https://api.longcat.chat/openai');
  const [embeddingProvider, setEmbeddingProvider] = useState('local');
  const [embeddingModel, setEmbeddingModel] = useState('all-MiniLM-L6-v2');

  // Chat State
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState([{ role: 'assistant', text: '👋 Welcome to the Namespace Playground. Ask me anything about the indexed documents!' }]);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const chatHistoryRef = useRef(null);

  // API Keys State
  const [nsKeys, setNsKeys] = useState([]);
  const [keysLoading, setKeysLoading] = useState(false);
  const [showKeyModal, setShowKeyModal] = useState(false);
  const [newKeyLabel, setNewKeyLabel] = useState('');
  const [rawKey, setRawKey] = useState(null);

  // Upload State
  const [uploadStatus, setUploadStatus] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchNamespace();
    fetchPlan();
  }, [name]);

  const fetchNamespace = async () => {
    try {
      const data = await api.getNamespaces();
      const ns = data?.namespaces?.find(n => n.name === name);
      if (ns) {
        setActiveNamespace(ns);
      } else {
        setAlert({ type: 'error', message: 'Namespace not found.' });
      }
    } catch (err) {
      setAlert({ type: 'error', message: 'Failed to load namespace details' });
    } finally {
      setLoading(false);
    }
  };

  const fetchPlan = async () => {
    try {
      const data = await api.getSettings();
      if (data) setPlan(data.plan || 'free');
    } catch (err) {}
  };

  useEffect(() => {
    if (activeNamespace) {
      if (nsTab === 'data' || nsTab === 'overview') loadDocuments(activeNamespace.name);
      if (nsTab === 'api') loadNsKeys(activeNamespace.name);
      if (nsTab === 'settings') {
         setRagType(activeNamespace.rag_type || 'standard');
         setLlmProvider(activeNamespace.llm_provider || 'longcat2-preview');
         setLlmModel(activeNamespace.llm_model || 'LongCat-2.0-Preview');
         setLlmApiKey(activeNamespace.llm_api_key || 'ak_2yp3Xw1Ny7ky2pF7er9x93ZO9jj6G');
         setLlmBaseUrl(activeNamespace.llm_base_url || 'https://api.longcat.chat/openai');
         setEmbeddingProvider(activeNamespace.embedding_provider || 'local');
         setEmbeddingModel(activeNamespace.embedding_model || 'all-MiniLM-L6-v2');
      }
      if (nsTab === 'chat' && chatHistoryRef.current) {
         chatHistoryRef.current.scrollTop = chatHistoryRef.current.scrollHeight;
      }
    }
  }, [nsTab, activeNamespace]);

  useEffect(() => {
    if (chatHistoryRef.current) {
      chatHistoryRef.current.scrollTop = chatHistoryRef.current.scrollHeight;
    }
  }, [chatMessages]);

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

  const loadNsKeys = async (nsName) => {
    setKeysLoading(true);
    try {
      const data = await api.getKeys();
      const keys = data?.keys || [];
      setNsKeys(keys.filter(k => k.namespace_name === nsName));
    } catch (error) {
      setAlert({ type: 'error', message: 'Failed to load API keys' });
    } finally {
      setKeysLoading(false);
    }
  };

  const handleCreateNsKey = async (e) => {
    e.preventDefault();
    try {
      const data = await api.createKey(newKeyLabel, activeNamespace.id || activeNamespace.name, 'admin');
      setRawKey(data.key);
      setShowKeyModal(false);
      setNewKeyLabel('');
      loadNsKeys(activeNamespace.name);
    } catch (error) {
      setAlert({ type: 'error', message: error.message || 'Failed to create key' });
    }
  };

  const handleRevokeNsKey = async (keyId) => {
    if (!confirm('Revoke this key?')) return;
    try {
      await api.revokeKey(keyId);
      loadNsKeys(activeNamespace.name);
    } catch (error) {
      setAlert({ type: 'error', message: error.message || 'Failed to revoke key' });
    }
  };

  const handleNsQuery = async (e) => {
    e.preventDefault();
    if (!chatInput.trim() || !activeNamespace) return;
    const query = chatInput.trim();
    setChatInput('');
    setChatMessages(prev => [...prev, { role: 'user', text: query }]);
    setIsChatLoading(true);
    try {
      const res = await api.query(activeNamespace.name, query, 5, activeNamespace.llm_model || 'gpt-4o');
      let answerText = res.answer || 'No answer generated.';
      if (res.sources && res.sources.length > 0) {
        answerText += '\n\n**Sources:**\n' + res.sources.map(s => `- ${s.metadata?.filename || 'Unknown'} (Score: ${s.score?.toFixed(2)})`).join('\n');
      }
      setChatMessages(prev => [...prev, { role: 'assistant', text: answerText }]);
    } catch (err) {
      setChatMessages(prev => [...prev, { role: 'assistant', text: `❌ Error: ${err.message}` }]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const handleSaveSettings = async (e) => {
    e.preventDefault();
    if (!activeNamespace) return;
    try {
      const updatedData = {
        rag_type: ragType,
        llm_provider: llmProvider,
        llm_model: llmModel,
        llm_api_key: llmApiKey,
        llm_base_url: llmBaseUrl,
        embedding_provider: embeddingProvider,
        embedding_model: embeddingModel,
      };
      
      await api.updateNamespace(activeNamespace.name, updatedData);
      setAlert({ type: 'success', message: `Settings for '${activeNamespace.name}' saved.` });
      
      setActiveNamespace(prev => ({ ...prev, ...updatedData }));
    } catch (error) {
      setAlert({ type: 'error', message: error.message || 'Failed to save settings' });
    }
  };

  const handleDeleteNamespace = async () => {
    if (!activeNamespace) return;
    if (!confirm(`Are you sure you want to delete the namespace '${activeNamespace.name}' and all its documents? This cannot be undone.`)) return;
    try {
      await api.deleteNamespace(activeNamespace.name);
      navigate('/dashboard'); // Go back after delete
    } catch (error) {
      setAlert({ type: 'error', message: error.message || 'Failed to delete namespace' });
    }
  };

  const handleDeleteDocument = async (docId) => {
    if (!confirm('Delete this document?')) return;
    try {
      await api.deleteDocument(docId);
      loadDocuments(activeNamespace.name);
    } catch (error) {
      setAlert({ type: 'error', message: error.message || 'Failed to delete document' });
    }
  };

  const handleFileUpload = async (file) => {
    if (!file || !activeNamespace) return;
    setUploadStatus({ type: 'info', message: `Uploading ${file.name}...` });
    try {
      await api.uploadDocument(activeNamespace.name, file);
      setUploadStatus({ type: 'success', message: `${file.name} successfully ingested!` });
      loadDocuments(activeNamespace.name);
    } catch (error) {
      setUploadStatus({ type: 'error', message: `Upload failed: ${error.message}` });
    }
    setTimeout(() => setUploadStatus(null), 5000);
  };

  const onFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileUpload(e.target.files[0]);
    }
    e.target.value = '';
  };

  const handleUrlIngest = async (e) => {
    e.preventDefault();
    if (!newUrl || !activeNamespace) return;
    setShowUrlModal(false);
    setUploadStatus({ type: 'info', message: `Ingesting URL: ${newUrl}...` });
    try {
      await api.uploadDocumentByUrl(activeNamespace.name, newUrl);
      setUploadStatus({ type: 'success', message: `URL successfully ingested!` });
      loadDocuments(activeNamespace.name);
      setNewUrl('');
    } catch (error) {
      setUploadStatus({ type: 'error', message: `URL ingest failed: ${error.message}` });
    }
    setTimeout(() => setUploadStatus(null), 5000);
  };

  if (loading) {
    return <div className="app-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}><div className="spinner"></div></div>;
  }

  if (!activeNamespace) {
    return (
      <div className="app-container" style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        <Header activeTab="namespaces" setActiveTab={() => navigate('/dashboard')} />
        <main className="main-content" style={{ padding: '2rem' }}>
          <Alert {...alert} onClose={() => setAlert(null)} />
          <div style={{ textAlign: 'center', marginTop: '2rem' }}>
             <button className="btn btn-secondary" onClick={() => navigate('/dashboard')}>Return to Dashboard</button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="app-container" style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      <Header activeTab="namespaces" setActiveTab={(tab) => { if (tab !== 'namespaces') navigate('/dashboard'); }} />
      
      <main className="main-content" style={{ flexGrow: 1, overflow: 'hidden', padding: '2rem' }}>
        <section className="tab-content" style={{ display: 'flex', height: '100%', gap: '1.5rem', alignItems: 'flex-start' }}>
          
          {/* SIDEBAR FOR NAMESPACE DASHBOARD */}
          <div className="glass-card" style={{ width: '250px', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: '1rem', padding: '1.5rem', height: '100%' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <button className="btn btn-secondary btn-sm" onClick={() => navigate('/dashboard')}>← Back</button>
              <h2 style={{ fontSize: '1.2rem', fontFamily: 'var(--font-display)', margin: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={activeNamespace.name}>
                {activeNamespace.name}
              </h2>
            </div>
            <span className="status-badge active" style={{textTransform:'uppercase', alignSelf: 'flex-start', marginBottom: '1rem'}}>{activeNamespace.rag_type || 'standard'} RAG</span>

            <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flexGrow: 1 }}>
              {[
                { id: 'overview', icon: <BarChartFill />, label: 'Overview' },
                { id: 'data', icon: <FolderFill />, label: 'Data Sources' },
                { id: 'chat', icon: <ChatDotsFill />, label: 'Playground' },
                { id: 'api', icon: <KeyFill />, label: 'API Keys' },
                { id: 'deploy', icon: <RocketTakeoffFill />, label: 'Deploy & Host' },
                { id: 'settings', icon: <GearFill />, label: 'Settings' }
              ].map(t => (
                <button 
                  key={t.id}
                  onClick={() => setNsTab(t.id)}
                  style={{
                    background: nsTab === t.id ? 'rgba(var(--primary-rgb), 0.1)' : 'transparent',
                    border: 'none',
                    color: nsTab === t.id ? 'var(--primary-color)' : 'var(--text-secondary)',
                    cursor: 'pointer',
                    fontSize: '0.95rem',
                    fontWeight: nsTab === t.id ? 600 : 400,
                    padding: '0.75rem 1rem',
                    borderRadius: 'var(--radius-md)',
                    textAlign: 'left',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    transition: 'all 0.2s',
                    width: '100%'
                  }}
                >
                  <span style={{ fontSize: '1.1rem' }}>{t.icon}</span> {t.label}
                </button>
              ))}
            </nav>
            
            <div style={{ marginTop: 'auto', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '1.5rem' }}>
               <button className="btn btn-danger btn-sm" style={{ width: '100%' }} onClick={handleDeleteNamespace}>Delete Namespace</button>
            </div>
          </div>

          {/* MAIN CONTENT AREA */}
          <div className="glass-card" style={{ flexGrow: 1, padding: '2rem', height: '100%', overflowY: 'auto' }}>
            <Alert {...alert} onClose={() => setAlert(null)} />
            {uploadStatus && <Alert {...uploadStatus} onClose={() => setUploadStatus(null)} />}

            {nsTab === 'overview' && (
              <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                <div>
                  <h3 className="section-title">Namespace Analytics</h3>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                    <div className="stat-card hover-glow" style={{ borderLeft: '4px solid var(--primary-color)' }}>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '0.5rem' }}>Documents</div>
                      <h2 style={{ margin: 0, fontSize: '2rem' }}>{activeNamespace.doc_count || 0}</h2>
                    </div>
                    <div className="stat-card hover-glow" style={{ borderLeft: '4px solid var(--secondary-color)' }}>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '0.5rem' }}>Tokens Volume</div>
                      <h2 style={{ margin: 0, fontSize: '2rem' }}>~{(activeNamespace.token_count || 0).toLocaleString()}</h2>
                    </div>
                    <div className="stat-card hover-glow" style={{ borderLeft: '4px solid var(--color-success)' }}>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '0.5rem' }}>RAG Framework</div>
                      <h2 style={{ margin: 0, fontSize: '1.5rem', textTransform: 'uppercase' }}>{activeNamespace.rag_type || 'STANDARD'}</h2>
                    </div>
                    <div className="stat-card hover-glow" style={{ borderLeft: '4px solid var(--color-warning)' }}>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '0.5rem' }}>Created At</div>
                      <h2 style={{ margin: 0, fontSize: '1.2rem' }}>{new Date(activeNamespace.created_at).toLocaleDateString()}</h2>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="section-title">Data Ingestion Overview</h3>
                  <div style={{ background: 'rgba(255,255,255,0.03)', padding: '2rem', borderRadius: 'var(--radius-md)', border: '1px solid rgba(255,255,255,0.05)', height: '350px' }}>
                    {documents.length > 0 ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={documents.map(d => ({ name: d.filename.length > 15 ? d.filename.substring(0, 15) + '...' : d.filename, chunks: d.chunk_count || 0 }))}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                          <XAxis dataKey="name" stroke="var(--text-secondary)" fontSize={12} tickMargin={10} />
                          <YAxis stroke="var(--text-secondary)" fontSize={12} />
                          <Tooltip 
                            contentStyle={{ background: 'rgba(10, 10, 15, 0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }} 
                            itemStyle={{ color: 'var(--primary-color)' }}
                          />
                          <Bar dataKey="chunks" fill="url(#colorChunks)" radius={[4, 4, 0, 0]} />
                          <defs>
                            <linearGradient id="colorChunks" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="var(--primary-color)" stopOpacity={0.8}/>
                              <stop offset="95%" stopColor="var(--secondary-color)" stopOpacity={0.8}/>
                            </linearGradient>
                          </defs>
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                        No document data to display. Please ingest some files first.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {nsTab === 'data' && (
              <div className="ns-details-container animate-fade-in">
                <div>
                  <h3 className="section-title">Ingested Documents</h3>
                  <div className="table-wrapper">
                    <table className="table">
                      <thead><tr><th>Filename</th><th>Type</th><th>Status</th><th>Chunks</th><th style={{ textAlign: 'right' }}>Action</th></tr></thead>
                      <tbody>
                        {docsLoading ? (
                          <tr><td colSpan="5" className="loader-container"><div className="spinner"></div> Loading documents...</td></tr>
                        ) : documents.length === 0 ? (
                          <tr><td colSpan="5" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No documents.</td></tr>
                        ) : documents.map(doc => (
                            <tr key={doc.id}>
                              <td style={{ maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={doc.filename}>{doc.filename}</td>
                              <td>{doc.content_type || 'text/plain'}</td>
                              <td><span className={`status-badge ${doc.status === 'completed' ? 'active' : doc.status === 'failed' ? 'revoked' : ''}`}>{doc.status || 'unknown'}</span></td>
                              <td>{doc.chunk_count || 0}</td>
                              <td style={{ textAlign: 'right' }}><button className="btn btn-danger btn-sm" onClick={() => handleDeleteDocument(doc.id)}>Delete</button></td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                <div>
                  <h3 className="section-title">Ingest Data</h3>
                  <div className="uploader-dropzone" onClick={() => fileInputRef.current?.click()} onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); if(e.dataTransfer.files?.length) handleFileUpload(e.dataTransfer.files[0]); }}>
                    <div className="uploader-icon">📤</div>
                    <div className="uploader-title">Drag & drop files here</div>
                    <div className="uploader-desc">or click to browse local files</div>
                    <input type="file" ref={fileInputRef} className="file-input" accept=".pdf,.docx,.txt,.md,.html" onChange={onFileChange} />
                  </div>
                  <button className="btn btn-secondary" style={{ width: '100%', marginTop: '1rem' }} onClick={() => setShowUrlModal(true)}>🌐 Import via URL</button>
                </div>
              </div>
            )}

            {nsTab === 'chat' && (
              <div className="animate-fade-in" style={{ height: '600px', display: 'flex', flexDirection: 'column' }}>
                <div className="chat-history" ref={chatHistoryRef} style={{ flexGrow: 1 }}>
                  {chatMessages.map((msg, i) => (
                    <div key={i} className={`chat-message ${msg.role}`}>
                      <div className="message-bubble" style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</div>
                    </div>
                  ))}
                  {isChatLoading && <div className="chat-message assistant"><div className="message-bubble"><div className="spinner"></div> Thinking...</div></div>}
                </div>
                <form className="chat-input-wrapper" onSubmit={handleNsQuery}>
                  <input type="text" className="form-input chat-input" placeholder={`Message ${activeNamespace.name} RAG System...`} value={chatInput} onChange={e => setChatInput(e.target.value)} required disabled={isChatLoading} />
                  <button type="submit" className="btn btn-primary" disabled={isChatLoading}>Query</button>
                </form>
              </div>
            )}

            {nsTab === 'api' && (
              <div className="animate-fade-in">
                <header className="header" style={{ marginBottom: '1.5rem', padding: 0 }}>
                  <h3 className="section-title" style={{ margin: 0 }}>Namespace API Keys</h3>
                  <button className="btn btn-primary btn-sm" onClick={() => setShowKeyModal(true)}>+ Generate Key</button>
                </header>
                <div className="table-wrapper">
                  <table className="table">
                    <thead><tr><th>Prefix</th><th>Label</th><th>Role</th><th>Created</th><th style={{ textAlign: 'right' }}>Action</th></tr></thead>
                    <tbody>
                      {keysLoading ? (
                        <tr><td colSpan="5" className="loader-container"><div className="spinner"></div> Loading keys...</td></tr>
                      ) : nsKeys.length === 0 ? (
                        <tr><td colSpan="5" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No API keys scoped to this namespace.</td></tr>
                      ) : nsKeys.map(k => (
                        <tr key={k.id}>
                          <td><code>{k.prefix}...</code></td>
                          <td>{k.label || '-'}</td>
                          <td><span className="status-badge" style={{opacity:0.8}}>{k.role}</span></td>
                          <td>{new Date(k.created_at).toLocaleDateString()}</td>
                          <td style={{ textAlign: 'right' }}><button className="btn btn-danger btn-sm" onClick={() => handleRevokeNsKey(k.id)}>Revoke</button></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {nsTab === 'deploy' && (
              <div className="animate-fade-in">
                <h3 className="section-title">Deploy & Host</h3>
                <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
                  Share your curated RAG system with the world or integrate it into your custom applications.
                </p>
                
                <div style={{ background: 'var(--bg-card)', padding: '1.5rem', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', border: '1px solid rgba(255,255,255,0.05)' }}>
                  <h4 style={{ marginBottom: '1rem', color: 'var(--primary-color)' }}>🌐 Public Share URL</h4>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <input type="text" className="form-input" readOnly value={`${window.location.origin}/share/${activeNamespace.name}`} style={{ flexGrow: 1 }} />
                    <button className="btn btn-secondary" onClick={() => { navigator.clipboard.writeText(`${window.location.origin}/share/${activeNamespace.name}`); setAlert({type:'success', message:'Copied!'}) }}>Copy Link</button>
                  </div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>Anyone with this link can chat with your data. (Read-only access)</p>
                </div>

                <div style={{ background: 'var(--bg-card)', padding: '1.5rem', borderRadius: 'var(--radius-md)', border: '1px solid rgba(255,255,255,0.05)' }}>
                  <h4 style={{ marginBottom: '1rem', color: 'var(--primary-color)' }}>🔌 API Integration</h4>
                  <p style={{ fontSize: '0.9rem', marginBottom: '1rem' }}><strong>Base URL:</strong> <code>{window.location.protocol}//{window.location.hostname}:8000/v1/namespaces/{activeNamespace.name}/query</code></p>
                  <div className="copy-box" style={{ background: '#1e1e1e', padding: '1rem', borderRadius: 'var(--radius-md)', overflowX: 'auto', fontFamily: 'monospace', fontSize: '0.85rem' }}>
                    <pre style={{ margin: 0, color: '#e0e0e0' }}>
{`curl -X POST ${window.location.protocol}//${window.location.hostname}:8000/v1/namespaces/${activeNamespace.name}/query \\
  -H "Authorization: Bearer <YOUR_API_KEY>" \\
  -H "Content-Type: application/json" \\
  -d '{"query": "Hello world"}'`}
                    </pre>
                  </div>
                </div>
              </div>
            )}

            {/* HELPER FUNCTION */}
            {(() => {
              const isAllowed = (requiredPlan) => {
                const tiers = { free: 0, start: 1, mid: 2, prime: 3, enterprise: 4 };
                return tiers[plan] >= tiers[requiredPlan];
              };

              return nsTab === 'settings' && (
              <div className="animate-fade-in" style={{ maxWidth: '600px' }}>
                <h3 className="section-title">Namespace Settings</h3>
                <form onSubmit={handleSaveSettings}>
                  <div className="form-group" style={{ background: 'rgba(var(--primary-rgb), 0.05)', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--primary-color)' }}>
                    <label className="form-label" style={{ color: 'var(--primary-color)' }}>Upgrade RAG System Type</label>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Changing the architecture will instantly upgrade how queries are processed.</p>
                    <select className="form-input" value={ragType} onChange={e => setRagType(e.target.value)}>
                      <option value="standard">Standard RAG (Basic)</option>
                      <option value="cag" disabled={!isAllowed('mid')}>Cache-Augmented (CAG) - Faster {!isAllowed('mid') && '🔒 (Mid)'}</option>
                      <option value="agentic" disabled={!isAllowed('prime')}>Agentic RAG - Self-Correcting {!isAllowed('prime') && '🔒 (Prime)'}</option>
                      <option value="multimodal" disabled={!isAllowed('prime')}>MultiModal RAG {!isAllowed('prime') && '🔒 (Prime)'}</option>
                    </select>
                  </div>

                  <hr style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.1)', margin: '1.5rem 0' }} />

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div className="form-group">
                      <label className="form-label">LLM Provider</label>
                      <select className="form-input" value={llmProvider} onChange={e => setLlmProvider(e.target.value)}>
                        <option value="longcat2-preview">LongCat 2 Preview (Free)</option>
                        <option value="openai" disabled={!isAllowed('start')}>OpenAI {!isAllowed('start') && '🔒 (Start)'}</option>
                        <option value="anthropic" disabled={!isAllowed('mid')}>Anthropic {!isAllowed('mid') && '🔒 (Mid)'}</option>
                        <option value="gemini" disabled={!isAllowed('mid')}>Google Gemini {!isAllowed('mid') && '🔒 (Mid)'}</option>
                      </select>
                    </div>
                    <div className="form-group"><label className="form-label">LLM Model</label><input type="text" className="form-input" value={llmModel} onChange={e => setLlmModel(e.target.value)} /></div>
                  </div>
                  <div className="form-group"><label className="form-label">LLM API Key</label><input type="password" className="form-input" placeholder="sk-..." value={llmApiKey} onChange={e => setLlmApiKey(e.target.value)} /></div>
                  <div className="form-group"><label className="form-label">LLM Base URL</label><input type="text" className="form-input" placeholder="https://api.longcat.chat/openai" value={llmBaseUrl} onChange={e => setLlmBaseUrl(e.target.value)} /></div>
                  
                  <hr style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.1)', margin: '1.5rem 0' }} />

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div className="form-group">
                      <label className="form-label">Embedding Provider</label>
                      <select className="form-input" value={embeddingProvider} onChange={e => {
                        const newProv = e.target.value;
                        setEmbeddingProvider(newProv);
                        if (newProv === 'local') setEmbeddingModel('all-MiniLM-L6-v2');
                        else if (newProv === 'dashscope') setEmbeddingModel('text-embedding-v4');
                        else if (newProv === 'openai') setEmbeddingModel('text-embedding-3-large');
                        else if (newProv === 'gemini') setEmbeddingModel('text-embedding-004');
                        else if (newProv === 'cohere') setEmbeddingModel('embed-english-v3.0');
                        else if (newProv === 'voyage') setEmbeddingModel('voyage-3-large');
                      }}>
                        <option value="local">Local (Free)</option>
                        <option value="dashscope">DashScope (Free)</option>
                        <option value="openai" disabled={!isAllowed('mid')}>OpenAI {!isAllowed('mid') && '🔒 (Mid)'}</option>
                        <option value="cohere" disabled={!isAllowed('mid')}>Cohere {!isAllowed('mid') && '🔒 (Mid)'}</option>
                        <option value="voyage" disabled={!isAllowed('prime')}>Voyage AI {!isAllowed('prime') && '🔒 (Prime)'}</option>
                      </select>
                    </div>
                    <div className="form-group"><label className="form-label">Embedding Model</label><input type="text" className="form-input" value={embeddingModel} onChange={e => setEmbeddingModel(e.target.value)} /></div>
                  </div>
                  
                  <button type="submit" className="btn btn-primary" style={{ marginTop: '1rem' }}>Save Settings</button>
                </form>
              </div>
            )
            })()}

          </div>

          {/* URL Modal */}
          {showUrlModal && (
            <div className="modal-overlay active" onClick={(e) => { if (e.target.className.includes('modal-overlay')) setShowUrlModal(false) }}>
              <div className="modal-content animate-fade-in">
                <header className="modal-header"><h2 className="modal-title">Import File from Web</h2><button className="modal-close" onClick={() => setShowUrlModal(false)}>&times;</button></header>
                <form onSubmit={handleUrlIngest}>
                  <div className="form-group"><label className="form-label">File HTTP URL</label><input type="url" className="form-input" placeholder="https://example.com/file.pdf" value={newUrl} onChange={e => setNewUrl(e.target.value)} required /></div>
                  <div className="modal-footer"><button type="button" className="btn btn-secondary" onClick={() => setShowUrlModal(false)}>Cancel</button><button type="submit" className="btn btn-primary">Start Ingestion</button></div>
                </form>
              </div>
            </div>
          )}

          {/* Key Modal */}
          {showKeyModal && (
            <div className="modal-overlay active" onClick={(e) => { if (e.target.className.includes('modal-overlay')) setShowKeyModal(false) }}>
              <div className="modal-content animate-fade-in">
                <header className="modal-header"><h2 className="modal-title">Generate Namespace API Key</h2><button className="modal-close" onClick={() => setShowKeyModal(false)}>&times;</button></header>
                <form onSubmit={handleCreateNsKey}>
                  <div className="form-group"><label className="form-label">Label</label><input type="text" className="form-input" placeholder="production-backend" value={newKeyLabel} onChange={e => setNewKeyLabel(e.target.value)} /></div>
                  <div className="modal-footer"><button type="button" className="btn btn-secondary" onClick={() => setShowKeyModal(false)}>Cancel</button><button type="submit" className="btn btn-primary">Generate</button></div>
                </form>
              </div>
            </div>
          )}

          {/* Raw Key Display Modal */}
          {rawKey && (
            <div className="modal-overlay active">
              <div className="modal-content animate-fade-in" style={{ maxWidth: '600px' }}>
                <header className="modal-header"><h2 className="modal-title">API Key Generated</h2></header>
                <div style={{ backgroundColor: 'var(--color-warning-bg)', border: '1px solid rgba(245, 158, 11, 0.2)', padding: '1rem', borderRadius: 'var(--radius-md)', fontSize: '0.85rem', color: 'var(--color-warning)', lineHeight: '1.4', marginBottom: '1.5rem' }}>⚠️ <strong>Store this key securely!</strong> We will only show this once.</div>
                <div className="copy-box"><span className="copy-text">{rawKey}</span><button className="btn btn-secondary btn-sm" onClick={() => { navigator.clipboard.writeText(rawKey); setAlert({type:'success', message:'Copied!'}); }}>Copy</button></div>
                <div className="modal-footer"><button type="button" className="btn btn-primary" style={{ width: '100%' }} onClick={() => setRawKey(null)}>I have saved my key</button></div>
              </div>
            </div>
          )}

        </section>
      </main>
    </div>
  );
};

export default NamespaceDetail;
