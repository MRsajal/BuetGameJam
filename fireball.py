import pygame

class Fireball(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, variant="normal"):
        super().__init__()
        
        self.variant = variant

        # Load base images
        # Ensure these match your actual file paths
        base_images = [
            pygame.image.load("fire/0.png").convert_alpha(),
            pygame.image.load("fire/1.png").convert_alpha(),
            pygame.image.load("fire/2.png").convert_alpha()
        ]

        # --- SETUP VARIANTS (Equivalent Exchange) ---
        if self.variant == "blood":
            # Blood Ammo: Big, Fast, Red, High Damage
            FIRE_SIZE = 32
            self.speed = 12
            self.damage = 5        # Deals 5 hits worth of damage
            self.max_distance = 600
            tint_color = (255, 50, 50) # Bright Red
        else:
            # Normal Ammo: Small, Normal Speed, Normal Damage
            FIRE_SIZE = 10
            self.speed = 8
            self.damage = 1        # Base damage (game.py can override this)
            self.max_distance = 200
            tint_color = None

        # Process images (Scale & Tint)
        self.images = []
        for img in base_images:
            scaled = pygame.transform.scale(img, (FIRE_SIZE, FIRE_SIZE))
            if tint_color:
                # Create a copy to tint it red
                tinted = scaled.copy()
                # BLEND_RGBA_MULT multiplies the colors (Red * White = Red)
                tinted.fill(tint_color, special_flags=pygame.BLEND_RGBA_MULT)
                self.images.append(tinted)
            else:
                self.images.append(scaled)

        # Flip if facing left
        if direction == "left":
            self.images = [pygame.transform.flip(img, True, False) for img in self.images]

        self.frame = 0
        self.image = self.images[self.frame]
        self.rect = self.image.get_rect(center=(x, y))

        self.direction = direction
        self.travel = 0
        self.anim_timer = 0

    def update(self):
        # Move
        if self.direction == "right":
            self.rect.x += self.speed
        else:
            self.rect.x -= self.speed

        self.travel += self.speed
        if self.travel >= self.max_distance:
            self.kill()

        # Animate
        self.anim_timer += 1
        if self.anim_timer >= 5:
            self.anim_timer = 0
            self.frame = (self.frame + 1) % len(self.images)
            self.image = self.images[self.frame]