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
    
    while running:
        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
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



        # 2. Update Logic
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
        player.draw(screen)
        world.draw_ui(screen, player, font_small)
        
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

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
