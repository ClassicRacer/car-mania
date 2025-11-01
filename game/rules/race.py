from dataclasses import dataclass, field
from typing import Dict, List, Optional

from game.core.model.car import Car

@dataclass
class RaceState:
    laps_completed: int = 0
    gates_cleared: int = 0
    score: int = 0
    next_gate_index: int = 0

@dataclass
class Player:
    id: int
    car: Car
    race: RaceState = field(default_factory=RaceState)

@dataclass
class RaceSession:
    target_laps: int
    gate_order: List[int]
    elapsed_time: float = 0.0
    finished: bool = False
    winner_id: Optional[int] = None

    _on_active_gate: Dict[int, bool] = field(default_factory=dict)

    def active_gate_id(self, race: "RaceState") -> Optional[int]:
        if not self.gate_order:
            return None
        return self.gate_order[race.next_gate_index % len(self.gate_order)]
    
    def tick(self, dt: float) -> None:
        if not self.finished and dt > 0.0:
            self.elapsed_time += dt

    def step_player(self, player_id: int, race: "RaceState", gate_id_hit: Optional[int]) -> bool:
        if race.laps_completed >= self.target_laps:
            return True

        active_id = self.active_gate_id(race)
        on_active = (active_id is not None and gate_id_hit == active_id)

        was_on = self._on_active_gate.get(player_id, False)
        self._on_active_gate[player_id] = on_active

        if not on_active or was_on:
            return self.finished

        race.gates_cleared += 1
        race.score += 10
        race.next_gate_index = (race.next_gate_index + 1) % max(1, len(self.gate_order))

        if race.gates_cleared >= len(self.gate_order):
            race.gates_cleared = 0
            race.next_gate_index = 0
            race.laps_completed += 1
            race.score += 90
        if race.laps_completed >= self.target_laps and not self.finished:
            self.finished = True
            self.winner_id = player_id
            self.finish_time = self.elapsed_time

        return self.finished