import React, { useState, useEffect } from 'react';
import { useParams, useLocation } from 'react-router-dom';

const SharedBot = () => {
  const { namespaceId } = useParams();
  const location = useLocation();
  const [messages, setMessages] = useState([{ role: 'assistant', content: 'Hello! I am your AI assistant. How can I help you today?' }]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  
  const [apiKey, setApiKey] = useState('demo_api_key_123'); 
  const [isKeyFromUrl, setIsKeyFromUrl] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const keyParam = params.get('key');
    if (keyParam) {
      setApiKey(keyParam);
      setIsKeyFromUrl(true);
    }
  }, [location]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(`http://localhost:8000/v1/bot/${namespaceId}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey
        },
        body: JSON.stringify({
          message: input,
          session_id: sessionId,
          user_id: 'guest_user_' + Math.floor(Math.random() * 1000)
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        setMessages((prev) => [...prev, { role: 'assistant', content: data.answer }]);
        if (data.session_id) setSessionId(data.session_id);
      } else {
        setMessages((prev) => [...prev, { role: 'assistant', content: `Error: ${data.error}` }]);
      }
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Network error. Please try again.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-950 text-gray-100 font-sans">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-800 p-4 shadow-xl flex justify-between items-center z-10">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-gradient-to-tr from-cyan-600 to-blue-500 flex items-center justify-center text-2xl font-bold shadow-lg shadow-cyan-500/20">
            🤖
          </div>
          <div>
            <h1 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-400">Company AI Assistant</h1>
            <p className="text-xs text-gray-400 font-medium tracking-wide">POWERED BY RAGAAS</p>
          </div>
        </div>
        <div className="text-xs text-gray-500 bg-gray-800 px-3 py-1 rounded-full border border-gray-700">
          ID: {namespaceId.slice(0,8)}
        </div>
      </header>

      {/* API Key Config (Demo Mode) */}
      {!isKeyFromUrl && (
        <div className="bg-gray-900/50 p-2 text-xs border-b border-gray-800 flex flex-col sm:flex-row items-center justify-center sm:justify-between px-6 gap-2 backdrop-blur-sm">
          <span className="text-orange-400 font-medium flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            Demo Mode: Enter API Key
          </span>
          <input 
            type="text" 
            value={apiKey} 
            onChange={(e) => setApiKey(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-gray-300 w-full sm:w-64 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all"
            placeholder="X-API-Key"
          />
        </div>
      )}

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] sm:max-w-[70%] rounded-2xl p-4 sm:p-5 shadow-lg transition-all duration-300 ${
              msg.role === 'user' 
                ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white rounded-br-sm ml-8' 
                : 'bg-gray-800/80 text-gray-200 border border-gray-700/50 rounded-bl-sm mr-8'
            }`}>
              {msg.role === 'assistant' && (
                <div className="flex items-center gap-2 mb-2 text-cyan-400 text-xs font-bold uppercase tracking-wider">
                  <span>AI Assistant</span>
                </div>
              )}
              <p className="whitespace-pre-wrap leading-relaxed text-sm md:text-base font-light">{msg.content}</p>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-800/80 border border-gray-700/50 rounded-2xl p-5 rounded-bl-sm flex gap-3 items-center mr-8">
              <div className="flex gap-1.5">
                <div className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce"></div>
                <div className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce" style={{animationDelay: '0.2s'}}></div>
                <div className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce" style={{animationDelay: '0.4s'}}></div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="bg-gray-900 border-t border-gray-800 p-4 sm:p-6">
        <form onSubmit={sendMessage} className="max-w-4xl mx-auto relative flex items-center group">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything about the company..."
            className="w-full bg-gray-800/50 border border-gray-700 text-gray-100 rounded-2xl py-4 pl-6 pr-16 focus:outline-none focus:border-cyan-500 focus:bg-gray-800 focus:ring-1 focus:ring-cyan-500 transition-all shadow-inner"
            disabled={isLoading}
          />
          <button 
            type="submit" 
            disabled={isLoading || !input.trim()}
            className="absolute right-2 p-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:from-gray-700 disabled:to-gray-700 text-white rounded-xl font-medium transition-all duration-200 shadow-md transform active:scale-95 flex items-center justify-center"
            aria-label="Send message"
          >
            <svg className="w-5 h-5 translate-x-px" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
};

export default SharedBot;
