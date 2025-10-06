import pygame

def draw_text(surf: pygame.Surface, text: str, font: pygame.font, color: tuple[int, int, int], pos: tuple[int, int], centered=False):
    render = font.render(text, True, color)
    if centered:
        surf.blit(render, render.get_rect(center=pos))
    else:
        surf.blit(render, pos)