import math
import pygame
from game.config.constants import FONT_FILE
from game.io.assets import load_font
from game.io.render import get_logical_size, end_frame, get_half_screen
from game.render.level_preview import LevelPreviewRenderer, parse_level_code
from game.render.level_full import Camera2D, LevelFullRenderer
from game.ui.base_screen import BaseScreen
from game.ui.widgets.button import BackControl, Button
from game.data.queries import fetch_levels


class CameraTour:
    WAIT_DURATION = 5.0
    PAN_SPEED = 640.0
    ZOOM_SPEED = 1.6
    MIN_ZOOM = 0.05
    MAX_ZOOM = 5.0
    POSITION_EPS = 1.0
    ZOOM_EPS = 0.02
    ZOOM_IN_FACTOR = 1.8

    def __init__(self, renderer: LevelFullRenderer, camera: Camera2D):
        self.renderer = renderer
        self.camera = camera
        self.state = "idle"
        self.timer = 0.0
        self.gate_points = []
        self.level_center = pygame.Vector2(0.0, 0.0)
        self.origin = pygame.Vector2(0.0, 0.0)
        self.index = 0

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

        _, _, gates, _ = parse_level_code(level_row.get("code", ""))
        gate_image = self.renderer.pieces.get("gate") if hasattr(self.renderer, "pieces") else None
        if gate_image:
            gx, gy = gate_image.get_size()
            gate_offset = pygame.Vector2(gx * 0.5, gy * 0.5)
        else:
            gate_offset = pygame.Vector2(0.0, 0.0)

        self.gate_points = []
        for order, x, y, _ in sorted(gates, key=lambda g: g[0]):
            px = (x - bounds.x) + gate_offset.x
            py = (y - bounds.y) + gate_offset.y
            self.gate_points.append(pygame.Vector2(px, py))

        self.state = "wait"
        self.timer = self.WAIT_DURATION
        self.index = 0
        self.camera.rot_deg = 0.0
        self.camera.zoom = 1.0

    def update(self, dt: float):
        if self.state == "idle":
            return

        if self.state == "wait":
            self.timer -= dt
            if self.timer <= 0.0:
                self.state = "origin"
            return

        if self.state == "origin":
            pos_done = self._approach_position(self.origin, dt)
            zoom_done = self._approach_zoom(self.ZOOM_IN_FACTOR, dt)
            if pos_done and zoom_done:
                self.index = 0
                self.state = "gates" if self.gate_points else "zoom_out"
            return

        if self.state == "gates":
            if not self.gate_points:
                self.state = "zoom_out"
                return
            target = self.gate_points[self.index]
            reached = self._approach_position(target, dt)
            self._approach_zoom(self.ZOOM_IN_FACTOR, dt)
            if reached:
                self.index += 1
                if self.index >= len(self.gate_points):
                    self.state = "zoom_out"
            return

        if self.state == "zoom_out":
            pos_done = self._approach_position(self.level_center, dt)
            zoom_done = self._approach_zoom(1.0, dt)
            if pos_done and zoom_done:
                self.state = "wait"
                self.timer = self.WAIT_DURATION
                self.index = 0

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

class LevelSelectScreen(BaseScreen):
    def __init__(self, back_action=None, continue_action=None, thumb_size=(150, 150), margin=24):
        super().__init__(back_action)
        self.card_font = None
        self.selected_level = 0
        self.levels = []
        self.thumbs = []
        self.full_renderer = None
        self.continue_button = None
        self.continue_action = continue_action
        self.thumb_size = thumb_size
        self.camera = None
        self.margin = margin
        self.rotation = 0
        self.camera_tour = None

    def enter(self, ctx):
        super().enter(ctx)
        self.card_font = load_font(FONT_FILE, 20)
        self.levels = fetch_levels(ctx["db"], ctx["profile_id"])
        renderer = LevelPreviewRenderer(ctx["pieces"], target_size=(360, 220))
        self.full_renderer = LevelFullRenderer(ctx["pieces"])
        self.thumbs = [renderer.render(row) for row in self.levels]
        self.continue_button = Button((1500,513,300,64), "Continue", self.font, (255,255,255), (30,30,30), (50,50,50), callback=lambda c: self._continue(c))
        self.continue_button.enter(ctx)
        if ctx.get("selected_level_id", -1) == -1:
            import random
            self.selected_level = random.randint(0, len(self.levels)-1) if self.levels else 0
        else:
            self.selected_level = ctx["selected_level_id"]
        self.camera = Camera2D()
        self.camera_tour = CameraTour(self.full_renderer, self.camera)
        if self.levels:
            self._focus_camera_on_selected_level()
            self.full_renderer.render_to(pygame.Surface((1, 1)), self.levels[self.selected_level], self.camera)

    def _continue(self, ctx):
        if self.levels:
            ctx["selected_level_id"] = self.selected_level
            if self.continue_action:
                self.continue_action(ctx, self.levels[self.selected_level])


    def update(self, ctx, dt):
        actions = self.step(ctx)
        if actions is None:
            return False
        mp = ctx["get_mouse_pos"]()
        for name, phase, payload in actions:
            if name == "right" and phase == "press":
                self.selected_level = (self.selected_level + 1) % len(self.levels)
                self._focus_camera_on_selected_level()
            elif name == "left" and phase == "press":
                self.selected_level = (self.selected_level - 1) % len(self.levels)
                self._focus_camera_on_selected_level()
            elif name == "enter" and phase == "press":
                self._continue(ctx)
            elif name == "window_resized" and phase == "change":
                if self.levels:
                    self.full_renderer.render_to(pygame.Surface((1, 1)), self.levels[self.selected_level], camera=self.camera)

        if self.camera_tour and self.levels:
            self.camera_tour.update(dt)

        if self.continue_button.update(ctx, actions):
            self._continue(ctx)
        if self.handle_back(ctx, actions):
            return True
        return True

    def render(self, ctx):
        surf = ctx["window"]
        surf.fill((20, 20, 20))

        W, H = get_logical_size()
        half_W, half_H = get_half_screen()

        if self.levels:
            self.full_renderer.render_to(surf, self.levels[self.selected_level], camera=self.camera)
            line = self.font.render(self.levels[self.selected_level]["name"], True, (255, 255, 255))
            surf.blit(line, line.get_rect(center=(half_W, 190)))

        title = self.title_font.render("Select Level", True, (255, 255, 255))
        surf.blit(title, title.get_rect(center=(half_W, 100)))

        N = max(1, len(self.levels))
        pad = self.margin
        slot_w = (W - pad*2) // N
        slot_h = self.thumb_size[1]
        y = H - 150
        for idx, (row, thumb) in enumerate(zip(self.levels, self.thumbs)):
            img = self._scale_image(thumb, self.thumb_size)
            name = self.card_font.render(row["name"], True, (255, 255, 255))
            rect = pygame.Rect(0, 0, slot_w, slot_h)
            rect.center = (pad + slot_w*idx + slot_w//2, y)
            if idx == self.selected_level:
                overlay = pygame.Surface((rect.w + 20, rect.h + 50), pygame.SRCALPHA)
                pygame.draw.rect(overlay, (50, 50, 50, 180), overlay.get_rect(), border_radius=8)
                surf.blit(overlay, (rect.x - 10, rect.y - 10))
            surf.blit(img, img.get_rect(center=rect.center))
            surf.blit(name, name.get_rect(center=(rect.centerx, rect.bottom + 20)))

        pygame.draw.line(surf, (255, 0, 0), (half_W - 10, half_H), (half_W + 10, half_H), 2)
        pygame.draw.line(surf, (255, 0, 0), (half_W, half_H - 10), (half_W, half_H + 10), 2)
        
        mp = ctx["get_mouse_pos"]()
        self.continue_button.draw(surf, mp)
        self.draw_back(ctx, surf)
        end_frame()

    def _scale_image(self, img : pygame.Surface, tile_size):
        w, h = img.get_size()
        tw, th = tile_size
        scale_ratio = min(tw/w, th/h)
        new_size = (int(w*scale_ratio), int(h*scale_ratio))
        return pygame.transform.scale(img, new_size)

    def _focus_camera_on_selected_level(self):
        if not self.levels or not self.camera:
            return
        row = self.levels[self.selected_level]
        self.full_renderer.focus_camera(self.camera, row)
        if self.camera_tour:
            self.camera_tour.load_level(row)
