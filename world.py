import pygame
import os
import math
from settings import *

class World:
    def __init__(self):
        self.current_screen = 0
        self.bg_image = self.load_background()
        self.collision_map = self.load_collision_map()
        self.active_tooltip = None
        
        # UI Sprites
        try:
            self.heart_full = pygame.image.load("photos for game/heart_full.png").convert_alpha()
            self.heart_full = pygame.transform.scale(self.heart_full, (48, 48))
            self.heart_empty = pygame.image.load("photos for game/heart_empty.png").convert_alpha()
            self.heart_empty = pygame.transform.scale(self.heart_empty, (48, 48))
            self.scroll_img = pygame.image.load("photos for game/scroll_ui.png").convert_alpha()
        except Exception as e:
            print(f"Error loading UI sprites: {e}")
            self.heart_full = None
            self.heart_empty = None
            self.scroll_img = None

        
    def load_background(self):
        bg_path = os.path.join("photos for game", "level1background.png")
        try:
            image = pygame.image.load(bg_path).convert()
            return pygame.transform.scale(image, (WIDTH, HEIGHT))
        except Exception as e:
            print(f"Error loading background: {e}")
            fallback = pygame.Surface((WIDTH, HEIGHT))
            fallback.fill((255, 200, 150))
            return fallback

    def load_collision_map(self):
        map_path = os.path.join("photos for game", "obstaclemap1.png")
        try:
            image = pygame.image.load(map_path).convert()
            return pygame.transform.scale(image, (WIDTH, HEIGHT))
        except Exception as e:
            print(f"Error loading collision map: {e}")
            return None

    def load_level(self, name):
        if name == "home":
            bg_path = os.path.join("photos for game", "home.png")
            try:
                image = pygame.image.load(bg_path).convert()
                self.bg_image = pygame.transform.scale(image, (WIDTH, HEIGHT))
                # Disable collision map inside home for now
                self.collision_map = None 
            except Exception as e:
                print(f"Error loading home level: {e}")
        elif name == "farm":
            self.bg_image = self.load_background()
            self.collision_map = self.load_collision_map()

    def update(self, player):

        # Screen transitions
        if player.x > WIDTH:
            player.x = 0
            self.current_screen += 1
        elif player.x + player.scaled_width < 0:
            player.x = WIDTH - player.scaled_width
            self.current_screen -= 1
            
        # Tooltip detection
        self.active_tooltip = None
        player_feet = pygame.Vector2(player.x + player.scaled_width/2, player.y)
        
        for inter in INTERACTORS:
            inter_pos = pygame.Vector2(inter["rect"].center)
            if player_feet.distance_to(inter_pos) < INTERACT_RANGE:
                self.active_tooltip = inter
                break

    def draw(self, surface):
        if self.bg_image:
            surface.blit(self.bg_image, (0, 0))
            
        # Draw Tooltip
        if self.active_tooltip:
            self.draw_floating_tooltip(surface, self.active_tooltip)
        
        # We NO LONGER draw the manual debug obstacles
        # The collision map is used internally but never drawn.

    def draw_floating_tooltip(self, surface, interactor):
        # Animation
        bob = math.sin(pygame.time.get_ticks() * 0.005) * 8
        rect = interactor["rect"]
        msg = interactor["msg"]
        
        # Fonts (Old-timey serif)
        font_name = pygame.font.match_font('georgia', 'timesnewroman', 'serif')
        font = pygame.font.Font(font_name, 28)
        text_surf = font.render(msg, True, (60, 40, 20)) # Dark brown ink color
        
        if self.scroll_img:
            # Scale scroll to fit text
            tw, th = text_surf.get_size()
            sw, sh = tw + 80, th + 50
            scroll_scaled = pygame.transform.scale(self.scroll_img, (sw, sh))
            
            # Position
            scroll_rect = scroll_scaled.get_rect(center=(rect.centerx, rect.top - 50 + bob))
            surface.blit(scroll_scaled, scroll_rect)
            
            # Text on scroll
            text_rect = text_surf.get_rect(center=scroll_rect.center)
            surface.blit(text_surf, text_rect)
        else:
            # Fallback
            bubble_rect = text_surf.get_rect(center=(rect.centerx, rect.top - 40 + bob))
            pygame.draw.rect(surface, (40, 30, 20, 200), bubble_rect.inflate(20, 10), border_radius=10)
            surface.blit(text_surf, bubble_rect)
            
    def draw_ui(self, surface, player, font):
        # Health Hearts (Top Left)
        start_x, start_y = 50, 50
        spacing = 55
        
        if self.heart_full and self.heart_empty:
            for i in range(MAX_HEALTH):
                x = start_x + (i * spacing)
                y = start_y
                # Draw empty heart background
                surface.blit(self.heart_empty, (x, y))
                # Draw full heart if health allows
                if i < player.health:
                    surface.blit(self.heart_full, (x, y))
        else:
            # Fallback if images fail
            health_text = font.render(f"HEALTH: {player.health}/{MAX_HEALTH}", True, WHITE)
            surface.blit(health_text, (start_x, start_y))
            
        # Screen Indicator
        screen_text = font.render(f"AREA {self.current_screen}", True, WHITE)
        surface.blit(screen_text, (start_x, start_y + 60))
