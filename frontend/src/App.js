import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Exercise from './pages/Exercise';  // Importe o novo componente
import PrivateRoute from './components/PrivateRoute';
import MCPGameGenerator from './components/MCPGameGenerator';
import GigiGameGenerator from './components/GigiGameGenerator'; // Import the GigiGameGenerator component
import GamePlay from './components/GamePlay'; // Import the GamePlay component
import './App.css';
import axios from 'axios'; // Import axios

// Add to your api.js
axios.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;

    // If the error is due to an expired token (usually 401)
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Call your refresh token endpoint
        const refreshResponse = await axios.post('/api/auth/refresh', {
          refresh_token: localStorage.getItem('refresh_token')
        });

        // Store the new token
        const { token } = refreshResponse.data;
        localStorage.setItem('token', token);

        // Update the authorization header
        originalRequest.headers.Authorization = `Bearer ${token}`;

        // Retry the original request
        return axios(originalRequest);
      } catch (refreshError) {
        // If refresh fails, redirect to login
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/mcp-games" element={<MCPGameGenerator />} />
          <Route path="/gigi-games" element={<GigiGameGenerator />} /> {/* Add this to your routes configuration */}

          {/* Rota para Dashboard */}
          <Route
            path="/dashboard"
            element={
              <PrivateRoute>
                <Dashboard />
              </PrivateRoute>
            }
          />

          {/* Nova rota para os exercícios */}
          <Route
            path="/exercise/:exerciseId"
            element={
              <PrivateRoute>
                <Exercise />
              </PrivateRoute>
            }
          />

          {/* Nova rota para jogar */}
          <Route path="/play/:gameId" element={<GamePlay />} />

          {/* Redirecionar para dashboard se o usuário tentar acessar a raiz */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;