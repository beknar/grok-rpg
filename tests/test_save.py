from __future__ import annotations

from pathlib import Path

import pytest

from grok_rpg.inventory import Inventory
from grok_rpg.save import player_state, read_save, write_save


class FakePlayer:
    def __init__(self) -> None:
        self.class_id = "fighter"
        self.x = 12.0
        self.y = 34.0
        self.hp = 99.0
        self.resource = 40.0
        self.inv = Inventory(gold=77)
        self.inv.add("monster_bone", 3)


def test_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "slot1.json"
    state = player_state(FakePlayer(), world_kind="town", world_seed=1337, time=9.5, deaths=2)
    write_save(path, state)
    loaded = read_save(path)
    assert loaded["version"] == 1
    assert loaded["class_id"] == "fighter"
    assert loaded["world_seed"] == 1337
    assert loaded["deaths"] == 2
    assert loaded["player"]["inventory"]["gold"] == 77
    assert loaded["player"]["inventory"]["stacks"]["monster_bone"] == 3


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_save(tmp_path / "nope.json")


def test_bad_version(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    write_save(path, {"version": 99})
    with pytest.raises(ValueError):
        read_save(path)
