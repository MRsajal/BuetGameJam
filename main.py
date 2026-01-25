import pygame
import sys

from menu import Menu
from game import Game


pygame.init()

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
        if action is not None:
            action_name, settings = action
            if action_name == "START_GAME":
                loadout = settings["loadout"]
                # --- UPDATED: Passing the class name to the Game ---
                game = Game(
                    screen,
                    SCREEN_WIDTH,
                    SCREEN_HEIGHT,
                    player_class=loadout["class"],  # This is the key change
                    player_speed=loadout["player_speed"],
                    player_hp=loadout["player_hp"],
                    enemy_count=loadout["enemy_count"],
                    damage_to_enemy=loadout["damage_to_enemy"],
                    #music_enabled=settings["music_enabled"]
                )
                app_state = "PLAYING"

    elif app_state == "PLAYING" and game is not None:
        game.update(keys, now_ms, mouse_pos)
        game.draw()

        if game.return_to_menu:
            game = None
            app_state = "MENU"

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()