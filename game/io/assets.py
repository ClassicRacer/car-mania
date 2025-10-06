from pathlib import Path
from functools import lru_cache

ASSETS_DIR = "game/assets"

ROOT = Path(ASSETS_DIR)

def path(*parts: str) -> Path:
    return ROOT.joinpath(*parts)

def _resolve_path(source: str, subdir: str) -> Path:
    p = Path(source).expanduser()
    if p.is_absolute() or p.exists():
        return p
    candidate = ROOT / subdir / source
    if candidate.exists():
        return candidate
    return p

def _can_convert() -> bool:
    import pygame
    return pygame.display.get_init() and pygame.display.get_surface() is not None

@lru_cache(maxsize=None)
def load_image(source: str, subdir: str = "images"):
    import pygame
    p = _resolve_path(source, subdir)
    s = pygame.image.load(str(p))
    if _can_convert():
        try:
            return s.convert_alpha() if s.get_alpha() else s.convert()
        except Exception:
            return s
    return s

@lru_cache(maxsize=None)
def load_sound(source: str, subdir: str = "sounds"):
    import pygame
    p = _resolve_path(source, subdir)
    return pygame.mixer.Sound(str(p))

@lru_cache(maxsize=None)
def load_font(name: str, size: int):
    import pygame
    return pygame.font.Font(str(path("fonts", name)), size)