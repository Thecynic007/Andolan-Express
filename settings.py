import pygame

# -------------------------
# INITIAL SETUP
# -------------------------
WIDTH, HEIGHT = 1000, 750
FPS = 60
CHAR_SIZE = 75

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
PURPLE = (128, 0, 128)


# -------------------------
# FONTS
# -------------------------
pygame.font.init()

title_font = pygame.font.SysFont("Arial", 64, bold=True)
menu_font = pygame.font.SysFont("Arial", 36)
info_font = pygame.font.SysFont("Arial", 24)
font = pygame.font.SysFont("Arial", 18)

def init_fonts():
    """
    Re-initialize fonts if needed (e.g. after video mode change if that affects fonts, 
    though usually not needed for SysFont).
    Returns a dict for convenience.
    """
    return {
        'title_font': title_font,
        'menu_font': menu_font,
        'info_font': info_font,
        'font': font
    }
