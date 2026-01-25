import pygame
import sys
import os


class Menu:
    """Menu system handling MENU / START_SUB / OPTIONS / CONTROLS states."""

    def __init__(self, screen: pygame.Surface, screen_width: int, screen_height: int):
        self.screen = screen
        self.SCREEN_WIDTH = screen_width
        self.SCREEN_HEIGHT = screen_height

        # Game States: "MENU", "START_SUB", "CONTROLS", "OPTIONS"
        self.game_state = "MENU"

        # Settings controlled by menu
        self.music_enabled = True
        self.sfx_enabled = True

        # Selected loadout (defaults)
        self.selected_loadout = "speed"  # speed|guard|damage

        # Assets
        self.menu_bg = pygame.image.load("menu_background.png").convert()
        self.menu_bg = pygame.transform.scale(self.menu_bg, (self.SCREEN_WIDTH, self.SCREEN_HEIGHT))

        self.menu_buttons = {
            "start": [pygame.image.load("menu/start/1.png").convert_alpha(),
                      pygame.image.load("menu/start/2.png").convert_alpha()],
            "option": [pygame.image.load("menu/option/1.png").convert_alpha(),
                       pygame.image.load("menu/option/2.png").convert_alpha()],
            "controls": [pygame.image.load("menu/controls/1.png").convert_alpha(),
                         pygame.image.load("menu/controls/2.png").convert_alpha()],
            "exit": [pygame.image.load("menu/exit/1.png").convert_alpha(),
                     pygame.image.load("menu/exit/2.png").convert_alpha()],
            "music_on": [pygame.image.load("menu/option/music/on/1.png").convert_alpha(),
                         pygame.image.load("menu/option/music/on/2.png").convert_alpha()],
            "music_off": [pygame.image.load("menu/option/music/off/1.png").convert_alpha(),
                          pygame.image.load("menu/option/music/off/2.png").convert_alpha()],
            "sfx_on": [pygame.image.load("menu/option/sfx/on/1.png").convert_alpha(),
                       pygame.image.load("menu/option/sfx/on/2.png").convert_alpha()],
            "sfx_off": [pygame.image.load("menu/option/sfx/off/1.png").convert_alpha(),
                        pygame.image.load("menu/option/sfx/off/2.png").convert_alpha()],
            "speed": [pygame.image.load("menu/start/speed/1.png").convert_alpha(),
                      pygame.image.load("menu/start/speed/2.png").convert_alpha()],
            "guard": [pygame.image.load("menu/start/guard/1.png").convert_alpha(),
                      pygame.image.load("menu/start/guard/2.png").convert_alpha()],
            "damage": [pygame.image.load("menu/option/1.png").convert_alpha(),
                       pygame.image.load("menu/option/2.png").convert_alpha()],
        }

        # --- LOAD CHARACTER AVATARS FOR MENU ---
        self.avatars = {
            "speed": self.load_frames(os.path.join("Assault_Class", "idle", "right")),
            "guard": self.load_frames(os.path.join("MachineGunner_Class", "Idle", "right")),
            "damage": self.load_frames(os.path.join("Sniper_Class", "Idle", "right"))
        }
        
        # Animation State
        self.avatar_frame_index = 0
        self.avatar_timer = 0

        # Fonts
        self.menu_title_font = pygame.font.SysFont("Arial", 48, bold=True)
        self.menu_controls_label_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.menu_detail_font = pygame.font.SysFont("Arial", 32, bold=True)
        self.menu_hint_font = pygame.font.SysFont("Arial", 24)

        # One-tap guard so click doesn't trigger multiple times
        self._prev_mouse_down = False

    def load_frames(self, path):
        """Helper to load animation frames from a folder."""
        frames = []
        i = 0
        while True:
            full_path = os.path.join(path, f"{i}.png")
            if not os.path.exists(full_path):
                break
            try:
                img = pygame.image.load(full_path).convert_alpha()
                # Scale up to look good in the menu (3x size = 96x96 since base is 32x32)
                img = pygame.transform.scale(img, (96, 96))
                frames.append(img)
            except Exception as e:
                print(f"Error loading {full_path}: {e}")
            i += 1
        return frames

    def _consume_click(self) -> bool:
        """Return True only on mouse down edge."""
        now_down = pygame.mouse.get_pressed()[0]
        clicked = now_down and not self._prev_mouse_down
        self._prev_mouse_down = now_down
        return clicked

    def draw_menu_button(self, button_name: str, x: int, y: int, mouse_pos) -> bool:
        """Draw a menu button and return True if hovered in middle 50%."""
        img_normal = self.menu_buttons[button_name][0]
        img_hover = self.menu_buttons[button_name][1]

        # Scale buttons to 510x170 pixels
        img_normal = pygame.transform.scale(img_normal, (510, 170))
        img_hover = pygame.transform.scale(img_hover, (510, 170))
        rect = img_normal.get_rect(topleft=(x, y))

        middle_left = x + (rect.width * 0.25)
        middle_right = x + (rect.width * 0.75)
        middle_top = y + (rect.height * 0.25)
        middle_bottom = y + (rect.height * 0.75)

        in_middle_50 = (middle_left <= mouse_pos[0] <= middle_right and
                        middle_top <= mouse_pos[1] <= middle_bottom)

        if in_middle_50:
            self.screen.blit(img_hover, rect)
            return True
        else:
            self.screen.blit(img_normal, rect)
            return False

    def _draw_main_menu(self):
        self.screen.blit(self.menu_bg, (0, 0))

        mouse = pygame.mouse.get_pos()
        clicked = self._consume_click()

        cx = 0
        start_y = 0

        if self.draw_menu_button("start", cx, start_y, mouse) and clicked:
            self.game_state = "START_SUB"

        if self.draw_menu_button("option", cx, start_y + 153, mouse) and clicked:
            self.game_state = "OPTIONS"

        if self.draw_menu_button("controls", cx, start_y + 306, mouse) and clicked:
            self.game_state = "CONTROLS"

        if self.draw_menu_button("exit", cx, start_y + 459, mouse) and clicked:
            pygame.quit()
            sys.exit()

    def _draw_controls_overlay(self):
        self.screen.blit(self.menu_bg, (0, 0))

        overlay = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        title = self.menu_title_font.render("ROBO SURVIVE", True, (255, 100, 100))
        self.screen.blit(title, (self.SCREEN_WIDTH // 2 - title.get_width() // 2,
                                self.SCREEN_HEIGHT // 2 - 120))

        controls_text = self.menu_controls_label_font.render("CONTROLS", True, (200, 200, 200))
        self.screen.blit(controls_text, (self.SCREEN_WIDTH // 2 - controls_text.get_width() // 2,
                                         self.SCREEN_HEIGHT // 2 - 50))

        controls = [
            "ARROW KEYS or WASD - Move",
            "MOUSE - Aim",
            "AUTO FIRE - Always",
        ]

        y_pos = self.SCREEN_HEIGHT // 2 + 20
        for control in controls:
            line = self.menu_detail_font.render(control, True, (255, 255, 255))
            self.screen.blit(line, (self.SCREEN_WIDTH // 2 - line.get_width() // 2, y_pos))
            y_pos += 40

        hint = self.menu_hint_font.render("Press any key to return", True, (200, 200, 200))
        self.screen.blit(hint, (self.SCREEN_WIDTH // 2 - hint.get_width() // 2, self.SCREEN_HEIGHT - 50))

    def _draw_options_menu(self):
        self.screen.blit(self.menu_bg, (0, 0))

        mouse = pygame.mouse.get_pos()
        clicked = self._consume_click()

        title = self.menu_title_font.render("OPTIONS", True, (255, 100, 100))
        self.screen.blit(title, (self.SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

        music_button_name = "music_on" if self.music_enabled else "music_off"
        if self.draw_menu_button(music_button_name, 50, self.SCREEN_HEIGHT // 2 - 100, mouse) and clicked:
            self.music_enabled = not self.music_enabled

        sfx_button_name = "sfx_on" if self.sfx_enabled else "sfx_off"
        if self.draw_menu_button(sfx_button_name, 50, self.SCREEN_HEIGHT // 2 + 50, mouse) and clicked:
            self.sfx_enabled = not self.sfx_enabled

        hint_text = self.menu_hint_font.render("Press any key to go back", True, (200, 200, 200))
        self.screen.blit(hint_text, (self.SCREEN_WIDTH // 2 - hint_text.get_width() // 2, self.SCREEN_HEIGHT - 50))

    def _draw_start_menu(self):
        self.screen.blit(self.menu_bg, (0, 0))

        # --- UPDATE ANIMATION ---
        self.avatar_timer += 1
        if self.avatar_timer >= 10:  # Adjust speed: Lower = Faster
            self.avatar_timer = 0
            self.avatar_frame_index += 1

        mouse = pygame.mouse.get_pos()
        clicked = self._consume_click()

        title = self.menu_title_font.render("CHOOSE MODE", True, (255, 100, 100))
        self.screen.blit(title, (self.SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

        # Layout
        left_x = 120
        avatar_x = left_x
        text_x = avatar_x + 120

        y1 = self.SCREEN_HEIGHT // 2 - 160
        y2 = self.SCREEN_HEIGHT // 2 - 20
        y3 = self.SCREEN_HEIGHT // 2 + 120

        stats_font = pygame.font.SysFont("Arial", 22, bold=True)
        class_name_font = pygame.font.SysFont("Arial", 42, bold=True)

        # Helper to draw the avatar
        def draw_avatar(key, y_pos):
            frames = self.avatars.get(key, [])
            if frames:
                frame = frames[self.avatar_frame_index % len(frames)]
                self.screen.blit(frame, (avatar_x, y_pos - 20))

        # Helper: draw text button
        def text_button(label: str, y_pos: int) -> bool:
            txt = class_name_font.render(label, True, (255, 255, 255))
            rect = txt.get_rect(topleft=(text_x, y_pos))

            # hover highlight
            if rect.collidepoint(mouse):
                pygame.draw.rect(self.screen, (255, 255, 255), rect.inflate(20, 14), 2)
                if clicked:
                    return True

            self.screen.blit(txt, rect.topleft)
            return False

        # --- Option 1: SPEEDY (Assault) ---
        draw_avatar("speed", y1)
        if text_button("SPEEDY", y1):
            self.selected_loadout = "speed"
            return "START_GAME"
        s1 = stats_font.render("SPD 5 | HP 12 | ENEMIES 5 | DMG 1", True, (255, 255, 255))
        self.screen.blit(s1, (text_x, y1 + 55))

        # --- Option 2: THE ROCK (MachineGunner) ---
        draw_avatar("guard", y2)
        if text_button("THE ROCK", y2):
            self.selected_loadout = "guard"
            return "START_GAME"
        s2 = stats_font.render("SPD 3 | HP 15 | ENEMIES 7 | DMG 1", True, (255, 255, 255))
        self.screen.blit(s2, (text_x, y2 + 55))

        # --- Option 3: ONE SHOT (Sniper) ---
        draw_avatar("damage", y3)
        if text_button("ONE SHOT", y3):
            self.selected_loadout = "damage"
            return "START_GAME"
        s3 = stats_font.render("SPD 4 | HP 10 | ENEMIES 6 | DMG 2", True, (255, 255, 255))
        self.screen.blit(s3, (text_x, y3 + 55))

        hint_text = self.menu_hint_font.render("Press any key to go back", True, (200, 200, 200))
        self.screen.blit(hint_text, (self.SCREEN_WIDTH // 2 - hint_text.get_width() // 2, self.SCREEN_HEIGHT - 50))

        return None

    def handle_event(self, event: pygame.event.Event):
        if event.type != pygame.KEYDOWN:
            return None

        # any key goes back from these
        if self.game_state in ("CONTROLS", "OPTIONS", "START_SUB"):
            self.game_state = "MENU"
        return None

    def update_and_draw(self):
        """Draw current menu state.

        Returns:
            None or ("START_GAME", settings_dict)
        """
        if self.game_state == "MENU":
            self._draw_main_menu()
            return None

        if self.game_state == "CONTROLS":
            self._draw_controls_overlay()
            return None

        if self.game_state == "OPTIONS":
            self._draw_options_menu()
            return None

        if self.game_state == "START_SUB":
            action = self._draw_start_menu()
            if action == "START_GAME":
                # Loadout rules:
                # 1) Speed:     Assault_Class, speed=5, hp=12, enemy=5, dmg_to_enemy=1
                # 2) Guard:     MachineGunner_Class, speed=3, hp=15, enemy=7, dmg_to_enemy=1
                # 3) HighDamage Sniper_Class, speed=4, hp=10, enemy=6, dmg_to_enemy=2
                
                if self.selected_loadout == "speed":
                    loadout = {
                        "class": "Assault_Class", 
                        "player_speed": 5, 
                        "player_hp": 12, 
                        "enemy_count": 5, 
                        "damage_to_enemy": 1
                    }
                elif self.selected_loadout == "guard":
                    loadout = {
                        "class": "MachineGunner_Class", 
                        "player_speed": 3, 
                        "player_hp": 15, 
                        "enemy_count": 7, 
                        "damage_to_enemy": 1
                    }
                else:
                    loadout = {
                        "class": "Sniper_Class", 
                        "player_speed": 4, 
                        "player_hp": 10, 
                        "enemy_count": 6, 
                        "damage_to_enemy": 2
                    }

                settings = {
                    "music_enabled": self.music_enabled,
                    "sfx_enabled": self.sfx_enabled,
                    "loadout": loadout,
                }
                return "START_GAME", settings
            return None

        # fallback
        self.game_state = "MENU"
        return None