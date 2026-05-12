import pygame

class SpriteSheet:
    def __init__(self, filename, cols=8, rows=3):
        try:
            self.sheet = pygame.image.load(filename).convert_alpha()
        except Exception as e:
            print(f"Error loading spritesheet: {e}")
            self.sheet = pygame.Surface((100, 100), pygame.SRCALPHA)


            
        self.cols = cols
        self.rows = rows
        self.total_width, self.total_height = self.sheet.get_size()
        self.cell_w = self.total_width // cols
        self.cell_h = self.total_height // rows

    def get_image(self, col, row, width=None, height=None, crop_y_offset=0, crop_h_factor=0.96):

        """
        Extracts a sprite from the grid.
        crop_h_factor removes the label at the bottom of each sprite.
        """

        w = width if width else self.cell_w
        h = height if height else int(self.cell_h * crop_h_factor)
        
        rect = pygame.Rect(col * self.cell_w, row * self.cell_h + crop_y_offset, w, h)
        image = pygame.Surface(rect.size, pygame.SRCALPHA).convert_alpha()
        image.blit(self.sheet, (0, 0), rect)
        
        # Scale for the game (sprites might be large)
        # Assuming we want the character to be around 120-150px tall
        scale_factor = 200 / h 
        image = pygame.transform.scale(image, (int(w * scale_factor), int(h * scale_factor)))
        
        return image

    def get_animations(self):
        """Returns a dictionary of named animations."""
        anims = {
            "idle": [self.get_image(0, 0)],
            "walk_side": [self.get_image(1, 0)],
            "jump": [self.get_image(5, 1), self.get_image(6, 1)],
            "sit": [self.get_image(5, 0)],
            "kneel": [self.get_image(6, 0)],
            "rake": [self.get_image(5, 2), self.get_image(6, 2)],
            "sheep": [self.get_image(7, 2)]
        }
        return anims
