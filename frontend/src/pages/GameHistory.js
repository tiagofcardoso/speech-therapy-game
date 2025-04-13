import React, { useState, useEffect } from 'react';
import { Table, Card, Spinner, Alert, Badge, Row, Col } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { fetchWithAuth } from '../services/api';
import './GameHistory.css';

const GameHistory = () => {
    const [history, setHistory] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                setLoading(true);
                const response = await fetchWithAuth('/api/user/history');

                if (response.success) {
                    setHistory(response);
                } else {
                    throw new Error(response.message || 'Falha ao carregar histórico de jogos');
                }
            } catch (error) {
                console.error('Erro ao buscar histórico:', error);
                setError('Não foi possível carregar seu histórico de jogos. Por favor, tente novamente mais tarde.');
            } finally {
                setLoading(false);
            }
        };

        fetchHistory();
    }, []);

    // Formatar data para exibição
    const formatDate = (dateString) => {
        try {
            const options = {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            };
            return new Date(dateString).toLocaleDateString('pt-BR', options);
        } catch (e) {
            return dateString;
        }
    };

    // Renderizar o badge de dificuldade com cor correspondente
    const renderDifficultyBadge = (difficulty) => {
        const difficultyMap = {
            'iniciante': 'success',
            'médio': 'warning',
            'avançado': 'danger',
            'beginner': 'success',
            'intermediate': 'warning',
            'advanced': 'danger'
        };

        const color = difficultyMap[difficulty] || 'secondary';
        return <Badge bg={color}>{difficulty}</Badge>;
    };

    if (loading) {
        return (
            <div className="text-center my-5">
                <Spinner animation="border" role="status">
                    <span className="visually-hidden">Carregando...</span>
                </Spinner>
                <p className="mt-2">Carregando seu histórico de jogos...</p>
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

    if (!history || history.sessions.length === 0) {
        return (
            <div className="history-empty text-center my-5">
                <div className="empty-icon">📋</div>
                <h3>Histórico Vazio</h3>
                <p>Você ainda não completou nenhum jogo. Comece a jogar para construir seu histórico!</p>
                <button
                    className="btn btn-primary mt-3"
                    onClick={() => navigate('/games')}
                >
                    Ir para os Jogos
                </button>
            </div>
        );
    }

    return (
        <div className="game-history-container">
            <h1 className="mb-4">Histórico de Jogos</h1>

            <Row className="mb-4">
                <Col md={3}>
                    <Card className="stat-card">
                        <Card.Body className="text-center">
                            <h2>{history.statistics.total_sessions}</h2>
                            <p>Total de Sessões</p>
                        </Card.Body>
                    </Card>
                </Col>
                <Col md={3}>
                    <Card className="stat-card">
                        <Card.Body className="text-center">
                            <h2>{history.statistics.total_exercises_completed}</h2>
                            <p>Exercícios Completados</p>
                        </Card.Body>
                    </Card>
                </Col>
                <Col md={3}>
                    <Card className="stat-card">
                        <Card.Body className="text-center">
                            <h2>{history.statistics.average_score}%</h2>
                            <p>Pontuação Média</p>
                        </Card.Body>
                    </Card>
                </Col>
                <Col md={3}>
                    <Card className="stat-card">
                        <Card.Body className="text-center">
                            <div className="d-flex justify-content-around">
                                <div>
                                    <span className="difficulty-dot beginner"></span>
                                    <div>{history.statistics.sessions_by_difficulty.iniciante}</div>
                                </div>
                                <div>
                                    <span className="difficulty-dot intermediate"></span>
                                    <div>{history.statistics.sessions_by_difficulty.médio}</div>
                                </div>
                                <div>
                                    <span className="difficulty-dot advanced"></span>
                                    <div>{history.statistics.sessions_by_difficulty.avançado}</div>
                                </div>
                            </div>
                            <p>Por Dificuldade</p>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>

            <Card className="mb-4">
                <Card.Header>
                    <h2 className="history-section-title">Sessões Recentes</h2>
                </Card.Header>
                <Card.Body>
                    <div className="table-responsive">
                        <Table hover striped className="game-history-table">
                            <thead>
                                <tr>
                                    <th>Data</th>
                                    <th>Jogo</th>
                                    <th>Dificuldade</th>
                                    <th>Pontuação</th>
                                    <th>Exercícios</th>
                                </tr>
                            </thead>
                            <tbody>
                                {history.sessions.map((session, index) => (
                                    <tr key={index} className="history-row">
                                        <td>{formatDate(session.completed_at)}</td>
                                        <td>{session.game_title}</td>
                                        <td>{renderDifficultyBadge(session.difficulty)}</td>
                                        <td>
                                            <span className={`score-value ${session.score >= 80 ? 'high-score' : session.score >= 60 ? 'medium-score' : 'low-score'}`}>
                                                {session.score}%
                                            </span>
                                        </td>
                                        <td>{session.exercises_completed}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </Table>
                    </div>
                </Card.Body>
            </Card>
        </div>
    );
};

export default GameHistory;