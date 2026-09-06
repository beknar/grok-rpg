from __future__ import annotations

import math
import os
import random
from dataclasses import dataclass, field
from typing import Any

import pygame

from grok_rpg.audio import Audio
from grok_rpg.combat import CooldownBank, aabb_hit, apply_damage, dist, norm, try_cast, undead_mult
from grok_rpg.constants import FPS, HITBOX, LOOT_MAGNET, TILE, VIEW_H, VIEW_W
from grok_rpg.data_load import catalog, validate_catalog
from grok_rpg.inventory import Inventory
from grok_rpg.loot import roll_table
from grok_rpg.save import player_state, read_save, slot_path, write_save
from grok_rpg.sprites import Animator, SpriteBank
from grok_rpg.ui import hud, panel_craft, panel_inventory, panel_vendor
from grok_rpg.world import World, make_dungeon, make_town


def facing_from(dx: float, dy: float) -> str:
    if abs(dx) > abs(dy):
        return "right" if dx > 0 else "left"
    return "down" if dy >= 0 else "up"


@dataclass
class Vfx:
    sprite_id: str
    x: float
    y: float
    anim: Animator = field(default_factory=Animator)
    life: float = 0.45

    def __post_init__(self) -> None:
        self.anim.play(self.sprite_id, True)


@dataclass
class Projectile:
    x: float
    y: float
    dx: float
    dy: float
    speed: float
    damage: float
    range: float
    aoe: float
    caster: Any
    ability: dict
    vfx: str | None
    impact_vfx: str | None
    sfx: str | None
    traveled: float = 0.0
    dead: bool = False


@dataclass
class Aoe:
    x: float
    y: float
    radius: float
    damage: float
    ticks: int
    interval: float
    ability: dict
    caster: Any
    vfx: str | None
    sfx: str | None
    timer: float = 0.0


@dataclass
class GroundLoot:
    item_id: str
    qty: int
    x: float
    y: float


@dataclass
class Floater:
    text: str
    x: float
    y: float
    life: float = 0.9
    color: tuple[int, int, int] = (255, 220, 120)


class Actor:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.hp = 1.0
        self.hp_max = 1.0
        self.radius = HITBOX // 2
        self.facing = "down"
        self.stun_until = 0.0
        self.slow = 0.0
        self.slow_until = 0.0
        self.shield = 0.0
        self.shield_until = 0.0
        self.attack_timer = 0.0
        self.anim = Animator()
        self.tags: list[str] = []
        self.power = 0.0
        self.armor = 0.0
        self.cooldowns = CooldownBank()
        self.now = 0.0
        self.resource = 0.0
        self.resource_max = 0.0
        self.resource_name = "mana"
        self.dead = False


class Player(Actor):
    def __init__(self, class_id: str, data: dict[str, Any]) -> None:
        super().__init__(0, 0)
        spec = data["classes"][class_id]
        self.class_id = class_id
        self.hp = self.hp_max = float(spec["hp"])
        self.resource = 0.0 if spec["resource"] == "rage" else float(spec["resource_max"])
        self.resource_max = float(spec["resource_max"])
        self.resource_name = spec["resource"]
        self.speed = float(spec["speed"])
        self.armor = float(spec["armor"])
        self.power = float(spec["power"])
        self.ability_ids = list(spec["abilities"])
        self.inv = Inventory(gold=20)
        self.inv.add("whetstone", 1)
        self.inv.add("health_potion", 2)
        self.click_target: tuple[float, float] | None = None
        self._inv_hit: list = []
        self._vendor_hit: list = []
        self._craft_hit: list = []

    def refresh_stats(self, data: dict[str, Any]) -> None:
        spec = data["classes"][self.class_id]
        self.hp_max = float(spec["hp"]) + self.inv.stat_bonus(data["items"], "hp")
        self.power = float(spec["power"]) + self.inv.stat_bonus(data["items"], "power")
        self.armor = float(spec["armor"]) + self.inv.stat_bonus(data["items"], "armor")
        self.hp = min(self.hp, self.hp_max)


class Monster(Actor):
    def __init__(self, spec_id: str, x: float, y: float, spec: dict[str, Any]) -> None:
        super().__init__(x, y)
        self.spec_id = spec_id
        self.name = spec["name"]
        self.hp = self.hp_max = float(spec["hp"])
        self.damage = float(spec["damage"])
        self.speed = float(spec["speed"])
        self.aggro = float(spec["aggro"])
        self.attack_range = float(spec["attack_range"])
        self.attack_cd = float(spec["attack_cooldown"])
        self.ranged = bool(spec.get("ranged"))
        self.loot_table = spec["loot_table"]
        self.tags = list(spec.get("tags") or [])
        self.vfx = spec.get("vfx")
        self.gold_range = spec.get("gold") or [1, 3]
        self.next_attack = 0.0
        self.power = self.damage


class Game:
    def __init__(self, *, headless: bool = False, world_seed: int = 1337) -> None:
        self.headless = headless
        if headless:
            os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
            os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        pygame.init()
        pygame.display.set_caption("Grok RPG")
        scale = 1
        if not headless:
            info = pygame.display.Info()
            if info.current_w >= VIEW_W * 2 and info.current_h >= VIEW_H * 2:
                scale = 2
        self.scale = scale
        self.window = pygame.display.set_mode((VIEW_W * scale, VIEW_H * scale))
        self.logical = pygame.Surface((VIEW_W, VIEW_H))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 22)
        self.big = pygame.font.Font(None, 42)
        self.data = catalog()
        errs = validate_catalog(self.data)
        if errs:
            print("data errors:", *errs, sep="\n  ")
        self.bank = SpriteBank()
        self.audio = Audio()
        self.world_seed = int(world_seed)
        self.rng = random.Random(self.world_seed + 7)
        self.mode = "title"
        self.ui = "none"
        self.debug = False
        self.player: Player | None = None
        self.world: World | None = None
        self.monsters: list[Monster] = []
        self.projectiles: list[Projectile] = []
        self.aoes: list[Aoe] = []
        self.loot: list[GroundLoot] = []
        self.vfx: list[Vfx] = []
        self.floaters: list[Floater] = []
        self.cam_x = 0.0
        self.cam_y = 0.0
        self.time = 0.0
        self.dt = 0.0
        self.deaths = 0
        self.message = ""
        self.message_t = 0.0
        self.tile_frames: list[pygame.Surface] = []
        self.running = True
        self.hover_class = "fighter"

    def say(self, text: str) -> None:
        self.message = text
        self.message_t = 2.5

    def world_mouse(self) -> tuple[float, float]:
        mx, my = pygame.mouse.get_pos()
        return mx / self.scale + self.cam_x, my / self.scale + self.cam_y

    def start_class(self, class_id: str) -> None:
        self.player = Player(class_id, self.data)
        self.enter_map("town")
        self.mode = "play"
        self.ui = "none"
        self.say(f"{self.data['classes'][class_id]['name']} enters the valley.")

    def enter_map(self, kind: str, *, keep_position: bool = False) -> None:
        assert self.player
        seed = self.world_seed if kind == "town" else self.world_seed + 1
        gen = random.Random(seed)
        self.world = make_town(gen, seed=seed) if kind == "town" else make_dungeon(gen, seed=seed)
        if not keep_position:
            self.player.x, self.player.y = self.world.player_start
        elif not self.world.walkable_px(self.player.x, self.player.y, self.player.radius):
            self.player.x, self.player.y = self.world.player_start
        self.monsters = [Monster(sid, x, y, self.data["monsters"][sid]) for sid, x, y in self.world.spawns]
        self.projectiles.clear()
        self.aoes.clear()
        self.loot.clear()
        self.vfx.clear()
        self.tile_frames = self.bank.frames("tile.palette")
        self.audio.ambience("amb.town" if kind == "town" else "amb.dungeon")
        self.ui = "none"
        if kind == "town" and not self.headless:
            self.save_to(slot_path(), quiet=True)

    def pop(self, x: float, y: float, text: str, color: tuple[int, int, int] = (255, 220, 120)) -> None:
        self.floaters.append(Floater(text=text, x=x, y=y, color=color))

    def deal(self, target: Any, amount: float) -> float:
        dealt = apply_damage(target, amount)
        if dealt > 0:
            self.pop(target.x, target.y, str(int(round(dealt))), (255, 80, 80))
        return dealt

    def cast_at(self, ability_id: str, aim_x: float, aim_y: float) -> None:
        p = self.player
        if not p or p.hp <= 0:
            return
        ability = self.data["abilities"][ability_id]
        enemies = [m for m in self.monsters if m.hp > 0]
        events = try_cast(
            caster=p,
            ability_id=ability_id,
            ability=ability,
            now=self.time,
            aim_x=aim_x,
            aim_y=aim_y,
            targets=enemies,
            spawn=self.spawn,
        )
        for ev in events:
            if ev.sfx:
                self.audio.play(ev.sfx)
            if ev.vfx:
                self.vfx.append(Vfx(ev.vfx, ev.x, ev.y))
            if ev.kind == "hit" and ev.damage:
                self.pop(ev.x, ev.y, str(int(round(ev.damage))), (255, 80, 80))
            if ev.kind == "heal" and ev.heal:
                self.pop(ev.x, ev.y, f"+{int(round(ev.heal))}", (80, 220, 120))
        p.facing = facing_from(aim_x - p.x, aim_y - p.y)

    def save_to(self, path=None, *, quiet: bool = False) -> None:
        if not self.player or not self.world:
            return
        path = path or slot_path()
        write_save(
            path,
            player_state(
                self.player,
                world_kind=self.world.kind,
                world_seed=self.world_seed,
                time=self.time,
                deaths=self.deaths,
            ),
        )
        if not quiet:
            self.say("Game saved.")

    def load_from(self, path=None) -> None:
        path = path or slot_path()
        data = read_save(path)
        self.world_seed = int(data["world_seed"])
        self.rng = random.Random(self.world_seed + 7)
        self.time = float(data.get("time", 0))
        self.deaths = int(data.get("deaths", 0))
        self.player = Player(data["class_id"], self.data)
        pdata = data["player"]
        self.player.inv = Inventory.from_dict(pdata["inventory"])
        self.player.refresh_stats(self.data)
        self.player.hp = min(float(pdata["hp"]), self.player.hp_max)
        self.player.resource = float(pdata["resource"])
        self.enter_map(data["world_kind"], keep_position=True)
        self.player.x = float(pdata["x"])
        self.player.y = float(pdata["y"])
        if self.world and not self.world.walkable_px(self.player.x, self.player.y, self.player.radius):
            self.player.x, self.player.y = self.world.player_start
        self.mode = "play"
        self.say("Game loaded.")

    def spawn(self, kind: str, payload: dict[str, Any]) -> None:
        if kind == "projectile":
            self.projectiles.append(Projectile(**{k: payload[k] for k in Projectile.__dataclass_fields__ if k in payload}))
        elif kind == "aoe":
            self.aoes.append(Aoe(**{k: payload[k] for k in Aoe.__dataclass_fields__ if k in payload}))
        elif kind == "dash":
            caster = payload["caster"]
            dx, dy = payload["dx"], payload["dy"]
            dist_px = float(payload["range"])
            caster.x += dx * dist_px
            caster.y += dy * dist_px
            if self.world:
                caster.x, caster.y = self.world.clamp_move(caster.x - dx, caster.y - dy, caster.x, caster.y, caster.radius)
            for m in self.monsters:
                if m.hp > 0 and dist(caster.x, caster.y, m.x, m.y) < 90:
                    self.deal(m, float(payload["damage"]) * undead_mult(payload["ability"], m.tags))
                    self.vfx.append(Vfx(payload.get("vfx") or "vfx.explosion", m.x, m.y))

    def cast(self, ability_id: str) -> None:
        p = self.player
        if not p or p.hp <= 0:
            return
        mx, my = self.world_mouse()
        self.cast_at(ability_id, mx, my)

    def use_item(self, item_id: str) -> None:
        p = self.player
        assert p
        spec = self.data["items"][item_id]
        if spec.get("kind") == "consumable":
            if not p.inv.remove(item_id, 1):
                return
            if spec.get("heal"):
                p.hp = min(p.hp_max, p.hp + spec["heal"])
            if spec.get("mana") and p.resource_name == "mana":
                p.resource = min(p.resource_max, p.resource + spec["mana"])
            self.audio.play("sfx.click")
            return
        if spec.get("kind") == "equipment":
            err = p.inv.try_equip(item_id, p.class_id, self.data["items"])
            self.say(err or f"Equipped {spec['name']}")
            self.audio.play("sfx.bag")
            p.refresh_stats(self.data)

    def handle_play(self, events: list[pygame.event.Event]) -> None:
        p = self.player
        assert p and self.world
        keys = pygame.key.get_pressed()
        for ev in events:
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    if self.ui != "none":
                        self.ui = "none"
                    else:
                        self.mode = "title"
                elif ev.key == pygame.K_i or ev.key == pygame.K_TAB:
                    self.ui = "none" if self.ui == "inventory" else "inventory"
                elif ev.key == pygame.K_c:
                    self.ui = "none" if self.ui == "craft" else "craft"
                elif ev.key == pygame.K_F3:
                    self.debug = not self.debug
                elif ev.key == pygame.K_F5:
                    self.save_to()
                elif ev.key == pygame.K_F9:
                    try:
                        self.load_from()
                    except FileNotFoundError:
                        self.say("No save yet.")
                elif ev.key == pygame.K_e:
                    self.try_interact()
                elif ev.key == pygame.K_h:
                    if p.inv.count("health_potion"):
                        self.use_item("health_potion")
                elif ev.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                    idx = ev.key - pygame.K_1
                    if 0 <= idx < len(p.ability_ids):
                        self.cast(p.ability_ids[idx])
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if self.ui == "inventory":
                    mx, my = ev.pos[0] / self.scale, ev.pos[1] / self.scale
                    for r, item_id in p._inv_hit:
                        if r.collidepoint(mx, my):
                            self.use_item(item_id)
                            break
                elif self.ui == "vendor":
                    mx, my = ev.pos[0] / self.scale, ev.pos[1] / self.scale
                    for r, item_id in p._vendor_hit:
                        if r.collidepoint(mx, my):
                            gained = p.inv.sell(item_id, self.data["items"], 1)
                            if gained:
                                self.audio.play("sfx.coins")
                                self.say(f"Sold for {gained}g")
                            break
                elif self.ui == "craft":
                    mx, my = ev.pos[0] / self.scale, ev.pos[1] / self.scale
                    for r, rid in p._craft_hit:
                        if r.collidepoint(mx, my):
                            rec = self.data["recipes"][rid]
                            if p.inv.craft(rec):
                                self.audio.play("sfx.shop")
                                self.say(f"Crafted {self.data['items'][rec['output']]['name']}")
                            else:
                                self.say("Missing materials.")
                            break
                else:
                    mx, my = self.world_mouse()
                    p.click_target = (mx, my)
                    self.cast(p.ability_ids[0])
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                p.click_target = None

        if self.ui != "none":
            return
        ax = ay = 0.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            ay -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            ay += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            ax -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            ax += 1
        if ax or ay:
            p.click_target = None
            nrm = norm(ax, ay)
            p.facing = facing_from(*nrm)
            speed = p.speed
            nx = p.x + nrm[0] * speed * self.dt
            ny = p.y + nrm[1] * speed * self.dt
            p.x, p.y = self.world.clamp_move(p.x, p.y, nx, ny, p.radius)
        elif pygame.mouse.get_pressed()[0] and p.click_target:
            mx, my = self.world_mouse()
            self.cast(p.ability_ids[0])
            dx, dy = mx - p.x, my - p.y
            if math.hypot(dx, dy) > 12:
                nrm = norm(dx, dy)
                p.facing = facing_from(*nrm)
                nx = p.x + nrm[0] * p.speed * self.dt
                ny = p.y + nrm[1] * p.speed * self.dt
                p.x, p.y = self.world.clamp_move(p.x, p.y, nx, ny, p.radius)

    def try_interact(self) -> None:
        p = self.player
        assert p and self.world
        for npc in self.world.npcs:
            if dist(p.x, p.y, npc["x"], npc["y"]) < 90:
                role = npc["role"]
                if role == "vendor":
                    self.ui = "vendor"
                    self.audio.play("sfx.click")
                elif role == "craft":
                    self.ui = "craft"
                    self.audio.play("sfx.click")
                elif role == "inn":
                    p.hp = p.hp_max
                    if p.resource_name == "mana":
                        p.resource = p.resource_max
                    self.say("Rested at the inn.")
                else:
                    self.say("Stay sharp out there.")
                return
        for portal in self.world.portals:
            if dist(p.x, p.y, portal["x"], portal["y"]) < 100:
                self.enter_map(portal["to"])
                self.say(f"Entered {portal['label']}.")
                return
        self.say("Nothing here.")

    def simulate(self) -> None:
        p = self.player
        w = self.world
        if not p or not w or self.ui != "none":
            return
        self.time += self.dt
        p.now = self.time
        p.attack_timer = max(0.0, p.attack_timer - self.dt)
        if p.shield_until and self.time > p.shield_until:
            p.shield = 0
        if p.resource_name == "rage":
            p.resource = max(0.0, p.resource - 8 * self.dt)
        else:
            p.resource = min(p.resource_max, p.resource + 6 * self.dt)

        for m in self.monsters:
            m.now = self.time
            m.attack_timer = max(0.0, m.attack_timer - self.dt)
            if m.hp <= 0:
                if not m.dead:
                    m.dead = True
                    self.on_kill(m)
                continue
            if self.time < m.stun_until:
                continue
            speed = m.speed
            if self.time < m.slow_until:
                speed *= 1.0 - m.slow
            d = dist(m.x, m.y, p.x, p.y)
            if d < m.aggro and d > m.attack_range * 0.7:
                nrm = norm(p.x - m.x, p.y - m.y)
                nx = m.x + nrm[0] * speed * self.dt
                ny = m.y + nrm[1] * speed * self.dt
                m.x, m.y = w.clamp_move(m.x, m.y, nx, ny, m.radius)
                m.facing = facing_from(*nrm)
            if d <= m.attack_range and self.time >= m.next_attack:
                m.next_attack = self.time + m.attack_cd
                m.attack_timer = 0.35
                if m.ranged:
                    nrm = norm(p.x - m.x, p.y - m.y)
                    self.projectiles.append(Projectile(
                        x=m.x, y=m.y, dx=nrm[0], dy=nrm[1], speed=280, damage=m.damage,
                        range=400, aoe=0, caster=m, ability={"undead_mult": 1},
                        vfx=m.vfx, impact_vfx="vfx.fire_explode", sfx=None,
                    ))
                    if m.vfx:
                        self.vfx.append(Vfx(m.vfx, m.x, m.y))
                elif aabb_hit(m.x, m.y, m.radius + 8, p.x, p.y, p.radius):
                    dealt = self.deal(p, max(1.0, m.damage - p.armor * 0.3))
                    self.audio.play("sfx.sword_hit", 0.35)
                    if dealt and m.vfx:
                        self.vfx.append(Vfx(m.vfx, p.x, p.y))

        for proj in list(self.projectiles):
            step = proj.speed * self.dt
            proj.x += proj.dx * step
            proj.y += proj.dy * step
            proj.traveled += step
            if proj.traveled > proj.range:
                proj.dead = True
                continue
            victims = [p] if proj.caster is not p else [m for m in self.monsters if m.hp > 0]
            for vic in victims:
                if aabb_hit(proj.x, proj.y, 16, vic.x, vic.y, vic.radius):
                    self.deal(vic, proj.damage * undead_mult(proj.ability, getattr(vic, "tags", [])))
                    if proj.impact_vfx:
                        self.vfx.append(Vfx(proj.impact_vfx, vic.x, vic.y))
                    if proj.aoe and proj.caster is p:
                        for m in self.monsters:
                            if m.hp > 0 and dist(proj.x, proj.y, m.x, m.y) < proj.aoe:
                                self.deal(m, proj.damage * 0.6 * undead_mult(proj.ability, m.tags))
                    proj.dead = True
                    break
        self.projectiles = [pr for pr in self.projectiles if not pr.dead]

        for aoe in list(self.aoes):
            aoe.timer += self.dt
            if aoe.timer >= aoe.interval:
                aoe.timer = 0
                aoe.ticks -= 1
                for m in self.monsters:
                    if m.hp > 0 and dist(aoe.x, aoe.y, m.x, m.y) <= aoe.radius:
                        self.deal(m, aoe.damage * undead_mult(aoe.ability, m.tags))
                if aoe.vfx:
                    self.vfx.append(Vfx(aoe.vfx, aoe.x, aoe.y))
            if aoe.ticks <= 0:
                self.aoes.remove(aoe)

        for drop in list(self.loot):
            if dist(p.x, p.y, drop.x, drop.y) < LOOT_MAGNET:
                p.inv.add(drop.item_id, drop.qty)
                self.loot.remove(drop)
                self.audio.play("sfx.bag", 0.5)
                name = self.data["items"][drop.item_id]["name"]
                self.say(f"+{drop.qty} {name}")

        alive_vfx = []
        for v in self.vfx:
            v.life -= self.dt
            if v.life > 0:
                alive_vfx.append(v)
        self.vfx = alive_vfx

        alive_float = []
        for fl in self.floaters:
            fl.life -= self.dt
            fl.y -= 28 * self.dt
            if fl.life > 0:
                alive_float.append(fl)
        self.floaters = alive_float

        if p.hp <= 0:
            self.deaths += 1
            kept = p.inv.to_dict()
            self.say("You fall. The innkeep drags you back to town.")
            p.hp = p.hp_max
            if p.resource_name == "mana":
                p.resource = p.resource_max * 0.5
            p.inv = Inventory.from_dict(kept)
            p.refresh_stats(self.data)
            p.hp = p.hp_max
            self.enter_map("town")

        # auto portal proximity hint is enough; E to use

        self.cam_x = p.x - VIEW_W / 2
        self.cam_y = p.y - VIEW_H / 2
        max_x = w.width * TILE - VIEW_W
        max_y = w.height * TILE - VIEW_H
        self.cam_x = max(0, min(self.cam_x, max(0, max_x)))
        self.cam_y = max(0, min(self.cam_y, max(0, max_y)))
        self.message_t = max(0.0, self.message_t - self.dt)

    def on_kill(self, m: Monster) -> None:
        table = self.data["loot_tables"][m.loot_table]
        for item_id, qty in roll_table(table, self.rng):
            self.loot.append(GroundLoot(item_id, qty, m.x + self.rng.randint(-20, 20), m.y + self.rng.randint(-20, 20)))
        gold = self.rng.randint(int(m.gold_range[0]), int(m.gold_range[1]))
        if gold:
            self.player.inv.add("gold", gold)  # type: ignore[union-attr]
            self.pop(m.x, m.y - 20, f"+{gold}g", (240, 210, 80))
        self.audio.play("sfx.monster", 0.5)
        dead_id = f"mon.{m.spec_id}.dead"
        if dead_id in self.bank.index:
            self.vfx.append(Vfx(dead_id, m.x, m.y, life=0.8))

    def sprite_for(self, actor: Actor, moving: bool) -> str | None:
        if isinstance(actor, Player):
            base = f"char.{actor.class_id}."
            if actor.hp <= 0:
                return base + "dead"
            if actor.attack_timer > 0:
                return base + "attack"
            if moving:
                return base + f"walk_{actor.facing}"
            return base + "idle"
        if isinstance(actor, Monster):
            base = f"mon.{actor.spec_id}."
            if actor.spec_id.startswith("dungeon_minion"):
                n = actor.spec_id[-2:]
                return f"mon.dungeon_minion_{n}.idle"
            if actor.hp <= 0:
                return base + "dead"
            if actor.attack_timer > 0:
                return base + "attack"
            if moving:
                return base + "walk"
            return base + "idle"
        return None

    def blit_world(self, sprite: pygame.Surface | None, x: float, y: float, fallback: tuple[int, int, int]) -> None:
        sx, sy = int(x - self.cam_x - TILE / 2), int(y - self.cam_y - TILE / 2)
        if sprite:
            self.logical.blit(sprite, (sx, sy))
        else:
            pygame.draw.rect(self.logical, fallback, (sx + 40, sy + 40, 48, 48))

    def draw_play(self) -> None:
        p = self.player
        w = self.world
        assert p and w
        self.logical.fill((8, 6, 8))
        t0 = int(self.cam_x // TILE)
        t1 = int((self.cam_x + VIEW_W) // TILE) + 1
        u0 = int(self.cam_y // TILE)
        u1 = int((self.cam_y + VIEW_H) // TILE) + 1
        for ty in range(u0, u1):
            for tx in range(t0, t1):
                if not w.in_bounds(tx, ty):
                    continue
                idx = w.tiles[ty][tx]
                dest = (int(tx * TILE - self.cam_x), int(ty * TILE - self.cam_y))
                if 0 <= idx < len(self.tile_frames):
                    self.logical.blit(self.tile_frames[idx], dest)
                else:
                    color = (40, 40, 48) if w.blocked[ty][tx] else (70, 90, 70)
                    pygame.draw.rect(self.logical, color, (*dest, TILE, TILE))

        for npc in w.npcs:
            spr = self.bank.first(npc["sprite"])
            self.blit_world(spr, npc["x"], npc["y"], (160, 120, 80))
            label = self.font.render(npc["name"], True, (255, 230, 180))
            self.logical.blit(label, (npc["x"] - self.cam_x - 20, npc["y"] - self.cam_y - 70))
        for portal in w.portals:
            pygame.draw.circle(self.logical, (120, 80, 200), (int(portal["x"] - self.cam_x), int(portal["y"] - self.cam_y)), 18, 2)
            self.logical.blit(self.font.render(portal["label"], True, (200, 180, 255)), (portal["x"] - self.cam_x - 20, portal["y"] - self.cam_y - 36))

        for drop in self.loot:
            icon = self.bank.first(self.data["items"][drop.item_id]["icon"])
            if icon:
                small = pygame.transform.scale(icon, (48, 48))
                self.logical.blit(small, (drop.x - self.cam_x - 24, drop.y - self.cam_y - 24))
            else:
                pygame.draw.circle(self.logical, (240, 200, 80), (int(drop.x - self.cam_x), int(drop.y - self.cam_y)), 8)
            name = self.data["items"][drop.item_id]["name"]
            label = self.font.render(f"{name} x{drop.qty}", True, (255, 230, 160))
            self.logical.blit(label, (drop.x - self.cam_x - label.get_width() / 2, drop.y - self.cam_y + 20))

        moving_p = pygame.key.get_pressed()[pygame.K_w] or pygame.key.get_pressed()[pygame.K_a] or pygame.key.get_pressed()[pygame.K_s] or pygame.key.get_pressed()[pygame.K_d] or pygame.mouse.get_pressed()[0]
        sid = self.sprite_for(p, bool(moving_p) and self.ui == "none")
        if sid:
            p.anim.play(sid)
        frame = p.anim.update(self.dt, self.bank)
        self.blit_world(frame, p.x, p.y, (80, 160, 220))

        for m in self.monsters:
            if m.hp <= 0:
                continue
            moving = dist(m.x, m.y, p.x, p.y) < m.aggro
            sid = self.sprite_for(m, moving)
            if sid:
                m.anim.play(sid)
            fr = m.anim.update(self.dt, self.bank)
            self.blit_world(fr, m.x, m.y, (180, 60, 60))
            if m.hp < m.hp_max:
                bx, by = int(m.x - self.cam_x - 20), int(m.y - self.cam_y - 50)
                pygame.draw.rect(self.logical, (40, 0, 0), (bx, by, 40, 4))
                pygame.draw.rect(self.logical, (200, 40, 40), (bx, by, int(40 * m.hp / m.hp_max), 4))

        for proj in self.projectiles:
            pygame.draw.circle(self.logical, (255, 180, 80), (int(proj.x - self.cam_x), int(proj.y - self.cam_y)), 6)

        for v in self.vfx:
            fr = v.anim.update(self.dt, self.bank)
            if fr:
                self.logical.blit(fr, (int(v.x - self.cam_x - TILE / 2), int(v.y - self.cam_y - TILE / 2)))

        for fl in self.floaters:
            img = self.font.render(fl.text, True, fl.color)
            self.logical.blit(img, (fl.x - self.cam_x - img.get_width() / 2, fl.y - self.cam_y - 40))

        if self.debug:
            pygame.draw.rect(self.logical, (0, 255, 0), (p.x - self.cam_x - p.radius, p.y - self.cam_y - p.radius, p.radius * 2, p.radius * 2), 1)

        hud(self.logical, p, self.data["abilities"], self.bank, self.font)
        hint = "WASD move  LMB attack  1-4 skills  E interact  I inv  C craft  H potion  F5 save  F9 load  Esc"
        self.logical.blit(self.font.render(hint, True, (200, 190, 160)), (16, VIEW_H - 22))
        if self.message_t > 0:
            self.logical.blit(self.big.render(self.message, True, (255, 230, 160)), (80, 120))
        if self.ui == "inventory":
            panel_inventory(self.logical, p, self.data["items"], self.bank, self.font)
        elif self.ui == "vendor":
            panel_vendor(self.logical, p, self.data["items"], self.bank, self.font)
        elif self.ui == "craft":
            panel_craft(self.logical, p, self.data["recipes"], self.data["items"], self.bank, self.font)

    def draw_title(self) -> None:
        self.logical.fill((10, 8, 12))
        title = self.big.render("GROK RPG", True, (240, 210, 140))
        self.logical.blit(title, (VIEW_W // 2 - title.get_width() // 2, 80))
        sub = self.font.render("128×128 pixel ARPG  —  slay, loot, sell, craft", True, (200, 180, 140))
        self.logical.blit(sub, (VIEW_W // 2 - sub.get_width() // 2, 130))
        classes = ("fighter", "mage", "cleric")
        self._title_hit = []
        for i, cid in enumerate(classes):
            x = 180 + i * 320
            y = 280
            r = pygame.Rect(x, y, 260, 360)
            pygame.draw.rect(self.logical, (30, 22, 16), r)
            pygame.draw.rect(self.logical, (200, 170, 90) if cid == self.hover_class else (120, 100, 60), r, 3)
            idle = self.bank.first(f"char.{cid}.idle")
            if idle:
                self.logical.blit(idle, (x + 66, y + 40))
            spec = self.data["classes"][cid]
            self.logical.blit(self.big.render(spec["name"], True, (255, 230, 180)), (x + 40, y + 200))
            self.logical.blit(self.font.render(f"HP {spec['hp']}  {spec['resource']}", True, (220, 200, 160)), (x + 40, y + 250))
            self.logical.blit(self.font.render("Click to enter town", True, (180, 160, 120)), (x + 40, y + 310))
            self._title_hit.append((r, cid))
        if not self.bank.ok:
            warn = self.font.render("No baked assets. Run: PYTHONPATH=src python3 -m grok_rpg.baker", True, (255, 120, 100))
            self.logical.blit(warn, (80, VIEW_H - 40))

    def handle_title(self, events: list[pygame.event.Event]) -> None:
        mx, my = pygame.mouse.get_pos()
        mx /= self.scale
        my /= self.scale
        self.hover_class = "fighter"
        for r, cid in getattr(self, "_title_hit", []):
            if r.collidepoint(mx, my):
                self.hover_class = cid
        for ev in events:
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for r, cid in getattr(self, "_title_hit", []):
                    if r.collidepoint(mx, my):
                        self.audio.play("sfx.click")
                        self.start_class(cid)
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                self.running = False

    def present(self) -> None:
        scaled = pygame.transform.scale(self.logical, self.window.get_size())
        self.window.blit(scaled, (0, 0))
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            self.dt = self.clock.tick(FPS) / 1000.0
            events = pygame.event.get()
            for ev in events:
                if ev.type == pygame.QUIT:
                    self.running = False
            if self.mode == "title":
                self.handle_title(events)
                self.draw_title()
            else:
                self.handle_play(events)
                self.simulate()
                self.draw_play()
            self.present()
        pygame.quit()


def main() -> None:
    if os.environ.get("GROK_RPG_HEADLESS") == "1":
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    Game().run()


if __name__ == "__main__":
    main()
