import pygame

def draw_text(surf: pygame.Surface, text: str, font: pygame.font, color: tuple[int, int, int], pos: tuple[int, int], centered=False):
    render = font.render(text, True, color)
    if centered:
        surf.blit(render, render.get_rect(center=pos))
    else:
        surf.blit(render, pos)

def center_text_on_oval(surface: pygame.Surface, text: str, font: pygame.font, text_y: int, oval_x: int, oval_width: int, color: tuple[int, int, int]):
    text_surface = font.render(text, True, color)
    text_width = text_surface.get_width()
    text_x = oval_x + (oval_width - text_width) // 2
    surface.blit(text_surface, (text_x, text_y))

def draw_right(surf: pygame.Surface, y: int, text: str, font: pygame.font.Font,
               color=(255, 255, 255), padding: int = 10, *,
               baseline_y: bool = False):
    text_w, text_h = font.size(text)
    x = surf.get_width() - padding - text_w
    top = y - font.get_ascent() if baseline_y else y
    surf.blit(font.render(text, True, color), (x, top))