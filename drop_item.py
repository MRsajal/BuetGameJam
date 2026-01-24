import os
import pygame


class DropItem(pygame.sprite.Sprite):
    """A collectible item stored in WORLD coordinates.

    kind: "item0" or "item1"
    """

    def __init__(self, kind: str, world_x: int, world_y: int):
        super().__init__()

        kind = kind.lower()
        if kind not in ("item0", "item1"):
            raise ValueError(f"Unknown drop kind: {kind}")

        self.kind = kind

        path = os.path.join("drop", f"{kind}.png")
        self.image = pygame.image.load(path).convert_alpha()
        # scale to a nice pickup size
        self.image = pygame.transform.scale(self.image, (18, 18))
        self.rect = self.image.get_rect(center=(int(world_x), int(world_y)))

    def draw(self, screen: pygame.Surface, map_x: int, map_y: int):
        # WORLD -> SCREEN
        screen.blit(self.image, (self.rect.x + map_x, self.rect.y + map_y))
