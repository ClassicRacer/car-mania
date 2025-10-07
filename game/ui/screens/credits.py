from game.io.render import end_frame, get_half_screen, get_logical_size
from game.ui.screens.base_screen import BaseScreen
from game.ui.utils import draw_text
from game.ui.widgets.button import Button


class Credits(BaseScreen):
    def __init__(self, back_action=None, continue_action=None):
        super().__init__(back_action)
        self.continue_button = None
        self.continue_action = continue_action
        self._light = (255, 255, 255)
        self._muted = (210, 210, 210)
        self.version = "v2.0.0-alpha.1"
        self._sections = [
            ("Programming & Game Design", "Harish Menon (ClassicRacer)"),
            ("Art & Assets", "Assets, cars, and level design derived from original release"),
            ("Technology", "Built with Python and pygame"),
        ]
        self._planned = [
            "Sound Effects",
            "Background Music",
            "Configurable Options",
            "Car / Level Creator",
            "Improved Assets",
        ]

    def enter(self, ctx):
        super().enter(ctx)
        W, H = get_logical_size() 
        self.continue_button = Button((0,H-120,300,64), "Continue", self.font, (255,255,255), (30,30,30), (50,50,50), callback=lambda c: self._continue(c), center_mode="horizontal")
        self.continue_button.enter(ctx)

    def _continue(self, ctx):
        if self.continue_action:
            self.continue_action(ctx)
    
    def on_resize(self, ctx, size):
        super().on_resize(ctx, size)
        W, H = get_logical_size()
        if self.continue_button:
            self.continue_button.set_rect((0, H - 120, 300, 64))

    def update(self, ctx, dt):
        actions = self.step(ctx)
        if actions is None:
            return False
        if self.continue_button.update(ctx, actions):
            self._continue(ctx)
        if self.handle_back(ctx, actions):
            return True
        return True
    
    def render(self, ctx):
        surf = ctx["window"]
        surf.fill((10,10,10))
        W, H = get_logical_size()
        half_W, _ = get_half_screen()
        y = 100
        draw_text(surf, "Credits", self.title_font, (255, 255, 255), (half_W, y), centered=True)
        y += 150
        for header, body in self._sections:
            draw_text(surf, header, self.subtitle_font, self._light, (half_W, y), centered=True)
            y += 36
            draw_text(surf, body, self.font, self._muted, (half_W, y), centered=True)
            y += 52
        draw_text(surf, "Planned Features", self.subtitle_font, self._light, (half_W, y), centered=True)
        y += 44
        for item in self._planned:
            draw_text(surf, f"{item}", self.font, self._muted, (half_W, y), centered=True)
            y += 32
        draw_text(surf, self.version, self.font, self._muted, (5, H - 45))
        mp = ctx["get_mouse_pos"]()
        self.continue_button.draw(surf, mp)
        self.draw_back(ctx, surf)
        end_frame()
    