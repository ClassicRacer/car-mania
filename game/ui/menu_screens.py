import pygame
from game.io.render import get_half_screen, end_frame
from game.io.render import resize_physical
from game.ui.widgets import Button, BackControl, poll_actions_cached
from game.config.constants import FONT_FILE, ICON_FONT_FILE
from game.core.state import Screen
from game.ui.car_select import CarSelectScreen

class MenuScreen(Screen):
    def __init__(self, title, items, back_action=None):
        self.title = title
        self.items = items
        self.back_action = back_action
        self.buttons = []
        self.back = BackControl() if back_action else None
        self.font = None
        self.title_font = None
        self.seq = 0
        self.down = False
        self.down_button = None

    def enter(self, ctx):
        self.font = ctx["fonts"]["ui"]
        self.title_font = ctx["fonts"]["title"]
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
        if self.back:
            self.back.enter(ctx)
        self.down = False
        self.down_button = None

    def _hit_index(self, pos):
        for i, b in enumerate(self.buttons):
            if b.rect.collidepoint(pos):
                return i
        return None

    def update(self, ctx, dt):
        actions = self.back.poll(ctx) if self.back else poll_actions_cached(ctx)
        for name, phase, payload in actions:
            if name == "quit":
                return False
            if name == "window_resized" and phase == "change":
                resize_physical(payload)
            if name == "mouse_down" and phase == "press" and payload == 1 and not self.down:
                mp = ctx["get_mouse_pos"]()
                self.down = True
                self.down_button = self._hit_index(mp)
            if name == "mouse_up" and phase == "release" and payload == 1:
                mp = ctx["get_mouse_pos"]()
                if self.down and ctx["screen_seq"] == self.seq:
                    up_idx = self._hit_index(mp)
                    if up_idx is not None and up_idx == self.down_button:
                        cb = self.items[up_idx][1]
                        if cb:
                            cb(ctx)
                self.down = False
                self.down_button = None
        if self.back and self.back.update(ctx, actions):
            self.back_action(ctx)
        return True

    def render(self, ctx):
        surf = ctx["window"]
        surf.fill((10,10,10))
        t = self.title_font.render(self.title, True, (255,255,255))
        surf.blit(t, t.get_rect(center=(get_half_screen()[0], 120)))
        mp = ctx["get_mouse_pos"]()
        if self.back and "back_button_draw" in ctx:
            ctx["back_button_draw"](surf, mp, self.back.rect)
        for b in self.buttons:
            b.draw(surf, mp)
        end_frame()

def main_menu(game):
    return MenuScreen("Car Mania", [
        ("Play",     lambda ctx: ctx["game"].set(CarSelectScreen(back_action=lambda ctx: ctx["game"].set(main_menu(game))))),
        ("Create",   lambda ctx: ctx["game"].set(create_menu(game))),
        ("Options",  None),
        ("Quit",     lambda ctx: ctx.update({"quit": True})),
    ])

def create_menu(game):
    return MenuScreen("Car Mania", [
        ("Car Creator", lambda ctx: ctx["game"].set(car_creator_menu(game))),
        ("Level Creator", lambda ctx: ctx["game"].set(level_creator_menu(game))),
    ], back_action=lambda ctx: ctx["game"].set(main_menu(game)))

def car_creator_menu(game):
    return MenuScreen("Car Creator Menu", [
        ("Create Car", None),
        ("Edit Car", None),
        ("Tutorial", None),
    ], back_action=lambda ctx: ctx["game"].set(create_menu(game)))

def level_creator_menu(game):
    return MenuScreen("Level Creator Menu", [
        ("Create Level", None),
        ("Edit Level", None),
        ("Tutorial", None),
    ], back_action=lambda ctx: ctx["game"].set(create_menu(game)))