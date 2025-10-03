from dataclasses import dataclass
from typing import Tuple
import pygame

@dataclass(frozen=True)
class CarMechanics:
    id: int
    name: str
    top_speed: float
    acceleration: float
    handling: float
    offroad: float
    engine_type: int

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
    mechanics: CarMechanics
    transform: Transform
    appearance: CarAppearance

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
        rect = rotated.get_rect()
        x = world_top_left_px[0] + t.pos[0] * zoom - a.pivot[0] * total_scale
        y = world_top_left_px[1] + t.pos[1] * zoom - a.pivot[1] * total_scale
        rect.topleft = (int(round(x)), int(round(y)))
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
    mech = CarMechanics(
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
    transform = Transform(pos=(0.0, 0.0), angle_deg=0.0, scale=scale)
    return Car(mechanics=mech, transform=transform, appearance=appearance)