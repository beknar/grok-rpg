from __future__ import annotations

import random

from grok_rpg.constants import TILE
from grok_rpg.world import WALL_SOLID, make_dungeon, make_town


def test_town_seed_stable() -> None:
    a = make_town(random.Random(42), seed=42)
    b = make_town(random.Random(42), seed=42)
    assert a.tiles == b.tiles
    assert a.npcs[0]["role"] == "vendor"
    assert any(p["to"] == "crypt" for p in a.portals)
    cave = next(p for p in a.portals if p["to"] == "cave")
    assert cave["locked"] is True


def test_dungeon_seed_stable() -> None:
    a = make_dungeon(random.Random(99), seed=99)
    b = make_dungeon(random.Random(99), seed=99)
    assert a.tiles == b.tiles
    assert a.spawns == b.spawns
    assert a.spawns[-1][0] == "necromancer"


def test_wall_blocks_movement() -> None:
    world = make_town(random.Random(1), seed=1)
    assert world.blocked[0][0]
    assert world.tiles[0][0] == WALL_SOLID
    x, y = TILE * 3 + 64, TILE * 3 + 64
    assert world.walkable_px(x, y, 16)
    nx, ny = x, y
    for _ in range(40):
        nx, ny = world.clamp_move(nx, ny, nx - 50, ny, 16)
    assert nx > 20
    assert world.walkable_px(nx, ny, 16)
