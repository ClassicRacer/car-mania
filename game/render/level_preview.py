import pygame

class LevelPreviewRenderer:
    def __init__(self, pieces, piece_map, target_size=(480, 270), tile_w=200):
        self.pieces = pieces
        self.piece_map = piece_map
        self.tw = tile_w
        self.size = target_size

    def _img(self, key):
        return self.pieces.get(key, self.piece_map[key])

    def _collect(self, level):
        road = []
        trees = []
        maze_road = []
        maze_h = []
        maze_v = []
        img_grid = self._img("maze_grid")
        img_h = self._img("maze_h")
        img_v = pygame.transform.rotate(img_h, 90)
        for line in level.code:
            k = line[0]
            if k == "road":
                t = int(line[1])
                ang = int(line[4])
                img = self._img(f"road_{t}")
                x = int(line[2])
                y = -int(line[3])
                road.append((img, ang, x, y))
            elif k == "gate":
                pass
            elif k == "tree":
                t = int(line[1])
                img = self._img(f"tree_{t}")
                x = int(line[2])
                y = -int(line[3])
                trees.append((img, x, y))
            elif k == "maze":
                sx = int(line[1])
                sy = int(line[2])
                for r in range(-1, sx + 1):
                    for c in range(-1, sy + 1):
                        maze_road.append((img_grid, self.tw*r, self.tw*c))
                for x,y in level.walls.get("Right", []):
                    maze_h.append((img_h, x, y))
                for x,y in level.walls.get("Left", []):
                    maze_h.append((img_h, x, y))
                for x,y in level.walls.get("Up", []):
                    maze_v.append((img_v, x, y))
                for x,y in level.walls.get("Down", []):
                    maze_v.append((img_v, x, y))
        return road, trees, maze_road, maze_h, maze_v

    def _bounds(self, road, trees, maze_road, maze_h, maze_v):
        pts = []
        for img, ang, x, y in road:
            w,h = img.get_size()
            pts.append((x, y))
            pts.append((x + w, y + h))
        for img, x, y in trees:
            w,h = img.get_size()
            pts.append((x, y))
            pts.append((x + w, y + h))
        for img, x, y in maze_road + maze_h + maze_v:
            w,h = img.get_size()
            pts.append((x, y))
            pts.append((x + w, y + h))
        if not pts:
            return pygame.Rect(0,0,1,1)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        r = pygame.Rect(min(xs), min(ys), 1, 1)
        r.width = max(xs) - r.x or 1
        r.height = max(ys) - r.y or 1
        return r

    def render(self, level):
        surf = pygame.Surface(self.size, pygame.SRCALPHA)
        surf.fill((*level.color, 255))
        road, trees, maze_road, maze_h, maze_v = self._collect(level)
        bounds = self._bounds(road, trees, maze_road, maze_h, maze_v)
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
        for img, x, y in maze_road:
            blit_scaled(img, to_screen(x, y))
        for img, x, y in maze_h:
            blit_scaled(img, to_screen(x, y))
        for img, x, y in maze_v:
            blit_scaled(img, to_screen(x, y))
        for img, ang, x, y in road:
            blit_scaled(img, to_screen(x, y), ang)
        for img, x, y in trees:
            blit_scaled(img, to_screen(x, y))
        return surf