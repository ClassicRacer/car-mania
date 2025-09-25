import pygame

class Button:
    def __init__(self, rect, text, font, fg, bg, hover):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.fg = fg
        self.bg = bg
        self.hover = hover
        self._surf = None
        self._pos = None

    def draw(self, surface, mouse_pos):
        m = self.rect.collidepoint(mouse_pos)
        color = self.hover if m else self.bg
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        if not self._surf:
            self._surf = self.font.render(self.text, True, self.fg)
            self._pos = self._surf.get_rect(center=self.rect.center)
        surface.blit(self._surf, self._pos)
        return m
    
    def clicked(self, mouse_pos, mouse_clicked):
        return self.rect.collidepoint(mouse_pos) and mouse_clicked
    
import pygame

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
        import pygame
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