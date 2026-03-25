import pygame
import os
from settings import WIDTH, HEIGHT, WHITE, BLACK, BLUE, LIGHT_BLUE
from ui import Button
import assets

class StoryMode:
    def __init__(self):
        # Story Configuration
        self.slides = [
            {"characters": ["Oli_talk1.png"], "positions": ["left"], "text": "We need to ban social media before they find out about our corruption.", "speaker": "Oli"},
            {"characters": ["Balen2.png"], "positions": ["right"], "text": "No way, I will end the corruption.", "speaker": "Balen"},
            {"characters": ["Oli_talk2.png"], "positions": ["left"], "text": "You are just a mayor, you can't do anything.", "speaker": "Oli"},
            {"characters": ["Balen1.png"], "positions": ["right"], "text": "I'm not backing down, my Gen-z army will end corruption and your ruling.", "speaker": "Balen"},
            {"characters": ["Oli_talk2.png"], "positions": ["left"], "text": "You can't defeat me, I have an army.", "speaker": "Oli"},
            {"characters": ["Balen1.png"], "positions": ["right"], "text": "And I have the support of every Nepali.", "speaker": "Balen"},
            # Collage Slide: Sher Bahadur (Left), Oli (Center), Prachanda (Right)
            {"characters": ["Sher_Bahadur_talk.png", "Oli_talk.png", "Prachanda_talk.png"], 
             "positions": ["collage_left", "collage_center", "collage_right"], 
             "text": "We will always rule!!!", "speaker": "Leaders"},
            {"characters": ["Balen1.png", "protestor.png"], "positions": ["right", "left"], "text": "Now, it's time to rise my soldiers. Run for your freedom! The path ahead is dangerous, but we must keep moving forward. Don't look back!", "speaker": "Balen"},
            {"characters": ["Balen1.png", "protestor.png"], "positions": ["right", "left"], "text": "We are right behind you! Let's go!", "speaker": "Protestor"}
        ]
        
        self.images = {} # Cache for loaded images
        self.background = None
        self.current_index = 0
        
        # Load assets
        self.load_assets()
        
        # UI Elements
        self.skip_button = Button(WIDTH - 120, 20, 100, 40, "SKIP", LIGHT_BLUE, BLUE)
        self.font = pygame.font.SysFont("Arial", 24)
        self.name_font = pygame.font.SysFont("Arial", 28, bold=True) # Font for speaker name
        self.dialog_box_rect = pygame.Rect(50, HEIGHT - 150, WIDTH - 100, 120)
        
        # Music
        self.music_playing = False
        self.final_music_playing = False
        
    def load_assets(self):
        base_path = "Assets/Sprites/Story"
        
        # Load Background
        try:
            bg_path = "Assets/Story/genz_andolan_nepal_bg.png"
            if os.path.exists(bg_path):
                self.background = pygame.image.load(bg_path)
                self.background = pygame.transform.scale(self.background, (WIDTH, HEIGHT))
            else:
                # Fallback background
                self.background = pygame.Surface((WIDTH, HEIGHT))
                self.background.fill((50, 50, 50)) # Dark Gray
        except Exception as e:
            print(f"Error loading background: {e}")
            self.background = pygame.Surface((WIDTH, HEIGHT))
            self.background.fill((50, 50, 50))

        # Load Character Images
        unique_images = set()
        for slide in self.slides:
            for char in slide["characters"]:
                unique_images.add(char)
                
        target_height = int(HEIGHT * 0.65) # Standardize height to 65% of screen
        
        for img_name in unique_images:
            path = os.path.join(base_path, img_name)
            try:
                img = pygame.image.load(path)
                
                # Special scaling for Balen and Protestor images (make them slightly smaller)
                current_target_height = target_height
                if "Balen" in img_name or "protestor" in img_name:
                    current_target_height = int(target_height * 0.85) # 85% size for Balen and Protestor
                
                # Scale characters to fixed height
                scale_factor = current_target_height / img.get_height()
                new_width = int(img.get_width() * scale_factor)
                new_height = int(img.get_height() * scale_factor)
                img = pygame.transform.scale(img, (new_width, new_height))
                self.images[img_name] = img
            except Exception as e:
                print(f"Error loading character image {path}: {e}")
                # Fallback
                surf = pygame.Surface((200, 300))
                surf.fill((255, 0, 255)) # Magenta for missing
                self.images[img_name] = surf

    def start_music(self):
        if not self.music_playing:
            try:
                pygame.mixer.music.load("Assets/Music/Conversation.mp3")
                pygame.mixer.music.play(-1)
                self.music_playing = True
            except Exception as e:
                print(f"Error playing story music: {e}")

    def play_final_music(self):
        if not self.final_music_playing:
            try:
                # Play Rage.mp3 or Mode.mp3 for the finale
                pygame.mixer.music.load("Assets/Music/Rage.mp3") 
                pygame.mixer.music.play(-1)
                self.final_music_playing = True
            except Exception as e:
                print(f"Error playing final music: {e}")

    def handle_events(self, event):
        if event.type == pygame.QUIT:
            return "quit"
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.skip_button.is_clicked(event.pos, True):
                    return "skip"
                else:
                    # Next slide
                    self.current_index += 1
                    if self.current_index >= len(self.slides):
                        return "done"
                        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # Next slide
                self.current_index += 1
                if self.current_index >= len(self.slides):
                    return "done"
            elif event.key == pygame.K_ESCAPE:
                return "skip"
                
        return None

    def check_music_transition(self):
        # Check if we reached the second last slide
        if self.current_index == len(self.slides) - 2:
            self.play_final_music()

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        self.skip_button.check_hover(mouse_pos)
        
        # Check for second last slide to change music
        if self.current_index == len(self.slides) - 2 and not self.final_music_playing:
            try:
                pygame.mixer.music.load(assets.MUSIC_RAGE) # Use Rage music for chase sequence
                pygame.mixer.music.play(-1)
                self.final_music_playing = True
            except:
                pass

    def draw(self, surface):
        # Draw Background
        if self.background:
            surface.blit(self.background, (0, 0))
        else:
            surface.fill(BLACK)
            
        # Draw Characters
        if 0 <= self.current_index < len(self.slides):
            slide = self.slides[self.current_index]
            characters = slide["characters"]
            positions = slide["positions"]
            
            # Check if it's the collage slide (3 characters)
            if len(characters) == 3:
                imgs = []
                for char_name in characters:
                    if char_name in self.images:
                        imgs.append(self.images[char_name])
                    else:
                        imgs.append(pygame.Surface((100, 100))) # Fallback
                
                # Draw Center (Oli) first to establish position
                if len(imgs) > 1:
                    oli_img = imgs[1]
                    oli_x = WIDTH // 2 - oli_img.get_width() // 2
                    oli_y = HEIGHT - oli_img.get_height()
                    surface.blit(oli_img, (oli_x, oli_y))
                    
                    # Draw Left (Sher Bahadur) relative to Oli
                    if len(imgs) > 0:
                        sb_img = imgs[0]
                        # Place to the left of Oli with OVERLAP to account for whitespace
                        sb_x = oli_x - sb_img.get_width() + 40 
                        sb_y = HEIGHT - sb_img.get_height()
                        surface.blit(sb_img, (sb_x, sb_y))
                        
                    # Draw Right (Prachanda) relative to Oli
                    if len(imgs) > 2:
                        p_img = imgs[2]
                        # Place to the right of Oli with OVERLAP to account for whitespace
                        p_x = oli_x + oli_img.get_width() - 40
                        p_y = HEIGHT - p_img.get_height()
                        surface.blit(p_img, (p_x, p_y))

            # Check if it's the final slide (Balen + Protestor)
            elif len(characters) == 2 and "protestor.png" in characters:
                 for i, char_name in enumerate(characters):
                    if char_name in self.images:
                        img = self.images[char_name]
                        y_pos = HEIGHT - img.get_height()
                        
                        if "Balen" in char_name:
                            # Balen strictly at right edge
                            x_pos = WIDTH - img.get_width()
                        else:
                            # Protestor at left edge
                            x_pos = 0
                            
                        surface.blit(img, (x_pos, y_pos))

            else:
                # Standard single/dual character drawing
                for i, char_name in enumerate(characters):
                    if char_name in self.images:
                        img = self.images[char_name]
                        pos = positions[i]
                        
                        x_pos = 0
                        y_pos = HEIGHT - img.get_height()
                        
                        if "Balen" in char_name:
                             # Force Balen to right edge
                            x_pos = WIDTH - img.get_width()
                        elif pos == "left":
                            x_pos = 0 # Strict Left Edge
                        elif pos == "right":
                            x_pos = WIDTH - img.get_width() # Strict Right Edge
                        elif pos == "center":
                            x_pos = WIDTH // 2 - img.get_width() // 2
                            
                        surface.blit(img, (x_pos, y_pos))
            
        # Draw Dialog Box
        pygame.draw.rect(surface, (0, 0, 0, 200), self.dialog_box_rect) # Semi-transparent black
        pygame.draw.rect(surface, WHITE, self.dialog_box_rect, 2) # White border
        
        # Draw Text
        if 0 <= self.current_index < len(self.slides):
            slide = self.slides[self.current_index]
            text = slide["text"]
            speaker = slide.get("speaker", "")
            
            # Draw Speaker Name
            if speaker:
                name_surf = self.name_font.render(speaker, True, (255, 255, 0)) # Yellow
                surface.blit(name_surf, (self.dialog_box_rect.x + 20, self.dialog_box_rect.y + 10))
            
            # Wrap text if too long
            words = text.split(' ')
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                test_surf = self.font.render(test_line, True, WHITE)
                if test_surf.get_width() < self.dialog_box_rect.width - 40:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            lines.append(' '.join(current_line))
            
            # Render lines
            start_y = self.dialog_box_rect.y + 45 # Start below speaker name
            for line in lines:
                text_surf = self.font.render(line, True, WHITE)
                surface.blit(text_surf, (self.dialog_box_rect.x + 20, start_y))
                start_y += 30
            
        # Draw Skip Button
        self.skip_button.draw(surface)
        
        # Draw "Click to Continue" hint
        hint_font = pygame.font.SysFont("Arial", 16)
        hint_text = hint_font.render("Click or Press Space to Continue", True, (200, 200, 200))
        surface.blit(hint_text, (WIDTH - hint_text.get_width() - 20, HEIGHT - 25))