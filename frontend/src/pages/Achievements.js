import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import './Achievements.css';

const Achievements = () => {
    const [achievementsData, setAchievementsData] = useState({
        earned_achievements: [],
        in_progress_achievements: [],
        total_achievements: 0
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchAchievements = async () => {
            try {
                setLoading(true);
                const response = await api.get('/api/user/achievements');
                setAchievementsData(response.data);
                setLoading(false);
            } catch (err) {
                console.error('Erro ao buscar conquistas:', err);
                setError('Não foi possível carregar suas conquistas.');
                setLoading(false);
            }
        };

        fetchAchievements();
    }, []);

    const formatDate = (dateString) => {
        if (!dateString) return "Data desconhecida";

        const date = new Date(dateString);
        return date.toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    };

    if (loading) {
        return (
            <div className="achievements-container">
                <div className="loading-indicator">Carregando conquistas...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="achievements-container">
                <div className="error-message">{error}</div>
                <Link to="/dashboard" className="back-button">Voltar para o Dashboard</Link>
            </div>
        );
    }

    return (
        <div className="achievements-container">
            <header className="achievements-header">
                <h1>Suas Conquistas</h1>
                <Link to="/dashboard" className="back-button">Voltar para o Dashboard</Link>
            </header>

            <div className="achievements-summary">
                <div className="achievement-counter">
                    <div className="counter-value">{achievementsData.earned_achievements.length}</div>
                    <div className="counter-label">de {achievementsData.total_achievements} conquistas desbloqueadas</div>
                </div>
                <div className="achievement-progress-bar">
                    <div
                        className="progress-fill"
                        style={{ width: `${(achievementsData.earned_achievements.length / Math.max(1, achievementsData.total_achievements)) * 100}%` }}
                    ></div>
                </div>
            </div>

            <section className="earned-achievements">
                <h2>Conquistas Desbloqueadas</h2>
                {achievementsData.earned_achievements.length === 0 ? (
                    <div className="no-achievements-message">
                        <p>Você ainda não desbloqueou nenhuma conquista.</p>
                        <p>Continue praticando para ganhar sua primeira conquista!</p>
                    </div>
                ) : (
                    <div className="achievements-grid">
                        {achievementsData.earned_achievements.map((achievement, index) => (
                            <div className="achievement-card earned" key={index}>
                                <div className="achievement-icon">{achievement.icon}</div>
                                <div className="achievement-content">
                                    <h3>{achievement.title}</h3>
                                    <p>{achievement.description}</p>
                                    <div className="achievement-earned-date">
                                        Conquistado em {formatDate(achievement.earned_at)}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </section>

            <section className="in-progress-achievements">
                <h2>Próximas Conquistas</h2>
                {achievementsData.in_progress_achievements.length === 0 ? (
                    <div className="no-achievements-message">
                        <p>Não há mais conquistas para desbloquear.</p>
                        <p>Parabéns por completar todas as conquistas disponíveis!</p>
                    </div>
                ) : (
                    <div className="achievements-grid">
                        {achievementsData.in_progress_achievements.map((achievement, index) => (
                            <div className="achievement-card in-progress" key={index}>
                                <div className="achievement-icon faded">{achievement.icon}</div>
                                <div className="achievement-content">
                                    <h3>{achievement.title}</h3>
                                    <p>{achievement.description}</p>
                                    <div className="achievement-progress">
                                        <div className="progress-bar">
                                            <div
                                                className="progress-fill"
                                                style={{ width: `${achievement.percentage}%` }}
                                            ></div>
                                        </div>
                                        <div className="progress-text">
                                            {achievement.progress} de {achievement.total} ({achievement.percentage}%)
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </section>

            <div className="navigation-buttons">
                <Link to="/history" className="nav-button">Ver Histórico de Progresso</Link>
                <Link to="/statistics" className="nav-button">Ver Estatísticas Detalhadas</Link>
            </div>
        </div>
    );
};

export default Achievements;