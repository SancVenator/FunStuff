import pygame
from settings import *
from spritesheet import SpriteSheet

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y # This is the "ground" position (feet)
        self.z = 0 # This is the "altitude" (height above ground)
        self.vx = 0
        self.vz = 0 # Vertical velocity for jumping (affects z)
        self.health = MAX_HEALTH
        
        # Load animations

        self.ss = SpriteSheet("photos for game/spritesheet1.png")
        self.animations = self.ss.get_animations()
        self.animations["back"] = [self.ss.get_image(4, 0)]
        self.animations["front"] = [self.ss.get_image(0, 0)]
        
        self.current_anim = "idle"
        self.frame_index = 0
        self.flip = False
        
        first_frame = self.animations["idle"][0]
        self.width = first_frame.get_width()
        self.height = first_frame.get_height()
        self.controls_enabled = True
        self.scale_override = None

        
    def handle_input(self, keys):
        if not self.controls_enabled:
            self.vx *= FRICTION # Slow down if controls disabled
            self.vy_walk = 0
            return

        # Scale movement speed based on perspective scale

        s = self.get_scale()
        current_accel = ACCEL * s
        
        # Horizontal movement
        if keys[pygame.K_LEFT]:
            self.vx -= current_accel
            self.flip = True
        if keys[pygame.K_RIGHT]:
            self.vx += current_accel
            self.flip = False
            
        # Vertical movement (Walking on the ground plane)
        self.vy_walk = 0
        if keys[pygame.K_UP]:
            self.vy_walk = -current_accel * 6
            self.current_anim = "back"
        elif keys[pygame.K_DOWN]:
            self.vy_walk = current_accel * 6
            self.current_anim = "front"
        elif abs(self.vx) > 0.5:
            self.current_anim = "walk_side"
        else:
            self.current_anim = "idle"

            
        # Animation state for jumping (z > 0)
        if self.z > 0:
            if self.vz > 0:
                self.current_anim = "jump"
                self.frame_index = 0
            else:
                self.current_anim = "jump"
                self.frame_index = 1

    def jump(self):
        # Only jump if on the ground
        if self.z == 0:
            self.vz = JUMP_STRENGTH
            return True
        return False

    def update(self, world):
        # 1. Physics & Movement
        old_x, old_y = self.x, self.y
        s = self.get_scale()
        scaled_max_speed = MAX_SPEED * s
        
        # Apply Horizontal Movement
        self.vx *= FRICTION
        if abs(self.vx) < 0.1: self.vx = 0
        if self.vx > scaled_max_speed: self.vx = scaled_max_speed
        if self.vx < -scaled_max_speed: self.vx = -scaled_max_speed
        
        self.x += self.vx
        if self.check_collision(world):
            self.x = old_x
            self.vx = 0
            
        # Apply Vertical Walking Movement
        self.y += self.vy_walk
        if self.check_collision(world):
            self.y = old_y
            self.vy_walk = 0


        # 2. Jump/Gravity Physics (affects z)
        if self.z > 0 or self.vz != 0:
            self.vz -= GRAVITY
            self.z += self.vz
            
            if self.z <= 0:
                self.z = 0
                self.vz = 0
        
        # 3. Ground Boundaries
        if self.y > HEIGHT:
            self.y = HEIGHT
        elif self.y < HORIZON:
            self.y = HORIZON


    def check_collision(self, world):
        # If jumping high enough, ignore ground collisions
        if self.z > 20:
            return False
            
        if not world.collision_map:
            return False
            
        # Check a few points around the feet
        s = self.get_scale()
        # Offset to center the feet check
        base_x = int(self.x + (self.width * s) / 2)
        base_y = int(self.y - 10 * s)
        
        # Check 3 points (center, left, right)
        offsets = [0, -15 * s, 15 * s]
        for ox in offsets:
            px = int(base_x + ox)
            py = int(base_y)
            
            # Clamp to screen
            px = max(0, min(WIDTH - 1, px))
            py = max(0, min(HEIGHT - 1, py))
            
            color = world.collision_map.get_at((px, py))
            # Check for Red (Collision color)
            if color[0] > 180 and color[1] < 100 and color[2] < 100:
                return True
                
        return False


    def get_scale(self):
        if self.scale_override is not None:
            return self.scale_override
            
        # Calculate scale based on Y position (Perspective)
        # Linear interpolation between MIN_SCALE at HORIZON and MAX_SCALE at HEIGHT
        t = (self.y - HORIZON) / (HEIGHT - HORIZON)
        return MIN_SCALE + (MAX_SCALE - MIN_SCALE) * t


    def draw(self, surface):
        # Get current frame
        frames = self.animations.get(self.current_anim, self.animations["idle"])
        frame = frames[int(self.frame_index) % len(frames)]
            
        if self.flip:
            frame = pygame.transform.flip(frame, True, False)
            
        # Dynamic Scaling
        s = self.get_scale()
        scaled_w = int(frame.get_width() * s)
        scaled_h = int(frame.get_height() * s)
        frame = pygame.transform.scale(frame, (scaled_w, scaled_h))
            
        # Render at (x, y - height - z)
        render_y = self.y - scaled_h - self.z
        surface.blit(frame, (int(self.x), int(render_y)))
        
        # Update width/height for other calculations if needed
        self.scaled_width = scaled_w
        self.scaled_height = scaled_h
        
        # Draw a shadow
        shadow_w = 50 * s * (1 - self.z/400)
        if shadow_w > 2:
            shadow_surf = pygame.Surface((int(shadow_w), int(15 * s)), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, 80), shadow_surf.get_rect())
            surface.blit(shadow_surf, (self.x + (scaled_w - shadow_w)/2, self.y - 10 * s))


