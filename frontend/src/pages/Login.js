import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import './Auth.css';

const Login = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const navigate = useNavigate();

    // Função de teste da API
    const testApi = async () => {
        try {
            const result = await fetch('http://localhost:5000/api/ping');
            const data = await result.json();
            console.log('Direct API test result:', data);
            alert('API Test: ' + JSON.stringify(data));
        } catch (error) {
            console.error('Direct API test error:', error);
            alert('API Test Error: ' + error.message);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (!username || !password) {
            setError('Please enter both username and password');
            return;
        }

        try {
            setIsLoading(true);
            console.log('Sending login request to backend...');

            const response = await api.post('/api/auth/login', {
                username,
                password
            });

            console.log('Login response:', response.data);

            if (response.data.success) {
                // Store token in localStorage
                localStorage.setItem('token', response.data.token);
                localStorage.setItem('user_id', response.data.user_id);
                localStorage.setItem('name', response.data.name || 'User');

                // Navigate to dashboard
                navigate('/dashboard');
            } else {
                setError(response.data.message || 'Invalid credentials');
            }
        } catch (err) {
            console.error('Login error:', err);
            // Mostrar mais detalhes do erro
            setError(
                err.response?.data?.message ||
                `Login failed: ${err.message}. ${err.response?.status === 500 ?
                    'Server error. Please check with administrator.' :
                    'Please check your credentials.'
                }`
            );
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-card">
                <div className="auth-header">
                    <h2>Speech Therapy Game</h2>
                    <h3>Login to Your Account</h3>
                </div>

                {/* Botão de teste API */}
                <button
                    type="button"
                    onClick={testApi}
                    style={{ marginBottom: '15px', padding: '8px 12px', backgroundColor: '#4CAF50' }}
                >
                    Test API Connection
                </button>

                {error && <div className="auth-error">{error}</div>}

                <form onSubmit={handleSubmit} className="auth-form">
                    <div className="form-group">
                        <label htmlFor="username">Username</label>
                        <input
                            type="text"
                            id="username"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            disabled={isLoading}
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="password">Password</label>
                        <input
                            type="password"
                            id="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            disabled={isLoading}
                        />
                    </div>

                    <button
                        type="submit"
                        className="auth-button"
                        disabled={isLoading}
                    >
                        {isLoading ? 'Logging in...' : 'Login'}
                    </button>
                </form>

                <div className="auth-footer">
                    Don't have an account? <Link to="/register">Register here</Link>
                </div>
            </div>
        </div>
    );
};

export default Login;