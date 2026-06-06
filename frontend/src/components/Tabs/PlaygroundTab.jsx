import React, { useState, useEffect, useRef } from 'react';
import api from '../../api/client';

const PlaygroundTab = () => {
  const [namespaces, setNamespaces] = useState([]);
  const [selectedNamespace, setSelectedNamespace] = useState('');
  const [model, setModel] = useState('gpt-4o');
  const [topK, setTopK] = useState(5);
  const [queryInput, setQueryInput] = useState('');
  const [messages, setMessages] = useState([
    { role: 'assistant', text: '👋 Welcome to the RAGaaS Playground. Select a namespace on the left, type a query below, and see retrieve-and-generate responses in real-time!' }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const chatHistoryRef = useRef(null);

  useEffect(() => {
    loadNamespaces();
  }, []);

  useEffect(() => {
    if (chatHistoryRef.current) {
      chatHistoryRef.current.scrollTop = chatHistoryRef.current.scrollHeight;
    }
  }, [messages]);

  const loadNamespaces = async () => {
    try {
      const data = await api.getNamespaces();
      setNamespaces(data || []);
      if (data && data.length > 0) {
        setSelectedNamespace(data[0].name);
      }
    } catch (error) {
      console.error('Failed to load namespaces for playground', error);
    }
  };

  const handleClear = () => {
    setMessages([
      { role: 'assistant', text: 'History cleared. Ready for your next query!' }
    ]);
  };

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!queryInput.trim() || !selectedNamespace) return;

    const query = queryInput.trim();
    setQueryInput('');
    setMessages(prev => [...prev, { role: 'user', text: query }]);
    setIsLoading(true);

    try {
      const response = await api.query(selectedNamespace, query, topK, model);
      
      let answerText = response.answer || 'No answer generated.';
      if (response.sources && response.sources.length > 0) {
        answerText += '\n\n**Sources:**\n' + response.sources.map(s => `- ${s.metadata?.filename || 'Unknown Document'} (Score: ${s.score?.toFixed(2)})`).join('\n');
      }
      
      setMessages(prev => [...prev, { role: 'assistant', text: answerText }]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', text: `❌ Error: ${error.message || 'Failed to execute query'}` }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section className="tab-content">
      <div className="glass-card chat-panel" style={{ height: '700px', padding: '1.5rem' }}>
        <header className="header" style={{ marginBottom: '1rem', padding: '0', flexShrink: 0 }}>
          <h1 style={{ fontSize: '1.35rem', fontFamily: 'var(--font-display)' }}>Query Playground</h1>
          <button className="btn btn-secondary btn-sm" onClick={handleClear}>Clear History</button>
        </header>

        <div className="playground-container">
          <div className="playground-sidebar">
            <div className="form-group">
              <label className="form-label">Target Namespace</label>
              <select 
                className="form-input" 
                value={selectedNamespace} 
                onChange={e => setSelectedNamespace(e.target.value)}
                required
              >
                {namespaces.length === 0 ? (
                  <option value="" disabled>Loading namespaces...</option>
                ) : (
                  namespaces.map(ns => (
                    <option key={ns.name} value={ns.name}>{ns.name}</option>
                  ))
                )}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">LLM Model</label>
              <select 
                className="form-input" 
                value={model} 
                onChange={e => setModel(e.target.value)}
              >
                <option value="gpt-4o">GPT-4o (Default)</option>
                <option value="claude-sonnet-4-20250514">Claude Sonnet</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Retrieve Count (Top K)</label>
              <input 
                type="number" 
                className="form-input" 
                min="1" 
                max="15" 
                value={topK} 
                onChange={e => setTopK(parseInt(e.target.value, 10))}
              />
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
            <div className="chat-history" ref={chatHistoryRef}>
              {messages.map((msg, i) => (
                <div key={i} className={`chat-message ${msg.role}`}>
                  <div className="message-bubble" style={{ whiteSpace: 'pre-wrap' }}>
                    {msg.text}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="chat-message assistant">
                  <div className="message-bubble">
                    <div className="spinner"></div> Generating answer...
                  </div>
                </div>
              )}
            </div>

            <form className="chat-input-wrapper" onSubmit={handleQuery}>
              <input 
                type="text" 
                className="form-input chat-input" 
                placeholder="Ask a question about your indexed documents..." 
                value={queryInput}
                onChange={e => setQueryInput(e.target.value)}
                required
                disabled={isLoading}
              />
              <button type="submit" className="btn btn-primary" disabled={isLoading || !selectedNamespace}>
                Query
              </button>
            </form>
          </div>
        </div>
      </div>
    </section>
  );
};

export default PlaygroundTab;
