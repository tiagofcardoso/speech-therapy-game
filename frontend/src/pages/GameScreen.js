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
    const [difficulty, setDifficulty] = useState("iniciante");
    const [completionThreshold] = useState(80); // Define a threshold for completion
    const navigate = useNavigate();

    useEffect(() => {
        startGame();
    }, []);

    // Adicione esta função para depuração
    const logDebugInfo = (message, data = {}) => {
        console.log(`[DEBUG] ${message}`, {
            timestamp: new Date().toISOString(),
            sessionId,
            difficulty,
            ...data
        });
    };

    const startGame = async (difficultyLevel = "iniciante") => {
        try {
            setIsLoading(true);
            setError(null);

            const token = localStorage.getItem('token');
            const response = await axios.post(
                '/api/start_game',
                { difficulty: difficultyLevel },
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
            setDifficulty(difficultyLevel);
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

    const handleRetryGame = () => {
        setSessionComplete(false);
        setFeedback(null);
        startGame(difficulty);
    };

    const handleNextGame = async () => {
        setSessionComplete(false);
        setFeedback(null);
        setIsLoading(true);

        try {
            const token = localStorage.getItem('token');
            let nextDifficulty = difficulty;

            if (finalScore >= completionThreshold && difficulty !== "avançado") {
                const difficultyMap = {
                    "iniciante": "médio",
                    "médio": "avançado"
                };
                nextDifficulty = difficultyMap[difficulty] || difficulty;
            }

            const response = await axios.post(
                '/api/start_game',
                {
                    difficulty: nextDifficulty,
                    progression: true
                },
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
            setDifficulty(nextDifficulty);
            setShowInstructions(true);
        } catch (err) {
            console.error('Error starting next game:', err);
            setError('Falha ao iniciar o próximo jogo. Tente novamente.');
        } finally {
            setIsLoading(false);
        }
    };

    // Modifique a função handleFinishGame para incluir mais logs
    const handleFinishGame = async (option = 'finish') => {
        logDebugInfo(`Iniciando finalização do jogo com opção: ${option}`);
        console.log(`Enviando finalização para sessionId: ${sessionId}`);

        try {
            setIsLoading(true);

            const token = localStorage.getItem('token');
            const payload = {
                session_id: sessionId,
                completed_manually: true,
                completion_option: option
            };

            console.log("Payload enviado:", payload);

            // Chamar o endpoint de finalização
            const response = await axios.post(
                '/api/game/finish',
                payload,
                {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                }
            );

            console.log("Resposta completa:", response);
            logDebugInfo(`Resposta do endpoint de finalização:`, response.data);

            // Ações específicas dependendo da opção escolhida
            switch (option) {
                case 'dashboard':
                    navigate('/dashboard');
                    break;

                case 'retry':
                    setSessionComplete(false);
                    setFeedback(null);
                    startGame(difficulty);
                    break;

                case 'next':
                    handleNextGame();
                    break;

                default:
                    // Marcar jogo como concluído e mostrar tela de conclusão
                    setSessionComplete(true);
                    // Calcular pontuação parcial se não tiver pontuação final
                    if (!finalScore) {
                        setFinalScore(calculatePartialScore());
                    }
                    // Definir feedback se não houver
                    if (!feedback) {
                        setFeedback({
                            praise: "Você completou parte do jogo!",
                            encouragement: "Praticar regularmente é importante para o progresso."
                        });
                    }
                    break;
            }
        } catch (err) {
            console.error('Erro ao finalizar jogo:', err);
            setError('Falha ao finalizar o jogo corretamente.');
            logDebugInfo(`ERRO ao finalizar jogo`, {
                error: err.message,
                stack: err.stack
            });
        } finally {
            setIsLoading(false);
        }
    };

    const calculatePartialScore = () => {
        if (!sessionId) return 0;

        // Se não tivermos dados suficientes, retornamos uma pontuação padrão
        if (!feedback) return 50;

        // Calcula com base nos exercícios atuais completados
        const exercisesCompleted = currentExercise ? currentExercise.index : 0;
        const totalExercises = currentExercise ? currentExercise.total : 1;
        const completionPercentage = (exercisesCompleted / totalExercises) * 100;

        // Penaliza um pouco por não completar todo o jogo
        return Math.max(30, completionPercentage * 0.8);
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
                    <h2>{finalScore >= completionThreshold ? "Parabéns! 🎉" : "Bom Trabalho!"}</h2>
                    <div className="final-score-container">
                        <div className={`final-score-circle ${finalScore >= completionThreshold ? "passed" : "retry"}`}>
                            <span>{Math.round(finalScore)}%</span>
                        </div>
                        {finalScore < completionThreshold && (
                            <p className="threshold-message">
                                Você precisa de {completionThreshold}% para avançar neste nível.
                            </p>
                        )}
                    </div>
                    <div className="feedback">
                        <p className="praise">{feedback?.praise}</p>
                        <p className="encouragement">{feedback?.encouragement}</p>
                    </div>
                    <div className="game-complete-buttons">
                        {/* Botões simplificados com ações diretas */}
                        <button
                            className="secondary-button"
                            onClick={() => handleFinishGame('retry')}
                            disabled={isLoading}
                        >
                            Jogar Novamente
                        </button>
                        <button
                            className="primary-button"
                            onClick={() => handleFinishGame('next')}
                            disabled={isLoading}
                        >
                            Próximo Jogo
                        </button>
                        <button
                            className="outline-button"
                            onClick={() => handleFinishGame('dashboard')}
                            disabled={isLoading}
                        >
                            Voltar ao Início
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

                    {!showInstructions && !sessionComplete && (
                        <button
                            className="finish-game-button"
                            onClick={() => handleFinishGame('finish')}
                            disabled={isLoading}
                        >
                            Finalizar Jogo
                        </button>
                    )}
                </>
            )}
        </div>
    );
};

export default GameScreen;