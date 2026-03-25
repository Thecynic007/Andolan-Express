import os
import pygame

# -------------------------
# SAFE IMAGE LOADER
# -------------------------
def safe_load(path):
    if os.path.exists(path):
        return pygame.image.load(path).convert_alpha()
    else:
        print(f" Missing: {path}")
        return None

def draw_text_centered(surface, text, font, color, y_pos):
    text_surf = font.render(text, True, color)
    text_rect = text_surf.get_rect(center=(surface.get_width() // 2, y_pos))
    surface.blit(text_surf, text_rect)
