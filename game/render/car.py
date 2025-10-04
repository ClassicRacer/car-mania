from dataclasses import dataclass
from typing import Tuple, Protocol
import math
import pygame

@dataclass(frozen=True)
class CarStats:
    id: int
    name: str
    top_speed: float
    acceleration: float
    handling: float
    offroad: float
    engine_type: int

class HasTransform(Protocol):
    pos: tuple[float, float]
    angle_deg: float
    scale: float

class HasStats(Protocol):
    top_speed: float
    acceleration: float
    handling: float

@dataclass(frozen=True)
class DriveInput:
    up: bool = False
    down: bool = False
    left: bool = False
    right: bool = False
    brake: bool = False

    @property
    def throttle(self) -> float:
        return (1.0 if self.up else 0.0) + (-1.0 if self.down else 0.0)

    @property
    def steer(self) -> float:
        return (-1.0 if self.left else 0.0) + (1.0 if self.right else 0.0)


@dataclass
class CarMechanics:
    speed: float = 0.0
    angle: float = 0.0
    steer_angle: float = 0.0 

    MOVE = 50.0
    ACCEL = 1.0

    STEER_RESP_HZ = 10.0
    TURN_GAIN = 0.60
    HANDLING_MIN = 0.40
    INVERT_REVERSE = True

    TURN_LOW = 0.50
    TURN_MID = 0.90
    HIGH_FALLOFF = 0.75
    SLOW_END = 0.20
    FAST_BEG = 0.55
    MAX_YAW_RPS = 2.10

    INPUT_SHAPE_POW = 1.35
    REVERSE_CAP = 0.5

    STEER_START_NORM = 0.02
    STEER_FULL_NORM  = 0.12

    BRAKE_POWER = 3.0

    def update(self, dt, stats, transform, inputs: DriveInput, *, sprite_height_px: int, surface_grip: float = 1.0, speed_cap_scale: float = 1.0):
        if dt <= 0.0:
            return
        if not hasattr(self, "steer_state"):
            self.steer_state = 0.0


        self.speed += inputs.throttle * stats.acceleration * self.ACCEL * dt
        if inputs.brake:
            decel = stats.acceleration * self.ACCEL * self.BRAKE_POWER * dt
            if self.speed > 0.0:
                self.speed = max(0.0, self.speed - decel)
            elif self.speed < 0.0:
                self.speed = min(0.0, self.speed + decel)

        top = stats.top_speed * speed_cap_scale
        rev_cap = -(top * self.REVERSE_CAP)
        if self.speed > top: self.speed = top
        if self.speed < rev_cap: self.speed = rev_cap

        v_px = self.speed * self.MOVE
        s = 0.0 if stats.top_speed <= 1e-6 else min(1.0, abs(self.speed) / stats.top_speed)

        alpha = 1.0 - math.exp(-self.STEER_RESP_HZ * dt)
        steer_in = inputs.steer
        if self.INVERT_REVERSE and self.speed < -0.01 * stats.top_speed:
            steer_in = -steer_in
        steer_in = math.copysign(abs(steer_in) ** self.INPUT_SHAPE_POW, steer_in)
        self.steer_state += (steer_in - self.steer_state) * alpha

        t_low = self.TURN_LOW
        t_mid = self.TURN_MID

        def smoothstep(a, b, x):
            if a == b: return 0.0
            t = max(0.0, min(1.0, (x - a) / (b - a)))
            return t*t*(3.0 - 2.0*t)

        base = t_low + (t_mid - t_low) * smoothstep(0.0, self.SLOW_END, s)
        high_cut = 1.0 - self.HIGH_FALLOFF * smoothstep(self.FAST_BEG, 1.0, s)
        handling_gain = max(self.HANDLING_MIN, float(stats.handling))
        yaw_rate = min(self.MAX_YAW_RPS, handling_gain * self.TURN_GAIN * base * high_cut)
        ramp = 0.0 if s <= self.STEER_START_NORM else (
            1.0 if s >= self.STEER_FULL_NORM else smoothstep(self.STEER_START_NORM, self.STEER_FULL_NORM, s)
        )
        yaw_rate *= ramp
        self.angle += (self.steer_state * yaw_rate) * dt

        transform.angle_deg = (math.degrees(self.angle)) % 360.0
        dx = math.sin(self.angle) * v_px * dt
        dy = -math.cos(self.angle) * v_px * dt
        transform.pos = (transform.pos[0] + dx, transform.pos[1] + dy)

@dataclass
class Transform:
    pos: Tuple[float, float] = (0.0, 0.0)
    angle_deg: float = 0.0
    scale: float = 1.0

@dataclass
class CarAppearance:
    image: pygame.Surface
    pivot: Tuple[float, float]
    z_index: int = 0

class CarActor:
    def __init__(self, car_renderer, car):
        self.car_renderer = car_renderer
        self.car = car
    def render_in_canvas_space(self, canvas, world_top_left_px, zoom):
        self.car_renderer.render(canvas, self.car, world_top_left_px, zoom)

@dataclass
class Car:
    stats: CarStats
    transform: Transform
    appearance: CarAppearance
    mechanics: CarMechanics

class CarRenderer:
    def __init__(self):
        self._cache = {}

    def _scaled_sprite(self, image: pygame.Surface, scale: float) -> pygame.Surface:
        key = (id(image), round(scale, 5))
        if key in self._cache:
            return self._cache[key]
        s = max(1e-6, scale)
        if abs(s - 1.0) <= 1e-3:
            spr = image
        else:
            w, h = image.get_size()
            spr = pygame.transform.smoothscale(image, (max(1, int(round(w * s))), max(1, int(round(h * s)))))
        self._cache[key] = spr
        return spr

    def render(self, canvas: pygame.Surface, car: Car, world_top_left_px: Tuple[float, float], zoom: float):
        t = car.transform
        a = car.appearance
        total_scale = t.scale * zoom
        spr = self._scaled_sprite(a.image, total_scale)
        rotated = pygame.transform.rotate(spr, -t.angle_deg)

        cx = world_top_left_px[0] + t.pos[0] * zoom
        cy = world_top_left_px[1] + t.pos[1] * zoom
        rect = rotated.get_rect(center=(int(round(cx)), int(round(cy))))
        canvas.blit(rotated, rect)

def compute_scale(pieces: dict, car_img: pygame.Surface, ref_key: str = "road_1", fraction: float = 0.70) -> float:
    ref = pieces.get(ref_key)
    if not ref or not car_img:
        return 1.0
    road_w, _ = ref.get_size()
    car_w, _ = car_img.get_size()
    if car_w <= 0:
        return 1.0
    return max(0.01, (road_w * fraction) / car_w)

def car_from_dict(selected_car: dict, ctx: dict) -> Car:
    img = selected_car["image_data"].convert_alpha()
    scale = compute_scale(ctx["pieces"], img, ref_key="road_1", fraction=0.35)
    mech = CarStats(
        id=int(selected_car["id"]),
        name=str(selected_car["name"]),
        top_speed=float(selected_car["top_speed"]),
        acceleration=float(selected_car["acceleration"]),
        handling=float(selected_car["handling"]),
        offroad=float(selected_car["offroad"]),
        engine_type=int(selected_car["engine_type"])
        #engine_type=EngineType(selected_car["engine_type"])
    )
    w, h = img.get_size()
    appearance = CarAppearance(image=img, pivot=(w * 0.5, h * 0.5), z_index=int(selected_car.get("z_index", 0)))
    transform = Transform(pos=(35.0, 0.0), angle_deg=0.0, scale=scale)
    mechanics = CarMechanics()
    return Car(stats=mech, transform=transform, appearance=appearance, mechanics=mechanics)