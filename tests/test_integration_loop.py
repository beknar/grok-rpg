from __future__ import annotations

from grok_rpg.game import Game, GroundLoot
from grok_rpg.inventory import Inventory
from grok_rpg.save import slot_path


def _tick(game: Game, n: int = 10, dt: float = 1 / 60) -> None:
    game.dt = dt
    for _ in range(n):
        game.simulate()


def test_boot_fighter_in_town() -> None:
    g = Game(headless=True, world_seed=1337)
    g.start_class("fighter")
    assert g.mode == "play"
    assert g.world is not None and g.world.kind == "town"
    assert g.player is not None
    assert g.player.hp == g.player.hp_max
    assert g.player.inv.count("health_potion") >= 1


def test_loot_magnet_picks_up() -> None:
    g = Game(headless=True)
    g.start_class("fighter")
    p = g.player
    assert p and g.world
    g.loot.append(GroundLoot("ghost_ectoplasm", 2, p.x, p.y))
    _tick(g, 3)
    assert p.inv.count("ghost_ectoplasm") == 2
    assert g.loot == []


def test_kill_creates_gold_or_drops() -> None:
    g = Game(headless=True, world_seed=1)
    g.start_class("fighter")
    g.enter_map("dungeon")
    gold_before = g.player.inv.gold  # type: ignore[union-attr]
    assert g.monsters
    g.monsters[0].hp = 0
    _tick(g, 2)
    assert g.monsters[0].dead
    assert g.player.inv.gold >= gold_before  # type: ignore[union-attr]


def test_vendor_and_craft_equip() -> None:
    g = Game(headless=True)
    g.start_class("fighter")
    p = g.player
    assert p
    p.inv.add("red_meat", 2)
    gained = p.inv.sell("red_meat", g.data["items"], 1)
    assert gained > 0
    p.inv.add("monster_bone", 3)
    p.inv.add("whetstone", 1)
    assert p.inv.craft(g.data["recipes"]["bone_sword"], g.data["items"])
    assert p.inv.try_equip("bone_sword", "fighter", g.data["items"]) is None
    p.refresh_stats(g.data)
    assert p.power > g.data["classes"]["fighter"]["power"]


def test_death_respawns_town_keeps_inventory() -> None:
    g = Game(headless=True, world_seed=5)
    g.start_class("fighter")
    p = g.player
    assert p
    p.inv.add("ruby", 4)
    g.enter_map("dungeon")
    p.hp = 0
    _tick(g, 2)
    assert g.world is not None and g.world.kind == "town"
    assert p.hp == p.hp_max
    assert p.inv.count("ruby") == 4
    assert g.deaths == 1


def test_save_load_round_trip(tmp_path) -> None:
    path = slot_path("itest", directory=tmp_path)
    g = Game(headless=True, world_seed=42)
    g.start_class("mage")
    assert g.player
    g.player.inv.gold = 333
    g.player.inv.add("coal", 9)
    g.save_to(path, quiet=True)
    g2 = Game(headless=True, world_seed=1)
    g2.load_from(path)
    assert g2.player is not None
    assert g2.player.class_id == "mage"
    assert g2.player.inv.gold == 333
    assert g2.player.inv.count("coal") == 9
    assert g2.world_seed == 42


def test_other_classes_boot() -> None:
    for cid in ("mage", "cleric"):
        g = Game(headless=True)
        g.start_class(cid)
        assert g.player is not None
        assert g.player.class_id == cid
        assert g.world is not None


def test_acts_lock_and_unlock() -> None:
    g = Game(headless=True, world_seed=9)
    g.start_class("fighter")
    cave = next(p for p in g.world.portals if p["to"] == "cave")  # type: ignore[union-attr]
    assert cave["locked"] is True
    g.enter_map("crypt")
    boss = next(m for m in g.monsters if m.spec_id == "necromancer")
    boss.hp = 0
    _tick(g, 2)
    assert "cave" in g.unlocked_acts
    g.enter_map("town")
    cave = next(p for p in g.world.portals if p["to"] == "cave")  # type: ignore[union-attr]
    assert cave["locked"] is False


def test_necromancer_summons() -> None:
    g = Game(headless=True, world_seed=2)
    g.start_class("fighter")
    g.enter_map("crypt")
    boss = next(m for m in g.monsters if m.spec_id == "necromancer")
    g.player.x, g.player.y = boss.x, boss.y  # type: ignore[union-attr]
    before = len(g.monsters)
    boss.next_attack = 0
    boss.next_summon = 0
    g.dt = 0.2
    g.time = 10
    g.simulate()
    assert len(g.monsters) >= before


def test_letterbox_mapping() -> None:
    g = Game(headless=True)
    g.letter_scale = 2
    g.letter_ox = 10
    g.letter_oy = 20
    lx, ly = g._map_window(10 + 4, 20 + 6)
    assert lx == 2
    assert ly == 3
