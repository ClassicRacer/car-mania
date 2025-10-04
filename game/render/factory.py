import pygame

from game.core.model.car import Car, CarMechanics, CarStats, Transform
from game.render.car_view import CarAppearance


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