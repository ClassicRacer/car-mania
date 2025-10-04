import math
import pygame

from game.render.camera import Camera
from game.render.level_utils import compute_piece_bounds, parse_level_code

class LevelFullRenderer:
    def __init__(self, pieces, margin_px=40, hud_h=240, origin_offset=None):
        self.pieces = pieces
        self.margin = margin_px
        self.hud_h = hud_h

        if origin_offset is None:
            road = self.pieces.get("road_1")
            if road:
                default_offset = (-road.get_width() * 0.33, 0.0)
            else:
                default_offset = (0.0, 0.0)
        else:
            default_offset = origin_offset

        self.origin_offset = pygame.Vector2(default_offset)
        self._cache = {}

    def set_origin_offset(self, offset):
        self.origin_offset = pygame.Vector2(offset)
        return self.origin_offset

    def _build_world(self, level_row, seed=None):
        code = level_row.get("code", "")
        seed_to_use = seed if seed is not None else level_row.get("_maze_seed")
        roads, trees, gates, extra = parse_level_code(code, seed=seed_to_use)
        if extra and "seed" in extra:
            actual_seed = extra["seed"]
        else:
            actual_seed = seed_to_use
        if actual_seed is not None:
            level_row["_maze_seed"] = actual_seed

        bounds = compute_piece_bounds(self.pieces, roads, trees, gates)

        world = pygame.Surface((bounds.w, bounds.h), pygame.SRCALPHA).convert_alpha()
        bg = (
            int(level_row["ground_r"]),
            int(level_row["ground_g"]),
            int(level_row["ground_b"]),
        )
        world.fill((0, 0, 0, 0))

        ox, oy = -bounds.x, -bounds.y
        for t, x, y, ang in roads:
            key = t if isinstance(t, str) else f"road_{t}"
            img = self.pieces.get(key)
            if img:
                world.blit(pygame.transform.rotate(img, ang), (x + ox, y + oy))
        for order, x, y, ang in gates:
            img = self.pieces.get("gate")
            if img:
                world.blit(pygame.transform.rotate(img, ang), (x + ox, y + oy))
        for t, x, y in trees:
            img = self.pieces.get(f"tree_{t}")
            if img:
                world.blit(img, (x + ox, y + oy))

        entry = {
            "world": world,
            "bounds": bounds,
            "bg": bg,
            "roads": tuple(roads),
            "trees": tuple(trees),
            "gates": tuple(gates),
            "extra": extra,
            "seed": actual_seed,
            "scaled_surface": None,
            "scaled_size": None,
        }
        return entry

    def _get_world(self, level_row):
        lid = level_row.get("id", None)
        entry = self._cache.get(lid)
        if entry is None:
            entry = self._build_world(level_row)
            self._cache[lid] = entry
        else:
            if entry.get("seed") is not None:
                level_row["_maze_seed"] = entry["seed"]
            if "scaled_surface" not in entry:
                entry["scaled_surface"] = None
            if "scaled_size" not in entry:
                entry["scaled_size"] = None
        return entry

    def refresh_level(self, level_row, *, seed=None):
        lid = level_row.get("id", None)
        if lid in self._cache:
            self._cache.pop(lid)
        if seed is None:
            level_row.pop("_maze_seed", None)
        else:
            level_row["_maze_seed"] = seed
        entry = self._build_world(level_row, seed=seed)
        self._cache[lid] = entry
        return entry

    def get_piece_bounds(self, level_row):
        entry = self._get_world(level_row)
        return entry["bounds"]

    def focus_camera(self, camera, level_row, reset_zoom=True, reset_rotation=True):
        entry = self._get_world(level_row)
        world = entry["world"]
        ww, wh = world.get_size()
        camera.x = ww * 0.5 + self.origin_offset.x
        camera.y = wh * 0.5 + self.origin_offset.y
        if reset_zoom:
            camera.zoom = 1.0
        if reset_rotation:
            camera.rot_deg = 0.0

    def render_to(self, target_surface, level_row, camera=None, actors=None):
        tw, th = target_surface.get_size()

        entry = self._get_world(level_row)
        world = entry["world"]
        bounds = entry["bounds"]
        bg = entry["bg"]
        ww, wh = world.get_size()

        avail_w = max(1, tw - self.margin*2)
        avail_h = max(1, th - self.margin*2 - self.hud_h)
        fit_zoom = min(avail_w / ww, avail_h / wh)

        if camera is None:
            camera = Camera(x=ww*0.5, y=wh*0.5, zoom=fit_zoom, rot_deg=0.0)

        offset_x, offset_y = self.origin_offset

        pivot = (tw // 2, th // 2)
        zoom = max(1e-6, camera.zoom)
        angle = camera.rot_deg % 360.0
        angle_eps = 1e-3

        full_scale_needed = zoom <= 1.0 or not (angle <= angle_eps or angle >= 360.0 - angle_eps)

        scaled = world
        if full_scale_needed:
            target_scaled_size = (max(1, int(round(ww * zoom))), max(1, int(round(wh * zoom))))
            if entry["scaled_size"] != target_scaled_size:
                if target_scaled_size == (ww, wh):
                    scaled = world
                else:
                    if zoom < 1.0:
                        scaled = pygame.transform.smoothscale(world, target_scaled_size)
                    else:
                        scaled = pygame.transform.scale(world, target_scaled_size)
                entry["scaled_surface"] = scaled
                entry["scaled_size"] = target_scaled_size
            else:
                scaled = entry["scaled_surface"] or world

        target_surface.fill(bg)

        cam_x = camera.x - offset_x
        cam_y = camera.y - offset_y

        if angle <= angle_eps or angle >= 360.0 - angle_eps:
            if full_scale_needed:
                top_left = (
                    int(round(pivot[0] - cam_x * zoom)),
                    int(round(pivot[1] - cam_y * zoom)),
                )
                target_surface.blit(scaled, top_left)
                if actors:
                    actors_top_left = (
                        top_left[0] - int(round(bounds.x * zoom)),
                        top_left[1] - int(round(bounds.y * zoom)),
                    )
                    for actor in actors:
                        if hasattr(actor, "render_in_canvas_space"):
                            actor.render_in_canvas_space(target_surface, actors_top_left, zoom)
                return
            else:
                pad = 4
                view_w = max(1, int(math.ceil(tw / zoom)))
                view_h = max(1, int(math.ceil(th / zoom)))
                view_left = int(math.floor(camera.x - view_w * 0.5)) - pad
                view_top = int(math.floor(camera.y - view_h * 0.5)) - pad
                view_rect = pygame.Rect(view_left, view_top, view_w + pad * 2, view_h + pad * 2)
                world_rect = world.get_rect()
                view_rect = view_rect.clip(world_rect)
                if view_rect.width <= 0 or view_rect.height <= 0:
                    view_rect = world_rect
                view = world.subsurface(view_rect)
                scaled_size = (
                    max(1, int(round(view_rect.width * zoom))),
                    max(1, int(round(view_rect.height * zoom))),
                )
                if zoom != 1.0:
                    view = pygame.transform.scale(view, scaled_size)
                screen_pos = (
                    int(round(pivot[0] - (cam_x - view_rect.x) * zoom)),
                    int(round(pivot[1] - (cam_y - view_rect.y) * zoom)),
                )
                target_surface.blit(view, screen_pos)
                if actors:
                    actors_top_left = (
                        screen_pos[0] - int(round((view_rect.x + bounds.x) * zoom)),
                        screen_pos[1] - int(round((view_rect.y + bounds.y) * zoom)),
                    )
                    for actor in actors:
                        if hasattr(actor, "render_in_canvas_space"):
                            actor.render_in_canvas_space(target_surface, actors_top_left, zoom)
                return

        diag = int(math.ceil(math.hypot(tw, th)))
        canvas = pygame.Surface((diag, diag), pygame.SRCALPHA).convert_alpha()
        canvas.fill((0, 0, 0, 0))

        cxc = cyc = diag // 2
        top_left = (
            int(round(cxc - cam_x * zoom)),
            int(round(cyc - cam_y * zoom)),
        )
        canvas.blit(scaled, top_left)
        if actors:
            actors_top_left = (
                top_left[0] - int(round(bounds.x * zoom)),
                top_left[1] - int(round(bounds.y * zoom)),
            )
            for actor in actors:
                if hasattr(actor, "render_in_canvas_space"):
                    actor.render_in_canvas_space(canvas, actors_top_left, zoom)

        rotated = pygame.transform.rotate(canvas, angle)
        target_surface.blit(rotated, rotated.get_rect(center=pivot))
