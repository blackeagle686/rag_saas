import React, { useEffect } from 'react';

const Alert = ({ type = 'success', message, onClose }) => {
  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => {
        if (onClose) onClose();
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [message, onClose]);

  if (!message) return null;

  return (
    <div className={`alert alert-${type} animate-fade-in`}>
      <span>{type === 'success' ? '✓' : '⚠️'}</span>
      <div>{message}</div>
    </div>
  );
};

export default Alert;
