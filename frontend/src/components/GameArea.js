import React, { useState, useEffect } from 'react';
import axios from 'axios';
import SpeechControls from './SpeechControls';
import ProgressTracker from './ProgressTracker';
import { useNavigate } from 'react-router-dom';
import './GameArea.css';

const GameArea = () => {
    const navigate = useNavigate();
    const [sessionId, setSessionId] = useState(null);
    const [currentExercise, setCurrentExercise] = useState(null);
    const [feedback, setFeedback] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [instructions, setInstructions] = useState(null);
    const [sessionComplete, setSessionComplete] = useState(false);
    const [finalScore, setFinalScore] = useState(0);

    // Start a new game session when component mounts
    useEffect(() => {
        startGame();
    }, []);

    // Start a new game session
    const startGame = async () => {
        try {
            setIsLoading(true);

            const token = localStorage.getItem('token');
            const response = await axios.post(
                '/api/start_game',
                {},
                {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                }
            );

            setSessionId(response.data.session_id);
            setCurrentExercise(response.data.current_exercise);
            setInstructions(response.data.instructions);
            setIsLoading(false);
        } catch (err) {
            console.error('Error starting game:', err);
            setIsLoading(false);

            if (err.response && err.response.status === 401) {
                // Unauthorized - redirect to login
                navigate('/login');
            }
        }
    };

    // Handle speech recognition results
    const handleRecognitionComplete = async (recognizedText) => {
        if (!sessionId || !recognizedText) return;

        try {
            setIsLoading(true);

            const token = localStorage.getItem('token');
            const response = await axios.post(
                '/api/submit_response',
                {
                    session_id: sessionId,
                    recognized_text: recognizedText
                },
                {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                }
            );

            // Handle session completion
            if (response.data.session_complete) {
                setSessionComplete(true);
                setFinalScore(response.data.final_score);
            } else {
                // Update with feedback and potentially new exercise
                setFeedback(response.data.feedback);
                setCurrentExercise(response.data.current_exercise);
            }

            setIsLoading(false);
        } catch (err) {
            console.error('Error submitting response:', err);
            setIsLoading(false);
        }
    };

    // Start a new game session
    const handleNewGame = () => {
        setSessionComplete(false);
        setFeedback(null);
        startGame();
    };

    if (isLoading) {
        return <div className="loading">Loading game...</div>;
    }

    if (sessionComplete) {
        return (
            <div className="game-complete">
                <h2>Game Complete!</h2>
                <div className="final-score">
                    <h3>Your Score: {finalScore}</h3>
                    <p>{feedback.praise}</p>
                    <p>{feedback.encouragement}</p>
                </div>
                <button className="btn btn-primary" onClick={handleNewGame}>
                    Play Again
                </button>
            </div>
        );
    }

    return (
        <div className="game-area">
            {/* Instructions */}
            {instructions && (
                <div className="instructions">
                    <h2>{instructions.greeting}</h2>
                    <p>{instructions.explanation}</p>
                    <p className="encouragement">{instructions.encouragement}</p>
                </div>
            )}

            {/* Progress tracker */}
            {currentExercise && (
                <ProgressTracker
                    current={currentExercise.index}
                    total={currentExercise.total}
                />
            )}

            {/* Current exercise */}
            {currentExercise && (
                <div className="exercise-card">
                    <div className="visual-cue">
                        {/* Placeholder for visual cue - this would be an actual image in production */}
                        <div className="image-placeholder">{currentExercise.visual_cue}</div>
                    </div>

                    <div className="word-area">
                        <h2 className="target-word">{currentExercise.word}</h2>
                        <p className="prompt">{currentExercise.prompt}</p>
                        <p className="hint"><strong>Hint:</strong> {currentExercise.hint}</p>
                    </div>

                    {/* Speech controls for recording/listening */}
                    <SpeechControls
                        word={currentExercise.word}
                        onRecognitionComplete={handleRecognitionComplete}
                    />
                </div>
            )}

            {/* Feedback area */}
            {feedback && (
                <div className="feedback-area">
                    <div className="feedback-card">
                        <p className="praise">{feedback.praise}</p>
                        {feedback.correction && (
                            <p className="correction">{feedback.correction}</p>
                        )}
                        <p className="tip">{feedback.tip}</p>
                    </div>
                </div>
            )}
        </div>
    );
};

export default GameArea;