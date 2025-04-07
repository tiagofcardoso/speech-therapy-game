import axios from 'axios';

const api = axios.create({
    // Certifique-se que está usando a porta correta onde o backend está rodando
    baseURL: 'http://localhost:5001',
    withCredentials: false
});

// Verifique se o interceptor não está causando problemas para rotas de autenticação
api.interceptors.request.use(
    config => {
        // Não devemos incluir token em rotas de autenticação
        if (config.url && (config.url.includes('/login') || config.url.includes('/register'))) {
            return config;  // Não adicione o token para login/registro
        }

        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    error => Promise.reject(error)
);

export default api;