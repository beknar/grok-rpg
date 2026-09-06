from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from grok_rpg.paths import SAVES_DIR

SAVE_VERSION = 2


def slot_path(slot: str = "slot1", directory: Path | None = None) -> Path:
    root = directory or SAVES_DIR
    name = slot if slot.endswith(".json") else f"{slot}.json"
    return root / name


def write_save(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    tmp.replace(path)


def read_save(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"No save at {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    ver = int(data.get("version", 0))
    if ver not in (1, 2):
        raise ValueError(f"Unsupported save version {data.get('version')}")
    if ver == 1:
        data["version"] = 2
        data.setdefault("unlocked_acts", ["crypt"])
        inv = data.get("player", {}).get("inventory", {})
        inv.setdefault("gear", [])
    data.setdefault("unlocked_acts", ["crypt"])
    return data


def player_state(
    player: Any,
    *,
    world_kind: str,
    world_seed: int,
    time: float,
    deaths: int,
    unlocked_acts: list[str],
) -> dict[str, Any]:
    return {
        "version": SAVE_VERSION,
        "class_id": player.class_id,
        "world_kind": world_kind,
        "world_seed": int(world_seed),
        "time": float(time),
        "deaths": int(deaths),
        "unlocked_acts": list(unlocked_acts),
        "player": {
            "x": float(player.x),
            "y": float(player.y),
            "hp": float(player.hp),
            "resource": float(player.resource),
            "inventory": player.inv.to_dict(),
        },
    }
