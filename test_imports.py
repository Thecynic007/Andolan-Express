import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

try:
    print("Importing settings...")
    import settings
    print("Settings imported.")

    print("Importing game...")
    import game
    print("Game imported.")
    
    print("Checking game functions...")
    if hasattr(game, 'show_main_menu') and hasattr(game, 'run_game'):
        print("Game functions found.")
    else:
        print("ERROR: Game functions missing.")
        
    print("Importing main...")
    import main
    print("Main imported.")
    
    print("All imports successful.")

except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
