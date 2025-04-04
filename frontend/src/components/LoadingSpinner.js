import React from 'react';
import './LoadingSpinner.css'; // Criaremos este arquivo em seguida

const LoadingSpinner = () => {
    return (
        <div className="loading-container">
            <div className="spinner"></div>
            <p>Loading...</p>
        </div>
    );
};

export default LoadingSpinner;