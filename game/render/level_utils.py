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


def compute_piece_bounds(pieces: dict, roads, trees, gates):
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
    rect = pygame.Rect(min(xs), min(ys), 1, 1)
    rect.width = max(xs) - rect.x or 1
    rect.height = max(ys) - rect.y or 1
    return rect
