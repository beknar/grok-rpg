from __future__ import annotations

from typing import Any

from grok_rpg.inventory import Inventory


def sell_one(inv: Inventory, item_id: str, items: dict[str, Any]) -> int:
    return inv.sell(item_id, items, 1)
