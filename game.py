import pygame
import random
import os

from collision import collision
from player import Player
from enemy import Enemy
from fireball import Fireball
from drop_item import DropItem


class Game:
    def __init__(
        self,
        screen: pygame.Surface,
        screen_width: int,
        screen_height: int,
        *,
        player_speed: int = 4,
        player_hp: int = 10,
        enemy_count: int = 5,
        damage_to_enemy: int = 1,
    ):
        self.screen = screen
        self.SCREEN_WIDTH = screen_width
        self.SCREEN_HEIGHT = screen_height

        # Gameplay tuning from loadout
        self.player_speed = int(player_speed)
        self.starting_hp = int(player_hp)
        self.enemy_count = int(enemy_count)
        self.damage_to_enemy = int(damage_to_enemy)

        # -------------------- MAP --------------------
        self.TILE_SIZE = 16
        self.ZOOM = 2
        self.SCALED_TILE_SIZE = int(self.TILE_SIZE * self.ZOOM)

        self.MAP_TILES_X, self.MAP_TILES_Y = 65, 42
        self.MAP_WIDTH = self.MAP_TILES_X * self.SCALED_TILE_SIZE
        self.MAP_HEIGHT = self.MAP_TILES_Y * self.SCALED_TILE_SIZE

        self.map_img = pygame.image.load("map.png").convert()
        self.map_img = pygame.transform.scale(self.map_img, (self.MAP_WIDTH, self.MAP_HEIGHT))

        self.map_x, self.map_y = 0, 0
        self.scroll_speed = 4

        # -------------------- PLAYER / ENEMIES --------------------
        self.PLAYER_SIZE = 32
        self.ENEMY_SIZE = 32

        self.player = Player(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2, self.PLAYER_SIZE, "Assault_Class")
        self.player.max_hp = self.starting_hp
        self.player.hp = self.starting_hp

        self.enemy_list = [Enemy(self.MAP_WIDTH, self.MAP_HEIGHT, self.ENEMY_SIZE, "Scarab") for _ in range(self.enemy_count)]

        # -------------------- UI / STATE --------------------
        self.DAMAGE_COOLDOWN_MS = 500
        self.next_touch_damage_time = 0
        self.is_touching_enemy = False

        self.kills = 0
        self.item0_count = 0
        self.GAME_OVER = False

        self.fire_group = pygame.sprite.Group()
        self.item_group = pygame.sprite.Group()

        # Load number images (0-9)
        self.number_images = {}
        for d in range(10):
            path = os.path.join("numbers", f"{d}.png")
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                self.number_images[str(d)] = pygame.transform.scale(img, (18, 24))

        self.item0_icon = None
        item0_icon_path = os.path.join("drop", "item0.png")
        if os.path.exists(item0_icon_path):
            self.item0_icon = pygame.image.load(item0_icon_path).convert_alpha()
            self.item0_icon = pygame.transform.scale(self.item0_icon, (18, 18))

        self.ui_font = pygame.font.Font(None, 28)
        self.game_over_font = pygame.font.Font(None, 80)
        self.game_over_hint_font = pygame.font.Font(None, 32)

        # Tune these to match your sprite (screen pixels)
        self.MUZZLE_Y = -4
        self.MUZZLE_X_PAD = 6

        # Burst fire
        self.next_fire_time = 0
        self.burst_count = 0
        self.in_burst = False

        # Aim / facing control
        self._prev_mouse_down = False

        # Auto-fire tuning
        self.auto_fire_enabled = True
        self.auto_fire_interval_ms = 175
        self.next_auto_fire_time = 0

    def reset(self):
        self.map_x, self.map_y = 0, 0

        self.player = Player(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2, self.PLAYER_SIZE, "Assault_Class")
        self.player.max_hp = self.starting_hp
        self.player.hp = self.starting_hp

        self.enemy_list = [Enemy(self.MAP_WIDTH, self.MAP_HEIGHT, self.PLAYER_SIZE, "Scarab") for _ in range(self.enemy_count)]

        self.kills = 0
        self.item0_count = 0
        self.next_touch_damage_time = 0
        self.is_touching_enemy = False
        self.GAME_OVER = False

        self.fire_group.empty()
        self.item_group.empty()

    # -------------------- HELPERS --------------------
    def get_player_world_rect(self) -> pygame.Rect:
        r = self.player.rect.copy()
        r.x = r.x - self.map_x
        r.y = r.y - self.map_y
        return r

    def maybe_spawn_drop(self, world_x: int, world_y: int):
        if random.random() < 0.20:
            self.item_group.add(DropItem("item0", world_x, world_y))
        if random.random() < 0.50:
            self.item_group.add(DropItem("item1", world_x, world_y))

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
                if item.kind == "item1":
                    self.player.hp = min(self.player.max_hp, self.player.hp + 1)
                elif item.kind == "item0":
                    self.item0_count += 1
                item.kill()

    def get_muzzle_world_pos(self):
        if self.player.facing == "right":
            muzzle_screen_x = self.player.rect.right - self.MUZZLE_X_PAD
        else:
            muzzle_screen_x = self.player.rect.left + self.MUZZLE_X_PAD

        muzzle_screen_y = self.player.rect.centery + self.MUZZLE_Y

        fx = muzzle_screen_x - self.map_x
        fy = muzzle_screen_y - self.map_y
        return fx, fy

    def can_move(self, dx, dy) -> bool:
        new_x = self.player.rect.centerx - self.map_x + dx
        new_y = self.player.rect.centery - self.map_y + dy

        tile_x = int(new_x // self.SCALED_TILE_SIZE)
        tile_y = int(new_y // self.SCALED_TILE_SIZE)

        if tile_x < 0 or tile_x >= self.MAP_TILES_X or tile_y < 0 or tile_y >= self.MAP_TILES_Y:
            return False

        return collision[tile_y][tile_x] != 1

    # -------------------- DRAW UI --------------------
    def draw_health_bar(self):
        bar_w = 160
        bar_h = 16
        pad = 12
        x = self.SCREEN_WIDTH - pad - bar_w
        y = pad

        pygame.draw.rect(self.screen, (30, 30, 30), (x - 2, y - 2, bar_w + 4, bar_h + 4))
        pygame.draw.rect(self.screen, (80, 80, 80), (x, y, bar_w, bar_h), 1)

        ratio = 0.0
        if self.player.max_hp > 0:
            ratio = max(0.0, min(1.0, self.player.hp / self.player.max_hp))

        fill_w = int(bar_w * ratio)
        if ratio > 0.6:
            color = (0, 200, 60)
        elif ratio > 0.3:
            color = (240, 180, 0)
        else:
            color = (220, 40, 40)

        pygame.draw.rect(self.screen, color, (x, y, fill_w, bar_h))

    def draw_kill_count(self):
        pad = 12
        bar_w = 160
        x = self.SCREEN_WIDTH - pad - bar_w
        y = pad + 24

        label = self.ui_font.render("KILLS:", True, (255, 255, 255))
        self.screen.blit(label, (x, y))

        value_str = str(self.kills)
        digits_x = x + label.get_width() + 8
        digits_y = y - 2

        for ch in value_str:
            img = self.number_images.get(ch)
            if img is not None:
                self.screen.blit(img, (digits_x, digits_y))
                digits_x += img.get_width() + 2
            else:
                t = self.ui_font.render(ch, True, (255, 255, 255))
                self.screen.blit(t, (digits_x, digits_y))
                digits_x += t.get_width() + 2

    def draw_item0_count(self):
        pad = 12
        bar_w = 160
        x = self.SCREEN_WIDTH - pad - bar_w
        y = pad + 52

        if self.item0_icon is not None:
            self.screen.blit(self.item0_icon, (x, y))
            text_x = x + self.item0_icon.get_width() + 6
        else:
            text_x = x

        label = self.ui_font.render(f"x {self.item0_count}", True, (255, 255, 255))
        self.screen.blit(label, (text_x, y - 1))

    def draw_game_over_overlay(self):
        overlay = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        title = self.game_over_font.render("GAME OVER", True, (255, 60, 60))
        hint = self.game_over_hint_font.render("Press ENTER to restart", True, (255, 255, 255))

        tx = (self.SCREEN_WIDTH - title.get_width()) // 2
        ty = (self.SCREEN_HEIGHT - title.get_height()) // 2 - 20
        hx = (self.SCREEN_WIDTH - hint.get_width()) // 2
        hy = ty + title.get_height() + 10

        self.screen.blit(title, (tx, ty))
        self.screen.blit(hint, (hx, hy))

    # -------------------- LOOP TICKS --------------------
    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if self.GAME_OVER and event.key == pygame.K_RETURN:
                self.reset()

    def _mouse_click_edge(self) -> bool:
        now_down = pygame.mouse.get_pressed()[0]
        clicked = now_down and not self._prev_mouse_down
        self._prev_mouse_down = now_down
        return clicked

    def update(self, keys, now_ms: int, mouse_pos):
        if self.GAME_OVER:
            return

        # Facing should stay to the last side the player clicked.
        if self._mouse_click_edge():
            if mouse_pos[0] < self.player.rect.centerx:
                self.player.facing = "left"
            else:
                self.player.facing = "right"

        moving = False
        dx, dy = 0, 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -self.player_speed
            moving = True
            self.player.facing = "left"
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = self.player_speed
            moving = True
            self.player.facing = "right"

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -self.player_speed
            moving = True
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = self.player_speed
            moving = True

        if self.can_move(dx, 0):
            self.map_x -= dx
        if self.can_move(0, dy):
            self.map_y -= dy

        self.player.update(moving, self.player.facing)

        # Auto-fire (no SPACE needed)
        if self.auto_fire_enabled and now_ms >= self.next_auto_fire_time:
            fx, fy = self.get_muzzle_world_pos()
            fireball = Fireball(fx, fy, self.player.facing)
            self.fire_group.add(fireball)
            self.next_auto_fire_time = now_ms + self.auto_fire_interval_ms

        self.fire_group.update()

        # Fireball -> Enemy
        for fire in list(self.fire_group):
            for enemy in self.enemy_list:
                if enemy.alive and fire.rect.colliderect(enemy.rect):
                    # Apply configurable damage (High Damage = 2)
                    for _ in range(max(1, self.damage_to_enemy)):
                        enemy.hit()
                        if not enemy.alive:
                            break

                    fire.kill()

                    if not enemy.alive:
                        self.kills += 1
                        self.maybe_spawn_drop(enemy.rect.centerx, enemy.rect.centery)
                    break

        # Enemy updates + touch damage
        for enemy in self.enemy_list:
            enemy.update(self.player.rect, self.map_x, self.map_y)

        self.apply_touch_damage(now_ms)
        self.collect_items()

        if self.player.hp <= 0:
            self.GAME_OVER = True

    def draw(self):
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.map_img, (self.map_x, self.map_y))

        for enemy in self.enemy_list:
            enemy.draw(self.screen, self.map_x, self.map_y)

        for item in self.item_group:
            item.draw(self.screen, self.map_x, self.map_y)

        self.player.draw(self.screen)

        for fire in self.fire_group:
            self.screen.blit(fire.image, (fire.rect.x + self.map_x, fire.rect.y + self.map_y))

        self.draw_health_bar()
        self.draw_kill_count()
        self.draw_item0_count()

        if self.GAME_OVER:
            self.draw_game_over_overlay()
