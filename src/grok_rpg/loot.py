from __future__ import annotations

import random
from typing import Any


def roll_table(table: list[dict[str, Any]], rng: random.Random) -> list[tuple[str, int]]:
    drops: list[tuple[str, int]] = []
    for row in table:
        if rng.random() <= float(row["chance"]):
            lo, hi = row["qty"]
            drops.append((row["item"], rng.randint(int(lo), int(hi))))
    return drops
