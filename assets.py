import pygame
from utils import safe_load
from settings import WIDTH, HEIGHT
from entities import StreetLamp, Dustbin, Police, TearGas, Token, Ambulance, Barricade, Tree, Road

# Global asset variables
intro_image = None
road_tile = None
run_frames = []
lamp_left = None
lamp_right = None
dustbin_img = None
police_img = None
teargas_sprites = []
tree_img = None
token_img = None
barricade1_img = None
barricade2_img = None
ambulance_frames = []
danger_img = None
dead1_img = None
dead3_img = None
blood_img = None
mute_icon = None
unmute_icon = None
MUSIC_MENU = None
MUSIC_MODE = None
MUSIC_RAGE = None
pause_icon = None

def load_assets():
    """Load all game assets. Must be called after pygame.display.set_mode()."""
    global intro_image, road_tile, run_frames, lamp_left, lamp_right
    global dustbin_img, police_img, teargas_sprites, tree_img, token_img
    global barricade1_img, barricade2_img, ambulance_frames, danger_img
    global dead1_img, dead3_img, blood_img

    # -------------------------
    # LOAD ASSETS
    # -------------------------
    intro_image = safe_load("Intro_img.png")
    if intro_image:
        intro_image = pygame.transform.scale(intro_image, (WIDTH, HEIGHT))

    global end_screen_img
    end_screen_img = safe_load("Assets/Sprites/Rage Mode/End_screen.png")
    if end_screen_img:
        end_screen_img = pygame.transform.scale(end_screen_img, (WIDTH, HEIGHT))

    road_tile = safe_load("Assets/Tiles/road11.png")
    if road_tile:
        road_tile = pygame.transform.scale(road_tile, (WIDTH, Road.TILE_HEIGHT))
    else:
        road_tile = pygame.Surface((WIDTH, Road.TILE_HEIGHT))
        road_tile.fill((50, 50, 50))

    CHAR_SIZE = 75
    run_frames = []
    for i in range(1, 4):
        path = f"Assets/Sprites/Main Character/Boy{i}.png"
        frame = safe_load(path)
        if frame:
            run_frames.append(pygame.transform.scale(frame, (CHAR_SIZE, CHAR_SIZE)))

    lamp_left = safe_load("Assets/Sprites/Road Objects/Street_lamp_left.png")
    lamp_right = safe_load("Assets/Sprites/Road Objects/Street_lamp_right.png")
    if lamp_left:
        lamp_left = pygame.transform.scale(lamp_left, (StreetLamp.SIZE, StreetLamp.SIZE))
    if lamp_right:
        lamp_right = pygame.transform.scale(lamp_right, (StreetLamp.SIZE, StreetLamp.SIZE))

    dustbin_img = safe_load("Assets/Sprites/Road Objects/Dustbin.png")
    if dustbin_img:
        dustbin_img = pygame.transform.scale(dustbin_img, (Dustbin.SIZE, Dustbin.SIZE))

    police_img = safe_load("Assets/Sprites/Enemy Characters/Police1.png")
    if not police_img:
        police_img = safe_load("Assets/Sprites/Enemy Characters/Police1.png")
    if police_img:
        police_img = pygame.transform.scale(police_img, (Police.SIZE, Police.SIZE))

    # Load tear gas animation frames
    teargas_img1 = safe_load("Assets/Sprites/Enemy Characters/Tear_gas1.png")
    teargas_img2 = safe_load("Assets/Sprites/Enemy Characters/Tear_gas2.png")
    teargas_sprites = []
    if teargas_img1:
        teargas_sprites.append(pygame.transform.scale(teargas_img1, (TearGas.SIZE, TearGas.SIZE)))
    if teargas_img2:
        teargas_sprites.append(pygame.transform.scale(teargas_img2, (TearGas.SIZE, TearGas.SIZE)))
    # Fallback if images not found
    if not teargas_sprites:
        teargas_fallback = safe_load("Assets/Sprites/Enemy Characters/Tear_gas.png")
        if teargas_fallback:
            teargas_sprites.append(pygame.transform.scale(teargas_fallback, (TearGas.SIZE, TearGas.SIZE)))

    # Load tree sprite (fallback chain)
    tree_img = safe_load("Assets/Sprites/Road Objects/Tree.png")
    if not tree_img:
        tree_img = safe_load("Assets/Sprites/Road Objects/Tree_.png")
    if not tree_img:
        tree_img = safe_load("Assets/Sprites/Road Objects/Tree_1.png")
    if tree_img:
        tree_img = pygame.transform.scale(tree_img, (Tree.SIZE, Tree.SIZE))

    # Load token sprite (fallback to Flags/Points.png if Token.png missing)
    token_img = safe_load("Assets/Sprites/Flags/Token.png")
    if not token_img:
        token_img = safe_load("Assets/Sprites/Flags/Token.png")
    if token_img:
        token_img = pygame.transform.scale(token_img, (Token.SIZE, Token.SIZE))

    # Load barricade sprites
    barricade1_img = safe_load("Assets/Sprites/Road Objects/Barricade 1.png")
    barricade2_img = safe_load("Assets/Sprites/Road Objects/Barricade 2.png")
    if barricade1_img:
        barricade1_img = pygame.transform.scale(barricade1_img, (Barricade.SIZE, Barricade.SIZE))
    if barricade2_img:
        barricade2_img = pygame.transform.scale(barricade2_img, (Barricade.SIZE, Barricade.SIZE))

    # Load ambulance assets
    ambulance_frames = []
    amb1 = safe_load("Assets/Sprites/Vehicles/Ambulance_1.png")
    amb2 = safe_load("Assets/Sprites/Vehicles/Ambulance_1.1.png") or safe_load("Assets/Sprites/Vehicles/Ambulance_1.1png")
    if amb1:
        ambulance_frames.append(pygame.transform.scale(amb1, (Ambulance.SIZE, Ambulance.SIZE)))
    if amb2:
        ambulance_frames.append(pygame.transform.scale(amb2, (Ambulance.SIZE, Ambulance.SIZE)))
    # Load Rage Mode Decorations
    dead1_img = safe_load("Assets/Sprites/Rage Mode/Dead1.png")
    if not dead1_img:
        dead1_img = safe_load("Assets/Sprites/Story/Dead1.png")
    if not dead1_img:
        dead1_img = safe_load("Assets/Sprites/Enemy Characters/Dead1.png")
    
    dead3_img = safe_load("Assets/Sprites/Rage Mode/Dead3.png")
    if not dead3_img:
        dead3_img = safe_load("Assets/Sprites/Story/Dead3.png")
    if not dead3_img:
        dead3_img = safe_load("Assets/Sprites/Enemy Characters/Dead3.png")
        
    blood_img = safe_load("Assets/Sprites/Rage Mode/Blood.png")
    if not blood_img:
        blood_img = safe_load("Assets/Sprites/Story/Blood.png")
    if not blood_img:
        blood_img = safe_load("Assets/Sprites/Effects/Blood.png")
        
    # Load Danger Sign
    danger_img = safe_load("Assets/Sprites/Road Objects/Danger.png")
    if danger_img:
        danger_img = pygame.transform.scale(danger_img, (60, 60))

    # Scale decorations if loaded
    if dead1_img:
        dead1_img = pygame.transform.scale(dead1_img, (140, 140))
    if dead3_img:
        dead3_img = pygame.transform.scale(dead3_img, (140, 140))
    if blood_img:
        blood_img = pygame.transform.scale(blood_img, (70, 70))

    # Load Music Paths
    global MUSIC_MENU, MUSIC_MODE, MUSIC_RAGE
    MUSIC_MENU = "Assets/Music/Menu.mp3"
    MUSIC_MODE = "Assets/Music/Mode.mp3"
    MUSIC_RAGE = "Assets/Music/Rage.mp3"
    
    # Mute Icon (Placeholder)
    global mute_icon, unmute_icon
    mute_icon = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.circle(mute_icon, (200, 200, 200), (20, 20), 18)
    pygame.draw.circle(mute_icon, (50, 50, 50), (20, 20), 18, 2)
    # Draw a speaker shape
    pygame.draw.rect(mute_icon, (50, 50, 50), (10, 15, 5, 10))
    pygame.draw.polygon(mute_icon, (50, 50, 50), [(15, 15), (25, 10), (25, 30), (15, 25)])
    
    unmute_icon = mute_icon.copy()
    # Add sound waves for unmute
    pygame.draw.arc(unmute_icon, (50, 50, 50), (20, 10, 15, 20), -1.0, 1.0, 2)
    
    # Add cross for mute
    mute_icon_crossed = mute_icon.copy()
    pygame.draw.line(mute_icon_crossed, (255, 0, 0), (10, 10), (30, 30), 3)
    pygame.draw.line(mute_icon_crossed, (255, 0, 0), (30, 10), (10, 30), 3)
    
    mute_icon = mute_icon_crossed # Set the crossed one as mute_icon

    # Create placeholder pause icon
    global pause_icon
    pause_icon = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.circle(pause_icon, (200, 200, 200), (20, 20), 18)
    pygame.draw.circle(pause_icon, (50, 50, 50), (20, 20), 18, 2)
    pygame.draw.rect(pause_icon, (50, 50, 50), (12, 10, 6, 20))
    pygame.draw.rect(pause_icon, (50, 50, 50), (22, 10, 6, 20))
    
    return {
        'intro_image': intro_image,
        'road_tile': road_tile,
        'run_frames': run_frames,
        'lamp_left': lamp_left,
        'lamp_right': lamp_right,
        'dustbin_img': dustbin_img,
        'police_img': police_img,
        'teargas_sprites': teargas_sprites,
        'tree_img': tree_img,
        'token_img': token_img,
        'barricade1_img': barricade1_img,
        'barricade2_img': barricade2_img,
        'ambulance_frames': ambulance_frames,
        'danger_img': danger_img,
        'dead1_img': dead1_img,
        'dead3_img': dead3_img,
        'blood_img': blood_img,
        'mute_icon': mute_icon,
        'unmute_icon': unmute_icon,
        'pause_icon': pause_icon,
        'music_menu': MUSIC_MENU,
        'music_mode': MUSIC_MODE,
        'music_rage': MUSIC_RAGE
    }
