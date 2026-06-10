import React from 'react';
import { useAuth } from '../context/AuthContext';
import { BarChartFill, FolderFill, KeyFill } from 'react-bootstrap-icons';

const Header = ({ activeTab, setActiveTab }) => {
  const { logout, apiHealth } = useAuth();

  const getHealthDotColor = () => {
    switch (apiHealth) {
      case 'ok': return 'var(--color-success)';
      case 'degraded': return 'var(--color-warning)';
      case 'disconnected': return 'var(--color-error)';
      default: return 'var(--text-muted)';
    }
  };



  const navItems = [
    { id: 'overview', icon: <BarChartFill size={18} />, label: 'Overview' },
    { id: 'namespaces', icon: <FolderFill size={18} />, label: 'Namespaces' },
    { id: 'settings', icon: <KeyFill size={18} />, label: 'Settings' },
    { id: 'billing', icon: <span style={{ fontSize: '18px' }}>💳</span>, label: 'Billing & Plans' }
  ];

  return (
    <header style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 2rem',
      height: '70px',
      background: 'rgba(10, 10, 15, 0.8)',
      backdropFilter: 'blur(12px)',
      borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
      position: 'sticky',
      top: 0,
      zIndex: 1000
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '3rem' }}>
        <a href="#" className="sidebar-logo" onClick={(e) => e.preventDefault()} style={{ margin: 0, padding: 0 }}>
          <div className="logo-icon">R</div>
          <span className="logo-text">RAGaaS</span>
        </a>

        <nav>
          <ul style={{ display: 'flex', gap: '0.5rem', listStyle: 'none', margin: 0, padding: 0 }}>
            {navItems.map(item => (
              <li key={item.id}>
                <a 
                  href={`#${item.id}`} 
                  onClick={(e) => { e.preventDefault(); setActiveTab(item.id); }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.5rem 1rem',
                    borderRadius: 'var(--radius-md)',
                    color: activeTab === item.id ? 'var(--primary-color)' : 'var(--text-secondary)',
                    background: activeTab === item.id ? 'rgba(var(--primary-rgb), 0.1)' : 'transparent',
                    textDecoration: 'none',
                    fontWeight: activeTab === item.id ? 600 : 500,
                    transition: 'all 0.2s'
                  }}
                >
                  <span>{item.icon}</span> {item.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: getHealthDotColor(), display: 'inline-block' }}></span>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{apiHealth === 'ok' ? 'Connected' : 'Degraded'}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', borderLeft: '1px solid rgba(255,255,255,0.1)', paddingLeft: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div className="user-avatar" style={{ width: '32px', height: '32px', fontSize: '1rem' }}>D</div>
            <span style={{ fontSize: '0.9rem', fontWeight: 500 }}>Developer Mode</span>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={logout}>Logout</button>
        </div>
      </div>
    </header>
  );
};

export default Header;
