import pygame
from game.config.constants import FONT_FILE
from game.io.assets import load_font, load_image
from game.io.render import get_logical_size, end_frame, resize_physical, get_half_screen
from game.ui.base_screen import BaseScreen
from game.ui.widgets.button import BackControl, Button, poll_actions_cached
from game.data.queries import fetch_cars, get_max_stats

class LevelSelectScreen(BaseScreen):
    def __init__(self, back_action=None, continue_action=None):
        super().__init__(back_action)
        self.continue_button = None
        self.continue_action = continue_action

    def enter(self, ctx):
        super().enter(ctx)
        self.continue_button = Button((1500,513,300,64), "Continue", self.font, (255,255,255), (30,30,30), (50,50,50), callback=lambda c: self._continue(c))
        self.continue_button.enter(ctx)

    def _continue(self, ctx):
        if self.continue_action and self.cars:
            self.continue_action(ctx, self.cars[self.selected_car])

    def update(self, ctx, dt):
        actions = self.step(ctx)
        if actions is None:
            return False
        mp = ctx["get_mouse_pos"]()
        for name, phase, payload in actions:
            if name == "enter" and phase == "press":
                self._continue(ctx)
            if name == "right" and phase == "press":
                pass
            if name == "left" and phase == "press":
                pass
        if self.continue_button.update(ctx, actions):
            self._continue(ctx)
        if self.handle_back(ctx, actions):
            return True
        return True

    def render(self, ctx):
        surf = ctx["window"]
        surf.fill((20, 20, 20))

        W, H = get_logical_size()
        half_W, half_H = get_half_screen()

        title = self.title_font.render("Select Level", True, (255, 255, 255))
        surf.blit(title, title.get_rect(center=(half_W, 100)))

        mp = ctx["get_mouse_pos"]()
        self.continue_button.draw(surf, mp)
        self.draw_back(ctx, surf)
        end_frame()
    
    def _scale_image(self, img : pygame.Surface, tile_size):
        w, h = img.get_size()
        tw, th = tile_size
        scale_ratio = min(tw/w, th/h)
        new_size = (int(w*scale_ratio), int(h*scale_ratio))
        return pygame.transform.scale(img, new_size)