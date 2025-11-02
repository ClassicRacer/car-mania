from typing import ClassVar
from game.core.engine.state import Screen
from game.io.render import resize_physical
from game.ui.widgets.button import BackControl, poll_actions_cached
from game.io.input import push_bindings, pop_bindings

class BaseScreen(Screen):
    LAYER_NAME = ClassVar[str]

    def __init_subclass__(cls, **kw):
        super().__init_subclass__(**kw)
        if 'LAYER_NAME' not in cls.__dict__:
            raise TypeError(f"{cls.__name__} must define LAYER_NAME")
        if not isinstance(cls.LAYER_NAME, str) or not cls.LAYER_NAME:
            raise TypeError(f"{cls.__name__}.LAYER_NAME must be a non-empty str")

    def __init__(self, back_action=None):
        self.back_action = back_action
        self.back = BackControl() if back_action else None
        self.seq = 0
        self.font = None
        self.title_font = None
        self.block_back = False

    def enter(self, ctx):
        self.seq = ctx["screen_seq"]
        self.font = ctx["fonts"]["ui"]
        self.title_font = ctx["fonts"]["title"]
        self.subtitle_font = ctx["fonts"]["subtitle"]
        bindings = getattr(self, "BINDINGS", None)
        if bindings:
            push_bindings(self.LAYER_NAME, bindings)
        if self.back:
            self.back.enter(ctx)

    def exit(self, ctx):
        pop_bindings(self.LAYER_NAME)

    def poll(self, ctx):
        return self.back.poll(ctx) if self.back else poll_actions_cached(ctx)
    
    def draw_back(self, ctx, surf):
        if self.back and "back_button_draw" in ctx:
            mp = ctx["get_mouse_pos"]()
            ctx["back_button_draw"](surf, mp, self.back.rect)

    def handle_back(self, ctx, actions):
        if not self.block_back and self.back and self.back.update(ctx, actions):
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
