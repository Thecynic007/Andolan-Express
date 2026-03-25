import os
import json

def test_scoreboard():
    scores_file = os.path.abspath("scores.json")
    print(f"Testing scoreboard with file: {scores_file}")
    
    # Check if file exists
    if not os.path.exists(scores_file):
        print("Scores file does not exist. Creating new one...")
        try:
            with open(scores_file, 'w') as f:
                json.dump([], f)
            print("Created new scores file.")
        except Exception as e:
            print(f"Error creating scores file: {e}")
            return False
    
    # Check file permissions
    try:
        print("\nTesting file permissions...")
        # Test reading
        with open(scores_file, 'r') as f:
            data = json.load(f)
            print(f"Successfully read {len(data)} scores from file.")
        
        # Test writing
        test_data = [{"id": 1, "name": "Test", "score": 100, "tokens": 10, "mode": "normal", "date": "2025-11-21T15:20:00.000000"}]
        with open(scores_file, 'w') as f:
            json.dump(test_data, f, indent=4)
        print("Successfully wrote test data to file.")
        
        # Restore original data
        with open(scores_file, 'w') as f:
            json.dump(data, f, indent=4)
        print("Restored original data.")
        
        return True
        
    except Exception as e:
        print(f"Error testing file permissions: {e}")
        return False

if __name__ == "__main__":
    if test_scoreboard():
        print("\n✅ Scoreboard test passed successfully!")
    else:
        print("\n❌ Scoreboard test failed. Please check the error messages above.")
