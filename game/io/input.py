import pygame

DEFAULT_BINDINGS = {
    "quit": [("event", pygame.QUIT)],
    "pause": [("keydown", pygame.K_ESCAPE)],
    "up": [("keydown", pygame.K_w), ("keydown", pygame.K_UP), ("keyup", pygame.K_w), ("keyup", pygame.K_UP)],
    "down": [("keydown", pygame.K_s), ("keydown", pygame.K_DOWN), ("keyup", pygame.K_s), ("keyup", pygame.K_DOWN)],
    "left": [("keydown", pygame.K_a), ("keydown", pygame.K_LEFT), ("keyup", pygame.K_a), ("keyup", pygame.K_LEFT)],
    "right": [("keydown", pygame.K_d), ("keydown", pygame.K_RIGHT), ("keyup", pygame.K_d), ("keyup", pygame.K_RIGHT)],
    "enter": [("keydown", pygame.K_RETURN), ("keyup", pygame.K_RETURN)],
    "space": [("keydown", pygame.K_SPACE), ("keyup", pygame.K_SPACE)],
    "escape": [("keydown", pygame.K_ESCAPE), ("keyup", pygame.K_ESCAPE)],
    "mouse_down": [("event", pygame.MOUSEBUTTONDOWN)],
    "mouse_up": [("event", pygame.MOUSEBUTTONUP)],
}

def _build_keymap(bindings):
    km = {}
    for name, pairs in bindings.items():
        for kind, code in pairs:
            km.setdefault((kind, code), []).append(name)
    return km

_KEYMAP = _build_keymap(DEFAULT_BINDINGS)

def poll_actions(bindings=None):
    bm = bindings or DEFAULT_BINDINGS
    km = _KEYMAP if bindings is None else _build_keymap(bindings)
    actions = []
    for e in pygame.event.get():
        t = e.type
        if t == pygame.QUIT:
            actions.append(("quit", "press", None))
        elif t == pygame.VIDEORESIZE:
            actions.append(("window_resized", "change", (e.w, e.h)))
        elif t == pygame.MOUSEBUTTONDOWN:
            actions.append(("mouse_down", "press", e.button))
        elif t == pygame.MOUSEBUTTONUP:
            actions.append(("mouse_up", "release", e.button))
        elif t == pygame.KEYDOWN:
            k = e.key
            for name in km.get(("keydown", k), ()):
                actions.append((name, "press", k))
        elif t == pygame.KEYUP:
            k = e.key
            for name in km.get(("keyup", k), ()):
                actions.append((name, "release", k))
    return actions