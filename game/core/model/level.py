from dataclasses import dataclass

@dataclass
class Level:
    id: int
    name: str
    code: str
    ground: tuple
    laps: int
    music_path: str