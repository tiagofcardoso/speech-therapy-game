import axios from 'axios';

// Create base axios instance with common config
const api = axios.create({
    baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5001',
    timeout: 15000, // Default timeout for most requests
    headers: {
        'Content-Type': 'application/json'
    }
});

// Request interceptor to add authentication token
api.interceptors.request.use(
    config => {
        console.log(`🚀 API Request: ${config.method.toUpperCase()} ${config.url} ${JSON.stringify(config.data || {})}`);

        // Add timestamp to prevent caching
        const separator = config.url.includes('?') ? '&' : '?';
        config.url = `${config.url}${separator}_t=${Date.now()}`;

        // Add authentication token if available
        const token = localStorage.getItem('token');
        console.log(`Token in localStorage: ${token ? 'Present' : 'Not found'}`);

        if (token) {
            console.log(`Token added to header: Bearer ${token.substring(0, 10)}...`);
            config.headers.Authorization = `Bearer ${token}`;
        }

        // Increase timeout for specific long-running operations
        if (config.url.includes('/gigi/generate-game')) {
            console.log('🕒 Increasing timeout for game generation to 60 seconds');
            config.timeout = 60000; // 60 seconds for game generation
        } else if (config.url.includes('/game/finish')) {
            console.log('🕒 Increasing timeout for game completion to 30 seconds');
            config.timeout = 30000; // 30 seconds for game completion
        }

        return config;
    },
    error => {
        console.error('❌ Request error:', error);
        return Promise.reject(error);
    }
);

// Response interceptor to handle common errors
api.interceptors.response.use(
    response => {
        console.log(`✅ API Response Success: ${response.config.url}`);
        return response;
    },
    error => {
        // Enhanced error logging for debugging
        if (error.response) {
            console.error(`❌ API Error: ${error.response.status} ${error.response.config.url}`, error.response.data);
        } else if (error.request) {
            console.error(`❌ API Error: No response received ${error.config.url}`, error.request);

            // For game generation timeouts, provide a more helpful message
            if (error.config.url.includes('/gigi/generate-game') && error.message.includes('timeout')) {
                console.error('Game generation is taking longer than expected. The server might still be processing your request.');
            }

            // For game/finish endpoint specifically, create a simulated success response
            if (error.config.url.includes('/game/finish') && error.config.method === 'post') {
                console.log('Returning simulated success response for game completion to ensure UI flow continues');
                return Promise.resolve({
                    data: {
                        success: true,
                        message: "Game completion process continued despite network error",
                        simulated: true,
                        original_error: error.message
                    }
                });
            }
        } else {
            console.error(`❌ API Error: ${error.message}`);
        }

        return Promise.reject(error);
    }
);

// Helper methods for common API operations
const apiHelpers = {
    // GET request with authentication
    get: (url, config = {}) => api.get(url, config),

    // POST request with authentication
    post: (url, data = {}, config = {}) => api.post(url, data, config),

    // POST with retry for game generation
    postWithRetry: async (url, data = {}, config = {}, maxRetries = 2) => {
        let lastError;

        for (let attempt = 1; attempt <= maxRetries + 1; attempt++) {
            try {
                console.log(`Attempt ${attempt}/${maxRetries + 1} for ${url}`);
                return await api.post(url, data, config);
            } catch (error) {
                lastError = error;
                const isTimeout = error.message.includes('timeout');

                if (attempt <= maxRetries && isTimeout) {
                    console.log(`Request timed out, retrying (${attempt}/${maxRetries})...`);
                    await new Promise(resolve => setTimeout(resolve, 1000)); // Wait before retrying
                } else {
                    break;
                }
            }
        }

        throw lastError;
    },

    // PUT request with authentication
    put: (url, data = {}, config = {}) => api.put(url, data, config),

    // DELETE request with authentication
    delete: (url, config = {}) => api.delete(url, config),

    // Test API connection
    ping: () => api.get('/api/ping'),

    // Upload file with progress tracking
    upload: (url, formData, onProgress) => {
        return api.post(url, formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            },
            onUploadProgress: progressEvent => {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                if (onProgress) onProgress(percentCompleted);
            }
        });
    }
};

export default apiHelpers;