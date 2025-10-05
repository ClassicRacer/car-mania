import math
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

COLL_SLIDE_KEEP   = 0.90   # keep this fraction of speed when sliding
COLL_BOUNCE_KEEP  = 0.25   # keep this fraction of speed on a dead stop
PERP_PROBE_PX     = 6.0    # how far we probe along tangents to find a slide
DEPENETRATE_EPS   = 1.5    # tiny push out of solids to avoid sticking
ALIGN_RATE        = 0.12   # how quickly heading turns toward the sliding direction

# extra anti-stuck
RADIAL_PROBE_INNER = 6.0     # px
RADIAL_PROBE_OUTER = 16.0    # px
RADIAL_PROBE_STEPS = 16      # directions to test around the car

UNSTICK_TIME       = 0.45    # s of being blocked before we force a nudge
UNSTICK_BACKSTEP   = 10.0    # px we step opposite the last motion
UNSTICK_TURN       = 0.25    # rad we twist the nose on unstick

@dataclass
class CollisionState:
    stuck_timer: float = 0.0
    last_free_pos: Optional[Tuple[float, float]] = None

@dataclass
class CollisionResult:
    pos: Tuple[float, float]
    state: str                
    allowed_vec: Tuple[float, float]

class CollisionResolver:
    def __init__(self):
        self._per_car: Dict[int, CollisionState] = {}

    def reset(self):
        self._per_car.clear()

    def reset_car(self, car):
        self._per_car.pop(id(car), None)

    def resolve(
            self, 
            car,
            old_pos: Tuple[float, float], 
            move_vec: Tuple[float, float],
            dt: float,
            level_renderer,
            level_row) -> CollisionResult:
        state = self._state_for(car)
        dx, dy = move_vec
        pos, kind, (dx_ok, dy_ok) = self._move_with_collisions(car, old_pos, dx, dy, level_renderer, level_row)
        if kind == "free":
            state.last_free_pos = pos
            state.stuck_timer = 0.0
        else:
            state.stuck_timer += dt
        tried_len = max(1e-6, (dx*dx + dy*dy) ** 0.5)
        ok_len    = (dx_ok*dx_ok + dy_ok*dy_ok) ** 0.5
        if kind in ("slide_x", "slide_y"):
            keep = COLL_SLIDE_KEEP * (ok_len / tried_len)
            car.mechanics.speed *= keep
            if ok_len > 1e-6:
                target_ang = math.atan2(dx_ok, -dy_ok)
                cur = car.mechanics.angle
                d = ((target_ang - cur + math.pi) % (2*math.pi)) - math.pi
                car.mechanics.angle = cur + d * ALIGN_RATE
                car.transform.angle_deg = (math.degrees(car.mechanics.angle)) % 360.0
        elif kind == "unstick":
            car.mechanics.speed *= 0.6
            car.mechanics.angle += UNSTICK_TURN * (1 if dx*dy >= 0 else -1)
            car.transform.angle_deg = (math.degrees(car.mechanics.angle)) % 360.0
            state.stuck_timer = 0.0

        elif kind == "blocked":
            car.mechanics.speed *= COLL_BOUNCE_KEEP
            if state.stuck_timer >= UNSTICK_TIME and state.last_free_pos:
                lx, ly = state.last_free_pos
                px, py = car.transform.pos
                vx, vy = px - lx, py - ly
                vlen = (vx*vx + vy*vy) ** 0.5
                if vlen > 1e-6:
                    ux, uy = vx / vlen, vy / vlen
                    npos = (px - ux*UNSTICK_BACKSTEP, py - uy*UNSTICK_BACKSTEP)
                    if not self._collides_solid_at(car, npos, level_renderer, level_row):
                        pos = npos
                        car.mechanics.angle += UNSTICK_TURN * (-1 if dx*dy >= 0 else 1)
                        car.transform.angle_deg = (math.degrees(car.mechanics.angle)) % 360.0
                        state.stuck_timer = 0.0
        return CollisionResult(pos=pos, state=kind, allowed_vec=(dx_ok, dy_ok))

    def _state_for(self, car) -> CollisionState:
        key = id(car)
        st = self._per_car.get(key)
        if st is None:
            st = CollisionState()
            self._per_car[key] = st
        return st
    
    def _collides_solid_at(self, car, pos, level_renderer, level_row) -> bool:
        old = car.transform.pos
        car.transform.pos = pos
        contacts = level_renderer.query_car_contacts(level_row, car)
        car.transform.pos = old
        return bool(contacts.get("hit_wall") or contacts.get("hit_tree"))

    def _try_nudge(self, car, base_pos, dir_vec, dist, level_renderer, level_row) -> tuple[tuple[float,float], bool]:
        bx, by = base_pos
        nx, ny = bx + dir_vec[0]*dist, by + dir_vec[1]*dist
        if not self._collides_solid_at(car, (nx, ny), level_renderer, level_row):
            return (nx, ny), True
        return base_pos, False

    def _find_free_direction(self, car, base_pos, level_renderer, level_row):
        for r in (RADIAL_PROBE_INNER, RADIAL_PROBE_OUTER):
            for i in range(RADIAL_PROBE_STEPS):
                a = (2.0*math.pi) * (i / RADIAL_PROBE_STEPS)
                d = (math.cos(a), math.sin(a))
                pos, ok = self._try_nudge(car, base_pos, d, r, level_renderer, level_row)
                if ok:
                    return pos, d
        return base_pos, None

    def _move_with_collisions(self, car, old_pos, dx, dy, level_renderer, level_row):
        ox, oy = old_pos
        nx, ny = ox + dx, oy + dy

        if not self._collides_solid_at(car, (nx, ny), level_renderer, level_row):
            return (nx, ny), "free", (dx, dy)

        if abs(dx) > 0 and not self._collides_solid_at(car, (ox + dx, oy), level_renderer, level_row):
            return (ox + dx, oy), "slide_x", (dx, 0.0)
        if abs(dy) > 0 and not self._collides_solid_at(car, (ox, oy + dy), level_renderer, level_row):
            return (ox, oy + dy), "slide_y", (0.0, dy)

        lo, hi = 0.0, 1.0
        for _ in range(7):
            mid = 0.5 * (lo + hi)
            test = (ox + dx*mid, oy + dy*mid)
            if self._collides_solid_at(car, test, level_renderer, level_row):
                hi = mid
            else:
                lo = mid
        pos = (ox + dx*lo, oy + dy*lo)

        mv_len = max(1e-6, (dx*dx + dy*dy) ** 0.5)
        back = (-dx/mv_len, -dy/mv_len)
        pos, _ = self._try_nudge(car, pos, back, DEPENETRATE_EPS, level_renderer, level_row)

        tx, ty = (-dy/mv_len, dx/mv_len)
        pos_try, ok = self._try_nudge(car, pos, (tx, ty), PERP_PROBE_PX, level_renderer, level_row)
        if not ok:
            pos_try, ok = self._try_nudge(car, pos, (-tx, -ty), PERP_PROBE_PX, level_renderer, level_row)
        if ok:
            return pos_try, "blocked", (0.0, 0.0)

        pos_free, d = self._find_free_direction(car, pos, level_renderer, level_row)
        if d is not None:
            return pos_free, "unstick", (0.0, 0.0)
        
        return pos, "blocked", (0.0, 0.0)