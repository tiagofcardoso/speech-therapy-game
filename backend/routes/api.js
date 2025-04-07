const express = require('express');
const router = express.Router();
const gameController = require('../controllers/gameController');

// Adicione uma rota de health check
router.get('/health', (req, res) => {
    return res.status(200).json({
        status: 'ok',
        message: 'API está funcionando corretamente'
    });
});

// Rota para geração de jogos - atualize de '/api/gigi/generate-game' para '/api/games/generate'
router.post('/games/generate', authenticateToken, gameController.generateGame);

module.exports = router;    });
  }
});

module.exports = router;