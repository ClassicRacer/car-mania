import math
import pygame
from game.config.constants import FONT_FILE
from game.io.assets import load_font
from game.io.render import get_logical_size, end_frame, get_half_screen
from game.render.level_preview import LevelPreviewRenderer
from game.render.level_full import Camera2D, LevelFullRenderer
from game.ui.base_screen import BaseScreen
from game.ui.widgets.button import BackControl, Button
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
        self.rotation = 0

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
        if self.levels:
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
                pass
                # if self.levels:
                #     self.selected_level = (self.selected_level + 1) % len(self.levels)
                #     # Re-fit camera when level changes
                #     self.full_renderer.render_to(pygame.Surface((1, 1)), self.levels[self.selected_level], camera=self.camera)
            elif name == "left" and phase == "press":
                pass
                # if self.levels:
                #     self.selected_level = (self.selected_level - 1) % len(self.levels)
                #     self.full_renderer.render_to(pygame.Surface((1, 1)), self.levels[self.selected_level], camera=self.camera)
            elif name == "enter" and phase == "press":
                # self._continue(ctx)
                self.selected_level = (self.selected_level + 1) % len(self.levels)
            elif name == "window_resized" and phase == "change":
                if self.levels:
                    self.full_renderer.render_to(pygame.Surface((1, 1)), self.levels[self.selected_level], camera=self.camera)
        if self.camera:
            PAN_SPEED  = 600.0
            ZOOM_RATE  = 1.5
            ROT_SPEED  = 90.0
            MIN_ZOOM   = 0.05
            MAX_ZOOM   = 5.0

            pressed = pygame.key.get_pressed()
            if pressed[pygame.K_UP]:
                self.camera.x += PAN_SPEED * dt * math.sin(math.radians(self.camera.rot_deg))
                self.camera.y -= PAN_SPEED * dt * math.cos(math.radians(self.camera.rot_deg))
            if pressed[pygame.K_DOWN]:
                self.camera.x -= PAN_SPEED * dt * math.sin(math.radians(self.camera.rot_deg))
                self.camera.y += PAN_SPEED * dt * math.cos(math.radians(self.camera.rot_deg))
            if pressed[pygame.K_LEFT]:
                self.camera.rot_deg -= ROT_SPEED * dt
            if pressed[pygame.K_RIGHT]:
                self.camera.rot_deg += ROT_SPEED * dt

            if pressed[pygame.K_MINUS]:
                self.camera.zoom /= (1.0 + ZOOM_RATE * dt)
            if pressed[pygame.K_EQUALS]:
                self.camera.zoom *= (1.0 + ZOOM_RATE * dt)


            self.camera.zoom = max(MIN_ZOOM, min(MAX_ZOOM, self.camera.zoom))
            self.camera.rot_deg %= 360.0

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
            line = self.font.render(f"{self.levels[self.selected_level]["name"]}", True, (255,255,255))
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