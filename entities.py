import pygame
import random
from settings import *

# -------------------------
# STREET LAMP CLASS
# -------------------------
class StreetLamp:
    SIZE = 175
    GAP = 450
    TOP_HEIGHT = 55
    BASE_HEIGHT = SIZE - TOP_HEIGHT
    POLE_WIDTH = 40
    POLE_HEIGHT = BASE_HEIGHT
    TOP_COLLISION_WIDTH = SIZE
    TOP_COLLISION_HEIGHT = TOP_HEIGHT
    # Collision sizes (tighter than visual)
    POLE_COLLISION_WIDTH = 25  
    TOP_COLLISION_WIDTH_TIGHT = 60  
    
    def __init__(self, x, y, lamp_type, left_sprite, right_sprite):
        self.x = x
        self.y = y
        self.type = lamp_type  # "left" or "right"
        self.left_sprite = left_sprite
        self.right_sprite = right_sprite
    
    def get_sprite(self):
        return self.left_sprite if self.type == "left" else self.right_sprite
    
    def get_pole_rect(self):
        # Center the smaller collision box on the pole
        pole_center_x = self.x + (self.SIZE // 2)
        pole_x = pole_center_x - (self.POLE_COLLISION_WIDTH // 2)
        pole_y = self.y + self.TOP_HEIGHT
        return pygame.Rect(pole_x, pole_y, self.POLE_COLLISION_WIDTH, self.POLE_HEIGHT)
    
    def get_top_rect(self):
        # Center the smaller collision box on the top
        top_center_x = self.x + (self.SIZE // 2)
        top_x = top_center_x - (self.TOP_COLLISION_WIDTH_TIGHT // 2)
        return pygame.Rect(top_x, self.y, self.TOP_COLLISION_WIDTH_TIGHT, self.TOP_COLLISION_HEIGHT)
    
    def check_collision(self, rect):
        return rect.colliderect(self.get_pole_rect()) or rect.colliderect(self.get_top_rect())
    
    def update(self, speed):
        self.y += speed
    
    def draw(self, surface):
        sprite = self.get_sprite()
        if sprite:
            surface.blit(sprite, (self.x, self.y))
    
    def is_visible(self, screen_height):
        return -self.SIZE < self.y < screen_height + self.SIZE

# -------------------------
# DUSTBIN CLASS
# -------------------------
class Dustbin:
    SIZE = 70
    GAP = 850
    COLLISION_SIZE = 45  # Smaller collision box for tighter detection
    
    def __init__(self, x, y, sprite):
        self.x = x
        self.y = y
        self.sprite = sprite
    
    def get_rect(self):
        # Return a smaller, centered collision box
        offset = (self.SIZE - self.COLLISION_SIZE) // 2
        return pygame.Rect(self.x + offset, self.y + offset, self.COLLISION_SIZE, self.COLLISION_SIZE)
    
    def check_collision(self, rect):
        return rect.colliderect(self.get_rect())
    
    def update(self, speed):
        self.y += speed
    
    def draw(self, surface):
        if self.sprite:
            surface.blit(self.sprite, (self.x, self.y))
    
    def is_visible(self, screen_height):
        return -self.SIZE < self.y < screen_height + self.SIZE

# -------------------------
# POLICE OBSTACLE CLASS
# -------------------------
class Police:
    SIZE = 110  # Fixed size
    BASE_GAP = 600  # Base gap, will be modified based on score (smaller = more frequent)
    DAMAGE = 15
    COLLISION_SIZE = 70  # Collision box size
    
    def __init__(self, x, y, sprite):
        self.x = x
        self.y = y
        self.sprite = sprite
    
    def get_rect(self):
        # Return a smaller, centered collision box
        offset = (Police.SIZE - Police.COLLISION_SIZE) // 2
        return pygame.Rect(self.x + offset, self.y + offset, self.COLLISION_SIZE, self.COLLISION_SIZE)
    
    def check_collision(self, rect):
        return rect.colliderect(self.get_rect())
    
    def update(self, speed):
        self.y += speed
    
    def draw(self, surface):
        if self.sprite:
            surface.blit(self.sprite, (self.x, self.y))
    
    def is_visible(self, screen_height):
        return -Police.SIZE < self.y < screen_height + self.SIZE

# -------------------------
# TEAR GAS OBSTACLE CLASS
# -------------------------
class TearGas:
    SIZE = 180  # Further increased size
    BASE_GAP = 700  # Base gap, will be modified based on score (smaller = more frequent)
    DAMAGE = 10
    COLLISION_SIZE = 180  # Full size collision for overlap detection from all sides
    ANIMATION_DELAY = 10  # Frames per animation frame
    
    def __init__(self, x, y, sprites):
        self.x = x
        self.y = y
        self.sprites = sprites  # List of sprites for animation
        self.current_frame = 0
        self.frame_timer = 0
    
    def update_animation(self):
        """Update animation frames"""
        self.frame_timer += 1
        if self.frame_timer >= self.ANIMATION_DELAY:
            self.frame_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.sprites)
    
    def get_rect(self):
        # Return full size collision box for overlap detection from all sides
        return pygame.Rect(self.x, self.y, self.SIZE, self.SIZE)
    
    def check_collision(self, rect):
        return rect.colliderect(self.get_rect())
    
    def update(self, speed):
        if speed > 0:  # Only move if speed is positive (not stunned)
            self.y += speed
        self.update_animation()
    
    def draw(self, surface):
        if self.sprites and len(self.sprites) > 0:
            surface.blit(self.sprites[self.current_frame], (self.x, self.y))
    
    def is_visible(self, screen_height):
        return -self.SIZE < self.y < screen_height + self.SIZE

# -------------------------
# TOKEN (CURRENCY) CLASS
# -------------------------
class Token:
    SIZE = 40
    def __init__(self, x, y, sprite):
        self.x = x
        self.y = y
        self.sprite = sprite
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.SIZE, self.SIZE)
    def update(self, speed):
        self.y += speed
    def is_visible(self, screen_height):
        return -self.SIZE < self.y < screen_height + self.SIZE
    def draw(self, surface):
        if self.sprite:
            surface.blit(self.sprite, (self.x, self.y))

# -------------------------
# AMBULANCE CLASS
# -------------------------
class Ambulance:
    SIZE = 140
    BASE_DAMAGE = 20
    MAX_DAMAGE = 50
    BASE_SPEED_MULTIPLIER = 1.2  # Base speed multiplier
    MAX_SPEED_MULTIPLIER = 2.0   # Max speed multiplier at high scores
    ANIM_DELAY = 8

    def __init__(self, x, y, frames, score=0):
        self.x = x
        self.y = y
        self.frames = frames or []
        self.current_frame = 0
        self.frame_timer = 0
        self.score = score
        self.has_collided = False
        self.collision_cooldown = 0  # Add collision cooldown
    
    def get_speed_multiplier(self, selected_mode="start_normal"):
        """Calculate speed multiplier based on score and game mode"""
        if selected_mode == "start_rage":
            # Much faster ambulances in rage mode
            if self.score < 500:
                return 1.8  # Faster base speed
            elif self.score >= 2000:
                return 3.0  # Extreme speed at high scores
            else:
                progress = (self.score - 500) / (2000 - 500)
                return 1.8 + (3.0 - 1.8) * progress
        else:
            # Normal mode speeds
            if self.score < 1000:
                return self.BASE_SPEED_MULTIPLIER
            elif self.score >= 5000:
                return self.MAX_SPEED_MULTIPLIER
            else:
                progress = (self.score - 1000) / (5000 - 1000)
                return self.BASE_SPEED_MULTIPLIER + (self.MAX_SPEED_MULTIPLIER - self.BASE_SPEED_MULTIPLIER) * progress
    
    def get_damage(self, selected_mode="start_normal"):
        """Calculate damage based on score/difficulty and game mode"""
        if selected_mode == "start_rage":
            # Increased damage in rage mode
            if self.score < 60:
                return 30  # Higher base damage
            elif self.score >= 1000:
                return 60  # Higher max damage
            else:
                progress = (self.score - 60) / (1000 - 60)
                return int(30 + (60 - 30) * progress)
        else:
            # Normal mode damage
            if self.score < 60:
                return self.BASE_DAMAGE
            elif self.score >= 1000:
                return self.MAX_DAMAGE
            else:
                progress = (self.score - 60) / (1000 - 60)
                return int(self.BASE_DAMAGE + (self.MAX_DAMAGE - self.BASE_DAMAGE) * progress)
    
    def get_rect(self):
        # Use larger collision box for better detection
        return pygame.Rect(self.x - 10, self.y - 10, self.SIZE + 20, self.SIZE + 20)
    
    def update(self, road_speed, selected_mode="start_normal"):
        """Move straight down at speed that scales with difficulty"""
        speed_multiplier = self.get_speed_multiplier(selected_mode)
        self.y += road_speed * speed_multiplier
        
        # Update collision cooldown
        if self.collision_cooldown > 0:
            self.collision_cooldown -= 1
        elif self.has_collided:
            # Reset collision flag after cooldown
            self.has_collided = False
        
        # Update animation
        if self.frames:
            self.frame_timer += 1
            if self.frame_timer >= self.ANIM_DELAY:
                self.frame_timer = 0
                self.current_frame = (self.current_frame + 1) % len(self.frames)
    
    def is_visible(self, screen_height):
        return -self.SIZE < self.y < screen_height + self.SIZE
    
    def draw(self, surface):
        if self.frames:
            surface.blit(self.frames[self.current_frame], (self.x, self.y))

# -------------------------
# BARRICADE OBSTACLE CLASS
# -------------------------
class Barricade:
    SIZE = 125
    DAMAGE = 1
    COLLISION_SIZE = 75  # Full collision box
    
    def __init__(self, x, y, sprite, barricade_type):
        self.x = x
        self.y = y
        self.sprite = sprite
        self.type = barricade_type  # "barricade1" or "barricade2"
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.SIZE, self.SIZE)
    
    def check_collision(self, rect):
        return rect.colliderect(self.get_rect())
    
    def update(self, speed):
        self.y += speed
    
    def draw(self, surface):
        if self.sprite:
            surface.blit(self.sprite, (self.x, self.y))
    
    def is_visible(self, screen_height):
        return -self.SIZE < self.y < screen_height + self.SIZE

# -------------------------
# TREE OBSTACLE CLASS
# -------------------------
class Tree:
    SIZE = 130
    DAMAGE = 0  # trees block, but do not damage by themselves
    
    def __init__(self, x, y, sprite):
        self.x = x
        self.y = y
        self.sprite = sprite
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.SIZE, self.SIZE)
    
    def update(self, speed):
        self.y += speed
    
    def is_visible(self, screen_height):
        return -self.SIZE < self.y < screen_height + self.SIZE
    
    def draw(self, surface):
        if self.sprite:
            surface.blit(self.sprite, (self.x, self.y))

# -------------------------
# ROAD CLASS
# -------------------------
class Road:
    TILE_HEIGHT = 200
    
    def __init__(self, width, height, road_tile):
        self.width = width
        self.height = height
        self.road_tile = road_tile
        self.positions = [i * self.TILE_HEIGHT for i in range(height // self.TILE_HEIGHT + 2)]
    
    def update(self, speed):
        """Update road positions"""
        for i in range(len(self.positions)):
            self.positions[i] += speed
            # Recycle tiles
            if self.positions[i] >= self.height:
                self.positions[i] -= len(self.positions) * self.TILE_HEIGHT
            elif self.positions[i] <= -self.TILE_HEIGHT:
                self.positions[i] += len(self.positions) * self.TILE_HEIGHT
    
    def draw(self, surface):
        """Draw road tiles"""
        for y in self.positions:
            surface.blit(self.road_tile, (0, y))

# -------------------------
# PLAYER CLASS
# -------------------------
class Player:
    def __init__(self, x, y, run_frames, walk_speed=5, run_speed=8, max_health=100):
        self.x = x
        self.y = y
        self.run_frames = run_frames
        self.walk_speed = walk_speed
        self.run_speed = run_speed
        self.current_frame = 0
        self.frame_timer = 0
        self.frame_delay = 8
        self.size = 75 if run_frames else 75
        self.collision_size = 40  # Smaller collision box for tighter detection
        self.max_health = max_health
        self.health = max_health
        self.damage_cooldown = 0
        self.damage_cooldown_time = 30  # Frames before taking damage again
        self.knockback_x = 0  # Knockback velocity
        self.knockback_y = 0  # Knockback velocity
        self.knockback_decay = 0.55  # Even faster decay for smoother, shorter knockback
        self.stun_timer = 0  # Stun timer in milliseconds
        self.stun_duration = 500  # ~0.5 second stun
        self.is_stunned = False
    
    def take_damage(self, amount, knockback_x=0, knockback_y=0, apply_stun=False):
        """Take damage if cooldown is over and apply knockback"""
        if self.damage_cooldown <= 0:
            self.health = max(0, self.health - amount)
            self.damage_cooldown = self.damage_cooldown_time
            # Apply knockback
            self.knockback_x = knockback_x
            self.knockback_y = knockback_y
            # Apply stun if requested
            if apply_stun:
                self.is_stunned = True
                self.stun_timer = self.stun_duration
            return True
        return False
    
    def update_stun(self, delta_time):
        """Update stun timer"""
        if self.is_stunned:
            self.stun_timer -= delta_time
            if self.stun_timer <= 0:
                self.is_stunned = False
                self.stun_timer = 0
    
    def update(self, width):
        """Update player state (cooldowns, knockback, etc.)"""
        if self.damage_cooldown > 0:
            self.damage_cooldown -= 1
        
        # Apply knockback and decay
        if abs(self.knockback_x) > 0.1 or abs(self.knockback_y) > 0.1:
            self.x += self.knockback_x
            self.y += self.knockback_y
            self.knockback_x *= self.knockback_decay
            self.knockback_y *= self.knockback_decay
            # Keep player within bounds and visible on screen
            self.x = max(0, min(width - self.size, self.x))
            # Keep player in bottom area of screen (visible)
            screen_bottom = 750  # HEIGHT
            self.y = max(screen_bottom - self.size - 100, min(screen_bottom - self.size - 10, self.y))
        else:
            self.knockback_x = 0
            self.knockback_y = 0
    
    def is_alive(self):
        """Check if player is still alive"""
        return self.health > 0
    
    def get_rect(self):
        # Return a smaller, centered collision box
        offset = (self.size - self.collision_size) // 2
        return pygame.Rect(self.x + offset, self.y + offset, self.collision_size, self.collision_size)
    
    def update_animation(self, moving):
        """Update animation frames"""
        if moving and self.run_frames:
            self.frame_timer += 1
            if self.frame_timer >= self.frame_delay:
                self.frame_timer = 0
                self.current_frame = (self.current_frame + 1) % len(self.run_frames)
        else:
            self.current_frame = 0
    
    def draw(self, surface):
        """Draw player"""
        if self.run_frames:
            surface.blit(self.run_frames[self.current_frame], (self.x, self.y))
        else:
            pygame.draw.rect(surface, BLUE, (self.x, self.y, self.size, self.size))
