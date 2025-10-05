from dataclasses import dataclass, field

from game.core.model.car import Car

@dataclass
class RaceState:
    laps_completed: int = 0
    gates_cleared: int = 0

@dataclass
class Player:
    id: int
    car: Car
    race: RaceState = field(default_factory=RaceState)

@dataclass
class RaceSession:
    target_laps: int
    time: int