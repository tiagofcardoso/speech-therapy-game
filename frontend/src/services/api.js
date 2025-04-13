import axios from 'axios';

const api = axios.create({
    // Certifique-se que está usando a porta correta onde o backend está rodando
    baseURL: 'http://localhost:5001',
    withCredentials: false
});

// Interceptor para requisições - adiciona token e logs
api.interceptors.request.use(
    config => {
        console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`, config.data || '');

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
    error => {
        console.error("❌ Erro na requisição API:", error);
        return Promise.reject(error);
    }
);

// Novo interceptor para respostas - adiciona logs detalhados
api.interceptors.response.use(
    response => {
        console.log(`✅ API Response (${response.status}):`, response.config.url, response.data);
        return response;
    },
    error => {
        if (error.response) {
            // A requisição foi feita, mas o servidor respondeu com status diferente de 2xx
            console.error(`❌ API Error (${error.response.status}):`,
                error.config.url,
                error.response.data);
        } else if (error.request) {
            // A requisição foi feita, mas não recebeu resposta
            console.error('❌ API Error: No response received', error.config?.url, error.request);
        } else {
            // Erro ao configurar a requisição
            console.error('❌ API Error: Request setup failed', error.message);
        }
        return Promise.reject(error);
    }
);

// Adicionar um timestamp para evitar problemas de cache
api.interceptors.request.use(config => {
    // Adicionar timestamp para evitar problemas de cache
    const separator = config.url.includes('?') ? '&' : '?';
    config.url = `${config.url}${separator}_t=${Date.now()}`;
    return config;
});

export default api;