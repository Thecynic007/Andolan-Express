import pygame
import sys
from scoreboard import scoreboard

# -------------------------
# COLORS
# -------------------------
WHITE = (255, 255, 255)
BLUE = (0, 100, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (150, 150, 150)
LIGHT_BLUE = (100, 150, 255)
ORANGE = (255, 165, 0)
DARK_ORANGE = (255, 140, 0)
YELLOW = (255, 255, 0)

# -------------------------
# FONTS
# -------------------------
pygame.font.init()
title_font = pygame.font.SysFont("Arial", 64, bold=True)
menu_font = pygame.font.SysFont("Arial", 32)
info_font = pygame.font.SysFont("Arial", 24)
font = pygame.font.SysFont("Arial", 18)

# -------------------------
# BUTTON CLASS
# -------------------------
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
        
    def is_clicked(self, pos, click):
        return self.rect.collidepoint(pos) and click

# -------------------------
# TEXT INPUT CLASS
# -------------------------
class TextInput:
    def __init__(self, x, y, width, height, max_length=15):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = ""
        self.active = False
        self.max_length = max_length
        self.color = (240, 240, 240)
        self.active_color = WHITE
        self.text_color = BLACK
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                return "submit"
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                if len(self.text) < self.max_length:
                    self.text += event.unicode
        return None
    
    def draw(self, surface):
        # Draw background
        pygame.draw.rect(surface, self.color, self.rect, border_radius=8)
        
        # Draw border (Blue if active, Black if inactive)
        border_color = BLUE if self.active else BLACK
        pygame.draw.rect(surface, border_color, self.rect, 3, border_radius=8)
        
        # Draw text
        if self.text:
            text_surf = menu_font.render(self.text, True, self.text_color)
            text_rect = text_surf.get_rect(midleft=(self.rect.x + 10, self.rect.centery))
            surface.blit(text_surf, text_rect)
        
        # Draw cursor if active
        if self.active:
            # Calculate cursor position
            if self.text:
                text_surf = menu_font.render(self.text, True, self.text_color)
                cursor_x = self.rect.x + 10 + text_surf.get_width() + 2
            else:
                cursor_x = self.rect.x + 10
                
            # Blink cursor every 500ms
            if pygame.time.get_ticks() % 1000 < 500:
                pygame.draw.line(surface, BLACK, (cursor_x, self.rect.y + 10), 
                               (cursor_x, self.rect.bottom - 10), 2)

# -------------------------
# NAME ENTRY SCREEN CLASS
# -------------------------
class NameEntryScreen:
    def __init__(self, score, tokens, mode):
        self.score = int(score)
        self.tokens = int(tokens)
        self.mode = mode
        
        # Input field
        self.name_input = TextInput(1000//2 - 150, 300, 300, 50)
        self.name_input.active = True
        
        # Buttons
        self.submit_button = Button(1000//2 - 150, 380, 300, 60, "SUBMIT", GREEN, (0, 200, 0))
        self.cancel_button = Button(1000//2 - 150, 460, 300, 60, "SKIP", LIGHT_BLUE, BLUE)
        
        self.message = ""
        self.message_timer = 0

    def handle_events(self, event):
        if event.type == pygame.QUIT:
            return "quit"
            
        input_result = self.name_input.handle_event(event)
        if input_result == "submit":
            return self._handle_submit()
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.submit_button.is_clicked(mouse_pos, True):
                return self._handle_submit()
            elif self.cancel_button.is_clicked(mouse_pos, True):
                return "main_menu"
                
        return None

    def _handle_submit(self):
        name = self.name_input.text.strip()
        if not name:
            self.message = "Please enter your name!"
            self.message_timer = pygame.time.get_ticks()
            return None
            
        scoreboard.submit_score(name, self.score, self.tokens, self.mode)
        return "done"

    def update(self):
        if self.message and pygame.time.get_ticks() - self.message_timer > 3000:
            self.message = ""
        
        mouse_pos = pygame.mouse.get_pos()
        self.submit_button.check_hover(mouse_pos)
        self.cancel_button.check_hover(mouse_pos)

    def draw(self, surface):
        # Semi-transparent overlay
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))
        
        # Title
        title = title_font.render("NEW RECORD!", True, YELLOW)
        surface.blit(title, (surface.get_width()//2 - title.get_width()//2, 100))
        
        # Stats
        stats_text = menu_font.render(f"Score: {self.score} | Tokens: {self.tokens}", True, WHITE)
        surface.blit(stats_text, (surface.get_width()//2 - stats_text.get_width()//2, 180))
        
        # Name input label
        label = menu_font.render("Enter Name:", True, WHITE)
        surface.blit(label, (surface.get_width()//2 - label.get_width()//2, 260))
        
        self.name_input.draw(surface)
        self.submit_button.draw(surface)
        self.cancel_button.draw(surface)
        
        if self.message:
            msg = info_font.render(self.message, True, RED)
            surface.blit(msg, (surface.get_width()//2 - msg.get_width()//2, 520))

# -------------------------
# GAME OVER SCREEN CLASS
# -------------------------
class GameOverScreen:
    def __init__(self, score, tokens_collected, mode_name="NORMAL", leaderboard=None):
        self.score = score
        self.tokens_collected = tokens_collected
        self.mode_name = mode_name
        self.leaderboard = leaderboard  # Kept for compatibility but we use global scoreboard
        
        self.buttons = [
            Button(1000//2 - 150, 300, 300, 60, "PLAY AGAIN", GREEN, (0, 200, 0)),
            Button(1000//2 - 150, 380, 300, 60, "MAIN MENU", LIGHT_BLUE, BLUE),
            Button(1000//2 - 150, 460, 300, 60, "QUIT", RED, (200, 0, 0))
        ]
        
        self.name_entry = NameEntryScreen(score, tokens_collected, mode_name)
        self.show_name_entry = True

    def handle_events(self, event):
        if self.show_name_entry:
            result = self.name_entry.handle_events(event)
            if result == "quit":
                return "quit"
            elif result == "done":
                self.show_name_entry = False
            elif result == "main_menu":
                return "main_menu"
            return None
            
        if event.type == pygame.QUIT:
            return "quit"
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                for i, button in enumerate(self.buttons):
                    if button.is_clicked(event.pos, True):
                        if i == 0: return "restart"
                        elif i == 1: return "main_menu"
                        elif i == 2: return "quit"
        return None

    def update(self):
        if self.show_name_entry:
            self.name_entry.update()
        else:
            mouse_pos = pygame.mouse.get_pos()
            for button in self.buttons:
                button.check_hover(mouse_pos)

    def draw(self, surface):
        if self.show_name_entry:
            self.name_entry.draw(surface)
        else:
            # Draw standard game over screen
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            surface.blit(overlay, (0, 0))
            
            title = title_font.render("GAME OVER", True, RED)
            surface.blit(title, (surface.get_width()//2 - title.get_width()//2, 100))
            
            score_text = menu_font.render(f"Final Score: {int(self.score)}", True, WHITE)
            tokens_text = menu_font.render(f"Tokens Collected: {self.tokens_collected}", True, YELLOW)
            
            surface.blit(score_text, (surface.get_width()//2 - score_text.get_width()//2, 180))
            surface.blit(tokens_text, (surface.get_width()//2 - tokens_text.get_width()//2, 230))
            
            for button in self.buttons:
                button.draw(surface)
            
# -------------------------
class MultiplayerGameOverScreen:
    def __init__(self, p1_score, p1_tokens, p2_score, p2_tokens):
        self.p1_score = int(p1_score)
        self.p1_tokens = int(p1_tokens)
        self.p2_score = int(p2_score)
        self.p2_tokens = int(p2_tokens)
        
        # Inputs
        self.p1_input = TextInput(200, 300, 250, 50)
        self.p2_input = TextInput(550, 300, 250, 50)
        self.p1_input.active = True  # Start with P1 active
        
        self.p1_submitted = False
        self.p2_submitted = False
        
        self.buttons = [
            Button(1000//2 - 150, 450, 300, 60, "SUBMIT SCORES", GREEN, (0, 200, 0)),
            Button(1000//2 - 150, 530, 300, 60, "SKIP", LIGHT_BLUE, BLUE)
        ]
        
        self.message = ""
        self.message_timer = 0

    def handle_events(self, event):
        if event.type == pygame.QUIT:
            return "quit"
            
        # Handle inputs
        if not self.p1_submitted:
            self.p1_input.handle_event(event)
        if not self.p2_submitted:
            self.p2_input.handle_event(event)
            
        # Mouse clicks for switching focus
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.p1_input.rect.collidepoint(event.pos) and not self.p1_submitted:
                self.p1_input.active = True
                self.p2_input.active = False
            elif self.p2_input.rect.collidepoint(event.pos) and not self.p2_submitted:
                self.p2_input.active = True
                self.p1_input.active = False
                
            # Buttons
            if event.button == 1:
                for i, button in enumerate(self.buttons):
                    if button.is_clicked(event.pos, True):
                        if i == 0: # Submit
                            return self._handle_submit()
                        elif i == 1: # Main Menu
                            return "main_menu"
        
        # Tab switching
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                if self.p1_input.active:
                    self.p1_input.active = False
                    self.p2_input.active = True
                else:
                    self.p1_input.active = True
                    self.p2_input.active = False
                    
        return None

    def _handle_submit(self):
        p1_name = self.p1_input.text.strip()
        p2_name = self.p2_input.text.strip()
        
        if not p1_name or not p2_name:
            self.message = "Both players must enter names!"
            self.message_timer = pygame.time.get_ticks()
            return None
            
        # Save scores
        scoreboard.submit_score(p1_name, self.p1_score, self.p1_tokens, "MULTIPLAYER")
        scoreboard.submit_score(p2_name, self.p2_score, self.p2_tokens, "MULTIPLAYER")
        
        return "main_menu"

    def update(self):
        if self.message and pygame.time.get_ticks() - self.message_timer > 3000:
            self.message = ""
            
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.check_hover(mouse_pos)

    def draw(self, surface):
        # Overlay
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        surface.blit(overlay, (0, 0))
        
        # Title
        title = title_font.render("MULTIPLAYER GAME OVER", True, YELLOW)
        surface.blit(title, (surface.get_width()//2 - title.get_width()//2, 50))
        
        # Player 1 Section (Left)
        p1_title = menu_font.render("PLAYER 1", True, LIGHT_BLUE)
        surface.blit(p1_title, (325 - p1_title.get_width()//2, 150))
        
        p1_score = font.render(f"Score: {self.p1_score}", True, WHITE)
        surface.blit(p1_score, (325 - p1_score.get_width()//2, 200))
        
        self.p1_input.draw(surface)
        
        # Player 2 Section (Right)
        p2_title = menu_font.render("PLAYER 2", True, LIGHT_BLUE)
        surface.blit(p2_title, (675 - p2_title.get_width()//2, 150))
        
        p2_score = font.render(f"Score: {self.p2_score}", True, WHITE)
        surface.blit(p2_score, (675 - p2_score.get_width()//2, 200))
        
        self.p2_input.draw(surface)
        
        # Buttons
        for button in self.buttons:
            button.draw(surface)
            
        # Message
        if self.message:
            msg = info_font.render(self.message, True, RED)
            surface.blit(msg, (surface.get_width()//2 - msg.get_width()//2, 410))