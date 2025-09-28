import pygame

def parse_level_code(code_text: str):
    roads = []
    trees = []
    gates = []
    if not code_text:
        return roads, trees, gates, None
    lines = [ln.strip() for ln in code_text.splitlines() if ln.strip()]
    for ln in lines:
        parts = ln.split(",")
        k = parts[0]
        if k == "road" and len(parts) >= 5:
            t = int(parts[1])
            x = int(parts[2])
            y = -int(parts[3])
            ang = int(parts[4])
            roads.append((t, x, y, ang))
        elif k == "tree" and len(parts) >= 4:
            t = int(parts[1])
            x = int(parts[2])
            y = -int(parts[3])
            trees.append((t, x, y))
        elif k == "gate" and len(parts) >= 5:
            order = int(parts[1])
            x = int(parts[2])
            y = -int(parts[3])
            ang = int(parts[4])
            gates.append((order, x, y, ang))
    return roads, trees, gates, None

class LevelPreviewRenderer:
    def __init__(self, pieces: dict, target_size=(480, 270)):
        self.pieces = pieces
        self.size = target_size

    def _bounds(self, roads, trees, gates):
        pts = []
        def add_rect(w, h, x, y):
            pts.append((x, y))
            pts.append((x + w, y + h))
        for t,x,y,ang in roads:
            img = self.pieces.get(f"road_{t}")
            if img:
                w,h = img.get_size()
                add_rect(w,h,x,y)
        for t,x,y in trees:
            img = self.pieces.get(f"tree_{t}")
            if img:
                w,h = img.get_size()
                add_rect(w,h,x,y)
        for order,x,y,ang in gates:
            img = self.pieces.get("gate")
            if img:
                w,h = img.get_size()
                add_rect(w,h,x,y)
        if not pts:
            return pygame.Rect(0,0,1,1)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        r = pygame.Rect(min(xs), min(ys), 1, 1)
        r.width = max(xs) - r.x or 1
        r.height = max(ys) - r.y or 1
        return r

    def render(self, level_row: dict):
        surf = pygame.Surface(self.size, pygame.SRCALPHA)
        bg = (int(level_row["ground_r"]), int(level_row["ground_g"]), int(level_row["ground_b"]))
        surf.fill(bg)
        roads, trees, gates, _ = parse_level_code(level_row["code"])
        bounds = self._bounds(roads, trees, gates)
        pad = 20
        vw = self.size[0] - pad*2
        vh = self.size[1] - pad*2
        sx = vw / bounds.w
        sy = vh / bounds.h
        s = min(sx, sy)
        ox = pad + (vw - bounds.w * s) * 0.5
        oy = pad + (vh - bounds.h * s) * 0.5
        def to_screen(x, y):
            return int(ox + (x - bounds.x) * s), int(oy + (y - bounds.y) * s)
        def blit_scaled(img, pos, angle=0):
            w,h = img.get_size()
            iw = max(1, int(w * s))
            ih = max(1, int(h * s))
            pic = pygame.transform.scale(img, (iw, ih))
            if angle:
                pic = pygame.transform.rotate(pic, angle)
            r = pic.get_rect()
            r.topleft = pos
            surf.blit(pic, r)
        for t,x,y,ang in roads:
            img = self.pieces.get(f"road_{t}")
            if img:
                blit_scaled(img, to_screen(x,y), ang)
        for order,x,y,ang in gates:
            img = self.pieces.get("gate")
            if img:
                blit_scaled(img, to_screen(x,y), ang)
        for t,x,y in trees:
            img = self.pieces.get(f"tree_{t}")
            if img:
                blit_scaled(img, to_screen(x,y))
        return surf