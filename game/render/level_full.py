import math
import pygame

class Camera2D:
    def __init__(self, x=0.0, y=0.0, zoom=1.0, rot_deg=0.0):
        self.x = float(x)
        self.y = float(y)
        self.zoom = float(zoom)
        self.rot_deg = float(rot_deg)

    def fit_to_bounds(self, surf_size, bounds, margin_px=40, hud_h=240):
        tw, th = surf_size
        avail_w = max(1, tw - margin_px*2)
        avail_h = max(1, th - margin_px*2 - hud_h)
        sx = avail_w / max(1, bounds.width)
        sy = avail_h / max(1, bounds.height)
        self.zoom = min(sx, sy)
        self.x = bounds.centerx
        self.y = bounds.centery
        self.rot_deg = 0.0

def _parse(code_text):
    roads, trees, gates = [], [], []
    for raw in code_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        p = [x.strip() for x in line.split(",")]
        t = p[0]
        if t == "road":
            roads.append((int(p[1]), int(p[2]), -int(p[3]), int(p[4])))
        elif t == "tree":
            trees.append((int(p[1]), int(p[2]), -int(p[3])))
        elif t == "gate":
            gates.append((int(p[1]), int(p[2]), -int(p[3]), int(p[4])))
    return roads, trees, gates

def _bounds(pieces, roads, trees, gates):
    pts = []
    def add_rect(w, h, x, y):
        pts.append((x, y))
        pts.append((x + w, y + h))
    for typ, x, y, ang in roads:
        img = pieces.get(f"road_{typ}")
        if img:
            w, h = img.get_size()
            add_rect(w, h, x, y)
    for typ, x, y in trees:
        img = pieces.get(f"tree_{typ}")
        if img:
            w, h = img.get_size()
            add_rect(w, h, x, y)
    for order, x, y, ang in gates:
        img = pieces.get("gate")
        if img:
            w, h = img.get_size()
            add_rect(w, h, x, y)
    if not pts:
        return pygame.Rect(0, 0, 1, 1)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    r = pygame.Rect(min(xs), min(ys), 1, 1)
    r.width = max(xs) - r.x or 1
    r.height = max(ys) - r.y or 1
    return r

def _world_to_screen(x, y, cam, surf_center, base_zoom=1.0):
    s = base_zoom * cam.zoom
    r = math.radians(cam.rot_deg)
    dx = x - cam.x
    dy = y - cam.y
    rx = dx*math.cos(r) - dy*math.sin(r)
    ry = dx*math.sin(r) + dy*math.cos(r)
    sx = surf_center[0] + rx*s
    sy = surf_center[1] + ry*s
    return s, sx, sy

def _blit_transformed(surf, img, base_scale, cam, ang, x, y, surf_center):
    s, sx, sy = _world_to_screen(x, y, cam, surf_center, base_scale)
    if s != 1.0:
        w, h = img.get_size()
        img = pygame.transform.smoothscale(img, (max(1, int(w*s)), max(1, int(h*s))))
    if ang or cam.rot_deg:
        img = pygame.transform.rotate(img, ang + cam.rot_deg)
    rect = img.get_rect()
    rect.topleft = (int(sx), int(sy))
    surf.blit(img, rect)

class LevelFullRenderer:
    def __init__(self, pieces, margin_px=40, hud_h=240):
        self.pieces = pieces
        self.margin = margin_px
        self.hud_h = hud_h
        self._cache = {}  # level_id -> {"world":surf, "bounds":rect, "bg":(r,g,b)}

    def _build_world(self, level_row):
        # Parse and measure
        roads, trees, gates = _parse(level_row["code"])
        # Compute bounds using unrotated piece sizes (same as your preview)
        pts = []
        def add_rect(w,h,x,y):
            pts.append((x,y)); pts.append((x+w, y+h))
        for t,x,y,ang in roads:
            img = self.pieces.get(f"road_{t}"); 
            if img: add_rect(*img.get_size(), x, y)
        for t,x,y in trees:
            img = self.pieces.get(f"tree_{t}");
            if img: add_rect(*img.get_size(), x, y)
        for _,x,y,ang in gates:
            img = self.pieces.get("gate");
            if img: add_rect(*img.get_size(), x, y)

        if not pts:
            bounds = pygame.Rect(0,0,1,1)
        else:
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            bounds = pygame.Rect(min(xs), min(ys), 1, 1)
            bounds.width  = max(xs) - bounds.x or 1
            bounds.height = max(ys) - bounds.y or 1

        # Bake level to a world surface at native resolution
        world = pygame.Surface((bounds.w, bounds.h), pygame.SRCALPHA).convert_alpha()
        bg = (int(level_row["ground_r"]), int(level_row["ground_g"]), int(level_row["ground_b"]))
        world.fill((0,0,0,0))

        # Blit all pieces *unrotated* at native scale, offset by -bounds.topleft
        ox, oy = -bounds.x, -bounds.y
        for t,x,y,ang in roads:
            img = self.pieces.get(f"road_{t}")
            if img:
                world.blit(pygame.transform.rotate(img, ang), (x+ox, y+oy))
        for order,x,y,ang in gates:
            img = self.pieces.get("gate")
            if img:
                world.blit(pygame.transform.rotate(img, ang), (x+ox, y+oy))
        for t,x,y in trees:
            img = self.pieces.get(f"tree_{t}")
            if img:
                world.blit(img, (x+ox, y+oy))

        return world, bounds, bg

    def _get_world(self, level_row):
        lid = level_row.get("id", None)
        entry = self._cache.get(lid)
        if entry is None:
            world, bounds, bg = self._build_world(level_row)
            entry = {"world": world, "bounds": bounds, "bg": bg}
            self._cache[lid] = entry
        return entry

    def render_to(self, target_surface, level_row, camera=None):
        tw, th = target_surface.get_size()

        entry = self._get_world(level_row)
        world = entry["world"]
        bg = entry["bg"]
        ww, wh = world.get_size()

        avail_w = max(1, tw - self.margin*2)
        avail_h = max(1, th - self.margin*2 - self.hud_h)
        base_scale = min(avail_w / ww, avail_h / wh)

        if camera is None:
            camera = Camera2D(x=ww*0.5, y=wh*0.5, zoom=1.0, rot_deg=0.0)

        pivot = (tw // 2, th // 2)
        zoom = base_scale * camera.zoom

        diag = int(math.ceil(math.hypot(tw, th)))
        canvas = pygame.Surface((diag, diag), pygame.SRCALPHA).convert_alpha()
        canvas.fill((0, 0, 0, 0))

        scaled = pygame.transform.smoothscale(world, (max(1, int(ww*zoom)), max(1, int(wh*zoom))))

        cxc, cyc = diag // 2, diag // 2
        top_left = (cxc - camera.x * zoom, cyc - camera.y * zoom)
        canvas.blit(scaled, top_left)

        rotated = pygame.transform.rotate(canvas, camera.rot_deg)

        target_surface.fill(bg)
        target_surface.blit(rotated, rotated.get_rect(center=pivot))