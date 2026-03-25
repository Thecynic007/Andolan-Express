import os
from scoreboard import Scoreboard

class Leaderboard:
    def __init__(self, filename="scores.json"):
        # Convert to absolute path
        self.filename = os.path.abspath(filename)
        self.scoreboard = Scoreboard(self.filename)
        
        # Ensure file is writable
        if not self.is_writable(self.filename):
            print(f"Warning: {self.filename} is not writable. Scores may not be saved.")

    def is_writable(self, path):
        """Check if file is writable"""
        if os.path.exists(path):
            return os.access(path, os.W_OK)
        try:
            with open(path, 'a'):
                pass
            return True
        except IOError:
            return False

    def is_high_score(self, score, mode="normal"):
        """Check if score qualifies for leaderboard (top 10)"""
        scores = self.scoreboard.read_records(mode)
        if len(scores) < 10:
            return True
        # Check if score is higher than the lowest score on the leaderboard
        return score > scores[-1]['score']

    def add_score(self, name, score, tokens, mode="normal"):
        """Add score to leaderboard"""
        return self.scoreboard.create_record(name, score, tokens, mode)
    
    def get_top_scores(self, mode=None, count=10):
        """
        Get top scores, optionally filtered by mode.
        
        Args:
            mode (str, optional): Game mode to filter by. Defaults to None (all modes).
            count (int, optional): Maximum number of scores to return. Defaults to 10.
        
        Returns:
            list: List of score entries, sorted by score (descending)
        """
        # Handle "None" mode as "all"
        if mode is None:
            mode = "all"
        scores = self.scoreboard.read_records(mode)
        return scores[:count]
