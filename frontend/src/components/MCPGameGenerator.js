import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useNavigate } from 'react-router-dom';
import './MCPGameGenerator.css';

const MCPGameGenerator = () => {
    const [loading, setLoading] = useState(false);
    const [analyzing, setAnalyzing] = useState(false);
    const [error, setError] = useState(null);
    const [userProfile, setUserProfile] = useState(null);
    const [progressData, setProgressData] = useState(null);
    const [focusAreas, setFocusAreas] = useState([]);
    const navigate = useNavigate();

    // Fetch user profile and progress data when component mounts
    useEffect(() => {
        const fetchUserData = async () => {
            setAnalyzing(true);
            try {
                const profileResponse = await api.get('/api/user/profile');
                setUserProfile(profileResponse.data);

                const progressResponse = await api.get('/api/user/progress');
                setProgressData(progressResponse.data);

                // Extract focus areas from progress data
                if (progressResponse.data && progressResponse.data.areas) {
                    const sorted = [...progressResponse.data.areas].sort((a, b) => a.score - b.score);
                    setFocusAreas(sorted.slice(0, 3)); // Top 3 areas needing improvement
                }
            } catch (err) {
                console.error("Failed to fetch user data:", err);
                setError("Não foi possível carregar os dados do usuário.");
            } finally {
                setAnalyzing(false);
            }
        };

        fetchUserData();
    }, []);

    // Create a new game session using MCP
    const createMCPGameSession = async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await api.post('/api/mcp/create-session', {
                user_profile: userProfile,
                focus_areas: focusAreas.map(area => area.name)
            });

            if (response.data.success) {
                // Navigate to the session page
                navigate(`/session/${response.data.session.session_id}`);
            } else {
                setError(response.data.message || "Falha ao criar sessão de jogo.");
            }
        } catch (err) {
            setError(err.response?.data?.message || err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="mcp-game-generator">
            <h2>Assistente de Terapia Inteligente</h2>
            <p className="mcp-description">
                O Sistema de Controle Principal (MCP) irá analisar seu progresso e
                gerar jogos personalizados focados nas áreas que precisam de mais atenção.
            </p>

            {analyzing ? (
                <div className="analyzing-progress">
                    <div className="spinner"></div>
                    <p>Analisando seu progresso...</p>
                </div>
            ) : (
                <>
                    {progressData && (
                        <div className="progress-summary">
                            <h3>Resumo do Progresso</h3>
                            <div className="progress-metrics">
                                <div className="metric">
                                    <span>Sessões Completadas</span>
                                    <strong>{progressData.completedSessions || 0}</strong>
                                </div>
                                <div className="metric">
                                    <span>Taxa de Acertos</span>
                                    <strong>{progressData.accuracyRate || 0}%</strong>
                                </div>
                                <div className="metric">
                                    <span>Nível Atual</span>
                                    <strong>{progressData.currentLevel || 'Iniciante'}</strong>
                                </div>
                            </div>

                            {focusAreas.length > 0 && (
                                <div className="focus-areas">
                                    <h4>Áreas que Precisam de Atenção</h4>
                                    <ul>
                                        {focusAreas.map((area, index) => (
                                            <li key={index}>
                                                <strong>{area.name}</strong>
                                                <div className="progress-bar">
                                                    <div
                                                        className="progress-fill"
                                                        style={{ width: `${area.score}%` }}
                                                    ></div>
                                                </div>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    )}

                    <button
                        onClick={createMCPGameSession}
                        disabled={loading || !progressData}
                        className="create-session-btn"
                    >
                        {loading ? 'Criando Sessão...' : 'Criar Sessão Personalizada'}
                    </button>

                    {error && <div className="error-message">{error}</div>}
                </>
            )}

            <div className="mcp-info">
                <h3>Como Funciona o MCP?</h3>
                <p>
                    O Sistema de Controle Principal analisa seu histórico de exercícios,
                    identifica padrões de dificuldade e cria jogos específicos para
                    ajudar no seu desenvolvimento. Quanto mais você pratica, mais
                    personalizada será a experiência!
                </p>
            </div>
        </div>
    );
};

export default MCPGameGenerator;