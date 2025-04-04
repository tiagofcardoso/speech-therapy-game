import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import './Dashboard.css'; // Vamos criar este arquivo a seguir

const Dashboard = () => {
    const navigate = useNavigate();
    const userName = localStorage.getItem('name') || 'Usuário';
    const [exercises, setExercises] = useState([]);
    const [loading, setLoading] = useState(false);

    // Carregar exercícios disponíveis
    useEffect(() => {
        // Exemplos de exercícios (normalmente viriam da API)
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
            }
        ]);
    }, []);

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user_id');
        localStorage.removeItem('name');
        navigate('/login');
    };

    const startExercise = (exerciseId) => {
        console.log(`Iniciando exercício ${exerciseId}`);
        navigate(`/exercise/${exerciseId}`);
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
                            <div key={exercise.id} className={`exercise-card ${exercise.difficulty}`}>
                                <h3>{exercise.title}</h3>
                                <span className="difficulty-badge">
                                    {exercise.difficulty === 'beginner' ? 'Iniciante' :
                                        exercise.difficulty === 'intermediate' ? 'Intermediário' : 'Avançado'}
                                </span>
                                <p>{exercise.description}</p>
                                <button
                                    className="start-exercise-button"
                                    onClick={() => startExercise(exercise.id)}
                                >
                                    Iniciar Exercício
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