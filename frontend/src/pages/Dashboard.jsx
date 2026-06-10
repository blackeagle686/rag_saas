import React, { useState } from 'react';
import Header from '../components/Header';
import OverviewTab from '../components/Tabs/OverviewTab';
import NamespacesTab from '../components/Tabs/NamespacesTab';
import ApiKeysTab from '../components/Tabs/ApiKeysTab';
import PlaygroundTab from '../components/Tabs/PlaygroundTab';
import SettingsTab from '../components/Tabs/SettingsTab';

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <div className="app-container" style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="main-content" style={{ flexGrow: 1, overflowY: 'auto', padding: '2rem' }}>
        <div style={{ display: activeTab === 'overview' ? 'block' : 'none' }}>
          <OverviewTab />
        </div>
        <div style={{ display: activeTab === 'namespaces' ? 'block' : 'none' }}>
          <NamespacesTab />
        </div>
        <div style={{ display: activeTab === 'keys' ? 'block' : 'none' }}>
          <ApiKeysTab />
        </div>
        <div style={{ display: activeTab === 'playground' ? 'block' : 'none' }}>
          <PlaygroundTab />
        </div>
        <div style={{ display: activeTab === 'settings' ? 'block' : 'none' }}>
          <SettingsTab />
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
