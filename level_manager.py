import pygame
import random
from enemy import Enemy, Boss

class LevelManager:
    def __init__(self, game):
        self.game = game
        self.boss_spawned = False

        # Hidden per-level boss timer
        self.level_started_ms = pygame.time.get_ticks()
        self.boss_spawn_delay_ms = 60_000  # 1 minute

    def reset(self):
        self.boss_spawned = False
        self.level_started_ms = pygame.time.get_ticks()

    def check_boss_spawn(self):
        """Spawn boss 1 minute after the level starts (timer hidden from player)."""
        if self.boss_spawned:
            return

        now_ms = pygame.time.get_ticks()
        if now_ms - self.level_started_ms >= self.boss_spawn_delay_ms:
            self.spawn_boss()

    def spawn_boss(self):
        if self.boss_spawned:
            return

        boss = Boss(self.game.MAP_WIDTH, self.game.MAP_HEIGHT, "Spider")
        self.game.enemy_list.append(boss)

        self.boss_spawned = True
        print("!!! BOSS SPAWNED !!!")

    def handle_boss_death(self):
        """Called when the boss is killed."""
        self.start_next_level()

    def start_next_level(self):
        """Starts the next level only after boss defeat; starts a new hidden boss timer."""
        self.game.level += 1
        self.boss_spawned = False

        # New hidden timer for the NEXT boss
        self.level_started_ms = pygame.time.get_ticks()

        # Difficulty ramp: more enemies each level
        self.game.enemy_count += 3

        # Keep player HP and kills (per your previous request)

        # Spawn new batch of enemies
        self.game.enemy_list = [
            Enemy(self.game.MAP_WIDTH, self.game.MAP_HEIGHT, self.game.ENEMY_SIZE, "Scarab")
            for _ in range(self.game.enemy_count)
        ]

        print(f"--- LEVEL {self.game.level} STARTED ---")