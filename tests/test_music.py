from __future__ import annotations

from grok_rpg.audio import scene_tracks
from grok_rpg.data_load import catalog
from grok_rpg.manifest import default_jobs


def test_every_scene_has_music_id() -> None:
    table = catalog()["music"]
    for kind in ("title", "town", "crypt", "cave", "castle", "boss"):
        music, _amb = scene_tracks(kind, table)
        assert music, kind
        assert music.startswith("music.")


def test_boss_uses_battle_track() -> None:
    table = catalog()["music"]
    music, amb = scene_tracks("crypt", table, combat=True)
    assert music == "music.boss"
    assert amb == "amb.dungeon"


def test_music_ids_are_in_manifest() -> None:
    ids = {j["id"] for j in default_jobs()}
    table = catalog()["music"]
    for spec in table["scenes"].values():
        if spec.get("music"):
            assert spec["music"] in ids
        if spec.get("ambience"):
            assert spec["ambience"] in ids


def test_mute_toggle_headless() -> None:
    from grok_rpg.audio import Audio

    audio = Audio(catalog()["music"])
    first = audio.muted
    audio.toggle_mute()
    assert audio.muted is (not first)
    audio.set_muted(False)
    audio.play_scene("title")
    audio.play_scene("town", combat=True)
    audio.play_scene("town", combat=False)
