from pathlib import Path
from game.io.render import get_mouse_pos_logical, init_display
from game.core.engine.loop import run
from game.core.engine.state import Game
from game.ui.screens.menu_screens import main_menu
from game.ui.widgets.button import make_back_draw
from game.io.assets import load_font, load_image
from game.io.input import poll_actions
from game.config.constants import FONT_FILE, ICON_FONT_FILE, DB_FILE
from game.data.store import open_db

import os, pygame


def _load_pieces() -> dict:
    base = Path("game/assets/images")

    def img(name):
        s = load_image(str(base / name))
        if s is None:
            s = pygame.Surface((64, 64), pygame.SRCALPHA)
            s.fill((255, 0, 255, 255))
        return s

    road_1 = img("road.png")
    road_2 = img("turn.png")
    gate    = img("checkpoint.png")
    gate_on = img("checkpoint_active.png")
    grid    = img("maze_grid.png")
    maze_wall  = img("maze_wall.png")
    tree_1  = img("tree1.png")
    tree_2  = img("tree2.png")
    tree_3  = img("tree3.png")

    return {
        "road_1": road_1,
        "road_2": road_2,
        "gate": gate,
        "gate_active": gate_on,
        "maze_grid": grid,
        "maze_wall": maze_wall,
        "tree_1": tree_1,
        "tree_2": tree_2,
        "tree_3": tree_3,
    }

def main():
    os.environ["SDL_MOUSE_FOCUS_CLICKTHROUGH"] = "1"
    pygame.init()
    db = open_db(DB_FILE)
    window = init_display()
    ui_font = load_font(FONT_FILE, 36)
    title_font = load_font(FONT_FILE, 100)
    icon_font = load_font(ICON_FONT_FILE, 36)

    ctx = {
        "window": window,
        "fonts": {"ui": ui_font, "title": title_font, "icon": icon_font},
        "back_button_draw": make_back_draw(icon_font, ui_font),
        "poll_actions": poll_actions,
        "get_mouse_pos": get_mouse_pos_logical,
        "db": db,
        "profile_id": 1,
        "selected_car_id": -1,
        "selected_level_id": -1,
        "pieces": _load_pieces(),
    }
    game = Game(ctx)
    ctx["game"] = game
    game.set(main_menu(game))
    run(game.update, game.render, fps=60)

if __name__ == "__main__":
    main()
