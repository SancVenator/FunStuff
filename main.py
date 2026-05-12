import pygame
import os
from settings import *
from player import Player
from world import World


def main():
    pygame.init()
    pygame.mixer.init()
    
    # Load and play background music
    music_path = os.path.join("photos for game", "Valley_Path_at_Sunset.mp3")
    try:
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.play(-1) # Loop forever
    except Exception as e:
        print(f"Error loading music: {e}")

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Ancient Israel Explorer")

    clock = pygame.time.Clock()
    
    # Fonts
    font_large = pygame.font.Font(None, 74)
    font_small = pygame.font.Font(None, 36)
    
    # Game objects
    player = Player(WIDTH // 2, HEIGHT - 250)
    world = World()
    
    # Transition state
    fade_alpha = 0
    fading = False
    fade_dir = 1 # 1 for out, -1 for in
    target_level = None
    
    start = False
    running = True
    
    # Menu state
    menu_open = False
    volume_on = True
    
    # Button rects
    menu_width, menu_height = 400, 300
    menu_rect = pygame.Rect((WIDTH - menu_width) // 2, (HEIGHT - menu_height) // 2, menu_width, menu_height)
    volume_btn = pygame.Rect(menu_rect.centerx - 150, menu_rect.centery - 30, 300, 50)
    quit_btn = pygame.Rect(menu_rect.centerx - 150, menu_rect.centery + 50, 300, 50)
    
    # Location Toast state
    location_toast = {"text": "", "alpha": 0, "timer": 0}
    
    # Gemara Interaction state
    gemara_menu_open = False
    try:
        gemara_progress_img = pygame.image.load("photos for game/gemeraprogress.png").convert_alpha()
        gemara_progress_img = pygame.transform.scale(gemara_progress_img, (WIDTH, HEIGHT))
    except:
        gemara_progress_img = None
    gemara_rect = pygame.Rect(820, 600, 200, 160) # Gemara hitbox at ~900, 680
    
    while running:
        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if gemara_menu_open:
                        gemara_menu_open = False
                    else:
                        menu_open = not menu_open
                        if menu_open and player.walk_sound:
                            player.walk_sound.stop()
                            player.walk_sound_playing = False
                    
                if not menu_open:
                    if event.key == pygame.K_SPACE:
                        if not start:
                            start = True
                        else:
                            player.jump()
                    
                    # Interaction keys
                    if start and event.key == pygame.K_1 and not fading:
                        if world.active_tooltip and "Home" in world.active_tooltip["msg"]:
                            fading = True
                            fade_dir = 1
                            target_level = "home"
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                if menu_open:
                    if volume_btn.collidepoint(event.pos):
                        volume_on = not volume_on
                        vol = 1.0 if volume_on else 0.0
                        pygame.mixer.music.set_volume(vol)
                        if player.walk_sound:
                            player.walk_sound.set_volume(vol)
                        # Also set volume for all active channels (like fire sound)
                        for i in range(pygame.mixer.get_num_channels()):
                            pygame.mixer.Channel(i).set_volume(vol)
                    elif quit_btn.collidepoint(event.pos):
                        running = False
                elif not gemara_menu_open and world.name == "home":
                    # Check for Gemara click
                    if gemara_rect.collidepoint(event.pos):
                        gemara_menu_open = True
                        if player.walk_sound:
                            player.walk_sound.stop()
                            player.walk_sound_playing = False
                elif gemara_menu_open:
                    # Clicking anywhere in the progress menu closes it
                    gemara_menu_open = False



        # 2. Update Logic
        if not menu_open and not gemara_menu_open:
            # Update Toast
            if location_toast["timer"] > 0:
                location_toast["timer"] -= 1
                if location_toast["timer"] < 60:
                    location_toast["alpha"] = int((location_toast["timer"] / 60) * 255)
                else:
                    location_toast["alpha"] = 255
            else:
                location_toast["alpha"] = 0

            if fading:
                fade_alpha += 5 * fade_dir
                if fade_alpha >= 255:
                    fade_alpha = 255
                    # Switch level and music while black
                    if target_level:
                        world.load_level(target_level)
                        player.controls_enabled = False
                        player.x = WIDTH // 2 - 50
                        player.y = HEIGHT - 200
                        player.z = 0
                        
                        # Audio Transition
                        if target_level == "home":
                            pygame.mixer.music.fadeout(1000)
                            nigun_path = os.path.join("photos for game", "Wordless Nigun  Ancient Jewish Chant for Reflection.mp3")
                            fire_path = os.path.join("photos for game", "Fire Crackling - Sound Effect [HQ].mp3")
                            try:
                                # Play Chant starting at 40s with fade-in
                                pygame.mixer.music.load(nigun_path)
                                pygame.mixer.music.play(-1, start=40.0, fade_ms=2000)
                                
                                # Play Fire Crackling on a separate channel
                                fire_sound = pygame.mixer.Sound(fire_path)
                                fire_sound.set_volume(1.0 if volume_on else 0.0)
                                fire_sound.play(-1)
                            except Exception as e:
                                print(f"Error switching audio: {e}")
                            
                            # Position and Pose
                            player.controls_enabled = False
                            player.x = 700
                            player.y = 760
                            player.z = 0
                            player.current_anim = "kneel"
                            player.scale_override = 1.3
                            
                            # Show Location Toast
                            location_toast = {"text": "Location: Your Home", "alpha": 255, "timer": 180}

                    fade_dir = -1

                elif fade_alpha <= 0:
                    fade_alpha = 0
                    fading = False

            if start:
                keys = pygame.key.get_pressed()
                if not fading:
                    player.handle_input(keys)
                player.update(world)
                world.update(player)


        # 3. Rendering
        world.draw(screen)
        
        # Gemara Highlight
        if world.name == "home" and not gemara_menu_open:
            mouse_pos = pygame.mouse.get_pos()
            if gemara_rect.collidepoint(mouse_pos):
                highlight = pygame.Surface(gemara_rect.size, pygame.SRCALPHA)
                highlight.fill((255, 255, 255, 60))
                screen.blit(highlight, gemara_rect.topleft)
        
        if not gemara_menu_open:
            player.draw(screen)
        
        world.draw_ui(screen, player, font_small)
        
        # Gemara Progress Menu
        if gemara_menu_open and gemara_progress_img:
            screen.blit(gemara_progress_img, (0, 0))
            # Hint to close
            close_hint = font_small.render("Click anywhere or press ESC to Close", True, WHITE)
            screen.blit(close_hint, (WIDTH // 2 - close_hint.get_width() // 2, HEIGHT - 50))

        # Location Toast
        if location_toast["alpha"] > 0:
            # Draw banner
            banner_surf = pygame.Surface((WIDTH, 120), pygame.SRCALPHA)
            banner_surf.fill((0, 0, 0, 180))
            banner_surf.set_alpha(location_toast["alpha"])
            screen.blit(banner_surf, (0, HEIGHT - 180))
            
            t_text = font_large.render(location_toast["text"], True, WHITE)
            t_rect = t_text.get_rect(center=(WIDTH // 2, HEIGHT - 120))
            t_text.set_alpha(location_toast["alpha"])
            screen.blit(t_text, t_rect)
        
        # Fade Overlay
        if fade_alpha > 0:
            fade_surf = pygame.Surface((WIDTH, HEIGHT))
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(fade_alpha)
            screen.blit(fade_surf, (0, 0))
        
        # Dev Feature: Mouse Coords
        if DEBUG:
            m_pos = pygame.mouse.get_pos()
            coord_text = font_small.render(f"({m_pos[0]}, {m_pos[1]})", True, (255, 255, 0))
            screen.blit(coord_text, (m_pos[0] + 15, m_pos[1] + 15))
        
        # Start overlay

        if not start:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill(OVERLAY_DIM)
            screen.blit(overlay, (0, 0))
            
            title = font_large.render("Ancient Israel Explorer", True, WHITE)
            title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
            screen.blit(title, title_rect)
            
            hint = font_small.render("Press SPACE to Start | ARROWS to Move", True, (255, 220, 180))
            hint_rect = hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))
            screen.blit(hint, hint_rect)

        # Escape Menu Overlay
        if menu_open:
            # Dim background
            menu_bg = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            menu_bg.fill((0, 0, 0, 180))
            screen.blit(menu_bg, (0, 0))
            
            # Draw Menu Box
            pygame.draw.rect(screen, (40, 40, 45), menu_rect, border_radius=15)
            pygame.draw.rect(screen, (200, 180, 150), menu_rect, 3, border_radius=15)
            
            # Title
            menu_title = font_large.render("PAUSED", True, WHITE)
            title_rect = menu_title.get_rect(center=(menu_rect.centerx, menu_rect.top + 50))
            screen.blit(menu_title, title_rect)
            
            # Buttons
            mouse_pos = pygame.mouse.get_pos()
            
            # Volume Button
            vol_color = (80, 80, 90) if volume_btn.collidepoint(mouse_pos) else (60, 60, 70)
            pygame.draw.rect(screen, vol_color, volume_btn, border_radius=10)
            vol_text = font_small.render(f"Volume: {'ON' if volume_on else 'OFF'}", True, WHITE)
            vol_text_rect = vol_text.get_rect(center=volume_btn.center)
            screen.blit(vol_text, vol_text_rect)
            
            # Quit Button
            quit_color = (150, 50, 50) if quit_btn.collidepoint(mouse_pos) else (100, 40, 40)
            pygame.draw.rect(screen, quit_color, quit_btn, border_radius=10)
            quit_text = font_small.render("Quit Game", True, WHITE)
            quit_text_rect = quit_text.get_rect(center=quit_btn.center)
            screen.blit(quit_text, quit_text_rect)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
