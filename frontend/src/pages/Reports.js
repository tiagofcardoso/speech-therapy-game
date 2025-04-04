import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Bar, Line } from 'react-chartjs-2';
import { Chart, registerables } from 'chart.js';
import './Reports.css';

// Register Chart.js components
Chart.register(...registerables);

const Reports = () => {
    const navigate = useNavigate();
    const [sessions, setSessions] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchUserSessions();
    }, []);

    const fetchUserSessions = async () => {
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                navigate('/login');
                return;
            }

            const response = await axios.get('/api/user/sessions', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            setSessions(response.data.sessions);
            setIsLoading(false);
        } catch (err) {
            console.error('Error fetching sessions:', err);
            setError('Failed to load your progress data. Please try again later.');
            setIsLoading(false);

            if (err.response && err.response.status === 401) {
                navigate('/login');
            }
        }
    };

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString();
    };

    // Prepare data for bar chart
    const prepareScoreData = () => {
        const labels = sessions.map(session => formatDate(session.date));
        const scores = sessions.map(session => session.score);

        return {
            labels,
            datasets: [
                {
                    label: 'Session Scores',
                    data: scores,
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1,
                },
            ],
        };
    };

    // Prepare data for line chart - difficulty progression
    const prepareDifficultyData = () => {
        const labels = sessions.map(session => formatDate(session.date));

        // Convert difficulty to numeric value
        const difficultyValues = sessions.map(session => {
            switch (session.difficulty) {
                case 'beginner': return 1;
                case 'intermediate': return 2;
                case 'advanced': return 3;
                default: return 0;
            }
        });

        return {
            labels,
            datasets: [
                {
                    label: 'Difficulty Progression',
                    data: difficultyValues,
                    fill: false,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    tension: 0.4,
                },
            ],
        };
    };

    if (isLoading) {
        return <div className="loading">Loading your progress data...</div>;
    }

    if (error) {
        return <div className="error">{error}</div>;
    }

    return (
        <div className="reports-container">
            <h1>User Performance Reports</h1>
            <div className="charts">
                <div className="chart">
                    <h2>Session Scores</h2>
                    <Bar data={prepareScoreData()} />
                </div>
                <div className="chart">
                    <h2>Difficulty Progression</h2>
                    <Line data={prepareDifficultyData()} />
                </div>
            </div>
        </div>
    );
};

export default Reports;