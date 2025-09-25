class Screen:
    def enter(self, ctx):
        '''Called once when the screen becomes active. Good place to build UI, reset variables, start music, etc.'''
        pass
    def exit(self, ctx):
        '''Called once when the screen is replaced. Good for cleanup.'''
        pass
    def update(self, ctx, dt):
        '''Called every frame to process input, update game logic, etc. Return True to keep running, or False to quit the app.'''
        return True
    def render(self, ctx):
        '''Called every frame to draw the screen’s visuals.'''
        pass

class Game:
    def __init__(self, ctx):
        self.ctx = ctx
        self.current = None
        self.ctx.setdefault("screen_seq", 0)
    def set(self, screen):
        '''Cleanly switches screens by calling exit() on the old one and enter() on the new one'''
        if self.current:
            self.current.exit(self.ctx)
        self.current = screen
        self.ctx["screen_seq"] += 1
        self.current.enter(self.ctx)
    def update(self, dt):
        '''Forward to the current screen'''
        if not self.current:
            return False
        if not self.current.update(self.ctx, dt):
            return False
        if self.ctx.get("quit"):
            return False
        return True
    def render(self):
        '''Forward to the current screen'''
        if self.current:
            self.current.render(self.ctx)