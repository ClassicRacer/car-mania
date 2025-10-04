import pygame
from game.core.engine.state import Screen
from game.io.render import resize_physical
from game.ui.widgets.button import BackControl, poll_actions_cached

class BaseScreen(Screen):
    def __init__(self, back_action=None):
        self.back_action = back_action
        self.back = BackControl() if back_action else None
        self.seq = 0
        self.font = None
        self.title_font = None

    def enter(self, ctx):
        self.seq = ctx["screen_seq"]
        self.font = ctx["fonts"]["ui"]
        self.title_font = ctx["fonts"]["title"]
        if self.back:
            self.back.enter(ctx)

    def poll(self, ctx):
        return self.back.poll(ctx) if self.back else poll_actions_cached(ctx)
    
    def draw_back(self, ctx, surf):
        if self.back and "back_button_draw" in ctx:
            mp = ctx["get_mouse_pos"]()
            ctx["back_button_draw"](surf, mp, self.back.rect)

    def handle_back(self, ctx, actions):
        if self.back and self.back.update(ctx, actions):
            self.back_action(ctx)
            return True
        return False
    
    def on_resize(self, ctx, size):
        resize_physical(size)

    def step(self, ctx):
        actions = self.poll(ctx)
        for name, phase, payload in actions:
            if name == "quit":
                return None
            if name == "window_resized" and phase == "change":
                self.on_resize(ctx, payload)
        return actions