import pygame
import sys

from menu import Menu
from game import Game


pygame.init()
pygame.mixer.init()

# -------------------- SCREEN --------------------
SCREEN_WIDTH, SCREEN_HEIGHT = 1040, 672
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("ROBO Survive")
clock = pygame.time.Clock()
FPS = 60

# -------------------- STATES --------------------
# "MENU" or "PLAYING"
app_state = "MENU"

menu = Menu(screen, SCREEN_WIDTH, SCREEN_HEIGHT)

def _start_bg_music():
    try:
        pygame.mixer.music.load("music2.mp3")
        pygame.mixer.music.set_volume(0.7)
        pygame.mixer.music.play(-1)
    except Exception:
        # If audio device missing or file can't load, just skip music.
        pass

# Start music initially (menu toggle can later stop it)
_start_bg_music()

game: Game | None = None

running = True
while running:
    keys = pygame.key.get_pressed()
    now_ms = pygame.time.get_ticks()
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if app_state == "MENU":
            menu.handle_event(event)
        elif app_state == "PLAYING" and game is not None:
            game.handle_event(event)

    if app_state == "MENU":
        action = menu.update_and_draw()

        # Apply music toggle live
        try:
            if menu.music_enabled:
                if not pygame.mixer.music.get_busy():
                    _start_bg_music()
            else:
                pygame.mixer.music.stop()
        except Exception:
            pass

        if action is not None:
            action_name, settings = action
            if action_name == "START_GAME":
                loadout = settings["loadout"]
                game = Game(
                    screen,
                    SCREEN_WIDTH,
                    SCREEN_HEIGHT,
                    player_class=loadout["class"],
                    player_speed=loadout["player_speed"],
                    player_hp=loadout["player_hp"],
                    enemy_count=loadout["enemy_count"],
                    damage_to_enemy=loadout["damage_to_enemy"],
                )
                app_state = "PLAYING"

    elif app_state == "PLAYING" and game is not None:
        game.update(keys, now_ms, mouse_pos)
        game.draw()

        # keep applying music toggle in-game too
        try:
            if menu.music_enabled:
                if not pygame.mixer.music.get_busy():
                    _start_bg_music()
            else:
                pygame.mixer.music.stop()
        except Exception:
            pass

        if game.return_to_menu:
            game = None
            app_state = "MENU"

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()