import pygame
from game.io.render import get_half_screen, get_mouse_pos_logical, end_frame
from game.io.input import poll_actions
from game.io.render import resize_physical
from game.io.assets import load_font
from game.ui.widgets import Button
from game.config.constants import FONT_FILE
from game.core.state import Screen

class MenuScreen(Screen):
    def __init__(self, title, items):
        self.title = title
        self.items = items
        self.buttons = []
        self.font = None
        self.title_font = None
        self.prev_left = False
        self.clicked = False

    def enter(self, ctx):
        self.font = load_font(FONT_FILE, 36)
        self.title_font = load_font(FONT_FILE, 100)
        cx, cy = get_half_screen()
        bw, bh, s = 300, 64, 20
        y0 = cy - (bh*len(self.items) + s*(len(self.items)-1))/2
        self.buttons = [
            Button((cx-bw//2, int(y0+i*(bh+s)), bw, bh),
                   label, self.font,
                   (255,255,255), (30,30,30), (50,50,50))
            for i,(label,_) in enumerate(self.items)
        ]

    def update(self, ctx, dt):
        self.clicked = False
        for name, phase, payload in poll_actions():
            if name == "quit":
                return False
            if name == "window_resized" and phase == "change":
                resize_physical(payload)
        mp = get_mouse_pos_logical()
        left = pygame.mouse.get_pressed()[0] == 1
        if left and not self.prev_left:
            self.clicked = True
        self.prev_left = left
        for btn,(label,callback) in zip(self.buttons,self.items):
            if btn.clicked(mp, self.clicked) and callback:
                callback(ctx)
        return True

    def render(self, ctx):
        surf = ctx["window"]
        surf.fill((10,10,10))
        title_surf = self.title_font.render(self.title, True, (255,255,255))
        surf.blit(title_surf, title_surf.get_rect(center=(get_half_screen()[0], 120)))
        mp = get_mouse_pos_logical()
        for b in self.buttons:
            b.draw(surf, mp)
        end_frame()