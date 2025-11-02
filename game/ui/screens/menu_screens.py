from game.io.render import get_half_screen, end_frame
from game.ui.screens.credits import Credits
from game.ui.screens.gameplay import Gameplay
from game.ui.screens.level_select import LevelSelectScreen
from game.ui.screens.pause_menu import PauseMenu
from game.ui.utils import draw_text
from game.ui.widgets.button import Button, layout_column
from game.ui.screens.base_screen import BaseScreen
from game.ui.screens.car_select import CarSelectScreen

class MenuScreen(BaseScreen):
    LAYER_NAME = "menu_screen"

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
        draw_text(surf, self.title, self.title_font, (255, 255, 255), (get_half_screen()[0], 120), centered=True)
        mp = ctx["get_mouse_pos"]()
        self.draw_back(ctx, surf)
        for b in self.buttons:
            b.draw(surf, mp)
        end_frame()

def main_menu(game):
    return MenuScreen("Car Mania", [
        ("Play",     go_car_select),
        # ("Create",   go_create_menu),
        # ("Options",  None),
        ("Credits", go_credits),
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
    ctx.pop("gameplay_screen", None)
    g = ctx["game"]
    g.set(main_menu(g))

def go_create_menu(ctx):
    g = ctx["game"]
    g.set(create_menu(g))

def go_credits(ctx):
    g = ctx["game"]
    g.set(Credits(back_action=go_main_menu, continue_action=go_main_menu))

def go_level_select(ctx):
    g = ctx["game"]
    g.set(LevelSelectScreen(back_action=go_car_select, continue_action=go_gameplay))

def go_car_select(ctx):
    g = ctx["game"]
    g.set(CarSelectScreen(back_action=go_main_menu, continue_action=go_level_select))

def go_gameplay(ctx):
    g = ctx["game"]
    if "gameplay_screen" not in ctx:
        ctx["gameplay_screen"] = Gameplay(back_action=go_pause_menu, continue_action=go_main_menu)
    g.set(ctx["gameplay_screen"])

def go_pause_menu(ctx):
    g = ctx["game"]
    current_gameplay = g.current

    def resume(_ctx):
        _ctx["game"].set(current_gameplay)

    g.set(PauseMenu([
        ("Resume Game", resume),
        ("Quit Game", go_main_menu),
    ], back_action=resume))