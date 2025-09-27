from dataclasses import dataclass

@dataclass
class LevelData:
    color: tuple
    laps: int
    code: list
    walls: dict
    is_maze: bool