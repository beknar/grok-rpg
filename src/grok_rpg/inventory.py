from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import random

SLOTS = ("weapon", "offhand", "head", "chest", "legs", "feet", "ring", "amulet")


def new_uid(rng: random.Random | None = None) -> str:
    rng = rng or random.Random()
    return f"g{rng.randrange(1_000_000_000):09d}"


@dataclass
class Gear:
    uid: str
    base_id: str
    name: str
    rarity: str
    slot: str
    stats: dict[str, int]
    ok_classes: list[str]
    icon: str
    sell: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "uid": self.uid,
            "base_id": self.base_id,
            "name": self.name,
            "rarity": self.rarity,
            "slot": self.slot,
            "stats": dict(self.stats),
            "ok_classes": list(self.ok_classes),
            "icon": self.icon,
            "sell": self.sell,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Gear:
        return cls(
            uid=str(data["uid"]),
            base_id=str(data["base_id"]),
            name=str(data["name"]),
            rarity=str(data.get("rarity", "common")),
            slot=str(data["slot"]),
            stats={k: int(v) for k, v in (data.get("stats") or {}).items()},
            ok_classes=list(data.get("ok_classes") or []),
            icon=str(data["icon"]),
            sell=int(data.get("sell", 1)),
        )

    @classmethod
    def from_base(cls, base_id: str, spec: dict[str, Any], rng: random.Random | None = None) -> Gear:
        return cls(
            uid=new_uid(rng),
            base_id=base_id,
            name=spec["name"],
            rarity=str(spec.get("rarity", "common")),
            slot=spec["slot"],
            stats=dict(spec.get("stats") or {}),
            ok_classes=list(spec.get("ok_classes") or []),
            icon=spec["icon"],
            sell=int(spec.get("sell", 1)),
        )


@dataclass
class Inventory:
    gold: int = 0
    stacks: dict[str, int] = field(default_factory=dict)
    gear: list[Gear] = field(default_factory=list)
    equipped: dict[str, str | None] = field(default_factory=lambda: {s: None for s in SLOTS})

    def add(self, item_id: str, qty: int = 1) -> None:
        if item_id == "gold":
            self.gold += qty
            return
        self.stacks[item_id] = self.stacks.get(item_id, 0) + qty

    def add_gear(self, piece: Gear) -> None:
        self.gear.append(piece)

    def find_gear(self, uid: str) -> Gear | None:
        for g in self.gear:
            if g.uid == uid:
                return g
        return None

    def count(self, item_id: str) -> int:
        if item_id == "gold":
            return self.gold
        stacked = self.stacks.get(item_id, 0)
        as_gear = sum(1 for g in self.gear if g.base_id == item_id)
        return stacked + as_gear

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

    def craft(self, recipe: dict[str, Any], items: dict[str, Any] | None = None) -> bool:
        if not self.can_craft(recipe):
            return False
        for iid, q in recipe["inputs"].items():
            self.remove(iid, q)
        out_id = recipe["output"]
        qty = int(recipe.get("qty", 1))
        spec = (items or {}).get(out_id)
        if spec and spec.get("kind") == "equipment":
            for _ in range(qty):
                self.gear.append(Gear.from_base(out_id, spec))
            return True
        self.add(out_id, qty)
        return True

    def sell(self, item_id: str, items: dict[str, Any], qty: int = 1) -> int:
        gear = self.find_gear(item_id)
        if gear is None:
            for g in self.gear:
                if g.base_id == item_id:
                    gear = g
                    break
        if gear:
            if self.equipped.get(gear.slot) == gear.uid:
                self.equipped[gear.slot] = None
            self.gear = [g for g in self.gear if g.uid != gear.uid]
            value = max(1, gear.sell // 2) if gear.rarity != "common" else max(1, gear.sell // 2)
            self.gold += value
            return value
        spec = items.get(item_id)
        if not spec or spec.get("kind") == "gold":
            return 0
        if not self.remove(item_id, qty):
            return 0
        value = int(spec.get("sell", 1)) * qty
        if spec.get("kind") == "equipment":
            value = max(1, value // 2)
        self.gold += value
        return value

    def try_equip(self, item_id: str, class_id: str, items: dict[str, Any]) -> str | None:
        piece = self.find_gear(item_id)
        if piece is None:
            for g in self.gear:
                if g.base_id == item_id:
                    piece = g
                    break
        if piece is None:
            spec = items.get(item_id)
            if not spec or spec.get("kind") != "equipment":
                return "Not equipment."
            if spec.get("ok_classes") and class_id not in spec["ok_classes"]:
                return "Wrong class."
            if not self.remove(item_id, 1):
                return "You do not have that."
            piece = Gear.from_base(item_id, spec)
            self.gear.append(piece)
        elif piece.ok_classes and class_id not in piece.ok_classes:
            return "Wrong class."
        self.equipped[piece.slot] = piece.uid
        return None

    def stat_bonus(self, items: dict[str, Any], stat: str) -> int:
        total = 0
        for uid in self.equipped.values():
            if not uid:
                continue
            piece = self.find_gear(uid)
            if piece:
                total += int(piece.stats.get(stat, 0))
                continue
            spec = items.get(uid)
            if spec:
                total += int(spec.get("stats", {}).get(stat, 0))
        return total

    def to_dict(self) -> dict[str, Any]:
        return {
            "gold": self.gold,
            "stacks": dict(self.stacks),
            "equipped": dict(self.equipped),
            "gear": [g.to_dict() for g in self.gear],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], items: dict[str, Any] | None = None) -> Inventory:
        inv = cls(gold=int(data.get("gold", 0)), stacks=dict(data.get("stacks") or {}))
        inv.gear = [Gear.from_dict(g) for g in data.get("gear") or []]
        equipped = dict(data.get("equipped") or {})
        # v1 saves stored base item ids in equipped + stacks
        if items:
            for slot, val in list(equipped.items()):
                if not val:
                    continue
                if inv.find_gear(val):
                    continue
                spec = items.get(val)
                if spec and spec.get("kind") == "equipment":
                    piece = Gear.from_base(val, spec)
                    inv.gear.append(piece)
                    equipped[slot] = piece.uid
                    inv.stacks.pop(val, None)
        inv.equipped.update(equipped)
        return inv
