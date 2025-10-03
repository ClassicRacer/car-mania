import pygame
from game.config.constants import FONT_FILE
from game.io.assets import load_font, load_image
from game.io.render import get_logical_size, end_frame, get_half_screen
from game.ui.base_screen import BaseScreen
from game.ui.widgets.button import Button
from game.data.queries import fetch_cars, get_max_stats

class CarSelectScreen(BaseScreen):
    def __init__(self, back_action=None, continue_action=None, tile_size=(150,150), margin=24):
        super().__init__(back_action)
        self.card_font = None
        self.selected_car = 0
        self.cars = []
        self.max_stats = {}
        self.continue_button = None
        self.continue_action = continue_action
        self.tile_size = tile_size
        self.margin = margin
        self.rotation = 0

    def enter(self, ctx):
        super().enter(ctx)
        self.card_font = load_font(FONT_FILE, 20)
        self.cars = fetch_cars(ctx["db"], ctx["profile_id"])
        self.max_stats = get_max_stats(ctx["db"], ctx["profile_id"])
        self.continue_button = Button((1500,513,300,64), "Continue", self.font, (255,255,255), (30,30,30), (50,50,50), callback=lambda c: self._continue(c))
        self.continue_button.enter(ctx)
        if(ctx.get("selected_car_id", -1) == -1):
            import random
            self.selected_car = random.randint(0, len(self.cars)-1) if self.cars else 0
        else:
            self.selected_car = ctx["selected_car_id"]
        for car in self.cars:
            img = load_image(car.pop("image"))
            if img is None:
                img = pygame.Surface((200, 100))
                img.fill((255, 0, 255))
            car["image_data"] = img

    def _continue(self, ctx):
        ctx["selected_car_id"] = self.selected_car
        selected = self.cars[self.selected_car] if self.cars else None
        ctx["selected_car"] = selected
        if self.continue_action and selected:
            self.continue_action(ctx, selected)

    def update(self, ctx, dt):
        actions = self.step(ctx)
        if actions is None:
            return False
        mp = ctx["get_mouse_pos"]()
        self.rotation -= ((mp[0] - get_half_screen()[0]) * 0.2 * dt)
        self.rotation %= 360
        for name, phase, payload in actions:
            if name == "enter" and phase == "press":
                self._continue(ctx)
            if name == "right" and phase == "press":
                self.selected_car = (self.selected_car + 1) % len(self.cars) if self.cars else 0
            if name == "left" and phase == "press":
                self.selected_car = (self.selected_car - 1) % len(self.cars) if self.cars else 0
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

        title = self.title_font.render("Select Car", True, (255, 255, 255))
        surf.blit(title, title.get_rect(center=(half_W, 100)))

        if self.cars:
            title = self.font.render(self.cars[self.selected_car]["name"], True, (255, 255, 255))
            surf.blit(title, title.get_rect(center=(half_W, 190)))

        stat_x = 60
        bar_w = 300

        overlay = pygame.Surface((bar_w + 100, 250), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (30, 30, 30, 180), overlay.get_rect(), border_radius=8)
        surf.blit(overlay, (stat_x - 20, half_H // 1.3))

        for idx, (label, stat) in enumerate(zip(["Top Speed", "Acceleration", "Handling", "Offroad"], ["top_speed", "acceleration", "handling", "offroad"])):
            render = self.font.render(label, True, (255, 255, 255))
            surf.blit(render, (stat_x, (half_H // 1.3) + idx * 60))
            value = self.cars[self.selected_car][stat] if self.cars else 0
            max_value = self.max_stats[f"max_{stat}"] if self.max_stats else 1
            bar_h = 10
            y = ((half_H // 1.3) + idx * 60) + 42
            pygame.draw.rect(surf, (128, 128, 128), (stat_x, y, bar_w, bar_h))
            fill_w = int((value / max_value) * bar_w) if max_value > 0 else 0
            pygame.draw.rect(surf, (255, 255, 255), (stat_x, y, fill_w, bar_h))
            stat_text = self.font.render(f"{round((value / max_value) * 10, 1)}", True, (255, 255, 255))
            surf.blit(stat_text, stat_text.get_rect(center=(stat_x + bar_w + 40, y + bar_h // 2)))

        if self.cars:
            img = self.cars[self.selected_car]["image_data"] if self.cars else None
            img = pygame.transform.rotate(img, self.rotation)
            surf.blit(img, img.get_rect(center=get_half_screen()))

        N = max(1, len(self.cars))
        pad = self.margin
        slot_w = (W - pad*2) // N
        slot_h = self.tile_size[1]
        y = H - 150

        for idx, car in enumerate(self.cars):
            img = self._scale_image(car["image_data"], self.tile_size)
            name = self.card_font.render(car["name"], True, (255, 255, 255))
            rect = pygame.Rect(0, 0, slot_w, slot_h)
            rect.center = (pad + slot_w*idx + slot_w//2, y)
            if idx == self.selected_car:
                overlay = pygame.Surface((rect.w + 20, rect.h + 50), pygame.SRCALPHA)
                pygame.draw.rect(overlay, (50, 50, 50, 180), overlay.get_rect(), border_radius=8)
                surf.blit(overlay, (rect.x - 10, rect.y - 10))
            surf.blit(img, img.get_rect(center=rect.center))
            surf.blit(name, name.get_rect(center=(rect.centerx, rect.bottom + 20)))

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
    
    def _draw_string_in_rect_center(self, surf, y, text, rect_x, rect_w, font, fixed_color=True):
        color = (255, 255, 255) if fixed_color else (200, 200, 200)
        text_surf = font.render(text, True, color)

        center_x = rect_x + rect_w // 2
        draw_x = center_x - text_surf.get_width() // 2

        surf.blit(text_surf, (draw_x, y))
