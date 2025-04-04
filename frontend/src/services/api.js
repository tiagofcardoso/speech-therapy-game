import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:5000',
    headers: {
        'Content-Type': 'application/json'
    }
});

// Interceptador para incluir token de autenticação
api.interceptors.request.use(
    config => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        console.log(`API Request: ${config.method.toUpperCase()} ${config.url}`);
        return config;
    },
    error => {
        return Promise.reject(error);
    }
);

// Interceptador para tratar erros de resposta
api.interceptors.response.use(
    response => response,
    error => {
        console.error('API Error:', error.response || error);

        if (error.response && error.response.status === 401) {
            localStorage.removeItem('token');
            localStorage.removeItem('user_id');
            window.location.href = '/login';
        }

        return Promise.reject(error);
    }
);

export default api;