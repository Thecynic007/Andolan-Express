import pygame
import os
import random
from settings import *
from utils import safe_load
from entities import Player, StreetLamp, Dustbin, Police, TearGas, Barricade, Tree, Road, Token, Ambulance
from managers import LampManager, DustbinManager, PoliceManager, TearGasManager, BarricadeManager, TreeManager, TokenManager, AmbulanceManager, DecorationManager
from screens import (
    PauseScreen, GameOverScreen, MultiplayerGameOverScreen, 
    MainMenu, ModesScreen, HowToPlayScreen, LeaderboardScreen, 
    MultiplayerLobbyScreen, MultiplayerJoinScreen
)
from leaderboard_manager import Leaderboard
import assets
import pygame.mixer

# -------------------------
# MUSIC MANAGER
# -------------------------
class MusicManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MusicManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
    
    def __init__(self):
        if self.initialized:
            return
        self.initialized = True
        self.current_track = None
        self.is_muted = False
        self.volume = 0.5
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.set_volume(self.volume)
        except:
            pass
        
        # Load icons
        self.mute_icon = assets.mute_icon
        self.unmute_icon = assets.unmute_icon
        self.rect = pygame.Rect(20, 20, 40, 40) # Top left position
        
    def set_position(self, x, y):
        self.rect.topleft = (x, y)
        
    def play(self, track_name):
        if self.is_muted:
            return
            
        track_path = None
        if track_name == "menu":
            track_path = assets.MUSIC_MENU
        elif track_name == "mode":
            track_path = assets.MUSIC_MODE
        elif track_name == "rage":
            track_path = assets.MUSIC_RAGE
            
        if track_path and (track_path != self.current_track or not pygame.mixer.music.get_busy()):
            try:
                pygame.mixer.music.load(track_path)
                pygame.mixer.music.play(-1) # Loop indefinitely
                self.current_track = track_path
            except Exception as e:
                print(f"Error playing music: {e}")
                
    def stop(self):
        pygame.mixer.music.stop()
        self.current_track = None
        
    def toggle_mute(self):
        self.is_muted = not self.is_muted
        if self.is_muted:
            pygame.mixer.music.pause()
        else:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.unpause()
            else:
                # Restart current track if it was stopped or never started
                if self.current_track:
                    try:
                        pygame.mixer.music.load(self.current_track)
                        pygame.mixer.music.play(-1)
                    except:
                        pass
                        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click
                if self.rect.collidepoint(event.pos):
                    self.toggle_mute()
                    return True
        return False
        
    def draw(self, surface):
        icon = self.mute_icon if self.is_muted else self.unmute_icon
        if icon:
            surface.blit(icon, self.rect)

# Initialize global music manager
music_manager = None

def get_music_manager():
    global music_manager
    if music_manager is None:
        music_manager = MusicManager()
    return music_manager

# -------------------------
# GAME INITIALIZATION FUNCTION
# -------------------------
def initialize_game(width=WIDTH, height=HEIGHT, player_frames=None):
    """Initialize all game objects and return them"""
    if player_frames is None:
        player_frames = assets.run_frames
        
    road = Road(width, height, assets.road_tile)
    lamp_manager = LampManager(width, height, assets.lamp_left, assets.lamp_right)
    dustbin_manager = DustbinManager(width, height, assets.dustbin_img)
    police_manager = PoliceManager(width, height, assets.police_img)
    teargas_manager = TearGasManager(width, height, assets.teargas_sprites)
    barricade_manager = BarricadeManager(width, height, assets.barricade1_img, assets.barricade2_img)
    tree_manager = TreeManager(width, height, assets.tree_img, lamp_manager)
    token_manager = TokenManager(width, height, assets.token_img)
    ambulance_manager = AmbulanceManager(width, height, assets.ambulance_frames, assets.danger_img)
    decoration_manager = DecorationManager(width, height, assets.dead1_img, assets.dead3_img, assets.blood_img)
    player = Player(width // 2 - CHAR_SIZE // 2, height - CHAR_SIZE - 50, player_frames)
    
    return {
        'road': road,
        'lamp_manager': lamp_manager,
        'dustbin_manager': dustbin_manager,
        'police_manager': police_manager,
        'teargas_manager': teargas_manager,
        'barricade_manager': barricade_manager,
        'tree_manager': tree_manager,
        'token_manager': token_manager,
        'ambulance_manager': ambulance_manager,
        'decoration_manager': decoration_manager,
        'player': player
    }

# -------------------------
# MULTIPLAYER GAME FUNCTION
# -------------------------
def run_multiplayer_game(multiplayer_game, tokens_collected=0):
    """Multiplayer version of the game"""
    screen = pygame.display.get_surface()
    clock = pygame.time.Clock()
    
    # Initialize game objects
    game_objects = initialize_game()
    
    # Unpack game objects
    road = game_objects['road']
    lamp_manager = game_objects['lamp_manager']
    dustbin_manager = game_objects['dustbin_manager']
    police_manager = game_objects['police_manager']
    teargas_manager = game_objects['teargas_manager']
    barricade_manager = game_objects['barricade_manager']
    tree_manager = game_objects['tree_manager']
    token_manager = game_objects['token_manager']
    ambulance_manager = game_objects['ambulance_manager']
    player = game_objects['player']
    
    # Multiplayer setup
    player_id = multiplayer_game.player_id
    is_host = multiplayer_game.is_host
    
    # Game state variables
    running = True
    paused = False
    game_over = False
    scroll_offset = 0
    score = 0
    base_road_speed = 5
    road_speed = base_road_speed
    last_speed_increase_score = 0
    last_generation_increase_score = 0
    game_start_time = pygame.time.get_ticks()
    leaderboard = Leaderboard()
    game_over_screen = None
    
    # Multiplayer mode adjustments
    mode_name = "MULTIPLAYER"
    player.max_health = 80
    player.health = 80
    
    # Main game loop
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if game_over:
                # Handle game over screen events
                if game_over_screen is None:
                    game_over_screen = GameOverScreen(score, tokens_collected, mode_name, leaderboard)
                result = game_over_screen.handle_events(event)
                if result == "restart":
                    # Restart game
                    multiplayer_game.disconnect()
                    return run_multiplayer_game(multiplayer_game, tokens_collected)
                elif result == "main_menu":
                    multiplayer_game.disconnect()
                    return "menu", tokens_collected
                elif result == "quit":
                    running = False
                continue
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Show pause screen
                    pause_screen = PauseScreen()
                    paused = True
                    while paused:
                        pause_event = pygame.event.wait()
                        if pause_event.type == pygame.QUIT:
                            running = False
                            paused = False
                        result = pause_screen.handle_events(pause_event)
                        if result == "resume":
                            paused = False
                        elif result == "restart":
                            # Restart game
                            multiplayer_game.disconnect()
                            return run_multiplayer_game(multiplayer_game, tokens_collected)
                        elif result == "main_menu":
                            multiplayer_game.disconnect()
                            return "menu", tokens_collected
                        elif result == "quit":
                            running = False
                            paused = False
                        
                        pause_screen.update()
                        # Draw game in background
                        screen.fill(WHITE)
                        road.draw(screen)
                        lamp_manager.draw(screen)
                        dustbin_manager.draw(screen)
                        ambulance_manager.draw(screen)
                        police_manager.draw(screen)
                        teargas_manager.draw(screen)
                        tree_manager.draw(screen)
                        barricade_manager.draw(screen)
                        token_manager.draw(screen)
                        player.draw(screen)
                        # Draw pause screen overlay
                        pause_screen.draw(screen)
                        pygame.display.flip()
                        clock.tick(60)
                if event.key == pygame.K_q:
                    running = False

        if paused or game_over:
            continue

        # Update multiplayer state
        multiplayer_game.update_player({
            'x': player.x,
            'y': player.y,
            'health': player.health,
            'score': score
        })
        
        # Get other players' data
        opponent_data = multiplayer_game.get_opponent_data()
        
        keys = pygame.key.get_pressed()
        moving = False
        lateral_movement = 0

        # LEFT / RIGHT MOVEMENT ONLY (no forward/backward controls)
        player_speed = player.walk_speed  # Use consistent speed
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            lateral_movement = -player_speed
            moving = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            lateral_movement = player_speed
            moving = True

        # UPDATE PLAYER (cooldowns, knockback, stun, etc.)
        delta_time = clock.get_time()  # Get time since last frame in milliseconds
        player.update_stun(delta_time)
        player.update(WIDTH)
        
        # COLLISION CHECK (LATERAL)
        player_rect = player.get_rect()
        
        # Only allow lateral movement if not stunned and not in knockback
        if not player.is_stunned and abs(player.knockback_x) < 0.1:
            if lateral_movement != 0:
                if lamp_manager.check_collision(player_rect, lateral_movement=lateral_movement):
                    lateral_movement = 0
                elif dustbin_manager.check_collision(player_rect, lateral_movement=lateral_movement):
                    lateral_movement = 0
                elif police_manager.check_collision(player_rect, lateral_movement=lateral_movement):
                    lateral_movement = 0
                # Allow overlap with tear gas; do not block lateral movement
                elif barricade_manager.check_collision(player_rect, lateral_movement=lateral_movement):
                    lateral_movement = 0
                elif tree_manager.check_collision(player_rect, lateral_movement=lateral_movement):
                    lateral_movement = 0

            player.x += lateral_movement
            player.x = max(0, min(WIDTH - player.size, player.x))
        
        # AUTOMATIC CONTINUOUS FORWARD MOVEMENT
        # Player always moves forward - no controls needed
        # Stop scrolling if player is stunned
        current_road_speed = 0 if player.is_stunned else road_speed
        current_time = pygame.time.get_ticks() - game_start_time
        road.update(current_road_speed)
        lamp_manager.update(current_road_speed)
        dustbin_manager.update(current_road_speed)
        # Pass score, time, and managers to police and teargas managers for collision checking
        police_manager.update(current_road_speed, score, current_time, lamp_manager, dustbin_manager, teargas_manager, barricade_manager, tree_manager, ambulance_manager)
        teargas_manager.update(current_road_speed, score, current_time, lamp_manager, dustbin_manager, police_manager, barricade_manager, tree_manager, ambulance_manager)
        barricade_manager.update(current_road_speed, current_time, lamp_manager, dustbin_manager, police_manager, teargas_manager, tree_manager, ambulance_manager)
        ambulance_manager.update(current_road_speed, score, current_time, lamp_manager, dustbin_manager, police_manager, teargas_manager, barricade_manager, tree_manager, "start_normal")
        tree_manager.update(current_road_speed)
        token_manager.update(current_road_speed, current_time, lamp_manager, dustbin_manager, police_manager, teargas_manager, barricade_manager, tree_manager, ambulance_manager)
        scroll_offset += current_road_speed
        moving = True if not player.is_stunned else False
        score += 0.2 if not player.is_stunned else 0  # Score increases continuously, but not when stunned
        
        # Update score in multiplayer
        multiplayer_game.update_score(score)
        
        # Check for collision with police after objects have moved - handle knockback and damage
        player_rect_after_move = player.get_rect()
        colliding_police = police_manager.check_damage_collision(player_rect_after_move)
        if colliding_police:
            # Calculate knockback direction (push player away from police)
            player_center_x = player.x + player.size // 2
            player_center_y = player.y + player.size // 2
            police_center_x = colliding_police.x + Police.SIZE // 2
            police_center_y = colliding_police.y + Police.SIZE // 2
            
            # Calculate direction vector
            dx = player_center_x - police_center_x
            dy = player_center_y - police_center_y
            distance = max(1, (dx**2 + dy**2)**0.5)  # Avoid division by zero
            
            # Normalize and scale knockback (reduced strength, smoother)
            knockback_strength = 4
            knockback_x = (dx / distance) * knockback_strength
            knockback_y = (dy / distance) * knockback_strength
            
            # Push player away to prevent overlap
            player.x += knockback_x
            player.y += knockback_y
            
            # Keep player within bounds and visible on screen
            player.x = max(0, min(WIDTH - player.size, player.x))
            player.y = max(HEIGHT - player.size - 50, min(HEIGHT - player.size - 10, player.y))  # Keep player visible on screen
            
            # Apply damage with knockback and stun
            player.take_damage(Police.DAMAGE, knockback_x, knockback_y, apply_stun=True)
        
        # Check for collision with tear gas (full overlap detection)
        if teargas_manager.check_damage_collision(player_rect_after_move):
            player.take_damage(TearGas.DAMAGE)

        # Check for collision with ambulance - damage scales with difficulty
        colliding_ambulance = ambulance_manager.check_collision(player_rect_after_move)
        if colliding_ambulance and not colliding_ambulance.has_collided:
            damage = colliding_ambulance.get_damage("start_normal")
            # Calculate knockback direction (push player away from ambulance to the side)
            player_center_x = player.x + player.size // 2
            player_center_y = player.y + player.size // 2
            ambulance_center_x = colliding_ambulance.x + Ambulance.SIZE // 2
            ambulance_center_y = colliding_ambulance.y + Ambulance.SIZE // 2
            
            # Calculate direction vector
            dx = player_center_x - ambulance_center_x
            dy = player_center_y - ambulance_center_y
            distance = max(1, (dx**2 + dy**2)**0.5)  # Avoid division by zero
            
            # Strong knockback to the side (more horizontal than vertical)
            knockback_strength = 8
            # Emphasize horizontal knockback (push to side)
            knockback_x = (dx / distance) * knockback_strength * 1.5  # 1.5x horizontal emphasis
            knockback_y = (dy / distance) * knockback_strength * 0.5  # 0.5x vertical emphasis
            
            # Ensure knockback is always to the side
            if abs(knockback_x) < 2:
                # If very little horizontal movement, force it
                knockback_x = 8 if dx > 0 else -8
            
            # Push player away to prevent overlap
            player.x += knockback_x
            player.y += knockback_y
            
            # Keep player within bounds and visible on screen
            player.x = max(0, min(WIDTH - player.size, player.x))
            player.y = max(HEIGHT - player.size - 50, min(HEIGHT - player.size - 10, player.y))
            
            # Apply damage with knockback (no stun for ambulance)
            player.take_damage(damage, knockback_x, knockback_y, apply_stun=False)
            colliding_ambulance.has_collided = True
        
        # Check for collision with barricade - stop player and apply damage
        if barricade_manager.check_damage_collision(player_rect_after_move):
            # Find all colliding barricades
            colliding_barricades = []
            for barricade in barricade_manager.barricades:
                if player_rect_after_move.colliderect(barricade.get_rect()):
                    colliding_barricades.append(barricade)
            
            # Calculate knockback for stun effect
            knockback_x = 0
            knockback_y = 0
            
            # If player is between two barricades (side-by-side), move to nearest side
            handled_two_barricades = False
            if len(colliding_barricades) >= 2:
                # Sort barricades by x position
                colliding_barricades.sort(key=lambda b: b.x)
                left_barricade = colliding_barricades[0]
                right_barricade = colliding_barricades[-1]
                
                # Check if barricades are horizontally adjacent (side-by-side)
                # They should be close in y position and the right one should be near the left one's right edge
                y_distance = abs(left_barricade.y - right_barricade.y)
                x_gap = right_barricade.x - (left_barricade.x + Barricade.SIZE)
                
                # If barricades are side-by-side (close in y, small x gap)
                if y_distance < Barricade.SIZE and x_gap < 50:  # 50 pixel tolerance for gap
                    player_center_x = player.x + player.size // 2
                    left_edge = left_barricade.x + Barricade.SIZE
                    right_edge = right_barricade.x
                    
                    # Determine which side is closer
                    dist_to_left = abs(player_center_x - left_edge)
                    dist_to_right = abs(player_center_x - right_edge)
                    
                    if dist_to_left < dist_to_right:
                        # Move player to left side of left barricade
                        player.x = left_barricade.x - player.size - 5  # 5 pixel gap
                        knockback_x = -5  # Small knockback for stun
                    else:
                        # Move player to right side of right barricade
                        player.x = right_barricade.x + Barricade.SIZE + 5  # 5 pixel gap
                        knockback_x = 5  # Small knockback for stun
                    
                    # Keep player within bounds
                    player.x = max(0, min(WIDTH - player.size, player.x))
                    handled_two_barricades = True
            
            # Single barricade collision or multiple non-adjacent - push player away completely
            if not handled_two_barricades:
                for barricade in colliding_barricades:
                    barricade_rect = barricade.get_rect()
                    player_rect = player.get_rect()
                    
                    # Calculate push direction (push player away from barricade)
                    player_center_x = player.x + player.size // 2
                    player_center_y = player.y + player.size // 2
                    barricade_center_x = barricade.x + Barricade.SIZE // 2
                    barricade_center_y = barricade.y + Barricade.SIZE // 2
                    
                    # Calculate direction vector
                    dx = player_center_x - barricade_center_x
                    dy = player_center_y - barricade_center_y
                    distance = max(1, (dx**2 + dy**2)**0.5)  # Avoid division by zero
                    
                    # Push player completely outside barricade - ensure no overlap
                    # Calculate minimum distance needed to separate
                    player_half_width = player.collision_size // 2
                    barricade_half_width = Barricade.SIZE // 2
                    min_separation = player_half_width + barricade_half_width + 5  # 5 pixel buffer
                    
                    # Push player away with enough force to prevent overlap
                    push_strength = max(15, min_separation)  # Strong push to prevent overlap
                    knockback_x = (dx / distance) * push_strength
                    knockback_y = (dy / distance) * push_strength
                    
                    # Apply push
                    player.x += knockback_x
                    player.y += knockback_y
                    
                    # Ensure player is completely outside barricade rect
                    new_player_rect = player.get_rect()
                    if new_player_rect.colliderect(barricade_rect):
                        # If still overlapping, push more aggressively
                        if player_center_x < barricade_center_x:
                            player.x = barricade.x - player.size - 5
                            knockback_x = -5
                        else:
                            player.x = barricade.x + Barricade.SIZE + 5
                            knockback_x = 5
                        if player_center_y < barricade_center_y:
                            player.y = barricade.y - player.size - 5
                            knockback_y = -5
                        else:
                            player.y = barricade.y + Barricade.SIZE + 5
                            knockback_y = 5
                    
                    # Keep player within bounds and visible
                    player.x = max(0, min(WIDTH - player.size, player.x))
                    player.y = max(HEIGHT - player.size - 50, min(HEIGHT - player.size - 10, player.y))
                    break
            
            # Apply damage with knockback and stun
            player.take_damage(Barricade.DAMAGE, knockback_x, knockback_y, apply_stun=True)
        
        # Resolve overlap with street lamps from all sides (push player away slightly)
        player_rect_after_move = player.get_rect()
        for lamp in lamp_manager.lamps:
            # Check both lamp parts
            pole_rect = lamp.get_pole_rect()
            top_rect = lamp.get_top_rect()
            collided_rect = None
            if player_rect_after_move.colliderect(pole_rect):
                collided_rect = pole_rect
            elif player_rect_after_move.colliderect(top_rect):
                collided_rect = top_rect
            if collided_rect:
                # Push player away from center of collided rect
                player_center_x = player.x + player.size // 2
                player_center_y = player.y + player.size // 2
                rect_center_x = collided_rect.x + collided_rect.width // 2
                rect_center_y = collided_rect.y + collided_rect.height // 2
                dx = player_center_x - rect_center_x
                dy = player_center_y - rect_center_y
                dist = max(1, (dx*dx + dy*dy) ** 0.5)
                push = 5
                player.x += (dx / dist) * push
                player.y += (dy / dist) * push
                player.x = max(0, min(WIDTH - player.size, player.x))
                player.y = max(HEIGHT - player.size - 50, min(HEIGHT - player.size - 10, player.y))
                # Recompute rect after push for subsequent checks
                player_rect_after_move = player.get_rect()
        
        # Resolve overlap with dustbins from all sides (push player away slightly)
        player_rect_after_move = player.get_rect()
        for dustbin in dustbin_manager.dustbins:
            d_rect = dustbin.get_rect()
            if player_rect_after_move.colliderect(d_rect):
                player_center_x = player.x + player.size // 2
                player_center_y = player.y + player.size // 2
                rect_center_x = d_rect.x + d_rect.width // 2
                rect_center_y = d_rect.y + d_rect.height // 2
                dx = player_center_x - rect_center_x
                dy = player_center_y - rect_center_y
                dist = max(1, (dx*dx + dy*dy) ** 0.5)
                push = 5
                player.x += (dx / dist) * push
                player.y += (dy / dist) * push
                player.x = max(0, min(WIDTH - player.size, player.x))
                player.y = max(HEIGHT - player.size - 50, min(HEIGHT - player.size - 10, player.y))
                player_rect_after_move = player.get_rect()

        # Resolve overlap with trees from all sides (push player away slightly)
        player_rect_after_move = player.get_rect()
        for t in tree_manager.trees:
            t_rect = t.get_rect()
            if player_rect_after_move.colliderect(t_rect):
                player_center_x = player.x + player.size // 2
                player_center_y = player.y + player.size // 2
                rect_center_x = t_rect.x + t_rect.width // 2
                rect_center_y = t_rect.y + t_rect.height // 2
                dx = player_center_x - rect_center_x
                dy = player_center_y - rect_center_y
                dist = max(1, (dx*dx + dy*dy) ** 0.5)
                push = 5
                player.x += (dx / dist) * push
                player.y += (dy / dist) * push
                player.x = max(0, min(WIDTH - player.size, player.x))
                player.y = max(HEIGHT - player.size - 50, min(HEIGHT - player.size - 10, player.y))
                player_rect_after_move = player.get_rect()
        
        # Final check: Ensure player never overlaps with barricades (even after knockback)
        player_rect_final = player.get_rect()
        for barricade in barricade_manager.barricades:
            barricade_rect = barricade.get_rect()
            if player_rect_final.colliderect(barricade_rect):
                # Push player completely outside barricade
                player_center_x = player.x + player.size // 2
                player_center_y = player.y + player.size // 2
                barricade_center_x = barricade.x + Barricade.SIZE // 2
                barricade_center_y = barricade.y + Barricade.SIZE // 2
                
                # Determine which side to push to
                dx = player_center_x - barricade_center_x
                dy = player_center_y - barricade_center_y
                
                # Push to nearest edge
                if abs(dx) > abs(dy):
                    # Push horizontally
                    if dx < 0:
                        player.x = barricade.x - player.size - 5
                    else:
                        player.x = barricade.x + Barricade.SIZE + 5
                else:
                    # Push vertically
                    if dy < 0:
                        player.y = barricade.y - player.size - 5
                    else:
                        player.y = barricade.y + Barricade.SIZE + 5
                
                # Keep player within bounds
                player.x = max(0, min(WIDTH - player.size, player.x))
                player.y = max(HEIGHT - player.size - 50, min(HEIGHT - player.size - 10, player.y))
                player_rect_final = player.get_rect()  # Update for next iteration

        # Collect tokens on overlap
        collected_now = token_manager.collect_if_overlap(player.get_rect())
        if collected_now:
            tokens_collected += collected_now
        
        # Check if player is stuck in barricade or tree (lamp) - game over condition
        player_rect = player.get_rect()
        if barricade_manager.check_player_stuck(player_rect, player.y, HEIGHT):
            game_over = True  # Game over - player stuck in barricade
        
        # CHECK IF PLAYER IS ALIVE
        if not player.is_alive():
            game_over = True

        if game_over:
            # Draw game over screen
            game_over_screen = GameOverScreen(score, tokens_collected, mode_name, leaderboard)
            game_over_screen.update()
            
            # Draw the final game state in background
            screen.fill(WHITE)
            road.draw(screen)
            lamp_manager.draw(screen)
            dustbin_manager.draw(screen)
            ambulance_manager.draw(screen)
            police_manager.draw(screen)
            teargas_manager.draw(screen)
            tree_manager.draw(screen)
            barricade_manager.draw(screen)
            token_manager.draw(screen)
            player.draw(screen)
            
            # Draw opponent if available
            if opponent_data:
                pygame.draw.rect(screen, RED, (opponent_data['x'], opponent_data['y'], player.size, player.size))
                opponent_text = font.render("Opponent", True, BLACK)
                screen.blit(opponent_text, (opponent_data['x'], opponent_data['y'] - 20))
            
            # Draw game over screen overlay
            game_over_screen.draw(screen)
            pygame.display.flip()
            continue

        # SCORE-BASED SPEED INCREASE - GRADUAL AND BALANCED
        # Increase speed every 250 points, but cap at reasonable maximum
        speed_increase_threshold = 250
        max_road_speed = 12  # Maximum speed cap for multiplayer

        if score >= last_speed_increase_score + speed_increase_threshold:
            if road_speed < max_road_speed:
                road_speed += 0.3  # Small, gradual increase
                last_speed_increase_score = score
        
        # SCORE-BASED GENERATION FREQUENCY INCREASE (smooth, gentle)
        if score >= 300:
            gen_increase_threshold = 300 if last_generation_increase_score < 300 else last_generation_increase_score + 300
            if score >= gen_increase_threshold:
                # Slightly decrease spawn intervals with safe minimums for smoothness
                new_police_interval = max(1200, police_manager.spawn_interval - 100)
                police_manager.set_spawn_interval(new_police_interval)
                # Barricades ramp too
                if hasattr(barricade_manager, "set_spawn_interval"):
                    new_barricade_interval = max(2000, barricade_manager.spawn_interval - 100)
                    barricade_manager.set_spawn_interval(new_barricade_interval)
                # Also decrease tear gas gap
                new_teargas_gap = max(450, teargas_manager.current_gap - 30)
                teargas_manager.set_gap(new_teargas_gap)
                last_generation_increase_score = gen_increase_threshold

        # ANIMATION
        player.update_animation(moving)

        # -------------------------
        # DRAW EVERYTHING
        # -------------------------
        screen.fill(WHITE)
        road.draw(screen)
        lamp_manager.draw(screen)
        dustbin_manager.draw(screen)
        ambulance_manager.draw(screen)
        police_manager.draw(screen)
        teargas_manager.draw(screen)
        tree_manager.draw(screen)
        barricade_manager.draw(screen)
        token_manager.draw(screen)
        player.draw(screen)
        
        # Draw opponent if available
        if opponent_data:
            pygame.draw.rect(screen, RED, (opponent_data['x'], opponent_data['y'], player.size, player.size))
            opponent_text = font.render("Opponent", True, BLACK)
            health_text = font.render(f"HP: {opponent_data.get('health', 0)}", True, RED)
            screen.blit(opponent_text, (opponent_data['x'], opponent_data['y'] - 40))
            screen.blit(health_text, (opponent_data['x'], opponent_data['y'] - 20))

        # HUD
        fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, BLACK)
        score_text = font.render(f"Score: {int(score)}", True, BLACK)
        health_text = font.render(f"Health: {int(player.health)}/{player.max_health}", True, BLACK)
        tokens_text = font.render(f"Tokens: {tokens_collected}", True, BLACK)
        mode_text = font.render(f"Mode: {mode_name}", True, BLACK)
        speed_text = font.render(f"Speed: {road_speed:.1f}", True, BLACK)
        screen.blit(fps_text, (10, 10))
        screen.blit(score_text, (10, 30))
        screen.blit(health_text, (10, 50))
        screen.blit(mode_text, (10, 70))
        screen.blit(speed_text, (10, 90))
        # Top-right tokens
        screen.blit(tokens_text, (WIDTH - 10 - tokens_text.get_width(), 10))
        
        # Multiplayer info
        player_role = "HOST" if is_host else "CLIENT"
        role_text = font.render(f"Role: {player_role}", True, BLUE)
        screen.blit(role_text, (WIDTH - 10 - role_text.get_width(), 30))
        
        # Health bar visualization
        bar_width = 200
        bar_height = 20
        bar_x = 10
        bar_y = 115
        health_percentage = player.health / player.max_health
        health_color = (255, 0, 0) if health_percentage < 0.3 else (255, 165, 0) if health_percentage < 0.6 else (0, 255, 0)
        
        # Background bar
        pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
        # Health bar
        pygame.draw.rect(screen, health_color, (bar_x, bar_y, int(bar_width * health_percentage), bar_height))
        # Border
        pygame.draw.rect(screen, BLACK, (bar_x, bar_y, bar_width, bar_height), 2)

        pygame.display.flip()
        clock.tick(60)

    multiplayer_game.disconnect()
    return "quit", tokens_collected

# -------------------------
# SPLIT SCREEN GAME FUNCTION
# -------------------------
def run_split_screen_game(tokens_collected=0):
    """Local multiplayer game (Shared Screen)"""
    screen = pygame.display.get_surface()
    clock = pygame.time.Clock()

    # Load girl frames
    girl_run_frames = []
    # Try loading from Assets/Sprites/Main Character/
    base_path = "Assets/Sprites/Main Character"
    for i in range(1, 4):
        img = safe_load(os.path.join(base_path, f"Girl{i}.png"))
        if img:
            girl_run_frames.append(pygame.transform.scale(img, (CHAR_SIZE, CHAR_SIZE)))
            
    if not girl_run_frames:
        # Fallback to boy frames if girl frames not found
        girl_run_frames = assets.run_frames

    # Full Map Dimensions (Same as Screen)
    full_map_width = WIDTH
    full_map_height = HEIGHT
    
    # Initialize P1 (Boy) - Shared Map
    # We only need one set of game objects (managers) for the shared world.
    game_objects = initialize_game(width=full_map_width, height=full_map_height, player_frames=assets.run_frames)
    
    # Unpack game objects
    road = game_objects['road']
    lamp_manager = game_objects['lamp_manager']
    dustbin_manager = game_objects['dustbin_manager']
    police_manager = game_objects['police_manager']
    teargas_manager = game_objects['teargas_manager']
    barricade_manager = game_objects['barricade_manager']
    tree_manager = game_objects['tree_manager']
    token_manager = game_objects['token_manager']
    ambulance_manager = game_objects['ambulance_manager']
    p1_player = game_objects['player']
    
    # Create Player 2 (Girl) manually and add to game
    # P1 (Boy) starts on LEFT (A/D)
    # P2 (Girl) starts on RIGHT (Arrows)
    p1_player.x = WIDTH // 2 - 150 # P1 Left
    p1_player.y = HEIGHT - 150 # Align P1 with P2
    p2_player = Player(WIDTH // 2 + 50, HEIGHT - 150, girl_run_frames) # P2 Right
    
    # Game state
    running = True
    game_over = False
    p1_score = 0
    p2_score = 0
    base_road_speed = 5
    road_speed = base_road_speed
    game_start_time = pygame.time.get_ticks()
    last_speed_increase_score = 0
    last_generation_increase_score = 0
    
    # Track tokens for this session separately for each player
    p1_session_tokens = 0
    p2_session_tokens = 0
    
    # Multiplayer Game Over Screen instance
    game_over_screen = None
    
    # Pause Screen instance
    pause_screen = None
    paused = False
    
    # Play multiplayer music (same as mode)
    music_manager = get_music_manager()
    music_manager.set_position(20, 20)
    music_manager.play("mode")

    def draw_hud(surface, player, score, tokens, player_label="P1", x_offset=0):
        # HUD drawn on the main screen
        
        # Health Bar
        bar_width = 150
        bar_height = 15
        bar_x = x_offset + 10
        bar_y = 50
        
        health_percentage = max(0, player.health / player.max_health)
        health_color = (255, 0, 0) if health_percentage < 0.3 else (255, 165, 0) if health_percentage < 0.6 else (0, 255, 0)
        
        # Background bar
        pygame.draw.rect(surface, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
        # Health bar
        pygame.draw.rect(surface, health_color, (bar_x, bar_y, int(bar_width * health_percentage), bar_height))
        # Border
        pygame.draw.rect(surface, BLACK, (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Text Info
        label_text = font.render(player_label, True, BLACK)
        score_text = font.render(f"Score: {int(score)}", True, BLACK)
        tokens_text = font.render(f"Tokens: {tokens}", True, BLACK)
        
        surface.blit(label_text, (bar_x, bar_y - 20))
        surface.blit(score_text, (x_offset + 10, 10))
        
        # Draw tokens below health bar
        surface.blit(tokens_text, (x_offset + 10, bar_y + 20))
        
        # Draw pause icon (Beside Score)
        if assets.pause_icon:
            surface.blit(assets.pause_icon, (110, 10))

        # Draw mute button (Beside Pause Icon)
        music_manager.set_position(155, 10)
        music_manager.draw(surface)

    def resolve_collisions(player, objects):
        # Helper to resolve collisions for a player
        
        # 1. Barricade Damage & Knockback
        if objects['barricade_manager'].check_damage_collision(player.get_rect()):
            # Calculate knockback direction
            knockback_x = 0
            knockback_y = 0
            player_center_x = player.x + player.size // 2
            player_center_y = player.y + player.size // 2
            
            # Find the colliding barricade
            for barricade in objects['barricade_manager'].barricades:
                if player.get_rect().colliderect(barricade.get_rect()):
                    barricade_center_x = barricade.x + Barricade.SIZE // 2
                    barricade_center_y = barricade.y + Barricade.SIZE // 2
                    dx = player_center_x - barricade_center_x
                    dy = player_center_y - barricade_center_y
                    
                    if abs(dx) > abs(dy):
                        knockback_x = 15 if dx > 0 else -15 # Increased knockback
                    else:
                        knockback_y = 15 if dy > 0 else -15 # Increased knockback
                    break
            
            player.take_damage(Barricade.DAMAGE, knockback_x, knockback_y, apply_stun=True)

        # 2. Police Damage & Knockback
        if objects['police_manager'].check_damage_collision(player.get_rect()):
            # Calculate knockback direction
            knockback_x = 0
            knockback_y = 0
            player_center_x = player.x + player.size // 2
            player_center_y = player.y + player.size // 2
            
            # Find the colliding police
            for police in objects['police_manager'].polices:
                if player.get_rect().colliderect(police.get_rect()):
                    police_center_x = police.x + Police.SIZE // 2
                    police_center_y = police.y + Police.SIZE // 2
                    dx = player_center_x - police_center_x
                    dy = player_center_y - police_center_y
                    
                    # Push away from center
                    dist = max(1, (dx*dx + dy*dy) ** 0.5)
                    knockback_x = (dx / dist) * 15 # Increased knockback
                    knockback_y = (dy / dist) * 15 # Increased knockback
                    break

            player.take_damage(Police.DAMAGE, knockback_x, knockback_y, apply_stun=True)

        # 3. Ambulance Damage & Knockback
        ambulance_hit = objects['ambulance_manager'].check_collision(player.get_rect())
        if ambulance_hit:
            # Calculate knockback direction
            knockback_x = 0
            knockback_y = 0
            player_center_x = player.x + player.size // 2
            player_center_y = player.y + player.size // 2
            
            amb_rect = ambulance_hit.get_rect()
            amb_center_x = amb_rect.x + amb_rect.width // 2
            amb_center_y = amb_rect.y + amb_rect.height // 2
            
            dx = player_center_x - amb_center_x
            dy = player_center_y - amb_center_y
            
            # Push away from center
            dist = max(1, (dx*dx + dy*dy) ** 0.5)
            knockback_x = (dx / dist) * 15 # Stronger knockback for ambulance
            knockback_y = (dy / dist) * 15
            
            player.take_damage(Ambulance.BASE_DAMAGE, knockback_x, knockback_y, apply_stun=True)

        # 4. Teargas Damage
        if objects['teargas_manager'].check_damage_collision(player.get_rect()):
            player.take_damage(TearGas.DAMAGE)

        # 5. Physical Push (Resolve Overlap)
        # Push away from obstacles (Lamps, Dustbins, Trees, Barricades, Police, Ambulance)
        player_rect = player.get_rect()
        
        # Lamps
        for lamp in objects['lamp_manager'].lamps:
            pole_rect = lamp.get_pole_rect()
            top_rect = lamp.get_top_rect()
            collided_rect = None
            if player_rect.colliderect(pole_rect): collided_rect = pole_rect
            elif player_rect.colliderect(top_rect): collided_rect = top_rect
            
            if collided_rect:
                _push_player(player, collided_rect)
                player_rect = player.get_rect()

        # Dustbins
        for dustbin in objects['dustbin_manager'].dustbins:
            if player_rect.colliderect(dustbin.get_rect()):
                _push_player(player, dustbin.get_rect())
                player_rect = player.get_rect()

        # Trees
        for t in objects['tree_manager'].trees:
            if player_rect.colliderect(t.get_rect()):
                _push_player(player, t.get_rect())
                player_rect = player.get_rect()
                
        # Barricades (Physical Push)
        for b in objects['barricade_manager'].barricades:
            if player_rect.colliderect(b.get_rect()):
                _push_player(player, b.get_rect())
                player_rect = player.get_rect()

        # Police (Physical Push)
        for p in objects['police_manager'].polices:
            if player_rect.colliderect(p.get_rect()):
                _push_player(player, p.get_rect())
                player_rect = player.get_rect()

        # Ambulance (Physical Push)
        for a in objects['ambulance_manager'].ambulances:
            if player_rect.colliderect(a.get_rect()):
                _push_player(player, a.get_rect())
                player_rect = player.get_rect()

    def _push_player(player, obstacle_rect):
        player_center_x = player.x + player.size // 2
        player_center_y = player.y + player.size // 2
        rect_center_x = obstacle_rect.x + obstacle_rect.width // 2
        rect_center_y = obstacle_rect.y + obstacle_rect.height // 2
        dx = player_center_x - rect_center_x
        dy = player_center_y - rect_center_y
        dist = max(1, (dx*dx + dy*dy) ** 0.5)
        push = 10 # Increased push to prevent getting stuck
        player.x += (dx / dist) * push
        player.y += (dy / dist) * push
        player.x = max(0, min(full_map_width - player.size, player.x))
        player.y = max(full_map_height - player.size - 50, min(full_map_height - player.size - 10, player.y))

    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit", tokens_collected + p1_session_tokens + p2_session_tokens
            
            # Handle mute button click
            if music_manager.handle_event(event):
                continue
            
            # Handle pause icon click
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # Check pause icon rect (110, 10, 40, 40)
                    pause_rect = pygame.Rect(110, 10, 40, 40)
                    if pause_rect.collidepoint(event.pos):
                        # Trigger pause
                        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
                        pygame.event.post(event)
                        continue
            
            # Handle Game Over Screen Events
            if game_over and game_over_screen:
                action = game_over_screen.handle_events(event)
                if action == "quit":
                    return "quit", tokens_collected + p1_session_tokens + p2_session_tokens
                elif action == "main_menu":
                    return "menu", tokens_collected + p1_session_tokens + p2_session_tokens
            
            if not game_over and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Show pause screen
                    pause_screen = PauseScreen()
                    paused = True
                    while paused:
                        pause_event = pygame.event.wait()
                        if pause_event.type == pygame.QUIT:
                            running = False
                            paused = False
                        result = pause_screen.handle_events(pause_event)
                        if result == "resume":
                            paused = False
                        elif result == "restart":
                            # Restart game
                            return "start_split_screen", tokens_collected + p1_session_tokens + p2_session_tokens
                        elif result == "main_menu":
                            return "menu", tokens_collected + p1_session_tokens + p2_session_tokens
                        elif result == "quit":
                            running = False
                            paused = False
                        
                        pause_screen.update()
                        
                        # Draw game in background
                        screen.fill(WHITE)
                        road.draw(screen)
                        lamp_manager.draw(screen)
                        dustbin_manager.draw(screen)
                        ambulance_manager.draw(screen)
                        police_manager.draw(screen)
                        teargas_manager.draw(screen)
                        tree_manager.draw(screen)
                        barricade_manager.draw(screen)
                        token_manager.draw(screen)
                        
                        if p1_player.is_alive():
                            p1_player.draw(screen)
                        if p2_player.is_alive():
                            p2_player.draw(screen)
                            
                        # Draw HUDs
                        draw_hud(screen, p1_player, p1_score, p1_session_tokens, "PLAYER 1", 0)
                        draw_hud(screen, p2_player, p2_score, p2_session_tokens, "PLAYER 2", WIDTH - 170)
                        
                        # Draw Pause Screen
                        pause_screen.draw(screen)
                        pygame.display.flip()
                        clock.tick(60)
                if event.key == pygame.K_q:
                    running = False

        if paused:
            continue

        if game_over:
            # Initialize Game Over Screen if not done
            if game_over_screen is None:
                # Create Multiplayer Game Over Screen
                game_over_screen = MultiplayerGameOverScreen(p1_score, p1_session_tokens, p2_score, p2_session_tokens)
                
            # Update Game Over Screen
            game_over_screen.update()
            
            # Draw everything in background (static)
            screen.fill(WHITE)
            road.draw(screen)
            lamp_manager.draw(screen)
            dustbin_manager.draw(screen)
            ambulance_manager.draw(screen)
            police_manager.draw(screen)
            teargas_manager.draw(screen)
            tree_manager.draw(screen)
            barricade_manager.draw(screen)
            token_manager.draw(screen)
            
            if p1_player.is_alive():
                p1_player.draw(screen)
                marker = font.render("1", True, BLUE)
                screen.blit(marker, (p1_player.x + p1_player.size//2 - marker.get_width()//2, p1_player.y - 20))
            if p2_player.is_alive():
                p2_player.draw(screen)
                marker = font.render("2", True, RED)
                screen.blit(marker, (p2_player.x + p2_player.size//2 - marker.get_width()//2, p2_player.y - 20))

            # Draw HUDs
            draw_hud(screen, p1_player, p1_score, p1_session_tokens, "PLAYER 1", 0)
            draw_hud(screen, p2_player, p2_score, p2_session_tokens, "PLAYER 2", WIDTH - 170)

            # Draw Game Over Screen
            game_over_screen.draw(screen)
            pygame.display.flip()
            continue
            
        else:
            # GAME LOGIC UPDATE
            
            # Input Handling
            keys = pygame.key.get_pressed()
            
            # Player 1 (WASD) - Left Side
            p1_lateral = 0
            if p1_player.is_alive():
                if keys[pygame.K_a]:
                    p1_lateral = -p1_player.walk_speed
                if keys[pygame.K_d]:
                    p1_lateral = p1_player.walk_speed
                
            # Player 2 (Arrows) - Right Side
            p2_lateral = 0
            if p2_player.is_alive():
                if keys[pygame.K_LEFT]:
                    p2_lateral = -p2_player.walk_speed
                if keys[pygame.K_RIGHT]:
                    p2_lateral = p2_player.walk_speed
                
            # Update P1
            if p1_player.is_alive():
                p1_player.update_stun(clock.get_time())
                p1_player.update(full_map_width)
                p1_moving = True if not p1_player.is_stunned else False
                p1_player.update_animation(p1_moving)
            
            # Update P2
            if p2_player.is_alive():
                p2_player.update_stun(clock.get_time())
                p2_player.update(full_map_width)
                p2_moving = True if not p2_player.is_stunned else False
                p2_player.update_animation(p2_moving)
            
            # -------------------------
            # SCROLLING & WORLD UPDATE
            # -------------------------
            # Scroll unless BOTH players are stunned or dead
            p1_active = p1_player.is_alive() and not p1_player.is_stunned
            p2_active = p2_player.is_alive() and not p2_player.is_stunned
            
            # If at least one player is active, the world moves
            current_road_speed = road_speed if (p1_active or p2_active) else 0
            
            current_time = pygame.time.get_ticks() - game_start_time
            
            road.update(current_road_speed)
            lamp_manager.update(current_road_speed)
            dustbin_manager.update(current_road_speed)
            
            police_manager.update(current_road_speed, max(p1_score, p2_score), current_time, lamp_manager, dustbin_manager, teargas_manager, barricade_manager, tree_manager, ambulance_manager)
            teargas_manager.update(current_road_speed, max(p1_score, p2_score), current_time, lamp_manager, dustbin_manager, police_manager, barricade_manager, tree_manager, ambulance_manager)
            barricade_manager.update(current_road_speed, current_time, lamp_manager, dustbin_manager, police_manager, teargas_manager, tree_manager, ambulance_manager)
            ambulance_manager.update(current_road_speed, max(p1_score, p2_score), current_time, lamp_manager, dustbin_manager, police_manager, teargas_manager, barricade_manager, tree_manager, "start_multiplayer")
            tree_manager.update(current_road_speed)
            token_manager.update(current_road_speed, current_time, lamp_manager, dustbin_manager, police_manager, teargas_manager, barricade_manager, tree_manager, ambulance_manager)
            
            # Score increases if at least one player is running
            if current_road_speed > 0:
                if p1_active: p1_score += 0.2
                if p2_active: p2_score += 0.2
            
            # -------------------------
            # COLLISION CHECKS
            # -------------------------
            for player in [p1_player, p2_player]:
                if not player.is_alive():
                    continue
                    
                # Lateral Movement Collision
                lateral = p1_lateral if player == p1_player else p2_lateral
                
                if not player.is_stunned and abs(player.knockback_x) < 0.1:
                    player_rect = player.get_rect()
                    if lateral != 0:
                        if lamp_manager.check_collision(player_rect, lateral_movement=lateral): lateral = 0
                        elif dustbin_manager.check_collision(player_rect, lateral_movement=lateral): lateral = 0
                        elif police_manager.check_collision(player_rect, lateral_movement=lateral): lateral = 0
                        elif barricade_manager.check_collision(player_rect, lateral_movement=lateral): lateral = 0
                        elif tree_manager.check_collision(player_rect, lateral_movement=lateral): lateral = 0
                    
                    player.x += lateral
                    player.x = max(0, min(full_map_width - player.size, player.x))

                # Resolve Collisions (Damage, Knockback, Push)
                resolve_collisions(player, game_objects)
                
                # Collect Tokens
                collected = token_manager.collect_if_overlap(player.get_rect())
                if collected:
                    if player == p1_player:
                        p1_session_tokens += collected
                    else:
                        p2_session_tokens += collected
                
                # Check Stuck
                if barricade_manager.check_player_stuck(player.get_rect(), player.y, HEIGHT):
                    player.health = 0 # Kill stuck player
            
            # -------------------------
            # GAME OVER CHECK
            # -------------------------
            # Game over if EITHER player is dead (Simultaneous Death)
            if not p1_player.is_alive() or not p2_player.is_alive():
                game_over = True
                # Initialize game over screen with separate scores and tokens
                game_over_screen = MultiplayerGameOverScreen(p1_score, p1_session_tokens, p2_score, p2_session_tokens)
            
            # Increase difficulty
            highest_score = max(p1_score, p2_score)
            if highest_score >= last_speed_increase_score + 250:
                if road_speed < 12:
                    road_speed += 0.3
                    last_speed_increase_score = highest_score
        
        # Draw world
        road.draw(screen)
        lamp_manager.draw(screen)
        dustbin_manager.draw(screen)
        ambulance_manager.draw(screen)
        police_manager.draw(screen)
        teargas_manager.draw(screen)
        tree_manager.draw(screen)
        barricade_manager.draw(screen)
        token_manager.draw(screen)
        
        # Draw players (ONLY IF ALIVE)
        if p1_player.is_alive():
            p1_player.draw(screen)
            # Draw Marker
            marker = font.render("1", True, BLUE)
            screen.blit(marker, (p1_player.x + p1_player.size//2 - marker.get_width()//2, p1_player.y - 20))
            
        if p2_player.is_alive():
            p2_player.draw(screen)
            # Draw Marker
            marker = font.render("2", True, RED)
            screen.blit(marker, (p2_player.x + p2_player.size//2 - marker.get_width()//2, p2_player.y - 20))
        
        # Draw HUDs
        # P1 (Left)
        draw_hud(screen, p1_player, p1_score, p1_session_tokens, "PLAYER 1", 0)
        # P2 (Right)
        draw_hud(screen, p2_player, p2_score, p2_session_tokens, "PLAYER 2", WIDTH - 170)
        
        pygame.display.flip()
        clock.tick(60)

# -------------------------
# MAIN GAME FUNCTION
# -------------------------
def run_game(selected_mode="start_normal", tokens_collected=0, multiplayer_game=None):
    """Main game function with menu integration"""
    screen = pygame.display.get_surface()
    clock = pygame.time.Clock()
    
    # If split-screen mode
    if selected_mode == "start_split_screen":
        return run_split_screen_game(tokens_collected)
    
    # If multiplayer mode, use the multiplayer game function
    if selected_mode == "start_multiplayer" and multiplayer_game:
        return run_multiplayer_game(multiplayer_game, tokens_collected)
    
    # Initialize game objects
    game_objects = initialize_game()
    
    # Unpack game objects
    road = game_objects['road']
    lamp_manager = game_objects['lamp_manager']
    dustbin_manager = game_objects['dustbin_manager']
    police_manager = game_objects['police_manager']
    teargas_manager = game_objects['teargas_manager']
    barricade_manager = game_objects['barricade_manager']
    tree_manager = game_objects['tree_manager']
    token_manager = game_objects['token_manager']
    ambulance_manager = game_objects['ambulance_manager']
    decoration_manager = game_objects['decoration_manager']
    player = game_objects['player']
    
    # Game state variables
    running = True
    paused = False
    game_over = False
    scroll_offset = 0
    score = 0
    session_tokens = 0  # Track tokens collected ONLY in this session
    base_road_speed = 5
    road_speed = base_road_speed
    last_speed_increase_score = 0
    last_generation_increase_score = 0
    game_start_time = pygame.time.get_ticks()
    leaderboard = Leaderboard()
    game_over_screen = None
    
    # === MODE-SPECIFIC ADJUSTMENTS ===
    # Apply mode-specific adjustments
    mode_name = "NORMAL"
    if selected_mode == "start_multiplayer":
        # MULTIPLAYER mode: increased difficulty
        road_speed = 6
        player.max_health = 80
        player.health = 80
        mode_name = "MULTIPLAYER"
    elif selected_mode == "start_rage":
        # RAGE MODE: extreme difficulty
        road_speed = 10  # Increased from 8 to 10
        player.max_health = 50  # Set to 50 as requested
        player.health = 50
        # Rage Mode specific adjustments
        police_manager.set_spawn_interval(1800)  # More frequent police
        barricade_manager.set_spawn_interval(1500)  # More frequent barricades
        teargas_manager.edge_spawn_interval = 1200  # More frequent tear gas
        teargas_manager.min_score = 0  # Tear gas appears immediately
        ambulance_manager.min_score = 30  # Ambulances appear earlier
        ambulance_manager.base_spawn_interval = 4500  # More frequent ambulances
        ambulance_manager.min_spawn_interval = 1800  # Minimum interval reduced
        mode_name = "RAGE"
    # ====================================================
    
    # RAGE MODE SPECIFIC FEATURES
    if selected_mode == "start_rage":
        # Increased damage in rage mode
        Police.DAMAGE = 20  # Increased from 15
        TearGas.DAMAGE = 15  # Increased from 10
        # Ambulance damage is handled in the Ambulance class based on mode
    
    # Play appropriate music
    music_manager = get_music_manager()
    music_manager.set_position(20, 20) # Reset position for game/pause
    if selected_mode == "start_rage":
        music_manager.play("rage")
    else:
        music_manager.play("mode")
    
    # Main game loop
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Handle mute button click
            if music_manager.handle_event(event):
                continue
            
            # Handle pause icon click
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # Check pause icon rect (110, 10, 40, 40)
                    pause_rect = pygame.Rect(110, 10, 40, 40)
                    if pause_rect.collidepoint(event.pos):
                        # Trigger pause
                        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
                        pygame.event.post(event)
                        continue

            if game_over:
                # Handle game over screen events
                if game_over_screen is None:
                    # Pass ONLY session tokens to game over screen for recording
                    game_over_screen = GameOverScreen(score, session_tokens, mode_name, leaderboard)
                result = game_over_screen.handle_events(event)
                if result == "restart":
                    # Restart game with same mode
                    return run_game(selected_mode, tokens_collected)
                elif result == "main_menu":
                    return "menu", tokens_collected + session_tokens
                elif result == "quit":
                    running = False
                continue
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Show pause screen
                    pause_screen = PauseScreen()
                    paused = True
                    while paused:
                        pause_event = pygame.event.wait()
                        if pause_event.type == pygame.QUIT:
                            running = False
                            paused = False
                        
                        # Handle mute button in pause screen too
                        if music_manager.handle_event(pause_event):
                            # Redraw pause screen to update icon
                            screen.fill(WHITE)
                            road.draw(screen)
                            lamp_manager.draw(screen)
                            dustbin_manager.draw(screen)
                            ambulance_manager.draw(screen)
                            police_manager.draw(screen)
                            teargas_manager.draw(screen)
                            tree_manager.draw(screen)
                            barricade_manager.draw(screen)
                            token_manager.draw(screen)
                            player.draw(screen)
                            # Draw decorations if rage mode
                            if selected_mode == "start_rage":
                                decoration_manager.draw(screen)
                            pause_screen.draw(screen)
                            music_manager.draw(screen)
                            pygame.display.flip()
                            continue

                        result = pause_screen.handle_events(pause_event)
                        if result == "resume":
                            paused = False
                        elif result == "restart":
                            # Restart game with same mode
                            return run_game(selected_mode, tokens_collected)
                        elif result == "main_menu":
                            return "menu", tokens_collected + session_tokens
                        elif result == "quit":
                            running = False
                            paused = False
                        
                        pause_screen.update()
                        # Draw game in background
                        screen.fill(WHITE)
                        road.draw(screen)
                        lamp_manager.draw(screen)
                        dustbin_manager.draw(screen)
                        ambulance_manager.draw(screen)
                        police_manager.draw(screen)
                        teargas_manager.draw(screen)
                        tree_manager.draw(screen)
                        barricade_manager.draw(screen)
                        token_manager.draw(screen)
                        player.draw(screen)
                        # Draw pause screen overlay
                        pause_screen.draw(screen)
                        pygame.display.flip()
                        clock.tick(60)
                if event.key == pygame.K_q:
                    running = False

        if paused:
            continue

        if game_over:
            # Draw game over screen
            if game_over_screen is None:
                game_over_screen = GameOverScreen(score, session_tokens, mode_name, leaderboard)
            game_over_screen.update()
            
            # Draw the final game state in background
            screen.fill(WHITE)
            road.draw(screen)
            lamp_manager.draw(screen)
            dustbin_manager.draw(screen)
            ambulance_manager.draw(screen)
            police_manager.draw(screen)
            teargas_manager.draw(screen)
            tree_manager.draw(screen)
            barricade_manager.draw(screen)
            token_manager.draw(screen)
            player.draw(screen)
            
            # Draw game over screen overlay
            game_over_screen.draw(screen)
            pygame.display.flip()
            continue

        keys = pygame.key.get_pressed()
        moving = False
        lateral_movement = 0

        # LEFT / RIGHT MOVEMENT ONLY (no forward/backward controls)
        player_speed = player.walk_speed  # Use consistent speed
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            lateral_movement = -player_speed
            moving = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            lateral_movement = player_speed
            moving = True

        # UPDATE PLAYER (cooldowns, knockback, stun, etc.)
        delta_time = clock.get_time()  # Get time since last frame in milliseconds
        player.update_stun(delta_time)
        player.update(WIDTH)
        
        # COLLISION CHECK (LATERAL)
        player_rect = player.get_rect()
        
        # Only allow lateral movement if not stunned and not in knockback
        if not player.is_stunned and abs(player.knockback_x) < 0.1:
            if lateral_movement != 0:
                if lamp_manager.check_collision(player_rect, lateral_movement=lateral_movement):
                    lateral_movement = 0
                elif dustbin_manager.check_collision(player_rect, lateral_movement=lateral_movement):
                    lateral_movement = 0
                elif police_manager.check_collision(player_rect, lateral_movement=lateral_movement):
                    lateral_movement = 0
                # Allow overlap with tear gas; do not block lateral movement
                elif barricade_manager.check_collision(player_rect, lateral_movement=lateral_movement):
                    lateral_movement = 0
                elif tree_manager.check_collision(player_rect, lateral_movement=lateral_movement):
                    lateral_movement = 0

            player.x += lateral_movement
            player.x = max(0, min(WIDTH - player.size, player.x))
        
        # AUTOMATIC CONTINUOUS FORWARD MOVEMENT
        # Player always moves forward - no controls needed
        # Stop scrolling if player is stunned
        current_road_speed = 0 if player.is_stunned else road_speed
        current_time = pygame.time.get_ticks() - game_start_time
        road.update(current_road_speed)
        lamp_manager.update(current_road_speed)
        dustbin_manager.update(current_road_speed, lamp_manager, tree_manager)
        
        # Rage Mode Decorations
        active_decoration_manager = None
        if selected_mode == "start_rage":
            decoration_manager.update(current_road_speed)
            active_decoration_manager = decoration_manager
            
        # Pass score, time, and managers to police and teargas managers for collision checking
        police_manager.update(current_road_speed, score, current_time, lamp_manager, dustbin_manager, teargas_manager, barricade_manager, tree_manager, ambulance_manager, active_decoration_manager)
        teargas_manager.update(current_road_speed, score, current_time, lamp_manager, dustbin_manager, police_manager, barricade_manager, tree_manager, ambulance_manager)
        barricade_manager.update(current_road_speed, current_time, lamp_manager, dustbin_manager, police_manager, teargas_manager, tree_manager, ambulance_manager)
        ambulance_manager.update(current_road_speed, score, current_time, lamp_manager, dustbin_manager, police_manager, teargas_manager, barricade_manager, tree_manager, selected_mode)
        tree_manager.update(current_road_speed)
        token_manager.update(current_road_speed, current_time, lamp_manager, dustbin_manager, police_manager, teargas_manager, barricade_manager, tree_manager, ambulance_manager)
        scroll_offset += current_road_speed
        moving = True if not player.is_stunned else False
        score += 0.2 if not player.is_stunned else 0  # Score increases continuously, but not when stunned
        
        # Check for collision with police after objects have moved - handle knockback and damage
        player_rect_after_move = player.get_rect()
        colliding_police = police_manager.check_damage_collision(player_rect_after_move)
        if colliding_police:
            # Calculate knockback direction (push player away from police)
            player_center_x = player.x + player.size // 2
            player_center_y = player.y + player.size // 2
            police_center_x = colliding_police.x + Police.SIZE // 2
            police_center_y = colliding_police.y + Police.SIZE // 2
            
            # Calculate direction vector
            dx = player_center_x - police_center_x
            dy = player_center_y - police_center_y
            distance = max(1, (dx**2 + dy**2)**0.5)  # Avoid division by zero
            
            # Normalize and scale knockback (reduced strength, smoother)
            knockback_strength = 4
            knockback_x = (dx / distance) * knockback_strength
            knockback_y = (dy / distance) * knockback_strength
            
            # Push player away to prevent overlap
            player.x += knockback_x
            player.y += knockback_y
            
            # Keep player within bounds and visible on screen
            player.x = max(0, min(WIDTH - player.size, player.x))
            player.y = max(HEIGHT - player.size - 50, min(HEIGHT - player.size - 10, player.y))  # Keep player visible on screen
            
            # Apply damage with knockback and stun
            player.take_damage(Police.DAMAGE, knockback_x, knockback_y, apply_stun=True)
        
        # Check for collision with tear gas (full overlap detection)
        if teargas_manager.check_damage_collision(player_rect_after_move):
            player.take_damage(TearGas.DAMAGE)

        # Check for collision with ambulance - damage scales with difficulty
        colliding_ambulance = ambulance_manager.check_collision(player_rect_after_move)
        if colliding_ambulance:
            damage = colliding_ambulance.get_damage(selected_mode)
            # Strong lateral knockback to avoid overlap
            if player.x + player.size / 2 < colliding_ambulance.x + Ambulance.SIZE / 2:
                # Player is to the left, push left
                knockback_x = -20
            else:
                # Player is to the right, push right
                knockback_x = 20
            knockback_y = 0 # Purely lateral push
            
            # Push player away to prevent overlap
            player.x += knockback_x
            player.y += knockback_y
            
            # Keep player within bounds and visible on screen
            player.x = max(0, min(WIDTH - player.size, player.x))
            player.y = max(HEIGHT - player.size - 50, min(HEIGHT - player.size - 10, player.y))
            
            # Apply damage with knockback (no stun for ambulance)
            player.take_damage(damage, knockback_x, knockback_y, apply_stun=False)
            colliding_ambulance.has_collided = True
        
        # Check for collision with barricade - stop player and apply damage
        if barricade_manager.check_damage_collision(player_rect_after_move):
            # Find all colliding barricades
            colliding_barricades = []
            for barricade in barricade_manager.barricades:
                if player_rect_after_move.colliderect(barricade.get_rect()):
                    colliding_barricades.append(barricade)
            
            # Calculate knockback for stun effect
            knockback_x = 0
            knockback_y = 0
            
            # If player is between two barricades (side-by-side), move to nearest side
            handled_two_barricades = False
            if len(colliding_barricades) >= 2:
                # Sort barricades by x position
                colliding_barricades.sort(key=lambda b: b.x)
                left_barricade = colliding_barricades[0]
                right_barricade = colliding_barricades[-1]
                
                # Check if barricades are horizontally adjacent (side-by-side)
                # They should be close in y position and the right one should be near the left one's right edge
                y_distance = abs(left_barricade.y - right_barricade.y)
                x_gap = right_barricade.x - (left_barricade.x + Barricade.SIZE)
                
                # If barricades are side-by-side (close in y, small x gap)
                if y_distance < Barricade.SIZE and x_gap < 50:  # 50 pixel tolerance for gap
                    player_center_x = player.x + player.size // 2
                    left_edge = left_barricade.x + Barricade.SIZE
                    right_edge = right_barricade.x
                    
                    # Determine which side is closer
                    dist_to_left = abs(player_center_x - left_edge)
                    dist_to_right = abs(player_center_x - right_edge)
                    
                    if dist_to_left < dist_to_right:
                        # Move player to left side of left barricade
                        player.x = left_barricade.x - player.size - 5  # 5 pixel gap
                        knockback_x = -5  # Small knockback for stun
                    else:
                        # Move player to right side of right barricade
                        player.x = right_barricade.x + Barricade.SIZE + 5  # 5 pixel gap
                        knockback_x = 5  # Small knockback for stun
                    
                    # Keep player within bounds
                    player.x = max(0, min(WIDTH - player.size, player.x))
                    handled_two_barricades = True
            
            # Single barricade collision or multiple non-adjacent - push player away completely
            if not handled_two_barricades:
                for barricade in colliding_barricades:
                    barricade_rect = barricade.get_rect()
                    player_rect = player.get_rect()
                    
                    # Calculate push direction (push player away from barricade)
                    player_center_x = player.x + player.size // 2
                    player_center_y = player.y + player.size // 2
                    barricade_center_x = barricade.x + Barricade.SIZE // 2
                    barricade_center_y = barricade.y + Barricade.SIZE // 2
                    
                    # Calculate direction vector
                    dx = player_center_x - barricade_center_x
                    dy = player_center_y - barricade_center_y
                    distance = max(1, (dx**2 + dy**2)**0.5)  # Avoid division by zero
                    
                    # Push player completely outside barricade - ensure no overlap
                    # Calculate minimum distance needed to separate
                    player_half_width = player.collision_size // 2
                    barricade_half_width = Barricade.SIZE // 2
                    min_separation = player_half_width + barricade_half_width + 5  # 5 pixel buffer
                    
                    # Push player away with enough force to prevent overlap
                    push_strength = max(15, min_separation)  # Strong push to prevent overlap
                    knockback_x = (dx / distance) * push_strength
                    knockback_y = (dy / distance) * push_strength
                    
                    # Apply push
                    player.x += knockback_x
                    player.y += knockback_y
                    
                    # Ensure player is completely outside barricade rect
                    new_player_rect = player.get_rect()
                    if new_player_rect.colliderect(barricade_rect):
                        # If still overlapping, push more aggressively
                        if player_center_x < barricade_center_x:
                            player.x = barricade.x - player.size - 5
                            knockback_x = -5
                        else:
                            player.x = barricade.x + Barricade.SIZE + 5
                            knockback_x = 5
                        if player_center_y < barricade_center_y:
                            player.y = barricade.y - player.size - 5
                            knockback_y = -5
                        else:
                            player.y = barricade.y + Barricade.SIZE + 5
                            knockback_y = 5
                    
                    # Keep player within bounds and visible
                    player.x = max(0, min(WIDTH - player.size, player.x))
                    player.y = max(HEIGHT - player.size - 50, min(HEIGHT - player.size - 10, player.y))
                    break
            
            # Apply damage with knockback and stun
            player.take_damage(Barricade.DAMAGE, knockback_x, knockback_y, apply_stun=True)
        
        # Resolve overlap with street lamps from all sides (push player away slightly)
        player_rect_after_move = player.get_rect()
        for lamp in lamp_manager.lamps:
            # Check both lamp parts
            pole_rect = lamp.get_pole_rect()
            top_rect = lamp.get_top_rect()
            collided_rect = None
            if player_rect_after_move.colliderect(pole_rect):
                collided_rect = pole_rect
            elif player_rect_after_move.colliderect(top_rect):
                collided_rect = top_rect
            if collided_rect:
                # Push player away from center of collided rect
                player_center_x = player.x + player.size // 2
                player_center_y = player.y + player.size // 2
                rect_center_x = collided_rect.x + collided_rect.width // 2
                rect_center_y = collided_rect.y + collided_rect.height // 2
                dx = player_center_x - rect_center_x
                dy = player_center_y - rect_center_y
                dist = max(1, (dx*dx + dy*dy) ** 0.5)
                push = 5
                player.x += (dx / dist) * push
                player.y += (dy / dist) * push
                player.x = max(0, min(WIDTH - player.size, player.x))
                player.y = max(HEIGHT - player.size - 50, min(HEIGHT - player.size - 10, player.y))
                # Recompute rect after push for subsequent checks
                player_rect_after_move = player.get_rect()
        
        # Resolve overlap with dustbins from all sides (push player away slightly)
        player_rect_after_move = player.get_rect()
        for dustbin in dustbin_manager.dustbins:
            d_rect = dustbin.get_rect()
            if player_rect_after_move.colliderect(d_rect):
                player_center_x = player.x + player.size // 2
                player_center_y = player.y + player.size // 2
                rect_center_x = d_rect.x + d_rect.width // 2
                rect_center_y = d_rect.y + d_rect.height // 2
                dx = player_center_x - rect_center_x
                dy = player_center_y - rect_center_y
                dist = max(1, (dx*dx + dy*dy) ** 0.5)
                push = 5
                player.x += (dx / dist) * push
                player.y += (dy / dist) * push
                player.x = max(0, min(WIDTH - player.size, player.x))
                player.y = max(HEIGHT - player.size - 50, min(HEIGHT - player.size - 10, player.y))
                player_rect_after_move = player.get_rect()

        # Resolve overlap with trees from all sides (push player away slightly)
        player_rect_after_move = player.get_rect()
        for t in tree_manager.trees:
            t_rect = t.get_rect()
            if player_rect_after_move.colliderect(t_rect):
                player_center_x = player.x + player.size // 2
                player_center_y = player.y + player.size // 2
                rect_center_x = t_rect.x + t_rect.width // 2
                rect_center_y = t_rect.y + t_rect.height // 2
                dx = player_center_x - rect_center_x
                dy = player_center_y - rect_center_y
                dist = max(1, (dx*dx + dy*dy) ** 0.5)
                push = 5
                player.x += (dx / dist) * push
                player.y += (dy / dist) * push
                player.x = max(0, min(WIDTH - player.size, player.x))
                player.y = max(HEIGHT - player.size - 50, min(HEIGHT - player.size - 10, player.y))
                player_rect_after_move = player.get_rect()
        
        # Final check: Ensure player never overlaps with barricades (even after knockback)
        player_rect_final = player.get_rect()
        for barricade in barricade_manager.barricades:
            barricade_rect = barricade.get_rect()
            if player_rect_final.colliderect(barricade_rect):
                # Push player completely outside barricade
                player_center_x = player.x + player.size // 2
                player_center_y = player.y + player.size // 2
                barricade_center_x = barricade.x + Barricade.SIZE // 2
                barricade_center_y = barricade.y + Barricade.SIZE // 2
                
                # Determine which side to push to
                dx = player_center_x - barricade_center_x
                dy = player_center_y - barricade_center_y
                
                # Push to nearest edge
                if abs(dx) > abs(dy):
                    # Push horizontally
                    if dx < 0:
                        player.x = barricade.x - player.size - 5
                    else:
                        player.x = barricade.x + Barricade.SIZE + 5
                else:
                    # Push vertically
                    if dy < 0:
                        player.y = barricade.y - player.size - 5
                    else:
                        player.y = barricade.y + Barricade.SIZE + 5
                
                # Keep player within bounds
                player.x = max(0, min(WIDTH - player.size, player.x))
                player.y = max(HEIGHT - player.size - 50, min(HEIGHT - player.size - 10, player.y))
                player_rect_final = player.get_rect()  # Update for next iteration

        # Collect tokens on overlap
        collected_now = token_manager.collect_if_overlap(player.get_rect())
        if collected_now:
            session_tokens += collected_now
        
        # Check if player is stuck in barricade or tree (lamp) - game over condition
        player_rect = player.get_rect()
        if barricade_manager.check_player_stuck(player_rect, player.y, HEIGHT):
            game_over = True  # Game over - player stuck in barricade
        
        # CHECK IF PLAYER IS ALIVE
        if not player.is_alive():
            game_over = True

        # SCORE-BASED SPEED INCREASE - GRADUAL AND BALANCED
        # Increase speed every 250 points, but cap at reasonable maximum
        speed_increase_threshold = 250
        if selected_mode == "start_rage":
            speed_increase_threshold = 200  # Rage mode speeds up faster
            max_road_speed = 16  # Higher maximum speed for rage mode
        else:
            max_road_speed = 12  # Maximum speed cap for normal modes

        if score >= last_speed_increase_score + speed_increase_threshold:
            if road_speed < max_road_speed:
                if selected_mode == "start_rage":
                    road_speed += 0.5  # Larger increase in rage mode
                else:
                    road_speed += 0.3  # Small, gradual increase for normal modes
                last_speed_increase_score = score
        
        # SCORE-BASED GENERATION FREQUENCY INCREASE (smooth, gentle)
        if score >= 300:
            gen_increase_threshold = 300 if last_generation_increase_score < 300 else last_generation_increase_score + 300
            if score >= gen_increase_threshold:
                # Slightly decrease spawn intervals with safe minimums for smoothness
                new_police_interval = max(1200, police_manager.spawn_interval - 100)
                police_manager.set_spawn_interval(new_police_interval)
                # Barricades ramp too
                if hasattr(barricade_manager, "set_spawn_interval"):
                    new_barricade_interval = max(2000, barricade_manager.spawn_interval - 100)
                    barricade_manager.set_spawn_interval(new_barricade_interval)
                # Also decrease tear gas gap
                new_teargas_gap = max(450, teargas_manager.current_gap - 30)
                teargas_manager.set_gap(new_teargas_gap)
                last_generation_increase_score = gen_increase_threshold

        # RAGE MODE SPECIFIC SPAWNING PATTERNS
        if selected_mode == "start_rage":
            # More aggressive spawning patterns for rage mode
            if score >= 200:  # Earlier ramp-up
                # More police in rage mode
                pass  # Police spawning is handled in police_manager.update()
            if score >= 400:
                # Even more police in rage mode
                pass  # Police spawning is handled in police_manager.update()

        # ANIMATION
        player.update_animation(moving)

        # -------------------------
        # DRAW EVERYTHING
        # -------------------------
        screen.fill(WHITE)
        road.draw(screen)
        
        # Draw decorations (Rage Mode) - Draw on ground
        if selected_mode == "start_rage":
            decoration_manager.draw(screen)
        lamp_manager.draw(screen)
        dustbin_manager.draw(screen)
        ambulance_manager.draw(screen)
        police_manager.draw(screen)
        teargas_manager.draw(screen)
        tree_manager.draw(screen)
        barricade_manager.draw(screen)
        token_manager.draw(screen)
        player.draw(screen)

        # RAGE MODE VISUAL FEEDBACK
        if selected_mode == "start_rage":
            # Add red tint to screen during rage mode
            rage_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            rage_intensity = min(80, 30 + (score / 1000) * 50)  # Increases with score
            rage_overlay.fill((255, 0, 0, int(rage_intensity)))
            screen.blit(rage_overlay, (0, 0))
            
            # Pulsing border effect
            border_thickness = 3 + int(2 * abs(pygame.time.get_ticks() % 1000 - 500) / 500)
            pygame.draw.rect(screen, (255, 0, 0), (0, 0, WIDTH, HEIGHT), border_thickness)

        # HUD
        fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, BLACK)
        score_text = font.render(f"Score: {int(score)}", True, BLACK)
        health_text = font.render(f"Health: {int(player.health)}/{player.max_health}", True, BLACK)
        tokens_text = font.render(f"Tokens: {session_tokens}", True, BLACK)
        mode_text = font.render(f"Mode: {mode_name}", True, BLACK)
        speed_text = font.render(f"Speed: {road_speed:.1f}", True, BLACK)
        screen.blit(fps_text, (10, 10))
        screen.blit(score_text, (10, 30))
        screen.blit(health_text, (10, 50))
        screen.blit(mode_text, (10, 70))
        screen.blit(speed_text, (10, 90))
        # Top-right tokens
        screen.blit(tokens_text, (WIDTH - 10 - tokens_text.get_width(), 10))
        
        # RAGE MODE HUD
        if selected_mode == "start_rage":
            rage_text = font.render("RAGE MODE!", True, (255, 0, 0))
            screen.blit(rage_text, (WIDTH // 2 - rage_text.get_width() // 2, 10))
            
            # Intensity meter based on score
            intensity = min(100, score / 10)
            intensity_text = font.render(f"Intensity: {int(intensity)}%", True, (255, 0, 0))
            screen.blit(intensity_text, (WIDTH // 2 - intensity_text.get_width()//2, 30))
        
        # Health bar visualization
        bar_width = 200
        bar_height = 20
        bar_x = 10
        bar_y = 115
        health_percentage = player.health / player.max_health
        health_color = (255, 0, 0) if health_percentage < 0.3 else (255, 165, 0) if health_percentage < 0.6 else (0, 255, 0)
        
        # Background bar
        pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
        # Health bar
        pygame.draw.rect(screen, health_color, (bar_x, bar_y, int(bar_width * health_percentage), bar_height))
        # Border
        pygame.draw.rect(screen, BLACK, (bar_x, bar_y, bar_width, bar_height), 2)

        # Draw pause icon (Beside Score)
        if assets.pause_icon:
            screen.blit(assets.pause_icon, (110, 10))

        # Draw mute button (Beside Pause Icon)
        music_manager.set_position(155, 10)
        music_manager.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    return "quit", tokens_collected + session_tokens

# -------------------------
# MAIN MENU NAVIGATION
# -------------------------

def show_main_menu(tokens_collected=0):
    """Main function to show the main menu and handle navigation"""
    screen = pygame.display.get_surface()
    clock = pygame.time.Clock()
    
    current_screen = "menu"
    main_menu = MainMenu(tokens_collected)
    how_to_play = HowToPlayScreen()
    modes_screen = ModesScreen(tokens_collected)
    leaderboard_screen = LeaderboardScreen(Leaderboard())
    multiplayer_join = None
    multiplayer_lobby = None
    current_multiplayer_game = None
    
    running = True
    
    # Play menu music
    music_manager = get_music_manager()
    music_manager.play("menu")
    
    while running:
        # Handle events based on current screen
        # Global event handling for mute button
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit", tokens_collected
            
            # Handle mute button click
            if music_manager.handle_event(event):
                continue
                
            # Pass event to current screen if it has handle_event method
            if current_screen == "menu":
                action = main_menu.handle_events(event)
                if action == "quit":
                    return "quit", tokens_collected
                elif action == "play_story":
                    return "play_story", tokens_collected
                elif action == "start_normal":
                    return "start_normal", tokens_collected
                elif action == "modes":
                    current_screen = "modes"
                elif action == "how_to_play":
                    current_screen = "how_to_play"
                elif action == "leaderboard":
                    current_screen = "leaderboard"
            elif current_screen == "modes":
                action = modes_screen.handle_events(event)
                if action == "quit":
                    return "quit", tokens_collected
                elif action == "menu":
                    current_screen = "menu"
                elif action.startswith("start_"):
                    return action, tokens_collected
                elif action == "multiplayer":
                    # Direct to split screen
                    return "start_split_screen", tokens_collected
                elif action == "multiplayer_join":
                    current_screen = "multiplayer_join"
            elif current_screen == "how_to_play":
                action = how_to_play.handle_events(event)
                if action == "quit":
                    return "quit", tokens_collected
                elif action == "menu":
                    current_screen = "menu"
            elif current_screen == "leaderboard":
                action = leaderboard_screen.handle_events(event)
                if action == "quit":
                    return "quit", tokens_collected
                elif action == "menu":
                    current_screen = "menu"
            
            elif current_screen == "multiplayer_lobby":
                if not multiplayer_lobby:
                    multiplayer_lobby = MultiplayerLobbyScreen(current_multiplayer_game, is_host=True)
                action = multiplayer_lobby.handle_events(event) 
                if action == "modes":
                    current_screen = "modes"
                    multiplayer_lobby = None
                    current_multiplayer_game = None
                elif action == "start_multiplayer":
                    return "start_multiplayer", tokens_collected, current_multiplayer_game
            
            elif current_screen == "multiplayer_join":
                if not multiplayer_join:
                    multiplayer_join = MultiplayerJoinScreen()
                action = multiplayer_join.handle_events(event)
                if action == "modes":
                    current_screen = "modes"
                    multiplayer_join = None
                elif isinstance(action, tuple) and action[0] == "multiplayer_lobby":
                    current_screen = "multiplayer_lobby"
                    current_multiplayer_game = action[1]
                    multiplayer_lobby = MultiplayerLobbyScreen(current_multiplayer_game, is_host=False)
                    multiplayer_join = None

        # Update
        if current_screen == "menu":
            main_menu.update()
        elif current_screen == "modes":
            modes_screen.update()
        elif current_screen == "how_to_play":
            how_to_play.update()
        elif current_screen == "leaderboard":
            leaderboard_screen.update()
        elif current_screen == "multiplayer_lobby" and multiplayer_lobby:
            multiplayer_lobby.update()
        elif current_screen == "multiplayer_join":
            multiplayer_join.update()
        
        # Draw current screen
        if current_screen == "menu":
            main_menu.draw(screen)
        elif current_screen == "modes":
            modes_screen.draw(screen)
        elif current_screen == "how_to_play":
            how_to_play.draw(screen)
        elif current_screen == "leaderboard":
            leaderboard_screen.draw(screen)
        elif current_screen == "multiplayer_lobby" and multiplayer_lobby:
            multiplayer_lobby.draw(screen)
        elif current_screen == "multiplayer_join" and multiplayer_join:
            multiplayer_join.draw(screen)
            
        # Update mute button position based on screen
        music_manager.set_position(20, 20)
            
        # Draw mute button on top
        music_manager.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
    return "quit", tokens_collected
