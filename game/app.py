from game.io.render import get_mouse_pos_logical, init_display
from game.core.loop import run
from game.core.state import Game
from game.ui.menu_screens import main_menu
from game.ui.widgets import make_back_draw
from game.io.assets import load_font
from game.io.input import poll_actions
from game.config.constants import FONT_FILE, ICON_FONT_FILE
import os, pygame

def main():
    os.environ["SDL_MOUSE_FOCUS_CLICKTHROUGH"] = "1"
    pygame.init()
    window = init_display()
    ui_font = load_font(FONT_FILE, 36)
    title_font = load_font(FONT_FILE, 100)
    icon_font = load_font(ICON_FONT_FILE, 36)
    ctx = {
        "window": window,
        "fonts": {"ui": ui_font, "title": title_font, "icon": icon_font},
        "back_button_draw": make_back_draw(icon_font, ui_font),
        "poll_actions": poll_actions,
        "get_mouse_pos": get_mouse_pos_logical
    }
    game = Game(ctx)
    ctx["game"] = game
    game.set(main_menu(game))
    run(game.update, game.render, fps=60)

if __name__ == "__main__":
    main()