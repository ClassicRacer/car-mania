import math

import pygame

from game.io.render import end_frame, get_half_screen, get_logical_size
from game.render.level_full import Camera, LevelFullRenderer
from game.ui.base_screen import BaseScreen

class Gameplay(BaseScreen):
    def __init__(self, back_action=None):
        super().__init__(back_action)
        self.full_renderer = None
        self.car_data = None
        self.car_image = None
        self.car_sprite = None
        self.car_scale = 1.0
        self.car_world_pos = (0.0, 0.0)
        self.camera = None

    def enter(self, ctx):
        super().enter(ctx)
        self.full_renderer = LevelFullRenderer(ctx["pieces"])
        self.camera = Camera(zoom=1.1)
        self.car_data = ctx["selected_car"]
        self.car_image = None
        self.car_sprite = None
        self.car_scale = 1.0
        level_data = ctx["level_data"]
        if level_data:
            bounds = self.full_renderer.get_piece_bounds(level_data)
            self.camera.x = -bounds.x
            self.camera.y = -bounds.y
            self.car_world_pos = (-bounds.x, -bounds.y)
        if self.car_data:
            img = self.car_data.get("image_data")
            if img:
                self.car_image = img
                scale_override = ctx.get("car_world_scale")
                if scale_override is not None:
                    self.car_scale = float(scale_override)
                else:
                    self.car_scale = float(self.car_data.get("world_scale", 0.25))
                self.car_sprite = self._build_car_sprite(self.car_image, self.car_scale)

    def on_resize(self, ctx, size):
        super().on_resize(ctx, size)

    def update(self, ctx, dt):
        actions = self.step(ctx)
        if self.handle_back(ctx, actions):
            return True
        return True

    def render(self, ctx):
        surf = ctx["window"]
        level_data = ctx["level_data"]
        W, H = get_logical_size()
        half_W, half_H = get_half_screen()
        self.full_renderer.render_to(surf, level_data, camera=self.camera)
        if self.car_sprite:
            sx, sy = self._world_to_screen(self.car_world_pos, self.camera, surf.get_size())
            rect = self.car_sprite.get_rect()
            rect.center = (int(round(sx)), int(round(sy)))
            surf.blit(self.car_sprite, rect)

        pygame.draw.line(surf, (255, 0, 0), (half_W - 10, half_H), (half_W + 10, half_H), 2)
        pygame.draw.line(surf, (255, 0, 0), (half_W, half_H - 10), (half_W, half_H + 10), 2)
        end_frame()

    def _world_to_screen(self, world_pos, camera, surface_size):
        pivot = (surface_size[0] * 0.5, surface_size[1] * 0.5)
        zoom = max(1e-6, camera.zoom)
        angle = math.radians(camera.rot_deg)
        dx = world_pos[0] - camera.x
        dy = world_pos[1] - camera.y
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        rx = dx * cos_a - dy * sin_a
        ry = dx * sin_a + dy * cos_a
        return pivot[0] + rx * zoom, pivot[1] + ry * zoom

    def _build_car_sprite(self, image: pygame.Surface, scale: float) -> pygame.Surface:
        scale = max(1e-3, scale)
        if abs(scale - 1.0) <= 1e-3:
            return image.copy()
        w, h = image.get_size()
        size = (max(1, int(round(w * scale))), max(1, int(round(h * scale))))
        if size == image.get_size():
            return image.copy()
        return pygame.transform.smoothscale(image, size)
