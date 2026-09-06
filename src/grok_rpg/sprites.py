from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pygame

from grok_rpg.paths import BAKED_DIR


class SpriteBank:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or BAKED_DIR
        self.index: dict[str, Any] = {}
        self.images: dict[str, pygame.Surface] = {}
        self.ok = False
        idx = self.root / "index.json"
        if idx.is_file():
            self.index = json.loads(idx.read_text(encoding="utf-8")).get("by_id", {})
            self.ok = True

    def frames(self, sprite_id: str) -> list[pygame.Surface]:
        meta = self.index.get(sprite_id)
        if not meta:
            return []
        out = []
        for rel in meta.get("frames", []):
            if rel not in self.images:
                path = self.root / rel
                if not path.is_file():
                    continue
                surf = pygame.image.load(str(path)).convert_alpha()
                self.images[rel] = surf
            out.append(self.images[rel])
        return out

    def first(self, sprite_id: str) -> pygame.Surface | None:
        fr = self.frames(sprite_id)
        return fr[0] if fr else None

    def fps(self, sprite_id: str, default: int = 8) -> int:
        meta = self.index.get(sprite_id) or {}
        return int(meta.get("fps") or default)

    def loops(self, sprite_id: str) -> bool:
        meta = self.index.get(sprite_id) or {}
        return bool(meta.get("loop", True))


class Animator:
    def __init__(self) -> None:
        self.sprite_id = ""
        self.t = 0.0
        self.frame = 0
        self.dir = 1

    def play(self, sprite_id: str, restart: bool = False) -> None:
        if sprite_id != self.sprite_id or restart:
            self.sprite_id = sprite_id
            self.t = 0.0
            self.frame = 0
            self.dir = 1

    def pingpong(self, bank: SpriteBank) -> bool:
        meta = bank.index.get(self.sprite_id) or {}
        return bool(meta.get("pingpong")) and bank.loops(self.sprite_id)

    def update(self, dt: float, bank: SpriteBank) -> pygame.Surface | None:
        frames = bank.frames(self.sprite_id)
        if not frames:
            return None
        fps = max(1, bank.fps(self.sprite_id))
        self.t += dt
        step = 1.0 / fps
        n = len(frames)
        while self.t >= step:
            self.t -= step
            if n == 1:
                self.frame = 0
                continue
            if self.pingpong(bank):
                self.frame += self.dir
                if self.frame >= n:
                    self.dir = -1
                    self.frame = max(0, n - 2)
                elif self.frame < 0:
                    self.dir = 1
                    self.frame = min(1, n - 1)
            else:
                self.frame += 1
                if self.frame >= n:
                    self.frame = 0 if bank.loops(self.sprite_id) else n - 1
        return frames[min(self.frame, n - 1)]
