import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { FaRocket, FaStar, FaTrophy, FaMedal, FaSignOutAlt, FaBook, FaGamepad, FaMagic } from 'react-icons/fa';
import SimpleConfetti from '../components/common/SimpleConfetti';
import { useTheme } from '../context/ThemeContext';
import api from '../services/api';
import AchievementBadge from '../components/common/AchievementBadge';
import CharacterGuide from '../components/common/CharacterGuide';
import { useToast } from '../components/common/SimpleToast';
import './Dashboard.css';

const Dashboard = () => {
    const navigate = useNavigate();
    const { currentTheme } = useTheme();
    const toast = useToast();
    const userName = localStorage.getItem('name') || 'Explorador';
    const [exercises, setExercises] = useState([]);
    const [loading, setLoading] = useState(false);
    const [stats, setStats] = useState({ completed: 0, score: 0, level: 'Iniciante I' });
    const [showConfetti, setShowConfetti] = useState(false);
    const [lastLogin, setLastLogin] = useState(null);
    const [dailyStreak, setDailyStreak] = useState(0);
    const [showCharacterTip, setShowCharacterTip] = useState(true);

    // Dicas do personagem que guia as crianças
    const tips = [
        "Tente fazer pelo menos um exercício por dia!",
        "Clique no Gigi para jogos super divertidos!",
        "A prática diária ajuda sua fala a melhorar mais rápido!",
        "Ganhe estrelas completando desafios!",
        "Experimente temas diferentes clicando no botão colorido!"
    ];

    // Seleciona uma dica aleatória
    const [currentTip, setCurrentTip] = useState(tips[Math.floor(Math.random() * tips.length)]);

    // Efeito de confete para celebrar conquistas (simulado para demo)
    useEffect(() => {
        const hasNewAchievement = Math.random() > 0.7; // Simulação de conquista
        if (hasNewAchievement) {
            setShowConfetti(true);
            setTimeout(() => setShowConfetti(false), 5000);

            // Exemplo de uso do nosso novo sistema de notificações
            toast.showSuccess("Parabéns! Você ganhou uma nova conquista!");
        }

        // Simulação de registro de login diário e contagem de sequência
        const today = new Date().toDateString();
        const lastLoginDate = localStorage.getItem('lastLogin');

        if (lastLoginDate) {
            setLastLogin(new Date(lastLoginDate));

            // Verificar se é um novo dia
            if (lastLoginDate !== today) {
                localStorage.setItem('lastLogin', today);

                // Verificar sequência (se último login foi ontem)
                const yesterday = new Date();
                yesterday.setDate(yesterday.getDate() - 1);

                if (lastLoginDate === yesterday.toDateString()) {
                    const streak = parseInt(localStorage.getItem('dailyStreak') || '0');
                    const newStreak = streak + 1;
                    localStorage.setItem('dailyStreak', newStreak.toString());
                    setDailyStreak(newStreak);

                    // Confetti para celebrar sequência
                    if (newStreak % 5 === 0) { // A cada 5 dias
                        setShowConfetti(true);
                        setTimeout(() => setShowConfetti(false), 5000);
                        toast.showSuccess(`Incrível! Você está praticando há ${newStreak} dias seguidos!`);
                    }
                } else {
                    // Resetar sequência se perdeu um dia
                    localStorage.setItem('dailyStreak', '1');
                    setDailyStreak(1);
                }
            } else {
                // Mesmo dia, manter sequência
                setDailyStreak(parseInt(localStorage.getItem('dailyStreak') || '0'));
            }
        } else {
            // Primeiro login
            localStorage.setItem('lastLogin', today);
            localStorage.setItem('dailyStreak', '1');
            setDailyStreak(1);
            toast.showInfo("Bem-vindo! Complete exercícios diariamente para ganhar recompensas!");
        }
    }, [toast]);

    // Atualizar os exercícios disponíveis
    useEffect(() => {
        setExercises([
            {
                id: 1,
                title: 'Aventura com os Sons R',
                difficulty: 'beginner',
                description: 'Embarque numa aventura para dominar o som do R nas palavras',
                icon: '🚀',
                stars: 3,
                unlocked: true
            },
            {
                id: 2,
                title: 'Missão S e Z',
                difficulty: 'intermediate',
                description: 'Diferencie os sons sibilantes super poderosos',
                icon: '🦸‍♂️',
                stars: 2,
                unlocked: true
            },
            {
                id: 3,
                title: 'Desafio das Frases Mágicas',
                difficulty: 'advanced',
                description: 'Desbloqueie o poder da fala com frases complexas',
                icon: '🔮',
                stars: 1,
                unlocked: true
            },
            {
                id: 4,
                title: 'Segredo das Rimas',
                difficulty: 'intermediate',
                description: 'Descubra o mundo encantado das palavras que rimam',
                icon: '🎭',
                stars: 0,
                unlocked: false
            },
            {
                id: 'gigi',
                title: 'Gigi, o Gênio dos Jogos',
                type: 'gigi',
                description: 'Jogos mágicos criados especialmente para você pelo nosso gênio',
                icon: '🧞‍♂️',
                stars: 5,
                unlocked: true
            }
        ]);

        // Dados simulados para demonstração
        setStats({
            completed: 7,
            score: 85,
            level: 'Aventureiro I'
        });
    }, []);

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user_id');
        localStorage.removeItem('name');
        toast.showInfo("Até logo! Volte em breve para continuar sua aventura!");
        navigate('/login');
    };

    // Iniciar um exercício
    const startExercise = (exerciseId, unlocked) => {
        if (!unlocked) {
            // Animação ou feedback para exercício bloqueado
            toast.showWarning("Este exercício ainda está bloqueado! Complete os anteriores primeiro.");
            return;
        }

        if (exerciseId === 'gigi') {
            navigate('/gigi-games');
        } else {
            navigate(`/exercise/${exerciseId}`);
        }
    };

    return (
        <div className="dashboard-container">
            {showConfetti && <SimpleConfetti duration={5000} particleCount={200} />}

            <header className="dashboard-header">
                <div className="dashboard-title">
                    <FaGamepad className="dashboard-icon" />
                    <h1>Mundo da Fala Divertida</h1>
                </div>

                <div className="user-profile">
                    <div className="user-avatar">
                        {userName.charAt(0).toUpperCase()}
                    </div>
                    <div className="user-details">
                        <span className="user-name">Olá, {userName}!</span>
                        <div className="user-badges">
                            <AchievementBadge
                                icon={<FaStar />}
                                label={`Nível: ${stats.level}`}
                            />
                            <AchievementBadge
                                icon={<FaMedal />}
                                label={`${dailyStreak} dias seguidos`}
                            />
                        </div>
                    </div>
                    <button className="logout-button" onClick={handleLogout}>
                        <FaSignOutAlt />
                    </button>
                </div>
            </header>

            <div className="dashboard-content">
                {showCharacterTip && (
                    <CharacterGuide
                        message={currentTip}
                        onClose={() => setShowCharacterTip(false)}
                        onNext={() => {
                            const newTip = tips[Math.floor(Math.random() * tips.length)];
                            setCurrentTip(newTip);
                        }}
                    />
                )}

                <section className="progress-summary">
                    <h2><FaTrophy /> Sua Jornada</h2>
                    <div className="progress-cards">
                        <div className="progress-card">
                            <div className="progress-card-icon">🎯</div>
                            <div className="progress-card-value">{stats.completed}</div>
                            <div className="progress-card-label">Desafios Vencidos</div>
                        </div>

                        <div className="progress-card">
                            <div className="progress-card-icon">⭐</div>
                            <div className="progress-card-value">{stats.score}</div>
                            <div className="progress-card-label">Pontos de Magia</div>
                        </div>

                        <div className="progress-card">
                            <div className="progress-card-icon">🏆</div>
                            <div className="progress-card-value">{dailyStreak}</div>
                            <div className="progress-card-label">Dias de Aventura</div>
                        </div>
                    </div>
                </section>

                <section className="exercises-section">
                    <h2><FaRocket /> Aventuras Disponíveis</h2>
                    <div className="exercises-grid">
                        {exercises.map(exercise => (
                            <div
                                key={exercise.id}
                                className={`exercise-card ${exercise.type === 'gigi' ? 'gigi' : exercise.difficulty} ${!exercise.unlocked ? 'locked' : ''}`}
                                onClick={() => startExercise(exercise.id, exercise.unlocked)}
                            >
                                <div className="exercise-card-header">
                                    <div className="exercise-icon">{exercise.icon}</div>
                                    <h3>{exercise.title}</h3>
                                    {exercise.type === 'gigi' && <FaMagic className="magic-icon" />}
                                </div>

                                <div className="exercise-difficulty">
                                    {exercise.type !== 'gigi' ? (
                                        <span className={`difficulty-badge ${exercise.difficulty}`}>
                                            {exercise.difficulty === 'beginner' ? 'Fácil' :
                                                exercise.difficulty === 'intermediate' ? 'Médio' : 'Desafiador'}
                                        </span>
                                    ) : (
                                        <span className="gigi-badge">Inteligência Mágica</span>
                                    )}
                                </div>

                                <p className="exercise-description">{exercise.description}</p>

                                <div className="exercise-footer">
                                    <div className="star-rating">
                                        {[...Array(5)].map((_, i) => (
                                            <span
                                                key={i}
                                                className={`star ${i < exercise.stars ? 'filled' : ''}`}
                                            >
                                                ⭐
                                            </span>
                                        ))}
                                    </div>

                                    <button
                                        className={`start-button ${exercise.type === 'gigi' ? 'gigi-button' : ''} ${!exercise.unlocked ? 'locked' : ''}`}
                                    >
                                        {!exercise.unlocked ? 'Bloqueado' :
                                            exercise.type === 'gigi' ? 'Jogar com Gigi' : 'Iniciar Aventura'}
                                    </button>
                                </div>

                                {!exercise.unlocked && (
                                    <div className="lock-overlay">
                                        <span className="lock-icon">🔒</span>
                                        <p>Complete missões anteriores para desbloquear!</p>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </section>

                <section className="daily-challenge">
                    <h2><FaBook /> Desafio do Dia</h2>
                    <div className="challenge-card">
                        <div className="challenge-header">
                            <div className="challenge-icon">🎪</div>
                            <h3>O Circo dos Sons</h3>
                        </div>
                        <p>Hoje seu desafio é praticar os sons que começam com P como no palhaço do circo!</p>
                        <div className="word-examples">
                            <span className="word-chip">Palhaço</span>
                            <span className="word-chip">Pipoca</span>
                            <span className="word-chip">Pato</span>
                            <span className="word-chip">Pião</span>
                        </div>
                        <button
                            className="challenge-button"
                            onClick={() => {
                                toast.showSuccess("Você iniciou o desafio do dia! Boa sorte!");
                            }}
                        >
                            Iniciar Desafio do Dia
                        </button>
                    </div>
                </section>
            </div>
        </div>
    );
};

export default Dashboard;