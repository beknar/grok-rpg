# AGENTS.md — Grok RPG

Instructions for coding agents working in this repository. Read this file before writing code, importing art, or changing combat, loot, or classes.

## What this repo is

A **top-down Diablo-style action RPG** (ARPG): click-or-aim movement, real-time monster killing, ground loot, vendor sell, and equipment crafting.

Three playable classes: **fighter**, **mage**, **cleric**.

All in-game pixel art is normalized to a **128×128** cell (nearest-neighbor only). Source packs live **outside** the repo.

Do **not** generate original character, monster, tile, VFX, or UI art while the Complete RPG Creator Bundle is available. Pick, slice, and scale from that bundle.

## Current status

Playable v1 is in the tree (Phases 1–5 of [PLAN.md](PLAN.md)). Bake assets, then `PYTHONPATH=src python -m grok_rpg`.

Still open: save/load, ITS identity sheets, remaining fodder/elites, balance (Phase 6).

## Stack (already on this machine)

Use **Python 3.12 + pygame 2.6 + Pillow + pygame.mixer**. All three are installed and free. Do not introduce Godot, Unity, Node, or Rust unless the user asks.

| Tool | Role |
| --- | --- |
| Python 3.12 | Game + baker |
| pygame 2.6 | Window, sprites, input, mixer |
| Pillow | Slice sheets, nearest-neighbor scale to 128×128 |
| pygame.mixer | WAV SFX and ambience |

Optional later: `pytest` for baker and data tests. Pin deps in `requirements.txt` when code exists.

## Resolution and scaling

- **Canonical cell:** 128×128 pixels. Every baked tile, character frame, monster frame, VFX frame, item icon, and skill icon occupies that canvas (transparent padding allowed; never stretch non-uniformly).
- **World tile size:** 128 px. Beowulf Mini Dungeons tiles are 16×16 → scale **×8** nearest-neighbor.
- **Filter:** `Image.NEAREST` / pygame `pygame.SCALE_NEAREST`. Never bilinear, bicubic, or smoothscale for pixel art.
- **Display:** the *game view* is **not** a 128×128 window. Default camera is an integer number of 128 px tiles (start at **10×7 tiles → 1280×896** logical pixels). Integer-scale the window (`SCALE=1` or `2`) with a letterbox if the monitor is smaller.
- **HUD:** source icons are 128×128; blit them smaller (32 or 64) at draw time if the bar is cramped. Do not re-bake a second resolution unless a profile needs it.
- **Audio:** copy/convert WAV as-is. Do not resample unless pygame cannot load the file.

## Asset source (do not commit the bundle)

| Environment | Path |
| --- | --- |
| Windows | `I:\game assets\complete rpg creator bundle` |
| WSL / Linux | `/mnt/i/game assets/complete rpg creator bundle` |

Override with env `GROK_RPG_ASSETS`. Never copy the whole bundle into git. Baker reads the bundle and writes **only selected** frames into `assets/baked/`.

Commercial packs. Do not redistribute the raw bundle. Baked subsets used by the game may live in `assets/baked/` locally; keep them gitignored until the user says otherwise.

### Packs to use (fantasy ARPG)

| Role | Pack folder (under the bundle root) | Notes |
| --- | --- | --- |
| Playable, 4-dir, already sliced | `pixel art rpg top down characters` | **Primary v1 characters** |
| Playable class identity sheets | `2d top down character bundle` → `ITS_2DTopDownCharacterBundleArt.zip` | Warrior / wizard / priest; unzip in baker temp |
| Mini 16×16 heroes (optional alt) | `mini adventure heroes humans` | Knight / wizard; scale ×8 |
| Dungeon tiles | `beowulfs rpg dungeon tilesets` | 16×16 → ×8 |
| Overworld / town tiles | `mana seed pixel art tileset collection` | Summer Forest, Thatch/Timber homes, Muddy Cave, Castle Dungeon, Eternal Dungeon |
| Town interiors | `pixel art medieval interiors_windows`, Mana Seed cozy furnishings / castle interiors | Vendor + craft benches |
| Fodder monsters | `pixel rpg dungeons monsters` | 117 mini dungeon monsters, 16×16 → ×8 |
| Named 4-dir enemies | `pixel art rpg top down enemies` | Ghost, Salamander, Mage, Necromancer, Beaver |
| Extra named monsters | ITS zip `30MonsterPack` + named files (`skeleton`, `slime`, `spider`, `golem`, `warlock`, `dragon`, `demon`, …) | Elites / bosses |
| VFX | `pixel art rpg vfx` | 64×384 strips = 6 frames of 64×64 → ×2 |
| Loot icons | `beowulfs rpg monster loots` / `monster_loots_size_128x128` | Already 128×128 (~90 icons) |
| Craft / equip icons | `gui pro_fantasy rpg_gamedevmarket` `Icon_EquipIcons/NoShadow/128` | Already 128×128 |
| Skill icons | `2d minimal skill icons/Round/128` and `spells and ability icons_windows/png/128x128` | Already 128×128 |
| Stat icons | `2d minimal stat icons/128` | Already 128×128 |
| Runes / craft reagents | `magic runes pixel art asset pack` / `runes_size_xxx_128x128` | Already 128×128 |
| Spellbook UI | `fantasy spellbook` | Mage/cleric tome screens |
| HUD chrome | `gui pro_fantasy rpg_gamedevmarket` | Frames, buttons, bars, popups |
| Skill HUD extras | `mmorpg ui kit_windows/png` | Bars / slots if needed |
| Dialogue | `dialogue boxes_windows/PNGs` | Vendor text |
| NPCs | `pixel art rpg npc` | Vendor, trainer, librarian |
| Combat SFX | `combat sounds bundle collection` | Sword + Fantasy_Combat_Sounds |
| Monster SFX | `monster sounds volume1` | Hit / death / growl |
| UI SFX | `user interface sfx bundle` | Click, loot, craft |
| Ambience | `ambience sounds pack` | Dungeon / town loops |

### Packs not to use for this game

Sci-fi, cyberpunk, futuristic cities/dungeons/vehicles, robots, children characters, girl power packs, cute-cartoon UI unless nothing else fits. Side-view platformer packs (`2d fantasy characters pack_V2` knight/orc/spider) are **not** the player camera; they may supply extra VFX only (`Effects/sprites`).

`spells variations complete collection 2` is audio zips (Khron Studio). Unzip on demand for extra spell SFX; not required for v1.

## Class → sprite → abilities → VFX → SFX → icons

Implement these mappings. Ability IDs are stable; do not rename without migrating data.

### Fighter (`fighter`)

| Field | Value |
| --- | --- |
| v1 world sprite | `pixel art rpg top down characters/.../Viking/` (`VikingIdle`, walk 4-dir, `Viking_Attack_01`, `VikingDead`, `VikingAttacked`) |
| Identity sheet (later) | ITS `male_warrior` / `female_warrior` (and `male_knight` / `female_knight` as heavy armor skin) |
| Mini alt | `mhap_male_knight_01` / `mhap_female_knight_01` |
| Portrait | `character avatar icons_windows` or `fantasy character avatars` warrior-like face |
| Resource | Rage (builds on hit; no mana) |
| Stats bias | High HP, high armor, melee range |

| Ability ID | Behavior | VFX (`pixel art rpg vfx/...`) | Icon | SFX |
| --- | --- | --- | --- | --- |
| `fighter.slash` | LMB melee arc | `Attack Slash/Slash_attack_00N` | `Skill_Attack` + `1_weapon_sword` | `Sword_Combat_Sounds` swing/hit |
| `fighter.cleave` | Cone / whirlwind | `Attack Slash` + `Wind/WindSlash` or `Earth/EarthSpin` | `Skill_Precision-Strike` | Heavy sword hit |
| `fighter.shield_bash` | Short stun | `Earth/EarthShield` + `Hit` | `Skill_Stone` | `Block_Metal` / `Block_With_Sword` |
| `fighter.leap` | Dash toward cursor, slam | `Earth/EarthGrow` or `Explosion/Explosion_0N` | `Skill_Rabbit_Rush` | Whoosh + slam |

Hit sparks: pack `2d fantasy characters pack_V2/Effects/sprites/Hit_efx_A` (optional).

### Mage (`mage`)

| Field | Value |
| --- | --- |
| v1 world sprite | `.../BloodMage/` (idle, 4-dir walk, attack 01–03, dead) + `Effect_BloodBubble.png` as charge FX. `MagicRogue` is the glass-cannon skin (projectiles already in folder). |
| Identity sheet | ITS `male_wizard` / `female_wizard` / `male_mage` / `female_mage` |
| Mini alt | `mhap_male_wizard_01` / `mhap_female_witch_01` |
| Resource | Mana |
| Stats bias | Low HP, high spell power |

| Ability ID | Behavior | VFX | Icon | SFX |
| --- | --- | --- | --- | --- |
| `mage.fireball` | Aimed projectile + small AOE | `Fire/FireBall`, `FireExplosion1` | `1_fire_1` / `Skill_Meteor` | `Arch_Magical_Shoot_0N` |
| `mage.ice_nova` | Point-blank freeze / slow | `Ice/IceSpike`, `IceSlam`, `IceBall` | `Skill_Ice` / `1_ice_1` | Magical shoot + ice |
| `mage.lightning` | Chain or targeted bolt | `Electricity/ElectricLighting1`, `ElectricBall` | `Skill_Lightning` / `1_lightning_1` | Magical multi |
| `mage.blink` | Short teleport | `Void/Void` portal / spin (folder `Void`) | `Skill_Blackhole` or `Skill_Time` | Soft whoosh |

Staff / rune cosmetics: Beowulf `runes_size_xxx_128x128`. Spellbook screen: `fantasy spellbook`.

### Cleric (`cleric`)

No dedicated “cleric” folder in the 4-dir pack. **v1 uses Druid** (has heal frames). **Identity is priest** from ITS.

| Field | Value |
| --- | --- |
| v1 world sprite | `.../Druid/` (idle, 4-dir walk, attack, dead) + `Effect_Heal_Poison.png`, `Druid_Root_Effect.png` |
| Identity sheet | ITS `male_priest`; female: `female_monk` (no female_priest in the zip) |
| Mini alt | `mhap_male_hero_01` (paladin-like) — do not use cultivator as the cleric |
| Resource | Mana (holy) |
| Stats bias | Mid HP, support + smite |

| Ability ID | Behavior | VFX | Icon | SFX |
| --- | --- | --- | --- | --- |
| `cleric.smite` | Melee-range holy hit or short bolt | `Holy/HolySlash`, `HolySlash2`, `HolyProjectile` | `Skill_Heaven` / `Skill_Starlight` | Fantasy attack + holy |
| `cleric.heal` | Self (and later ally) heal | `Holy/HolyBlessing`, `Earth/EarthHeal` | `Skill_Heal` / `Skill_Health_Up` | Soft magical |
| `cleric.ward` | Temporary shield | `Holy/HolyShield` | `Skill_Vaccine` or `Skill_Mirror` | Block fantasy |
| `cleric.consecrate` | Ground AOE, damages undead more | `Holy/HolyCross`, `HolyBall`, `HolyWings` | `Skill_Heaven` | Magical shoot + explosion |

NPC monk (`pixel art rpg npc` `Monk_*`) is a **town NPC**, not the player.

## Monsters

Every monster needs: idle/walk/attack/hit/death (fallback: idle + flip), HP, damage, speed, aggro radius, loot table ID, SFX, and an attack VFX.

### v1 named enemies (AFGame 4-dir)

| ID | Folder | Role | Attack VFX | Typical loot |
| --- | --- | --- | --- | --- |
| `beast_beaver` | `Beaver` | Forest melee | Slash / `Wind` | `fur_tuft`, `bear_paw` (stand-in), `red_meat` |
| `undead_ghost` | `Ghost` | Phasing caster | `Void`, `Holy` inverted | `ghost_ectoplasm` |
| `elemental_salamander` | `Salamander` | Fire melee | `Fire/FireFlamme`, `FireSlash` | `monster_scale`, `coal` |
| `enemy_mage` | `Mage` | Ranged fire/ice | `FireBall` or `IceProjectile` | `mana_potion`, a rune |
| `necromancer` | `Necromancer` | Elite; may summon fodder | `Void`, `Skull` icon language | `human_skull`, `monster_core` |

### Fodder

`pixel rpg dungeons monsters/(INDIVIDUAL MONSTERS) v1.3/Monster_NNN` — treat as `dungeon_minion_NNN`. Scale 16×16 frames ×8. Use for crypt trash. Map subsets to biomes in data, not in code.

### Elites / bosses (ITS named PNGs, after unzip)

Prefer fantasy names, skip alien/robot: `slime`, `skeleton`, `spider`, `golem`, `warlock`, `ogre`, `troll`, `vampire`, `gargoyle`, `demon`, `dragon`, `skeletonking`. One act boss per biome.

### Monster SFX

`monster sounds volume1` growls, attacks, deaths. Combat hits still use `combat sounds` / `Blood_And_Wounds_Sounds`.

## Loot, vendors, crafting

**Loop:** kill → drops on ground (magnet on overlap) → inventory → sell at vendor **or** consume in recipes → wear crafted gear.

### Item kinds

- `material` — Beowulf monster loots (wings, fangs, pelts, gems, `health_potion`, `mana_potion`, …).
- `equipment` — GUI Pro `equip_icon_*` (weapons, armor, jewelry). Slots: weapon, offhand, head, chest, legs, feet, ring, amulet.
- `rune` — Beowulf runes; socket or recipe catalyst.
- `gold` — numeric; `Skill_Gold` as pickup icon if needed.

Rarity: common / magic / rare / legendary. Magic+ rolls affixes (damage, armor, +fire, +holy, life, mana). Data in JSON, not hardcoded if-else forests.

### Vendor

Town NPC: `TentacleButcher` (general/loot buyer) and `BarMan` (inn). `ShieldMan` = trainer (later). Buyback optional for v1.

### Crafting

Station in town (Mana Seed interior + GUI Pro popup). Recipes in `data/recipes.json`. Example pattern:

- 3× `monster_bone` + 1× `whetstone` → common sword (`equip_icon` sword/axe/hammer matching class).
- `dragon_scale` + `ruby` + rune → rare chest.
- Class gating: fighter prefers swords/axes/hammers; mage staves/tomes; cleric maces/holy symbols. Anyone can *craft*; anyone can *equip* with stat penalties if wrong class (keep v1 simple: class-ok or not).

Do not require the mining-crafting *gameplay* from `pixel art mining crafting` (those files are 512×512 preview sheets, not a tileset). Use GUI Pro + loot icons for the craft UI.

## World layout

1. **Hub town** — Mana Seed summer forest + thatch/timber homes. Interiors for vendor and craft. NPCs from `pixel art rpg npc`.
2. **Dungeon acts** — Beowulf Mini Dungeons (crypt) and Mana Seed Muddy Cave / Castle Dungeon / Eternal Dungeon as later acts.
3. Camera follows player, clamped to map. Click-to-move **or** WASD; mouse aims attacks. Diablo-style: hold LMB to attack toward cursor.

Skip isometric. This game is **orthogonal top-down**.

## Planned tree (when code starts)

```
grok-rpg/
  AGENTS.md
  README.md
  requirements.txt
  pyproject.toml          # optional
  data/                   # json: classes, abilities, monsters, loot, recipes, maps
  tools/bake_assets.py    # reads GROK_RPG_ASSETS + data/asset_manifest.json
  src/grok_rpg/
    __main__.py
    game.py               # loop, scenes
    render.py             # integer scale, camera
    world.py              # tilemap, collisions
    entities.py           # player, monsters, projectiles
    combat.py
    inventory.py
    crafting.py
    vendor.py
    ui.py
    audio.py
    data_load.py
  assets/baked/           # gitignored output of baker
  tests/
```

Python import package: `grok_rpg`. Entry: `python -m grok_rpg`.

## Asset baker rules

- Manifest maps logical IDs → bundle-relative paths, slice rects / frame counts, scale factor.
- Output: `assets/baked/<category>/<id>/<anim>_###.png` plus `atlas.json` if you pack later.
- VFX strips: 64×384 → six 64×64 frames → each ×2 to 128×128.
- AFGame character strips: width 64, height multiple of 64 (or 192/256) — split on 64 px rows unless a frame is clearly 64×48; verify with a one-off script, store frame size in the manifest, do not guess in the game loop.
- ITS 2048×8192 sheets: detect grid from file (likely 128 or 256 px cells); scale each cell to 128×128.
- Mini heroes 64×64 sheets and 16×16 dungeon monsters: scale so **one character/monster frame** is 128×128.
- Idempotent. `--dry-run` lists work. Fail if `GROK_RPG_ASSETS` missing.
- Do not bake unused sci-fi/cyberpunk trees.

## Code conventions

- 4-space indent, type hints on public functions, `from __future__ import annotations` if useful.
- Gameplay numbers live in `data/*.json`. Code reads data.
- Deterministic combat given a seed (loot rolls, map gen).
- No secret network calls. No telemetry.
- Keep the pygame loop thin: input → simulate(dt) → draw.
- `dt` in seconds. 60 FPS target; gameplay must not depend on frame count.
- Entities: position in **world pixels** (128 = one tile).
- Collisions: AABB; player/monster radius smaller than the 128 sprite (hitbox ~32–48 px).

## Do not

- Do not invent a fourth class.
- Do not switch to side-view or isometric mid-project.
- Do not smooth-scale pixel art.
- Do not vendor the 80+ pack bundle inside git.
- Do not implement crafting as a full mining sim.
- Do not generate code that attacks remote systems or ships malware.

## Verify before calling work done

- Baker: a 16×16 tile becomes 128×128; a 128×128 loot icon is copied unchanged; a 64×64 VFX frame becomes 128×128.
- Fighter slash shows Attack Slash VFX; mage fireball uses FireBall; cleric heal uses HolyBlessing (or EarthHeal).
- A monster dies, loot appears, inventory receives it, vendor buys it, a recipe consumes materials and grants equipment.
- WASD/click move, attack toward mouse, integer-scaled window with no blur.
```
