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
            console.log("Rota de autenticação - não adicionando token");
            return config;  // Não adicione o token para login/registro
        }

        const token = localStorage.getItem('token');
        console.log("Token no localStorage:", token ? "Presente" : "Ausente");

        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
            console.log("Token adicionado ao header:", `Bearer ${token.substring(0, 10)}...`);
        } else {
            console.warn("ATENÇÃO: Token não encontrado no localStorage!");
        }

        return config;
    },
    error => Promise.reject(error)
);

export default api;