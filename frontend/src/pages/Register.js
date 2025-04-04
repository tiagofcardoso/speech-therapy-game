import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api'; // Importe o serviço centralizado
import './Auth.css';

const Register = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [name, setName] = useState('');
    const [age, setAge] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const navigate = useNavigate();

    // Adicione a função de teste da API aqui
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
            console.log('Sending registration request to backend...');

            const response = await api.post('/api/auth/register', {
                username,
                password,
                name,
                age: parseInt(age, 10) || 0
            });

            console.log('Registration response:', response.data);

            if (response.data.success) {
                // Store token in localStorage first
                localStorage.setItem('token', response.data.token);
                localStorage.setItem('user_id', response.data.user_id);
                localStorage.setItem('name', name);

                // Navigate without trying to update state afterward
                return navigate('/dashboard');
            } else {
                setError(response.data.message || 'Registration failed');
            }
        } catch (err) {
            console.error('Registration error:', err);
            setError(err.response?.data?.message || 'An error occurred during registration');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-card">
                <div className="auth-header">
                    <h2>Speech Therapy Game</h2>
                    <h3>Create an Account</h3>
                </div>

                {error && <div className="auth-error">{error}</div>}

                {/* Adicione o botão de teste aqui, antes do formulário */}
                <button
                    type="button"
                    onClick={testApi}
                    style={{ marginBottom: '15px', padding: '8px 12px', backgroundColor: '#4CAF50' }}
                >
                    Test API Connection
                </button>

                <form onSubmit={handleSubmit} className="auth-form">
                    <div className="form-group">
                        <label htmlFor="username">Username</label>
                        <input
                            type="text"
                            id="username"
                            name="username"
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
                            name="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            disabled={isLoading}
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="name">Child's Name</label>
                        <input
                            type="text"
                            id="name"
                            name="name"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            disabled={isLoading}
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="age">Child's Age</label>
                        <input
                            type="number"
                            id="age"
                            name="age"
                            min="1"
                            max="15"
                            value={age}
                            onChange={(e) => setAge(e.target.value)}
                            disabled={isLoading}
                        />
                    </div>

                    <button
                        type="submit"
                        className="auth-button"
                        disabled={isLoading}
                    >
                        {isLoading ? 'Registering...' : 'Register'}
                    </button>
                </form>

                <div className="auth-footer">
                    Already have an account? <Link to="/login">Login here</Link>
                </div>
            </div>
        </div>
    );
};

export default Register;