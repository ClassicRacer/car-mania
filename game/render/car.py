import pygame


class Car:

    def __init__(self, image: pygame.Surface, pos=(0.0, 0.0), angle_deg=0.0, scale=1.0, pivot=None, z_index=0):
        self.image = image.convert_alpha()
        self.pos = (float(pos[0]), float(pos[1]))
        self.angle_deg = float(angle_deg)
        self.scale = float(scale)
        self._cached_scale = None
        self._cached_sprite = None
        self._w, self._h = self.image.get_size()
        self.pivot = (self._w * 0.5, self._h * 0.5) if pivot is None else (float(pivot[0]), float(pivot[1]))
        self.z_index = int(z_index)

    def set_pose(self, pos, angle_deg):
        self.pos = (float(pos[0]), float(pos[1]))
        self.angle_deg = float(angle_deg)

    def set_scale(self, scale):
        self.scale = float(scale)

    def _scaled_sprite(self, total_scale: float) -> pygame.Surface:
        if self._cached_sprite is not None and self._cached_scale_total == total_scale:
            return self._cached_sprite
        s = max(1e-6, total_scale)
        if abs(s - 1.0) <= 1e-3:
            spr = self.image
        else:
            w = max(1, int(round(self._w * s)))
            h = max(1, int(round(self._h * s)))
            spr = pygame.transform.smoothscale(self.image, (w, h))
        self._cached_scale_total = total_scale
        self._cached_sprite = spr
        return spr

    def _screen_from_world(self, world_xy, camera_xy, zoom, pivot_xy):
        dx = (world_xy[0] - camera_xy[0]) * zoom
        dy = (world_xy[1] - camera_xy[1]) * zoom
        return (pivot_xy[0] + dx, pivot_xy[1] + dy)
    
    def render_in_canvas_space(self, canvas: pygame.Surface, world_top_left_px, zoom: float):
        total_scale = self.scale * zoom
        spr = self._scaled_sprite(total_scale)

        x = world_top_left_px[0] + self.pos[0] * zoom
        y = world_top_left_px[1] + self.pos[1] * zoom

        rotated = pygame.transform.rotate(spr, -self.angle_deg)
        rect = rotated.get_rect()
        rect.topleft = (int(round(x)), int(round(y)))
        canvas.blit(rotated, rect)