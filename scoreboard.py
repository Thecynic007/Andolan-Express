import json
import os
from typing import List, Dict, Optional
from datetime import datetime
import enum

class GameMode(enum.Enum):
    """Enum for different game modes"""
    ALL = "all"
    NORMAL = "normal"
    MULTIPLAYER = "multiplayer"
    RAGE = "rage"

class Scoreboard:
    """
    Fully-featured CRUD leaderboard for game scores.
    Stores scores in a JSON file with multiple modes, dates, and ranks.
    """
    def __init__(self, filename: str = "scores.json"):
        self.filename = os.path.abspath(filename)
        self._ensure_file_exists()
        self.recalc_all_ranks()

    # ------------------ File Handling ------------------
    def _ensure_file_exists(self) -> None:
        """Create the scores file if it doesn't exist"""
        try:
            os.makedirs(os.path.dirname(self.filename) or '.', exist_ok=True)
            if not os.path.exists(self.filename):
                with open(self.filename, 'w') as f:
                    json.dump([], f)
        except Exception:
            # Fallback: create in current directory
            self.filename = os.path.basename(self.filename)
            with open(self.filename, 'w') as f:
                json.dump([], f)

    def load_scores(self) -> List[Dict]:
        """Load all scores from JSON file"""
        try:
            with open(self.filename, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def save_scores(self, data: List[Dict]) -> None:
        """Save scores to JSON file"""
        with open(self.filename, 'w') as f:
            json.dump(data, f, indent=4)

    # ------------------ CRUD Operations ------------------
    def create_record(self, name: str, score: int, tokens: int, mode: str) -> Dict:
        """Create a new player record"""
        scores = self.load_scores()
        try:
            score = int(score)
            tokens = int(tokens)
        except (ValueError, TypeError):
            score = 0
            tokens = 0

        timestamp = datetime.now().astimezone().isoformat()
        new_record = {
            "id": len(scores) + 1,
            "name": name.strip(),
            "score": score,
            "tokens": tokens,
            "mode": mode.lower(),
            "date": timestamp,
            "rank": 0
        }
        scores.append(new_record)
        self.save_scores(scores)
        self.recalc_all_ranks()
        return new_record

    def read_records(self, mode: str = "all") -> List[Dict]:
        """Get player records filtered by mode and sorted by score"""
        scores = self.load_scores()
        filtered_scores = scores if mode.lower() == "all" else [r for r in scores if r["mode"] == mode.lower()]
        
        # Sort logic: Multiplayer = Tokens desc, Score desc. Others = Score desc, Tokens desc.
        if mode.lower() == "multiplayer":
            sorted_scores = sorted(filtered_scores, key=lambda x: (x.get("tokens", 0), x["score"]), reverse=True)
        else:
            sorted_scores = sorted(filtered_scores, key=lambda x: (x["score"], x.get("tokens", 0)), reverse=True)
            
        for i, record in enumerate(sorted_scores):
            record["rank"] = i + 1
        return sorted_scores

    def recalc_all_ranks(self) -> None:
        """Recalculate ranks for all modes and overall"""
        scores = self.load_scores()
        # Update overall rank - Sort by score (descending) then tokens (descending)
        overall_sorted = sorted(scores, key=lambda x: (x["score"], x.get("tokens", 0)), reverse=True)
        for i, record in enumerate(overall_sorted):
            record["rank"] = i + 1
        # Update mode-specific ranks
        for mode in ["normal", "multiplayer", "rage"]:
            mode_scores = [r for r in scores if r["mode"] == mode]
            
            # Sort logic: Multiplayer = Tokens desc, Score desc. Others = Score desc, Tokens desc.
            if mode == "multiplayer":
                sorted_mode = sorted(mode_scores, key=lambda x: (x.get("tokens", 0), x["score"]), reverse=True)
            else:
                sorted_mode = sorted(mode_scores, key=lambda x: (x["score"], x.get("tokens", 0)), reverse=True)
                
            for i, record in enumerate(sorted_mode):
                record[f"{mode}_rank"] = i + 1
        self.save_scores(scores)

    def submit_score(self, name: str, score: int, tokens: int, mode: str) -> Dict:
        """Submit a new score and return its ranks"""
        new_record = self.create_record(name, score, tokens, mode)
        mode_records = self.read_records(mode)
        current_rank = next((r["rank"] for r in mode_records if r["id"] == new_record["id"]), None)
        all_records = self.read_records("all")
        overall_rank = next((r["rank"] for r in all_records if r["id"] == new_record["id"]), None)
        return {
            "record": new_record,
            "rank_in_mode": current_rank,
            "overall_rank": overall_rank,
            "message": f"Score submitted! Rank in {mode}: {current_rank}, Overall: {overall_rank}"
        }

    def delete_record(self, record_id: int) -> bool:
        """Delete a specific record by ID"""
        scores = self.load_scores()
        initial_length = len(scores)
        scores = [r for r in scores if r["id"] != record_id]
        if len(scores) < initial_length:
            self.save_scores(scores)
            self.recalc_all_ranks()
            return True
        return False

    def delete_player_records(self, name: str) -> bool:
        """Delete all records of a player"""
        scores = self.load_scores()
        initial_length = len(scores)
        scores = [r for r in scores if r["name"].lower() != name.lower()]
        if len(scores) < initial_length:
            self.save_scores(scores)
            self.recalc_all_ranks()
            return True
        return False

    def clear_all(self) -> None:
        """Clear all records"""
        self.save_scores([])
        self.recalc_all_ranks()

    # ------------------ Player Stats ------------------
    def get_player_stats(self, name: str) -> Dict:
        """Get detailed stats for a player"""
        scores = self.load_scores()
        player_records = [r for r in scores if r["name"].lower() == name.lower()]
        if not player_records:
            return {"error": "Player not found"}

        total_games = len(player_records)
        highest_score = max(r["score"] for r in player_records)
        total_tokens = sum(r["tokens"] for r in player_records)
        average_score = sum(r["score"] for r in player_records) // total_games
        average_tokens = total_tokens // total_games
        best_mode_record = max(player_records, key=lambda x: x["score"])
        best_mode = best_mode_record["mode"]
        best_score = best_mode_record["score"]

        mode_stats = {}
        for mode in ["normal", "multiplayer", "rage"]:
            mode_records = [r for r in player_records if r["mode"] == mode]
            if mode_records:
                mode_stats[mode] = {
                    "games_played": len(mode_records),
                    "highest_score": max(r["score"] for r in mode_records),
                    "total_tokens": sum(r["tokens"] for r in mode_records)
                }

        recent_games = sorted(player_records, key=lambda x: x["date"], reverse=True)[:5]

        # Current ranks
        all_ranks = self.read_records("all")
        normal_ranks = self.read_records("normal")
        multiplayer_ranks = self.read_records("multiplayer")
        rage_ranks = self.read_records("rage")

        return {
            "name": name,
            "total_games": total_games,
            "highest_score": highest_score,
            "average_score": average_score,
            "total_tokens": total_tokens,
            "average_tokens": average_tokens,
            "best_mode": best_mode,
            "best_score": best_score,
            "mode_stats": mode_stats,
            "current_ranks": {
                "all": next((r["rank"] for r in all_ranks if r["name"].lower() == name.lower()), None),
                "normal": next((r["rank"] for r in normal_ranks if r["name"].lower() == name.lower()), None),
                "multiplayer": next((r["rank"] for r in multiplayer_ranks if r["name"].lower() == name.lower()), None),
                "rage": next((r["rank"] for r in rage_ranks if r["name"].lower() == name.lower()), None)
            },
            "recent_games": recent_games
        }

    def get_player_high_scores(self, name: str) -> Dict:
        """Get highest scores per mode for a player"""
        scores = self.load_scores()
        player_records = [r for r in scores if r["name"].lower() == name.lower()]
        if not player_records:
            return {"error": "Player not found"}
        high_scores = {}
        for mode in ["normal", "multiplayer", "rage"]:
            mode_scores = [r["score"] for r in player_records if r["mode"] == mode]
            high_scores[mode] = max(mode_scores) if mode_scores else 0
        high_scores["all"] = max(r["score"] for r in player_records)
        return {"name": name, "high_scores": high_scores}

    def get_total_tokens(self) -> int:
        """Get total tokens collected across all games"""
        scores = self.load_scores()
        return sum(r.get("tokens", 0) for r in scores)

    # ------------------ Leaderboard ------------------
    def get_leaderboard(self, mode: str = "all", top_n: Optional[int] = None) -> List[Dict]:
        scores = self.read_records(mode)
        return scores[:top_n] if top_n else scores

    def display_leaderboard(self, mode: str = "all", top_n: int = 10) -> None:
        leaderboard = self.get_leaderboard(mode, top_n)
        print(f"\n{'='*60}")
        print(f"LEADERBOARD - {mode.upper()} MODE")
        print(f"{'='*60}")
        print(f"{'Rank':<6} {'Name':<15} {'Score':<10} {'Tokens':<10} {'Mode':<12} {'Date':<12}")
        print(f"{'-'*60}")
        for record in leaderboard:
            date_obj = datetime.fromisoformat(record["date"])
            formatted_date = date_obj.strftime("%m/%d/%Y")
            print(f"{record['rank']:<6} {record['name']:<15} {record['score']:<10} "
                  f"{record['tokens']:<10} {record['mode']:<12} {formatted_date:<12}")
        if not leaderboard:
            print("No records found for this mode")
        print(f"{'='*60}")


# ------------------ Global Instance & Convenience Functions ------------------
scoreboard = Scoreboard()

def submit_score(name: str, score: int, tokens: int, mode: str) -> Dict:
    return scoreboard.submit_score(name, score, tokens, mode)

def display_leaderboard(mode: str = "all", top_n: int = 10) -> None:
    scoreboard.display_leaderboard(mode, top_n)

def get_player_stats(name: str) -> Dict:
    return scoreboard.get_player_stats(name)

def get_player_high_scores(name: str) -> Dict:
    return scoreboard.get_player_high_scores(name)

def get_total_tokens() -> int:
    return scoreboard.get_total_tokens()

def clear_all() -> None:
    scoreboard.clear_all()
