from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


SLOTS = ("weapon", "offhand", "head", "chest", "legs", "feet", "ring", "amulet")


@dataclass
class Inventory:
    gold: int = 0
    stacks: dict[str, int] = field(default_factory=dict)
    equipped: dict[str, str | None] = field(default_factory=lambda: {s: None for s in SLOTS})

    def add(self, item_id: str, qty: int = 1) -> None:
        if item_id == "gold":
            self.gold += qty
            return
        self.stacks[item_id] = self.stacks.get(item_id, 0) + qty

    def count(self, item_id: str) -> int:
        if item_id == "gold":
            return self.gold
        return self.stacks.get(item_id, 0)

    def remove(self, item_id: str, qty: int = 1) -> bool:
        if item_id == "gold":
            if self.gold < qty:
                return False
            self.gold -= qty
            return True
        have = self.stacks.get(item_id, 0)
        if have < qty:
            return False
        left = have - qty
        if left:
            self.stacks[item_id] = left
        else:
            self.stacks.pop(item_id, None)
        return True

    def can_craft(self, recipe: dict[str, Any]) -> bool:
        return all(self.count(i) >= q for i, q in recipe["inputs"].items())

    def craft(self, recipe: dict[str, Any]) -> bool:
        if not self.can_craft(recipe):
            return False
        for iid, q in recipe["inputs"].items():
            self.remove(iid, q)
        self.add(recipe["output"], int(recipe.get("qty", 1)))
        return True

    def sell(self, item_id: str, items: dict[str, Any], qty: int = 1) -> int:
        spec = items[item_id]
        if spec.get("kind") == "gold":
            return 0
        if not self.remove(item_id, qty):
            return 0
        value = int(spec.get("sell", 1)) * qty
        if spec.get("kind") == "equipment":
            value = max(1, value // 2)
        self.gold += value
        return value

    def try_equip(self, item_id: str, class_id: str, items: dict[str, Any]) -> str | None:
        spec = items.get(item_id)
        if not spec or spec.get("kind") != "equipment":
            return "Not equipment."
        ok = spec.get("ok_classes") or []
        if ok and class_id not in ok:
            return "Wrong class."
        if self.count(item_id) < 1:
            return "You do not have that."
        slot = spec["slot"]
        prev = self.equipped.get(slot)
        self.remove(item_id, 1)
        if prev:
            self.add(prev, 1)
        self.equipped[slot] = item_id
        return None

    def stat_bonus(self, items: dict[str, Any], stat: str) -> int:
        total = 0
        for item_id in self.equipped.values():
            if not item_id:
                continue
            total += int(items[item_id].get("stats", {}).get(stat, 0))
        return total

    def to_dict(self) -> dict[str, Any]:
        return {"gold": self.gold, "stacks": dict(self.stacks), "equipped": dict(self.equipped)}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Inventory:
        inv = cls(gold=int(data.get("gold", 0)), stacks=dict(data.get("stacks") or {}))
        inv.equipped.update(data.get("equipped") or {})
        return inv
