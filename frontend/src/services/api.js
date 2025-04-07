import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:5001',  // Make sure this matches your backend port
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json'
    }
});

// Interceptor to add auth token
api.interceptors.request.use(config => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export default api;