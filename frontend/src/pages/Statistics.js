import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Title, Tooltip, Legend } from 'chart.js';
import api from '../services/api';
import './Statistics.css';

// Registrando os componentes Chart.js necessários
ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Title,
    Tooltip,
    Legend
);

const Statistics = () => {
    const [statistics, setStatistics] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('progress');

    useEffect(() => {
        const fetchStatistics = async () => {
            try {
                setLoading(true);
                // Vamos buscar dados de várias endpoints para construir gráficos completos
                const [userStatsResponse, historyResponse, reportsResponse] = await Promise.all([
                    api.get('/api/user/statistics'),
                    api.get('/api/user/history'),
                    api.get('/api/user/reports')
                ]);

                // Consolidar todos os dados em um único objeto
                const consolidatedData = {
                    userStats: userStatsResponse.data,
                    history: historyResponse.data,
                    reports: reportsResponse.data
                };

                setStatistics(consolidatedData);
                setLoading(false);
            } catch (err) {
                console.error('Erro ao buscar estatísticas:', err);
                setError('Não foi possível carregar suas estatísticas.');
                setLoading(false);
            }
        };

        fetchStatistics();
    }, []);

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

    // Preparar dados para o gráfico de progresso ao longo do tempo
    const prepareProgressChartData = () => {
        if (!statistics || !statistics.history || !statistics.history.sessions) return null;

        const sessions = [...statistics.history.sessions].reverse(); // Inverte para ordem cronológica

        // Limitar a 15 sessões para melhor visualização
        const recentSessions = sessions.slice(0, 15);

        const labels = recentSessions.map((session, index) => `Sessão ${index + 1}`);
        const scores = recentSessions.map(session => session.score || 0);
        const difficulties = recentSessions.map(session => session.difficulty || 'iniciante');

        const data = {
            labels,
            datasets: [
                {
                    label: 'Pontuação (%)',
                    data: scores,
                    borderColor: '#3f51b5',
                    backgroundColor: scores.map((_, index) => getDifficultyColor(difficulties[index])),
                    tension: 0.3,
                    pointRadius: 5,
                    pointHoverRadius: 8,
                }
            ]
        };

        return data;
    };

    // Preparar dados para o gráfico de distribuição de dificuldade
    const prepareDifficultyChartData = () => {
        if (!statistics || !statistics.history || !statistics.history.statistics) return null;

        const difficultyStats = statistics.history.statistics.sessions_by_difficulty;

        const data = {
            labels: ['Iniciante', 'Médio', 'Avançado'],
            datasets: [
                {
                    data: [
                        difficultyStats.iniciante || 0,
                        difficultyStats.médio || 0,
                        difficultyStats.avançado || 0
                    ],
                    backgroundColor: [
                        getDifficultyColor('iniciante'),
                        getDifficultyColor('médio'),
                        getDifficultyColor('avançado')
                    ],
                    borderWidth: 1,
                },
            ],
        };

        return data;
    };

    // Preparar dados para o gráfico de precisão por palavra
    const prepareWordAccuracyChartData = () => {
        if (!statistics || !statistics.reports || !statistics.reports.word_accuracy) return null;

        const wordAccuracy = statistics.reports.word_accuracy;
        const words = Object.keys(wordAccuracy).slice(0, 10); // Limitar a 10 palavras

        const data = {
            labels: words,
            datasets: [
                {
                    label: 'Precisão (%)',
                    data: words.map(word => wordAccuracy[word].percentage || 0),
                    backgroundColor: '#2196F3',
                    borderColor: '#1976D2',
                    borderWidth: 1,
                },
            ],
        };

        return data;
    };

    if (loading) {
        return (
            <div className="statistics-container">
                <div className="loading-indicator">Carregando estatísticas...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="statistics-container">
                <div className="error-message">{error}</div>
                <Link to="/dashboard" className="back-button">Voltar para o Dashboard</Link>
            </div>
        );
    }

    const progressChartData = prepareProgressChartData();
    const difficultyChartData = prepareDifficultyChartData();
    const wordAccuracyChartData = prepareWordAccuracyChartData();

    const userStats = statistics?.userStats || {};
    const totalSessions = statistics?.history?.statistics?.total_sessions || 0;

    return (
        <div className="statistics-container">
            <header className="statistics-header">
                <h1>Estatísticas Detalhadas</h1>
                <Link to="/dashboard" className="back-button">Voltar para o Dashboard</Link>
            </header>

            <section className="user-level-section">
                <h2>Seu Nível Atual</h2>
                <div className="level-info">
                    <div className="level-badge">
                        {userStats.current_level === 'iniciante' ? '🌱' :
                            userStats.current_level === 'médio' ? '🌿' : '🌳'}
                    </div>
                    <div className="level-details">
                        <h3>{userStats.current_level === 'iniciante' ? 'Iniciante' :
                            userStats.current_level === 'médio' ? 'Médio' : 'Avançado'}</h3>
                        <p className="level-description">{userStats.level_progress_message}</p>

                        <div className="level-progress">
                            <div className="progress-bar">
                                <div
                                    className="progress-fill"
                                    style={{
                                        width: `${userStats.level_progress_percentage || 0}%`,
                                        backgroundColor: getDifficultyColor(userStats.current_level)
                                    }}
                                ></div>
                            </div>
                            <div className="progress-text">
                                {Math.round(userStats.level_progress_percentage || 0)}% para o nível {userStats.next_level}
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <section className="stat-cards">
                <div className="stat-card">
                    <div className="stat-icon">🎯</div>
                    <div className="stat-value">{userStats.accuracy || 0}%</div>
                    <div className="stat-label">Precisão Média</div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon">🎮</div>
                    <div className="stat-value">{totalSessions}</div>
                    <div className="stat-label">Total de Sessões</div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon">✅</div>
                    <div className="stat-value">{userStats.exercises_completed || 0}</div>
                    <div className="stat-label">Exercícios Completados</div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon">📅</div>
                    <div className="stat-value">{userStats.joined_days_ago || 0}</div>
                    <div className="stat-label">Dias desde Inscrição</div>
                </div>
            </section>

            <section className="chart-tabs">
                <div className="tab-buttons">
                    <button
                        className={`tab-button ${activeTab === 'progress' ? 'active' : ''}`}
                        onClick={() => setActiveTab('progress')}
                    >
                        Progresso ao Longo do Tempo
                    </button>
                    <button
                        className={`tab-button ${activeTab === 'difficulty' ? 'active' : ''}`}
                        onClick={() => setActiveTab('difficulty')}
                    >
                        Distribuição por Dificuldade
                    </button>
                    <button
                        className={`tab-button ${activeTab === 'words' ? 'active' : ''}`}
                        onClick={() => setActiveTab('words')}
                    >
                        Precisão por Palavra
                    </button>
                </div>

                <div className="chart-container">
                    {activeTab === 'progress' && progressChartData && (
                        <div className="chart">
                            <h3>Seu Progresso ao Longo do Tempo</h3>
                            <Line
                                data={progressChartData}
                                options={{
                                    responsive: true,
                                    plugins: {
                                        legend: {
                                            position: 'top',
                                        },
                                        title: {
                                            display: true,
                                            text: 'Pontuação das Sessões Recentes'
                                        },
                                        tooltip: {
                                            callbacks: {
                                                label: function (context) {
                                                    return `Pontuação: ${context.raw}%`;
                                                }
                                            }
                                        }
                                    },
                                    scales: {
                                        y: {
                                            min: 0,
                                            max: 100,
                                            ticks: {
                                                stepSize: 10
                                            }
                                        }
                                    }
                                }}
                            />
                            <p className="chart-explanation">
                                Este gráfico mostra a evolução da sua pontuação nas sessões mais recentes.
                                É possível ver como você tem progredido ao longo do tempo.
                            </p>
                        </div>
                    )}

                    {activeTab === 'difficulty' && difficultyChartData && (
                        <div className="chart">
                            <h3>Distribuição por Nível de Dificuldade</h3>
                            <div className="donut-chart-container">
                                <Doughnut
                                    data={difficultyChartData}
                                    options={{
                                        responsive: true,
                                        plugins: {
                                            legend: {
                                                position: 'top',
                                            },
                                            title: {
                                                display: true,
                                                text: 'Sessões por Nível de Dificuldade'
                                            }
                                        }
                                    }}
                                />
                            </div>
                            <p className="chart-explanation">
                                Este gráfico mostra quantas sessões você completou em cada nível de dificuldade.
                                À medida que você progride, deve haver um aumento nas sessões de níveis mais avançados.
                            </p>
                        </div>
                    )}

                    {activeTab === 'words' && wordAccuracyChartData && (
                        <div className="chart">
                            <h3>Precisão por Palavra</h3>
                            <Bar
                                data={wordAccuracyChartData}
                                options={{
                                    responsive: true,
                                    plugins: {
                                        legend: {
                                            position: 'top',
                                        },
                                        title: {
                                            display: true,
                                            text: 'Precisão na Pronúncia de Palavras (%)'
                                        }
                                    },
                                    scales: {
                                        y: {
                                            min: 0,
                                            max: 100,
                                            ticks: {
                                                stepSize: 20
                                            }
                                        }
                                    }
                                }}
                            />
                            <p className="chart-explanation">
                                Este gráfico mostra sua precisão na pronúncia de palavras específicas.
                                As palavras com menor precisão indicam áreas onde você pode focar para melhorar.
                            </p>
                        </div>
                    )}

                    {(!progressChartData && activeTab === 'progress') ||
                        (!difficultyChartData && activeTab === 'difficulty') ||
                        (!wordAccuracyChartData && activeTab === 'words') ? (
                        <div className="no-data-message">
                            <p>Ainda não há dados suficientes para gerar este gráfico.</p>
                            <p>Continue praticando para ver estatísticas detalhadas aqui!</p>
                        </div>
                    ) : null}
                </div>
            </section>

            <div className="navigation-buttons">
                <Link to="/history" className="nav-button">Ver Histórico de Progresso</Link>
                <Link to="/achievements" className="nav-button">Ver Conquistas</Link>
            </div>
        </div>
    );
};

export default Statistics;