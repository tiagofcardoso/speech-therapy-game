import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import ProgressTracker from '../components/ProgressTracker';
import SpeechControls from '../components/SpeechControls';
import { FaHome, FaArrowLeft } from 'react-icons/fa';
import './GameScreen.css';

const GameScreen = () => {
    const [sessionId, setSessionId] = useState(null);
    const [currentExercise, setCurrentExercise] = useState(null);
    const [instructions, setInstructions] = useState(null);
    const [feedback, setFeedback] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showInstructions, setShowInstructions] = useState(true);
    const [sessionComplete, setSessionComplete] = useState(false);
    const [finalScore, setFinalScore] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        startGame();
    }, []);

    const startGame = async () => {
        try {
            setIsLoading(true);
            setError(null);

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
            setShowInstructions(true);
        } catch (err) {
            console.error('Error starting game:', err);
            setError('Failed to start the game. Please try again.');

            if (err.response && err.response.status === 401) {
                navigate('/login');
            }
        } finally {
            setIsLoading(false);
        }
    };

    const handleStartExercises = () => {
        setShowInstructions(false);
    };

    // Add this function to your GameScreen component

    const fetchGame = async (gameId) => {
        try {
            setIsLoading(true);
            setError(null);

            const token = localStorage.getItem('token');
            const response = await axios.get(`/api/games/${gameId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.data.success) {
                console.error('Error in game data:', response.data.message);
                setError(response.data.message || 'Failed to load game data');
                return null;
            }

            // Successfully loaded the game
            return response.data.game;
        } catch (error) {
            console.error('Error fetching game:', error);
            setError(error.message || 'Failed to load game');
            return null;
        } finally {
            setIsLoading(false);
        }
    };

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

            if (response.data.session_complete) {
                setSessionComplete(true);
                setFinalScore(response.data.final_score);
                setFeedback(response.data.feedback);
            } else {
                setFeedback(response.data.feedback);

                // If not repeating the current exercise, update to the next one
                if (!response.data.repeat_exercise) {
                    setCurrentExercise(response.data.current_exercise);
                }
            }
        } catch (err) {
            console.error('Error submitting response:', err);
            setError('Failed to process your speech. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleGoToDashboard = () => {
        navigate('/dashboard');
    };

    const handleNewGame = () => {
        setSessionComplete(false);
        setFeedback(null);
        startGame();
    };

    if (isLoading && !currentExercise) {
        return (
            <div className="loading-container">
                <div className="loading-spinner"></div>
                <p>Loading your speech game...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="game-error">
                <h2>Oops! Something went wrong</h2>
                <p>{error}</p>
                <button className="primary-button" onClick={startGame}>
                    Try Again
                </button>
                <button className="secondary-button" onClick={handleGoToDashboard}>
                    Go to Dashboard
                </button>
            </div>
        );
    }

    if (sessionComplete) {
        return (
            <div className="game-complete">
                <div className="game-complete-content">
                    <h2>Great Job!</h2>
                    <div className="final-score-container">
                        <div className="final-score-circle">
                            <span>{finalScore}%</span>
                        </div>
                    </div>
                    <div className="feedback">
                        <p className="praise">{feedback?.praise}</p>
                        <p className="encouragement">{feedback?.encouragement}</p>
                    </div>
                    <div className="game-complete-buttons">
                        <button className="primary-button" onClick={handleNewGame}>
                            Play Again
                        </button>
                        <button className="secondary-button" onClick={handleGoToDashboard}>
                            Back to Dashboard
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="game-screen">
            <header className="game-header">
                <button className="back-button" onClick={handleGoToDashboard}>
                    <FaHome /> Dashboard
                </button>
                <h1>Speech Practice</h1>
            </header>

            {showInstructions && instructions ? (
                <div className="instructions-container">
                    <div className="instructions-content">
                        <h2>{instructions.greeting}</h2>
                        <p>{instructions.explanation}</p>
                        <p className="encouragement">{instructions.encouragement}</p>
                        <button className="start-button" onClick={handleStartExercises}>
                            Start Exercises
                        </button>
                    </div>
                </div>
            ) : (
                <>
                    {currentExercise && (
                        <div className="game-content">
                            <ProgressTracker
                                current={currentExercise.index}
                                total={currentExercise.total}
                            />

                            <div className="exercise-card">
                                <div className="word-container">
                                    <h2 className="target-word">{currentExercise.word}</h2>
                                    <p className="word-prompt">{currentExercise.prompt}</p>
                                </div>

                                <div className="visual-cue">
                                    {/* This would be an actual image in production */}
                                    <div className="image-placeholder">
                                        {currentExercise.visual_cue}
                                    </div>
                                </div>

                                <div className="hint-container">
                                    <p className="hint"><strong>Hint:</strong> {currentExercise.hint}</p>
                                </div>

                                <SpeechControls
                                    word={currentExercise.word}
                                    onRecognitionComplete={handleRecognitionComplete}
                                    isLoading={isLoading}
                                />
                            </div>

                            {feedback && (
                                <div className="feedback-container">
                                    <div className="feedback-content">
                                        <p className="feedback-praise">{feedback.praise}</p>
                                        {feedback.correction && (
                                            <p className="feedback-correction">{feedback.correction}</p>
                                        )}
                                        <p className="feedback-tip">{feedback.tip}</p>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default GameScreen;