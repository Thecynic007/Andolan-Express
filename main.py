import pygame
import sys
from settings import WIDTH, HEIGHT
from game import show_main_menu, run_game
from story import StoryMode

import assets
from scoreboard import scoreboard

if __name__ == "__main__":
    # Initialize Pygame
    pygame.init()
    pygame.mixer.init()
    
    # Set up display
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Andolan Express")
    
    # Load assets
    assets.load_assets()
    
    # Run Story Mode
    story = StoryMode()
    story.start_music()
    story_running = True
    while story_running:
        result = story.handle_events(pygame.event.wait())
        if result == "quit":
            pygame.quit()
            sys.exit()
        elif result == "skip" or result == "done":
            story_running = False
            
        story.update()
        story.draw(screen)
        pygame.display.flip()
    
    # Stop story music before main menu
    pygame.mixer.music.stop()
    
    # Main execution loop
    tokens_collected = scoreboard.get_total_tokens()
    running = True
    
    while running:
        # Show main menu
        result = show_main_menu(tokens_collected)
        
        # Unpack result (it can be 2 or 3 values)
        action = result[0]
        tokens_collected = result[1]
        multiplayer_game = result[2] if len(result) > 2 else None
        
        if action == "quit":
            running = False
        elif action == "play_story":
            # Replay Story Mode
            story = StoryMode()
            story.start_music()
            story_running = True
            while story_running:
                result = story.handle_events(pygame.event.wait())
                if result == "quit":
                    pygame.quit()
                    sys.exit()
                elif result == "skip" or result == "done":
                    story_running = False
                    
                story.update()
                story.draw(screen)
                pygame.display.flip()
            
            # Stop story music before returning to main menu
            pygame.mixer.music.stop()
            
        elif action.startswith("start_"):
            # Run the game
            game_result = run_game(action, tokens_collected, multiplayer_game)
            
            # Unpack game result
            status = game_result[0]
            tokens_collected = game_result[1]
            
            if status == "quit":
                running = False
            # If status is "menu", loop continues and shows menu again
            
    pygame.quit()
    sys.exit()