import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Spinner, Alert, ProgressBar } from 'react-bootstrap';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import { fetchWithAuth } from '../services/api';
import './ProgressDashboard.css';

// Importação necessária para o Chart.js
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js';

// Registrar componentes necessários do Chart.js
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

const ProgressDashboard = () => {
    const [statistics, setStatistics] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                setLoading(true);
                const response = await fetchWithAuth('/api/user/statistics');

                if (response.success) {
                    setStatistics(response.statistics);
                } else {
                    throw new Error(response.message || 'Falha ao carregar estatísticas');
                }
            } catch (error) {
                console.error('Erro ao buscar estatísticas:', error);
                setError('Não foi possível carregar suas estatísticas. Por favor, tente novamente mais tarde.');
            } finally {
                setLoading(false);
            }
        };

        fetchStats();
    }, []);

    if (loading) {
        return (
            <div className="text-center my-5">
                <Spinner animation="border" role="status">
                    <span className="visually-hidden">Carregando...</span>
                </Spinner>
                <p className="mt-2">Carregando suas estatísticas...</p>
            </div>
        );
    }

    if (error) {
        return (
            <Alert variant="danger" className="my-3">
                <Alert.Heading>Erro</Alert.Heading>
                <p>{error}</p>
            </Alert>
        );
    }

    if (!statistics) {
        return (
            <Alert variant="info" className="my-3">
                <Alert.Heading>Sem dados</Alert.Heading>
                <p>Não foi possível carregar suas estatísticas de progresso.</p>
            </Alert>
        );
    }

    // Configuração do gráfico de pontuação ao longo do tempo
    const scoreChartData = {
        labels: statistics.weekly_progress.map(day => day.day),
        datasets: [
            {
                label: 'Pontuação Média',
                data: statistics.weekly_progress.map(day => day.avg_score),
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.4
            }
        ]
    };

    // Configuração do gráfico de exercícios por dificuldade
    const difficultyChartData = {
        labels: Object.keys(statistics.difficulty_distribution),
        datasets: [
            {
                label: 'Exercícios por Dificuldade',
                data: Object.values(statistics.difficulty_distribution),
                backgroundColor: [
                    'rgba(75, 192, 192, 0.6)',
                    'rgba(255, 159, 64, 0.6)',
                    'rgba(255, 99, 132, 0.6)',
                ],
                borderColor: [
                    'rgba(75, 192, 192, 1)',
                    'rgba(255, 159, 64, 1)',
                    'rgba(255, 99, 132, 1)',
                ],
                borderWidth: 1
            }
        ]
    };

    // Configuração do gráfico de distribuição de tipos de exercícios
    const exerciseTypesData = {
        labels: Object.keys(statistics.exercise_types_distribution),
        datasets: [
            {
                label: 'Tipos de Exercícios',
                data: Object.values(statistics.exercise_types_distribution),
                backgroundColor: [
                    'rgba(54, 162, 235, 0.6)',
                    'rgba(153, 102, 255, 0.6)',
                    'rgba(255, 206, 86, 0.6)',
                    'rgba(75, 192, 192, 0.6)',
                    'rgba(255, 99, 132, 0.6)',
                ],
                borderWidth: 1
            }
        ]
    };

    return (
        <div className="progress-dashboard-container">
            <h1 className="mb-4">Meu Progresso</h1>

            <Row className="mb-4">
                <Col md={3}>
                    <Card className="stat-card">
                        <Card.Body className="text-center">
                            <div className="stat-icon">🎯</div>
                            <h2>{statistics.total_exercises_completed}</h2>
                            <p>Exercícios Completados</p>
                        </Card.Body>
                    </Card>
                </Col>
                <Col md={3}>
                    <Card className="stat-card">
                        <Card.Body className="text-center">
                            <div className="stat-icon">⏱️</div>
                            <h2>{statistics.total_time_spent_mins} min</h2>
                            <p>Tempo Total</p>
                        </Card.Body>
                    </Card>
                </Col>
                <Col md={3}>
                    <Card className="stat-card">
                        <Card.Body className="text-center">
                            <div className="stat-icon">📈</div>
                            <h2>{statistics.average_score}%</h2>
                            <p>Pontuação Média</p>
                        </Card.Body>
                    </Card>
                </Col>
                <Col md={3}>
                    <Card className="stat-card">
                        <Card.Body className="text-center">
                            <div className="stat-icon">🏆</div>
                            <h2>{statistics.achievements_count}</h2>
                            <p>Conquistas</p>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>

            <Row className="mb-4">
                <Col md={6}>
                    <Card className="chart-card">
                        <Card.Header>
                            <h2 className="chart-title">Progresso Semanal</h2>
                        </Card.Header>
                        <Card.Body>
                            <Line
                                data={scoreChartData}
                                options={{
                                    responsive: true,
                                    plugins: {
                                        legend: {
                                            position: 'top',
                                        },
                                        title: {
                                            display: false
                                        }
                                    },
                                    scales: {
                                        y: {
                                            min: 0,
                                            max: 100,
                                            ticks: {
                                                callback: value => `${value}%`
                                            }
                                        }
                                    }
                                }}
                            />
                        </Card.Body>
                    </Card>
                </Col>
                <Col md={6}>
                    <Card className="chart-card">
                        <Card.Header>
                            <h2 className="chart-title">Distribuição por Dificuldade</h2>
                        </Card.Header>
                        <Card.Body>
                            <Doughnut
                                data={difficultyChartData}
                                options={{
                                    responsive: true,
                                    plugins: {
                                        legend: {
                                            position: 'top',
                                        }
                                    }
                                }}
                            />
                        </Card.Body>
                    </Card>
                </Col>
            </Row>

            <Row className="mb-4">
                <Col md={6}>
                    <Card className="chart-card">
                        <Card.Header>
                            <h2 className="chart-title">Tipos de Exercícios</h2>
                        </Card.Header>
                        <Card.Body>
                            <Bar
                                data={exerciseTypesData}
                                options={{
                                    responsive: true,
                                    plugins: {
                                        legend: {
                                            display: false,
                                        }
                                    }
                                }}
                            />
                        </Card.Body>
                    </Card>
                </Col>
                <Col md={6}>
                    <Card className="chart-card">
                        <Card.Header>
                            <h2 className="chart-title">Áreas de Foco</h2>
                        </Card.Header>
                        <Card.Body>
                            <div className="focus-area-container">
                                {statistics.focus_areas.map((area, index) => (
                                    <div key={index} className="focus-area">
                                        <div className="focus-area-title">
                                            <span>{area.name}</span>
                                            <span>{area.score}%</span>
                                        </div>
                                        <ProgressBar
                                            now={area.score}
                                            variant={area.score >= 80 ? "success" : area.score >= 60 ? "info" : "warning"}
                                        />
                                    </div>
                                ))}
                            </div>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>

            <Card className="mb-4">
                <Card.Header>
                    <h2 className="chart-title">Recomendações</h2>
                </Card.Header>
                <Card.Body>
                    <Row>
                        {statistics.recommendations.map((rec, index) => (
                            <Col md={4} key={index} className="mb-3">
                                <Card className="recommendation-card">
                                    <Card.Body>
                                        <div className="rec-icon">{rec.icon}</div>
                                        <h3>{rec.title}</h3>
                                        <p>{rec.description}</p>
                                    </Card.Body>
                                </Card>
                            </Col>
                        ))}
                    </Row>
                </Card.Body>
            </Card>
        </div>
    );
};

export default ProgressDashboard;