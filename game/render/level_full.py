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
        
    def render_to(self, target_surface, level_row, camera=None):
        code = level_row["code"]
        roads, trees, gates = _parse(code)
        bounds = _bounds(self.pieces, roads, trees, gates)
        tw, th = target_surface.get_size()
        avail_w = max(1, tw - self.margin*2)
        avail_h = max(1, th - self.margin*2 - self.hud_h)
        sx = avail_w / max(1, bounds.width)
        sy = avail_h / max(1, bounds.height)
        base_scale = min(sx, sy)
        cx, cy = tw//2, self.margin + int((avail_h)*0.5) + 80
        target_surface.fill((int(level_row["ground_r"]), int(level_row["ground_g"]), int(level_row["ground_b"])))
        if camera is None:
            camera = Camera2D()
            camera.fit_to_bounds((tw, th), bounds, self.margin, self.hud_h)
        for typ, x, y, ang in roads:
            img = self.pieces.get(f"road_{typ}")
            if img:
                _blit_transformed(target_surface, img, base_scale, camera, ang, x, y, (cx, cy))
        for order, x, y, ang in gates:
            img = self.pieces.get("gate")
            if img:
                _blit_transformed(target_surface, img, base_scale, camera, ang, x, y, (cx, cy))
        for typ, x, y in trees:
            img = self.pieces.get(f"tree_{typ}")
            if img:
                _blit_transformed(target_surface, img, base_scale, camera, 0, x, y, (cx, cy))