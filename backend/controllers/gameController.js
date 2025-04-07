const express = require('express');
const router = express.Router();
const { generateGameForUser } = require('../services/gameService');

// Função de controlador para geração de jogos
exports.generateGame = async (req, res) => {
    try {
        const { game_type, difficulty } = req.body;
        const userId = req.user.id;

        // Lógica para gerar o jogo baseada nos parâmetros recebidos
        const game = await generateGameForUser(userId, game_type, difficulty);

        return res.status(200).json({
            success: true,
            game: game
        });
    } catch (error) {
        console.error('Erro ao gerar jogo:', error);
        return res.status(500).json({
            success: false,
            message: 'Erro ao gerar jogo: ' + error.message
        });
    }
};

module.exports = router;