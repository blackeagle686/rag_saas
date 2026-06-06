import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../api/client';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(api.isAuthenticated());
  const [apiHealth, setApiHealth] = useState('checking'); // 'checking', 'ok', 'degraded', 'disconnected'

  useEffect(() => {
    checkHealth();
    // Poll health every 30 seconds
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      const data = await api.getHealth();
      if (data && data.status === 'ok') {
        setApiHealth('ok');
      } else {
        setApiHealth('degraded');
      }
    } catch (error) {
      setApiHealth('disconnected');
    }
  };

  const login = (key) => {
    api.setApiKey(key);
    setIsAuthenticated(true);
    checkHealth(); // Re-check health with new key
  };

  const logout = () => {
    api.clearApiKey();
    setIsAuthenticated(false);
    setApiHealth('checking');
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout, apiHealth }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
