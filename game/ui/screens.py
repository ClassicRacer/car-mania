import pygame
from game.io.render import get_half_screen, get_mouse_pos_logical, end_frame
from game.io.input import poll_actions
from game.io.render import resize_physical
from game.io.assets import load_font
from game.ui.widgets import Button
from game.config.constants import FONT_FILE, ICON_FONT_FILE
from game.core.state import Screen

class MenuScreen(Screen):
    def __init__(self, title, items, back_action=None):
        self.title = title
        self.items = items
        self.back_action = back_action
        self.buttons = []
        self.back_button = None
        self.font = None
        self.title_font = None
        self.icon_font = None
        self.prev_left = False
        self.clicked = False
        self.down = False
        self.down_button = None
        self.down_on_back = False

    def enter(self, ctx):
        self.font = load_font(FONT_FILE, 36)
        self.title_font = load_font(FONT_FILE, 100)
        self.icon_font = load_font(ICON_FONT_FILE, 36)
        self.seq = ctx["screen_seq"]
        cx, cy = get_half_screen()
        bw, bh, s = 300, 64, 20
        y0 = cy + (bh*len(self.items) + s*(len(self.items)-1))/10
        self.buttons = [
            Button((cx-bw//2, int(y0+i*(bh+s)), bw, bh),
                   label, self.font,
                   (255,255,255), (30,30,30), (50,50,50))
            for i,(label,_) in enumerate(self.items)
        ]
        self.back_button = Button((20, 20, 140, 50), "", self.font,
                                  (255,255,255), (30,30,30), (50,50,50)) if self.back_action else None
        self.down = False
        self.down_button = None
        self.down_on_back = False

    def _hit_index(self, pos):
        for i, b in enumerate(self.buttons):
            if b.rect.collidepoint(pos):
                return i
        return None

    def update(self, ctx, dt):
        for name, phase, payload in poll_actions():
            if name == "quit":
                return False
            if name == "window_resized" and phase == "change":
                resize_physical(payload)
            if name == "escape" and phase == "press" and self.back_action:
                self.back_action(ctx)
            if name == "mouse_down" and phase == "press" and payload == 1 and not self.down:
                mp = get_mouse_pos_logical()
                self.down = True
                self.down_on_back = False
                # record if press began on back button; otherwise track which menu button
                if self.back_button and self.back_button.rect.collidepoint(mp):
                    self.down_on_back = True
                    self.down_button = None
                else:
                    self.down_button = self._hit_index(mp)
            if name == "mouse_up" and phase == "release" and payload == 1:
                mp = get_mouse_pos_logical()
                if self.down and ctx["screen_seq"] == self.seq:
                    if self.back_button and self.down_on_back and self.back_button.rect.collidepoint(mp):
                        self.back_action(ctx)
                    else:
                        up_idx = self._hit_index(mp)
                        if up_idx is not None and up_idx == self.down_button:
                            cb = self.items[up_idx][1]
                            if cb:
                                cb(ctx)
                self.down = False
                self.down_button = None
                self.down_on_back = False
        return True

    def render(self, ctx):
        surf = ctx["window"]
        surf.fill((10,10,10))
        title_surf = self.title_font.render(self.title, True, (255,255,255))
        surf.blit(title_surf, title_surf.get_rect(center=(get_half_screen()[0], 120)))
        mp = get_mouse_pos_logical()
        if self.back_button:
            self.back_button.draw(surf, mp)
            r = self.back_button.rect

            arrow = self.icon_font.render("←", True, (255, 255, 255))
            txt   = self.font.render("Back", True, (255, 255, 255))

            spacing = 8
            total_w = arrow.get_width() + spacing + txt.get_width()
            x = r.x + (r.w - total_w) // 2

            arrow_y = r.y + (r.h - arrow.get_height()) // 2
            txt_y   = r.y + (r.h - txt.get_height()) // 2

            surf.blit(arrow, (x, arrow_y))
            surf.blit(txt, (x + arrow.get_width() + spacing, txt_y))
        for b in self.buttons:
            b.draw(surf, mp)
        end_frame()