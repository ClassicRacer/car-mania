from game.io.render import init_display
from game.core.loop import run
from game.core.state import Game
from game.ui.menus import main_menu
import os

def main():
    os.environ["SDL_MOUSE_FOCUS_CLICKTHROUGH"] = "1"
    window = init_display()
    import pygame
    pygame.init()
    ctx = {"window": window}
    game = Game(ctx)
    ctx["game"] = game
    game.set(main_menu(game))
    run(game.update, game.render, fps=60)

if __name__ == "__main__":
    main()