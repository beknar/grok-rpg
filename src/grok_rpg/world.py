from __future__ import annotations

import random
from dataclasses import dataclass, field

from grok_rpg.constants import TILE

# tile.palette frame indices from the baker grid_cells list
FLOOR_DUNGEON = 0
FLOOR_DUNGEON_2 = 1
WALL = 2
WALL_SOLID = 3
GRASS = 5
GRASS_2 = 6
PATH = 7
FLOOR_DARK = 11


@dataclass
class World:
    width: int
    height: int
    tiles: list[list[int]]
    blocked: list[list[bool]]
    spawns: list[tuple[str, float, float]] = field(default_factory=list)
    npcs: list[dict] = field(default_factory=list)
    portals: list[dict] = field(default_factory=list)
    player_start: tuple[float, float] = (TILE * 3, TILE * 3)
    kind: str = "dungeon"
    seed: int = 0

    def in_bounds(self, tx: int, ty: int) -> bool:
        return 0 <= tx < self.width and 0 <= ty < self.height

    def walkable_px(self, x: float, y: float, radius: float = 16) -> bool:
        for ox, oy in ((-radius, 0), (radius, 0), (0, -radius), (0, radius), (0, 0)):
            tx = int((x + ox) // TILE)
            ty = int((y + oy) // TILE)
            if not self.in_bounds(tx, ty) or self.blocked[ty][tx]:
                return False
        return True

    def clamp_move(self, x: float, y: float, nx: float, ny: float, radius: float = 16) -> tuple[float, float]:
        if self.walkable_px(nx, y, radius):
            x = nx
        if self.walkable_px(x, ny, radius):
            y = ny
        return x, y


def _fill(w: int, h: int, tile: int, blocked: bool) -> tuple[list[list[int]], list[list[bool]]]:
    tiles = [[tile for _ in range(w)] for _ in range(h)]
    block = [[blocked for _ in range(w)] for _ in range(h)]
    return tiles, block


def make_town(rng: random.Random, seed: int = 0) -> World:
    w, h = 24, 16
    tiles, block = _fill(w, h, GRASS, False)
    for y in range(h):
        for x in range(w):
            if rng.random() < 0.35:
                tiles[y][x] = GRASS_2
            if x == 0 or y == 0 or x == w - 1 or y == h - 1:
                tiles[y][x] = WALL_SOLID
                block[y][x] = True
    # path down the middle
    for y in range(2, h - 2):
        tiles[y][w // 2] = PATH
        tiles[y][w // 2 + 1] = PATH
        block[y][w // 2] = False
        block[y][w // 2 + 1] = False
    for x in range(3, w - 3):
        tiles[h // 2][x] = PATH
        block[h // 2][x] = False
    world = World(w, h, tiles, block, kind="town", seed=seed)
    world.player_start = ((w // 2) * TILE + 64, (h - 4) * TILE)
    world.npcs = [
        {"id": "vendor", "sprite": "npc.vendor", "name": "Butcher", "x": 6 * TILE, "y": 6 * TILE, "role": "vendor"},
        {"id": "inn", "sprite": "npc.inn", "name": "Innkeep", "x": 17 * TILE, "y": 6 * TILE, "role": "inn"},
        {"id": "craft", "sprite": "npc.librarian", "name": "Artificer", "x": 6 * TILE, "y": 11 * TILE, "role": "craft"},
        {"id": "trainer", "sprite": "npc.trainer", "name": "Trainer", "x": 17 * TILE, "y": 11 * TILE, "role": "flavor"},
    ]
    world.portals = [{"to": "dungeon", "x": (w // 2) * TILE, "y": 2 * TILE, "label": "Crypt"}]
    return world


def make_dungeon(rng: random.Random, seed: int = 0) -> World:
    w, h = 40, 30
    tiles, block = _fill(w, h, WALL_SOLID, True)
    rooms: list[tuple[int, int, int, int]] = []
    for _ in range(12):
        rw, rh = rng.randint(5, 9), rng.randint(5, 8)
        x = rng.randint(1, w - rw - 2)
        y = rng.randint(1, h - rh - 2)
        rooms.append((x, y, rw, rh))
        for yy in range(y, y + rh):
            for xx in range(x, x + rw):
                tiles[yy][xx] = FLOOR_DUNGEON if rng.random() > 0.2 else FLOOR_DUNGEON_2
                block[yy][xx] = False
    # corridors between consecutive rooms
    centers = [(x + rw // 2, y + rh // 2) for x, y, rw, rh in rooms]
    for (x0, y0), (x1, y1) in zip(centers, centers[1:]):
        cx, cy = x0, y0
        while cx != x1:
            tiles[cy][cx] = FLOOR_DARK
            block[cy][cx] = False
            cx += 1 if x1 > cx else -1
        while cy != y1:
            tiles[cy][cx] = FLOOR_DARK
            block[cy][cx] = False
            cy += 1 if y1 > cy else -1
    world = World(w, h, tiles, block, kind="dungeon", seed=seed)
    sx, sy = centers[0]
    world.player_start = (sx * TILE + 64, sy * TILE + 64)
    world.portals = [{"to": "town", "x": sx * TILE + 64, "y": sy * TILE + 64, "label": "Town"}]

    roster = [
        "dungeon_minion_01",
        "dungeon_minion_02",
        "dungeon_minion_03",
        "undead_ghost",
        "elemental_salamander",
        "beast_beaver",
        "enemy_mage",
    ]
    for cx, cy in centers[1:-1]:
        kind = rng.choice(roster)
        world.spawns.append((kind, cx * TILE + 64, cy * TILE + 64))
        if rng.random() < 0.5:
            extra = rng.choice(roster[:3])
            world.spawns.append((extra, cx * TILE + 20, cy * TILE + 90))
    bx, by = centers[-1]
    world.spawns.append(("necromancer", bx * TILE + 64, by * TILE + 64))
    return world
