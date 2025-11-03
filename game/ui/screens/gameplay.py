import pygame

from game.io.render import end_frame, get_half_screen, get_logical_size
from game.core.model.car import DriveInput
from game.render.car_view import CarActor, CarRenderer
from game.render.level_full import Camera, LevelFullRenderer
from game.ui.screens.base_screen import BaseScreen
from game.rules.race import RaceSession
from game.ui.utils import draw_text, center_text_on_oval, draw_right
from game.ui.widgets.button import Button
from game.world.collision import CollisionResolver
from game.io.input import is_action_down
from game.core.engine.loop import get_fps

class Gameplay(BaseScreen):
    LAYER_NAME = "gameplay"
    BINDINGS = {"view": [("keydown", pygame.K_v)],
                "zoom_in": [("keydown", pygame.K_EQUALS), ("keydown", pygame.K_KP_PLUS)],
                "zoom_out": [("keydown", pygame.K_MINUS), ("keydown", pygame.K_KP_MINUS)],
                "rotate_camera_left": [("keydown", pygame.K_x)],
                "rotate_camera_right": [("keydown", pygame.K_z)],
                }

    def __init__(self, back_action=None, continue_action=None):
        super().__init__(back_action)
        self.continue_button = None
        self.continue_action = continue_action
        self.full_renderer = None
        self.car_renderer = CarRenderer()
        self.camera = None
        self.level_data = None
        self.players = []
        self.actors = []
        self.main_player_idx = 0
        self.keep_car_upright = True
        self._upright_lerp = 0.35
        self.cam_angle_offset = 0.0
        self.session = None
        self.collision = None
        self.icon_hud = None
        self.hud_font = None
        self._frame_contacts = {}
        self._speedometer_bg = None
        self._speedometer_bg_key = None

    def enter(self, ctx):
        super().enter(ctx)
        W, H = get_logical_size() 
        self.continue_button = Button((0,H-120,300,64), "Continue", self.font, (255,255,255), (30,30,30), (50,50,50), callback=lambda c: self._continue(c), center_mode="horizontal")
        self.continue_button.enter(ctx)

        payload = ctx.pop("gameplay", {}) or {}

        if self.full_renderer is None:
            self.full_renderer = LevelFullRenderer(ctx["pieces"])
        
        new_level = payload.get("level_data") or ctx.get("level_data") or self.level_data
        level_changed = (self.level_data or {}).get("id") != (new_level or {}).get("id")
        self.level_data = new_level

        if self.camera is None:
            self.camera = payload.get("camera") or self.camera or Camera()
        
        if (not self.players) and (payload.get("players") or ctx.get("players")):
            self.players = list(payload.get("players") or ctx.get("players") or [])
            self.actors = [CarActor(self.car_renderer, p.car) for p in self.players if getattr(p, "car", None)]

        if self.session is None or level_changed:
            gate_order = self._compute_gate_order()
            laps = int(self.level_data.get("laps", 1))
            self.session = RaceSession(target_laps=laps, gate_order=gate_order)
        
        if self.collision is None:
            self.collision = CollisionResolver()

        fonts = ctx.get("fonts", {})
        self.icon_hud = fonts.get("icon_hud")
        self.icon_2_hud = fonts.get("icon_2_hud")
        self.hud_font = fonts.get("hud")

        self._ensure_speedometer_bg()

    def _continue(self, ctx):
        if self.continue_action:
            self.continue_action(ctx)

    def on_resize(self, ctx, size):
        super().on_resize(ctx, size)
        self._ensure_speedometer_bg()
        W, H = get_logical_size()
        if self.continue_button:
            self.continue_button.set_rect((0, H - 120, 300, 64))

    def update(self, ctx, dt):
        actions = self.step(ctx)
        if actions is None:
            return False
        for name, phase, payload in actions:
            if name == "view" and phase == "press":
                self.keep_car_upright = not self.keep_car_upright
        if self.continue_button.update(ctx, actions):
            self._continue(ctx)
        if (self.session is None) or (self.session.winner_id is None) and self.handle_back(ctx, actions):
            return True

        self._apply_camera_zoom(dt)
        self._apply_camera_rotation(dt)
        self._step_physics(dt)
        self._update_race(dt)
        self._focus_camera_on_main_player()
        return True

    def render(self, ctx):
        surf = ctx["window"]

        if self.full_renderer and self.level_data and self.camera:
            active_gate = None
            if self.session and self.players:
                active_gate = self.session.active_gate_id(self.players[self.main_player_idx].race)
            self.full_renderer.render_to(
                surf,self.level_data,
                camera=self.camera,
                actors=self.actors if self.actors else None,
                active_gate_id=active_gate)
        else:
            surf.fill((20, 20, 20))
        
        self.render_ui(surf, ctx)
        end_frame()

    def render_ui(self, surf, ctx):
        if not self.players:
            return
        player = self.players[self.main_player_idx]
        draw_text(surf, "↻", self.icon_hud, (255, 255, 255), (5, 10))
        draw_text(surf, f"{player.race.laps_completed + 1}" + (f" / {self.session.target_laps}" if player.race.laps_completed < self.session.target_laps else ""), self.hud_font, (255, 255, 255), (55, 5))
        draw_text(surf, "⏱", self.icon_2_hud, (255, 255, 255), (5, 60))
        draw_right(surf, 10, str(player.race.score), self.hud_font, (255, 255, 255))
        draw_text(surf, f"{self.camera.zoom}", self.font, (255, 255, 255), (5, 300))
        draw_text(surf, f"{int(get_fps())}", self.font, (255, 255, 255), (5, 400))
        import math
        frac, whole = math.modf(self.session.elapsed_time)
        minutes = int(whole // 60)
        seconds = int(whole % 60)
        millis = int(frac * 1000)
        draw_text(surf, f"{minutes:02d}:{seconds:02d}.{millis:03d}", self.hud_font, (255, 255, 255), (55, 60))
        w, h = get_logical_size()
        oval_size = 265
        oval_pos = (w - 297, h - 280)
        self._ensure_speedometer_bg(oval_size)
        if self._speedometer_bg:
            surf.blit(self._speedometer_bg, oval_pos)

        speed = player.car.mechanics.speed * player.car.mechanics.MOVE
        top_speed = player.car.stats.top_speed * player.car.mechanics.MOVE
        reverse_speed = abs(player.car.stats.top_speed * player.car.mechanics.REVERSE_CAP * player.car.mechanics.MOVE)
        converted_speed = str(abs(int(speed / 2)))
        center_text_on_oval(surf, converted_speed, self.hud_font, h - 190, oval_pos[0], oval_size, (255, 255, 255))
        center_text_on_oval(surf, "KPH", self.hud_font, h - 150, oval_pos[0], oval_size, (255, 255, 255))
        self._draw_speed_arc(surf, speed, [top_speed, reverse_speed], (255, 255, 255))
        self._render_finish_banner(surf, ctx)

    def _render_finish_banner(self, surf, ctx):
        if not (self.session and self.session.winner_id is not None):
            return
        winner = self.players[self.main_player_idx].id == self.session.winner_id
        winner_id = self.session.winner_id
        half_W, half_H = get_half_screen()
        draw_text(surf, "YOU WON!" if winner else "YOU LOST!", self.title_font, (255, 255, 255), (half_W, 100), centered=True)
        mp = ctx["get_mouse_pos"]()
        self.continue_button.draw(surf, mp)
    
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

    def _ensure_speedometer_bg(self, oval_size=265):
        if not self.level_data:
            return
        r = max(20, int(self.level_data["ground_r"] * 0.7))
        g = max(20, int(self.level_data["ground_g"] * 0.7))
        b = max(20, int(self.level_data["ground_b"] * 0.7))
        key = (r, g, b, oval_size)
        if key == self._speedometer_bg_key and self._speedometer_bg is not None:
            return
        surf = pygame.Surface((oval_size, oval_size), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (r, g, b, 128), (0, 0, oval_size, oval_size))
        self._speedometer_bg = surf
        self._speedometer_bg_key = key
        
    @staticmethod
    def _lerp_deg(a, b, t):
        d = ((b - a + 180.0) % 360.0) - 180.0
        return a + d * t

    def _focus_camera_on_main_player(self):
        if not (self.camera and self.players):
            return
        player = self.players[self.main_player_idx]
        if not getattr(player, "car", None):
            return
        pos = pygame.Vector2(player.car.transform.pos)

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
            base = float(player.car.transform.angle_deg)
            target = (base + self.cam_angle_offset) % 360.0
            self.camera.rot_deg = self._lerp_deg(float(self.camera.rot_deg), target, self._upright_lerp)

    def _get_input_for_player(self, idx: int) -> DriveInput:
        if idx == self.main_player_idx:
            return DriveInput(
                up=is_action_down("up"),
                down=is_action_down("down"),
                left=is_action_down("left"),
                right=is_action_down("right"),
                brake=is_action_down("space"),
            )
        return DriveInput()

    def _apply_camera_zoom(self, dt: float):
        MIN_ZOOM, MAX_ZOOM= 0.05, 5.0
        ZOOM_RATE = 1.5

        zoom_in_down  = is_action_down("zoom_in")
        zoom_out_down = is_action_down("zoom_out")
        if zoom_in_down and zoom_out_down:
            self.camera.zoom = Camera.DEFAULT_ZOOM
            return
        z = self.camera.zoom
        if zoom_in_down:
            z *= (1.0 + ZOOM_RATE * dt)
        elif zoom_out_down:
            z /= (1.0 + ZOOM_RATE * dt)
        self.camera.zoom = max(MIN_ZOOM, min(MAX_ZOOM, z))

    def _wrap_deg(self, a: float) -> float:
        return ((a + 180.0) % 360.0) - 180.0

    def _apply_camera_rotation(self, dt: float):
        ROTATE_RATE = 120.0

        left = is_action_down("rotate_camera_left")
        right = is_action_down("rotate_camera_right")

        if left and right:
            if self.keep_car_upright:
                self.cam_angle_offset = 0.0
            else:
                self.camera.rot_deg = 0.0
            return

        if self.keep_car_upright:
            if left:
                self.cam_angle_offset = self._wrap_deg(self.cam_angle_offset - ROTATE_RATE * dt)
            elif right:
                self.cam_angle_offset = self._wrap_deg(self.cam_angle_offset + ROTATE_RATE * dt)
        else:
            if left:
                self.camera.rot_deg -= ROTATE_RATE * dt
            elif right:
                self.camera.rot_deg += ROTATE_RATE * dt
            self.camera.rot_deg %= 360.0

    def _step_physics(self, dt: float):
        if not (self.players and self.full_renderer and self.level_data):
            return
        self._frame_contacts.clear()
        for idx, p in enumerate(self.players):
            car = p.car
            if not car:
                continue

            controls = self._get_input_for_player(idx)

            contacts_pre = self.full_renderer.query_car_contacts(self.level_data, car)
            is_on_road = bool(contacts_pre.get("on_road"))

            old_pos = car.transform.pos
            car.mechanics.update(
                dt,
                stats=car.stats,
                transform=car.transform,
                inputs=controls,
                sprite_height_px=car.appearance.image.get_height() if car.appearance else 0,
                on_road=is_on_road,
                surface_grip=1.0,
            )

            new_pos = car.transform.pos
            dx = new_pos[0] - old_pos[0]
            dy = new_pos[1] - old_pos[1]
            res = self.collision.resolve(car, old_pos, (dx, dy), dt, self.full_renderer, self.level_data)
            car.transform.pos = res.pos

            contacts_post = self.full_renderer.query_car_contacts(self.level_data, car)
            self._frame_contacts[p.id] = contacts_post

    def _update_race(self, dt: float):
        if not (self.session and self.players and self.level_data):
            return
        self.session.tick(dt)
        for p in self.players:
            contacts = self._frame_contacts.get(p.id) or self.full_renderer.query_car_contacts(self.level_data, p.car)
            gate_id = contacts.get("gate_id")
            self.session.step_player(p.id, p.race, gate_id)

    def _compute_gate_order(self):
        get_public = getattr(self.full_renderer, "get_gate_order", None)
        if callable(get_public):
            return list(get_public(self.level_data))

        entry = self.full_renderer._get_world(self.level_data)
        return [order for (order, _, _, _) in sorted(entry.get("gates", ()), key=lambda g: g[0])]