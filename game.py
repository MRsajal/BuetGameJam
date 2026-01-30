import pygame
import random
import os

from collision import collision
from player import Player
from enemy import Enemy, Boss
from fireball import Fireball
from drop_item import DropItem
from level_manager import LevelManager  # --- IMPORT ---

class Game:
    def __init__(
        self,
        screen: pygame.Surface,
        screen_width: int,
        screen_height: int,
        *,
        player_class: str = "Assault_Class",
        player_speed: int = 4,
        player_hp: int = 10,
        enemy_count: int = 5,
        damage_to_enemy: int = 1,
    ):
        self.screen = screen
        self.SCREEN_WIDTH = screen_width
        self.SCREEN_HEIGHT = screen_height

        self.player_class = player_class
        self.player_speed = int(player_speed)
        self.starting_hp = int(player_hp)
        self.enemy_count = int(enemy_count)
        self.damage_to_enemy = int(damage_to_enemy)

        # --- NEW: Level Manager ---
        self.level = 1
        self.level_manager = LevelManager(self)
        # --------------------------

        # Map
        self.TILE_SIZE = 16
        self.ZOOM = 2
        self.SCALED_TILE_SIZE = int(self.TILE_SIZE * self.ZOOM)
        self.MAP_TILES_X, self.MAP_TILES_Y = 65, 42
        self.MAP_WIDTH = self.MAP_TILES_X * self.SCALED_TILE_SIZE
        self.MAP_HEIGHT = self.MAP_TILES_Y * self.SCALED_TILE_SIZE
        self.map_img = pygame.image.load("map1.png").convert()
        self.map_img = pygame.transform.scale(self.map_img, (self.MAP_WIDTH, self.MAP_HEIGHT))
        self.map_x, self.map_y = 0, 0

        # Entities
        self.PLAYER_SIZE = 32
        self.ENEMY_SIZE = 32
        self.player = Player(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2, self.PLAYER_SIZE, self.player_class)
        self.player.max_hp = self.starting_hp
        self.player.hp = self.starting_hp
        
        self.enemy_list = [Enemy(self.MAP_WIDTH, self.MAP_HEIGHT, self.ENEMY_SIZE, "Scarab") for _ in range(self.enemy_count)]

        # State
        self.DAMAGE_COOLDOWN_MS = 500
        self.next_touch_damage_time = 0
        self.is_touching_enemy = False
        self.kills = 0
        self.item0_count = 0
        self.GAME_OVER = False
        self.PAUSED = False
        self.return_to_menu = False

        self.fire_group = pygame.sprite.Group()
        self.item_group = pygame.sprite.Group()

        # UI Assets
        self.number_images = {}
        for d in range(10):
            path = os.path.join("numbers", f"{d}.png")
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                self.number_images[str(d)] = pygame.transform.scale(img, (18, 24))

        self.item0_icon = None
        if os.path.exists(os.path.join("drop", "item0.png")):
            self.item0_icon = pygame.image.load(os.path.join("drop", "item0.png")).convert_alpha()
            self.item0_icon = pygame.transform.scale(self.item0_icon, (18, 18))

        self.ui_font = pygame.font.Font(None, 28)
        self.game_over_font = pygame.font.Font(None, 80)
        self.game_over_hint_font = pygame.font.Font(None, 32)
        
        self.blood_font = pygame.font.SysFont("Arial", 20, bold=True)
        self.clone_font = pygame.font.SysFont("Arial", 20, bold=True)
        self.pause_font = pygame.font.SysFont("Arial", 60, bold=True)
        self.pause_option_font = pygame.font.SysFont("Arial", 36)
        self.boss_font = pygame.font.SysFont("Impact", 50)

        self.MUZZLE_Y = -4
        self.MUZZLE_X_PAD = 6
        self._prev_mouse_down = False
        
        self.auto_fire_enabled = True
        self.auto_fire_interval_ms = 175
        self.next_auto_fire_time = 0

        self.last_blood_shot_time = -15000
        self.BLOOD_SHOT_COOLDOWN = 15000
        self.shadow_clone = None
        self.shadow_clone_spawn_time = 0
        self.SHADOW_CLONE_LIFETIME_MS = 8000  # clone lasts 8 seconds

        # Survival time
        self.start_time_ms = pygame.time.get_ticks()
        self.survival_time_ms = 0

        # Upper layer (drawn above player)
        self.upper_img = None
        if os.path.exists("upper.png"):
            self.upper_img = pygame.image.load("upper.png").convert_alpha()
            self.upper_img = pygame.transform.scale(self.upper_img, (self.MAP_WIDTH, self.MAP_HEIGHT))

        # SFX
        self.enemy_die_sfx = None
        try:
            if os.path.exists("enemyDie.mp3"):
                self.enemy_die_sfx = pygame.mixer.Sound("enemyDie.mp3")
                self.enemy_die_sfx.set_volume(0.5)
        except Exception:
            self.enemy_die_sfx = None

        self.fireball_shoot_sfx = None
        try:
            # supports either mp3 or wav; expects a file named fireballshoot.*
            for ext in ("mp3", "wav", "ogg"):
                p = f"fireballshoot.{ext}"
                if os.path.exists(p):
                    self.fireball_shoot_sfx = pygame.mixer.Sound(p)
                    self.fireball_shoot_sfx.set_volume(0.05)
                    break
        except Exception:
            self.fireball_shoot_sfx = None

        # --- Mission system ---
        self.mission_type = random.choice(["collect_item0", "survive", "reach_level"])
        self.mission_completed = False
        self.mission_complete_time_ms = 0
        self.mission_complete_overlay_ms = 3000
        self.mission_font = pygame.font.SysFont("Arial", 26, bold=True)
        self.congrats_font = pygame.font.SysFont("Arial", 72, bold=True)

    def reset(self):
        self.map_x, self.map_y = 0, 0
        self.level = 1
        self.level_manager.reset()
        
        self.player = Player(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2, self.PLAYER_SIZE, self.player_class)
        self.player.max_hp = self.starting_hp
        self.player.hp = self.starting_hp
        self.shadow_clone = None 
        self.shadow_clone_spawn_time = 0

        self.enemy_list = [Enemy(self.MAP_WIDTH, self.MAP_HEIGHT, self.PLAYER_SIZE, "Scarab") for _ in range(self.enemy_count)]
        self.kills = 0
        self.item0_count = 0
        self.next_touch_damage_time = 0
        self.is_touching_enemy = False
        self.GAME_OVER = False
        self.PAUSED = False
        self.return_to_menu = False
        self.fire_group.empty()
        self.item_group.empty()
        self.last_blood_shot_time = -self.BLOOD_SHOT_COOLDOWN

        # Survival time
        self.start_time_ms = pygame.time.get_ticks()
        self.survival_time_ms = 0

        # --- Mission system ---
        self.mission_type = random.choice(["collect_item0", "survive", "reach_level"])
        self.mission_completed = False
        self.mission_complete_time_ms = 0

    def _mission_text(self) -> str:
        if self.mission_type == "collect_item0":
            return f"TASK: Collect 10 ITEM0 ({self.item0_count}/10)"
        if self.mission_type == "survive":
            # 5 minutes = 300 seconds
            secs = self.survival_time_ms // 1000
            return f"TASK: Survive 5 min ({secs}/300s)"
        return f"TASK: Reach Level 5 (LV {self.level}/5)"

    def _check_mission_complete(self, now_ms: int):
        if self.mission_completed:
            return

        if self.mission_type == "collect_item0" and self.item0_count >= 10:
            self.mission_completed = True
        elif self.mission_type == "survive" and self.survival_time_ms >= 300_000:
            self.mission_completed = True
        elif self.mission_type == "reach_level" and self.level >= 5:
            self.mission_completed = True

        if self.mission_completed:
            self.mission_complete_time_ms = now_ms

    def draw_mission_ui(self):
        if self.mission_completed:
            return

        # Special UI for item0 mission: show icon instead of the word ITEM0
        if self.mission_type == "collect_item0":
            text_left = self.mission_font.render("TASK: Collect 10", True, (255, 255, 255))
            text_right = self.mission_font.render(f"({self.item0_count}/10)", True, (255, 255, 255))

            icon = self.item0_icon
            icon_w = icon.get_width() if icon is not None else 0
            icon_h = icon.get_height() if icon is not None else 0

            total_w = text_left.get_width() + 8 + icon_w + 8 + text_right.get_width()
            x = self.SCREEN_WIDTH // 2 - total_w // 2
            y = 58

            bg_rect = pygame.Rect(x - 10, y - 6, total_w + 20, max(text_left.get_height(), icon_h) + 12)
            pygame.draw.rect(self.screen, (0, 0, 0, 160), bg_rect)

            self.screen.blit(text_left, (x, y))
            x += text_left.get_width() + 8

            if icon is not None:
                self.screen.blit(icon, (x, y + (text_left.get_height() - icon_h) // 2))
                x += icon_w + 8

            self.screen.blit(text_right, (x, y))
            return

        # Default UI for other missions
        text = self._mission_text()
        surf = self.mission_font.render(text, True, (255, 255, 255))
        rect = surf.get_rect(center=(self.SCREEN_WIDTH // 2, 66))
        bg = rect.inflate(20, 10)
        pygame.draw.rect(self.screen, (0, 0, 0, 160), bg)
        self.screen.blit(surf, rect.topleft)

    def draw_congrats_overlay(self):
        overlay = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        title = self.congrats_font.render("CONGRATS!", True, (120, 255, 120))
        msg = self.game_over_hint_font.render("Task completed", True, (255, 255, 255))
        hint = self.game_over_hint_font.render("Press ENTER to return to Menu", True, (220, 220, 220))

        self.screen.blit(title, ((self.SCREEN_WIDTH - title.get_width()) // 2, self.SCREEN_HEIGHT // 2 - 80))
        self.screen.blit(msg, ((self.SCREEN_WIDTH - msg.get_width()) // 2, self.SCREEN_HEIGHT // 2 + 10))
        self.screen.blit(hint, ((self.SCREEN_WIDTH - hint.get_width()) // 2, self.SCREEN_HEIGHT // 2 + 55))

    def get_player_world_rect(self) -> pygame.Rect:
        r = self.player.rect.copy()
        r.x = r.x - self.map_x
        r.y = r.y - self.map_y
        return r

    def maybe_spawn_drop(self, world_x: int, world_y: int):
        if random.random() < 0.20: self.item_group.add(DropItem("item0", world_x, world_y))
        if random.random() < 0.50: self.item_group.add(DropItem("item1", world_x, world_y))

    def apply_touch_damage(self, now_ms: int):
        player_world_rect = self.get_player_world_rect()
        touching = any(enemy.alive and enemy.rect.colliderect(player_world_rect) for enemy in self.enemy_list)
        if touching:
            if not self.is_touching_enemy:
                self.is_touching_enemy = True
                self.next_touch_damage_time = now_ms
            if now_ms >= self.next_touch_damage_time:
                self.player.hp = max(0, self.player.hp - 1)
                self.next_touch_damage_time = now_ms + self.DAMAGE_COOLDOWN_MS
        else:
            self.is_touching_enemy = False

    def collect_items(self):
        player_world_rect = self.get_player_world_rect()
        for item in list(self.item_group):
            if item.rect.colliderect(player_world_rect):
                if item.kind == "item1": self.player.hp = min(self.player.max_hp, self.player.hp + 1)
                elif item.kind == "item0": self.item0_count += 1
                item.kill()

    def get_muzzle_world_pos(self, target_player=None):
        p = target_player if target_player else self.player
        if p.facing == "right": muzzle_screen_x = p.rect.right - self.MUZZLE_X_PAD
        else: muzzle_screen_x = p.rect.left + self.MUZZLE_X_PAD
        muzzle_screen_y = p.rect.centery + self.MUZZLE_Y
        fx = muzzle_screen_x - self.map_x
        fy = muzzle_screen_y - self.map_y
        return fx, fy

    def can_move(self, dx, dy) -> bool:
        new_x = self.player.rect.centerx - self.map_x + dx
        new_y = self.player.rect.centery - self.map_y + dy
        tile_x = int(new_x // self.SCALED_TILE_SIZE)
        tile_y = int(new_y // self.SCALED_TILE_SIZE)
        if tile_x < 0 or tile_x >= self.MAP_TILES_X or tile_y < 0 or tile_y >= self.MAP_TILES_Y: return False
        try: return collision[tile_y][tile_x] != 1
        except IndexError: return False

    def draw_health_bar(self):
        bar_w, bar_h, pad = 160, 16, 12
        x, y = self.SCREEN_WIDTH - pad - bar_w, pad
        pygame.draw.rect(self.screen, (30, 30, 30), (x - 2, y - 2, bar_w + 4, bar_h + 4))
        pygame.draw.rect(self.screen, (80, 80, 80), (x, y, bar_w, bar_h), 1)
        ratio = max(0.0, min(1.0, self.player.hp / self.player.max_hp))
        fill_w = int(bar_w * ratio)
        color = (0, 200, 60) if ratio > 0.6 else (240, 180, 0) if ratio > 0.3 else (220, 40, 40)
        pygame.draw.rect(self.screen, color, (x, y, fill_w, bar_h))

    def draw_kill_count(self):
        pad = 12
        x, y = self.SCREEN_WIDTH - pad - 160, pad + 24
        
        # Level Text
        lvl_surf = self.ui_font.render(f"LEVEL: {self.level}", True, (255, 215, 0))
        center_x = self.SCREEN_WIDTH // 2 - lvl_surf.get_width() // 2
        self.screen.blit(lvl_surf, (center_x, 10))

        label = self.ui_font.render("KILLS:", True, (255, 255, 255))
        self.screen.blit(label, (x, y))
        value_str = str(self.kills)
        digits_x = x + label.get_width() + 8
        for ch in value_str:
            img = self.number_images.get(ch)
            if img:
                self.screen.blit(img, (digits_x, y - 2))
                digits_x += img.get_width() + 2

        # Survival time (top center under level)
        now_ms = pygame.time.get_ticks()
        if not self.GAME_OVER:
            self.survival_time_ms = max(0, now_ms - self.start_time_ms)
        secs = self.survival_time_ms // 1000
        time_surf = self.ui_font.render(f"TIME: {secs}s", True, (200, 255, 255))
        tx = self.SCREEN_WIDTH // 2 - time_surf.get_width() // 2
        self.screen.blit(time_surf, (tx, 34))

    def draw_item0_count(self):
        pad = 12
        x, y = self.SCREEN_WIDTH - pad - 160, pad + 76
        if self.item0_icon:
            self.screen.blit(self.item0_icon, (x, y))
            text_x = x + self.item0_icon.get_width() + 6
        else: text_x = x
        label = self.ui_font.render(f"x {self.item0_count}", True, (255, 255, 255))
        self.screen.blit(label, (text_x, y - 1))

    def draw_ability_ui(self):
        center_x = self.SCREEN_WIDTH // 2
        now = pygame.time.get_ticks()
        time_since_shot = now - self.last_blood_shot_time
        remaining = self.BLOOD_SHOT_COOLDOWN - time_since_shot
        y_pos = self.SCREEN_HEIGHT - 40

        if remaining <= 0:
            if self.player.hp > 1:
                text, color = "BLOOD SHOT: READY (R-Click, -1 HP)", (255, 50, 50)
            else:
                text, color = "BLOOD SHOT: HP TOO LOW", (150, 150, 150)
        else:
            text, color = f"BLOOD SHOT: {int(remaining/1000)+1}s", (200, 200, 200)

        surf = self.blood_font.render(text, True, color)
        bg_rect = surf.get_rect(center=(center_x, y_pos))
        bg_rect.inflate_ip(20, 10)
        pygame.draw.rect(self.screen, (0, 0, 0, 150), bg_rect)
        self.screen.blit(surf, (center_x - surf.get_width() // 2, y_pos - surf.get_height() // 2))

        # Clone UI
        if self.shadow_clone is not None:
            c_text, c_col = "SHADOW CLONE: ACTIVE", (100, 200, 255)
        else:
            if self.player.hp > 1: c_text, c_col = "CLONE: READY (Press C, -50% HP)", (100, 255, 100)
            else: c_text, c_col = "CLONE: HP TOO LOW", (150, 150, 150)
        
        c_surf = self.clone_font.render(c_text, True, c_col)
        c_bg = c_surf.get_rect(center=(center_x, y_pos - 40))
        c_bg.inflate_ip(20, 10)
        pygame.draw.rect(self.screen, (0, 0, 0, 150), c_bg)
        self.screen.blit(c_surf, (center_x - c_surf.get_width()//2, y_pos - 40 - c_surf.get_height()//2))

    def draw_game_over_overlay(self):
        overlay = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        title = self.game_over_font.render("GAME OVER", True, (255, 60, 60))
        hint = self.game_over_hint_font.render("Press ENTER to restart", True, (255, 255, 255))
        tx = (self.SCREEN_WIDTH - title.get_width()) // 2
        ty = (self.SCREEN_HEIGHT - title.get_height()) // 2 - 20
        self.screen.blit(title, (tx, ty))
        self.screen.blit(hint, ((self.SCREEN_WIDTH - hint.get_width()) // 2, ty + 90))

        # Show survival time
        secs = self.survival_time_ms // 1000
        t_surf = self.game_over_hint_font.render(f"Survived: {secs}s", True, (200, 255, 255))
        self.screen.blit(t_surf, ((self.SCREEN_WIDTH - t_surf.get_width()) // 2, ty + 130))

    def draw_pause_overlay(self):
        overlay = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        title = self.pause_font.render("PAUSED", True, (255, 255, 255))
        resume = self.pause_option_font.render("Press ESC to Resume", True, (200, 200, 200))
        quit_text = self.pause_option_font.render("Press Q to Quit to Menu", True, (200, 200, 200))
        tx = (self.SCREEN_WIDTH - title.get_width()) // 2
        ty = (self.SCREEN_HEIGHT - 200) // 2
        self.screen.blit(title, (tx, ty))
        self.screen.blit(resume, ((self.SCREEN_WIDTH - resume.get_width()) // 2, ty + 80))
        self.screen.blit(quit_text, ((self.SCREEN_WIDTH - quit_text.get_width()) // 2, ty + 130))

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            # If mission is completed and congrats overlay is showing
            if self.mission_completed:
                if event.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                    self.return_to_menu = True
                return

            if self.GAME_OVER:
                if event.key == pygame.K_RETURN: self.reset()
                elif event.key == pygame.K_ESCAPE: self.return_to_menu = True
                return
            if event.key == pygame.K_ESCAPE: self.PAUSED = not self.PAUSED
            if self.PAUSED and event.key == pygame.K_q: self.return_to_menu = True

    def _mouse_click_edge(self) -> bool:
        now_down = pygame.mouse.get_pressed()[0]
        clicked = now_down and not self._prev_mouse_down
        self._prev_mouse_down = now_down
        return clicked

    def update(self, keys, now_ms: int, mouse_pos):
        if self.GAME_OVER or self.PAUSED: return

        # --- MANAGER CHECK ---
        self.level_manager.check_boss_spawn()

        # Facing
        if self._mouse_click_edge():
            if mouse_pos[0] < self.player.rect.centerx: self.player.facing = "left"
            else: self.player.facing = "right"

        moving = False
        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -self.player_speed; moving = True; self.player.facing = "left"
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = self.player_speed; moving = True; self.player.facing = "right"
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -self.player_speed; moving = True
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = self.player_speed; moving = True

        if self.can_move(dx, 0): self.map_x -= dx
        if self.can_move(0, dy): self.map_y -= dy

        self.player.update(moving, self.player.facing)

        # Clone Activation
        if keys[pygame.K_c] and self.shadow_clone is None:
            if self.player.hp > 1:
                self.player.hp = max(1, self.player.hp // 2)
                self.shadow_clone = Player(self.player.rect.x, self.player.rect.y, self.PLAYER_SIZE, self.player_class)
                self.shadow_clone_spawn_time = now_ms
                for anim_name, frames in self.shadow_clone.animations.items():
                    for img in frames: img.set_alpha(150)

        # Timed clone vanish
        if self.shadow_clone is not None and (now_ms - self.shadow_clone_spawn_time) >= self.SHADOW_CLONE_LIFETIME_MS:
            self.shadow_clone = None

        # --- CLONE UPDATE & SNAP ---
        if self.shadow_clone:
            # 1. Update Animation first
            self.shadow_clone.update(moving, self.player.facing)
            # 2. Then SNAP to position (Screen Coordinates)
            offset = 50 if self.player.facing == "left" else -50
            self.shadow_clone.rect.x = self.player.rect.x + offset
            self.shadow_clone.rect.y = self.player.rect.y
            self.shadow_clone.facing = self.player.facing

        # Blood Shot
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[2]:
            if self.player.hp > 1 and now_ms >= self.last_blood_shot_time + self.BLOOD_SHOT_COOLDOWN:
                self.player.hp -= 1
                fx, fy = self.get_muzzle_world_pos()
                blood_fire = Fireball(fx, fy, self.player.facing, variant="blood")
                self.fire_group.add(blood_fire)
                self.last_blood_shot_time = now_ms

        # Fire
        if self.auto_fire_enabled and now_ms >= self.next_auto_fire_time:
            fx, fy = self.get_muzzle_world_pos()
            fireball = Fireball(fx, fy, self.player.facing)
            self.fire_group.add(fireball)

            # Shoot SFX (once per fire interval)
            if self.fireball_shoot_sfx is not None:
                try:
                    self.fireball_shoot_sfx.play()
                except Exception:
                    pass

            if self.shadow_clone:
                cx, cy = self.get_muzzle_world_pos(self.shadow_clone)
                c_fireball = Fireball(cx, cy, self.shadow_clone.facing)
                self.fire_group.add(c_fireball)
            self.next_auto_fire_time = now_ms + self.auto_fire_interval_ms
        self.fire_group.update()

        # Collisions
        for fire in list(self.fire_group):
            for enemy in self.enemy_list:
                if enemy.alive and fire.rect.colliderect(enemy.rect):
                    dmg = getattr(fire, 'damage', 1) 
                    if getattr(fire, 'variant', 'normal') == "normal":
                        dmg += max(0, self.damage_to_enemy - 1)
                    for _ in range(dmg):
                        enemy.hit()
                        if not enemy.alive: break
                    fire.kill()
                    if not enemy.alive:
                        # Check Boss Death via Manager
                        if isinstance(enemy, Boss):
                            # Guarantee: boss always drops 1x item0
                            try:
                                self.item_group.add(DropItem("item0", enemy.rect.centerx, enemy.rect.centery))
                            except Exception:
                                pass
                            self.level_manager.handle_boss_death()
                        else:
                            # Enemy died (play SFX)
                            if self.enemy_die_sfx is not None:
                                try:
                                    self.enemy_die_sfx.play()
                                except Exception:
                                    pass

                            self.kills += 1
                            self.maybe_spawn_drop(enemy.rect.centerx, enemy.rect.centery)
                    break

        for enemy in self.enemy_list:
            enemy.update(self.player.rect, self.map_x, self.map_y)

        self.apply_touch_damage(now_ms)
        self.collect_items()

        # Mission check after collecting / leveling / time updates
        self._check_mission_complete(now_ms)

        if self.player.hp <= 0:
            self.GAME_OVER = True
            # Freeze final time
            self.survival_time_ms = max(0, now_ms - self.start_time_ms)

    def draw(self):
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.map_img, (self.map_x, self.map_y))
        
        for enemy in self.enemy_list: enemy.draw(self.screen, self.map_x, self.map_y)
        for item in self.item_group: item.draw(self.screen, self.map_x, self.map_y)
        
        self.player.draw(self.screen)
        if self.shadow_clone: self.shadow_clone.draw(self.screen)
        
        # Draw upper layer AFTER entities so it appears above the player
        if self.upper_img is not None:
            self.screen.blit(self.upper_img, (self.map_x, self.map_y))
        
        for fire in self.fire_group:
            self.screen.blit(fire.image, (fire.rect.x + self.map_x, fire.rect.y + self.map_y))

        # Boss health bar (only when boss is alive)
        for enemy in self.enemy_list:
            if isinstance(enemy, Boss) and enemy.alive:
                bar_w = 140
                bar_h = 12
                x = enemy.rect.centerx + self.map_x - bar_w // 2
                y = enemy.rect.y + self.map_y - 18

                max_hp = max(1, int(getattr(enemy, "max_hp", enemy.hp)))
                hp = max(0, int(enemy.hp))
                fill_w = int(bar_w * (hp / max_hp))

                pygame.draw.rect(self.screen, (0, 0, 0), (x - 2, y - 2, bar_w + 4, bar_h + 4))
                pygame.draw.rect(self.screen, (140, 0, 0), (x, y, bar_w, bar_h))
                pygame.draw.rect(self.screen, (0, 220, 0), (x, y, fill_w, bar_h))
                break

        self.draw_health_bar()
        self.draw_kill_count()
        self.draw_item0_count()
        self.draw_ability_ui()
        self.draw_mission_ui()
        
        if self.level_manager.boss_spawned and any(isinstance(e, Boss) and e.alive for e in self.enemy_list):
             warn = self.boss_font.render("BOSS FIGHT!", True, (255, 0, 0))
             self.screen.blit(warn, (self.SCREEN_WIDTH//2 - warn.get_width()//2, 100))

        if self.mission_completed:
            self.draw_congrats_overlay()
        elif self.GAME_OVER:
            self.draw_game_over_overlay()
        elif self.PAUSED:
            self.draw_pause_overlay()