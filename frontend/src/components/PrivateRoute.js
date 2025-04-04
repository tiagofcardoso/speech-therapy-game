import React from 'react';
import { Navigate } from 'react-router-dom';

const PrivateRoute = ({ children }) => {
    const token = localStorage.getItem('token');

    // Se não houver token, redirecione para a página de login
    if (!token) {
        return <Navigate to="/login" replace />;
    }

    // Se houver token, renderize os filhos (neste caso, o Dashboard)
    return children;
};

export default PrivateRoute;