from __future__ import annotations

import random
from typing import Any

from grok_rpg.inventory import Gear, new_uid


def roll_rarity(rng: random.Random, table: dict[str, Any], *, elite: bool = False) -> str:
    rarities = table["rarities"]
    bonus = int(table.get("elite_rarity_bonus", 0) if elite else 0)
    names = []
    weights = []
    for name, spec in rarities.items():
        w = int(spec["weight"])
        if elite and name != "common":
            w += bonus
        names.append(name)
        weights.append(w)
    return rng.choices(names, weights=weights, k=1)[0]


def roll_gear(
    base_id: str,
    spec: dict[str, Any],
    rng: random.Random,
    table: dict[str, Any],
    *,
    elite: bool = False,
    rarity: str | None = None,
) -> Gear:
    rarity = rarity or roll_rarity(rng, table, elite=elite)
    rspec = table["rarities"][rarity]
    stats = dict(spec.get("stats") or {})
    names: list[str] = []
    pool = list(table["pool"])
    rng.shuffle(pool)
    for aff in pool[: int(rspec["count"])]:
        value = rng.randint(int(aff["min"]), int(aff["max"]))
        stats[aff["stat"]] = int(stats.get(aff["stat"], 0)) + value
        names.append(aff["name"])
    label = spec["name"]
    if names:
        label = f"{' '.join(names)} {label}"
    sell = max(1, int(round(int(spec.get("sell", 1)) * float(rspec["sell_mult"]))))
    return Gear(
        uid=new_uid(rng),
        base_id=base_id,
        name=label,
        rarity=rarity,
        slot=spec["slot"],
        stats=stats,
        ok_classes=list(spec.get("ok_classes") or []),
        icon=spec["icon"],
        sell=sell,
    )
