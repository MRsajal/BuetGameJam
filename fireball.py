import pygame
import sys
class Fireball(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()

        self.images = [
            pygame.image.load("fire/0.png").convert_alpha(),
            pygame.image.load("fire/1.png").convert_alpha(),
            pygame.image.load("fire/2.png").convert_alpha()
        ]
        FIRE_SIZE = 10
        self.images = [pygame.transform.scale(img, (FIRE_SIZE, FIRE_SIZE)) for img in self.images]

        if direction == "left":
            self.images = [pygame.transform.flip(img, True, False) for img in self.images]

        self.frame = 0
        self.image = self.images[self.frame]
        self.rect = self.image.get_rect(center=(x, y))

        self.direction = direction
        self.speed = 8
        self.travel = 0
        self.max_distance = 200  # pixels
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
