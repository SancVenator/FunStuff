import pygame

# Display settings
WIDTH = 1920
HEIGHT = 1080
FPS = 60

# Colors
DARK_GRAY = (30, 30, 30)
WHITE = (255, 255, 255)
STAMINA_BG = (60, 40, 20, 180)
STAMINA_FILL = (255, 180, 50)
STAMINA_LOW = (200, 50, 0)
OVERLAY_DIM = (0, 0, 0, 80)

# Physics constants
GRAVITY = 0.5
BOUNCE_FACTOR = -0.3
ACCEL = 0.8
FRICTION = 0.85
MAX_SPEED = 10
JUMP_STRENGTH = 14
MAX_HEALTH = 3

# Perspective settings

HORIZON = 480 # Y coordinate where the ground starts
MIN_SCALE = 0.4 # Scale at the horizon
MAX_SCALE = 1.0 # Scale at the bottom of the screen

# Debug settings
DEBUG = True

# Obstacles (x, y, w, h)
OBSTACLES = [
    pygame.Rect(480, 320, 450, 220),  # House Left
    pygame.Rect(930, 340, 290, 210),  # House Right
    pygame.Rect(930, 550, 280, 200),  # Well Area
    pygame.Rect(0, 540, 420, 100),    # Fence Left
    pygame.Rect(170, 750, 350, 150),  # Lower left rocks/cactus
]

# Interaction settings
INTERACT_RANGE = 100

# Interactors: (Rect, Message)
INTERACTORS = [
    {"rect": pygame.Rect(580, 440, 100, 100), "msg": "Press 1 to Enter Hut"},
    {"rect": pygame.Rect(1055, 507, 80, 80), "msg": "Press 1 to Enter Home"},
    {"rect": pygame.Rect(1070, 640, 100, 100), "msg": "Press 2 to Draw Water"},
    {"rect": pygame.Rect(200, 750, 150, 150), "msg": "Press 3 to Rest"},
]





