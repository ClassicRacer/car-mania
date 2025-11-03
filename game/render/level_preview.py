
import pygame
from game.render.level_full import LevelFullRenderer

class LevelPreviewRenderer:
    def __init__(self, pieces: dict, target_size=(150, 150), *, pad=12, corner_radius=12, show_bg=True):
        self.size = target_size
        self.pad = pad
        self.radius = int(corner_radius)
        self.show_bg = show_bg
        self.full = LevelFullRenderer(pieces)
        self._mask_cache = {}

    def _rounded_mask(self, w: int, h: int, r: int) -> pygame.Surface:
        key = (w, h, r)
        surf = self._mask_cache.get(key)
        if surf is None:
            surf = pygame.Surface((w, h), pygame.SRCALPHA).convert_alpha()
            surf.fill((0, 0, 0, 0))
            pygame.draw.rect(surf, (255, 255, 255, 255), (0, 0, w, h), border_radius=r)
            self._mask_cache[key] = surf
        return surf

    def render(self, level_row: dict) -> pygame.Surface:
        entry = self.full._get_world(level_row)
        world: pygame.Surface = entry["world"]
        bg = entry["bg"]

        ww, wh = world.get_size()
        W, H = self.size
        avail_w = max(1, W - 2 * self.pad)
        avail_h = max(1, H - 2 * self.pad)

        s = min(avail_w / max(1, ww), avail_h / max(1, wh))
        scaled_w = max(1, int(round(ww * s)))
        scaled_h = max(1, int(round(wh * s)))

        if s < 1.0:
            scaled = pygame.transform.smoothscale(world, (scaled_w, scaled_h))
        elif s > 1.0:
            scaled = pygame.transform.scale(world, (scaled_w, scaled_h))
        else:
            scaled = world

        thumb = pygame.Surface((W, H), pygame.SRCALPHA).convert_alpha()
        if self.show_bg:
            thumb.fill((*bg, 255))
        else:
            thumb.fill((0, 0, 0, 0))

        x = (W - scaled.get_width()) // 2
        y = (H - scaled.get_height()) // 2
        thumb.blit(scaled, (x, y))

        mask = self._rounded_mask(W, H, self.radius)
        thumb.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        return thumb