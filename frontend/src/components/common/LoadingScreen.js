import React from 'react';
import './LoadingScreen.css';

const LoadingScreen = ({ message = "Carregando..." }) => {
    return (
        <div className="loading-screen">
            <div className="loading-animation">
                <div className="character-container">
                    <div className="character">
                        <div className="face">
                            <div className="eye left"></div>
                            <div className="eye right"></div>
                            <div className="mouth"></div>
                        </div>
                    </div>
                </div>
                <div className="loading-bubbles">
                    <div className="bubble"></div>
                    <div className="bubble"></div>
                    <div className="bubble"></div>
                </div>
            </div>
            <h3 className="loading-message">{message}</h3>
        </div>
    );
};

export default LoadingScreen;