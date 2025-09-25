from game.ui.screens import MenuScreen

def main_menu(game):
    return MenuScreen("Car Mania", [
        ("Play",     lambda ctx: ctx["game"].set(play_menu(game))),
        ("Create",   lambda ctx: ctx["game"].set(create_menu(game))),
        ("Options",  None),
        ("Quit",     lambda ctx: ctx.update({"quit": True})),
    ])

def play_menu(game):
    return MenuScreen("Car Mania", [], back_action=lambda ctx: ctx["game"].set(main_menu(game)))

def create_menu(game):
    return MenuScreen("Car Mania", [
        ("Car Creator", lambda ctx: ctx["game"].set(car_creator_menu(game))),
        ("Level Creator", lambda ctx: ctx["game"].set(level_creator_menu(game))),
    ], back_action=lambda ctx: ctx["game"].set(main_menu(game)))

def car_creator_menu(game):
    return MenuScreen("Car Creator Menu", [
        ("Create Car", None),
        ("Edit Car", None),
        ("Tutorial", None),
    ], back_action=lambda ctx: ctx["game"].set(create_menu(game)))

def level_creator_menu(game):
    return MenuScreen("Level Creator Menu", [
        ("Create Level", None),
        ("Edit Level", None),
        ("Tutorial", None),
    ], back_action=lambda ctx: ctx["game"].set(create_menu(game)))