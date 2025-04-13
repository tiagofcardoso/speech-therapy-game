import React, { useState, useEffect } from 'react';
import './CharacterGuide.css';

const CharacterGuide = ({ message, onClose, onNext }) => {
    const [isAnimating, setIsAnimating] = useState(false);

    // Animate character periodically
    useEffect(() => {
        const interval = setInterval(() => {
            setIsAnimating(true);
            setTimeout(() => setIsAnimating(false), 1000);
        }, 5000);

        return () => clearInterval(interval);
    }, []);

    return (
        <div className="character-guide-container">
            <div className={`character-figure ${isAnimating ? 'bounce' : ''}`}>
                <div className="character-head">
                    <div className="character-face">
                        <div className="character-eyes">
                            <div className="character-eye"></div>
                            <div className="character-eye"></div>
                        </div>
                        <div className="character-smile"></div>
                    </div>
                </div>
                <div className="character-body"></div>
            </div>

            <div className="speech-bubble">
                <p>{message}</p>
                <div className="bubble-actions">
                    <button
                        className="bubble-button next-tip"
                        onClick={onNext}
                        aria-label="Próxima dica"
                    >
                        Mais dicas
                    </button>
                    <button
                        className="bubble-button close-tip"
                        onClick={onClose}
                        aria-label="Fechar dica"
                    >
                        Entendi!
                    </button>
                </div>
            </div>
        </div>
    );
};

export default CharacterGuide;