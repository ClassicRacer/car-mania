import math
import pygame

from game.io.render import end_frame, get_half_screen
from game.render.car import CarRenderer, CarActor, DriveInput
from game.render.level_full import Camera, LevelFullRenderer
from game.ui.base_screen import BaseScreen


class Gameplay(BaseScreen):
    def __init__(self, back_action=None):
        super().__init__(back_action)
        self.full_renderer = None
        self.car_renderer = CarRenderer()
        self.camera = None
        self.car = None
        self.car_actor = None
        self.level_data = None
        self._input_state = {"up": False, "down": False, "left": False, "right": False, "brake": False}
        self.keep_car_upright = True
        self._upright_lerp = 0.35

    def enter(self, ctx):
        super().enter(ctx)
        payload = ctx.pop("gameplay", {}) or {}

        if self.full_renderer is None:
            self.full_renderer = LevelFullRenderer(ctx["pieces"])

        self.level_data = payload.get("level_data") or ctx.get("level_data") or self.level_data
        self.camera = payload.get("camera") or self.camera or Camera()
        self.car = payload.get("car") or self.car
        self.car_actor = CarActor(self.car_renderer, self.car)

        if self.full_renderer and self.level_data:
            self.full_renderer.refresh_level(self.level_data)

        if self.car is None and self.car_data:
            image = self.car_data.get("image_data")
            if image is not None:
                self.car = CarRenderer(image, pos=(0.0, 0.0))

        self._focus_camera_on_car()

    def on_resize(self, ctx, size):
        super().on_resize(ctx, size)

    def update(self, ctx, dt):
        actions = self.step(ctx)
        if self.handle_back(ctx, actions):
            return True

        self._process_actions(actions)
        self._update_car_motion(dt)
        self._focus_camera_on_car()
        return True

    def render(self, ctx):
        surf = ctx["window"]
        half_W, half_H = get_half_screen()

        if self.full_renderer and self.level_data and self.camera:
            self.full_renderer.render_to(surf, self.level_data, camera=self.camera, actors=[self.car_actor])
        else:
            surf.fill((20, 20, 20))
            
        end_frame()

    @staticmethod
    def _lerp_deg(a, b, t):
        d = ((b - a + 180.0) % 360.0) - 180.0
        return a + d * t

    def _focus_camera_on_car(self):
        if not self.camera or not self.car:
            return
        pos = pygame.Vector2(self.car.transform.pos)

        if self.full_renderer and self.level_data:
            bounds = self.full_renderer.get_piece_bounds(self.level_data)
            if bounds:
                pos.x -= bounds.x
                pos.y -= bounds.y
            offset = self.full_renderer.origin_offset
            self.camera.x = pos.x + offset.x
            self.camera.y = pos.y + offset.y
        else:
            self.camera.x = pos.x
            self.camera.y = pos.y

        if self.keep_car_upright:
            target = float(self.car.transform.angle_deg)
            self.camera.rot_deg = self._lerp_deg(float(self.camera.rot_deg), target, self._upright_lerp)

    def _process_actions(self, actions):
        for name, phase, _ in actions:
            if name == "up":
                self._input_state["up"] = phase == "press"
            elif name == "down":
                self._input_state["down"] = phase == "press"
            elif name == "left":
                self._input_state["left"] = phase == "press"
            elif name == "right":
                self._input_state["right"] = phase == "press"
            elif name == "space":
                self._input_state["brake"] = phase == "press"

    def _update_car_motion(self, dt: float):
        if not self.car:
            return
        c = self.car
        controls = DriveInput(
            up=self._input_state.get("up", False),
            down=self._input_state.get("down", False),
            left=self._input_state.get("left", False),
            right=self._input_state.get("right", False),
            brake=self._input_state.get("brake", False),
        )
        c.mechanics.update(
            dt,
            stats=c.stats,
            transform=c.transform,
            inputs=controls,
            sprite_height_px=c.appearance.image.get_height(),
            surface_grip=1.0,
            speed_cap_scale=1.0,
        )
