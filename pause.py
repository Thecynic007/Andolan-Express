import pygame
import sys

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 100, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
LIGHT_BLUE = (100, 150, 255)
ORANGE = (255, 165, 0)
DARK_ORANGE = (255, 140, 0)

# Fonts
title_font = pygame.font.SysFont("Arial", 64, bold=True)
menu_font = pygame.font.SysFont("Arial", 36)

class Button:
    def __init__(self, x, y, width, height, text, color=LIGHT_BLUE, hover_color=BLUE, text_color=WHITE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        
    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=12)
        pygame.draw.rect(surface, BLACK, self.rect, 3, border_radius=12)
        
        text_surf = menu_font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
        
    def is_clicked(self, pos, click):
        return self.rect.collidepoint(pos) and click

class PauseScreen:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.buttons = [
            Button(screen_width//2 - 150, 250, 300, 60, "RESUME", GREEN, (0, 200, 0)),
            Button(screen_width//2 - 150, 330, 300, 60, "RESTART", LIGHT_BLUE, BLUE),
            Button(screen_width//2 - 150, 410, 300, 60, "MAIN MENU", ORANGE, DARK_ORANGE),
            Button(screen_width//2 - 150, 490, 300, 60, "QUIT GAME", RED, (200, 0, 0))
        ]
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "resume"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for i, button in enumerate(self.buttons):
                        if button.is_clicked(event.pos, True):
                            if i == 0:  # RESUME
                                return "resume"
                            elif i == 1:  # RESTART
                                return "restart"
                            elif i == 2:  # MAIN MENU
                                return "main_menu"
                            elif i == 3:  # QUIT
                                return "quit"
        return "pause"
    
    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.check_hover(mouse_pos)
    
    def draw(self, surface):
        # Draw semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Black with transparency
        surface.blit(overlay, (0, 0))
        
        # Draw title
        title_text = title_font.render("GAME PAUSED", True, WHITE)
        title_rect = title_text.get_rect(center=(self.screen_width//2, 150))
        surface.blit(title_text, title_rect)
        
        # Draw buttons
        for button in self.buttons:
            button.draw(surface)

def show_pause_screen(screen, clock, screen_width=1000, screen_height=750):
    """
    Show the pause screen and return the user's choice
    
    Args:
        screen: The pygame surface to draw on
        clock: The pygame clock for frame rate control
        screen_width: Width of the screen (default 1000)
        screen_height: Height of the screen (default 750)
    
    Returns:
        str: One of "resume", "restart", "main_menu", or "quit"
    """
    pause_screen = PauseScreen(screen_width, screen_height)
    
    while True:
        action = pause_screen.handle_events()
        
        if action != "pause":
            return action
            
        pause_screen.update()
        pause_screen.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)

# Test function - you can run this file directly to test the pause screen
if __name__ == "__main__":
    pygame.init()
    test_screen = pygame.display.set_mode((1000, 750))
    test_clock = pygame.time.Clock()
    pygame.display.set_caption("Pause Screen Test")
    
    # Fill with a test background
    test_screen.fill((50, 100, 150))
    pygame.display.flip()
    
    # Show pause screen
    result = show_pause_screen(test_screen, test_clock)
    print(f"Pause screen returned: {result}")
    
    pygame.quit()