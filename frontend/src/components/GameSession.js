import React, { useState, useEffect } from 'react';

const GameSession = ({ sessionId, onGameComplete }) => {
    const [currentExercise, setCurrentExercise] = useState(null);
    const [error, setError] = useState(null);

    // Add this useEffect to validate exercise data
    useEffect(() => {
        if (currentExercise && !currentExercise.word) {
            console.error("Invalid exercise data:", currentExercise);
            setError("Exercício inválido. Por favor, tente novamente.");
            return;
        }
        // ...rest of the effect
    }, [currentExercise]);

    // ...rest of component code
};

export default GameSession;