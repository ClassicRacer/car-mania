import heapq
import random
from typing import Dict, Iterable, List, Optional, Tuple

import pygame

MAZE_TILE_SIZE = 200
MAZE_GATE_SIZE = (70, 10)
MAZE_GRID_KEY = "maze_grid"
MAZE_WALL_KEY = "maze_wall"

def parse_level_code(code_text: str, *, seed: Optional[int] = None):
    roads: List[Tuple[object, int, int, int]] = []
    trees: List[Tuple[int, int, int]] = []
    gates: List[Tuple[int, int, int, int]] = []
    if not code_text:
        return roads, trees, gates, None

    lines = [ln.strip() for ln in code_text.splitlines() if ln.strip()]
    if seed is None:
        seed = random.SystemRandom().randrange(0, 1 << 63)
    base_seed = seed
    maze_index = 0
    mazes: List[dict] = []

    for ln in lines:
        parts = ln.split(",")
        if not parts:
            continue
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
        elif k == "maze" and len(parts) >= 4:
            if len(parts) >= 6:
                x_offset = int(parts[1])
                y_offset = -int(parts[2])
                width = max(1, int(parts[3]))
                height = max(1, int(parts[4]))
                checkpoints = max(0, int(parts[5]))
            else:
                x_offset = 0
                y_offset = 0
                width = max(1, int(parts[1]))
                height = max(1, int(parts[2]))
                checkpoints = max(0, int(parts[3]))
            maze_seed = base_seed + maze_index
            rng = random.Random(maze_seed)
            maze_index += 1
            origin = (x_offset, y_offset)
            maze_roads, maze_gates, meta = _build_maze(width, height, checkpoints, rng, origin)
            meta["seed"] = maze_seed
            roads.extend(maze_roads)
            gates.extend(maze_gates)
            mazes.append(meta)

    extra = None
    if mazes:
        extra = {"mazes": mazes, "seed": base_seed}
    elif maze_index > 0:
        extra = {"seed": base_seed}
    gates.sort(key=lambda item: item[0])
    return roads, trees, gates, extra


def compute_piece_bounds(pieces: dict, roads, trees, gates):
    pts = []

    def add_rect(w, h, x, y):
        pts.append((x, y))
        pts.append((x + w, y + h))

    for typ, x, y, ang in roads:
        img = _get_piece_image(pieces, typ, road=True)
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


def _build_maze(width: int, height: int, checkpoints: int, rng: random.Random, origin: Tuple[int, int]):
    adjacency = _generate_maze_graph(width, height, rng)
    grid_tiles = _build_maze_grid_tiles(width, height, origin)
    wall_tiles = _build_maze_walls(width, height, adjacency, origin)
    checkpoint_cells = _select_maze_checkpoints(adjacency, width, height, checkpoints)
    gate_entries = _create_gate_entries(checkpoint_cells, origin)

    maze_meta = {
        "width": width,
        "height": height,
        "tile_size": MAZE_TILE_SIZE,
        "grid": [tuple(cell) for cell in grid_tiles],
        "walls": [tuple(wall) for wall in wall_tiles],
        "checkpoints": [tuple(cell) for cell in checkpoint_cells],
        "graph": {node: tuple(sorted(neigh)) for node, neigh in adjacency.items()},
        "origin": tuple(origin),
    }

    maze_roads = [(MAZE_GRID_KEY, x, y, 0) for (x, y) in grid_tiles]
    maze_roads.extend((MAZE_WALL_KEY, x, y, angle) for (x, y, angle) in wall_tiles)
    return maze_roads, gate_entries, maze_meta


def _build_maze_grid_tiles(width: int, height: int, origin: Tuple[int, int]) -> List[Tuple[int, int]]:
    base_x, base_y = origin
    tiles: List[Tuple[int, int]] = []
    for cy in range(height):
        for cx in range(width):
            tiles.append((base_x + cx * MAZE_TILE_SIZE, base_y + cy * MAZE_TILE_SIZE))
    return tiles


def _build_maze_walls(
    width: int,
    height: int,
    adjacency: Dict[Tuple[int, int], Iterable[Tuple[int, int]]],
    origin: Tuple[int, int],
):
    walls = set()
    base_x, base_y = origin

    def add_wall(x: int, y: int, angle: int):
        walls.add((x, y, angle))

    for cy in range(height):
        for cx in range(width):
            x_pos = base_x + cx * MAZE_TILE_SIZE
            y_pos = base_y + cy * MAZE_TILE_SIZE
            neighbours = adjacency.get((cx, cy), ())

            if cy == 0:
                add_wall(x_pos, y_pos, 0)
            if cx == 0:
                add_wall(x_pos, y_pos, 90)

            right = (cx + 1, cy)
            if cx == width - 1 or right not in neighbours:
                add_wall(x_pos + MAZE_TILE_SIZE, y_pos, 90)

            down = (cx, cy + 1)
            if cy == height - 1 or down not in neighbours:
                add_wall(x_pos, y_pos + MAZE_TILE_SIZE, 0)

    ordered = sorted(walls)
    return ordered


def _generate_maze_graph(width: int, height: int, rng: random.Random):
    adjacency: Dict[Tuple[int, int], set] = {
        (cx, cy): set() for cy in range(height) for cx in range(width)
    }
    start = (0, 0)
    stack: List[Tuple[int, int]] = [start]
    visited = {start}

    def valid_neighbors(cell):
        cx, cy = cell
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < width and 0 <= ny < height:
                yield (nx, ny)

    while stack:
        current = stack[-1]
        unvisited = [nb for nb in valid_neighbors(current) if nb not in visited]
        if unvisited:
            nxt = rng.choice(unvisited)
            adjacency[current].add(nxt)
            adjacency[nxt].add(current)
            stack.append(nxt)
            visited.add(nxt)
        else:
            stack.pop()

    return adjacency


def _select_maze_checkpoints(
    adjacency: Dict[Tuple[int, int], Iterable[Tuple[int, int]]],
    width: int,
    height: int,
    count: int,
) -> List[Tuple[int, int]]:
    total_cells = width * height
    if count <= 0 or total_cells <= 0 or not adjacency:
        return []

    start = (0, 0)
    if start not in adjacency:
        start = next(iter(adjacency))

    dist, prev = _dijkstra(adjacency, start)
    if not dist:
        return []

    farthest = max(dist.items(), key=lambda item: (item[1], item[0]))[0]
    path = _reconstruct_path(prev, start, farthest)

    count = min(count, total_cells)
    selected: List[Tuple[int, int]] = []
    seen = set()

    if path:
        if count == 1:
            candidates = [len(path) - 1]
        else:
            step = (len(path) - 1) / max(1, count - 1)
            candidates = [int(round(step * i)) for i in range(count)]

        for idx in candidates:
            idx = max(0, min(len(path) - 1, idx))
            node = path[idx]
            if node not in seen:
                selected.append(node)
                seen.add(node)
            if len(selected) == count:
                return selected

        for node in path:
            if len(selected) == count:
                break
            if node not in seen:
                selected.append(node)
                seen.add(node)

    if len(selected) < count:
        ordered_nodes = sorted(dist.items(), key=lambda item: (-item[1], item[0]))
        for node, _ in ordered_nodes:
            if node not in seen:
                selected.append(node)
                seen.add(node)
                if len(selected) == count:
                    break

    return selected


def _reconstruct_path(prev: Dict[Tuple[int, int], Tuple[int, int]], start, target):
    path: List[Tuple[int, int]] = []
    node: Optional[Tuple[int, int]] = target
    while node is not None:
        path.append(node)
        if node == start:
            break
        node = prev.get(node)
        if node is None and path[-1] != start:
            break
    path.reverse()
    return path


def _dijkstra(
    adjacency: Dict[Tuple[int, int], Iterable[Tuple[int, int]]],
    start: Tuple[int, int],
):
    dist: Dict[Tuple[int, int], float] = {start: 0.0}
    prev: Dict[Tuple[int, int], Tuple[int, int]] = {}
    heap: List[Tuple[float, Tuple[int, int]]] = [(0.0, start)]

    while heap:
        cost, node = heapq.heappop(heap)
        if cost > dist.get(node, float("inf")):
            continue
        for neighbor in adjacency.get(node, ()):
            new_cost = cost + 1.0
            if new_cost < dist.get(neighbor, float("inf")):
                dist[neighbor] = new_cost
                prev[neighbor] = node
                heapq.heappush(heap, (new_cost, neighbor))

    return dist, prev


def _create_gate_entries(cells: List[Tuple[int, int]], origin: Tuple[int, int]):
    gates: List[Tuple[int, int, int, int]] = []
    if not cells:
        return gates

    base_x, base_y = origin
    offset_x = (MAZE_TILE_SIZE - MAZE_GATE_SIZE[0]) // 2
    offset_y = (MAZE_TILE_SIZE - MAZE_GATE_SIZE[1]) // 2

    for order, (cx, cy) in enumerate(cells):
        gate_x = base_x + cx * MAZE_TILE_SIZE + offset_x
        gate_y = base_y + cy * MAZE_TILE_SIZE + offset_y
        gates.append((order, gate_x, gate_y, 0))

    return gates

def _get_piece_image(pieces: dict, typ: object, *, road: bool = False):
    if isinstance(typ, str):
        return pieces.get(typ)
    if road:
        return pieces.get(f"road_{typ}")
    return pieces.get(typ)
