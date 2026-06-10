import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const Auth = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (isLogin) {
        await login(email, password);
      } else {
        await register(name, email, password);
      }
      navigate('/dashboard');
    } catch (err) {
      setError(err.message || 'Authentication failed');
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: 'var(--bg-base)' }}>
      {/* Left side: Image and branding (Hidden on small screens) */}
      <div style={{ 
        flex: 1, 
        backgroundImage: 'url(/auth-bg.png)',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        position: 'relative'
      }} className="auth-sidebar-hide">
        <div style={{ 
          position: 'absolute', 
          inset: 0, 
          background: 'linear-gradient(to right, rgba(10,10,15,0.2), var(--bg-base))' 
        }} />
        
        <div style={{ position: 'relative', zIndex: 1, padding: '4rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', height: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
            <div className="logo-icon" style={{ width: '40px', height: '40px', margin: 0, fontSize: '1.2rem' }}>R</div>
            <span style={{ fontSize: '1.8rem', fontWeight: 700, fontFamily: 'var(--font-display)', color: 'white' }}>RAGaaS</span>
          </div>
          
          <div style={{ maxWidth: '400px' }}>
            <h2 style={{ fontSize: '2.5rem', fontFamily: 'var(--font-display)', color: 'white', marginBottom: '1rem', lineHeight: 1.2 }}>
              Deploy Production AI in Minutes.
            </h2>
            <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '1.1rem', lineHeight: 1.6 }}>
              Join developers building scalable, reliable, and secure Retrieval-Augmented Generation applications with our managed infrastructure.
            </p>
          </div>
        </div>
      </div>

      {/* Right side: Auth Form */}
      <div style={{ 
        flex: 1, 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        padding: '2rem',
        position: 'relative',
        backgroundColor: 'var(--bg-base)'
      }}>
        {/* Mobile Header (Only visible when sidebar is hidden) */}
        <div className="auth-mobile-header" style={{ position: 'absolute', top: '2rem', left: '2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div className="logo-icon" style={{ width: '30px', height: '30px', margin: 0, fontSize: '0.9rem' }}>R</div>
          <span style={{ fontSize: '1.2rem', fontWeight: 700, fontFamily: 'var(--font-display)' }}>RAGaaS</span>
        </div>

        <div style={{ width: '100%', maxWidth: '400px' }} className="animate-fade-in">
          <div style={{ marginBottom: '2.5rem' }}>
            <h1 style={{ fontSize: '2rem', fontFamily: 'var(--font-display)', marginBottom: '0.5rem' }}>
              {isLogin ? 'Welcome back' : 'Create your account'}
            </h1>
            <p style={{ color: 'var(--text-secondary)' }}>
              {isLogin ? 'Enter your details to access your dashboard.' : 'Start building your AI assistant today.'}
            </p>
          </div>

          {error && (
            <div style={{ 
              background: 'rgba(255, 107, 107, 0.1)', 
              color: '#ff6b6b', 
              padding: '1rem', 
              borderRadius: 'var(--radius-md)', 
              marginBottom: '1.5rem',
              border: '1px solid rgba(255, 107, 107, 0.2)',
              fontSize: '0.9rem'
            }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
            {!isLogin && (
              <div className="form-group" style={{ margin: 0 }}>
                <label className="form-label">Full Name</label>
                <input 
                  type="text" 
                  className="form-input" 
                  placeholder="John Doe" 
                  required 
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-color)' }}
                />
              </div>
            )}

            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">Email</label>
              <input 
                type="email" 
                className="form-input" 
                placeholder="you@example.com" 
                required 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-color)' }}
              />
            </div>

            <div className="form-group" style={{ margin: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label className="form-label" style={{ marginBottom: 0 }}>Password</label>
                {isLogin && (
                  <a href="#" style={{ fontSize: '0.85rem', color: 'var(--accent-primary)', textDecoration: 'none' }}>Forgot password?</a>
                )}
              </div>
              <input 
                type="password" 
                className="form-input" 
                placeholder="••••••••" 
                required 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-color)', marginTop: '0.5rem' }}
              />
            </div>

            <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '0.5rem', padding: '0.8rem' }} disabled={loading}>
              {loading ? 'Processing...' : (isLogin ? 'Sign In' : 'Create Account')}
            </button>
          </form>

          <div style={{ marginTop: '2rem', textAlign: 'center', fontSize: '0.95rem', color: 'var(--text-secondary)' }}>
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <button 
              type="button" 
              onClick={() => { setIsLogin(!isLogin); setError(null); }} 
              style={{ background: 'none', border: 'none', color: 'white', fontWeight: 600, cursor: 'pointer' }}
            >
              {isLogin ? "Sign up" : "Log in"}
            </button>
          </div>
        </div>
      </div>
      
      {/* Media Queries */}
      <style>{`
        @media (max-width: 768px) {
          .auth-sidebar-hide {
            display: none !important;
          }
        }
        @media (min-width: 769px) {
          .auth-mobile-header {
            display: none !important;
          }
          .auth-sidebar-hide {
            display: flex !important;
          }
        }
      `}</style>
    </div>
  );
};

export default Auth;
