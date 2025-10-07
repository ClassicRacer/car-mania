import os
import pygame

from game.io.assets import ASSETS_DIR

_window = None
_screen = None
_physical = (0, 0)
_logical = (0, 0)
_ratio = 1.0
_offset = (0, 0)

def _recalc():
    global _ratio, _offset
    lw, lh = _logical
    pw, ph = _physical
    if lw == 0 or lh == 0 or pw == 0 or ph == 0:
        _ratio = 1.0
        _offset = (0, 0)
        return
    r = min(pw / lw, ph / lh)
    _ratio = r
    sw = int(lw * r)
    sh = int(lh * r)
    _offset = ((pw - sw) // 2, (ph - sh) // 2)

def init_display(physical_size=(1280, 720), logical_size=(1920, 1080), caption="Car Mania"):
    global _window, _screen, _physical, _logical
    os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"
    pygame.display.set_caption(caption)
    _logical = logical_size
    _physical = physical_size
    _window = pygame.Surface(_logical)
    _screen = pygame.display.set_mode(_physical, pygame.RESIZABLE | pygame.DOUBLEBUF)
    icon = pygame.image.load(os.path.join(ASSETS_DIR, "images", "icon.png")).convert_alpha()
    pygame.display.set_icon(icon)
    _recalc()
    return _window

def resize_physical(size):
    global _screen, _physical
    _physical = size
    _screen = pygame.display.set_mode(_physical, pygame.RESIZABLE | pygame.DOUBLEBUF)
    _recalc()

def get_window():
    return _window

def get_logical_size():
    return _logical

def get_half_screen():
    return (_logical[0] / 2, _logical[1] / 2)

def get_mouse_pos_logical():
    mp = pygame.mouse.get_pos()
    x = (mp[0] - _offset[0]) / _ratio
    y = (mp[1] - _offset[1]) / _ratio
    x = 0 if x < 0 else (_logical[0] if x > _logical[0] else x)
    y = 0 if y < 0 else (_logical[1] if y > _logical[1] else y)
    return (x, y)

def begin_frame():
    pass

def end_frame():
    pw, ph = _physical
    lw, lh = _logical
    scaled = pygame.transform.scale(_window, (int(lw * _ratio), int(lh * _ratio)))
    _screen.fill((0, 0, 0))
    _screen.blit(scaled, _offset)
    pygame.display.flip()