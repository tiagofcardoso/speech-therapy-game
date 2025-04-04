import React, { useState, useEffect } from 'react';
import api from '../services/api';

function ApiTest() {
  const [status, setStatus] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  
  const testApi = async () => {
    setLoading(true);
    setStatus('');
    setMessage('');
    
    try {
      const response = await api.ping();
      setStatus('success');
      setMessage(`API Connected! Response: ${JSON.stringify(response)}`);
    } catch (error) {
      setStatus('error');
      setMessage(`API Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="api-test-container">
      <h2>API Connection Test</h2>
      <button 
        onClick={testApi} 
        disabled={loading}
        className="primary-button"
      >
        {loading ? 'Testing...' : 'Test API Connection'}
      </button>
      
      {status === 'success' && (
        <div className="success-message">{message}</div>
      )}
      
      {status === 'error' && (
        <div className="error-message">{message}</div>
      )}
    </div>
  );
}

export default ApiTest;