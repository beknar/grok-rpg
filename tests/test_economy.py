import random

from grok_rpg.combat import aabb_hit, apply_damage
from grok_rpg.data_load import catalog
from grok_rpg.inventory import Inventory
from grok_rpg.loot import roll_table


class Dummy:
    def __init__(self) -> None:
        self.hp = 50
        self.shield = 10


def test_craft_and_sell() -> None:
    data = catalog()
    inv = Inventory()
    inv.add("monster_bone", 3)
    inv.add("whetstone", 1)
    rec = data["recipes"]["bone_sword"]
    assert inv.craft(rec, data["items"])
    assert inv.count("bone_sword") == 1
    assert inv.count("monster_bone") == 0
    gained = inv.sell("bone_sword", data["items"], 1)
    assert gained == 12  # 25 // 2
    assert inv.gold == 12


def test_class_gate() -> None:
    data = catalog()
    inv = Inventory()
    inv.add("bone_sword", 1)
    err = inv.try_equip("bone_sword", "mage", data["items"])
    assert err
    err = inv.try_equip("bone_sword", "fighter", data["items"])
    assert err is None
    uid = inv.equipped["weapon"]
    assert uid
    assert inv.find_gear(uid).base_id == "bone_sword"


def test_loot_seeded() -> None:
    table = catalog()["loot_tables"]["ghost"]
    a = roll_table(table, random.Random(1))
    b = roll_table(table, random.Random(1))
    assert a == b


def test_aabb_and_shield() -> None:
    assert aabb_hit(0, 0, 10, 15, 0, 10)
    assert not aabb_hit(0, 0, 5, 40, 0, 5)
    d = Dummy()
    dealt = apply_damage(d, 12)
    assert dealt == 2
    assert d.hp == 48
    assert d.shield == 0
