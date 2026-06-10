import React, { useState, useEffect } from 'react';
import api from '../../api/client';
import Alert from '../Alert';

const BillingTab = () => {
  const [loading, setLoading] = useState(null);
  const [alert, setAlert] = useState(null);
  const [currentPlan, setCurrentPlan] = useState('free');
  
  useEffect(() => {
    loadPlan();
    const params = new URLSearchParams(window.location.search);
    if (params.get('success') === 'true') {
      setAlert({ type: 'success', message: 'Payment successful! Your plan has been upgraded.' });
    }
  }, []);

  const loadPlan = async () => {
    try {
      const data = await api.getSettings();
      if (data && data.plan) setCurrentPlan(data.plan);
    } catch (error) {
      console.error('Failed to load plan', error);
    }
  };

  const getPlanProps = (planId) => {
    const weights = { free: 0, start: 1, mid: 2, prime: 3 };
    const currW = weights[currentPlan] || 0;
    const tarW = weights[planId] || 0;
    
    if (planId === currentPlan) return { text: 'Current Plan', disabled: true };
    if (tarW < currW) return { text: 'Downgrade', disabled: false };
    return { text: `Upgrade to ${planId.charAt(0).toUpperCase() + planId.slice(1)}`, disabled: false };
  };

  const plans = [
    {
      id: 'free',
      name: 'Free (Playground)',
      price: '$0',
      description: 'Test the platform without any friction.',
      features: ['Local Embeddings', 'Chroma DB', 'Basic RAG System', 'Dashboard Chatbot', '10 Requests / Day']
    },
    {
      id: 'start',
      name: 'Start',
      price: '$29',
      interval: '/mo',
      description: 'For early-stage startups and MVPs.',
      features: ['API Deployment', 'Advanced RAG', 'GPT-4o-mini', '50 MB Ingestion', '500 Requests / Day']
    },
    {
      id: 'mid',
      name: 'Mid',
      price: '$99',
      interval: '/mo',
      description: 'For growing businesses needing scale and speed.',
      features: ['Qdrant DB Cluster', 'Hybrid Models (GPT/Gemini)', 'CAG System', 'Web App Templates', '5,000 Requests / Day']
    },
    {
      id: 'prime',
      name: 'Prime',
      price: '$299',
      interval: '/mo',
      description: 'Enterprise scale with autonomous agents.',
      features: ['Bring Your Own DB', 'Agentic & MultiModal RAG', 'Claude 3.5 & GPT-4o', 'White-labeled Apps', '50,000 Requests / Day']
    }
  ];

  const handleUpgrade = async (planId) => {
    setLoading(planId);
    setAlert(null);
    try {
      const response = await api.createCheckoutSession(planId);
      if (response.url) {
        window.location.href = response.url;
      }
    } catch (error) {
      setAlert({ type: 'error', message: error.message || 'Failed to start checkout session' });
      setLoading(null);
    }
  };

  return (
    <section className="tab-content">
      <header className="header" style={{ marginBottom: '2rem', padding: '0' }}>
        <h1 style={{ fontSize: '1.8rem', fontFamily: 'var(--font-display)' }}>Subscription Plans</h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>Upgrade your plan to deploy to production and access advanced models.</p>
      </header>

      <Alert {...alert} onClose={() => setAlert(null)} />

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: '1.5rem',
        marginTop: '2rem'
      }}>
        {plans.map((plan) => (
          <div key={plan.id} className="glass-card" style={{ 
            display: 'flex', 
            flexDirection: 'column', 
            border: plan.id === 'mid' ? '1px solid var(--accent-primary)' : '1px solid var(--border-color)',
            boxShadow: plan.id === 'mid' ? 'var(--shadow-glow)' : 'var(--shadow-md)',
            position: 'relative'
          }}>
            {plan.id === 'mid' && (
              <div style={{
                position: 'absolute',
                top: '-12px',
                right: '20px',
                background: 'var(--accent-glow)',
                color: 'white',
                fontSize: '0.75rem',
                fontWeight: 'bold',
                padding: '0.3rem 0.8rem',
                borderRadius: 'var(--radius-full)',
                textTransform: 'uppercase',
                letterSpacing: '1px',
                boxShadow: 'var(--shadow-md)'
              }}>Most Popular</div>
            )}
            
            <h3 style={{ fontSize: '1.4rem', fontFamily: 'var(--font-display)', marginBottom: '0.5rem' }}>{plan.name}</h3>
            <div style={{ marginBottom: '1rem' }}>
              <span style={{ fontSize: '2.5rem', fontWeight: 'bold' }}>{plan.price}</span>
              {plan.interval && <span style={{ color: 'var(--text-secondary)' }}>{plan.interval}</span>}
            </div>
            
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginBottom: '1.5rem', flexGrow: 1 }}>
              {plan.description}
            </p>
            
            <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 2rem 0', display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
              {plan.features.map((feature, i) => (
                <li key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', fontSize: '0.95rem', color: 'var(--text-primary)' }}>
                  <div style={{ 
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    width: '20px', height: '20px', borderRadius: '50%', 
                    background: 'var(--color-success-bg)', color: 'var(--color-success)',
                    fontSize: '0.8rem', fontWeight: 'bold'
                  }}>✓</div>
                  {feature}
                </li>
              ))}
            </ul>
            
            <button 
              className={`btn ${plan.id === currentPlan ? 'btn-secondary' : plan.id === 'mid' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ width: '100%', marginTop: 'auto', padding: '0.8rem', opacity: plan.id === currentPlan ? 0.7 : 1 }}
              onClick={() => handleUpgrade(plan.id)}
              disabled={getPlanProps(plan.id).disabled || loading !== null}
            >
              {loading === plan.id ? 'Loading...' : getPlanProps(plan.id).text}
            </button>
          </div>
        ))}
      </div>
      
      <div className="glass-card" style={{ marginTop: '3rem', textAlign: 'center', padding: '2rem' }}>
        <h3 style={{ marginBottom: '0.5rem', fontSize: '1.3rem' }}>Pay-as-you-go / Enterprise</h3>
        <p style={{ color: 'var(--text-secondary)' }}>Need unlimited scale, dedicated instances, and custom SLAs? Contact our sales team for a tailored solution.</p>
        <button className="btn btn-secondary" style={{ marginTop: '1.5rem', padding: '0.6rem 2rem' }}>Contact Sales</button>
      </div>
    </section>
  );
};

export default BillingTab;
