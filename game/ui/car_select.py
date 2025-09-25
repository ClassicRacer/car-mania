import pygame
from game.core.state import Screen
from game.io.assets import load_image
from game.io.render import get_mouse_pos_logical, end_frame, resize_physical, get_half_screen
from game.ui.widgets import BackControl
from game.data.queries import fetch_cars

class CarSelectScreen(Screen):
    def __init__(self, back_action=None, on_select=None, tile_size=(360,220), margin=24):
        self.back_action = back_action
        self.on_select = on_select
        self.seq = 0
        self.font = None
        self.selected_car = 0
        self.images = []
        self.back = BackControl() if back_action else None
        self.title_font = None
        self.back_rect = pygame.Rect(20, 20, 160, 56)
        self.down = False
        self.down_on_back = False

    def enter(self, ctx):
        self.seq = ctx["screen_seq"]
        self.font = ctx["fonts"]["ui"]
        self.title_font = ctx["fonts"]["title"]
        cars = fetch_cars(ctx["db"], ctx["profile_id"])
        import random
        self.selected_car = random.randint(0, len(cars)-1) if cars else 0
        self.images = []
        for car in cars:
            img = load_image(car["image"])
            if img is None:
                img = pygame.Surface((200, 100))
                img.fill((255, 0, 255))
            self.images.append(img)
        self.down = False
        self.down_on_back = False
        self.down_card = None

    def update(self, ctx, dt):
        for name, phase, payload in ctx["poll_actions"]():
            if name == "quit":
                return False
            if name == "window_resized" and phase == "change":
                resize_physical(payload)
            if name == "escape" and phase == "press":
                if self.back_action:
                    self.back_action(ctx)
            if name == "mouse_down" and phase == "press" and payload == 1 and not self.down:
                mp = get_mouse_pos_logical()
                self.down = True
                self.down_on_back = self.back_rect.collidepoint(mp)
            if name == "mouse_up" and phase == "release" and payload == 1:
                mp = get_mouse_pos_logical()
                if self.down and ctx["screen_seq"] == self.seq:
                    if self.down_on_back and self.back_rect.collidepoint(mp):
                        if self.back_action:
                            self.back_action(ctx)
                self.down = False
                self.down_on_back = False
            if name == "right" and phase == "press":
                self.selected_car = (self.selected_car + 1) % len(self.images) if self.images else 0
            if name == "left" and phase == "press":
                self.selected_car = (self.selected_car - 1) % len(self.images) if self.images else 0
        return True

    def render(self, ctx):
        surf = ctx["window"]
        surf.fill((20, 20, 20))
        title = self.title_font.render("Select Car", True, (255, 255, 255))
        surf.blit(title, title.get_rect(center=(get_half_screen()[0], 100)))

        surf.blit(self.images[self.selected_car], self.images[self.selected_car].get_rect(center=get_half_screen()))

        mp = ctx["get_mouse_pos"]()
        if self.back and "back_button_draw" in ctx:
            ctx["back_button_draw"](surf, mp, self.back.rect)
        end_frame()