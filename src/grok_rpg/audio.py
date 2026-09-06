from __future__ import annotations

import json

import pygame

from grok_rpg.paths import BAKED_DIR


class Audio:
    def __init__(self) -> None:
        self.enabled = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.current_amb: str | None = None
        try:
            pygame.mixer.init()
            self.enabled = True
        except pygame.error:
            self.enabled = False
        idx_path = BAKED_DIR / "index.json"
        if self.enabled and idx_path.is_file():
            data = json.loads(idx_path.read_text(encoding="utf-8"))
            for job in data.get("jobs", []):
                if job.get("kind") != "audio":
                    continue
                for rel in job.get("frames", []):
                    path = BAKED_DIR / rel
                    if path.is_file():
                        try:
                            self.sounds[job["id"]] = pygame.mixer.Sound(str(path))
                        except pygame.error:
                            pass

    def play(self, sound_id: str | None, volume: float = 0.6) -> None:
        if not self.enabled or not sound_id:
            return
        snd = self.sounds.get(sound_id)
        if snd:
            snd.set_volume(volume)
            snd.play()

    def ambience(self, sound_id: str | None) -> None:
        if not self.enabled:
            return
        if sound_id == self.current_amb:
            return
        pygame.mixer.music.stop()
        self.current_amb = sound_id
        if not sound_id:
            return
        idx = BAKED_DIR / "index.json"
        if not idx.is_file():
            return
        data = json.loads(idx.read_text(encoding="utf-8"))
        job = data.get("by_id", {}).get(sound_id)
        if not job:
            return
        frames = job.get("frames") or []
        if not frames:
            return
        path = BAKED_DIR / frames[0]
        if path.is_file():
            try:
                pygame.mixer.music.load(str(path))
                pygame.mixer.music.set_volume(0.25)
                pygame.mixer.music.play(-1)
            except pygame.error:
                pass
