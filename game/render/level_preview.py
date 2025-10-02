import pygame

from game.render.level_utils import compute_piece_bounds, parse_level_code

class LevelPreviewRenderer:
    def __init__(self, pieces: dict, target_size=(480, 270)):
        self.pieces = pieces
        self.size = target_size

    def render(self, level_row: dict):
        surf = pygame.Surface(self.size, pygame.SRCALPHA)
        bg = (int(level_row["ground_r"]), int(level_row["ground_g"]), int(level_row["ground_b"]))
        surf.fill(bg)
        roads, trees, gates, _ = parse_level_code(level_row["code"])
        bounds = compute_piece_bounds(self.pieces, roads, trees, gates)
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
