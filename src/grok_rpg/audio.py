from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pygame

from grok_rpg.paths import BAKED_DIR, DATA_DIR


def load_music_table() -> dict[str, Any]:
    path = DATA_DIR / "music.json"
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def scene_tracks(kind: str, table: dict[str, Any], *, combat: bool = False) -> tuple[str | None, str | None]:
    scenes = table.get("scenes") or {}
    if combat and "boss" in scenes:
        music = scenes["boss"].get("music")
        amb = (scenes.get(kind) or {}).get("ambience") or scenes["boss"].get("ambience")
        return music, amb
    spec = scenes.get(kind) or scenes.get("title") or {}
    return spec.get("music"), spec.get("ambience")


class Audio:
    def __init__(self, table: dict[str, Any] | None = None) -> None:
        self.enabled = False
        self.muted = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.paths: dict[str, Path] = {}
        self.current_music: str | None = None
        self.current_amb: str | None = None
        self.amb_channel: pygame.mixer.Channel | None = None
        self.table = table or load_music_table()
        self.music_vol = float(self.table.get("music_volume", 0.4))
        self.amb_vol = float(self.table.get("ambience_volume", 0.2))
        self.sfx_vol = float(self.table.get("sfx_volume", 0.6))
        try:
            pygame.mixer.init()
            pygame.mixer.set_num_channels(16)
            pygame.mixer.set_reserved(1)
            self.amb_channel = pygame.mixer.Channel(0)
            self.enabled = True
        except pygame.error:
            self.enabled = False
        idx_path = BAKED_DIR / "index.json"
        if idx_path.is_file():
            data = json.loads(idx_path.read_text(encoding="utf-8"))
            for job in data.get("jobs", []):
                if job.get("kind") != "audio":
                    continue
                frames = job.get("frames") or []
                if not frames:
                    continue
                path = BAKED_DIR / frames[0]
                if not path.is_file():
                    continue
                self.paths[job["id"]] = path
                if self.enabled and not str(job["id"]).startswith("music."):
                    try:
                        self.sounds[job["id"]] = pygame.mixer.Sound(str(path))
                    except pygame.error:
                        pass

    def play(self, sound_id: str | None, volume: float | None = None) -> None:
        if not self.enabled or not sound_id:
            return
        snd = self.sounds.get(sound_id)
        if snd:
            snd.set_volume(self.sfx_vol if volume is None else volume)
            snd.play()

    def set_muted(self, muted: bool) -> None:
        self.muted = bool(muted)
        if not self.enabled:
            return
        if self.muted:
            pygame.mixer.music.pause()
            if self.amb_channel:
                self.amb_channel.pause()
        else:
            pygame.mixer.music.unpause()
            if self.amb_channel:
                self.amb_channel.unpause()

    def toggle_mute(self) -> bool:
        self.set_muted(not self.muted)
        return self.muted

    def _play_music(self, music_id: str | None) -> None:
        if not self.enabled:
            self.current_music = music_id
            return
        if music_id == self.current_music:
            return
        pygame.mixer.music.stop()
        self.current_music = music_id
        path = self.paths.get(music_id) if music_id else None
        if path and path.is_file():
            try:
                pygame.mixer.music.load(str(path))
                pygame.mixer.music.set_volume(0.0 if self.muted else self.music_vol)
                pygame.mixer.music.play(-1)
            except pygame.error:
                pass

    def _play_ambience(self, amb_id: str | None) -> None:
        if amb_id == self.current_amb:
            return
        self.current_amb = amb_id
        if not self.enabled or self.amb_channel is None:
            return
        self.amb_channel.stop()
        snd = self.sounds.get(amb_id) if amb_id else None
        if snd:
            snd.set_volume(0.0 if self.muted else self.amb_vol)
            self.amb_channel.play(snd, loops=-1)

    def play_scene(self, kind: str, *, combat: bool = False) -> None:
        music, amb = scene_tracks(kind, self.table, combat=combat)
        self._play_music(music)
        self._play_ambience(amb)

    def ambience(self, sound_id: str | None) -> None:
        """Back-compat: treat as a full scene if it looks like a scene id, else amb only."""
        if sound_id and sound_id in (self.table.get("scenes") or {}):
            self.play_scene(sound_id)
            return
        self._play_ambience(sound_id)
