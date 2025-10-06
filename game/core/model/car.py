from dataclasses import dataclass
from typing import Optional, Tuple, TYPE_CHECKING
import math

if TYPE_CHECKING:
    from game.render.car_view import CarAppearance

@dataclass(frozen=True)
class CarStats:
    id: int
    name: str
    top_speed: float
    acceleration: float
    handling: float
    offroad: float
    engine_type: int

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
    ACCEL = 0.55

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

    DRAG_OFFROAD_MAX = 2.8
    DRAG_OFFROAD_SPEED_BIAS = 0.35
    SPEED_EPS = 0.003

    def update(self, dt, stats, transform, inputs: DriveInput, *, sprite_height_px: int, on_road: bool = True, surface_grip: float = 1.0, speed_cap_scale: float = 1.0):
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

        if not on_road:
            off = max(1.0, min(5.0, float(stats.offroad)))
            t = (off - 1.0) / 4.0
            c_drag = (1.0 - t) * self.DRAG_OFFROAD_MAX

            s_norm = 0.0 if top <= 1e-6 else min(1.0, abs(self.speed) / top)
            c_drag *= (self.DRAG_OFFROAD_SPEED_BIAS + (1.0 - self.DRAG_OFFROAD_SPEED_BIAS) * s_norm)

            if surface_grip > 0.0:
                c_drag *= (1.0 / surface_grip)

            self.speed *= math.exp(-c_drag * dt)

        if abs(self.speed) < self.SPEED_EPS:
            self.speed = 0.0

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
class Car:
    stats: CarStats
    transform: Transform
    mechanics: CarMechanics
    appearance: Optional["CarAppearance"] = None