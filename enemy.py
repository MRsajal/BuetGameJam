import pygame
import os
import random

class Enemy:
    def __init__(self, map_width, map_height, size, sprite_root):
        self.size = size
        self.map_width = map_width
        self.map_height = map_height
        self.sprite_root = sprite_root

        self.rect = pygame.Rect(0, 0, size, size)
        self.respawn()

        # Enemy stats
        self.hp = 3
        self.damage = 1
        self.alive = True

        # Movement
        self.speed = 1  # pixels per frame in WORLD coords (slowed down from 2)

        # Animation
        self.animations = {
            "idle_left": self.load_images(os.path.join(sprite_root, "idle", "left")),
            "idle_right": self.load_images(os.path.join(sprite_root, "idle", "right")),
            "walk_left": self.load_images(os.path.join(sprite_root, "walk", "left")),
            "walk_right": self.load_images(os.path.join(sprite_root, "walk", "right")),
            "death_left": self.load_images(os.path.join(sprite_root, "death", "left")),
            "death_right": self.load_images(os.path.join(sprite_root, "death", "right")),
        }

        self.current_animation = "idle_right"
        self.frame_index = 0
        self.frame_timer = 0
        self.frame_delay = 10

    def hit(self):
        self.hp -= 1
        if self.hp <= 0:
            self.alive = False

    def load_images(self, folder):
        images = []
        i = 0
        while True:
            path = os.path.join(folder, f"{i}.png")
            if not os.path.exists(path):
                break
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, (self.size, self.size))
            images.append(img)
            i += 1
        if not images:
            img = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            img.fill((255, 0, 255))
            images.append(img)
        return images

    def respawn(self):
        self.rect.x = random.randint(0, self.map_width - self.size)
        self.rect.y = random.randint(0, self.map_height - self.size)
        self.hp = 5
        self.alive = True
        self.current_animation = "idle_right"
        self.frame_index = 0
        self.frame_timer = 0

    def _set_animation(self, name: str):
        """Switch animation safely (reset frame_index if animation changes)."""
        if name != self.current_animation:
            self.current_animation = name
            self.frame_index = 0
            self.frame_timer = 0

    def update(self, player_rect, map_x=0, map_y=0):
        """Follow the player every frame.

        IMPORTANT: In this project the player stays fixed on screen while the map moves.
        Enemies are stored in WORLD coordinates. Therefore we must convert the player's
        screen position to world coordinates using map offsets.

        - player_rect: player's SCREEN rect
        - map_x/map_y: map top-left on screen (offset)
        """
        if not self.alive:
            # death animation
            death_anim = "death_right" if "right" in self.current_animation else "death_left"
            self._set_animation(death_anim)
            self.animate(loop=False)
            # when finished, respawn
            if self.frame_index >= len(self.animations[self.current_animation]) - 1:
                self.respawn()
            return

        # Convert player SCREEN -> WORLD
        player_world_x = player_rect.centerx - map_x
        player_world_y = player_rect.centery - map_y

        dx = player_world_x - self.rect.centerx
        dy = player_world_y - self.rect.centery
        dist = (dx * dx + dy * dy) ** 0.5

        if dist < 1:
            idle_anim = "idle_right" if "right" in self.current_animation else "idle_left"
            self._set_animation(idle_anim)
            self.animate(loop=True)
            return

        # Move toward player every frame
        step_x = self.speed * dx / dist
        step_y = self.speed * dy / dist
        self.rect.x += int(round(step_x))
        self.rect.y += int(round(step_y))

        # Clamp to world bounds (so enemies don't leave map)
        self.rect.x = max(0, min(self.rect.x, self.map_width - self.size))
        self.rect.y = max(0, min(self.rect.y, self.map_height - self.size))

        # Choose animation by horizontal direction
        walk_anim = "walk_right" if dx >= 0 else "walk_left"
        self._set_animation(walk_anim)
        self.animate(loop=True)

    def animate(self, loop: bool = True):
        frames = self.animations.get(self.current_animation, [])
        if not frames:
            self.frame_index = 0
            return

        # Clamp frame index (prevents IndexError if animation has fewer frames)
        if self.frame_index >= len(frames):
            self.frame_index = 0

        self.frame_timer += 1
        if self.frame_timer >= self.frame_delay:
            self.frame_timer = 0
            if loop:
                self.frame_index = (self.frame_index + 1) % len(frames)
            else:
                # death: stop at last frame
                self.frame_index = min(self.frame_index + 1, len(frames) - 1)

    def draw(self, screen, map_x, map_y):
        frames = self.animations.get(self.current_animation, [])
        if not frames:
            return

        # Clamp again for safety
        if self.frame_index >= len(frames):
            self.frame_index = len(frames) - 1

        screen.blit(
            frames[self.frame_index],
            (self.rect.x + map_x, self.rect.y + map_y),
        )

    def check_collision_with_player(self, player):
        if self.alive and self.rect.colliderect(player.rect):
            player.hp -= self.damage
            return True
        return False
