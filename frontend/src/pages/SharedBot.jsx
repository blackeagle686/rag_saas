import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import '../styles/variables.css';
import '../styles/styles.css';

const SharedBot = () => {
  const { namespaceId } = useParams();
  const [messages, setMessages] = useState([{ role: 'assistant', text: 'Hello! I am your AI assistant. How can I help you today?' }]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const chatHistoryRef = useRef(null);

  useEffect(() => {
    if (chatHistoryRef.current) {
      chatHistoryRef.current.scrollTop = chatHistoryRef.current.scrollHeight;
    }
  }, [messages]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { role: 'user', text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(`http://localhost:8000/v1/widget/${namespaceId}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: input,
          session_id: sessionId,
          user_id: 'guest_user_' + Math.floor(Math.random() * 1000)
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        setMessages((prev) => [...prev, { role: 'assistant', text: data.answer }]);
        if (data.session_id) setSessionId(data.session_id);
      } else {
        setMessages((prev) => [...prev, { role: 'assistant', text: `Error: ${data.error}` }]);
      }
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'assistant', text: 'Network error. Please try again.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', height: '100vh', 
      backgroundColor: '#0a0a0f', color: '#e0e0e0', fontFamily: 'var(--font-primary)'
    }}>
      {/* Header */}
      <header style={{
        padding: '1rem 2rem', backgroundColor: '#13131a', borderBottom: '1px solid #1f1f2e',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center', boxShadow: '0 4px 20px rgba(0,0,0,0.5)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            width: '40px', height: '40px', borderRadius: '50%', background: 'linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem', boxShadow: '0 0 15px rgba(0, 210, 255, 0.4)'
          }}>🤖</div>
          <div>
            <h1 style={{ margin: 0, fontSize: '1.2rem', color: '#fff', letterSpacing: '0.5px' }}>AI Assistant</h1>
            <p style={{ margin: 0, fontSize: '0.75rem', color: '#888', textTransform: 'uppercase', letterSpacing: '1px' }}>Powered by RAGaaS</p>
          </div>
        </div>
        <div style={{ fontSize: '0.8rem', color: '#666', background: '#1c1c24', padding: '4px 12px', borderRadius: '20px', border: '1px solid #2a2a35' }}>
          ID: {namespaceId.slice(0,8)}
        </div>
      </header>

      {/* Chat Area */}
      <div ref={chatHistoryRef} style={{ flexGrow: 1, padding: '2rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {messages.map((msg, idx) => (
          <div key={idx} style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
            <div style={{
              maxWidth: '75%', padding: '1rem 1.25rem', borderRadius: '1rem',
              backgroundColor: msg.role === 'user' ? '#0056b3' : '#1e1e2d',
              color: '#fff', borderBottomRightRadius: msg.role === 'user' ? 0 : '1rem',
              borderBottomLeftRadius: msg.role === 'assistant' ? 0 : '1rem',
              border: msg.role === 'assistant' ? '1px solid #2a2a35' : 'none',
              boxShadow: '0 4px 15px rgba(0,0,0,0.1)',
              lineHeight: 1.5, fontSize: '0.95rem', whiteSpace: 'pre-wrap'
            }}>
              {msg.role === 'assistant' && <div style={{ fontSize: '0.7rem', color: '#00d2ff', textTransform: 'uppercase', marginBottom: '6px', fontWeight: 'bold', letterSpacing: '1px' }}>AI Assistant</div>}
              {msg.text}
            </div>
          </div>
        ))}
        {isLoading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div style={{ backgroundColor: '#1e1e2d', padding: '1rem', borderRadius: '1rem', borderBottomLeftRadius: 0, border: '1px solid #2a2a35', display: 'flex', gap: '8px', alignItems: 'center' }}>
              <div className="spinner" style={{ width: '16px', height: '16px' }}></div>
              <span style={{ fontSize: '0.9rem', color: '#888' }}>Thinking...</span>
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div style={{ padding: '1.5rem 2rem', backgroundColor: '#13131a', borderTop: '1px solid #1f1f2e' }}>
        <form onSubmit={sendMessage} style={{ display: 'flex', gap: '1rem', maxWidth: '900px', margin: '0 auto', position: 'relative' }}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            disabled={isLoading}
            style={{
              flexGrow: 1, padding: '1rem 1.5rem', borderRadius: '30px', border: '1px solid #2a2a35',
              backgroundColor: '#0a0a0f', color: '#fff', fontSize: '1rem', outline: 'none',
              boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.2)', paddingRight: '100px'
            }}
          />
          <button 
            type="submit" 
            disabled={isLoading || !input.trim()}
            style={{
              position: 'absolute', right: '6px', top: '6px', bottom: '6px',
              padding: '0 1.5rem', borderRadius: '24px', border: 'none',
              background: 'linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%)',
              color: '#fff', fontWeight: 'bold', cursor: isLoading || !input.trim() ? 'not-allowed' : 'pointer',
              opacity: isLoading || !input.trim() ? 0.5 : 1, transition: 'all 0.2s'
            }}
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
};

export default SharedBot;
