import React from 'react';
import { useAuth } from '../context/AuthContext';

const Sidebar = ({ activeTab, setActiveTab }) => {
  const { logout, apiHealth } = useAuth();

  const getHealthDotColor = () => {
    switch (apiHealth) {
      case 'ok': return 'var(--color-success)';
      case 'degraded': return 'var(--color-warning)';
      case 'disconnected': return 'var(--color-error)';
      default: return 'var(--text-muted)';
    }
  };

  const getHealthText = () => {
    switch (apiHealth) {
      case 'ok': return 'API Connected';
      case 'degraded': return 'Degraded';
      case 'disconnected': return 'Disconnected';
      default: return 'Checking API...';
    }
  };

  const navItems = [
    { id: 'overview', icon: '📊', label: 'Overview' },
    { id: 'namespaces', icon: '📂', label: 'Namespaces' },
    { id: 'keys', icon: '🔑', label: 'API Keys' },
    { id: 'playground', icon: '💬', label: 'Playground' },
    { id: 'settings', icon: '⚙️', label: 'LLM Settings' }
  ];

  return (
    <aside className="sidebar">
      <a href="#" className="sidebar-logo" onClick={(e) => e.preventDefault()}>
        <div className="logo-icon">R</div>
        <span className="logo-text">RAGaaS</span>
      </a>

      <nav>
        <ul className="sidebar-menu">
          {navItems.map(item => (
            <li className="menu-item" key={item.id}>
              <a 
                href={`#${item.id}`} 
                className={`menu-link ${activeTab === item.id ? 'active' : ''}`}
                onClick={(e) => { e.preventDefault(); setActiveTab(item.id); }}
              >
                <span>{item.icon}</span> {item.label}
              </a>
            </li>
          ))}
        </ul>
      </nav>

      <div className="sidebar-footer">
        <div className="user-profile">
          <div className="user-avatar">D</div>
          <div className="user-info">
            <span className="user-name">Developer Mode</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: getHealthDotColor(), display: 'inline-block' }}></span>
              <span className="user-role">{getHealthText()}</span>
            </div>
          </div>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={logout} style={{ width: '100%' }}>
          Logout
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
