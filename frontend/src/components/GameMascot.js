import React, { useState, useEffect } from 'react';
import './GameMascot.css';

const GameMascot = ({ mood = 'neutral', message = null, name = 'Fala' }) => {
    const [animation, setAnimation] = useState('idle');

    // Change l'animation en fonction de l'humeur
    useEffect(() => {
        if (mood === 'happy') {
            setAnimation('jump');
            setTimeout(() => setAnimation('idle'), 2000);
        } else if (mood === 'excited') {
            setAnimation('dance');
            setTimeout(() => setAnimation('idle'), 3000);
        } else if (mood === 'thinking') {
            setAnimation('thinking');
        } else {
            setAnimation('idle');
        }
    }, [mood]);

    // Différentes mascottes disponibles
    const mascots = {
        default: {
            neutral: '🦊',
            happy: '🦊',
            sad: '🦊',
            excited: '🦊',
            thinking: '🦊'
        },
        frog: {
            neutral: '🐸',
            happy: '🐸',
            sad: '🐸',
            excited: '🐸',
            thinking: '🐸'
        },
        robot: {
            neutral: '🤖',
            happy: '🤖',
            sad: '🤖',
            excited: '🤖',
            thinking: '🤖'
        },
        alien: {
            neutral: '👽',
            happy: '👽',
            sad: '👽',
            excited: '👽',
            thinking: '👽'
        }
    };

    // Utilise la mascotte par défaut si le nom n'est pas reconnu
    const mascot = mascots[name] || mascots.default;
    const emoji = mascot[mood] || mascot.neutral;

    return (
        <div className="game-mascot-container">
            <div className={`game-mascot ${animation}`}>
                <div className="mascot-emoji">{emoji}</div>
            </div>
            {message && <div className="mascot-message">{message}</div>}
        </div>
    );
};

export default GameMascot;