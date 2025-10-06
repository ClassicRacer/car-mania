import pygame
from game.ui.utils import draw_text

class Button:
    def __init__(self, rect, text, font, fg, bg, hover, callback=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.fg = fg
        self.bg = bg
        self.hover = hover
        self.callback = callback
        self._surf = None
        self._pos = None
        self._down = False
        self._seq = 0

    def set_rect(self, rect):
        self.rect = pygame.Rect(rect)
        self._pos = None

    def enter(self, ctx):
        self._seq = ctx["screen_seq"]
        self._down = False

    def update(self, ctx, actions):
        for name, phase, payload in actions:
            if name == "mouse_down" and phase == "press" and payload == 1 and not self._down:
                mp = ctx["get_mouse_pos"]()
                if self.rect.collidepoint(mp):
                    self._down = True
            if name == "mouse_up" and phase == "release" and payload == 1:
                mp = ctx["get_mouse_pos"]()
                if self._down and ctx["screen_seq"] == self._seq and self.rect.collidepoint(mp):
                    self._down = False
                    return True
                self._down = False
        return False

    def draw(self, surface, mouse_pos):
        m = self.rect.collidepoint(mouse_pos)
        color = self.hover if m else self.bg
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        draw_text(surface, self.text, self.font, self.fg, self.rect.center, centered=True)
    
    def clicked(self, mouse_pos, mouse_clicked):
        return self.rect.collidepoint(mouse_pos) and mouse_clicked
    
def layout_column(center_x, top_y, size, spacing, buttons):
    w, h = size
    for i, b in enumerate(buttons):
        x = center_x - w // 2
        y = int(top_y + i * (h + spacing))
        b.set_rect((x, y, w, h))

def poll_actions_cached(ctx):
    a = ctx.get("_actions_cache")
    if a is None:
        a = list(ctx["poll_actions"]())
        ctx["_actions_cache"] = a
    return a

class BackControl:
    def __init__(self, rect=(20,20,140,50)):
        self.rect = pygame.Rect(rect)
        self.seq = 0
        self.down = False
    def enter(self, ctx):
        self.seq = ctx["screen_seq"]
        self.down = False
    def poll(self, ctx):
        return poll_actions_cached(ctx)
    def update(self, ctx, actions):
        triggered = False
        for name, phase, payload in actions:
            if name == "escape" and phase == "press":
                return True
            if name == "mouse_down" and phase == "press" and payload == 1 and not self.down:
                mp = ctx["get_mouse_pos"]()
                if self.rect.collidepoint(mp):
                    self.down = True
            if name == "mouse_up" and phase == "release" and payload == 1:
                mp = ctx["get_mouse_pos"]()
                if self.down and ctx["screen_seq"] == self.seq and self.rect.collidepoint(mp):
                    triggered = True
                self.down = False
        return triggered

def make_back_draw(icon_font, text_font):
    def draw(surf, mp, rect, pressed=False):
        hovering = rect.collidepoint(mp)
        bg = (30,30,30)
        if hovering and not pressed:
            bg = (50,50,50)
        if pressed:
            bg = (70,70,70)
        pygame.draw.rect(surf, bg, rect, border_radius=8)
        arrow = icon_font.render("←", True, (255,255,255))
        txt = text_font.render("Back", True, (255,255,255))
        spacing = 8
        total_w = arrow.get_width() + spacing + txt.get_width()
        x = rect.x + (rect.w - total_w) // 2
        ay = rect.y + (rect.h - arrow.get_height()) // 2
        ty = rect.y + (rect.h - txt.get_height()) // 2
        surf.blit(arrow, (x, ay))
        surf.blit(txt, (x + arrow.get_width() + spacing, ty))
    return draw