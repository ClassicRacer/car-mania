import pygame
from game.io.render import get_half_screen, end_frame
from game.ui.gameplay import Gameplay
from game.ui.level_select import LevelSelectScreen
from game.ui.widgets.button import Button, layout_column, poll_actions_cached
from game.config.constants import FONT_FILE, ICON_FONT_FILE
from game.ui.base_screen import BaseScreen
from game.ui.car_select import CarSelectScreen

class MenuScreen(BaseScreen):
    def __init__(self, title, items, back_action=None):
        super().__init__(back_action)
        self.title = title
        self.items = items
        self.buttons = []

    def enter(self, ctx):
        super().enter(ctx)
        cx, cy = get_half_screen()
        bw, bh, s = 300, 64, 20
        self.buttons = [Button((0,0,bw,bh), label, self.font, (255,255,255), (30,30,30), (50,50,50), callback=cb) for (label, cb) in self.items]
        layout_column(cx, cy + (bh*len(self.items) + s*(len(self.items)-1))//10, (bw,bh), s, self.buttons)
        for b in self.buttons:
            b.enter(ctx)

    def on_resize(self, ctx, size):
        super().on_resize(ctx, size)
        cx, cy = get_half_screen()
        bw, bh, s = 300, 64, 20
        layout_column(cx, cy + (bh*len(self.buttons) + s*(len(self.buttons)-1))//10, (bw,bh), s, self.buttons)

    def update(self, ctx, dt):
        actions = self.step(ctx)
        if actions is None:
            return False
        for b in self.buttons:
            if b.update(ctx, actions):
                if b.callback:
                    b.callback(ctx)
        if self.handle_back(ctx, actions):
            return True
        return True

    def render(self, ctx):
        surf = ctx["window"]
        surf.fill((10,10,10))
        t = self.title_font.render(self.title, True, (255,255,255))
        surf.blit(t, t.get_rect(center=(get_half_screen()[0], 120)))
        mp = ctx["get_mouse_pos"]()
        self.draw_back(ctx, surf)
        for b in self.buttons:
            b.draw(surf, mp)
        end_frame()

def main_menu(game):
    return MenuScreen("Car Mania", [
        ("Play",     go_car_select),
        ("Create",   go_create_menu),
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

def go_main_menu(ctx):
    _debug_ctx(ctx)
    g = ctx["game"]
    g.set(main_menu(g))

def go_create_menu(ctx):
    _debug_ctx(ctx)
    g = ctx["game"]
    g.set(create_menu(g))

def on_car_selected(ctx, car):
    _debug_ctx(ctx)
    g = ctx["game"]
    g.set(LevelSelectScreen(back_action=go_car_select, continue_action=on_level_selected))

def go_car_select(ctx):
    _debug_ctx(ctx)
    g = ctx["game"]
    g.set(CarSelectScreen(back_action=go_main_menu, continue_action=on_car_selected))

def on_level_selected(ctx):
    _debug_ctx(ctx)
    g = ctx["game"]
    g.set(Gameplay(back_action=go_main_menu))

def _debug_ctx(ctx):
    import inspect
    print("*"*20)
    outer_func = inspect.currentframe().f_back.f_code.co_name
    print(f"{outer_func}:\n\n{ctx.keys()}")