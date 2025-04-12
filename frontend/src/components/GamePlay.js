import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import './GamePlay.css';

const GamePlay = () => {
    const { gameId } = useParams();
    const navigate = useNavigate();
    const [game, setGame] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [currentExerciseIndex, setCurrentExerciseIndex] = useState(0);
    const [userAnswer, setUserAnswer] = useState('');
    const [feedback, setFeedback] = useState(null);
    const [score, setScore] = useState(0);
    const [gameComplete, setGameComplete] = useState(false);

    useEffect(() => {
        // Fetch game data when component mounts
        const fetchGame = async () => {
            try {
                setLoading(true);
                const response = await api.get(`/api/games/${gameId}`);
                if (response.data.success) {
                    console.log("Game data received:", response.data.game);
                    setGame(response.data.game);
                } else {
                    setError("Não foi possível carregar o jogo");
                }
            } catch (err) {
                console.error("Error fetching game:", err);
                setError("Erro ao carregar o jogo: " + (err.response?.data?.message || err.message));
            } finally {
                setLoading(false);
            }
        };

        fetchGame();
    }, [gameId]);

    const handleAnswerSubmit = async (e) => {
        e.preventDefault();

        if (!userAnswer.trim()) return;

        try {
            // In a real app, you'd send this to the backend for evaluation
            // For now, we'll just simulate feedback

            // Simple placeholder evaluation logic
            const currentExercise = getCurrentExercise();
            const isCorrect = Math.random() > 0.3; // 70% chance of being "correct"

            setFeedback({
                correct: isCorrect,
                message: isCorrect
                    ? "Muito bem! Sua resposta está correta."
                    : "Tente novamente. Preste atenção na pronúncia."
            });

            if (isCorrect) {
                setScore(prev => prev + 10);
            }

            // Clear answer after feedback
            setUserAnswer('');

        } catch (err) {
            setError("Erro ao avaliar resposta: " + err.message);
        }
    };

    const moveToNextExercise = () => {
        if (currentExerciseIndex < (game.content?.length || 0) - 1) {
            setCurrentExerciseIndex(prev => prev + 1);
            setFeedback(null);
        } else {
            // Game complete
            setGameComplete(true);
        }
    };

    const getCurrentExercise = () => {
        if (!game || !game.content || game.content.length === 0) return null;
        return game.content[currentExerciseIndex];
    };

    const returnToDashboard = () => {
        navigate('/dashboard');
    };

    if (loading) {
        return (
            <div className="game-play-loading">
                <div className="game-play-spinner"></div>
                <p>Carregando jogo...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="game-play-error">
                <h3>Houve um problema</h3>
                <p>{error}</p>
                <button onClick={returnToDashboard}>Voltar ao Início</button>
            </div>
        );
    }

    if (gameComplete) {
        return (
            <div className="game-play-complete">
                <div className="game-complete-header">
                    <span className="game-complete-emoji">🎉</span>
                    <h2>Parabéns!</h2>
                </div>

                <p>Você completou o jogo "{game.title}" com sucesso!</p>

                <div className="game-score">
                    <h3>Sua pontuação: {score}</h3>
                    <div className="score-bar">
                        <div
                            className="score-fill"
                            style={{ width: `${Math.min(100, (score / ((game.content?.length || 1) * 10)) * 100)}%` }}
                        ></div>
                    </div>
                </div>

                <div className="game-complete-actions">
                    <button onClick={returnToDashboard}>Voltar ao Início</button>
                    <button
                        onClick={() => {
                            setCurrentExerciseIndex(0);
                            setScore(0);
                            setGameComplete(false);
                            setFeedback(null);
                        }}
                        className="play-again-button"
                    >
                        Jogar Novamente
                    </button>
                </div>
            </div>
        );
    }

    const currentExercise = getCurrentExercise();
    if (!currentExercise) {
        return (
            <div className="game-play-error">
                <h3>Houve um problema</h3>
                <p>Não foi possível carregar os exercícios do jogo.</p>
                <button onClick={returnToDashboard}>Voltar ao Início</button>
            </div>
        );
    }

    return (
        <div className="game-play-container">
            <div className="game-play-header">
                <h2>{game.title}</h2>
                <div className="game-progress">
                    <span>Exercício {currentExerciseIndex + 1} de {game.content?.length || 0}</span>
                    <div className="progress-bar">
                        <div
                            className="progress-fill"
                            style={{ width: `${((currentExerciseIndex + 1) / (game.content?.length || 1)) * 100}%` }}
                        ></div>
                    </div>
                </div>
            </div>

            <div className="exercise-container">
                <h3>{currentExercise.word || "Exercício de pronúncia"}</h3>

                <div className="exercise-details">
                    <p className="exercise-description">{currentExercise.prompt || currentExercise.description || "Pronuncie a palavra corretamente"}</p>

                    {currentExercise.hint && (
                        <div className="hint-box">
                            <span className="hint-label">Dica:</span>
                            <span className="hint-text">{currentExercise.hint}</span>
                        </div>
                    )}

                    <div className="word-display">
                        <h2 className="highlight-word">{currentExercise.word}</h2>
                    </div>

                    <div className="activity-instructions">
                        <h4>Atividade:</h4>
                        <p>{currentExercise.activity || "Diga esta palavra em voz alta, prestando atenção na pronúncia."}</p>
                    </div>
                </div>

                {feedback ? (
                    <div className={`feedback-container ${feedback.correct ? 'correct' : 'incorrect'}`}>
                        <p>{feedback.message}</p>
                        <button
                            onClick={moveToNextExercise}
                            className="next-exercise-button"
                        >
                            {currentExerciseIndex < (game.content?.length || 0) - 1 ? 'Próximo Exercício' : 'Finalizar Jogo'}
                        </button>
                    </div>
                ) : (
                    <form onSubmit={handleAnswerSubmit} className="answer-form">
                        <div className="input-group">
                            <label htmlFor="userAnswer">Sua resposta:</label>
                            <input
                                type="text"
                                id="userAnswer"
                                value={userAnswer}
                                onChange={(e) => setUserAnswer(e.target.value)}
                                placeholder="Digite ou fale sua resposta..."
                            />
                        </div>
                        <button type="submit" className="submit-answer">
                            Enviar Resposta
                        </button>
                    </form>
                )}
            </div>

            <div className="game-play-footer">
                <button onClick={returnToDashboard} className="exit-button">
                    Sair do Jogo
                </button>
                <div className="score-display">
                    <span>Pontuação:</span>
                    <span className="score-value">{score}</span>
                </div>
            </div>
        </div>
    );
};

export default GamePlay;