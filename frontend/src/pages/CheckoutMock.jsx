import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import api from '../api/client';
import Header from '../components/Header';
import Alert from '../components/Alert';

const CheckoutMock = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const planId = searchParams.get('plan') || 'free';
  
  const [loading, setLoading] = useState(false);
  const [alert, setAlert] = useState(null);

  const planDetails = {
    start: { name: 'Start Plan', price: '$29/mo' },
    mid: { name: 'Mid Plan', price: '$99/mo' },
    prime: { name: 'Prime Plan', price: '$299/mo' }
  };
  
  const planInfo = planDetails[planId] || { name: 'Unknown Plan', price: '$0/mo' };

  const handleSimulatePayment = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.mockCheckoutSuccess(planId);
      navigate('/dashboard?success=true');
    } catch (error) {
      setAlert({ type: 'error', message: error.message || 'Failed to simulate payment.' });
      setLoading(false);
    }
  };

  return (
    <div className="app-container" style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      <Header activeTab="" setActiveTab={() => navigate('/dashboard')} />
      
      <main className="main-content" style={{ flexGrow: 1, overflowY: 'auto', padding: '2rem', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <div className="glass-card animate-fade-in" style={{ width: '100%', maxWidth: '500px', padding: '3rem' }}>
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <div style={{ display: 'inline-block', background: 'rgba(245, 158, 11, 0.2)', color: 'var(--color-warning)', padding: '0.5rem 1rem', borderRadius: '50px', fontSize: '0.85rem', fontWeight: 600, marginBottom: '1rem', border: '1px solid var(--color-warning)' }}>
              Development Mode Checkout
            </div>
            <h1 className="section-title" style={{ fontSize: '2rem' }}>{planInfo.name}</h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '1.2rem' }}>Total: <strong>{planInfo.price}</strong></p>
          </div>

          <Alert {...alert} onClose={() => setAlert(null)} />

          <form onSubmit={handleSimulatePayment}>
            <div className="form-group">
              <label className="form-label">Cardholder Name (Mock)</label>
              <input type="text" className="form-input" placeholder="Jane Doe" required defaultValue="Developer Sandbox" />
            </div>
            <div className="form-group">
              <label className="form-label">Card Number (Mock)</label>
              <input type="text" className="form-input" placeholder="4242 4242 4242 4242" required defaultValue="4242 4242 4242 4242" />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label">Expiry</label>
                <input type="text" className="form-input" placeholder="MM/YY" required defaultValue="12/34" />
              </div>
              <div className="form-group">
                <label className="form-label">CVC</label>
                <input type="text" className="form-input" placeholder="123" required defaultValue="123" />
              </div>
            </div>
            
            <button 
              type="submit" 
              className="btn btn-primary" 
              style={{ width: '100%', marginTop: '1.5rem', padding: '1rem', fontSize: '1.1rem' }}
              disabled={loading}
            >
              {loading ? 'Processing...' : `Pay ${planInfo.price}`}
            </button>
            <button 
              type="button" 
              className="btn btn-secondary" 
              style={{ width: '100%', marginTop: '0.75rem' }}
              onClick={() => navigate('/dashboard')}
              disabled={loading}
            >
              Cancel
            </button>
          </form>
          
          <div style={{ marginTop: '2rem', textAlign: 'center', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            This is a simulated payment gateway. No real charges will be made.
          </div>
        </div>
      </main>
    </div>
  );
};

export default CheckoutMock;
