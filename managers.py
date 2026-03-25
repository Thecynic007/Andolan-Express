import pygame
import random
from entities import StreetLamp, Dustbin, Police, TearGas, Token, Ambulance, Barricade, Tree

# -------------------------
# LAMP MANAGER CLASS
# -------------------------
class LampManager:
    def __init__(self, width, height, left_sprite, right_sprite):
        self.width = width
        self.height = height
        self.left_sprite = left_sprite
        self.right_sprite = right_sprite
        self.lamps = []
        self.vertical_spacing = StreetLamp.GAP
        
        # Initialize lamps
        self._initialize_lamps()
    
    def _initialize_lamps(self):
        # Create initial set of lamps to fill the screen and a bit more
        num_lamps = self.height // self.vertical_spacing + 2
        for i in range(num_lamps):
            y = self.height - (i * self.vertical_spacing)
            self._add_lamp_pair(y)
            
    def _add_lamp_pair(self, y):
        # Add a pair of lamps (left and right) at given y
        # Left lamp - shifted inwards
        self.lamps.append(StreetLamp(100, y, "left", self.left_sprite, self.right_sprite))
        # Right lamp - shifted inwards
        self.lamps.append(StreetLamp(self.width - StreetLamp.SIZE - 100, y, "right", self.left_sprite, self.right_sprite))

        
    def update(self, speed):
        # Move lamps
        for lamp in self.lamps:
            lamp.update(speed)
            
        # Remove off-screen lamps
        self.lamps = [lamp for lamp in self.lamps if lamp.is_visible(self.height)]
        
        # Add new lamps at the top if needed
        # Find the highest lamp
        min_y = min((lamp.y for lamp in self.lamps), default=self.height)
        
        if min_y > -StreetLamp.SIZE:
            next_y = min_y - self.vertical_spacing
            self._add_lamp_pair(next_y)
            
    def draw(self, surface):
        for lamp in self.lamps:
            lamp.draw(surface)
            
    def check_collision(self, rect, lateral_movement=0):
        # Check collision with all lamps
        test_rect = rect
        if lateral_movement != 0:
            test_rect = pygame.Rect(rect.x + lateral_movement, rect.y, rect.width, rect.height)
            
        for lamp in self.lamps:
            if lamp.check_collision(test_rect):
                return True
        return False

# -------------------------
# DUSTBIN MANAGER CLASS
# -------------------------
class DustbinManager:
    def __init__(self, width, height, dustbin_sprite):
        self.width = width
        self.height = height
        self.dustbin_sprite = dustbin_sprite
        self.dustbins = []
        self.vertical_spacing = Dustbin.GAP
        
        # self._initialize_dustbins() # Don't spawn initially
        self.last_spawn_time = 0
        self.spawn_interval = 3000 # Spawn every 3 seconds roughly
        
    def _initialize_dustbins(self):
        num_dustbins = self.height // self.vertical_spacing + 2
        for i in range(num_dustbins):
            y = self.height - (i * self.vertical_spacing) - (self.vertical_spacing // 2)
            # Alternate sides or random? Let's alternate for balance
            side = "left" if i % 2 == 0 else "right"
            self._add_dustbin(y, side)
            
    def _add_dustbin(self, y, side, lamp_manager=None, tree_manager=None):
        if side == "left":
            x = 140  # Next to left sidewalk
        else:
            x = self.width - 140 - Dustbin.SIZE  # Next to right sidewalk
            
        # Check for overlap with lamps and trees
        test_rect = pygame.Rect(x, y, Dustbin.SIZE, Dustbin.SIZE)
        safe = True
        
        if lamp_manager:
            for lamp in lamp_manager.lamps:
                # Check pole rect or base rect? Lamps are tall.
                # Let's check proximity in Y since X is fixed.
                # Lamps are at 100 and width-100. Dustbins at 140 and width-140.
                # They are close in X. If Y is close, they overlap visually.
                if abs(lamp.y - y) < 60: # Dustbin size + margin
                    safe = False
                    break
        
        if safe and tree_manager:
            for tree in tree_manager.trees:
                if abs(tree.y - y) < 60:
                    safe = False
                    break
                    
        if safe:
            self.dustbins.append(Dustbin(x, y, self.dustbin_sprite))
        
    def update(self, speed, lamp_manager=None, tree_manager=None):
        for dustbin in self.dustbins:
            dustbin.update(speed)
            
        self.dustbins = [d for d in self.dustbins if d.is_visible(self.height)]
        
        # Add new dustbins at the top if needed - REMOVED to prevent double spawning
        # min_y = min((d.y for d in self.dustbins), default=self.height)
        
        # if min_y > -Dustbin.SIZE:
        #     next_y = min_y - self.vertical_spacing
        #     # Determine side based on last added (to maintain alternating pattern)
        #     # If we just removed the bottom one, we need to know what the top one is
        #     # Simple toggle based on count isn't reliable if we remove from bottom
        #     # So we look at the highest one's position
        #     highest_dustbin = min(self.dustbins, key=lambda d: d.y) if self.dustbins else None
            
        #     if highest_dustbin and highest_dustbin.x < self.width // 2: # It's on left
        #         side = "right"
        #     else:
        #         side = "left"
        #     self._add_dustbin(next_y, side, lamp_manager, tree_manager)
            
        # Time-based spawning for random dustbins
        current_time = pygame.time.get_ticks()
        if current_time - self.last_spawn_time > self.spawn_interval:
             self.last_spawn_time = current_time
             if random.random() < 0.4: # 40% chance to spawn
                 side = "left" if random.random() < 0.5 else "right"
                 self._add_dustbin(-Dustbin.SIZE, side, lamp_manager, tree_manager)
        
            
    def draw(self, surface):
        for dustbin in self.dustbins:
            dustbin.draw(surface)
            
    def check_collision(self, rect, lateral_movement=0):
        test_rect = rect
        if lateral_movement != 0:
            test_rect = pygame.Rect(rect.x + lateral_movement, rect.y, rect.width, rect.height)
            
        for dustbin in self.dustbins:
            if dustbin.check_collision(test_rect):
                return True
        return False

# -------------------------
# POLICE MANAGER CLASS
# -------------------------
class PoliceManager:
    def __init__(self, width, height, police_sprite):
        self.width = width
        self.height = height
        self.police_sprite = police_sprite
        self.polices = []
        self.spawn_interval = 1500  # Milliseconds - Increased frequency
        self.last_spawn_time = 0
        
        self._initialize_polices()
        
    def _get_random_position(self, y, existing_objects, lamp_manager, dustbin_manager, teargas_manager, barricade_manager, tree_manager, ambulance_manager):
        """Find a valid x position that doesn't overlap with other objects"""
        # Define lanes or valid areas
        # Adjust margins to avoid side lanes (Dustbins/Lamps)
        # Dustbins are at 140 + 70 = 210. Safe starts at 220.
        min_x = 220
        max_x = self.width - 220 - Police.SIZE
        
        attempts = 0
        while attempts < 10:
            attempts += 1
            x = random.randint(min_x, max_x)
            
            # Check overlap with existing police in this batch
            if self._check_overlap(x, y, existing_objects):
                continue
                
            # Check overlap with lamps (poles)
            if lamp_manager:
                # Lamps are at edges, but check just in case
                lamp_objects = []
                for lamp in lamp_manager.lamps:
                    if abs(lamp.y - y) < 100:
                        lamp_objects.append(lamp)
                if self._check_overlap(x, y, lamp_objects):
                    continue

            # Check overlap with dustbins
            if dustbin_manager:
                dustbin_objects = []
                for d in dustbin_manager.dustbins:
                    if abs(d.y - y) < 100:
                        dustbin_objects.append(d)
                if self._check_overlap(x, y, dustbin_objects):
                    continue
            
            # Check overlap with tear gas
            if teargas_manager:
                teargas_objects = []
                for teargas in teargas_manager.teargases:
                    if abs(teargas.y - y) < 150:  # Only check nearby tear gas
                        teargas_objects.append(teargas)
                if self._check_overlap(x, y, teargas_objects):
                    continue
            # Check overlap with barricades
            if barricade_manager:
                barricade_objects = []
                for b in barricade_manager.barricades:
                    if abs(b.y - y) < 150:
                        barricade_objects.append(b)
                if self._check_overlap(x, y, barricade_objects):
                    continue
            # Check overlap with trees
            if tree_manager:
                tree_objects = []
                for t in tree_manager.trees:
                    if abs(t.y - y) < 150:
                        tree_objects.append(t)
                if self._check_overlap(x, y, tree_objects):
                    continue
            
            # Check ambulance reserved paths
            if ambulance_manager:
                reserved_rects = ambulance_manager.get_reserved_rects()
                test_rect = pygame.Rect(x, y, Police.SIZE, Police.SIZE)
                blocked = any(test_rect.colliderect(r) for r in reserved_rects)
                if blocked:
                    continue
            return x
        
        # If no valid position found after max attempts, return None to skip spawn
        return None
    
    def _check_overlap(self, x, y, existing_objects, min_distance=100):
        """Check if position overlaps with existing objects"""
        test_rect = pygame.Rect(x, y, Police.SIZE, Police.SIZE)
        for obj in existing_objects:
            obj_rect = None
            if hasattr(obj, 'get_rect'):
                obj_rect = obj.get_rect()
            elif hasattr(obj, 'rect'):
                obj_rect = obj.rect
            elif hasattr(obj, 'get_pole_rect'): # For lamps
                obj_rect = obj.get_pole_rect()
            
            if obj_rect:
                # Expand rect slightly for spacing
                expanded_rect = obj_rect.inflate(min_distance, min_distance)
                if test_rect.colliderect(expanded_rect):
                    return True
        return False
    
    def _initialize_polices(self):
        """Initialize police obstacles randomly"""
        # Time-based spawning, no initial setup needed
        pass
    
    def update(self, speed, score=0, current_time=0, lamp_manager=None, dustbin_manager=None, teargas_manager=None, barricade_manager=None, tree_manager=None, ambulance_manager=None, decoration_manager=None):
        """Update all police obstacles and recycle as needed - time-based spawning"""
        # Update existing police
        for police in self.polices:
            police.update(speed)
        
        # Remove off-screen police
        self.polices = [p for p in self.polices if p.is_visible(self.height)]
        
        # Time-based spawning (looped)
        # Calculate spawn rate based on score
        if score < 200:
            effective_interval = int(self.spawn_interval * 1.2)
        elif score < 400:
            effective_interval = int(self.spawn_interval * 1.0)
        elif score < 600:
            effective_interval = int(self.spawn_interval * 0.85)
        else:
            effective_interval = int(self.spawn_interval * 0.75)
        
        # Spawn police at intervals
        if current_time - self.last_spawn_time >= effective_interval:
            self.last_spawn_time = current_time
            
            # Determine number of police to spawn based on score
            if score < 300:
                num_police = random.choices([1, 2], weights=[75, 25])[0]
            elif score < 700:
                num_police = random.choices([1, 2, 3], weights=[35, 55, 10])[0]
            else:
                num_police = random.choices([1, 2, 3], weights=[20, 55, 25])[0]
            
            # Spawn police at the top
            spawn_y = -Police.SIZE
            spawned_positions = []
            for _ in range(num_police):
                x = self._get_random_position(
                    spawn_y, 
                    spawned_positions + self.polices,
                    lamp_manager, 
                    dustbin_manager, 
                    teargas_manager,
                    barricade_manager,
                    tree_manager,
                    ambulance_manager
                )
                
                if x is not None:
                    new_police = Police(x, spawn_y, self.police_sprite)
                    self.polices.append(new_police)
                    spawned_positions.append(new_police)
                    
                    # Try to spawn decoration (Rage Mode only feature, controlled by presence of decoration_manager)
                    if decoration_manager:
                        decoration_manager.spawn_near_police(
                            new_police, 
                            spawned_positions + self.polices, # Check against other police
                            lamp_manager,
                            dustbin_manager,
                            teargas_manager,
                            barricade_manager,
                            tree_manager,
                            ambulance_manager
                        )
    
    def check_collision(self, rect, lateral_movement=0, forward_speed=0, backward_speed=0):
        """Check collision with player rect"""
        test_rect = rect
        if lateral_movement != 0:
            test_rect = pygame.Rect(rect.x + lateral_movement, rect.y, rect.width, rect.height)
        
        for police in self.polices:
            if forward_speed > 0:
                offset = (Police.SIZE - Police.COLLISION_SIZE) // 2
                police_rect = pygame.Rect(police.x + offset, police.y + offset + forward_speed, 
                                          Police.COLLISION_SIZE, Police.COLLISION_SIZE)
            elif backward_speed > 0:
                offset = (Police.SIZE - Police.COLLISION_SIZE) // 2
                police_rect = pygame.Rect(police.x + offset, police.y + offset - backward_speed,
                                          Police.COLLISION_SIZE, Police.COLLISION_SIZE)
            else:
                police_rect = police.get_rect()
            
            if test_rect.colliderect(police_rect):
                return True
        return False
    
    def check_damage_collision(self, rect):
        """Check collision and return the police object if collision occurs, None otherwise"""
        for police in self.polices:
            if rect.colliderect(police.get_rect()):
                return police
        return None
    
    def draw(self, surface):
        """Draw all police obstacles"""
        for police in self.polices:
            police.draw(surface)

    def set_spawn_interval(self, interval):
        self.spawn_interval = interval

# -------------------------
# TEAR GAS MANAGER CLASS
# -------------------------
class TearGasManager:
    def __init__(self, width, height, teargas_sprites):
        self.width = width
        self.height = height
        self.teargas_sprites = teargas_sprites  # List of sprites
        self.teargases = []  # Random/middle tear gas
        self.edge_teargases_left = []   # Active left-side instances (capped to 1)
        self.edge_teargases_right = []  # Active right-side instances (capped to 1)
        self.current_gap = TearGas.BASE_GAP
        self.min_score = 15  # Start a touch earlier
        self.edge_spacing = 200
        # Timed, alternating single-instance edge spawns
        self.edge_spawn_interval = 1800  # milliseconds; slightly more frequent
        self.last_edge_spawn_time = 0
        # Alternate between edges only (no middle)
        self.spawn_cycle = ["left", "middle", "right"]
        self.spawn_cycle_index = 0
        # Do not pre-initialize continuous edge gas
        # self._initialize_teargases()  # intentionally not called to avoid early gas
    
    def set_gap(self, gap):
        """Update the gap between tear gas obstacles"""
        self.current_gap = gap
    
    def _check_overlap(self, x, y, existing_objects, min_distance=120):
        """Check if position overlaps with existing objects"""
        test_rect = pygame.Rect(x, y, TearGas.SIZE, TearGas.SIZE)
        for obj in existing_objects:
            obj_rect = None
            if hasattr(obj, 'get_rect'):
                obj_rect = obj.get_rect()
            elif hasattr(obj, 'rect'):
                obj_rect = obj.rect
            
            if obj_rect:
                # Expand rect slightly for spacing
                expanded_rect = obj_rect.inflate(min_distance, min_distance)
                if test_rect.colliderect(expanded_rect):
                    return True
        return False
    
    def _get_random_position(self, y, existing_objects, lamp_manager, dustbin_manager, police_manager, barricade_manager, tree_manager, ambulance_manager):
        """Find a valid x position"""
        # Middle area - Avoiding side lanes
        min_x = 220
        max_x = self.width - 220 - TearGas.SIZE
        
        attempts = 0
        while attempts < 10:
            attempts += 1
            x = random.randint(min_x, max_x)
            
            # Check overlap with existing tear gas
            if self._check_overlap(x, y, existing_objects):
                continue
            
            # Check overlap with dustbins - STILL CHECK just in case
            if dustbin_manager:
                dustbin_objects = [d for d in dustbin_manager.dustbins if abs(d.y - y) < 150]
                if self._check_overlap(x, y, dustbin_objects):
                    continue
            
            # Check overlap with police
            if police_manager:
                police_objects = []
                for p in police_manager.polices:
                    if abs(p.y - y) < 150:
                        police_objects.append(p)
                if self._check_overlap(x, y, police_objects):
                    continue
                    
            # Check overlap with barricades
            if barricade_manager:
                barricade_objects = []
                for b in barricade_manager.barricades:
                    if abs(b.y - y) < 150:
                        barricade_objects.append(b)
                if self._check_overlap(x, y, barricade_objects):
                    continue
            
            # Check overlap with trees
            if tree_manager:
                tree_objects = []
                for t in tree_manager.trees:
                    if abs(t.y - y) < 150:
                        tree_objects.append(t)
                if self._check_overlap(x, y, tree_objects):
                    continue
            
            # Check ambulance reserved paths
            if ambulance_manager:
                reserved_rects = ambulance_manager.get_reserved_rects()
                test_rect = pygame.Rect(x, y, TearGas.SIZE, TearGas.SIZE)
                blocked = any(test_rect.colliderect(r) for r in reserved_rects)
                if blocked:
                    continue
            
            return x
        
        return min_x if random.random() < 0.5 else max_x
    
    def update(self, speed, score=0, current_time=0, lamp_manager=None, dustbin_manager=None, police_manager=None, barricade_manager=None, tree_manager=None, ambulance_manager=None):
        """Update tear gas obstacles"""
        # Update existing tear gas
        for teargas in self.teargases:
            teargas.update(speed)
        for teargas in self.edge_teargases_left:
            teargas.update(speed)
        for teargas in self.edge_teargases_right:
            teargas.update(speed)
            
        # Remove off-screen
        self.teargases = [t for t in self.teargases if t.is_visible(self.height)]
        self.edge_teargases_left = [t for t in self.edge_teargases_left if t.is_visible(self.height)]
        self.edge_teargases_right = [t for t in self.edge_teargases_right if t.is_visible(self.height)]
        
        # Only spawn if score is high enough
        if score >= self.min_score:
            # Adjust gap based on score
            if score < 50:
                self.current_gap = TearGas.BASE_GAP
                self.edge_spawn_interval = 1800
            elif score < 150:
                self.current_gap = int(TearGas.BASE_GAP * 0.85)
                self.edge_spawn_interval = 1500
            else:
                self.current_gap = int(TearGas.BASE_GAP * 0.7)
                self.edge_spawn_interval = 1200
            
            # Timed spawning logic
            if current_time - self.last_edge_spawn_time >= self.edge_spawn_interval:
                self.last_edge_spawn_time = current_time
                
                spawn_type = self.spawn_cycle[self.spawn_cycle_index]
                self.spawn_cycle_index = (self.spawn_cycle_index + 1) % len(self.spawn_cycle)
                
                spawn_y = -TearGas.SIZE
                
                if spawn_type == "left":
                    # Spawn one on left edge (footpath)
                    x = 10 # Most left edge
                    self.edge_teargases_left.append(TearGas(x, spawn_y, self.teargas_sprites))
                elif spawn_type == "right":
                    # Spawn one on right edge (footpath)
                    x = self.width - TearGas.SIZE - 10 # Most right edge
                    self.edge_teargases_right.append(TearGas(x, spawn_y, self.teargas_sprites))
                else: # "middle"
                    # Spawn one in random middle position
                    x = self._get_random_position(
                        spawn_y, 
                        self.teargases + self.edge_teargases_left + self.edge_teargases_right,
                        lamp_manager, 
                        dustbin_manager, 
                        police_manager,
                        barricade_manager,
                        tree_manager,
                        ambulance_manager
                    )
                    self.teargases.append(TearGas(x, spawn_y, self.teargas_sprites))
    
    def draw(self, surface):
        for teargas in self.teargases:
            teargas.draw(surface)
        for teargas in self.edge_teargases_left:
            teargas.draw(surface)
        for teargas in self.edge_teargases_right:
            teargas.draw(surface)

    def check_damage_collision(self, rect):
        """Check collision with tear gas and return True if collision occurs"""
        for teargas in self.teargases + self.edge_teargases_left + self.edge_teargases_right:
            if rect.colliderect(teargas.get_rect()):
                return True
        return False

# -------------------------
# TOKEN MANAGER CLASS
# -------------------------
class TokenManager:
    def __init__(self, width, height, token_sprite):
        self.width = width
        self.height = height
        self.token_sprite = token_sprite
        self.tokens = []
        self.spawn_interval = 1500  # ms
        self.last_spawn_time = 0
    
    def _check_overlap(self, x, y, existing_objects, min_distance=60):
        test_rect = pygame.Rect(x, y, Token.SIZE, Token.SIZE)
        for obj in existing_objects:
            obj_rect = None
            if hasattr(obj, 'get_rect'):
                obj_rect = obj.get_rect()
            elif hasattr(obj, 'rect'):
                obj_rect = obj.rect
            elif hasattr(obj, 'get_pole_rect'):
                obj_rect = obj.get_pole_rect()
            
            if obj_rect:
                expanded_rect = obj_rect.inflate(min_distance, min_distance)
                if test_rect.colliderect(expanded_rect):
                    return True
        return False
    
    def _get_random_position(self, y, lamp_manager, dustbin_manager, police_manager, teargas_manager, barricade_manager, tree_manager, ambulance_manager):
        min_x = 220
        max_x = self.width - 220 - Token.SIZE
        
        attempts = 0
        while attempts < 10:
            attempts += 1
            x = random.randint(min_x, max_x)
            
            # Check overlap with dustbins
            if dustbin_manager:
                dustbin_objects = [d for d in dustbin_manager.dustbins if abs(d.y - y) < 100]
                if self._check_overlap(x, y, dustbin_objects):
                    continue
            
            # Check overlap with police
            if police_manager:
                police_objects = [p for p in police_manager.polices if abs(p.y - y) < 100]
                if self._check_overlap(x, y, police_objects):
                    continue
            # Check overlap with tear gas
            if teargas_manager:
                teargas_objects = [t for t in teargas_manager.teargases if abs(t.y - y) < 100]
                if self._check_overlap(x, y, teargas_objects):
                    continue
            # Check overlap with barricades
            if barricade_manager:
                barricade_objects = [b for b in barricade_manager.barricades if abs(b.y - y) < 100]
                if self._check_overlap(x, y, barricade_objects):
                    continue
            # Check overlap with trees
            if tree_manager:
                tree_objects = [t for t in tree_manager.trees if abs(t.y - y) < 100]
                if self._check_overlap(x, y, tree_objects):
                    continue
            
            # Check overlap with lamps
            if lamp_manager:
                lamp_objects = [l for l in lamp_manager.lamps if abs(l.y - y) < 100]
                if self._check_overlap(x, y, lamp_objects):
                    continue

            # Check overlap with ambulances
            if ambulance_manager:
                ambulance_objects = [a for a in ambulance_manager.ambulances if abs(a.y - y) < 200] # Larger buffer for ambulance
                if self._check_overlap(x, y, ambulance_objects):
                    continue
            
            return x
        return min_x if random.random() < 0.5 else max_x

    def update(self, speed, current_time, lamp_manager, dustbin_manager, police_manager, teargas_manager, barricade_manager, tree_manager, ambulance_manager):
        for token in self.tokens:
            token.update(speed)
        self.tokens = [t for t in self.tokens if t.is_visible(self.height)]
        
        if current_time - self.last_spawn_time >= self.spawn_interval:
            self.last_spawn_time = current_time
            spawn_y = -Token.SIZE
            x = self._get_random_position(spawn_y, lamp_manager, dustbin_manager, police_manager, teargas_manager, barricade_manager, tree_manager, ambulance_manager)
            self.tokens.append(Token(x, spawn_y, self.token_sprite))
    
    def check_collection(self, player_rect):
        collected_count = 0
        remaining_tokens = []
        for token in self.tokens:
            if player_rect.colliderect(token.get_rect()):
                collected_count += 1
            else:
                remaining_tokens.append(token)
        self.tokens = remaining_tokens
        return collected_count

    def collect_if_overlap(self, player_rect):
        return self.check_collection(player_rect)
    
    def draw(self, surface):
        for token in self.tokens:
            token.draw(surface)

# -------------------------
# AMBULANCE MANAGER CLASS
# -------------------------
class AmbulanceManager:
    def __init__(self, width, height, ambulance_frames, danger_img):
        self.width = width
        self.height = height
        self.ambulance_frames = ambulance_frames
        self.danger_img = danger_img
        self.ambulances = []
        self.spawn_interval = 8000  # Base interval (8 seconds)
        self.last_spawn_time = 0
        self.min_score = 50  # Start appearing after score 50
        self.warning_duration = 2000  # 2 seconds warning
        self.pending_spawns = []  # List of (spawn_time, x_pos)
    
    def get_reserved_rects(self):
        """Return rects of areas reserved for incoming ambulances (including warnings)"""
        rects = []
        # Add rects for active ambulances
        for amb in self.ambulances:
            rects.append(pygame.Rect(amb.x, -1000, Ambulance.SIZE, self.height + 2000))
        # Add rects for pending spawns
        for _, x in self.pending_spawns:
            rects.append(pygame.Rect(x, -1000, Ambulance.SIZE, self.height + 2000))
        return rects
    
    def _get_random_lane(self, lamp_manager, dustbin_manager, police_manager, teargas_manager, barricade_manager, tree_manager):
        """Find a clear vertical lane"""
        # Define potential lanes (x coordinates)
        # Try 5 evenly spaced lanes
        margin = 180
        available_width = self.width - 2 * margin - Ambulance.SIZE
        lanes = [margin + i * (available_width // 4) for i in range(5)]
        random.shuffle(lanes)
        
        for x in lanes:
            # Check if this lane is relatively clear of other obstacles
            # We check a vertical strip
            lane_rect = pygame.Rect(x, -100, Ambulance.SIZE, self.height + 200)
            
            # Count collisions with other objects
            collisions = 0
            
            if police_manager:
                for p in police_manager.polices:
                    if lane_rect.colliderect(p.get_rect()):
                        collisions += 1
            
            if teargas_manager:
                for t in teargas_manager.teargases:
                    if lane_rect.colliderect(t.get_rect()):
                        collisions += 1
            
            if barricade_manager:
                for b in barricade_manager.barricades:
                    if lane_rect.colliderect(b.get_rect()):
                        collisions += 1
            
            if tree_manager:
                for t in tree_manager.trees:
                    if lane_rect.colliderect(t.get_rect()):
                        collisions += 1
            
            if dustbin_manager:
                for d in dustbin_manager.dustbins:
                    if lane_rect.colliderect(d.get_rect()):
                        collisions += 1
            
            # If lane is not too crowded, use it
            if collisions <= 1:
                return x
        
        # Fallback
        return lanes[0]
    
    def update(self, road_speed, score, current_time, lamp_manager, dustbin_manager, police_manager, teargas_manager, barricade_manager, tree_manager, selected_mode="start_normal"):
        # Update active ambulances
        for amb in self.ambulances:
            amb.update(road_speed, selected_mode)
            
            # Check for collisions with other obstacles and push them aside
            amb_rect = amb.get_rect()
            
            if police_manager:
                for police in police_manager.polices:
                    if amb_rect.colliderect(police.get_rect()):
                        # Push police aside (laterally) - don't disappear
                        if police.x < amb.x + Ambulance.SIZE / 2:
                            police.x = amb.x - Police.SIZE - 10 # Push left
                        else:
                            police.x = amb.x + Ambulance.SIZE + 10 # Push right
            
            if barricade_manager:
                for barricade in barricade_manager.barricades:
                    if amb_rect.colliderect(barricade.get_rect()):
                        # Push barricade aside - don't disappear
                        if barricade.x < amb.x + Ambulance.SIZE / 2:
                            barricade.x = amb.x - 100 # Push left
                        else:
                            barricade.x = amb.x + Ambulance.SIZE + 10 # Push right
            
            # Tear gas overlap allowed - do nothing
            # if teargas_manager: ...
        
        # Remove off-screen
        self.ambulances = [a for a in self.ambulances if a.is_visible(self.height)]
        
        # Handle pending spawns (warnings)
        active_warnings = []
        for spawn_time, x in self.pending_spawns:
            if current_time >= spawn_time:
                # Time to spawn
                self.ambulances.append(Ambulance(x, -Ambulance.SIZE, self.ambulance_frames, score))
            else:
                active_warnings.append((spawn_time, x))
        self.pending_spawns = active_warnings
        
        # Spawn logic
        if score >= self.min_score:
            # Adjust interval based on score
            if score < 200:
                current_interval = self.spawn_interval
            elif score < 500:
                current_interval = int(self.spawn_interval * 0.8)
            else:
                current_interval = int(self.spawn_interval * 0.6)
            
            if current_time - self.last_spawn_time >= current_interval:
                self.last_spawn_time = current_time
                
                # Choose a lane
                x = self._get_random_lane(lamp_manager, dustbin_manager, police_manager, teargas_manager, barricade_manager, tree_manager)
                
                # Add to pending spawns (schedule for future)
                spawn_time = current_time + self.warning_duration
                self.pending_spawns.append((spawn_time, x))
    
    def check_collision(self, player_rect):
        """Check collision with player"""
        for amb in self.ambulances:
            if not amb.has_collided and player_rect.colliderect(amb.get_rect()):
                amb.has_collided = True
                amb.collision_cooldown = 60  # 1 second cooldown
                return amb
        return None
    
    def draw(self, surface):
        # Draw active ambulances
        for amb in self.ambulances:
            amb.draw(surface)
        
        # Draw warnings for pending spawns
        current_time = pygame.time.get_ticks()
        for spawn_time, x in self.pending_spawns:
            # Blink effect
            if (current_time // 200) % 2 == 0:
                if self.danger_img:
                    # Draw danger sign at TOP of screen in that lane
                    surface.blit(self.danger_img, (x + (Ambulance.SIZE - 60)//2, 5))

# -------------------------
# BARRICADE MANAGER CLASS
# -------------------------
class BarricadeManager:
    def __init__(self, width, height, barricade1_sprite, barricade2_sprite):
        self.width = width
        self.height = height
        self.barricade1_sprite = barricade1_sprite
        self.barricade2_sprite = barricade2_sprite
        self.barricades = []
        self.spawn_interval = 1800  # ms - Increased frequency
        self.last_spawn_time = 0
        self.min_score = 30
    
    def _check_overlap(self, x, y, existing_objects, min_distance=100):
        test_rect = pygame.Rect(x, y, Barricade.SIZE, Barricade.SIZE)
        for obj in existing_objects:
            obj_rect = None
            if hasattr(obj, 'get_rect'):
                obj_rect = obj.get_rect()
            elif hasattr(obj, 'rect'):
                obj_rect = obj.rect
            elif hasattr(obj, 'get_pole_rect'): # Handle StreetLamp
                obj_rect = obj.get_pole_rect()
            
            if obj_rect:
                expanded_rect = obj_rect.inflate(min_distance, min_distance)
                if test_rect.colliderect(expanded_rect):
                    return True
        return False
    
    def _get_random_position(self, y, existing_objects, lamp_manager, dustbin_manager, police_manager, teargas_manager, tree_manager, ambulance_manager):
        # Adjust margins to avoid side lanes (Lamps/Trees)
        # Lamps are at ~100 and ~WIDTH-100-SIZE. Trees are similar.
        # Safe zone is roughly 250 to WIDTH-250
        # Safe zone is roughly 250 to WIDTH-250 to avoid everything
        min_x = 250
        max_x = self.width - 250 - Barricade.SIZE
        
        attempts = 0
        while attempts < 10:
            attempts += 1
            x = random.randint(min_x, max_x)
            
            if self._check_overlap(x, y, existing_objects):
                continue
            
            if dustbin_manager:
                dustbin_objects = [d for d in dustbin_manager.dustbins if abs(d.y - y) < 100]
                if self._check_overlap(x, y, dustbin_objects):
                    continue
            
            if police_manager:
                police_objects = [p for p in police_manager.polices if abs(p.y - y) < 150]
                if self._check_overlap(x, y, police_objects):
                    continue
            
            if teargas_manager:
                teargas_objects = [t for t in teargas_manager.teargases if abs(t.y - y) < 150]
                if self._check_overlap(x, y, teargas_objects):
                    continue
            
            # Check overlap with trees
            if tree_manager:
                tree_objects = []
                for t in tree_manager.trees:
                    if abs(t.y - y) < 150:
                        tree_objects.append(t)
                if self._check_overlap(x, y, tree_objects):
                    continue
            
            # Check overlap with lamps (poles)
            if lamp_manager:
                lamp_objects = []
                for lamp in lamp_manager.lamps:
                    if abs(lamp.y - y) < 100:
                        lamp_objects.append(lamp)
                if self._check_overlap(x, y, lamp_objects):
                    continue
            
            if tree_manager:
                tree_objects = [t for t in tree_manager.trees if abs(t.y - y) < 150]
                if self._check_overlap(x, y, tree_objects):
                    continue
            
            if ambulance_manager:
                reserved_rects = ambulance_manager.get_reserved_rects()
                test_rect = pygame.Rect(x, y, Barricade.SIZE, Barricade.SIZE)
                blocked = any(test_rect.colliderect(r) for r in reserved_rects)
                if blocked:
                    continue
            
            return x
        # If no valid position found after max attempts, return None to skip spawn
        return None
    
    def update(self, speed, current_time, lamp_manager, dustbin_manager, police_manager, teargas_manager, tree_manager, ambulance_manager):
        for barricade in self.barricades:
            barricade.update(speed)
        self.barricades = [b for b in self.barricades if b.is_visible(self.height)]
        
        if current_time - self.last_spawn_time >= self.spawn_interval:
            self.last_spawn_time = current_time
            
            # Randomly choose type
            b_type = "barricade1" if random.random() < 0.5 else "barricade2"
            sprite = self.barricade1_sprite if b_type == "barricade1" else self.barricade2_sprite
            
            spawn_y = -Barricade.SIZE
            x = self._get_random_position(
                spawn_y, 
                self.barricades, 
                lamp_manager, 
                dustbin_manager, 
                police_manager, 
                teargas_manager,
                tree_manager,
                ambulance_manager
            )
            
            if x is not None:
                self.barricades.append(Barricade(x, spawn_y, sprite, b_type))
    
    def check_collision(self, rect, lateral_movement=0):
        test_rect = rect
        if lateral_movement != 0:
            test_rect = pygame.Rect(rect.x + lateral_movement, rect.y, rect.width, rect.height)
        
        for barricade in self.barricades:
            if barricade.check_collision(test_rect):
                return True
        return False

    def check_damage_collision(self, rect):
        """Check collision and return True if collision occurs"""
        for barricade in self.barricades:
            if rect.colliderect(barricade.get_rect()):
                return True
        return False

    def check_player_stuck(self, player_rect, player_y, screen_height):
        """Check if player is stuck in a barricade (e.g. pushed off screen)"""
        # If player is colliding with a barricade and is very close to bottom
        for barricade in self.barricades:
            if player_rect.colliderect(barricade.get_rect()):
                # If player is at the bottom and colliding, they are likely stuck/crushed
                if player_y >= screen_height - player_rect.height - 10:
                    return True
        return False
    
    def draw(self, surface):
        for barricade in self.barricades:
            barricade.draw(surface)

    def set_spawn_interval(self, interval):
        self.spawn_interval = interval

# -------------------------
# DECORATION MANAGER CLASS
# -------------------------
class Decoration:
    def __init__(self, x, y, image):
        self.x = x
        self.y = y
        self.image = image
        self.width = image.get_width()
        self.height = image.get_height()
        
    def update(self, speed):
        self.y += speed
        
    def draw(self, surface):
        surface.blit(self.image, (self.x, self.y))
        
    def is_visible(self, height):
        return self.y < height

class DecorationManager:
    def __init__(self, width, height, dead1_img, dead3_img, blood_img):
        self.width = width
        self.height = height
        self.dead1_img = dead1_img
        self.dead3_img = dead3_img
        self.blood_img = blood_img
        self.decorations = []
        
    def spawn_near_police(self, police, existing_objects, lamp_manager, dustbin_manager, teargas_manager, barricade_manager, tree_manager, ambulance_manager):
        """Spawn a decoration near the given police object if possible"""
        # Always attempt to spawn (removed 50% skip)

        # Choose type
        r = random.random()
        if r < 0.30: # Increased Dead1
            img = self.dead1_img
        elif r < 0.60: # Increased Dead3
            img = self.dead3_img
        else:
            img = self.blood_img
            
        if not img:
            return

        # Try to find a spot near the police
        # Police is at police.x, police.y
        # We want it nearby, maybe slightly offset
        
        attempts = 0
        while attempts < 25: # Increased attempts further
            attempts += 1
            # Random offset - Widened search area
            offset_x = random.randint(-150, 150) # Widened further for footpaths
            offset_y = random.randint(-80, 80)
            
            x = police.x + offset_x
            y = police.y + offset_y
            
            # Keep within SCREEN bounds (allow footpaths)
            if x < 0 or x > self.width - img.get_width():
                continue
                
            # Check overlap with EVERYTHING except player
            # We reuse the logic from other managers but we need to be careful
            # We can't easily access "all objects" unless passed.
            # We'll do a quick check against passed managers.
            
            test_rect = pygame.Rect(x, y, img.get_width(), img.get_height())
            
            if self._check_overlap(test_rect, existing_objects): continue
            if self._check_overlap(test_rect, police.get_rect()): continue # Don't overlap the police itself too much? Or maybe it's fine? User said "near police". Let's avoid direct overlap with the police unit itself so it looks like it's *next* to them.
            
            # Check other managers
            if lamp_manager and self._check_manager_overlap(test_rect, lamp_manager.lamps): continue
            if dustbin_manager and self._check_manager_overlap(test_rect, dustbin_manager.dustbins): continue
            if teargas_manager and self._check_manager_overlap(test_rect, teargas_manager.teargases): continue
            if barricade_manager and self._check_manager_overlap(test_rect, barricade_manager.barricades): continue
            if tree_manager and self._check_manager_overlap(test_rect, tree_manager.trees): continue
            if ambulance_manager and self._check_manager_overlap(test_rect, ambulance_manager.ambulances): continue
            
            # If we got here, it's a valid spot
            self.decorations.append(Decoration(x, y, img))
            break
            
    def _check_overlap(self, rect, objects):
        # Use a smaller rect for overlap checks to allow visual overlap
        # Deflate by 20 pixels on all sides
        check_rect = rect.inflate(-20, -20)
        
        # Handle single rect or list of objects
        if isinstance(objects, pygame.Rect):
             return check_rect.colliderect(objects)
             
        for obj in objects:
            obj_rect = None
            if hasattr(obj, 'get_rect'):
                obj_rect = obj.get_rect()
            elif hasattr(obj, 'rect'):
                obj_rect = obj.rect
            
            if obj_rect and check_rect.colliderect(obj_rect):
                return True
        return False

    def _check_manager_overlap(self, rect, objects):
        return self._check_overlap(rect, objects)

    def update(self, speed):
        for d in self.decorations:
            d.update(speed)
        self.decorations = [d for d in self.decorations if d.is_visible(self.height)]
        
    def draw(self, surface):
        for d in self.decorations:
            d.draw(surface)

# -------------------------
# TREE MANAGER CLASS
# -------------------------
class TreeManager:
    def __init__(self, width, height, tree_sprite, lamp_manager):
        self.width = width
        self.height = height
        self.tree_sprite = tree_sprite
        self.lamp_manager = lamp_manager
        self.trees = []
        self.vertical_offset = 100  # Distance below lamp
        
        self._initialize_trees()
    
    def _initialize_trees(self):
        # Clear existing trees to prevent duplicates
        self.trees = []
        # Place a tree below each lamp
        for lamp in self.lamp_manager.lamps:
            # Place directly below lamp; shift right-side trees further to the right
            if getattr(lamp, 'type', 'left') == 'right':
                shift = max(0, StreetLamp.SIZE - Tree.SIZE - 10)
                tree_x = lamp.x + shift
            else:
                # Shift left tree a little to the right
                tree_x = lamp.x + 20
            tree_y = lamp.y + self.vertical_offset
            self.trees.append(Tree(tree_x, tree_y, self.tree_sprite))
    
    def update(self, speed):
        # Move trees
        for t in self.trees:
            t.update(speed)
        # Remove off-screen
        self.trees = [t for t in self.trees if t.is_visible(self.height)]
        
        # Ensure there is a tree below each lamp (kept in sync as lamps recycle)
        existing_positions = {(t.x, int(t.y)) for t in self.trees}
        for lamp in self.lamp_manager.lamps:
            if getattr(lamp, 'type', 'left') == 'right':
                shift = max(0, StreetLamp.SIZE - Tree.SIZE - 10)
                tree_x = lamp.x + shift
            else:
                tree_x = lamp.x + 20
            tree_y = lamp.y + self.vertical_offset
            # Avoid overlap with lamp: only add when tree is fully below lamp
            if tree_y > lamp.y + StreetLamp.TOP_HEIGHT:
                # Check if a tree already exists near this position
                found = False
                for t in self.trees:
                    if abs(t.x - tree_x) < 5 and abs(t.y - tree_y) < 5:
                        found = True
                        break
                if not found:
                    self.trees.append(Tree(tree_x, tree_y, self.tree_sprite))
    
    def check_collision(self, rect, lateral_movement=0, forward_speed=0, backward_speed=0):
        test_rect = rect
        if lateral_movement != 0:
            test_rect = pygame.Rect(rect.x + lateral_movement, rect.y, rect.width, rect.height)
        for t in self.trees:
            if forward_speed > 0:
                t_rect = pygame.Rect(t.x, t.y + forward_speed, Tree.SIZE, Tree.SIZE)
            elif backward_speed > 0:
                t_rect = pygame.Rect(t.x, t.y - backward_speed, Tree.SIZE, Tree.SIZE)
            else:
                t_rect = t.get_rect()
            if test_rect.colliderect(t_rect):
                return True
        return False
    
    def draw(self, surface):
        for t in self.trees:
            t.draw(surface)
