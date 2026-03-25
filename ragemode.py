# ragemode.py
import pygame
import random
import math

# Rage Mode specific colors
RAGE_RED = (255, 50, 50, 50)  # Semi-transparent red overlay
RAGE_AMBIENT = (150, 0, 0)    # Red ambient light

class RagePolice:
    """Police that actively chases the player in rage mode"""
    SIZE = 110
    CHASE_SPEED = 3
    DAMAGE = 20
    VISION_RANGE = 300
    COLLISION_SIZE = 70
    
    def __init__(self, x, y, sprite):
        self.x = x
        self.y = y
        self.sprite = sprite
        self.chasing = False
        self.stuck_timer = 0
        self.last_x = x
        self.stuck_threshold = 60  # Frames before considering stuck
    
    def get_rect(self):
        offset = (self.SIZE - self.COLLISION_SIZE) // 2
        return pygame.Rect(self.x + offset, self.y + offset, self.COLLISION_SIZE, self.COLLISION_SIZE)
    
    def update(self, speed, player_x, player_y, obstacles):
        # Move with the road
        self.y += speed
        
        # Chase player if within vision range
        dist_to_player = math.sqrt((self.x - player_x)**2 + (self.y - player_y)**2)
        
        if dist_to_player < self.VISION_RANGE:
            self.chasing = True
            
            # Calculate direction to player
            dx = player_x - self.x
            dy = player_y - self.y
            distance = max(1, math.sqrt(dx*dx + dy*dy))
            
            # Normalize and apply chase speed
            dx = dx / distance * self.CHASE_SPEED
            dy = dy / distance * self.CHASE_SPEED
            
            # Store old position for collision checking
            old_x, old_y = self.x, self.y
            
            # Move towards player
            self.x += dx
            self.y += dy
            
            # Check for collisions with obstacles
            new_rect = self.get_rect()
            collision = False
            
            for obstacle in obstacles:
                if hasattr(obstacle, 'get_rect'):
                    if new_rect.colliderect(obstacle.get_rect()):
                        collision = True
                        break
            
            # If collision occurred, revert position and try to pathfind around
            if collision:
                self.x, self.y = old_x, old_y
                
                # Try moving only horizontally or vertically
                test_x = old_x + dx
                test_y = old_y
                test_rect = pygame.Rect(test_x + (self.SIZE - self.COLLISION_SIZE)//2, 
                                      test_y + (self.SIZE - self.COLLISION_SIZE)//2,
                                      self.COLLISION_SIZE, self.COLLISION_SIZE)
                
                horizontal_clear = True
                for obstacle in obstacles:
                    if hasattr(obstacle, 'get_rect'):
                        if test_rect.colliderect(obstacle.get_rect()):
                            horizontal_clear = False
                            break
                
                if horizontal_clear:
                    self.x = test_x
                else:
                    # Try vertical movement
                    test_x = old_x
                    test_y = old_y + dy
                    test_rect = pygame.Rect(test_x + (self.SIZE - self.COLLISION_SIZE)//2, 
                                          test_y + (self.SIZE - self.COLLISION_SIZE)//2,
                                          self.COLLISION_SIZE, self.COLLISION_SIZE)
                    
                    vertical_clear = True
                    for obstacle in obstacles:
                        if hasattr(obstacle, 'get_rect'):
                            if test_rect.colliderect(obstacle.get_rect()):
                                vertical_clear = False
                                break
                    
                    if vertical_clear:
                        self.y = test_y
            
            # Check if stuck (not moving much)
            if abs(self.x - self.last_x) < 1:
                self.stuck_timer += 1
            else:
                self.stuck_timer = 0
                self.last_x = self.x
                
        else:
            self.chasing = False
            self.stuck_timer = 0
    
    def is_stuck(self):
        return self.stuck_timer >= self.stuck_threshold
    
    def is_visible(self, screen_height):
        return -self.SIZE < self.y < screen_height + self.SIZE
    
    def draw(self, surface):
        if self.sprite:
            surface.blit(self.sprite, (self.x, self.y))
        
        # Draw vision range when chasing (for debug)
        if self.chasing:
            pygame.draw.circle(surface, (255, 0, 0, 100), 
                             (int(self.x + self.SIZE//2), int(self.y + self.SIZE//2)), 
                             self.VISION_RANGE, 1)

class RagePoliceManager:
    """Manager for rage mode police that chase the player"""
    def __init__(self, width, height, police_sprite):
        self.width = width
        self.height = height
        self.police_sprite = police_sprite
        self.polices = []
        self.spawn_interval = 2000  # ms
        self.last_spawn_time = 0
        self.max_police = 5
    
    def update(self, speed, player_x, player_y, current_time, obstacles):
        # Update existing police
        for police in self.polices:
            police.update(speed, player_x, player_y, obstacles)
        
        # Remove off-screen police
        self.polices = [p for p in self.polices if p.is_visible(self.height)]
        
        # Spawn new police
        if current_time - self.last_spawn_time >= self.spawn_interval and len(self.polices) < self.max_police:
            self.last_spawn_time = current_time
            
            # Spawn police at the top, away from player
            spawn_y = -RagePolice.SIZE
            spawn_x = random.randint(100, self.width - 100 - RagePolice.SIZE)
            
            # Ensure spawn is not too close to player
            attempts = 0
            while abs(spawn_x - player_x) < 200 and attempts < 10:
                spawn_x = random.randint(100, self.width - 100 - RagePolice.SIZE)
                attempts += 1
            
            self.polices.append(RagePolice(spawn_x, spawn_y, self.police_sprite))
    
    def check_collision(self, player_rect):
        """Check if any police catches the player"""
        for police in self.polices:
            if police.chasing and police.get_rect().colliderect(player_rect):
                return police
        return None
    
    def check_player_trapped(self, player_rect, obstacles):
        """Check if player is trapped by police and obstacles"""
        trapped_police = 0
        
        for police in self.polices:
            if police.chasing:
                # Check if police is close to player and there are obstacles blocking escape
                police_rect = police.get_rect()
                dist = math.sqrt((police_rect.centerx - player_rect.centerx)**2 + 
                               (police_rect.centery - player_rect.centery)**2)
                
                if dist < 150:  # Close range
                    # Check if escape paths are blocked by obstacles
                    escape_paths_blocked = 0
                    
                    # Check left
                    test_rect = pygame.Rect(player_rect.x - 50, player_rect.y, player_rect.width, player_rect.height)
                    for obstacle in obstacles:
                        if hasattr(obstacle, 'get_rect') and test_rect.colliderect(obstacle.get_rect()):
                            escape_paths_blocked += 1
                            break
                    
                    # Check right
                    test_rect = pygame.Rect(player_rect.x + 50, player_rect.y, player_rect.width, player_rect.height)
                    for obstacle in obstacles:
                        if hasattr(obstacle, 'get_rect') and test_rect.colliderect(obstacle.get_rect()):
                            escape_paths_blocked += 1
                            break
                    
                    # Check up (if player can move up)
                    test_rect = pygame.Rect(player_rect.x, player_rect.y - 50, player_rect.width, player_rect.height)
                    for obstacle in obstacles:
                        if hasattr(obstacle, 'get_rect') and test_rect.colliderect(obstacle.get_rect()):
                            escape_paths_blocked += 1
                            break
                    
                    # Check down
                    test_rect = pygame.Rect(player_rect.x, player_rect.y + 50, player_rect.width, player_rect.height)
                    for obstacle in obstacles:
                        if hasattr(obstacle, 'get_rect') and test_rect.colliderect(obstacle.get_rect()):
                            escape_paths_blocked += 1
                            break
                    
                    # If most escape paths are blocked and police is close, count as trapped
                    if escape_paths_blocked >= 2 and dist < 100:
                        trapped_police += 1
        
        # If multiple police have player trapped, it's a capture
        return trapped_police >= 2
    
    def get_all_obstacles_for_police(self, lamp_manager, dustbin_manager, barricade_manager, tree_manager):
        """Get all obstacles for police pathfinding"""
        obstacles = []
        
        # Add lamps
        if lamp_manager:
            for lamp in lamp_manager.lamps:
                obstacles.append(lamp)
        
        # Add dustbins
        if dustbin_manager:
            for dustbin in dustbin_manager.dustbins:
                obstacles.append(dustbin)
        
        # Add barricades
        if barricade_manager:
            for barricade in barricade_manager.barricades:
                obstacles.append(barricade)
        
        # Add trees
        if tree_manager:
            for tree in tree_manager.trees:
                obstacles.append(tree)
        
        return obstacles
    
    def draw(self, surface):
        for police in self.polices:
            police.draw(surface)

class RageModeOverlay:
    """Red overlay and visual effects for rage mode"""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        self.pulse_timer = 0
        self.pulse_speed = 0.05
        self.pulse_intensity = 0
    
    def update(self):
        """Update pulse effect"""
        self.pulse_timer += self.pulse_speed
        self.pulse_intensity = (math.sin(self.pulse_timer) + 1) * 0.3  # 0 to 0.6 intensity
    
    def draw(self, surface, danger_level):
        """Draw red overlay with pulse effect based on danger"""
        # Base red overlay
        self.overlay.fill((0, 0, 0, 0))  # Clear
        base_alpha = 80 + int(danger_level * 40)  # 80-120 alpha based on danger
        pulse_alpha = int(self.pulse_intensity * 50 * danger_level)  # Pulsing based on danger
        
        pygame.draw.rect(self.overlay, (255, 50, 50, base_alpha + pulse_alpha), 
                        (0, 0, self.width, self.height))
        
        # Add vignette effect
        for i in range(100):
            radius = self.width // 2 - i
            alpha = 10 + i // 2
            pygame.draw.circle(self.overlay, (255, 0, 0, alpha), 
                             (self.width // 2, self.height // 2), radius, 2)
        
        surface.blit(self.overlay, (0, 0))

def initialize_rage_game():
    """Initialize rage mode specific game objects"""
    from main import initialize_game, safe_load, Police
    
    # Get base game objects
    game_objects = initialize_game()
    
    # Replace police manager with rage police manager
    police_img = safe_load("Assets/Sprites/Enemy Characters/Police1.png")
    if police_img:
        police_img = pygame.transform.scale(police_img, (RagePolice.SIZE, RagePolice.SIZE))
    
    game_objects['rage_police_manager'] = RagePoliceManager(
        game_objects['police_manager'].width,
        game_objects['police_manager'].height,
        police_img
    )
    
    # Create rage overlay
    game_objects['rage_overlay'] = RageModeOverlay(
        game_objects['police_manager'].width,
        game_objects['police_manager'].height
    )
    
    return game_objects

def run_rage_mode(tokens_collected=0):
    """Main rage mode game function"""
    from main import WIDTH, HEIGHT, screen, clock, pygame, Police
    
    # Initialize rage mode specific objects
    game_objects = initialize_rage_game()
    
    # Unpack game objects
    road = game_objects['road']
    lamp_manager = game_objects['lamp_manager']
    dustbin_manager = game_objects['dustbin_manager']
    teargas_manager = game_objects['teargas_manager']
    barricade_manager = game_objects['barricade_manager']
    tree_manager = game_objects['tree_manager']
    token_manager = game_objects['token_manager']
    ambulance_manager = game_objects['ambulance_manager']
    player = game_objects['player']
    rage_police_manager = game_objects['rage_police_manager']
    rage_overlay = game_objects['rage_overlay']
    
    # Rage mode specific variables
    running = True
    game_over = False
    score = 0
    road_speed = 8  # Faster base speed for rage mode
    game_start_time = pygame.time.get_ticks()
    danger_level = 0  # 0-1 scale of how trapped player is
    
    # Rage mode adjustments
    player.max_health = 60
    player.health = 60
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return "quit", tokens_collected
            
            if game_over:
                # Handle game over (you can implement rage mode specific game over screen)
                from main import GameOverScreen, Leaderboard
                game_over_screen = GameOverScreen(score, tokens_collected, "RAGE", Leaderboard())
                result = game_over_screen.handle_events(event)
                if result == "restart":
                    return run_rage_mode(tokens_collected)
                elif result == "main_menu":
                    return "menu", tokens_collected
                elif result == "quit":
                    running = False
                continue
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Pause menu (you can implement rage mode specific pause)
                    from main import PauseScreen
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
                            return run_rage_mode(tokens_collected)
                        elif result == "main_menu":
                            return "menu", tokens_collected
                        elif result == "quit":
                            running = False
                            paused = False

        if game_over:
            continue

        # Player movement (same as normal mode)
        keys = pygame.key.get_pressed()
        moving = False
        lateral_movement = 0
        player_speed = player.walk_speed
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            lateral_movement = -player_speed
            moving = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            lateral_movement = player_speed
            moving = True

        # Update player
        delta_time = clock.get_time()
        player.update_stun(delta_time)
        player.update(WIDTH)
        
        # Collision checking for lateral movement
        player_rect = player.get_rect()
        if not player.is_stunned and abs(player.knockback_x) < 0.1:
            if lateral_movement != 0:
                if lamp_manager.check_collision(player_rect, lateral_movement=lateral_movement):
                    lateral_movement = 0
                elif dustbin_manager.check_collision(player_rect, lateral_movement=lateral_movement):
                    lateral_movement = 0
                elif barricade_manager.check_collision(player_rect, lateral_movement=lateral_movement):
                    lateral_movement = 0
                elif tree_manager.check_collision(player_rect, lateral_movement=lateral_movement):
                    lateral_movement = 0

            player.x += lateral_movement
            player.x = max(0, min(WIDTH - player.size, player.x))
        
        # Game world updates
        current_time = pygame.time.get_ticks() - game_start_time
        road.update(road_speed)
        lamp_manager.update(road_speed)
        dustbin_manager.update(road_speed)
        teargas_manager.update(road_speed, score, current_time, lamp_manager, dustbin_manager, None, barricade_manager, tree_manager, ambulance_manager)
        barricade_manager.update(road_speed, current_time, lamp_manager, dustbin_manager, None, teargas_manager, tree_manager, ambulance_manager)
        ambulance_manager.update(road_speed, score, current_time, lamp_manager, dustbin_manager, None, teargas_manager, barricade_manager, tree_manager)
        tree_manager.update(road_speed)
        token_manager.update(road_speed, current_time, lamp_manager, dustbin_manager, None, teargas_manager, barricade_manager, tree_manager)
        
        # Update rage mode specific systems
        obstacles = rage_police_manager.get_all_obstacles_for_police(
            lamp_manager, dustbin_manager, barricade_manager, tree_manager
        )
        rage_police_manager.update(road_speed, player.x, player.y, current_time, obstacles)
        rage_overlay.update()
        
        # Score increases
        score += 0.3  # Faster scoring in rage mode
        
        # Check for police capture
        colliding_police = rage_police_manager.check_collision(player_rect)
        if colliding_police:
            # Strong knockback and damage from rage police
            player_center_x = player.x + player.size // 2
            player_center_y = player.y + player.size // 2
            police_center_x = colliding_police.x + RagePolice.SIZE // 2
            police_center_y = colliding_police.y + RagePolice.SIZE // 2
            
            dx = player_center_x - police_center_x
            dy = player_center_y - police_center_y
            distance = max(1, (dx**2 + dy**2)**0.5)
            
            knockback_strength = 6  # Stronger knockback
            knockback_x = (dx / distance) * knockback_strength
            knockback_y = (dy / distance) * knockback_strength
            
            player.x += knockback_x
            player.y += knockback_y
            player.x = max(0, min(WIDTH - player.size, player.x))
            player.y = max(HEIGHT - player.size - 50, min(HEIGHT - player.size - 10, player.y))
            
            player.take_damage(RagePolice.DAMAGE, knockback_x, knockback_y, apply_stun=True)
        
        # Check if player is trapped
        is_trapped = rage_police_manager.check_player_trapped(player_rect, obstacles)
        
        # Update danger level based on trap situation and nearby police
        nearby_police = 0
        for police in rage_police_manager.polices:
            if police.chasing:
                police_rect = police.get_rect()
                dist = math.sqrt((police_rect.centerx - player_rect.centerx)**2 + 
                               (police_rect.centery - player_rect.centery)**2)
                if dist < 200:
                    nearby_police += 1
        
        danger_level = min(1.0, (nearby_police * 0.3 + (1.0 if is_trapped else 0.0)))
        
        # If completely trapped for too long, game over
        if is_trapped and danger_level > 0.8:
            trapped_time = 0
            while is_trapped and trapped_time < 180:  # 3 seconds at 60 FPS
                trapped_time += 1
                # You might want to add visual feedback here
            if trapped_time >= 180:
                game_over = True
        
        # Collect tokens
        collected_now = token_manager.collect_if_overlap(player_rect)
        if collected_now:
            tokens_collected += collected_now
        
        # Check player health
        if not player.is_alive():
            game_over = True
        
        # Increase speed over time
        if score % 500 == 0 and road_speed < 15:
            road_speed += 0.5
        
        # Animation
        player.update_animation(moving)
        
        # DRAW EVERYTHING
        screen.fill(RAGE_AMBIENT)  # Red ambient background
        
        # Draw game objects
        road.draw(screen)
        lamp_manager.draw(screen)
        dustbin_manager.draw(screen)
        ambulance_manager.draw(screen)
        teargas_manager.draw(screen)
        tree_manager.draw(screen)
        barricade_manager.draw(screen)
        token_manager.draw(screen)
        rage_police_manager.draw(screen)
        player.draw(screen)
        
        # Draw rage overlay
        rage_overlay.draw(screen, danger_level)
        
        # HUD (with rage mode specific info)
        from main import font, BLACK
        fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, BLACK)
        score_text = font.render(f"Score: {int(score)}", True, BLACK)
        health_text = font.render(f"Health: {int(player.health)}/{player.max_health}", True, BLACK)
        tokens_text = font.render(f"Tokens: {tokens_collected}", True, BLACK)
        mode_text = font.render(f"MODE: RAGE", True, (255, 0, 0))
        danger_text = font.render(f"DANGER: {int(danger_level * 100)}%", True, (255, 0, 0))
        police_text = font.render(f"POLICE: {len(rage_police_manager.polices)}", True, (255, 0, 0))
        
        screen.blit(fps_text, (10, 10))
        screen.blit(score_text, (10, 30))
        screen.blit(health_text, (10, 50))
        screen.blit(mode_text, (10, 70))
        screen.blit(danger_text, (10, 90))
        screen.blit(police_text, (10, 110))
        screen.blit(tokens_text, (WIDTH - 10 - tokens_text.get_width(), 10))
        
        # Health bar (red to match rage theme)
        bar_width = 200
        bar_height = 20
        bar_x = 10
        bar_y = 135
        health_percentage = player.health / player.max_health
        
        pygame.draw.rect(screen, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, int(bar_width * health_percentage), bar_height))
        pygame.draw.rect(screen, BLACK, (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Danger indicator
        if danger_level > 0.7:
            warning_text = font.render("WARNING: TRAPPED!", True, (255, 255, 0))
            screen.blit(warning_text, (WIDTH // 2 - warning_text.get_width() // 2, 20))
        
        pygame.display.flip()
        clock.tick(60)
    
    return "menu", tokens_collected

# For testing the rage mode independently
if __name__ == "__main__":
    pygame.init()
    WIDTH, HEIGHT = 1000, 750
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Andolan Express - RAGE MODE")
    clock = pygame.time.Clock()
    
    run_rage_mode()
    