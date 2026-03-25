from scoreboard import scoreboard

def add_bonus_tokens():
    print("Adding 500 Starter Bonus tokens...")
    # Submit a score with 0 points but 500 tokens
    scoreboard.submit_score("Starter Bonus", 0, 500, "bonus")
    
    total = scoreboard.get_total_tokens()
    print(f"Done! New Total Tokens: {total}")

if __name__ == "__main__":
    add_bonus_tokens()
