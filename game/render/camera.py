import random
from typing import TYPE_CHECKING

import pygame

from game.io.render import get_logical_size

if TYPE_CHECKING:
    from game.render.level_full import LevelFullRenderer


class Camera:
    def __init__(self, x=0.0, y=0.0, zoom=1.0, rot_deg=0.0):
        self.x = float(x)
        self.y = float(y)
        self.zoom = float(zoom)
        self.rot_deg = float(rot_deg)

    def fit_to_bounds(self, surf_size, bounds, margin_px=40, hud_h=240):
        tw, th = surf_size
        avail_w = max(1, tw - margin_px*2)
        avail_h = max(1, th - margin_px*2 - hud_h)
        sx = avail_w / max(1, bounds.width)
        sy = avail_h / max(1, bounds.height)
        self.zoom = min(sx, sy)
        self.x = bounds.centerx
        self.y = bounds.centery
        self.rot_deg = 0.0


class CameraTour:
    WAIT_DURATION = 2.5
    PAN_SPEED = 640.0
    ZOOM_SPEED = 1.6
    MIN_ZOOM = 0.05
    MAX_ZOOM = 5.0
    POSITION_EPS = 1.0
    ZOOM_EPS = 0.02
    FOCUS_ZOOM = 1.2
    ROTATE_SPEED = 20.0
    ROTATE_EPS = 0.5

    def __init__(self, renderer: 'LevelFullRenderer', camera: Camera):
        self.renderer = renderer
        self.camera = camera
        self.state = "idle"
        self.timer = 0.0
        self.gate_points = []
        self.level_center = pygame.Vector2(0.0, 0.0)
        self.origin = pygame.Vector2(0.0, 0.0)
        self.index = 0
        self._zoom_out_start_zoom = 1.0
        self._zoom_out_start_rot = 0.0
        self._zoom_out_start_pos = pygame.Vector2(0.0, 0.0)
        self._origin_start_pos = pygame.Vector2(0.0, 0.0)
        self._origin_target_pos = pygame.Vector2(0.0, 0.0)
        self._origin_start_zoom = 1.0
        self._origin_target_zoom = 1.0
        self._origin_duration = 0.0
        self._origin_progress = 0.0
        self._rotation_dir = 1
        self._zoom_out_end_rot = 0.0
        self.base_zoom = 1.0
        self._zoom_in_target = 1.0
        self._zoom_out_target_zoom = 1.0
        self._gameplay_start_pos = pygame.Vector2(0.0, 0.0)
        self._gameplay_target_pos = pygame.Vector2(0.0, 0.0)
        self._gameplay_start_zoom = 1.0
        self._gameplay_target_zoom = 1.0
        self._gameplay_duration = 0.0
        self._gameplay_progress = 0.0
        self._gameplay_start_rot = 0.0
        self._gameplay_end_rot = 0.0
        self._level_bounds = None
        self._gameplay_on_complete = None

    def load_level(self, level_row: dict):
        if not level_row:
            self.state = "idle"
            self.gate_points = []
            return

        entry = self.renderer._get_world(level_row)
        bounds = entry["bounds"]
        world = entry["world"]

        self.origin = pygame.Vector2(-bounds.x, -bounds.y)
        self.level_center = pygame.Vector2(world.get_width() * 0.5, world.get_height() * 0.5)
        self._level_bounds = bounds.copy()

        gates = list(entry.get("gates") or [])
        gate_image = self.renderer.pieces.get("gate") if hasattr(self.renderer, "pieces") else None
        if gate_image:
            gx, gy = gate_image.get_size()
            gate_offset = pygame.Vector2(gx * 0.5, gy * 0.5)
        else:
            gate_offset = pygame.Vector2(0.0, 0.0)

        fit_zoom = self._compute_fit_zoom(world)
        focus_zoom = self._clamp_zoom(self.FOCUS_ZOOM)
        self._zoom_in_target = focus_zoom
        self.base_zoom = self._clamp_zoom(min(fit_zoom, focus_zoom))
        self._zoom_out_target_zoom = self.base_zoom

        self.gate_points = []
        for order, x, y, _ in sorted(gates, key=lambda g: g[0]):
            px = (x - bounds.x) + gate_offset.x
            py = (y - bounds.y) + gate_offset.y
            self.gate_points.append(pygame.Vector2(px, py))

        self.state = "wait"
        self.timer = self.WAIT_DURATION
        self.index = 0
        self.camera.rot_deg = 0.0
        self.camera.zoom = self.base_zoom
        self._zoom_out_start_zoom = self.camera.zoom
        self._zoom_out_start_rot = 0.0
        self._zoom_out_start_pos = pygame.Vector2(self.camera.x, self.camera.y)
        self._origin_start_pos = pygame.Vector2(self.camera.x, self.camera.y)
        self._origin_target_pos = self.origin.copy()
        self._origin_start_zoom = self.camera.zoom
        self._origin_target_zoom = self._zoom_in_target
        self._origin_duration = 0.0
        self._origin_progress = 0.0
        self._rotation_dir = random.choice((-1, 1))

    def update(self, dt: float):
        if self.state not in ["idle", "wait", "zoom_out", "gameplay"]:
            self.camera.rot_deg = (self.camera.rot_deg + self._rotation_dir * self.ROTATE_SPEED * dt) % 360.0

        if self.state == "idle":
            return

        if self.state == "wait":
            self.timer -= dt
            if self.timer <= 0.0:
                self._begin_origin_move()
            else:
                return

        if self.state == "origin":
            done = self._update_origin_motion(dt)
            if done:
                self.index = 0
                if self.gate_points:
                    self.state = "gates"
                else:
                    self._begin_zoom_out()
            return

        if self.state == "gates":
            if not self.gate_points:
                self._begin_zoom_out()
                return
            target = self.gate_points[self.index]
            reached = self._approach_position(target, dt)
            self._approach_zoom(self._zoom_in_target, dt)
            if reached:
                self.index += 1
                if self.index >= len(self.gate_points):
                    self._begin_zoom_out()
            return

        if self.state == "zoom_out":
            zoom_done = self._approach_zoom(self._zoom_out_target_zoom, dt)
            position_done = self._update_zoom_out_position()
            rotation_done = self._update_zoom_out_rotation()
            if position_done and zoom_done and rotation_done:
                self.state = "wait"
                self.timer = self.WAIT_DURATION
                self.index = 0
                self._zoom_out_start_zoom = self.camera.zoom
                self._zoom_out_start_rot = 0.0
                self._zoom_out_start_pos = pygame.Vector2(self.camera.x, self.camera.y)
            return

        if self.state == "gameplay":
            done = self._update_gameplay_motion(dt)
            if done:
                self.state = "idle"
                self._dispatch_gameplay_complete()
            return

    def _approach_position(self, target: pygame.Vector2, dt: float) -> bool:
        current = pygame.Vector2(self.camera.x, self.camera.y)
        delta = target - current
        dist = delta.length()
        if dist <= self.POSITION_EPS:
            self.camera.x, self.camera.y = target.x, target.y
            return True

        if dist > 0:
            step = self.PAN_SPEED * dt
            if step >= dist:
                current = target
            else:
                current += delta.normalize() * step
            self.camera.x, self.camera.y = current.x, current.y
        return False

    def _approach_zoom(self, target_zoom: float, dt: float) -> bool:
        current = self.camera.zoom
        delta = target_zoom - current
        if abs(delta) <= self.ZOOM_EPS:
            self.camera.zoom = self._clamp_zoom(target_zoom)
            return True

        step = self.ZOOM_SPEED * dt
        if step >= abs(delta):
            self.camera.zoom = self._clamp_zoom(target_zoom)
        else:
            self.camera.zoom = self._clamp_zoom(current + step if delta > 0 else current - step)
        return False

    def _clamp_zoom(self, value: float) -> float:
        return max(self.MIN_ZOOM, min(self.MAX_ZOOM, value))

    def _begin_origin_move(self) -> None:
        self._origin_start_pos = pygame.Vector2(self.camera.x, self.camera.y)
        self._origin_target_pos = self.origin.copy()
        self._origin_start_zoom = self.camera.zoom
        self._origin_target_zoom = self._zoom_in_target
        dist = self._origin_start_pos.distance_to(self._origin_target_pos)
        move_duration = dist / self.PAN_SPEED if self.PAN_SPEED > 1e-6 else 0.0
        zoom_delta = abs(self._origin_target_zoom - self._origin_start_zoom)
        zoom_duration = zoom_delta / self.ZOOM_SPEED if self.ZOOM_SPEED > 1e-6 else 0.0
        self._origin_duration = max(move_duration, zoom_duration, 1e-6)
        self._origin_progress = 0.0
        self._rotation_dir = random.choice((-1, 1))
        self.state = "origin"

    def _update_origin_motion(self, dt: float) -> bool:
        if self._origin_duration <= 1e-6:
            self.camera.x, self.camera.y = self._origin_target_pos.x, self._origin_target_pos.y
            self.camera.zoom = self._origin_target_zoom
            return True

        self._origin_progress = min(1.0, self._origin_progress + dt / self._origin_duration)
        t = self._origin_progress
        pos = self._origin_start_pos.lerp(self._origin_target_pos, t)
        self.camera.x, self.camera.y = pos.x, pos.y
        self.camera.zoom = self._origin_start_zoom + (self._origin_target_zoom - self._origin_start_zoom) * t
        return self._origin_progress >= 0.999

    def _begin_zoom_out(self) -> None:
        self._zoom_out_start_zoom = self.camera.zoom
        start_angle = self.camera.rot_deg % 360.0
        self._zoom_out_start_rot = start_angle
        self._zoom_out_end_rot = 0.0 if start_angle <= 180.0 else 360.0
        self._zoom_out_start_pos = pygame.Vector2(self.camera.x, self.camera.y)
        self.state = "zoom_out"

    def _update_zoom_out_rotation(self) -> bool:
        progress = self._zoom_out_progress()
        if progress is None:
            angle = self._zoom_out_end_rot
        else:
            angle = self._zoom_out_end_rot + (self._zoom_out_start_rot - self._zoom_out_end_rot) * progress
        angle %= 360.0
        self.camera.rot_deg = angle
        return min(angle, 360.0 - angle) <= self.ROTATE_EPS

    def _update_zoom_out_position(self) -> bool:
        progress = self._zoom_out_progress()
        if progress is None:
            target = self.level_center
        else:
            t = 1.0 - progress
            target = self._zoom_out_start_pos.lerp(self.level_center, t)
        self.camera.x, self.camera.y = target.x, target.y
        return target.distance_to(self.level_center) <= self.POSITION_EPS

    def _zoom_out_progress(self):
        start_zoom = self._zoom_out_start_zoom
        target_zoom = self._zoom_out_target_zoom
        span = start_zoom - target_zoom
        if abs(span) <= 1e-6:
            return None
        progress = (self.camera.zoom - target_zoom) / span
        return max(0.0, min(1.0, progress))

    def _compute_fit_zoom(self, world_surface: pygame.Surface) -> float:
        screen_w, screen_h = get_logical_size()
        margin = getattr(self.renderer, "margin", 0)
        hud_h = getattr(self.renderer, "hud_h", 0)
        avail_w = max(1, screen_w - margin * 2)
        avail_h = max(1, screen_h - margin * 2 - hud_h)
        ww, wh = world_surface.get_size()
        if ww <= 0 or wh <= 0:
            return 1.0
        return min(avail_w / ww, avail_h / wh)

    def begin_gameplay(self, car_pos, target_zoom=None, *, relative=False, on_complete=None):
        if car_pos is None:
            car_vec = pygame.Vector2(self.camera.x, self.camera.y)
        else:
            if hasattr(car_pos, "pos"):
                src_pos = car_pos.pos
            else:
                src_pos = car_pos
            car_vec = pygame.Vector2(src_pos)
            if self._level_bounds is not None:
                if not relative:
                    bounds = self._level_bounds
                    car_vec.x -= bounds.x
                    car_vec.y -= bounds.y
                else:
                    margin = max(64.0, float(getattr(self.renderer, "margin", 0)))
                    bounds = self._level_bounds
                    if (
                        car_vec.x < -margin
                        or car_vec.y < -margin
                        or car_vec.x > bounds.width + margin
                        or car_vec.y > bounds.height + margin
                    ):
                        car_vec.x -= bounds.x
                        car_vec.y -= bounds.y

        self._gameplay_start_pos = pygame.Vector2(self.camera.x, self.camera.y)
        self._gameplay_target_pos = car_vec
        self._gameplay_start_zoom = float(self.camera.zoom)
        if target_zoom is None:
            self._gameplay_target_zoom = self._gameplay_start_zoom
        else:
            self._gameplay_target_zoom = self._clamp_zoom(float(target_zoom))

        dist = self._gameplay_start_pos.distance_to(self._gameplay_target_pos)
        move_duration = dist / self.PAN_SPEED if self.PAN_SPEED > 1e-6 else 0.0
        zoom_delta = abs(self._gameplay_target_zoom - self._gameplay_start_zoom)
        zoom_duration = zoom_delta / self.ZOOM_SPEED if self.ZOOM_SPEED > 1e-6 else 0.0
        self._gameplay_duration = max(move_duration, zoom_duration, 1e-6)
        self._gameplay_progress = 0.0

        start_angle = self.camera.rot_deg % 360.0
        self._gameplay_start_rot = start_angle
        self._gameplay_end_rot = 0.0 if start_angle <= 180.0 else 360.0

        self._gameplay_on_complete = on_complete
        self.state = "gameplay"

        if self._gameplay_duration <= 1e-6:
            if self._update_gameplay_motion(self._gameplay_duration):
                self.state = "idle"
                self._dispatch_gameplay_complete()
                return True
        return False
    
    def skip_to_gameplay(self, car_pos, target_zoom=None, on_complete=None):
        if car_pos is None:
            car_vec = pygame.Vector2(self.camera.x, self.camera.y)
        else:
            src_pos = getattr(car_pos, "pos", car_pos)
            car_vec = pygame.Vector2(src_pos)
            if self._level_bounds is not None:
                car_vec.x -= self._level_bounds.x
                car_vec.y -= self._level_bounds.y

        self.camera.x = car_vec.x
        self.camera.y = car_vec.y
        self.camera.zoom = self._clamp_zoom(self.camera.zoom if target_zoom is None else float(target_zoom))
        self.camera.rot_deg = 0.0

        self.state = "idle"
        self.timer = 0.0
        self._gameplay_progress = 1.0
        self._gameplay_duration = 0.0
        self._gameplay_on_complete = None

        if on_complete:
            on_complete()

        return True


    def _update_gameplay_motion(self, dt: float) -> bool:
        if self._gameplay_duration <= 1e-6:
            self.camera.x = self._gameplay_target_pos.x
            self.camera.y = self._gameplay_target_pos.y
            self.camera.zoom = self._gameplay_target_zoom
            self.camera.rot_deg = 0.0
            return True

        self._gameplay_progress = min(1.0, self._gameplay_progress + dt / self._gameplay_duration)
        t = self._gameplay_progress

        pos = self._gameplay_start_pos.lerp(self._gameplay_target_pos, t)
        self.camera.x, self.camera.y = pos.x, pos.y

        zoom = self._gameplay_start_zoom + (self._gameplay_target_zoom - self._gameplay_start_zoom) * t
        self.camera.zoom = self._clamp_zoom(zoom)

        angle = self._gameplay_start_rot + (self._gameplay_end_rot - self._gameplay_start_rot) * t
        angle %= 360.0
        if min(angle, 360.0 - angle) <= self.ROTATE_EPS:
            angle = 0.0
        self.camera.rot_deg = angle

        if t >= 0.999:
            self.camera.x = self._gameplay_target_pos.x
            self.camera.y = self._gameplay_target_pos.y
            self.camera.zoom = self._clamp_zoom(self._gameplay_target_zoom)
            self.camera.rot_deg = 0.0
            return True

        return False

    def _dispatch_gameplay_complete(self) -> None:
        if self._gameplay_on_complete:
            callback = self._gameplay_on_complete
            self._gameplay_on_complete = None
            callback()
