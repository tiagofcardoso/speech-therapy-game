import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Exercise from './pages/Exercise';
import PrivateRoute from './components/PrivateRoute';
import MCPGameGenerator from './components/MCPGameGenerator';
import GigiGameGenerator from './components/GigiGameGenerator';
import GamePlay from './components/GamePlay';
import LoadingScreen from './components/common/LoadingScreen';
import AccessibilityControls from './components/common/AccessibilityControls';
import ThemeSwitcher from './components/common/ThemeSwitcher';
import ThemeProvider from './context/ThemeContext';
import { ToastProvider } from './components/common/SimpleToast';
import axios from 'axios';
import './App.css';

// Token refresh e interceptors
axios.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;

    // Se o erro for devido a um token expirado (geralmente 401)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Chamada para endpoint de refresh token
        const refreshResponse = await axios.post('/api/auth/refresh', {
          refresh_token: localStorage.getItem('refresh_token')
        });

        // Armazena o novo token
        const { token } = refreshResponse.data;
        localStorage.setItem('token', token);

        // Atualiza o cabeçalho de autorização
        originalRequest.headers.Authorization = `Bearer ${token}`;

        // Tenta a requisição original novamente
        return axios(originalRequest);
      } catch (refreshError) {
        // Se o refresh falhar, redireciona para login
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

function App() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simula carregamento inicial de recursos
    const timer = setTimeout(() => {
      setLoading(false);
    }, 1500);

    return () => clearTimeout(timer);
  }, []);

  if (loading) {
    return <LoadingScreen message="Carregando sua aventura de aprendizagem..." />;
  }

  return (
    <ThemeProvider>
      <ToastProvider>
        <Router>
          <div className="App">
            <AccessibilityControls />
            <ThemeSwitcher />
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/mcp-games" element={<MCPGameGenerator />} />
              <Route path="/gigi-games" element={<GigiGameGenerator />} />

              {/* Rota para Dashboard */}
              <Route
                path="/dashboard"
                element={
                  <PrivateRoute>
                    <Dashboard />
                  </PrivateRoute>
                }
              />

              {/* Rota para exercícios */}
              <Route
                path="/exercise/:exerciseId"
                element={
                  <PrivateRoute>
                    <Exercise />
                  </PrivateRoute>
                }
              />

              {/* Rota para jogar */}
              <Route
                path="/play/:gameId"
                element={
                  <PrivateRoute>
                    <GamePlay />
                  </PrivateRoute>
                }
              />

              {/* Redirecionar para dashboard quando acessar a raiz */}
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </div>
        </Router>
      </ToastProvider>
    </ThemeProvider>
  );
}

export default App;