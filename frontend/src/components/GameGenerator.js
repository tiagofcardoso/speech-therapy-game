import React, { useState } from 'react';
import api from '../services/api';
import { useNavigate } from 'react-router-dom';

const GameGenerator = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [gameType, setGameType] = useState('');
    const [difficulty, setDifficulty] = useState('');
    const navigate = useNavigate();

    const generateGame = async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await api.post('/api/games/generate', {
                game_type: gameType || undefined,
                difficulty: difficulty || undefined
            });

            if (response.data.success) {
                // Navigate to the game page with the generated game
                navigate(`/play/${response.data.game.game_id}`);
            } else {
                setError(response.data.message);
            }
        } catch (err) {
            setError(err.response?.data?.message || err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="game-generator-container">
            <h2>Gerar Novo Jogo de Terapia</h2>

            <div className="form-group">
                <label>Tipo de Jogo</label>
                <select
                    value={gameType}
                    onChange={(e) => setGameType(e.target.value)}
                    className="form-control"
                >
                    <option value="">Automático (baseado no progresso)</option>
                    <option value="articulation">Articulação</option>
                    <option value="vocabulary">Vocabulário e Linguagem</option>
                    <option value="fluency">Fluência</option>
                    <option value="pragmatic">Linguagem Pragmática</option>
                    <option value="pragmatic">Ditongos</option>
                    <option value="pragmatic">Tritongos</option>
                    <option value="pragmatic">Sílaba Tónica</option>
                    <option value="pragmatic">Separação de Silabas</option>
                </select>
            </div>

            <div className="form-group">
                <label>Nível de Dificuldade</label>
                <select
                    value={difficulty}
                    onChange={(e) => setDifficulty(e.target.value)}
                    className="form-control"
                >
                    <option value="">Automático (baseado no progresso)</option>
                    <option value="beginner">Iniciante</option>
                    <option value="intermediate">Intermediário</option>
                    <option value="advanced">Avançado</option>
                </select>
            </div>

            <button
                onClick={generateGame}
                disabled={loading}
                className="btn btn-primary"
            >
                {loading ? 'Gerando Jogo...' : 'Gerar Novo Jogo'}
            </button>

            {error && <div className="alert alert-danger mt-3">{error}</div>}

            <div className="game-types-info mt-4">
                <h3>Tipos de Jogos Disponíveis</h3>

                <div className="card mb-3">
                    <div className="card-header">Articulação</div>
                    <div className="card-body">
                        <p>Jogos focados na pronúncia correta de sons específicos do português.</p>
                        <p>Exemplo: "O que é o que é?", "Twister de Línguas", "Jogo da Memória dos Sons"</p>
                    </div>
                </div>

                <div className="card mb-3">
                    <div className="card-header">Vocabulário e Linguagem</div>
                    <div className="card-body">
                        <p>Jogos para desenvolver vocabulário e habilidades linguísticas.</p>
                        <p>Exemplo: "Jogo das Categorias", "Contar Histórias", "Oposto"</p>
                    </div>
                </div>

                <div className="card mb-3">
                    <div className="card-header">Fluência</div>
                    <div className="card-body">
                        <p>Jogos para melhorar a fluência verbal.</p>
                        <p>Exemplo: "Cantar em Coro", "Leitura Rítmica", "Respiração e Relaxamento"</p>
                    </div>
                </div>

                <div className="card mb-3">
                    <div className="card-header">Linguagem Pragmática</div>
                    <div className="card-body">
                        <p>Jogos para desenvolver habilidades sociais e comunicação pragmática.</p>
                        <p>Exemplo: "Jogo de Papéis", "Jogo das Emoções", "Jogo da Empatia"</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default GameGenerator;