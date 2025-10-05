import math
import pygame

from game.io.render import end_frame, get_half_screen
from game.core.model.car import DriveInput
from game.render.car_view import CarActor, CarRenderer
from game.render.level_full import Camera, LevelFullRenderer
from game.ui.screens.base_screen import BaseScreen
from game.rules.race import RaceSession


class Gameplay(BaseScreen):
    def __init__(self, back_action=None):
        super().__init__(back_action)
        self.full_renderer = None
        self.car_renderer = CarRenderer()
        self.camera = None
        self.level_data = None
        self.players = []
        self.actors = []
        self._input_state = {"up": False, "down": False, "left": False, "right": False, "brake": False}
        self.keep_car_upright = True
        self._upright_lerp = 0.35
        self._last_contacts = None
        self.debug_collision_print = True
        self.session = None


    def enter(self, ctx):
        super().enter(ctx)
        payload = ctx.pop("gameplay", {}) or {}

        if self.full_renderer is None:
            self.full_renderer = LevelFullRenderer(ctx["pieces"])

        self.level_data = payload.get("level_data") or ctx.get("level_data") or self.level_data
        self.camera = payload.get("camera") or self.camera or Camera()
        
        self.players = list(payload.get("players") or ctx.get("players") or [])
        self.actors = [CarActor(self.car_renderer, p.car) for p in self.players if getattr(p, "car", None)]

        entry = self.full_renderer._get_world(self.level_data)
        gate_order = [order for (order, _, _, _) in sorted(entry["gates"], key=lambda g: g[0])]
        laps = self.level_data["laps"]
        self.session = RaceSession(target_laps=laps, gate_order=gate_order)


        self._focus_camera_on_main_player()

    def on_resize(self, ctx, size):
        super().on_resize(ctx, size)

    def update(self, ctx, dt):
        actions = self.step(ctx)
        if self.handle_back(ctx, actions):
            return True

        self._process_actions(actions)
        self._update_car_motion(dt)
        self._update_race(dt)
        self._focus_camera_on_main_player()
        self._debug_print_collisions()
        return True

    def render(self, ctx):
        surf = ctx["window"]
        half_W, half_H = get_half_screen()

        if self.full_renderer and self.level_data and self.camera:
            self.full_renderer.render_to(surf, self.level_data, camera=self.camera, actors=self.actors if self.actors else None)
        else:
            surf.fill((20, 20, 20))
            
        end_frame()

    @staticmethod
    def _lerp_deg(a, b, t):
        d = ((b - a + 180.0) % 360.0) - 180.0
        return a + d * t

    def _focus_camera_on_main_player(self):
        if not (self.camera and self.players):
            return
        car = self.players[0].car
        if not getattr(self.players[0], "car", None):
            return
        pos = pygame.Vector2(car.transform.pos)

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
            target = float(car.transform.angle_deg)
            self.camera.rot_deg = self._lerp_deg(float(self.camera.rot_deg), target, self._upright_lerp)

    def _process_actions(self, actions):
        for name, phase, _ in actions:
            if name == "up":
                self._input_state["up"] = phase == "press"
            elif name == "down":
                self._input_state["down"] = phase == "press"
            elif name == "left":
                self._input_state["left"] = phase == "press"
            elif name == "right":
                self._input_state["right"] = phase == "press"
            elif name == "space":
                self._input_state["brake"] = phase == "press"

    def _update_car_motion(self, dt: float):
        c = self.players[0].car
        controls = DriveInput(
            up=self._input_state.get("up", False),
            down=self._input_state.get("down", False),
            left=self._input_state.get("left", False),
            right=self._input_state.get("right", False),
            brake=self._input_state.get("brake", False),
        )
        contacts = self.full_renderer.query_car_contacts(self.level_data, c)
        is_on_road = bool(contacts.get("on_road"))
        c.mechanics.update(
            dt,
            stats=c.stats,
            transform=c.transform,
            inputs=controls,
            sprite_height_px=c.appearance.image.get_height(),
            on_road=is_on_road,
            surface_grip=1.0,
            speed_cap_scale=1.0,
        )

    
    def _update_race(self, dt: float):
        if not (self.session and self.players and self.level_data):
            return

        self.session.tick(dt)

        for p in self.players:
            contacts = self.full_renderer.query_car_contacts(self.level_data, p.car)
            gate_id = contacts.get("gate_id")
            finished_now = self.session.step_player(p.id, p.race, gate_id)

            # simple debug prints
            if gate_id is not None:
                print(f"[race] player={p.id} hit gate {gate_id} | cleared={p.race.gates_cleared} lap={p.race.laps_completed}")

            if finished_now:
                print(f"[race] FINISH! winner={self.session.winner_id} time={self.session.finish_time:.3f}s")

    def _debug_print_collisions(self):
        if not self.debug_collision_print:
            return
        if not (self.full_renderer and self.level_data and self.players):
            return

        car = self.players[0].car
        contacts = self.full_renderer.query_car_contacts(self.level_data, car)
        if contacts != self._last_contacts:
            surf = "road" if contacts.get("on_road") else "offroad"

            solids = []
            if contacts.get("hit_wall"):
                solids.append("maze_wall")
            if contacts.get("hit_tree"):
                solids.append("tree")
            if contacts.get("hit_gate"):
                gid = contacts.get("gate_id")
                solids.append(f"gate:{gid}" if gid is not None else "gate")

            solid_str = "clear" if not solids else "|".join(solids)

            pos = car.transform.pos
            ang = getattr(car.transform, "angle_deg", 0.0)
            v_world = car.mechanics.speed * car.mechanics.MOVE

            print(f"[contacts] {surf}, {solid_str} | pos=({pos[0]:.1f},{pos[1]:.1f}) ang={ang:.1f}° speed={v_world:.1f}px/s")

            self._last_contacts = contacts
