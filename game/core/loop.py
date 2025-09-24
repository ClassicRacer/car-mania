import time
from game.config.constants import TARGET_FPS
from game.io.render import begin_frame, end_frame

def run(screen, update_fn, render_fn):
    dt_target = 1 / TARGET_FPS
    last = time.perf_counter()
    running = True
    while running:
        now = time.perf_counter()
        dt = now - last
        last = now
        running = update_fn(dt)
        begin_frame()
        render_fn(screen)
        end_frame()
        sleep = dt_target - (time.perf_counter() - now)
        if sleep > 0:
            time.sleep(sleep)