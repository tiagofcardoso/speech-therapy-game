class Game:
    def __init__(self, game_id, difficulty_level):
        self.game_id = game_id
        self.difficulty_level = difficulty_level
        self.score = 0

    def start_game(self):
        # Logic to start the game
        pass

    def end_game(self):
        # Logic to end the game
        pass

    def update_score(self, points):
        self.score += points

    def get_game_info(self):
        return {
            "game_id": self.game_id,
            "difficulty_level": self.difficulty_level,
            "score": self.score
        }