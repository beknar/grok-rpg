from __future__ import annotations

import random

from grok_rpg.affix import roll_gear, roll_rarity
from grok_rpg.data_load import catalog


def test_rarity_seeded() -> None:
    table = catalog()["affixes"]
    a = roll_rarity(random.Random(1), table)
    b = roll_rarity(random.Random(1), table)
    assert a == b


def test_magic_gear_has_affix_stats() -> None:
    data = catalog()
    spec = data["items"]["bone_sword"]
    g = roll_gear("bone_sword", spec, random.Random(3), data["affixes"], rarity="rare")
    assert g.rarity == "rare"
    assert g.stats["power"] >= spec["stats"]["power"]
    assert "Keen" in g.name or "Fierce" in g.name or "Sturdy" in g.name or "Vital" in g.name or "Iron" in g.name
