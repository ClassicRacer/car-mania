from game.io.render import end_frame, get_half_screen
from game.render.level_full import Camera2D, LevelFullRenderer
from game.ui.base_screen import BaseScreen


class Gameplay(BaseScreen):
    def __init__(self, back_action=None):
        super().__init__(back_action)
        self.full_renderer = None
        self.camera = None

    def enter(self, ctx):
        super().enter(ctx)
        self.full_renderer = LevelFullRenderer(ctx["pieces"])
        self.camera = Camera2D(zoom=4.0)
        level_data = ctx.get("level_data")
        if level_data:
            bounds = self.full_renderer.get_piece_bounds(level_data)
            self.camera.x = -bounds.x
            self.camera.y = -bounds.y

    def on_resize(self, ctx, size):
        super().on_resize(ctx, size)

    def update(self, ctx, dt):
        actions = self.step(ctx)
        if self.handle_back(ctx, actions):
            return True
        return True

    def render(self, ctx):
        surf = ctx["window"]
        level_data = ctx["level_data"]
        self.full_renderer.render_to(surf, level_data, camera=self.camera)
        end_frame()
