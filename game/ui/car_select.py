import pygame
from game.core.state import Screen
from game.io.render import get_mouse_pos_logical, end_frame, resize_physical, get_half_screen
from game.ui.widgets import BackControl

class CarSelectScreen(Screen):
    def __init__(self, on_back=None, on_select=None):
        self.on_back = on_back
        self.on_select = on_select
        self.seq = 0
        self.font = None
        self.back = BackControl() if on_back else None
        self.title_font = None
        self.back_rect = pygame.Rect(20, 20, 160, 56)
        self.down = False
        self.down_on_back = False

    def enter(self, ctx):
        # Load fonts from context
        self.seq = ctx["screen_seq"]
        self.font = ctx["fonts"]["ui"]
        self.title_font = ctx["fonts"]["title"]
        self.down = False
        self.down_on_back = False

    def update(self, ctx, dt):
        for name, phase, payload in ctx["poll_actions"]():
            if name == "quit":
                return False
            if name == "window_resized" and phase == "change":
                resize_physical(payload)
            if name == "escape" and phase == "press":
                if self.on_back:
                    self.on_back(ctx)
            if name == "mouse_down" and phase == "press" and payload == 1 and not self.down:
                mp = get_mouse_pos_logical()
                self.down = True
                self.down_on_back = self.back_rect.collidepoint(mp)
            if name == "mouse_up" and phase == "release" and payload == 1:
                mp = get_mouse_pos_logical()
                if self.down and ctx["screen_seq"] == self.seq:
                    if self.down_on_back and self.back_rect.collidepoint(mp):
                        if self.on_back:
                            self.on_back(ctx)
                    # later: detect card clicks here
                self.down = False
                self.down_on_back = False
        return True

    def render(self, ctx):
        surf = ctx["window"]
        surf.fill((20, 20, 20))
        # Title text
        title = self.title_font.render("Select Car", True, (255, 255, 255))
        surf.blit(title, title.get_rect(center=(get_half_screen()[0], 100)))
        # Back button (placeholder)
        mp = get_mouse_pos_logical()
        if self.back and "back_button_draw" in ctx:
            ctx["back_button_draw"](surf, mp, self.back.rect)
        end_frame()