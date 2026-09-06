from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from grok_rpg.paths import DATA_DIR


def load_json(name: str) -> Any:
    path = DATA_DIR / name
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=None)
def catalog() -> dict[str, Any]:
    return {
        "classes": load_json("classes.json"),
        "abilities": load_json("abilities.json"),
        "monsters": load_json("monsters.json"),
        "items": load_json("items.json"),
        "loot_tables": load_json("loot_tables.json"),
        "recipes": load_json("recipes.json"),
        "input": load_json("input.json"),
    }


def validate_catalog(data: dict[str, Any] | None = None) -> list[str]:
    data = data or catalog()
    errors: list[str] = []
    abilities = data["abilities"]
    items = data["items"]
    for cid, cls in data["classes"].items():
        for aid in cls["abilities"]:
            if aid not in abilities:
                errors.append(f"class {cid} missing ability {aid}")
    for mid, mon in data["monsters"].items():
        table = mon.get("loot_table")
        if table not in data["loot_tables"]:
            errors.append(f"monster {mid} loot_table {table} missing")
    for table, rows in data["loot_tables"].items():
        for row in rows:
            if row["item"] not in items:
                errors.append(f"loot {table} unknown item {row['item']}")
    for rid, rec in data["recipes"].items():
        if rec["output"] not in items:
            errors.append(f"recipe {rid} output missing")
        for iid in rec["inputs"]:
            if iid not in items:
                errors.append(f"recipe {rid} input {iid} missing")
    return errors
