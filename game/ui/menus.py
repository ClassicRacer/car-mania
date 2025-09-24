from game.ui.screens import MenuScreen

def main_menu(game):
    # return MenuScreen("Car Mania", [
    #     ("Play",     lambda ctx: ctx["game"].set(make_play_screen(game))),
    #     ("Options",  lambda ctx: ctx["game"].set(make_options_menu(game))),
    #     ("Quit",     lambda ctx: ctx.update({"quit": True})),
    # ])
    return MenuScreen("Car Mania", [
        ("Play",     lambda ctx: ctx["game"].set(play_screen(game))),
        ("Options",  print("Options pressed")),
        ("Instructions", lambda ctx: print("Instructions pressed")),
        ("Quit",     lambda ctx: ctx.update({"quit": True})),
    ])

def play_screen(game):
    return MenuScreen("Car Mania", [
        ("Select Car", None),
        ("Select Level", None),
        ("Car Creator", None),
        ("Level Creator", None),
        ("Back to Main Menu", lambda ctx: ctx["game"].set(main_menu(game))),
    ])