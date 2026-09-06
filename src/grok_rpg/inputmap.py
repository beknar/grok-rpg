from __future__ import annotations

import pygame

_NAME_TO_KEY = {
    "w": pygame.K_w,
    "a": pygame.K_a,
    "s": pygame.K_s,
    "d": pygame.K_d,
    "q": pygame.K_q,
    "e": pygame.K_e,
    "r": pygame.K_r,
    "f": pygame.K_f,
    "c": pygame.K_c,
    "i": pygame.K_i,
    "h": pygame.K_h,
    "b": pygame.K_b,
    "tab": pygame.K_TAB,
    "up": pygame.K_UP,
    "down": pygame.K_DOWN,
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "escape": pygame.K_ESCAPE,
    "1": pygame.K_1,
    "2": pygame.K_2,
    "3": pygame.K_3,
    "4": pygame.K_4,
    "f3": pygame.K_F3,
    "f5": pygame.K_F5,
    "f9": pygame.K_F9,
}


def keys_for(bindings: dict[str, list[str]], action: str) -> list[int]:
    out = []
    for name in bindings.get(action, []):
        key = _NAME_TO_KEY.get(name.lower())
        if key is not None:
            out.append(key)
    return out


def action_pressed(keystate: pygame.key.ScancodeWrapper, bindings: dict[str, list[str]], action: str) -> bool:
    return any(keystate[k] for k in keys_for(bindings, action))


def keydown_action(key: int, bindings: dict[str, list[str]], action: str) -> bool:
    return key in keys_for(bindings, action)
