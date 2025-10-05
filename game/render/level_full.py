import math
import pygame

from game.render.camera import Camera
from game.render.level_utils import compute_piece_bounds, parse_level_code

def _scaled(img: pygame.Surface, s: float) -> pygame.Surface:
    if abs(s - 1.0) <= 1e-3:
        return img
    w, h = img.get_size()
    return pygame.transform.smoothscale(img, (max(1, int(round(w*s))), max(1, int(round(h*s)))))

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
        w, h = bounds.w, bounds.h
        world = pygame.Surface((w, h), pygame.SRCALPHA).convert_alpha()
        road_surf = pygame.Surface((w, h), pygame.SRCALPHA).convert_alpha()
        gate_surf = pygame.Surface((w, h), pygame.SRCALPHA).convert_alpha()
        tree_surf = pygame.Surface((w, h), pygame.SRCALPHA).convert_alpha()
        wall_surf  = pygame.Surface((w, h), pygame.SRCALPHA).convert_alpha()

        bg = (int(level_row["ground_r"]), int(level_row["ground_g"]), int(level_row["ground_b"]))
        for s in (world, road_surf, gate_surf, tree_surf, wall_surf):
            s.fill((0, 0, 0, 0))

        ox, oy = -bounds.x, -bounds.y
        gate_masks = []

        for t,x,y,ang in roads:
            key = t if isinstance(t, str) else f"road_{t}"
            img = self.pieces.get(key)
            if not img:
                continue
            r = pygame.transform.rotate(img, ang)
            pos = (x+ox, y+oy)
            world.blit(r, pos)
            if key in ("road_1", "road_2", "maze_grid"):
                road_surf.blit(r, pos)
            elif key == "maze_wall":
                wall_surf.blit(r, pos)

        gate_img = self.pieces.get("gate") or self.pieces.get("gate_active")
        for order, x, y, ang in gates:
            if not gate_img:
                continue
            r = pygame.transform.rotate(gate_img, ang)
            pos = (x + ox, y + oy)
            world.blit(r, pos)
            gate_surf.blit(r, pos)
            grect = r.get_rect(topleft=pos)
            gmask = pygame.mask.from_surface(r)
            gate_masks.append((order, gmask, grect))

        for t,x,y in trees:
            img = self.pieces.get(f"tree_{t}")
            if img:
                pos = (x+ox, y+oy)
                world.blit(img, pos)
                tree_surf.blit(img, pos)

        occluder_surf = pygame.Surface((w, h), pygame.SRCALPHA).convert_alpha()
        occluder_surf.fill((0, 0, 0, 0))
        occluder_surf.blit(wall_surf, (0, 0))
        occluder_surf.blit(gate_surf, (0, 0))
        occluder_surf.blit(tree_surf, (0, 0))

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

            "road_mask": pygame.mask.from_surface(road_surf),
            "gate_mask": pygame.mask.from_surface(gate_surf),
            "tree_mask": pygame.mask.from_surface(tree_surf),
            "wall_mask": pygame.mask.from_surface(wall_surf),
            "gate_masks": tuple(gate_masks),

            "occluder_surface": occluder_surf,
            "scaled_occ_surface": None,
            "scaled_occ_size": None,
        }
        return entry
    
    def query_car_contacts(self, level_row, car) -> dict:
        entry = self._get_world(level_row)
        bounds = entry["bounds"]

        t = car.transform
        a = car.appearance
        img = a.image
        s = float(t.scale)
        if abs(s - 1.0) > 1e-3:
            w, h = img.get_size()
            spr = pygame.transform.smoothscale(img, (max(1, int(round(w*s))), max(1, int(round(h*s)))))
        else:
            spr = img

        rotated = pygame.transform.rotate(spr, -t.angle_deg)
        cx = int(round(t.pos[0] - bounds.x))
        cy = int(round(t.pos[1] - bounds.y))
        rect = rotated.get_rect(center=(cx, cy))
        car_mask = pygame.mask.from_surface(rotated)

        off = (-rect.left, -rect.top)

        on_road  = bool(car_mask.overlap(entry["road_mask"], off))
        hit_gate = bool(car_mask.overlap(entry["gate_mask"], off))
        hit_tree = bool(car_mask.overlap(entry["tree_mask"], off))

        wall_mask = entry.get("wall_mask")
        hit_wall = False
        if wall_mask:
            # treat as "no walls" if the mask is empty
            has_bits = False
            if hasattr(wall_mask, "count"):
                has_bits = wall_mask.count() > 0
            else:
                has_bits = len(wall_mask.get_bounding_rects()) > 0
            if has_bits:
                hit_wall = bool(car_mask.overlap(wall_mask, off))

        gate_id = None
        if hit_gate:
            for gid, gmask, grect in entry["gate_masks"]:
                if car_mask.overlap(gmask, (grect.left - rect.left, grect.top - rect.top)):
                    gate_id = gid
                    break

        return {
            "on_road": on_road,
            "hit_tree": hit_tree,
            "hit_gate": hit_gate,
            "gate_id": gate_id,
            "hit_wall": hit_wall,
        }

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

    def render_to(self, target_surface, level_row, camera=None, actors=None, active_gate_id=None):
        tw, th = target_surface.get_size()

        entry = self._get_world(level_row)
        world = entry["world"]
        bounds = entry["bounds"]
        bg = entry["bg"]
        ww, wh = world.get_size()

        if "occluder_surface" not in entry or entry["occluder_surface"] is None:
            occ = pygame.Surface((ww, wh), pygame.SRCALPHA).convert_alpha()
            occ.fill((0, 0, 0, 0))
            entry["occluder_surface"] = occ
        if "scaled_occ_surface" not in entry:
            entry["scaled_occ_surface"] = None
        if "scaled_occ_size" not in entry:
            entry["scaled_occ_size"] = None

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

        def scale_world(target_size):
            if entry["scaled_size"] != target_size:
                if target_size == (ww, wh):
                    scaled_w = world
                else:
                    if zoom < 1.0:
                        scaled_w = pygame.transform.smoothscale(world, target_size)
                    else:
                        scaled_w = pygame.transform.scale(world, target_size)
                entry["scaled_surface"] = scaled_w
                entry["scaled_size"] = target_size
                return scaled_w
            return entry["scaled_surface"] or world
        
        def scale_occluder(target_size):
            occ = entry["occluder_surface"]
            if entry["scaled_occ_size"] != target_size:
                if target_size == occ.get_size():
                    scaled_o = occ
                else:
                    if zoom < 1.0:
                        scaled_o = pygame.transform.smoothscale(occ, target_size)
                    else:
                        scaled_o = pygame.transform.scale(occ, target_size)
                entry["scaled_occ_surface"] = scaled_o
                entry["scaled_occ_size"] = target_size
                return scaled_o
            return entry["scaled_occ_surface"] or occ
        
        def _draw_active_gate(dest, top_left_px, view_rect=None):
            if active_gate_id is None:
                return
            gimg = self.pieces.get("gate_active")
            if not gimg:
                return
            gx = gy = gang = None
            for order, x, y, ang in entry["gates"]:
                if order == active_gate_id:
                    gx, gy, gang = x, y, ang
                    break
            if gx is None:
                return
            gspr = pygame.transform.rotate(gimg, gang)
            if abs(zoom - 1.0) > 1e-3:
                rw, rh = gspr.get_size()
                gspr = pygame.transform.smoothscale(
                    gspr, (max(1, int(round(rw * zoom))), max(1, int(round(rh * zoom))))
                )

            ox, oy = -bounds.x, -bounds.y
            wx = (gx + ox) * zoom
            wy = (gy + oy) * zoom
            if view_rect is not None:
                wx -= view_rect.x * zoom
                wy -= view_rect.y * zoom

            grect = gspr.get_rect(topleft=(int(round(top_left_px[0] + wx)), int(round(top_left_px[1] + wy))))
            dest.blit(gspr, grect)
            
        target_surface.fill(bg)

        cam_x = camera.x - offset_x
        cam_y = camera.y - offset_y

        if angle <= angle_eps or angle >= 360.0 - angle_eps:
            if full_scale_needed:
                target_scaled_size = (max(1, int(round(ww * zoom))), max(1, int(round(wh * zoom))))
                scaled = scale_world(target_scaled_size)

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

                occ_scaled = scale_occluder(target_scaled_size)
                target_surface.blit(occ_scaled, top_left)
                _draw_active_gate(target_surface, top_left)
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

                occ_view = entry["occluder_surface"].subsurface(view_rect)
                if zoom != 1.0:
                    occ_view = pygame.transform.scale(occ_view, scaled_size)
                target_surface.blit(occ_view, screen_pos)
                _draw_active_gate(target_surface, screen_pos, view_rect=view_rect)
                return

        diag = int(math.ceil(math.hypot(tw, th)))
        canvas = pygame.Surface((diag, diag), pygame.SRCALPHA).convert_alpha()
        canvas.fill((0, 0, 0, 0))

        cxc = cyc = diag // 2
        top_left = (
            int(round(cxc - cam_x * zoom)),
            int(round(cyc - cam_y * zoom)),
        )
        if full_scale_needed:
            target_scaled_size = (max(1, int(round(ww * zoom))), max(1, int(round(wh * zoom))))
            scaled = scale_world(target_scaled_size)
            occ_scaled = scale_occluder(target_scaled_size)
        else:
            scaled = world
            occ_scaled = entry["occluder_surface"]
        canvas.blit(scaled, top_left)
        if actors:
            actors_top_left = (
                top_left[0] - int(round(bounds.x * zoom)),
                top_left[1] - int(round(bounds.y * zoom)),
            )
            for actor in actors:
                if hasattr(actor, "render_in_canvas_space"):
                    actor.render_in_canvas_space(canvas, actors_top_left, zoom)
        canvas.blit(occ_scaled, top_left)
        _draw_active_gate(canvas, top_left)
        rotated = pygame.transform.rotate(canvas, angle)
        target_surface.blit(rotated, rotated.get_rect(center=pivot))
