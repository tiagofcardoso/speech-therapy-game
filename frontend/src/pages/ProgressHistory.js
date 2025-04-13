import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import './ProgressHistory.css';

const ProgressHistory = () => {
    const [historyData, setHistoryData] = useState({
        sessions: [],
        statistics: {
            total_sessions: 0,
            total_exercises_completed: 0,
            average_score: 0,
            sessions_by_difficulty: {
                iniciante: 0,
                médio: 0,
                avançado: 0
            }
        }
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                setLoading(true);
                const response = await api.get('/api/user/history');
                setHistoryData(response.data);
                setLoading(false);
            } catch (err) {
                console.error('Erro ao buscar histórico:', err);
                setError('Não foi possível carregar seu histórico de progresso.');
                setLoading(false);
            }
        };

        fetchHistory();
    }, []);

    const formatDate = (dateString) => {
        if (!dateString) return "Data desconhecida";

        const date = new Date(dateString);
        return date.toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getDifficultyColor = (difficulty) => {
        switch (difficulty) {
            case 'iniciante':
                return '#4CAF50';
            case 'médio':
                return '#FFC107';
            case 'avançado':
                return '#F44336';
            default:
                return '#9E9E9E';
        }
    };

    const getDifficultyLabel = (difficulty) => {
        switch (difficulty) {
            case 'iniciante':
                return 'Iniciante';
            case 'médio':
                return 'Médio';
            case 'avançado':
                return 'Avançado';
            default:
                return 'Desconhecido';
        }
    };

    if (loading) {
        return (
            <div className="progress-history-container">
                <div className="loading-indicator">Carregando histórico...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="progress-history-container">
                <div className="error-message">{error}</div>
                <Link to="/dashboard" className="back-button">Voltar para o Dashboard</Link>
            </div>
        );
    }

    return (
        <div className="progress-history-container">
            <header className="history-header">
                <h1>Seu Histórico de Progresso</h1>
                <Link to="/dashboard" className="back-button">Voltar para o Dashboard</Link>
            </header>

            <section className="summary-section">
                <h2>Resumo</h2>
                <div className="summary-cards">
                    <div className="summary-card">
                        <div className="summary-icon">🎮</div>
                        <div className="summary-value">{historyData.statistics.total_sessions}</div>
                        <div className="summary-label">Sessões Completadas</div>
                    </div>
                    <div className="summary-card">
                        <div className="summary-icon">✅</div>
                        <div className="summary-value">{historyData.statistics.total_exercises_completed}</div>
                        <div className="summary-label">Exercícios Feitos</div>
                    </div>
                    <div className="summary-card">
                        <div className="summary-icon">📊</div>
                        <div className="summary-value">{historyData.statistics.average_score}%</div>
                        <div className="summary-label">Pontuação Média</div>
                    </div>
                </div>

                <div className="difficulty-distribution">
                    <h3>Distribuição por Dificuldade</h3>
                    <div className="difficulty-bars">
                        <div className="difficulty-bar">
                            <div className="difficulty-label">Iniciante</div>
                            <div className="bar-container">
                                <div
                                    className="bar"
                                    style={{
                                        width: `${(historyData.statistics.sessions_by_difficulty.iniciante / Math.max(1, historyData.statistics.total_sessions)) * 100}%`,
                                        backgroundColor: getDifficultyColor('iniciante')
                                    }}
                                ></div>
                            </div>
                            <div className="difficulty-count">{historyData.statistics.sessions_by_difficulty.iniciante}</div>
                        </div>
                        <div className="difficulty-bar">
                            <div className="difficulty-label">Médio</div>
                            <div className="bar-container">
                                <div
                                    className="bar"
                                    style={{
                                        width: `${(historyData.statistics.sessions_by_difficulty.médio / Math.max(1, historyData.statistics.total_sessions)) * 100}%`,
                                        backgroundColor: getDifficultyColor('médio')
                                    }}
                                ></div>
                            </div>
                            <div className="difficulty-count">{historyData.statistics.sessions_by_difficulty.médio}</div>
                        </div>
                        <div className="difficulty-bar">
                            <div className="difficulty-label">Avançado</div>
                            <div className="bar-container">
                                <div
                                    className="bar"
                                    style={{
                                        width: `${(historyData.statistics.sessions_by_difficulty.avançado / Math.max(1, historyData.statistics.total_sessions)) * 100}%`,
                                        backgroundColor: getDifficultyColor('avançado')
                                    }}
                                ></div>
                            </div>
                            <div className="difficulty-count">{historyData.statistics.sessions_by_difficulty.avançado}</div>
                        </div>
                    </div>
                </div>
            </section>

            <section className="history-section">
                <h2>Histórico de Sessões</h2>
                {historyData.sessions.length === 0 ? (
                    <div className="no-history-message">
                        <p>Você ainda não completou nenhuma sessão de exercícios.</p>
                        <p>Volte para o dashboard e comece a praticar!</p>
                    </div>
                ) : (
                    <div className="sessions-list">
                        {historyData.sessions.map((session, index) => (
                            <div className="session-card" key={index}>
                                <div className="session-header">
                                    <h3>{session.game_title || "Sessão de Exercícios"}</h3>
                                    <span
                                        className="difficulty-badge"
                                        style={{ backgroundColor: getDifficultyColor(session.difficulty) }}
                                    >
                                        {getDifficultyLabel(session.difficulty)}
                                    </span>
                                </div>
                                <div className="session-details">
                                    <div className="session-detail">
                                        <span className="detail-label">Data:</span>
                                        <span className="detail-value">{formatDate(session.completed_at)}</span>
                                    </div>
                                    <div className="session-detail">
                                        <span className="detail-label">Pontuação:</span>
                                        <span className="detail-value">{session.score}%</span>
                                    </div>
                                    <div className="session-detail">
                                        <span className="detail-label">Exercícios Completados:</span>
                                        <span className="detail-value">{session.exercises_completed}</span>
                                    </div>
                                </div>
                                <div
                                    className="session-score-indicator"
                                    style={{ width: `${session.score}%`, backgroundColor: getDifficultyColor(session.difficulty) }}
                                ></div>
                            </div>
                        ))}
                    </div>
                )}
            </section>

            <div className="navigation-buttons">
                <Link to="/statistics" className="nav-button">Ver Estatísticas Detalhadas</Link>
                <Link to="/achievements" className="nav-button">Ver Conquistas</Link>
            </div>
        </div>
    );
};

export default ProgressHistory;