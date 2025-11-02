from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import pygame


Binding = Dict[str, List[Tuple[str, int]]]

DEFAULT_BINDINGS: Dict[str, List[Tuple[str, int]]] = {
    "quit":   [("event", pygame.QUIT)],
    "pause":  [("keydown", pygame.K_ESCAPE)],
    "up":     [("keydown", pygame.K_w), ("keydown", pygame.K_UP), ("keyup", pygame.K_w), ("keyup", pygame.K_UP)],
    "down":   [("keydown", pygame.K_s), ("keydown", pygame.K_DOWN), ("keyup", pygame.K_s), ("keyup", pygame.K_DOWN)],
    "left":   [("keydown", pygame.K_a), ("keydown", pygame.K_LEFT), ("keyup", pygame.K_a), ("keyup", pygame.K_LEFT)],
    "right":  [("keydown", pygame.K_d), ("keydown", pygame.K_RIGHT), ("keyup", pygame.K_d), ("keyup", pygame.K_RIGHT)],
    "enter":  [("keydown", pygame.K_RETURN), ("keyup", pygame.K_RETURN)],
    "space":  [("keydown", pygame.K_SPACE), ("keyup", pygame.K_SPACE)],
    "escape": [("keydown", pygame.K_ESCAPE), ("keyup", pygame.K_ESCAPE)],
    "mouse_down": [("event", pygame.MOUSEBUTTONDOWN)],
    "mouse_up":   [("event", pygame.MOUSEBUTTONUP)],
}

def _build_keymap(bindings: Dict[str, List[Tuple[str, int]]]) -> Dict[Tuple[str, int], List[str]]:
    km: Dict[Tuple[str, int], List[str]] = {}
    for action, pairs in bindings.items():
        for kind, code in pairs:
            km.setdefault((kind, code), []).append(action)
    return km

def _poll_with_keymap(km: Dict[Tuple[str, int], List[str]]):
    out: List[Tuple[str, str, Optional[int]]] = []
    for e in pygame.event.get():
        t = e.type
        if t == pygame.QUIT:
            out.append(("quit", "press", None))
        elif t == pygame.VIDEORESIZE:
            out.append(("window_resized", "change", (e.w, e.h)))
        elif t == pygame.MOUSEBUTTONDOWN:
            out.append(("mouse_down", "press", e.button))
        elif t == pygame.MOUSEBUTTONUP:
            out.append(("mouse_up", "release", e.button))
        elif t == pygame.KEYDOWN:
            k = e.key
            for name in km.get(("keydown", k), ()):
                out.append((name, "press", k))
        elif t == pygame.KEYUP:
            k = e.key
            for name in km.get(("keyup", k), ()):
                out.append((name, "release", k))
    return out

@dataclass
class BindingLayer:
    name: str
    bindings: Dict[str, List[Tuple[str, int]]]
    keymap: Dict[Tuple[str, int], List[str]] = field(default_factory=dict)

    def rebuild(self) -> None:
        self.keymap = _build_keymap(self.bindings)

class InputManager:

    def __init__(self, default: Optional[Dict[str, List[Tuple[str, int]]]] = None):
        self.layers: List[BindingLayer] = []
        self.global_layer = BindingLayer("global", dict(default or DEFAULT_BINDINGS))
        self.global_layer.rebuild()
        self.layers.append(self.global_layer)

        self._keys_down: Dict[int, bool] = {}
        self._capture_mode: bool = False
        self._last_captured: Optional[Tuple[int, int]] = None

    def push_context(self, name: str, bindings: Dict[str, List[Tuple[str, int]]]) -> None:
        layer = BindingLayer(name, dict(bindings))
        layer.rebuild()
        self.layers.append(layer)

    def pop_context(self, name: Optional[str] = None) -> None:
        if len(self.layers) <= 1:
            return
        if name is None:
            self.layers.pop()
            return

        for i in range(len(self.layers) - 1, 0, -1):
            if self.layers[i].name == name:
                self.layers.pop(i)
                return

    def rebind(self, action: str, specs: List[Tuple[str, int]], layer: str = "top") -> None:
        target = self.layers[-1] if layer == "top" else self.global_layer
        target.bindings[action] = list(specs)
        target.rebuild()

    def add_binding(self, action: str, spec: Tuple[str, int], layer: str = "top") -> None:
        target = self.layers[-1] if layer == "top" else self.global_layer
        target.bindings.setdefault(action, []).append(spec)
        target.rebuild()

    def remove_action(self, action: str, layer: str = "top") -> None:
        target = self.layers[-1] if layer == "top" else self.global_layer
        target.bindings.pop(action, None)
        target.rebuild()

    def begin_capture(self) -> None:
        self._capture_mode = True
        self._last_captured = None

    def poll_capture(self) -> Optional[Tuple[int, int]]:
        return self._last_captured

    def save(self, path: str) -> None:
        data = {layer.name: layer.bindings for layer in self.layers}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.layers = []
        for name, bindings in data.items():
            layer = BindingLayer(name, bindings)
            layer.rebuild()
            self.layers.append(layer)
        if not self.layers:
            self.layers = [self.global_layer]

    def _lookup_actions(self, kind: str, code: int) -> List[str]:
        for layer in reversed(self.layers):
            acts = layer.keymap.get((kind, code))
            if acts:
                return acts
        return []

    def poll(self) -> List[Tuple[str, str, Optional[int]]]:
        actions: List[Tuple[str, str, Optional[int]]] = []
        for e in pygame.event.get():
            t = e.type
            if t == pygame.KEYDOWN:
                actions.append(("raw_keydown", "press", e.key))
            elif t == pygame.KEYUP:
                actions.append(("raw_keyup", "release", e.key))
            elif t == pygame.MOUSEBUTTONDOWN:
                actions.append(("raw_mouse_down", "press", e.button))
            elif t == pygame.MOUSEBUTTONUP:
                actions.append(("raw_mouse_up", "release", e.button))
            elif t == pygame.TEXTINPUT:
                actions.append(("raw_text", "input", e.text))

            if self._capture_mode and t == pygame.KEYDOWN:
                self._last_captured = (e.key, pygame.key.get_mods())
                actions.append(("capture", "press", e.key))
                self._capture_mode = False

            if t == pygame.QUIT:
                actions.append(("quit", "press", None))
                continue
            if t == pygame.VIDEORESIZE:
                actions.append(("window_resized", "change", (e.w, e.h)))
                continue

            if t == pygame.MOUSEBUTTONDOWN:
                for name in self._lookup_actions("event", pygame.MOUSEBUTTONDOWN):
                    actions.append((name, "press", e.button))
            elif t == pygame.MOUSEBUTTONUP:
                for name in self._lookup_actions("event", pygame.MOUSEBUTTONUP):
                    actions.append((name, "release", e.button))
            elif t == pygame.KEYDOWN:
                self._keys_down[e.key] = True
                for name in self._lookup_actions("keydown", e.key):
                    actions.append((name, "press", e.key))
            elif t == pygame.KEYUP:
                self._keys_down.pop(e.key, None)
                for name in self._lookup_actions("keyup", e.key):
                    actions.append((name, "release", e.key))
        return actions

    def is_key_down(self, key: int) -> bool:
        return bool(self._keys_down.get(key, False))

    def is_action_down(self, action: str) -> bool:
        for layer in reversed(self.layers):
            specs = layer.bindings.get(action)
            if not specs:
                continue
            for kind, code in specs:
                if kind == "keydown" and self._keys_down.get(code):
                    return True
            return False
        return False

_MANAGER: Optional[InputManager] = None

def get_manager() -> InputManager:
    global _MANAGER
    if _MANAGER is None:
        _MANAGER = InputManager(DEFAULT_BINDINGS)
    return _MANAGER

def init_input_system() -> None:
    if pygame.get_init() and pygame.display.get_init():
        try:
            pygame.key.set_repeat(0, 0)
        except pygame.error:
            pass

def poll_actions(bindings: Optional[Binding] = None):
    if bindings is None:
        return get_manager().poll()
    return _poll_with_keymap(_build_keymap(bindings))

def push_bindings(name: str, bindings: Dict[str, List[Tuple[str, int]]]) -> None:
    get_manager().push_context(name, bindings)

def pop_bindings(name: Optional[str] = None) -> None:
    get_manager().pop_context(name)

def rebind(action: str, specs: List[Tuple[str, int]], layer: str = "top") -> None:
    get_manager().rebind(action, specs, layer)

def begin_capture() -> None:
    get_manager().begin_capture()

def poll_capture() -> Optional[Tuple[int, int]]:
    return get_manager().poll_capture()

def save_bindings(path: str) -> None:
    get_manager().save(path)

def load_bindings(path: str) -> None:
    get_manager().load(path)

def is_key_down(key: int) -> bool:
    return get_manager().is_key_down(key)

def is_action_down(name: str) -> bool:
    return get_manager().is_action_down(name)