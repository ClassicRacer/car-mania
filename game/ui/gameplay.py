import math
import pygame

from game.io.render import end_frame, get_half_screen
from game.render.car import CarRenderer, CarActor
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
        self._input_state = {"up": False, "down": False, "left": False, "right": False}
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
            if name == "left":
                self._input_state["left"] = phase == "press"
            elif name == "right":
                self._input_state["right"] = phase == "press"

    # TODO: Move to CarMechanics
    def _update_car_motion(self, dt: float):
        if not self.car or dt <= 0:
            return
        car = self.car
        mech = car.mechanics
        stats = car.stats
        t = car.transform
        inp = self._input_state

        throttle = (1.0 if inp.get("up") else 0.0) + (-1.0 if inp.get("down") else 0.0)
        mech.speed += throttle * stats.acceleration * mech.ACCEL * dt

        max_rev = stats.top_speed * 0.5
        if   mech.speed >  stats.top_speed: mech.speed = stats.top_speed
        elif mech.speed < -max_rev:          mech.speed = -max_rev

        steer_in = (-1.0 if inp.get("left") else 0.0) + (1.0 if inp.get("right") else 0.0)
        v_px = mech.speed * mech.MOVE
        if mech.WHEELBASE_PX <= 0.0:
            sprite_h = car.appearance.image.get_height()
            mech.WHEELBASE_PX = max(60.0, sprite_h * car.transform.scale * 0.55)
        L = mech.WHEELBASE_PX
        max_deg = min(mech.STEER_MAX_CAP_DEG, mech.STEER_MAX_BASE_DEG + stats.handling * mech.STEER_MAX_GAIN_DEG)
        delta_max = math.radians(max_deg)
        target_delta = steer_in * delta_max
        alpha = 1.0 - math.exp(-mech.STEER_RESP_HZ * dt)
        mech.steer_angle += (target_delta - mech.steer_angle) * alpha
        ay_max = mech.AY_MAX_BASE + mech.AY_PER_HANDLING * stats.handling
        if abs(v_px) > 1e-6:
            tan_limit = (ay_max * L) / (v_px * v_px)
            limit_delta = math.atan(max(0.0, tan_limit))
            delta_eff = max(-limit_delta, min(limit_delta, mech.steer_angle))
        else:
            delta_eff = mech.steer_angle
        omega = (v_px / L) * math.tan(delta_eff)
        mech.angle += omega * dt
        t.angle_deg = (math.degrees(mech.angle)) % 360.0

        dx = math.sin(mech.angle) * (mech.speed * mech.MOVE) * dt
        dy = -math.cos(mech.angle) * (mech.speed * mech.MOVE) * dt
        t.pos = (t.pos[0] + dx, t.pos[1] + dy)
