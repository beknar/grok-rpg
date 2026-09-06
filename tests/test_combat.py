from grok_rpg.combat import CooldownBank, try_cast
from grok_rpg.data_load import catalog


class Caster:
    def __init__(self) -> None:
        self.x = 0.0
        self.y = 0.0
        self.hp = 100.0
        self.hp_max = 100.0
        self.power = 18.0
        self.resource = 100.0
        self.resource_max = 100.0
        self.cooldowns = CooldownBank()
        self.attack_timer = 0.0
        self.shield = 0.0
        self.radius = 20
        self.tags: list[str] = []


class Foe:
    def __init__(self) -> None:
        self.x = 40.0
        self.y = 0.0
        self.hp = 50.0
        self.radius = 20
        self.tags = ["undead"]
        self.stun_until = 0.0
        self.slow = 0.0
        self.slow_until = 0.0
        self.shield = 0.0


def test_slash_hits_and_uses_slash_vfx() -> None:
    ab = catalog()["abilities"]["fighter.slash"]
    c, m = Caster(), Foe()
    events = try_cast(
        caster=c, ability_id="fighter.slash", ability=ab, now=0.0,
        aim_x=50, aim_y=0, targets=[m], spawn=lambda *_: None,
    )
    assert m.hp < 50
    assert any(e.vfx == "vfx.slash" for e in events)


def test_fireball_spawns_projectile() -> None:
    ab = catalog()["abilities"]["mage.fireball"]
    spawned: list[str] = []
    try_cast(
        caster=Caster(), ability_id="mage.fireball", ability=ab, now=0.0,
        aim_x=80, aim_y=0, targets=[], spawn=lambda k, p: spawned.append(p["vfx"]),
    )
    assert spawned == ["vfx.fireball"]


def test_heal_uses_holy_bless() -> None:
    ab = catalog()["abilities"]["cleric.heal"]
    c = Caster()
    c.hp = 40
    events = try_cast(
        caster=c, ability_id="cleric.heal", ability=ab, now=0.0,
        aim_x=0, aim_y=0, targets=[], spawn=lambda *_: None,
    )
    assert c.hp > 40
    assert events[0].vfx == "vfx.holy_bless"
