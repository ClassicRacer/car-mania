import time

_CURRENT_FPS = 0.0
_FPS_ALPHA = 0.1

def get_fps() -> float:
    return _CURRENT_FPS

def run(update_fn, render_fn, fps=60):
    global _CURRENT_FPS
    dt_target = 1.0 / fps
    last = time.perf_counter()
    running = True
    while running:
        now = time.perf_counter()
        dt = now - last
        last = now

        inst_fps = (1.0 / dt) if dt > 0 else float("inf")
        _CURRENT_FPS += _FPS_ALPHA * (inst_fps - _CURRENT_FPS)

        running = update_fn(dt)
        render_fn()
        elapsed = time.perf_counter() - now
        sleep = dt_target - elapsed
        if sleep > 0:
            time.sleep(sleep)