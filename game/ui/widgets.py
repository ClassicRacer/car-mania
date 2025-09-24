import pygame

class Button:
    def __init__(self, rect, text, font, fg, bg, hover):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.fg = fg
        self.bg = bg
        self.hover = hover
        self._surf = None
        self._pos = None

    def draw(self, surface, mouse_pos):
        m = self.rect.collidepoint(mouse_pos)
        color = self.hover if m else self.bg
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        if not self._surf:
            self._surf = self.font.render(self.text, True, self.fg)
            self._pos = self._surf.get_rect(center=self.rect.center)
        surface.blit(self._surf, self._pos)
        return m
    
    def clicked(self, mouse_pos, mouse_clicked):
        return self.rect.collidepoint(mouse_pos) and mouse_clicked