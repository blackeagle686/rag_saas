import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Auth from './pages/Auth';
import Dashboard from './pages/Dashboard';
import Landing from './pages/Landing';
import NamespaceDetail from './pages/NamespaceDetail';
import CheckoutMock from './pages/CheckoutMock';
import SharedBot from './pages/SharedBot';
import './styles/variables.css';
import './styles/styles.css';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />;
  }
  return children;
};

const AppRoutes = () => {
  const { isAuthenticated } = useAuth();
  
  return (
    <Routes>
      <Route path="/auth" element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Auth />} />
      <Route path="/" element={<Landing />} />
      <Route 
        path="/dashboard" 
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/namespaces/:name" 
        element={
          <ProtectedRoute>
            <NamespaceDetail />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/checkout-mock" 
        element={
          <ProtectedRoute>
            <CheckoutMock />
          </ProtectedRoute>
        } 
      />
      <Route path="/bot/:namespaceId" element={<SharedBot />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

const App = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
