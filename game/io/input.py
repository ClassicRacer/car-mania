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

def poll_actions(bindings: dict = None):
    bindings = bindings or DEFAULT_BINDINGS
    actions = []
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            actions.append(("quit", "press", None))
            continue
        if event.type == pygame.MOUSEBUTTONDOWN:
            actions.append(("mouse_down", "press", event.button))
            continue
        if event.type == pygame.MOUSEBUTTONUP:
            actions.append(("mouse_up", "release", event.button))
            continue
        if event.type == pygame.KEYDOWN:
            k = event.key
            for name, binds in bindings.items():
                if ("keydown", k) in binds:
                    actions.append((name, "press", k))
            continue
        if event.type == pygame.KEYUP:
            k = event.key
            for name, binds in bindings.items():
                if ("keyup", k) in binds:
                    actions.append((name, "release", k))
            continue
    return actions