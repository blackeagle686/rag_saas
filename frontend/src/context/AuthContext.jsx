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

  const login = async (email, password) => {
    await api.login(email, password);
    setIsAuthenticated(true);
    checkHealth(); // Re-check health with new token
  };

  const register = async (name, email, password) => {
    await api.register(name, email, password);
    setIsAuthenticated(true);
    checkHealth(); // Re-check health with new token
  };

  const logout = () => {
    api.clearToken();
    setIsAuthenticated(false);
    setApiHealth('checking');
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, register, logout, apiHealth }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
