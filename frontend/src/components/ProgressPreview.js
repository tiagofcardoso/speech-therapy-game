import React, { useState } from 'react';
import { Container, Card, Tabs, Tab, Table, Badge, ProgressBar, Row, Col } from 'react-bootstrap';
import './ProgressPreview.css';

const ProgressPreview = () => {
    const [key, setKey] = useState('history');

    // Dados de exemplo para histórico
    const mockHistory = [
        {
            id: '1',
            game_title: 'Explorando o Som P',
            completed_at: '2025-04-13T10:30:00',
            difficulty: 'iniciante',
            exercises_completed: 5,
            score: 92
        },
        {
            id: '2',
            game_title: 'Aventuras com o Som R',
            completed_at: '2025-04-12T14:45:00',
            difficulty: 'médio',
            exercises_completed: 6,
            score: 85
        },
        {
            id: '3',
            game_title: 'Viagem pelo Som S',
            completed_at: '2025-04-10T09:15:00',
            difficulty: 'iniciante',
            exercises_completed: 5,
            score: 78
        },
        {
            id: '4',
            game_title: 'Desafio do Som T',
            completed_at: '2025-04-09T16:20:00',
            difficulty: 'avançado',
            exercises_completed: 7,
            score: 90
        }
    ];

    // Dados de exemplo para conquistas
    const mockAchievements = {
        earned: [
            {
                id: 'first_game',
                title: 'Primeiro Passo',
                description: 'Complete seu primeiro jogo',
                icon: '🎮',
                earned_at: '2025-04-09T16:30:00'
            },
            {
                id: 'perfect_score',
                title: 'Pontuação Perfeita',
                description: 'Obtenha 100% em qualquer jogo',
                icon: '🌟',
                earned_at: '2025-04-11T11:45:00'
            }
        ],
        inProgress: [
            {
                id: 'master_beginner',
                title: 'Mestre Iniciante',
                description: 'Complete 5 jogos no nível iniciante com pontuação acima de 80%',
                icon: '🥉',
                progress: 2,
                total: 5,
                percentage: 40
            },
            {
                id: 'practice_master',
                title: 'Mestre da Prática',
                description: 'Complete 50 exercícios no total',
                icon: '🏆',
                progress: 23,
                total: 50,
                percentage: 46
            }
        ]
    };

    // Dados de exemplo para estatísticas
    const mockStats = {
        totalSessions: 4,
        averageScore: 86.25,
        totalExercises: 23,
        currentLevel: 'iniciante',
        progressToNextLevel: 70
    };

    // Formatar data
    const formatDate = (dateString) => {
        const options = {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        return new Date(dateString).toLocaleDateString('pt-BR', options);
    };

    // Definir cor baseada na pontuação
    const getScoreColor = (score) => {
        if (score >= 90) return 'success';
        if (score >= 70) return 'primary';
        if (score >= 50) return 'warning';
        return 'danger';
    };

    // Função para renderizar o histórico
    const renderHistory = () => (
        <div>
            <Card className="mb-4">
                <Card.Header>
                    <h3>Resumo</h3>
                </Card.Header>
                <Card.Body>
                    <div className="statistics-summary">
                        <div className="stat-item">
                            <div className="stat-value">{mockStats.totalSessions}</div>
                            <div className="stat-label">Jogos Completados</div>
                        </div>
                        <div className="stat-item">
                            <div className="stat-value">{mockStats.totalExercises}</div>
                            <div className="stat-label">Exercícios Realizados</div>
                        </div>
                        <div className="stat-item">
                            <div className="stat-value">{mockStats.averageScore.toFixed(1)}%</div>
                            <div className="stat-label">Pontuação Média</div>
                        </div>
                    </div>
                </Card.Body>
            </Card>

            <Card>
                <Card.Header>
                    <h3>Histórico Detalhado</h3>
                </Card.Header>
                <Card.Body className="p-0">
                    <Table responsive hover className="mb-0">
                        <thead>
                            <tr>
                                <th>Jogo</th>
                                <th>Data</th>
                                <th>Dificuldade</th>
                                <th>Exercícios</th>
                                <th>Pontuação</th>
                            </tr>
                        </thead>
                        <tbody>
                            {mockHistory.map((session) => (
                                <tr key={session.id}>
                                    <td>{session.game_title}</td>
                                    <td>{formatDate(session.completed_at)}</td>
                                    <td>
                                        <Badge bg={
                                            session.difficulty === 'avançado' ? 'danger' :
                                                session.difficulty === 'médio' ? 'warning' :
                                                    'success'
                                        }>
                                            {session.difficulty}
                                        </Badge>
                                    </td>
                                    <td>{session.exercises_completed}</td>
                                    <td>
                                        <Badge bg={getScoreColor(session.score)}>
                                            {session.score}%
                                        </Badge>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </Table>
                </Card.Body>
            </Card>
        </div>
    );

    // Função para renderizar as conquistas
    const renderAchievements = () => (
        <div>
            <div className="achievements-summary mb-4">
                <Card>
                    <Card.Body>
                        <div className="d-flex justify-content-between align-items-center">
                            <div>
                                <div className="achievements-count">
                                    {mockAchievements.earned.length}/{mockAchievements.earned.length + mockAchievements.inProgress.length}
                                </div>
                                <div className="achievements-label">
                                    Conquistas Desbloqueadas
                                </div>
                            </div>
                            <div className="achievements-progress">
                                <ProgressBar
                                    now={(mockAchievements.earned.length / (mockAchievements.earned.length + mockAchievements.inProgress.length)) * 100}
                                    variant="success"
                                    style={{ height: '12px', width: '200px' }}
                                />
                                <div className="text-muted mt-1 text-center">
                                    {Math.round((mockAchievements.earned.length / (mockAchievements.earned.length + mockAchievements.inProgress.length)) * 100)}% completo
                                </div>
                            </div>
                        </div>
                    </Card.Body>
                </Card>
            </div>

            <Tabs defaultActiveKey="earned" id="achievements-tabs" className="mb-3">
                <Tab eventKey="earned" title={`Desbloqueadas (${mockAchievements.earned.length})`}>
                    <Row xs={1} md={2} className="g-4">
                        {mockAchievements.earned.map((achievement) => (
                            <Col key={achievement.id}>
                                <Card className="achievement-card earned">
                                    <Card.Body>
                                        <div className="d-flex">
                                            <div className="achievement-icon">{achievement.icon}</div>
                                            <div className="achievement-details">
                                                <Card.Title>{achievement.title}</Card.Title>
                                                <Card.Subtitle className="mb-2 text-muted">
                                                    Conquistado em {formatDate(achievement.earned_at)}
                                                </Card.Subtitle>
                                                <Card.Text>{achievement.description}</Card.Text>
                                            </div>
                                        </div>
                                    </Card.Body>
                                </Card>
                            </Col>
                        ))}
                    </Row>
                </Tab>
                <Tab eventKey="progress" title={`Em Progresso (${mockAchievements.inProgress.length})`}>
                    <Row xs={1} md={2} className="g-4">
                        {mockAchievements.inProgress.map((achievement) => (
                            <Col key={achievement.id}>
                                <Card className="achievement-card in-progress">
                                    <Card.Body>
                                        <div className="d-flex">
                                            <div className="achievement-icon faded">{achievement.icon}</div>
                                            <div className="achievement-details">
                                                <Card.Title>{achievement.title}</Card.Title>
                                                <Card.Text>{achievement.description}</Card.Text>
                                                <div className="achievement-progress">
                                                    <ProgressBar
                                                        now={achievement.percentage}
                                                        variant="primary"
                                                        style={{ height: '10px' }}
                                                    />
                                                    <div className="text-muted mt-1 small">
                                                        {achievement.progress}/{achievement.total} ({Math.round(achievement.percentage)}%)
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </Card.Body>
                                </Card>
                            </Col>
                        ))}
                    </Row>
                </Tab>
            </Tabs>
        </div>
    );

    // Função para renderizar dados de progresso
    const renderProgress = () => (
        <div>
            <Row className="mb-4">
                <Col md={4} className="mb-3 mb-md-0">
                    <Card className="h-100">
                        <Card.Body className="d-flex flex-column align-items-center justify-content-center text-center">
                            <div className="stat-value">{mockStats.totalSessions}</div>
                            <div className="stat-label">Jogos Completados</div>
                        </Card.Body>
                    </Card>
                </Col>
                <Col md={4} className="mb-3 mb-md-0">
                    <Card className="h-100">
                        <Card.Body className="d-flex flex-column align-items-center justify-content-center text-center">
                            <div className="stat-value">{mockStats.averageScore.toFixed(1)}%</div>
                            <div className="stat-label">Pontuação Média</div>
                        </Card.Body>
                    </Card>
                </Col>
                <Col md={4}>
                    <Card className="h-100">
                        <Card.Body className="d-flex flex-column align-items-center justify-content-center text-center">
                            <div className="stat-value">{mockStats.currentLevel}</div>
                            <div className="stat-label">Nível Atual</div>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>

            <Card>
                <Card.Header>
                    <h3>Progresso para o Próximo Nível</h3>
                </Card.Header>
                <Card.Body>
                    <div className="level-progress">
                        <h4>
                            {mockStats.currentLevel} → {mockStats.currentLevel === 'iniciante' ? 'médio' : mockStats.currentLevel === 'médio' ? 'avançado' : 'mestre'}
                        </h4>
                        <ProgressBar
                            now={mockStats.progressToNextLevel}
                            variant="success"
                            className="my-3"
                            style={{ height: '20px' }}
                        />
                        <div className="text-center">
                            {mockStats.progressToNextLevel}% completo
                        </div>
                        <div className="text-muted mt-3">
                            Continue completando jogos com boa pontuação para avançar ao próximo nível!
                        </div>
                    </div>
                </Card.Body>
            </Card>

            <Card className="mt-4">
                <Card.Header>
                    <h3>Visualização das Pontuações</h3>
                </Card.Header>
                <Card.Body>
                    <div className="text-center p-5">
                        <div style={{ fontSize: '5rem', opacity: 0.5 }}>📊</div>
                        <p className="mt-3">
                            Aqui serão exibidos gráficos com os dados de progresso do usuário ao longo do tempo.
                            <br />
                            (Necessário implementar Chart.js para visualização completa)
                        </p>
                    </div>
                </Card.Body>
            </Card>
        </div>
    );

    return (
        <Container className="preview-container my-4">
            <h1 className="mb-4">Prévia de Funcionalidades</h1>

            <Tabs
                id="progress-tabs"
                activeKey={key}
                onSelect={(k) => setKey(k)}
                className="mb-4"
            >
                <Tab eventKey="history" title="Histórico">
                    {renderHistory()}
                </Tab>
                <Tab eventKey="achievements" title="Conquistas">
                    {renderAchievements()}
                </Tab>
                <Tab eventKey="progress" title="Progresso">
                    {renderProgress()}
                </Tab>
            </Tabs>
        </Container>
    );
};

export default ProgressPreview;