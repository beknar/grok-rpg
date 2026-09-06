from __future__ import annotations

from typing import Any

from grok_rpg.inventory import Inventory


def craft_recipe(inv: Inventory, recipe: dict[str, Any], items: dict[str, Any] | None = None) -> bool:
    return inv.craft(recipe, items)
