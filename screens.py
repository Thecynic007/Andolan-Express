import pygame
import sys
import os
from settings import *
from ui import Button, TextInput
from utils import safe_load
from scoreboard import scoreboard
import assets

# Try to import multiplayer module, provide dummy if not found
try:
    import multiplayer
except ImportError:
    print("Multiplayer module not found. Multiplayer features will be disabled.")
    class DummyMultiplayer:
        def __init__(self, *args, **kwargs):
            pass
        def start_host(self):
            return False
        def connect_to_host(self):
            return False
        def disconnect(self):
            pass
        def update_player(self, data):
            pass
        def update_score(self, score):
            pass
        def get_opponent_data(self):
            return None
        def is_game_ready(self):
            return False
        def start_game(self):
            pass
        @property
        def player_id(self):
            return "player1"
        @property
        def is_host(self):
            return True
        @property
        def game_state(self):
            return {'player1': None, 'player2': None, 'game_started': False}
    multiplayer = type('Multiplayer', (), {'AndolanExpressMultiplayer': DummyMultiplayer})

# -------------------------
# NAME ENTRY SCREEN CLASS
# -------------------------
# -------------------------
# NAME ENTRY SCREEN CLASS
# -------------------------
class NameEntryScreen:
    def __init__(self, score, tokens, mode):
        self.score = int(score)
        self.tokens = int(tokens)
        self.mode = mode
        
        # Input field
        self.name_input = TextInput(WIDTH//2 - 150, 300, 300, 50)
        self.name_input.active = True
        
        # Buttons
        self.submit_button = Button(WIDTH//2 - 150, 380, 300, 60, "SUBMIT", GREEN, (0, 200, 0))
        self.cancel_button = Button(WIDTH//2 - 150, 460, 300, 60, "SKIP", LIGHT_BLUE, BLUE)
        
        self.message = ""
        self.message_timer = 0
        
        # Fade Effect
        self.alpha = 0
        self.target_alpha = 255
        self.fade_speed = 2 # Slow fade
        self.fade_start_time = pygame.time.get_ticks() + 1000 # 1 second delay before fade starts

    def handle_events(self, event):
        if event.type == pygame.QUIT:
            return "quit"
            
        # Only handle events if fully visible (or close to it) to prevent accidental clicks during fade
        if self.alpha > 200:
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
        
        # Update Fade
        if self.alpha < self.target_alpha:
            if pygame.time.get_ticks() > self.fade_start_time:
                self.alpha += self.fade_speed
                if self.alpha > self.target_alpha:
                    self.alpha = self.target_alpha
        
        mouse_pos = pygame.mouse.get_pos()
        self.submit_button.check_hover(mouse_pos)
        self.cancel_button.check_hover(mouse_pos)

    def draw(self, surface):
        # Create a temporary surface to handle alpha fading for everything
        temp_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        
        # Semi-transparent overlay
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        temp_surf.blit(overlay, (0, 0))
        
        # Title
        title = title_font.render("NEW RECORD!", True, YELLOW)
        temp_surf.blit(title, (WIDTH//2 - title.get_width()//2, 100))
        
        # Stats
        stats_text = menu_font.render(f"Score: {self.score} | Tokens: {self.tokens}", True, WHITE)
        temp_surf.blit(stats_text, (WIDTH//2 - stats_text.get_width()//2, 180))
        
        # Name input label
        label = menu_font.render("Enter Name:", True, WHITE)
        temp_surf.blit(label, (WIDTH//2 - label.get_width()//2, 260))
        
        self.name_input.draw(temp_surf)
        self.submit_button.draw(temp_surf)
        self.cancel_button.draw(temp_surf)
        
        if self.message:
            msg = info_font.render(self.message, True, RED)
            temp_surf.blit(msg, (WIDTH//2 - msg.get_width()//2, 520))
            
        # Apply alpha
        temp_surf.set_alpha(self.alpha)
        surface.blit(temp_surf, (0, 0))

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
            Button(WIDTH//2 - 150, 300, 300, 60, "PLAY AGAIN", GREEN, (0, 200, 0)),
            Button(WIDTH//2 - 150, 380, 300, 60, "MAIN MENU", LIGHT_BLUE, BLUE),
            Button(WIDTH//2 - 150, 460, 300, 60, "QUIT", RED, (200, 0, 0))
        ]
        
        self.name_entry = NameEntryScreen(score, tokens_collected, mode_name)
        self.show_name_entry = True
        
        # If NOT Rage Mode, skip fade (set alpha to max immediately)
        if self.mode_name != "RAGE":
            self.name_entry.alpha = 255

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
        # Draw Background Image for Rage Mode
        if self.mode_name == "RAGE" and assets.end_screen_img:
            surface.blit(assets.end_screen_img, (0, 0))
        
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
# MULTIPLAYER GAME OVER SCREEN
# -------------------------
class MultiplayerGameOverScreen:
    def __init__(self, p1_score, p1_tokens, p2_score, p2_tokens):
        self.p1_score = int(p1_score)
        self.p1_tokens = int(p1_tokens)
        self.p2_score = int(p2_score)
        self.p2_tokens = int(p2_tokens)
        
        # Determine Winner
        if self.p1_tokens > self.p2_tokens:
            self.winner = "PLAYER 1 WINS!"
            self.winner_color = BLUE
        elif self.p2_tokens > self.p1_tokens:
            self.winner = "PLAYER 2 WINS!"
            self.winner_color = RED
        else:
            # Tie breaker: Score
            if self.p1_score > self.p2_score:
                self.winner = "PLAYER 1 WINS! (Score Tie-break)"
                self.winner_color = BLUE
            elif self.p2_score > self.p1_score:
                self.winner = "PLAYER 2 WINS! (Score Tie-break)"
                self.winner_color = RED
            else:
                self.winner = "IT'S A DRAW!"
                self.winner_color = GREEN
        
        # Inputs
        self.p1_input = TextInput(200, 330, 250, 50)
        self.p2_input = TextInput(550, 330, 250, 50)
        self.p1_input.active = True  # Start with P1 active
        
        self.p1_submitted = False
        self.p2_submitted = False
        
        self.buttons = [
            Button(WIDTH//2 - 150, 480, 300, 60, "SUBMIT SCORES", GREEN, (0, 200, 0)),
            Button(WIDTH//2 - 150, 560, 300, 60, "SKIP", LIGHT_BLUE, BLUE)
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
        surface.blit(title, (surface.get_width()//2 - title.get_width()//2, 30))
        
        # Winner Display
        winner_text = title_font.render(self.winner, True, self.winner_color)
        surface.blit(winner_text, (surface.get_width()//2 - winner_text.get_width()//2, 100))
        
        # Player 1 Section (Left)
        p1_title = menu_font.render("PLAYER 1", True, LIGHT_BLUE)
        surface.blit(p1_title, (325 - p1_title.get_width()//2, 180))
        
        p1_score = font.render(f"Score: {self.p1_score}", True, WHITE)
        p1_tokens = font.render(f"Tokens: {self.p1_tokens}", True, YELLOW)
        surface.blit(p1_score, (325 - p1_score.get_width()//2, 230))
        surface.blit(p1_tokens, (325 - p1_tokens.get_width()//2, 255))
        
        self.p1_input.draw(surface)
        
        # Player 2 Section (Right)
        p2_title = menu_font.render("PLAYER 2", True, LIGHT_BLUE)
        surface.blit(p2_title, (675 - p2_title.get_width()//2, 180))
        
        p2_score = font.render(f"Score: {self.p2_score}", True, WHITE)
        p2_tokens = font.render(f"Tokens: {self.p2_tokens}", True, YELLOW)
        surface.blit(p2_score, (675 - p2_score.get_width()//2, 230))
        surface.blit(p2_tokens, (675 - p2_tokens.get_width()//2, 255))
        
        self.p2_input.draw(surface)
        
        # Buttons
        for button in self.buttons:
            button.draw(surface)
            
        # Message
        if self.message:
            msg = info_font.render(self.message, True, RED)
            surface.blit(msg, (surface.get_width()//2 - msg.get_width()//2, 410))

# -------------------------
# MULTIPLAYER LOBBY SCREEN
# -------------------------
class MultiplayerLobbyScreen:
    def __init__(self, multiplayer_game, is_host=False):
        self.multiplayer_game = multiplayer_game
        self.is_host = is_host
        self.back_button = Button(WIDTH//2 - 100, HEIGHT - 100, 200, 50, "BACK", LIGHT_BLUE, BLUE)
        self.start_button = Button(WIDTH//2 - 100, HEIGHT - 160, 200, 50, "START GAME", GREEN, (0, 200, 0))
        self.players = []
        self.status_text = "Waiting for players..." if is_host else "Connected to game"
        
    def handle_events(self, event=None):
        events = [event] if event else pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                return "quit"
            if e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1:
                    if self.back_button.is_clicked(e.pos, True):
                        self.multiplayer_game.disconnect()
                        return "modes"
                    if self.is_host and self.start_button.is_clicked(e.pos, True):
                        if self.multiplayer_game.is_game_ready():  # Check if both players are ready
                            self.multiplayer_game.start_game()
                            return "start_multiplayer"
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.multiplayer_game.disconnect()
                    return "modes"
        
        # Update player list from multiplayer game state
        self.players = []
        if self.multiplayer_game.game_state.get('player1'):
            self.players.append("Player 1")
        if self.multiplayer_game.game_state.get('player2'):
            self.players.append("Player 2")
        
        # Check if game was started by host
        if self.multiplayer_game.game_state.get('game_started'):
            return "start_multiplayer"
            
        return "multiplayer_lobby"
    
    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        self.back_button.check_hover(mouse_pos)
        if self.is_host:
            self.start_button.check_hover(mouse_pos)
    
    def draw(self, surface):
        # Draw semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))
        
        # Draw title
        title_text = title_font.render("MULTIPLAYER LOBBY", True, WHITE)
        surface.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 50))
        
        # Draw connection info
        if self.is_host:
            status_text = info_font.render("Hosting on localhost:5555", True, GREEN)
        else:
            status_text = info_font.render("Connected to host", True, GREEN)
        surface.blit(status_text, (WIDTH//2 - status_text.get_width()//2, 120))
        
        # Draw players
        players_text = menu_font.render(f"Players ({len(self.players)}/2):", True, WHITE)
        surface.blit(players_text, (WIDTH//2 - players_text.get_width()//2, 180))
        
        for i, player_name in enumerate(self.players):
            player_text = info_font.render(f"{player_name}", True, LIGHT_BLUE)
            surface.blit(player_text, (WIDTH//2 - player_text.get_width()//2, 230 + i * 40))
        
        # Draw buttons
        self.back_button.draw(surface)
        if self.is_host and len(self.players) >= 2:
            self.start_button.draw(surface)
        elif self.is_host:
            waiting_text = info_font.render("Waiting for Player 2 to connect...", True, YELLOW)
            surface.blit(waiting_text, (WIDTH//2 - waiting_text.get_width()//2, HEIGHT - 200))

# -------------------------
# MULTIPLAYER JOIN SCREEN
# -------------------------
class MultiplayerJoinScreen:
    def __init__(self):
        self.back_button = Button(WIDTH//2 - 100, HEIGHT - 100, 200, 50, "BACK", LIGHT_BLUE, BLUE)
        self.connect_button = Button(WIDTH//2 - 100, 400, 200, 50, "CONNECT", GREEN, (0, 200, 0))
        self.ip_input = TextInput(WIDTH//2 - 150, 300, 300, 60)
        self.status_text = "Enter host IP address:"
        
    def handle_events(self, event=None):
        events = [event] if event else pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                return "quit"
            
            self.ip_input.handle_event(e)
            
            if e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1:
                    if self.back_button.is_clicked(e.pos, True):
                        return "modes"
                    if self.connect_button.is_clicked(e.pos, True):
                        # Try to connect to host
                        ip = self.ip_input.text.strip() or "localhost"
                        try:
                            multiplayer_game = multiplayer.AndolanExpressMultiplayer(is_host=False, host_ip=ip)
                            if multiplayer_game.connect_to_host():
                                return "multiplayer_lobby", multiplayer_game
                            else:
                                self.status_text = "Connection failed!"
                        except Exception as ex:
                            print(f"Connection error: {ex}")
                            self.status_text = "Connection failed!"
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return "modes"
                if e.key == pygame.K_RETURN and self.ip_input.text.strip():
                    # Try to connect
                    ip = self.ip_input.text.strip()
                    try:
                        multiplayer_game = multiplayer.AndolanExpressMultiplayer(is_host=False, host_ip=ip)
                        if multiplayer_game.connect_to_host():
                            return "multiplayer_lobby", multiplayer_game
                        else:
                            self.status_text = "Connection failed!"
                    except Exception as ex:
                        print(f"Connection error: {ex}")
                        self.status_text = "Connection failed!"
        
        return "multiplayer_join"
    
    def update(self):
        pass
    
    def draw(self, surface):
        # Draw semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))
        
        # Draw title
        title_text = title_font.render("JOIN GAME", True, WHITE)
        surface.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 50))
        
        # Draw status
        status_color = RED if "failed" in self.status_text else WHITE
        status_surf = info_font.render(self.status_text, True, status_color)
        surface.blit(status_surf, (WIDTH//2 - status_surf.get_width()//2, 250))
        
        # Draw input and buttons
        self.ip_input.draw(surface)
        self.connect_button.draw(surface)
        self.back_button.draw(surface)

# -------------------------
# PAUSE SCREEN CLASS
# -------------------------
class PauseScreen:
    def __init__(self):
        self.buttons = [
            Button(WIDTH//2 - 150, 250, 300, 60, "RESUME", GREEN, (0, 200, 0)),
            Button(WIDTH//2 - 150, 330, 300, 60, "RESTART", LIGHT_BLUE, BLUE),
            Button(WIDTH//2 - 150, 410, 300, 60, "MAIN MENU", ORANGE, DARK_ORANGE),
            Button(WIDTH//2 - 150, 490, 300, 60, "QUIT GAME", RED, (200, 0, 0))
        ]
        
    def handle_events(self, event):
        if event.type == pygame.QUIT:
            return "quit"
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "resume"
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                for i, button in enumerate(self.buttons):
                    if button.is_clicked(event.pos, True):
                        if i == 0:  # RESUME
                            return "resume"
                        elif i == 1:  # RESTART
                            return "restart"
                        elif i == 2:  # MAIN MENU
                            return "main_menu"
                        elif i == 3:  # QUIT GAME
                            return "quit"
        return "pause"
    
    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.check_hover(mouse_pos)
    
    def draw(self, surface):
        # Draw semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))
        
        # Draw title
        title_text = title_font.render("PAUSED", True, WHITE)
        surface.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 100))
        
        # Draw buttons
        for button in self.buttons:
            button.draw(surface)

# -------------------------
# LEADERBOARD SCREEN CLASS
# -------------------------
class LeaderboardScreen:
    def __init__(self, leaderboard):
        self.leaderboard = leaderboard
        self.back_button = Button(WIDTH//2 - 150, HEIGHT - 100, 300, 60, "BACK", LIGHT_BLUE, BLUE)
        self.mode_buttons = [
            Button(60, 100, 200, 60, "ALL MODES", LIGHT_BLUE, BLUE),
            Button(280, 100, 200, 60, "NORMAL", GREEN, (0, 200, 0)),
            Button(500, 100, 240, 60, "MULTIPLAYER", LIGHT_BLUE, BLUE),
            Button(760, 100, 200, 60, "RAGE", RED, (200, 0, 0))
        ]
        self.current_mode = None  # None = all modes
    
    def handle_events(self, event=None):
        events = [event] if event else pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.back_button.is_clicked(e.pos, True):
                    return "menu"
                    
                for i, button in enumerate(self.mode_buttons):
                    if button.is_clicked(e.pos, True):
                        if i == 0:  # ALL MODES
                            self.current_mode = None
                        elif i == 1:  # NORMAL
                            self.current_mode = "NORMAL"
                        elif i == 2:  # MULTIPLAYER
                            self.current_mode = "MULTIPLAYER"
                        elif i == 3:  # RAGE
                            self.current_mode = "RAGE"
            
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return "menu"
        
        return "leaderboard"
    
    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        self.back_button.check_hover(mouse_pos)
        for button in self.mode_buttons:
            button.check_hover(mouse_pos)
    
    def draw(self, surface):
        # Semi-transparent background
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))
        
        # Title
        title = title_font.render("LEADERBOARD", True, WHITE)
        surface.blit(title, (WIDTH//2 - title.get_width()//2, 30))
        
        # Draw mode buttons
        for i, button in enumerate(self.mode_buttons):
            # Highlight active mode button
            if (i == 0 and self.current_mode is None) or \
               (i == 1 and self.current_mode == "NORMAL") or \
               (i == 2 and self.current_mode == "MULTIPLAYER") or \
               (i == 3 and self.current_mode == "RAGE"):
                button.color = BLUE
                button.hover_color = LIGHT_BLUE
            else:
                button.color = LIGHT_BLUE
                button.hover_color = BLUE
            button.draw(surface)
        
        # Get scores for current mode
        scores = self.leaderboard.get_top_scores(self.current_mode)
        
        # Column headers
        if self.current_mode == "MULTIPLAYER":
            headers = ["Rank", "Name", "Score", "Tokens", "Mode", "Date"]
            col_widths = [60, 180, 100, 100, 120, 140]
        else:
            headers = ["Rank", "Name", "Score", "Mode", "Date"]
            col_widths = [80, 200, 120, 150, 150]
            
        header_y = 220
        col_x = WIDTH//2 - sum(col_widths)//2
        
        # Draw header background
        header_rect = pygame.Rect(col_x - 10, header_y - 10, sum(col_widths) + 20, 40)
        pygame.draw.rect(surface, (50, 50, 100), header_rect, border_radius=5)
        pygame.draw.rect(surface, WHITE, header_rect, 2, border_radius=5)
        
        # Draw headers
        for i, header in enumerate(headers):
            header_text = font.render(header, True, WHITE)
            x_pos = col_x + sum(col_widths[:i]) + 10
            surface.blit(header_text, (x_pos, header_y))
        
        # Draw scores
        if not scores:
            no_scores = menu_font.render("No scores yet for this mode!", True, WHITE)
            surface.blit(no_scores, (WIDTH//2 - no_scores.get_width()//2, 280))
        else:
            for i, score in enumerate(scores[:10]):  # Show top 10 scores
                y_pos = header_y + 50 + i * 30
                
                # Alternate row colors
                row_color = (40, 40, 40) if i % 2 == 0 else (30, 30, 30)
                pygame.draw.rect(surface, row_color, 
                               (col_x - 10, y_pos - 5, sum(col_widths) + 20, 30))
                
                # Rank
                rank_text = font.render(f"{i+1}.", True, WHITE)
                surface.blit(rank_text, (col_x + 10, y_pos))
                
                # Name (truncate if too long)
                name = str(score.get("name", "Unknown"))[:15]
                name_text = font.render(name, True, WHITE)
                surface.blit(name_text, (col_x + col_widths[0] + 10, y_pos))
                
                # Score
                score_val = str(score.get("score", 0))
                score_text = font.render(score_val, True, YELLOW)
                surface.blit(score_text, (col_x + sum(col_widths[:2]) + 10, y_pos))
                
                current_col_idx = 3
                
                # Tokens (Only in Multiplayer)
                if self.current_mode == "MULTIPLAYER":
                    tokens_val = str(score.get("tokens", 0))
                    tokens_text = font.render(tokens_val, True, YELLOW)
                    surface.blit(tokens_text, (col_x + sum(col_widths[:current_col_idx]) + 10, y_pos))
                    current_col_idx += 1
                
                # Mode with color coding
                mode = str(score.get("mode", "NORMAL")).upper()
                mode_color = (GREEN if mode == "NORMAL" else 
                             YELLOW if mode == "MULTIPLAYER" else 
                             ORANGE if mode == "RAGE" else WHITE)
                mode_text = font.render(mode, True, mode_color)
                surface.blit(mode_text, (col_x + sum(col_widths[:current_col_idx]) + 10, y_pos))
                current_col_idx += 1
                
                # Date (format: MM/DD/YYYY)
                date = score.get("date", "")
                # Format date safely
                try:
                    from datetime import datetime
                    date_obj = datetime.fromisoformat(date)
                    date = date_obj.strftime("%Y-%m-%d")
                except:
                    pass # Use original string if parsing fails

                if len(date) > 10:
                    date = date[5:10] + "-" + date[2:4]  # MM-DD-YY
                date_text = font.render(date, True, WHITE)
                surface.blit(date_text, (col_x + sum(col_widths[:current_col_idx]) + 10, y_pos))
        
        # Draw back button
        self.back_button.draw(surface)

# -------------------------
# MODES SCREEN CLASS
# -------------------------

# -------------------------
# MAIN MENU CLASS
# -------------------------
class MainMenu:
    def __init__(self, tokens_collected):
        self.tokens_collected = tokens_collected
        self.buttons = [
            Button(WIDTH//2 - 150, 250, 300, 60, "START GAME", GREEN, (0, 200, 0)),
            Button(WIDTH//2 - 150, 330, 300, 60, "MODES", LIGHT_BLUE, BLUE),
            Button(WIDTH//2 - 150, 410, 300, 60, "HOW TO PLAY", LIGHT_BLUE, BLUE),
            Button(WIDTH//2 - 150, 490, 300, 60, "LEADERBOARD", LIGHT_BLUE, BLUE),
            Button(WIDTH//2 - 150, 570, 300, 60, "QUIT", RED, (200, 0, 0))
        ]
        
        # Story Replay Icon (Top Left, beside Mute Button at 20,20)
        self.story_icon_button = Button(70, 20, 40, 40, "", LIGHT_BLUE, BLUE)
        
        # Larger font for tokens
        self.token_font = pygame.font.SysFont("Arial", 48, bold=True)
        
    def handle_events(self, event=None):
        events = [event] if event else pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                return "quit"
            
            if e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1:
                    # Check Story Icon
                    if self.story_icon_button.is_clicked(e.pos, True):
                        print("Story button clicked!")
                        return "play_story"
                        
                    for i, button in enumerate(self.buttons):
                        if button.is_clicked(e.pos, True):
                            if i == 0: return "start_normal"
                            elif i == 1: return "modes"
                            elif i == 2: return "how_to_play"
                            elif i == 3: return "leaderboard"
                            elif i == 4: return "quit"
                            
        return "menu"
    
    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.check_hover(mouse_pos)
        self.story_icon_button.check_hover(mouse_pos)
            
    def draw(self, surface):
        # Draw background
        if assets.intro_image:
            surface.blit(assets.intro_image, (0, 0))
        else:
            surface.fill((0, 0, 0))
        
        # Tokens (Top Right now, since Top Left has buttons)
        tokens_text = self.token_font.render(f"Tokens: {self.tokens_collected}", True, YELLOW)
        surface.blit(tokens_text, (WIDTH - 20 - tokens_text.get_width(), 20))
        
        # Draw buttons
        for button in self.buttons:
            button.draw(surface)
            
        # Draw Story Icon Button (Custom circular style to match Mute icon)
        # self.story_icon_button.draw(surface) # Don't use default button draw
        
        icon_rect = self.story_icon_button.rect
        center = icon_rect.center
        
        # Draw Background Circle (Light Gray)
        pygame.draw.circle(surface, (200, 200, 200), center, 18)
        # Draw Border Circle (Dark Gray)
        pygame.draw.circle(surface, (50, 50, 50), center, 18, 2)
        
        # Draw "Play" icon (Triangle)
        # Triangle points: (left_x, top_y), (left_x, bottom_y), (right_x, mid_y)
        # Adjusting points to center them in the circle
        points = [
            (center[0] - 5, center[1] - 10),
            (center[0] - 5, center[1] + 10),
            (center[0] + 10, center[1])
        ]
        pygame.draw.polygon(surface, (50, 50, 50), points)
            
        # Footer
        footer = info_font.render("v1.0 - Pygame Edition", True, WHITE)
        surface.blit(footer, (WIDTH//2 - footer.get_width()//2, HEIGHT - 30))

# -------------------------
# MODES SCREEN CLASS
# -------------------------
class ModesScreen:
    def __init__(self, tokens_collected):
        self.tokens_collected = tokens_collected
        self.rage_locked = tokens_collected < 100
        self.multiplayer_locked = tokens_collected < 200
        
        rage_color = GRAY if self.rage_locked else RED
        rage_hover = GRAY if self.rage_locked else (200, 0, 0)
        multi_color = GRAY if self.multiplayer_locked else LIGHT_BLUE
        multi_hover = GRAY if self.multiplayer_locked else BLUE
        
        # Larger font for tokens
        self.token_font = pygame.font.SysFont("Arial", 48, bold=True)
        
        self.buttons = [
            Button(WIDTH//2 - 150, 200, 300, 60, "NORMAL MODE", GREEN, (0, 200, 0)),
            Button(WIDTH//2 - 150, 300, 300, 60, "RAGE MODE" + (" (LOCKED)" if self.rage_locked else ""), rage_color, rage_hover),
            Button(WIDTH//2 - 150, 400, 300, 60, "MULTIPLAYER" + (" (LOCKED)" if self.multiplayer_locked else ""), multi_color, multi_hover),
            Button(WIDTH//2 - 150, 550, 300, 60, "BACK", LIGHT_BLUE, BLUE)
        ]
        
    def handle_events(self, event=None):
        events = [event] if event else pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                return "quit"
                
            if e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1:
                    for i, button in enumerate(self.buttons):
                        if button.is_clicked(e.pos, True):
                            if i == 0: return "start_normal"
                            elif i == 1: 
                                if not self.rage_locked: return "start_rage"
                            elif i == 2: 
                                if not self.multiplayer_locked: return "multiplayer" # Goes to lobby/join choice
                            elif i == 3: return "menu"
                            
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return "menu"
                    
        return "modes"
    
    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.check_hover(mouse_pos)
            
    def draw(self, surface):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))
        
        title = title_font.render("SELECT GAME MODE", True, WHITE)
        surface.blit(title, (WIDTH//2 - title.get_width()//2, 80))
        
        tokens_text = self.token_font.render(f"Tokens: {self.tokens_collected}", True, YELLOW)
        surface.blit(tokens_text, (WIDTH - 20 - tokens_text.get_width(), 10))
        
        for button in self.buttons:
            button.draw(surface)
            
        # Mode descriptions
        descriptions = [
            "Standard game speed",
            "Fast game speed" + (" (Unlock at 100 tokens)" if self.rage_locked else ""),
            "Play with a friend" + (" (Unlock at 200 tokens)" if self.multiplayer_locked else "")
        ]
        
        for i, desc in enumerate(descriptions):
            desc_surf = info_font.render(desc, True, WHITE)
            surface.blit(desc_surf, (WIDTH//2 - desc_surf.get_width()//2, 265 + i * 100))

# -------------------------
# HOW TO PLAY SCREEN CLASS
# -------------------------
class HowToPlayScreen:
    def __init__(self):
        self.back_button = Button(WIDTH//2 - 150, HEIGHT - 100, 300, 60, "BACK", LIGHT_BLUE, BLUE)
        
    def handle_events(self, event=None):
        events = [event] if event else pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.back_button.is_clicked(e.pos, True):
                    return "menu"
                    
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return "menu"
                    
        return "how_to_play"
    
    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        self.back_button.check_hover(mouse_pos)
    
    def draw(self, surface):
        # Semi-transparent background
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))
        
        # Title
        title = title_font.render("HOW TO PLAY?", True, WHITE)
        surface.blit(title, (WIDTH//2 - title.get_width()//2, 50))
        
        # Instructions
        instructions = [
            "• Use LEFT and RIGHT arrow keys to move your character.",
            "• Collect tokens to increase your score.",
            "• Avoid obstacles like police, barricades, and tear gas.",
            "• Watch out for the danger signs!",
            "• Different game modes offer unique challenges.",
            "",
            "Good luck and have fun!"
        ]
        
        # Calculate centering for the text block
        max_width = 0
        for line in instructions:
            w = menu_font.size(line)[0]
            if w > max_width:
                max_width = w
        
        start_x = (WIDTH - max_width) // 2
        
        y_offset = 150
        for line in instructions:
            text = menu_font.render(line, True, WHITE)
            if line.startswith("•"):
                surface.blit(text, (start_x, y_offset))
            else:
                # Center non-bullet lines (like "Good luck")
                surface.blit(text, (WIDTH//2 - text.get_width()//2, y_offset))
            y_offset += 50
        
        # Draw back button
        self.back_button.draw(surface)

