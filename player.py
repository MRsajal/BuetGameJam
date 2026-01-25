import pygame
import os

class Player:
    def __init__(self, x, y, size, sprite_root):
        self.rect = pygame.Rect(x, y, size, size)
        self.size = size
        self.sprite_root = sprite_root

        self.facing = "right"
        self.current_animation = "idle_right"
        self.frame_index = 0
        self.frame_timer = 0
        self.frame_delay = 10

        # --- FIX: Handle capitalization differences (idle vs Idle) ---
        # Check if the uppercase "Idle" folder exists (Sniper/MachineGunner)
        # Otherwise default to lowercase "idle" (Assault)
        idle_folder_name = "idle"
        if os.path.exists(os.path.join(sprite_root, "Idle")):
            idle_folder_name = "Idle"

        self.animations = {
            "idle_left": self.load_images(os.path.join(sprite_root, idle_folder_name, "left")),
            "idle_right": self.load_images(os.path.join(sprite_root, idle_folder_name, "right")),
            "walk_left": self.load_images(os.path.join(sprite_root, "walk", "left")),
            "walk_right": self.load_images(os.path.join(sprite_root, "walk", "right")),
            "death_left": self.load_images(os.path.join(sprite_root, "death", "left")),
            "death_right": self.load_images(os.path.join(sprite_root, "death", "right")),
        }

        self._fallback_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self._fallback_surface.fill((255, 0, 255, 255))  # missing sprite fallback

        # --- NEW: HP ---
        self.max_hp = 10
        self.hp = self.max_hp

    def load_images(self, folder):
        images = []
        i = 0
        while True:
            path = os.path.join(folder, f"{i}.png")
            if not os.path.exists(path):
                break
            try:
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, (self.size, self.size))
                images.append(img)
            except Exception as e:
                print(f"Error loading {path}: {e}")
            i += 1
            
        if not images:
            # Create a fallback image if folder is empty or missing
            img = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            img.fill((255, 0, 255))
            images.append(img)
        return images

    def update(self, moving, facing):
        self.facing = facing
        desired = ("walk_" if moving else "idle_") + self.facing
        if desired != self.current_animation:
            self.current_animation = desired
            self.frame_index = 0
            self.frame_timer = 0

        frames = self.animations.get(self.current_animation, [])
        if not frames:
            self.frame_index = 0
            return

        self.frame_timer += 1
        if self.frame_timer >= self.frame_delay:
            self.frame_timer = 0
            self.frame_index = (self.frame_index + 1) % len(frames)

    def draw(self, screen):
        frames = self.animations.get(self.current_animation, [])
        if not frames:
            screen.blit(self._fallback_surface, self.rect.topleft)
            return
        self.frame_index = max(0, min(self.frame_index, len(frames) - 1))
        screen.blit(frames[self.frame_index], self.rect.topleft)