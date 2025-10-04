import pygame
from game.config.constants import FONT_FILE
from game.io.assets import load_font
from game.io.render import get_logical_size, end_frame, get_half_screen
from game.render.camera import CameraTour
from game.render.car import CarRenderer, car_from_dict, CarActor
from game.render.level_preview import LevelPreviewRenderer
from game.render.level_full import Camera, LevelFullRenderer
from game.ui.base_screen import BaseScreen
from game.ui.widgets.button import Button
from game.data.queries import fetch_levels

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
        self.camera_tour = None
        self.car = None
        self.car_renderer = CarRenderer()
        self.car_actor = None
        self.hide_ui = False

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
        self.camera = Camera()
        self.camera_tour = CameraTour(self.full_renderer, self.camera)
        self.car = car_from_dict(ctx.pop("selected_car"), ctx)
        self.car_actor = CarActor(self.car_renderer, self.car)
        if self.levels:
            self._focus_camera_on_selected_level()
            self.full_renderer.render_to(pygame.Surface((1, 1)), self.levels[self.selected_level], self.camera, actors=[self.car_actor])

    def _continue(self, ctx):
        if self.levels:
            ctx["selected_level_id"] = self.selected_level
            ctx["level_data"] = self.levels[self.selected_level]
            self.hide_ui = True
            target_pos = self.car.transform.pos if self.car else None

            def _finish_transition():
                ctx["gameplay"] = {
                    "camera": self.camera,
                    "level_data": self.levels[self.selected_level],
                    "car": self.car,
                }
                if self.continue_action:
                    self.continue_action(ctx)

            self.camera_tour.begin_gameplay(target_pos, 1.5, on_complete=_finish_transition)

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
                    self.full_renderer.render_to(pygame.Surface((1, 1)), self.levels[self.selected_level], self.camera, actors=[self.car_actor])

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
            self.full_renderer.render_to(surf, self.levels[self.selected_level], camera=self.camera, actors=[self.car_actor] if self.car_actor else None)
            if not self.hide_ui:
                line = self.font.render(self.levels[self.selected_level]["name"], True, (255, 255, 255))
                surf.blit(line, line.get_rect(center=(half_W, 190)))

        if not self.hide_ui:
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