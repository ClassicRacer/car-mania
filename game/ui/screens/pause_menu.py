import pygame
from game.io.render import end_frame
from game.ui.screens.base_screen import BaseScreen
from game.ui.utils import draw_text
from game.ui.widgets.button import Button, layout_column


class PauseMenu(BaseScreen):
    LAYER_NAME = "pause_menu"

    def __init__(self, items, back_action=None, panel_size=(700, 500)):
        super().__init__(back_action)
        self.items = items
        self.buttons = []
        self.panel_size = panel_size
        self._panel_rect = pygame.Rect(0, 0, *panel_size)
        self._bg_snapshot = None

    def enter(self, ctx):
        surf = ctx["window"]
        try:
            self._bg_snapshot = surf.copy()
        except Exception:
            self._bg_snapshot = None
        super().enter(ctx)
        bw, bh, spacing = 300, 64, 16
        self.buttons = [
            Button((0, 0, bw, bh), label, self.font,
                   (255, 255, 255), (30, 30, 30), (50, 50, 50),
                   callback=cb)
            for (label, cb) in self.items
        ]
        self._relayout(surf.get_size(), bw, bh, spacing)
        for b in self.buttons:
            b.enter(ctx)
    
    def on_resize(self, ctx, size):
        super().on_resize(ctx, size)
        if self.buttons:
            bw, bh, spacing = self.buttons[0].rect.w, self.buttons[0].rect.h, 16
            self._relayout(size, bw, bh, spacing)

    def _relayout(self, surface_size, bw, bh, spacing):
        sw, sh = surface_size
        cx, cy = sw // 2, sh // 2
        self._panel_rect.size = self.panel_size
        self._panel_rect.center = (cx, cy)
        top_y = self._panel_rect.y + 240
        layout_column(self._panel_rect.centerx, top_y, (bw, bh), spacing, self.buttons)

    def update(self, ctx, dt):
        actions = self.step(ctx)
        if actions is None:
            return False
        for b in self.buttons:
            if b.update(ctx, actions) and b.callback:
                b.callback(ctx)
        if self.handle_back(ctx, actions):
            return True
        return True
    
    def render(self, ctx):
        surf = ctx["window"]
        if self._bg_snapshot:
            surf.blit(self._bg_snapshot, (0, 0))
        overlay = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surf.blit(overlay, (0, 0))
        pygame.draw.rect(surf, (24, 24, 24), self._panel_rect, border_radius=16)
        pygame.draw.rect(surf, (255, 255, 255), self._panel_rect, width=2, border_radius=16)
        title_pos = (self._panel_rect.centerx, self._panel_rect.y + 60)
        font_pos = (self._panel_rect.centerx, self._panel_rect.y + 140)
        draw_text(surf, "Game Paused", self.title_font, (255, 255, 255), title_pos, centered=True)
        draw_text(surf, ctx["level_data"]["name"], self.font, (255, 255, 255), font_pos, centered=True)
        mp = ctx["get_mouse_pos"]()
        for b in self.buttons:
            b.draw(surf, mp)
        end_frame()
    