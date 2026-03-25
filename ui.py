import pygame
from settings import *

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
        
        # Initialize font here if not globally available, or import from settings/assets
        # For now, we'll create a local font or assume it's passed/available.
        # Ideally, fonts should be in assets or settings.
        # Let's use a default font for now to ensure independence.
        self.font = pygame.font.SysFont("Arial", 36)
        
    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=12)
        pygame.draw.rect(surface, BLACK, self.rect, 3, border_radius=12)
        
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
        
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
        self.font = pygame.font.SysFont("Arial", 36) # Local font
        
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
            text_surf = self.font.render(self.text, True, self.text_color)
            text_rect = text_surf.get_rect(midleft=(self.rect.x + 10, self.rect.centery))
            surface.blit(text_surf, text_rect)
        
        # Draw cursor if active
        if self.active:
            # Calculate cursor position
            if self.text:
                text_surf = self.font.render(self.text, True, self.text_color)
                cursor_x = self.rect.x + 10 + text_surf.get_width() + 2
            else:
                cursor_x = self.rect.x + 10
                
            # Blink cursor every 500ms
            if pygame.time.get_ticks() % 1000 < 500:
                pygame.draw.line(surface, BLACK, (cursor_x, self.rect.y + 10), 
                               (cursor_x, self.rect.bottom - 10), 2)
