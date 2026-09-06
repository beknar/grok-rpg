from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable


def dist(ax: float, ay: float, bx: float, by: float) -> float:
    return math.hypot(bx - ax, by - ay)


def norm(dx: float, dy: float) -> tuple[float, float]:
    length = math.hypot(dx, dy)
    if length <= 1e-6:
        return (0.0, 0.0)
    return (dx / length, dy / length)


def angle_of(dx: float, dy: float) -> float:
    return math.atan2(dy, dx)


def angle_delta(a: float, b: float) -> float:
    d = (a - b + math.pi) % (math.tau) - math.pi
    return abs(d)


def aabb_hit(ax: float, ay: float, ar: float, bx: float, by: float, br: float) -> bool:
    return abs(ax - bx) < ar + br and abs(ay - by) < ar + br


@dataclass
class CooldownBank:
    ready_at: dict[str, float] = field(default_factory=dict)

    def ready(self, ability_id: str, now: float) -> bool:
        return now >= self.ready_at.get(ability_id, 0.0)

    def trigger(self, ability_id: str, now: float, cooldown: float) -> None:
        self.ready_at[ability_id] = now + cooldown


@dataclass
class CombatEvent:
    kind: str
    x: float
    y: float
    damage: float = 0.0
    heal: float = 0.0
    source: Any = None
    target: Any = None
    vfx: str | None = None
    sfx: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


def undead_mult(ability: dict[str, Any], tags: list[str]) -> float:
    if "undead" in tags:
        return float(ability.get("undead_mult", 1.0))
    return 1.0


def apply_damage(target: Any, amount: float) -> float:
    shield = float(getattr(target, "shield", 0.0) or 0.0)
    if shield > 0:
        used = min(shield, amount)
        target.shield = shield - used
        amount -= used
    if amount <= 0:
        return 0.0
    target.hp = max(0.0, float(target.hp) - amount)
    return amount


def try_cast(
    *,
    caster: Any,
    ability_id: str,
    ability: dict[str, Any],
    now: float,
    aim_x: float,
    aim_y: float,
    targets: list[Any],
    spawn: Callable[[str, dict[str, Any]], None],
) -> list[CombatEvent]:
    events: list[CombatEvent] = []
    if not caster.cooldowns.ready(ability_id, now):
        return events
    cost = float(ability.get("cost", 0))
    resource = ability.get("resource")
    if resource and cost > 0 and float(getattr(caster, "resource", 0)) < cost:
        return events
    if resource and cost > 0:
        caster.resource -= cost

    kind = ability["kind"]
    dmg_base = float(ability.get("damage", 0)) + float(getattr(caster, "power", 0)) * 0.35
    vfx = ability.get("vfx")
    sfx = ability.get("sfx")
    dx, dy = norm(aim_x - caster.x, aim_y - caster.y)
    if dx == 0 and dy == 0:
        dx, dy = 0.0, 1.0
    facing = angle_of(dx, dy)

    def hit_target(t: Any, amount: float) -> None:
        dealt = apply_damage(t, amount * undead_mult(ability, getattr(t, "tags", [])))
        if dealt > 0:
            events.append(CombatEvent("hit", t.x, t.y, damage=dealt, source=caster, target=t, vfx=vfx, sfx=sfx))
            stun = float(ability.get("stun", 0) or 0)
            if stun:
                t.stun_until = max(getattr(t, "stun_until", 0.0), now + stun)
            slow = float(ability.get("slow", 0) or 0)
            if slow:
                t.slow = slow
                t.slow_until = now + float(ability.get("slow_time", 1.5))

    if kind == "melee_arc":
        reach = float(ability["range"])
        arc = math.radians(float(ability.get("arc", 90)))
        for t in targets:
            if t is caster or getattr(t, "hp", 0) <= 0:
                continue
            if dist(caster.x, caster.y, t.x, t.y) > reach + getattr(t, "radius", 20):
                continue
            ang = angle_of(t.x - caster.x, t.y - caster.y)
            if angle_delta(ang, facing) <= arc / 2:
                hit_target(t, dmg_base)
        events.append(CombatEvent("vfx", caster.x + dx * 40, caster.y + dy * 40, vfx=vfx, sfx=sfx, source=caster))
        if ability.get("rage_gain"):
            caster.resource = min(caster.resource_max, caster.resource + float(ability["rage_gain"]))

    elif kind == "nova":
        reach = float(ability["range"])
        for t in targets:
            if t is caster or getattr(t, "hp", 0) <= 0:
                continue
            if dist(caster.x, caster.y, t.x, t.y) <= reach + getattr(t, "radius", 20):
                hit_target(t, dmg_base)
        events.append(CombatEvent("vfx", caster.x, caster.y, vfx=vfx, sfx=sfx, source=caster))

    elif kind == "projectile":
        spawn("projectile", {
            "x": caster.x,
            "y": caster.y,
            "dx": dx,
            "dy": dy,
            "speed": float(ability.get("speed", 400)),
            "damage": dmg_base,
            "range": float(ability.get("range", 400)),
            "aoe": float(ability.get("aoe", 0)),
            "ability": ability,
            "caster": caster,
            "vfx": vfx,
            "impact_vfx": ability.get("impact_vfx"),
            "sfx": sfx,
        })
        events.append(CombatEvent("vfx", caster.x, caster.y, vfx=vfx, sfx=sfx, source=caster))

    elif kind == "bolt":
        reach = float(ability["range"])
        best = None
        best_d = 1e9
        for t in targets:
            if t is caster or getattr(t, "hp", 0) <= 0:
                continue
            d = dist(caster.x, caster.y, t.x, t.y)
            if d < best_d and d <= reach:
                best, best_d = t, d
        if best:
            hit_target(best, dmg_base)
        events.append(CombatEvent("vfx", aim_x, aim_y, vfx=vfx, sfx=sfx, source=caster))

    elif kind == "dash":
        spawn("dash", {
            "caster": caster,
            "dx": dx,
            "dy": dy,
            "range": float(ability.get("range", 200)),
            "damage": dmg_base,
            "ability": ability,
            "vfx": vfx,
            "sfx": sfx,
        })
        events.append(CombatEvent("vfx", caster.x, caster.y, vfx=vfx, sfx=sfx, source=caster))

    elif kind == "blink":
        reach = float(ability.get("range", 200))
        caster.x += dx * reach
        caster.y += dy * reach
        events.append(CombatEvent("vfx", caster.x, caster.y, vfx=vfx, sfx=sfx, source=caster))

    elif kind == "self_heal":
        heal = float(ability.get("heal", 0))
        caster.hp = min(caster.hp_max, caster.hp + heal)
        events.append(CombatEvent("heal", caster.x, caster.y, heal=heal, source=caster, target=caster, vfx=vfx, sfx=sfx))

    elif kind == "self_buff":
        caster.shield = float(ability.get("shield", 0))
        caster.shield_until = now + float(ability.get("duration", 5))
        events.append(CombatEvent("vfx", caster.x, caster.y, vfx=vfx, sfx=sfx, source=caster))

    elif kind == "ground_aoe":
        spawn("aoe", {
            "x": caster.x,
            "y": caster.y,
            "radius": float(ability.get("range", 100)),
            "damage": dmg_base,
            "ticks": int(ability.get("ticks", 4)),
            "interval": float(ability.get("tick_interval", 0.4)),
            "ability": ability,
            "caster": caster,
            "vfx": vfx,
            "sfx": sfx,
        })
        events.append(CombatEvent("vfx", caster.x, caster.y, vfx=vfx, sfx=sfx, source=caster))

    caster.cooldowns.trigger(ability_id, now, float(ability.get("cooldown", 0.5)))
    caster.attack_timer = 0.35
    return events
