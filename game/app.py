from game.io.render import init_display, end_frame, get_mouse_pos_logical
from game.core.loop import run
from . import _legacy_game as L

def main():
    window = init_display()
    L.bootstrap(window)
    run(window, L.update, L.render)
    L.shutdown()

if __name__ == "__main__":
    main()