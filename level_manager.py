import pygame
from enemy import Enemy, Boss

class LevelManager:
    def __init__(self, game):
        self.game = game
        self.boss_spawned = False
        self.boss_spawn_kills = 10  # Kills needed for first boss

    def reset(self):
        self.boss_spawned = False
        self.boss_spawn_kills = 10

    def check_boss_spawn(self):
        """Checks if enough kills occurred to spawn the boss."""
        # Only spawn if boss isn't already there and we reached kill count
        if self.game.kills >= self.boss_spawn_kills and not self.boss_spawned:
            self.spawn_boss()

    def spawn_boss(self):
        if self.boss_spawned: return
        
        # Despawn normal enemies to focus on boss
        self.game.enemy_list.clear()
        
        # Spawn Boss
        boss = Boss(self.game.MAP_WIDTH, self.game.MAP_HEIGHT, "Scarab")
        self.game.enemy_list.append(boss)
        
        self.boss_spawned = True
        print("!!! BOSS SPAWNED !!!")

    def handle_boss_death(self):
        """Called when the boss is killed."""
        self.start_next_level()

    def start_next_level(self):
        """Increases difficulty, heals player, and resets spawning."""
        self.game.level += 1
        self.boss_spawned = False
        
        # 1. REWARD: Increase Max HP + Full Heal
        self.game.player.max_hp += 2
        self.game.player.hp = self.game.player.max_hp
        
        # 2. DIFFICULTY: Increase enemy count & kill requirement
        self.game.enemy_count += 3
        self.game.kills = 0
        self.boss_spawn_kills = int(self.boss_spawn_kills * 1.5)
        
        # 3. RESPAWN: Spawn new batch of enemies
        self.game.enemy_list = [
            Enemy(self.game.MAP_WIDTH, self.game.MAP_HEIGHT, self.game.ENEMY_SIZE, "Scarab") 
            for _ in range(self.game.enemy_count)
        ]
        
        print(f"--- LEVEL {self.game.level} STARTED ---")