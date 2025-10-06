import pygame

from game.io.render import end_frame, get_logical_size
from game.core.model.car import DriveInput
from game.render.car_view import CarActor, CarRenderer
from game.render.level_full import Camera, LevelFullRenderer
from game.ui.screens.base_screen import BaseScreen
from game.rules.race import RaceSession
from game.ui.utils import draw_text, center_text_on_oval
from game.world.collision import CollisionResolver

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
        self.session = None
        self.collision = None
        self.icon_hud = None
        self.hud_font = None

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
        self.collision = CollisionResolver()
        self.icon_hud = ctx["fonts"]["icon_hud"]
        self.icon_2_hud = ctx["fonts"]["icon_2_hud"]
        self.hud_font = ctx["fonts"]["hud"]

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
        return True

    def render(self, ctx):
        surf = ctx["window"]

        if self.full_renderer and self.level_data and self.camera:
            self.full_renderer.render_to(
                surf,self.level_data,
                camera=self.camera,
                actors=self.actors if self.actors else None,
                active_gate_id=self.session.active_gate_id(self.players[0].race) if self.session else None,)
        else:
            surf.fill((20, 20, 20))
        
        self.render_ui(surf)
            
        end_frame()

    def render_ui(self, surf):
        player = self.players[0]
        draw_text(surf, "↻", self.icon_hud, (255, 255, 255), (5, 10))
        draw_text(surf, f"{player.race.laps_completed + 1}" + (f" / {self.session.target_laps}" if player.race.laps_completed < self.session.target_laps else ""), self.hud_font, (255, 255, 255), (55, 5))
        draw_text(surf, "⏱", self.icon_2_hud, (255, 255, 255), (5, 60))
        import math
        frac, whole = math.modf(self.session.elapsed_time)
        minutes = int(whole // 60)
        seconds = int(whole % 60)
        millis = int(frac * 1000)
        draw_text(surf, f"{minutes:02d}:{seconds:02d}.{millis:03d}", self.hud_font, (255, 255, 255), (55, 60))
        w, h = get_logical_size()
        oval_size = 265
        oval_pos = (w - 297, h - 280)
        speedometer = pygame.Surface((oval_size, oval_size), pygame.SRCALPHA)
        r = max(20, int(self.level_data["ground_r"] * 0.7))
        g = max(20, int(self.level_data["ground_g"] * 0.7))
        b = max(20, int(self.level_data["ground_b"] * 0.7))
        pygame.draw.ellipse(speedometer, (r, g, b, 128), (0, 0, oval_size, oval_size))
        surf.blit(speedometer, oval_pos)
        speed = player.car.mechanics.speed * player.car.mechanics.MOVE
        top_speed = player.car.stats.top_speed * player.car.mechanics.MOVE
        reverse_speed = abs(player.car.stats.top_speed * player.car.mechanics.REVERSE_CAP * player.car.mechanics.MOVE)
        converted_speed = str(abs(int(speed / 2)))
        center_text_on_oval(surf, converted_speed, self.hud_font, h - 190, oval_pos[0], oval_size, (255, 255, 255))
        center_text_on_oval(surf, "KPH", self.hud_font, h - 150, oval_pos[0], oval_size, (255, 255, 255))
        self._draw_speed_arc(surf, speed, [top_speed, reverse_speed], (255, 255, 255))

    def _draw_speed_arc(self, surface, speed, speed_thresholds, color):
        if speed == 0:
            return
        import math
        max_speed = speed_thresholds[0] if speed > 0 else speed_thresholds[1]
        speed = min(abs(speed), max_speed)
        arc_angle = int(360.0 * abs(speed / float(max_speed)))
        if arc_angle < 1:
            return
        speed_arc_x = 1627
        speed_arc_y = 804
        speed_arc_diameter = 265
        rect = pygame.Rect(speed_arc_x, speed_arc_y, speed_arc_diameter, speed_arc_diameter)
        start_angle = math.radians(270 - arc_angle)
        stop_angle = math.radians(270)
        pygame.draw.arc(surface, color, rect, start_angle, stop_angle, 8)
        
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
        old_pos = c.transform.pos
        c.mechanics.update(
            dt,
            stats=c.stats,
            transform=c.transform,
            inputs=controls,
            sprite_height_px=c.appearance.image.get_height(),
            on_road=is_on_road,
            surface_grip=1.0,
        )
        new_pos = c.transform.pos
        dx = new_pos[0] - old_pos[0]
        dy = new_pos[1] - old_pos[1]
        res = self.collision.resolve(c, old_pos, (dx, dy), dt, self.full_renderer, self.level_data)
        c.transform.pos = res.pos

    def _update_race(self, dt: float):
        if not (self.session and self.players and self.level_data):
            return

        self.session.tick(dt)

        for p in self.players:
            contacts = self.full_renderer.query_car_contacts(self.level_data, p.car)
            gate_id = contacts.get("gate_id")
            finished_now = self.session.step_player(p.id, p.race, gate_id)

            if finished_now:
                print(f"[race] FINISH! winner={self.session.winner_id} time={self.session.finish_time:.3f}s")