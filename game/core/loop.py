import time
from game.config.constants import TARGET_FPS

def run(update_fn, render_fn, fps=60):
    dt_target = 1.0 / fps
    last = time.perf_counter()
    running = True
    while running:
        now = time.perf_counter()
        dt = now - last
        last = now
        running = update_fn(dt)
        render_fn()
        elapsed = time.perf_counter() - now
        sleep = dt_target - elapsed
        if sleep > 0:
            time.sleep(sleep)