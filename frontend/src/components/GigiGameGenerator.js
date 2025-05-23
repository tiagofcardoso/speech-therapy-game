import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useNavigate } from 'react-router-dom';
import './GigiGameGenerator.css';

const GigiGameGenerator = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [gameType, setGameType] = useState('');
    const [difficulty, setDifficulty] = useState('');
    const [showOptions, setShowOptions] = useState(false);
    const [generatedGame, setGeneratedGame] = useState(null);
    const [apiChecked, setApiChecked] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) {
            // Redirect to login if no token exists
            navigate('/login');
        }

        // Check if API is available on component mount
        checkApiConnection();
    }, [navigate]);

    // New function to check API connection
    const checkApiConnection = async () => {
        try {
            await api.get('/api/health');
            setApiChecked(true);
        } catch (err) {
            console.log("API connection check failed:", err);
            setError("Servidor indisponível. Por favor, tente novamente mais tarde.");
            setApiChecked(false);
        }
    };

    const generateGame = async () => {
        try {
            setLoading(true);
            setError(null);
            console.log("Iniciando geração de jogo");

            // Create the request payload
            const requestData = {
                difficulty: difficulty,
                game_type: gameType || "exercícios de pronúncia",
            };

            console.log("Token presente:", !!localStorage.getItem('token'));

            // Use the enhanced postWithRetry method for more resilience
            const response = await api.postWithRetry(
                '/api/gigi/generate-game',
                requestData,
                {
                    headers: { 'Content-Type': 'application/json' },
                },
                // 2 retries in addition to initial attempt
                2
            );

            console.log("Game generated successfully:", response.data);

            if (response.data.success && response.data.game) {
                setGeneratedGame(response.data.game);
            } else {
                setError("O jogo foi gerado mas houve um problema com os dados retornados.");
            }
        } catch (err) {
            console.error("Game generation error:", err);

            const errorMessage = err.response?.data?.message ||
                (err.message.includes('timeout')
                    ? "A geração do jogo está demorando mais do que o esperado. Por favor, tente novamente em alguns instantes."
                    : "Erro ao gerar o jogo. Por favor, tente novamente.");

            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    const startGame = () => {
        if (generatedGame && generatedGame.game_id) {
            navigate(`/play/${generatedGame.game_id}`);
        }
    };

    return (
        <div className="gigi-game-generator">
            <div className="gigi-header">
                <div className="gigi-avatar">
                    <span className="gigi-emoji">🧞‍♀️</span>
                </div>
                <div className="gigi-title">
                    <h2>Gigi, o Gênio dos Jogos</h2>
                    <p className="gigi-subtitle">Sua companheira de terapia da fala inteligente</p>
                </div>
            </div>

            <div className="gigi-intro">
                <p>
                    Olá! Eu sou Gigi, sua assistente de terapia da fala!
                    Posso criar jogos personalizados para ajudar no seu desenvolvimento da fala.
                    O que você gostaria de praticar hoje?
                </p>
            </div>

            <div className="gigi-request-section">
                {!showOptions ? (
                    <div className="gigi-quick-options">
                        <button
                            className="gigi-quick-button surprise"
                            onClick={() => {
                                setGameType('');
                                setDifficulty('');
                                generateGame();
                            }}
                            disabled={loading}
                        >
                            <span className="option-icon">✨</span>
                            Surpreenda-me!
                        </button>
                        <button
                            className="gigi-quick-button customize"
                            onClick={() => setShowOptions(true)}
                            disabled={loading}
                        >
                            <span className="option-icon">🎮</span>
                            Personalizar jogo
                        </button>
                    </div>
                ) : (
                    <div className="gigi-custom-options">
                        <h3>Personalize seu jogo</h3>

                        <div className="option-group">
                            <label>Tipo de Jogo</label>
                            <select
                                value={gameType}
                                onChange={(e) => setGameType(e.target.value)}
                                disabled={loading}
                                className="gigi-select"
                            >
                                <option value="">Automático (baseado no seu progresso)</option>
                                <option value="articulation">Articulação</option>
                                <option value="vocabulary">Vocabulário e Linguagem</option>
                                <option value="fluency">Fluência</option>
                                <option value="pragmatic">Linguagem Pragmática</option>
                                <option value="diphthongs">Ditongos</option>
                                <option value="triphthongs">Tritongos</option>
                                <option value="stress">Sílaba Tónica</option>
                                <option value="syllables">Separação de Sílabas</option>
                            </select>
                        </div>

                        <div className="option-group">
                            <label>Nível de Dificuldade</label>
                            <select
                                value={difficulty}
                                onChange={(e) => setDifficulty(e.target.value)}
                                disabled={loading}
                                className="gigi-select"
                            >
                                <option value="">Automático (baseado no seu progresso)</option>
                                <option value="beginner">Iniciante</option>
                                <option value="intermediate">Intermediário</option>
                                <option value="advanced">Avançado</option>
                            </select>
                        </div>

                        <div className="gigi-actions">
                            <button
                                className="gigi-back-button"
                                onClick={() => setShowOptions(false)}
                                disabled={loading}
                            >
                                Voltar
                            </button>
                            <button
                                className="gigi-generate-button"
                                onClick={generateGame}
                                disabled={loading}
                            >
                                {loading ? 'Criando jogo...' : 'Criar Jogo'}
                            </button>
                        </div>
                    </div>
                )}

                {loading && (
                    <div className="gigi-loading">
                        <div className="gigi-spinner"></div>
                        <p>Gigi está criando um jogo especial para você...</p>
                    </div>
                )}

                {error && (
                    <div className="gigi-error">
                        <p>Oops! Gigi encontrou um problema: {error}</p>
                        <button
                            className="gigi-retry-button"
                            onClick={generateGame}
                        >
                            Tentar Novamente
                        </button>
                    </div>
                )}

                {!apiChecked && !loading && (
                    <div className="gigi-api-warning">
                        <p>O servidor parece estar indisponível. Alguns recursos podem não funcionar corretamente.</p>
                        <button
                            className="gigi-retry-button"
                            onClick={checkApiConnection}
                        >
                            Verificar conexão
                        </button>
                    </div>
                )}
            </div>

            {generatedGame && (
                <div id="generated-game" className="gigi-game-result">
                    <h3 className="game-title">{generatedGame.title}</h3>

                    <div className="game-metadata">
                        <span className="game-badge type">
                            {generatedGame.game_type === 'articulation' ? 'Articulação' :
                                generatedGame.game_type === 'vocabulary' ? 'Vocabulário' :
                                    generatedGame.game_type === 'fluency' ? 'Fluência' :
                                        generatedGame.game_type === 'pragmatic' ? 'Linguagem Pragmática' :
                                            generatedGame.game_type === 'diphthongs' ? 'Ditongos' :
                                                generatedGame.game_type === 'triphthongs' ? 'Tritongos' :
                                                    generatedGame.game_type === 'stress' ? 'Sílaba Tónica' :
                                                        generatedGame.game_type === 'syllables' ? 'Separação de Sílabas' :
                                                            'Outros'}
                        </span>
                        <span className="game-badge difficulty">
                            {generatedGame.difficulty === 'beginner' ? 'Iniciante' :
                                generatedGame.difficulty === 'intermediate' ? 'Intermediário' : 'Avançado'}
                        </span>
                        <span className="game-badge duration">
                            {generatedGame.metadata?.estimated_duration || '5-10 minutos'}
                        </span>
                    </div>

                    <p className="game-description">{generatedGame.description}</p>

                    <div className="game-instructions">
                        <h4>Instruções</h4>
                        <p>{generatedGame.instructions}</p>
                    </div>

                    <div className="game-exercises-preview">
                        <h4>Exercícios ({generatedGame.content?.length || 0})</h4>
                        <ul className="exercises-list">
                            {generatedGame.content?.map((exercise, index) => (
                                <li key={index} className="exercise-item">
                                    <span className="exercise-number">{index + 1}</span>
                                    <span className="exercise-title">{exercise.title}</span>
                                </li>
                            ))}
                        </ul>
                    </div>

                    <button
                        className="gigi-start-game-button"
                        onClick={startGame}
                    >
                        Iniciar Este Jogo
                    </button>
                </div>
            )}

            <div className="gigi-info">
                <h3>Como Funciona a Gigi?</h3>
                <p>
                    Gigi analisa seu progresso anterior para criar jogos personalizados
                    que atendam às suas necessidades específicas de terapia da fala.
                    Quanto mais você joga, mais inteligente Gigi se torna!
                </p>

                <div className="game-types-overview">
                    <div className="game-type-card articulation">
                        <h4>Articulação</h4>
                        <p>Jogos focados na pronúncia correta de sons do português brasileiro.</p>
                    </div>
                    <div className="game-type-card vocabulary">
                        <h4>Vocabulário</h4>
                        <p>Jogos para expandir o vocabulário e melhorar a expressão verbal.</p>
                    </div>
                    <div className="game-type-card fluency">
                        <h4>Fluência</h4>
                        <p>Jogos para desenvolver a fala fluente e natural.</p>
                    </div>
                    <div className="game-type-card pragmatic">
                        <h4>Pragmática</h4>
                        <p>Jogos para melhorar as habilidades de comunicação social.</p>
                    </div>
                    <div className="game-type-card diphthongs">
                        <h4>Ditongos</h4>
                        <p>Jogos para praticar a pronúncia correta de ditongos do português.</p>
                    </div>
                    <div className="game-type-card triphthongs">
                        <h4>Tritongos</h4>
                        <p>Exercícios focados na articulação de tritongos.</p>
                    </div>
                    <div className="game-type-card stress">
                        <h4>Sílaba Tónica</h4>
                        <p>Jogos para identificar e praticar a acentuação das palavras.</p>
                    </div>
                    <div className="game-type-card syllables">
                        <h4>Separação de Sílabas</h4>
                        <p>Atividades para desenvolver a consciência silábica.</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default GigiGameGenerator;