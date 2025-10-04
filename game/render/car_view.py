from dataclasses import dataclass
from typing import Tuple

import pygame

from game.core.model.car import Car


@dataclass
class CarAppearance:
    image: pygame.Surface
    pivot: Tuple[float, float]
    z_index: int = 0

class CarRenderer:
    def __init__(self):
        self._cache = {}

    def _scaled_sprite(self, image: pygame.Surface, scale: float) -> pygame.Surface:
        key = (id(image), round(scale, 5))
        if key in self._cache:
            return self._cache[key]
        s = max(1e-6, scale)
        if abs(s - 1.0) <= 1e-3:
            spr = image
        else:
            w, h = image.get_size()
            spr = pygame.transform.smoothscale(image, (max(1, int(round(w * s))), max(1, int(round(h * s)))))
        self._cache[key] = spr
        return spr

    def render(self, canvas: pygame.Surface, car: Car, world_top_left_px: Tuple[float, float], zoom: float):
        t = car.transform
        a = car.appearance
        total_scale = t.scale * zoom
        spr = self._scaled_sprite(a.image, total_scale)
        rotated = pygame.transform.rotate(spr, -t.angle_deg)

        cx = world_top_left_px[0] + t.pos[0] * zoom
        cy = world_top_left_px[1] + t.pos[1] * zoom
        rect = rotated.get_rect(center=(int(round(cx)), int(round(cy))))
        canvas.blit(rotated, rect)

class CarActor:
    def __init__(self, car_renderer, car):
        self.car_renderer = car_renderer
        self.car = car
    def render_in_canvas_space(self, canvas, world_top_left_px, zoom):
        self.car_renderer.render(canvas, self.car, world_top_left_px, zoom)