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
        
        # Load animations
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

        self.respawn()

        # Stats
        self.hp = 3
        self.damage = 1
        self.alive = True
        self.speed = 1

    def hit(self):
        self.hp -= 1
        if self.hp <= 0:
            self.alive = False

    def load_images(self, folder):
        images = []
        i = 0
        while True:
            path = os.path.join(folder, f"{i}.png")
            if not os.path.exists(path): break
            try:
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, (self.size, self.size))
                images.append(img)
            except Exception: pass
            i += 1
        if not images:
            img = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            img.fill((255, 0, 255))
            images.append(img)
        return images

    def respawn(self):
        self.rect.x = random.randint(0, self.map_width - self.size)
        self.rect.y = random.randint(0, self.map_height - self.size)
        self.hp = 3
        self.alive = True
        self.current_animation = "idle_right"
        self.frame_index = 0

    def _set_animation(self, name: str):
        if name != self.current_animation:
            self.current_animation = name
            self.frame_index = 0
            self.frame_timer = 0

    def update(self, player_rect, map_x=0, map_y=0):
        if not self.alive:
            death_anim = "death_right" if "right" in self.current_animation else "death_left"
            self._set_animation(death_anim)
            self.animate(loop=False)
            if self.frame_index >= len(self.animations[self.current_animation]) - 1:
                self.kill_cleanup()
            return

        # --- FIX: CALCULATE REAL WORLD TARGET ---
        # Player is fixed on screen. Map moves underneath.
        # Player World X = Player Screen X - Map Offset (map_x is usually negative)
        target_x = player_rect.centerx - map_x
        target_y = player_rect.centery - map_y

        dx = target_x - self.rect.centerx
        dy = target_y - self.rect.centery
        dist = (dx * dx + dy * dy) ** 0.5

        if dist < 1:
            idle_anim = "idle_right" if "right" in self.current_animation else "idle_left"
            self._set_animation(idle_anim)
            self.animate(loop=True)
            return

        step_x = self.speed * dx / dist
        step_y = self.speed * dy / dist
        self.rect.x += int(round(step_x))
        self.rect.y += int(round(step_y))

        self.rect.x = max(0, min(self.rect.x, self.map_width - self.size))
        self.rect.y = max(0, min(self.rect.y, self.map_height - self.size))

        walk_anim = "walk_right" if dx >= 0 else "walk_left"
        self._set_animation(walk_anim)
        self.animate(loop=True)

    def kill_cleanup(self):
        self.respawn()

    def animate(self, loop: bool = True):
        frames = self.animations.get(self.current_animation, [])
        if not frames: return
        
        self.frame_timer += 1
        if self.frame_timer >= self.frame_delay:
            self.frame_timer = 0
            if loop:
                self.frame_index = (self.frame_index + 1) % len(frames)
            else:
                self.frame_index = min(self.frame_index + 1, len(frames) - 1)

    def draw(self, screen, map_x, map_y):
        frames = self.animations.get(self.current_animation, [])
        if not frames: return
        idx = min(self.frame_index, len(frames) - 1)
        screen.blit(frames[idx], (self.rect.x + map_x, self.rect.y + map_y))

# --- BOSS CLASS ---
class Boss(Enemy):
    def __init__(self, map_width, map_height, sprite_root):
        super().__init__(map_width, map_height, 96, sprite_root)
        self.respawn()

    def respawn(self):
        self.rect.x = random.randint(0, self.map_width - self.size)
        self.rect.y = random.randint(0, self.map_height - self.size)
        self.hp = 50
        self.damage = 2
        self.alive = True
        self.current_animation = "idle_right"
    
    def kill_cleanup(self):
        self.alive = False # Stay dead so LevelManager detects victory