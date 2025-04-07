import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';
import './Dashboard.css'; // Vamos criar este arquivo a seguir

const Dashboard = () => {
    const navigate = useNavigate();
    const userName = localStorage.getItem('name') || 'Usuário';
    const [exercises, setExercises] = useState([]);
    const [loading, setLoading] = useState(false);

    // Update the exercise data
    useEffect(() => {
        setExercises([
            {
                id: 1,
                title: 'Pronunciação de R',
                difficulty: 'beginner',
                description: 'Pratique palavras com som de R inicial'
            },
            {
                id: 2,
                title: 'Sons de S e Z',
                difficulty: 'intermediate',
                description: 'Diferencie sons sibilantes em palavras comuns'
            },
            {
                id: 3,
                title: 'Frases Complexas',
                difficulty: 'advanced',
                description: 'Pratique frases com múltiplos sons desafiadores'
            },
            // Change MCP to Gigi
            {
                id: 'gigi',
                title: 'Gigi, o Gênio dos Jogos',
                type: 'gigi',
                description: 'Exercícios personalizados gerados pela IA com base no seu progresso'
            }
        ]);
    }, []);

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user_id');
        localStorage.removeItem('name');
        navigate('/login');
    };

    // Update the navigation function
    const startExercise = (exerciseId) => {
        if (exerciseId === 'gigi') {
            navigate('/gigi-games');
        } else {
            console.log(`Iniciando exercício ${exerciseId}`);
            navigate(`/exercise/${exerciseId}`);
        }
    };

    return (
        <div className="dashboard-container">
            <header className="dashboard-header">
                <h1>Speech Therapy Dashboard</h1>
                <div className="user-info">
                    <span>Olá, {userName}!</span>
                    <button className="logout-button" onClick={handleLogout}>
                        Sair
                    </button>
                </div>
            </header>

            <div className="dashboard-content">
                <section className="welcome-section">
                    <h2>Bem-vindo(a) ao seu programa de terapia de fala</h2>
                    <p>Aqui você encontrará exercícios personalizados para melhorar sua fala.</p>
                </section>

                <section className="exercises-section">
                    <h2>Exercícios Disponíveis</h2>
                    <div className="exercises-grid">
                        {exercises.map(exercise => (
                            <div
                                key={exercise.id}
                                className={`exercise-card ${exercise.type === 'gigi' ? 'gigi' : exercise.difficulty}`}
                            >
                                <h3>
                                    {exercise.title}
                                    {exercise.type === 'gigi' && <i className="fas fa-magic gigi-icon"></i>}
                                </h3>

                                {exercise.type !== 'gigi' && (
                                    <span className="difficulty-badge">
                                        {exercise.difficulty === 'beginner' ? 'Iniciante' :
                                            exercise.difficulty === 'intermediate' ? 'Intermediário' : 'Avançado'}
                                    </span>
                                )}

                                {exercise.type === 'gigi' && (
                                    <span className="gigi-badge">Inteligência Artificial</span>
                                )}

                                <p>{exercise.description}</p>

                                <button
                                    className={`start-exercise-button ${exercise.type === 'gigi' ? 'gigi-button' : ''}`}
                                    onClick={() => startExercise(exercise.id)}
                                >
                                    {exercise.type === 'gigi' ? 'Consultar o Gênio' : 'Iniciar Exercício'}
                                </button>
                            </div>
                        ))}
                    </div>
                </section>

                <section className="progress-section">
                    <h2>Seu Progresso</h2>
                    <div className="progress-overview">
                        <div className="progress-card">
                            <h3>Exercícios Completados</h3>
                            <p className="progress-number">0</p>
                        </div>
                        <div className="progress-card">
                            <h3>Pontuação Média</h3>
                            <p className="progress-number">-</p>
                        </div>
                        <div className="progress-card">
                            <h3>Próximo Nível</h3>
                            <p className="progress-number">Iniciante II</p>
                        </div>
                    </div>
                </section>
            </div>
        </div>
    );
};

export default Dashboard;