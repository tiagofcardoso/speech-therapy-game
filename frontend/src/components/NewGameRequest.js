import React, { useState } from 'react';
import api from '../services/api';

const NewGameRequest = ({ onGameCreated }) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [focusArea, setFocusArea] = useState('');

    const requestNewGame = async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await api.post('/api/games/generate', {
                focus_area: focusArea
            });

            if (response.data.success) {
                onGameCreated(response.data.game);
            } else {
                setError(response.data.message);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="new-game-request">
            <h3>Create a New Game</h3>

            <div className="form-group">
                <label>Focus Area (optional)</label>
                <select
                    value={focusArea}
                    onChange={(e) => setFocusArea(e.target.value)}
                >
                    <option value="">Automatic (based on progress)</option>
                    <option value="articulation">Articulation</option>
                    <option value="phonology">Phonology</option>
                    <option value="vocabulary">Vocabulary</option>
                    <option value="fluency">Fluency</option>
                </select>
            </div>

            <button
                onClick={requestNewGame}
                disabled={loading}
                className="primary-button"
            >
                {loading ? 'Creating Game...' : 'Create New Game'}
            </button>

            {error && <div className="error-message">{error}</div>}
        </div>
    );
};

export default NewGameRequest;