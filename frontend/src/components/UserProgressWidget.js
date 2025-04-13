import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ProgressBar } from 'react-bootstrap';
import { FaTrophy, FaGamepad, FaHistory, FaStar, FaArrowUp, FaChartLine, FaSyncAlt } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import './UserProgressWidget.css';

const UserProgressWidget = () => {
    const [progress, setProgress] = useState(null);
    const [userStats, setUserStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    // Adicionar uma função de atualização periódica
    useEffect(() => {
        // Função para buscar os dados
        const fetchData = async () => {
            try {
                setLoading(true);
                const token = localStorage.getItem('token');

                // Fazer ambas as requisições em paralelo
                const [progressResponse, statsResponse] = await Promise.all([
                    axios.get('/api/user/current_progress', {
                        headers: { 'Authorization': `Bearer ${token}` }
                    }),
                    axios.get('/api/user/statistics', {
                        headers: { 'Authorization': `Bearer ${token}` }
                    })
                ]);

                setProgress(progressResponse.data);
                setUserStats(statsResponse.data);
                setLoading(false);
            } catch (err) {
                console.error('Error fetching user data:', err);
                setError('Falha ao carregar suas informações de progresso');
                setLoading(false);
            }
        };

        // Buscar dados imediatamente
        fetchData();

        // Configurar a atualização automática a cada 30 segundos
        const intervalId = setInterval(fetchData, 30000);

        // Limpar o intervalo quando o componente for desmontado
        return () => clearInterval(intervalId);
    }, []);

    // Adicionar um método de atualização manual
    const refreshData = () => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const token = localStorage.getItem('token');

                // Fazer ambas as requisições em paralelo
                const [progressResponse, statsResponse] = await Promise.all([
                    axios.get('/api/user/current_progress', {
                        headers: { 'Authorization': `Bearer ${token}` }
                    }),
                    axios.get('/api/user/statistics', {
                        headers: { 'Authorization': `Bearer ${token}` }
                    })
                ]);

                setProgress(progressResponse.data);
                setUserStats(statsResponse.data);
                setLoading(false);
            } catch (err) {
                console.error('Error fetching user data:', err);
                setError('Falha ao carregar suas informações de progresso');
                setLoading(false);
            }
        };

        fetchData();
    };

    const handleStartNewGame = () => {
        navigate('/game');
    };

    const handleContinueGame = () => {
        if (progress?.game_id) {
            navigate(`/game/${progress.game_id}`);
        }
    };

    if (loading) {
        return <div className="progress-widget-loading">Carregando seu progresso...</div>;
    }

    if (error) {
        return <div className="progress-widget-error">{error}</div>;
    }

    return (
        <div className="user-progress-widget">
            <div className="progress-header-main">
                <h3>Seu Progresso</h3>
                <div className="header-actions">
                    <FaChartLine className="progress-icon-main" />
                    <button className="refresh-button" onClick={refreshData} disabled={loading}>
                        <FaSyncAlt className={loading ? 'spinning' : ''} />
                    </button>
                </div>
            </div>

            {/* Resumo das estatísticas */}
            <div className="stats-summary">
                <div className="stat-item">
                    <span className="stat-value">{userStats?.exercises_completed || 0}</span>
                    <span className="stat-label">Exercícios Completados</span>
                </div>
                <div className="stat-item">
                    <span className="stat-value">{userStats?.accuracy ? `${Math.round(userStats.accuracy)}%` : '0%'}</span>
                    <span className="stat-label">Precisão Média</span>
                </div>
                <div className="stat-item">
                    <span className="stat-value">{userStats?.current_level || 'Iniciante'}</span>
                    <span className="stat-label">Seu Nível</span>
                </div>
            </div>

            {/* Jogo atual ou último jogo */}
            {progress?.has_active_game ? (
                <div className="active-game-progress">
                    <div className="progress-header">
                        <FaGamepad className="progress-icon" />
                        <h4>Jogo em Andamento</h4>
                    </div>

                    <div className="game-details">
                        <p className="game-type">{progress.game_type}</p>
                        <p className="difficulty-label">
                            Nível: <span className={`difficulty ${progress.difficulty}`}>
                                {progress.difficulty}
                            </span>
                        </p>
                    </div>

                    <div className="score-display">
                        <FaTrophy className="score-icon" />
                        <span className="score">{progress.current_score}</span>
                    </div>

                    <div className="progress-bar-container">
                        <label>Progresso: {progress.progress.current_exercise} de {progress.progress.total_exercises}</label>
                        <ProgressBar
                            now={progress.progress.completion_percentage}
                            label={`${Math.round(progress.progress.completion_percentage)}%`}
                            variant="success"
                        />
                    </div>

                    <button className="continue-button" onClick={handleContinueGame}>
                        Continuar Jogo
                    </button>
                </div>
            ) : (
                <div className="no-active-game">
                    {progress?.last_activity ? (
                        <div className="last-activity">
                            <div className="progress-header">
                                <FaHistory className="progress-icon" />
                                <h4>Última Atividade</h4>
                            </div>

                            <p className="game-type">{progress.last_activity.game_type}</p>
                            <p className="score-label">
                                Pontuação: <span className="score">{Math.round(progress.last_activity.score)}</span>
                            </p>
                            <p className="completed-label">
                                Exercícios concluídos: {progress.last_activity.exercises_completed}
                            </p>

                            <button className="new-game-button" onClick={handleStartNewGame}>
                                Iniciar Novo Jogo
                            </button>
                        </div>
                    ) : (
                        <div className="no-progress">
                            <p>Comece seu primeiro jogo para ver seu progresso!</p>
                            <button className="start-game-button" onClick={handleStartNewGame}>
                                Iniciar Jogo
                            </button>
                        </div>
                    )}
                </div>
            )}

            {/* Nível atual e progresso para o próximo */}
            {userStats && (
                <div className="level-progress">
                    <h4>Progresso para Próximo Nível</h4>
                    <div className="level-indicator">
                        <span className="current-level">{userStats.current_level}</span>
                        <FaArrowUp className="level-arrow" />
                        <span className="next-level">{userStats.next_level}</span>
                    </div>
                    <ProgressBar
                        now={userStats.level_progress_percentage}
                        label={`${Math.round(userStats.level_progress_percentage)}%`}
                        variant="info"
                    />
                    <p className="level-message">
                        {userStats.level_progress_message || `Continue praticando para avançar para ${userStats.next_level}!`}
                    </p>
                </div>
            )}
        </div>
    );
};

export default UserProgressWidget;