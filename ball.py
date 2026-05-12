import pygame
import random
import os

pygame.init()
# Set up the display
WIDTH, HEIGHT = 1920, 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Drone Simulation - Level 1: Ancient Israel")

# Load background image from the specific directory
bg_path = os.path.join("photos for game", "level1background.png")
try:
    bg_image = pygame.image.load(bg_path).convert()
    bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))
except Exception as e:
    print(f"Could not load background image at {bg_path}: {e}")
    # Try a fallback if the folder name is slightly different in some environments
    try:
        bg_image = pygame.image.load("level1background.png").convert()
        bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))
    except:
        bg_image = None

# Ball properties
ball = {
    "x": WIDTH // 2,
    "y": HEIGHT // 2,
    "radius": 20,
    "color": (255, 60, 60),
    "vx": 0,
    "vy": 0
}

# Stamina properties
stamina = 100.0
MAX_STAMINA = 100.0
STAMINA_RECOVERY = 0.3
JUMP_COST = 25.0

# Physics constants
GRAVITY = 0.5
BOUNCE_FACTOR = -0.7
ACCEL = 0.8
FRICTION = 0.95
MAX_SPEED = 15
JUMP_STRENGTH = 12

# World management
current_screen = 0

start = False
font = pygame.font.Font(None, 74)
small_font = pygame.font.Font(None, 36)
clock = pygame.time.Clock()

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
            
            # Jump logic
            if start and event.key == pygame.K_UP:
                if stamina >= JUMP_COST:
                    ball["vy"] = -JUMP_STRENGTH
                    stamina -= JUMP_COST

    keys = pygame.key.get_pressed()
    
    # 2. Update Logic
    if start:
        # Horizontal Movement
        if keys[pygame.K_LEFT]:
            ball["vx"] -= ACCEL
        if keys[pygame.K_RIGHT]:
            ball["vx"] += ACCEL
            
        ball["vx"] *= FRICTION
        
        if ball["vx"] > MAX_SPEED: ball["vx"] = MAX_SPEED
        if ball["vx"] < -MAX_SPEED: ball["vx"] = -MAX_SPEED
        
        # Apply Gravity
        ball["vy"] += GRAVITY
        
        # Update Position
        ball["x"] += ball["vx"]
        ball["y"] += ball["vy"]
        
        # Screen Transitions
        if ball["x"] > WIDTH:
            ball["x"] = 0
            current_screen += 1
        elif ball["x"] < 0:
            ball["x"] = WIDTH
            current_screen -= 1
        
        # Floor collision
        if ball["y"] + ball["radius"] > HEIGHT:
            ball["y"] = HEIGHT - ball["radius"]
            ball["vy"] *= BOUNCE_FACTOR
            
        # Stamina Recovery
        if stamina < MAX_STAMINA:
            stamina += STAMINA_RECOVERY

    # 3. Rendering
    if bg_image:
        screen.blit(bg_image, (0, 0))
    else:
        screen.fill((255, 200, 150))
    
    # Draw UI
    bar_width, bar_height = 400, 30
    bar_x, bar_y = (WIDTH - bar_width) // 2, 50
    pygame.draw.rect(screen, (60, 40, 20, 180), (bar_x, bar_y, bar_width, bar_height))
    current_bar_width = int((stamina / MAX_STAMINA) * bar_width)
    stamina_color = (255, 180, 50) if stamina >= JUMP_COST else (200, 50, 0)
    pygame.draw.rect(screen, stamina_color, (bar_x, bar_y, current_bar_width, bar_height))
    pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)
    
    stamina_text = small_font.render(f"STAMINA - AREA {current_screen}", True, (255, 255, 255))
    screen.blit(stamina_text, (bar_x, bar_y - 25))

    # Draw the ball
    pygame.draw.circle(screen, (0, 0, 0), (int(ball["x"]), int(ball["y"])), ball["radius"] + 2)
    pygame.draw.circle(screen, ball["color"], (int(ball["x"]), int(ball["y"])), ball["radius"])
    
    # Start message
    if not start:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 80))
        screen.blit(overlay, (0, 0))
        
        text = font.render("Press SPACE to Start", True, (255, 255, 255))
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
        screen.blit(text, text_rect)
        
        hint = small_font.render("Explore the Ancient Farm", True, (255, 220, 180))
        hint_rect = hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))
        screen.blit(hint, hint_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()






