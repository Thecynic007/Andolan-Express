import pygame
import sys
import os

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 1000, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Andolan Express")
clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 100, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (150, 150, 150)
LIGHT_BLUE = (100, 150, 255)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)

# Fonts
title_font = pygame.font.SysFont("Arial", 64, bold=True)
menu_font = pygame.font.SysFont("Arial", 36)
info_font = pygame.font.SysFont("Arial", 24)

# Safe Image Loader
def safe_load(path):
    if os.path.exists(path):
        return pygame.image.load(path).convert_alpha()
    else:
        print(f" Missing: {path}")
        return None

# Load background image for main menu
menu_bg = safe_load("Assets/Backgrounds/menu_bg.png") or safe_load("Intro_img.png")
if menu_bg:
    menu_bg = pygame.transform.scale(menu_bg, (WIDTH, HEIGHT))
else:
    menu_bg = None

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

class MainMenu:
    def __init__(self):
        self.buttons = [
            Button(WIDTH//2 - 150, 250, 300, 60, "START GAME", GREEN, (0, 200, 0)),
            Button(WIDTH//2 - 150, 330, 300, 60, "MODES", ORANGE, (255, 140, 0)),
            Button(WIDTH//2 - 150, 410, 300, 60, "HOW TO PLAY", LIGHT_BLUE, BLUE),
            Button(WIDTH//2 - 150, 490, 300, 60, "QUIT", RED, (200, 0, 0))
        ]
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    for i, button in enumerate(self.buttons):
                        if button.is_clicked(event.pos, True):
                            if i == 0:  # START GAME
                                return "start_game"
                            elif i == 1:  # MODES
                                return "modes"
                            elif i == 2:  # HOW TO PLAY
                                return "how_to_play"
                            elif i == 3:  # QUIT
                                pygame.quit()
                                sys.exit()
        return "menu"
    
    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.check_hover(mouse_pos)
    
    def draw(self, surface):
        # Draw background
        if menu_bg:
            surface.blit(menu_bg, (0, 0))
        else:
            surface.fill((50, 50, 80))  # Dark blue background if no image
        
        # Draw title
        title_text = title_font.render("ANDOLAN EXPRESS", True, WHITE)
        title_shadow = title_font.render("ANDOLAN EXPRESS", True, BLACK)
        title_rect = title_text.get_rect(center=(WIDTH//2, 150))
        
        # Draw shadow effect
        surface.blit(title_shadow, (title_rect.x + 3, title_rect.y + 3))
        surface.blit(title_text, title_rect)
        
        # Draw buttons
        for button in self.buttons:
            button.draw(surface)
        
        # Draw footer
        footer_text = info_font.render("Use ARROW KEYS or A/D to move | Avoid obstacles and collect tokens!", True, WHITE)
        surface.blit(footer_text, (WIDTH//2 - footer_text.get_width()//2, HEIGHT - 50))

class ModesScreen:
    def __init__(self):
        self.back_button = Button(WIDTH//2 - 100, HEIGHT - 100, 200, 50, "BACK", LIGHT_BLUE, BLUE)
        self.mode_buttons = [
            Button(WIDTH//2 - 150, 200, 300, 60, "NORMAL MODE", GREEN, (0, 200, 0)),
            Button(WIDTH//2 - 150, 280, 300, 60, "50+ MODE", YELLOW, (200, 200, 0)),
            Button(WIDTH//2 - 150, 360, 300, 60, "100+ MODE", ORANGE, (255, 140, 0)),
            Button(WIDTH//2 - 150, 440, 300, 60, "150+ MODE", RED, (200, 0, 0))
        ]
        self.mode_descriptions = [
            "Standard gameplay with all features",
            "Unlock at 50 tokens - Increased difficulty",
            "Unlock at 100 tokens - Extreme challenge", 
            "Unlock at 150 tokens - Ultimate test"
        ]
        self.tokens_collected = 0  # You'll need to load this from saved data
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.back_button.is_clicked(event.pos, True):
                        return "menu"
                    for i, button in enumerate(self.mode_buttons):
                        if button.is_clicked(event.pos, True):
                            if i == 0:  # NORMAL MODE
                                return "start_normal"
                            elif i == 1 and self.tokens_collected >= 50:  # 50+ MODE
                                return "start_50"
                            elif i == 2 and self.tokens_collected >= 100:  # 100+ MODE
                                return "start_100"
                            elif i == 3 and self.tokens_collected >= 150:  # 150+ MODE
                                return "start_150"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"
        return "modes"
    
    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        self.back_button.check_hover(mouse_pos)
        for button in self.mode_buttons:
            button.check_hover(mouse_pos)
    
    def draw(self, surface):
        # Draw semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))  # Black with transparency
        surface.blit(overlay, (0, 0))
        
        # Draw title
        title_text = title_font.render("SELECT MODE", True, WHITE)
        surface.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 50))
        
        # Draw tokens info
        tokens_text = info_font.render(f"Tokens Collected: {self.tokens_collected}", True, YELLOW)
        surface.blit(tokens_text, (WIDTH//2 - tokens_text.get_width()//2, 120))
        
        # Draw mode buttons and descriptions
        for i, (button, description) in enumerate(zip(self.mode_buttons, self.mode_descriptions)):
            # Check if mode is locked
            if i == 0:  # Normal mode is always available
                button.draw(surface)
            elif i == 1 and self.tokens_collected >= 50:  # 50+ mode
                button.draw(surface)
            elif i == 2 and self.tokens_collected >= 100:  # 100+ mode
                button.draw(surface)
            elif i == 3 and self.tokens_collected >= 150:  # 150+ mode
                button.draw(surface)
            else:
                # Draw locked button
                locked_color = (100, 100, 100)
                pygame.draw.rect(surface, locked_color, button.rect, border_radius=12)
                pygame.draw.rect(surface, BLACK, button.rect, 3, border_radius=12)
                text_surf = menu_font.render(button.text, True, (150, 150, 150))
                text_rect = text_surf.get_rect(center=button.rect.center)
                surface.blit(text_surf, text_rect)
            
            # Draw description
            desc_text = info_font.render(description, True, WHITE)
            surface.blit(desc_text, (WIDTH//2 - desc_text.get_width()//2, button.rect.bottom + 10))
            
            # Draw lock icon for locked modes
            if i > 0:
                if (i == 1 and self.tokens_collected < 50) or \
                   (i == 2 and self.tokens_collected < 100) or \
                   (i == 3 and self.tokens_collected < 150):
                    lock_text = info_font.render(f"Requires {i*50}+ tokens", True, RED)
                    surface.blit(lock_text, (WIDTH//2 - lock_text.get_width()//2, button.rect.bottom + 35))
        
        # Draw back button
        self.back_button.draw(surface)

class HowToPlayScreen:
    def __init__(self):
        self.back_button = Button(WIDTH//2 - 100, HEIGHT - 100, 200, 50, "BACK", LIGHT_BLUE, BLUE)
        self.instructions = [
            "CONTROLS:",
            "• LEFT ARROW or A - Move Left",
            "• RIGHT ARROW or D - Move Right",
            "• ESC - Pause Game",
            "",
            "OBJECTIVE:",
            "• Run as far as possible without getting caught",
            "• Avoid police, tear gas, barricades, and ambulances",
            "• Collect tokens to unlock new modes",
            "",
            "OBSTACLES:",
            "• Police - High damage, knocks you back",
            "• Tear Gas - Continuous damage in cloud",
            "• Barricades - Blocks your path",
            "• Ambulances - Fast moving, high damage",
            "• Trees & Lamps - Block movement",
            "",
            "TIP: Watch for ambulance warning signs!"
        ]
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and self.back_button.is_clicked(event.pos, True):
                    return "menu"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"
        return "how_to_play"
    
    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        self.back_button.check_hover(mouse_pos)
    
    def draw(self, surface):
        # Draw semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))  # Black with transparency
        surface.blit(overlay, (0, 0))
        
        # Draw title
        title_text = title_font.render("HOW TO PLAY", True, WHITE)
        surface.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 50))
        
        # Draw instructions
        y_offset = 150
        for line in self.instructions:
            if line.startswith("•"):
                text_surf = info_font.render(line, True, LIGHT_BLUE)
            elif line.endswith(":"):
                text_surf = menu_font.render(line, True, GREEN)
            else:
                text_surf = info_font.render(line, True, WHITE)
            
            surface.blit(text_surf, (WIDTH//2 - text_surf.get_width()//2, y_offset))
            y_offset += 35
        
        # Draw back button
        self.back_button.draw(surface)

def show_main_menu():
    """Main function to show the main menu and handle navigation"""
    current_screen = "menu"
    main_menu = MainMenu()
    how_to_play = HowToPlayScreen()
    modes_screen = ModesScreen()
    
    running = True
    while running:
        # Handle events based on current screen
        if current_screen == "menu":
            action = main_menu.handle_events()
            if action == "start_game":
                return "start_normal"  # Default to normal mode
            elif action == "modes":
                current_screen = "modes"
            elif action == "how_to_play":
                current_screen = "how_to_play"
        
        elif current_screen == "modes":
            action = modes_screen.handle_events()
            if action == "menu":
                current_screen = "menu"
            elif action.startswith("start_"):
                return action  # Return the selected mode
        
        elif current_screen == "how_to_play":
            action = how_to_play.handle_events()
            if action == "menu":
                current_screen = "menu"
        
        # Update
        if current_screen == "menu":
            main_menu.update()
        elif current_screen == "modes":
            modes_screen.update()
        elif current_screen == "how_to_play":
            how_to_play.update()
        
        # Draw
        if current_screen == "menu":
            main_menu.draw(screen)
        elif current_screen == "modes":
            modes_screen.draw(screen)
        elif current_screen == "how_to_play":
            how_to_play.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
    return "quit"

if __name__ == "__main__":
    result = show_main_menu()
    print(f"Selected mode: {result}")