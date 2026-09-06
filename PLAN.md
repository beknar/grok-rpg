# Grok RPG — Implementation Plan

Source of truth for *what* the game is: [AGENTS.md](AGENTS.md) and [README.md](README.md). This file is *how* we build it, in order, without leaving the Diablo loop (kill → loot → sell → craft).

## Goal (v1 playable)

A top-down orthogonal ARPG at **128×128 art cells**, default view **10×7 tiles (1280×896)** integer-scaled.

Player picks **fighter / mage / cleric**, fights a crypt, picks up loot, returns to town, sells, crafts, equips.

Python 3.12 + pygame 2.6 + Pillow. No other engine.

## Non-goals (v1)

- Isometric camera, fourth class, mining sim, multiplayer, generated hero art
- Committing the Complete RPG Creator Bundle or `assets/baked/`
- ITS 2048×8192 identity sheets (optional later skin)
- All 117 fodder monsters (bake a handful of minions, not the full set)

## Architecture

```
data/*.json          gameplay numbers (classes, abilities, monsters, items, recipes, maps)
tools/bake_assets.py reads GROK_RPG_ASSETS + data/asset_manifest.json → assets/baked/
src/grok_rpg/        pygame loop: input → simulate(dt) → draw
tests/               baker scale invariants + data load + combat/loot/craft without a window
```

World units: **pixels**. One tile = 128 px. Entity hitboxes ~32–48 px AABB, not the full sprite.

Render: draw to a 1280×896 (or current view) Surface with nearest-neighbor, then integer-scale to the window. Letterbox leftover pixels. Never `smoothscale`.

Scenes: `title` (class select) → `town` → `dungeon` → back to town. Death respawns in town with gold/loot kept, equipped gear kept, HP full.

RNG: `random.Random(seed)` for loot and map gen so tests are deterministic.

## Asset baker

Manifest entry:

```json
{
  "id": "fighter.idle",
  "category": "characters/fighter",
  "source": "pixel art rpg top down characters/.../VikingIdle.png",
  "op": "strip_v",
  "frame": 64,
  "scale_to": 128
}
```

Operations:

| `op` | Meaning |
| --- | --- |
| `copy` | Resize canvas to 128×128 (pad center, nearest). 128×128 sources stay 1:1. |
| `strip_v` | Slice a vertical strip into `frame × frame` cells (drop remainder), each → 128×128. |
| `strip_h` | Same, horizontal (heal sheet 320×128). |
| `grid_cells` | Slice a tilesheet into `cell × cell` at listed `(col,row)` indices, each → 128×128. |
| `audio_copy` | Copy WAV into `assets/baked/audio/...`. |

`frame` may be omitted: default to image width for `strip_v` (square frames). Druid idle is 32 px wide — use `frame: 32`. Remainder rows are dropped (documented in baker log).

Output layout: `assets/baked/<category>/<id>/<anim>_000.png` plus `assets/baked/index.json` listing frame counts.

Fail hard if `GROK_RPG_ASSETS` is missing. `--dry-run` prints jobs. Idempotent overwrite.

### v1 bake set (required)

**Player (AFGame 4-dir)**

- Fighter: `Viking/` idle, walk 4-dir, attack_01, dead, attacked
- Mage: `BloodMage/` idle, walk 4-dir, attack_01, dead, `Effect_BloodBubble`
- Cleric: `Druid/` idle, walk 4-dir, attack_01, dead, `Effect_Heal_Poison` (strip_h)

**Named monsters**

- Ghost, Salamander, Mage, Necromancer, Beaver — all pngs in each folder

**Fodder:** `pixel rpg dungeons monsters/.../Monster_01`, `Monster_02`, `Monster_03` sheets ×8

**VFX (64×384 → 6 frames ×2):** slash 001–004, FireBall, FireExplosion1, IceSpike, IceSlam, ElectricLighting1, ElectricBall, HolySlash, HolyBlessing, HolyShield, HolyCross, VoidPortal, EarthShield, EarthSpin, EarthGrow, EarthHeal, WindSlash, Explosion_01

**Tiles:** Beowulf Mini Dungeons full sheet, extract a **palette** (not all 3914 cells): gray dungeon floor/wall/door, earth dungeon accents, grass autotile block for town. Indices recorded in the manifest after a one-time probe (see Phase 1).

**Icons (already 128):** selected loots (`ghost_ectoplasm`, `red_meat`, `fur_tuft`, `monster_bone`, `monster_scale`, `coal`, `human_skull`, `monster_core`, `whetstone`, `ruby`, `health_potion`, `mana_potion`, `dragon_scale`), skill icons used by the 12 abilities, a few `equip_icon_*` (sword, hammer, axe, potions), 2–3 runes, `Skill_Gold`.

**UI chrome:** GUI Pro square frame, rectangle button, HP/resource-usable bars if present, popup border. Scale/pad to 128 only if smaller; large frames stay native and are drawn at HUD size (not forced to 128 if they are panels). *Exception:* full-screen chrome may exceed 128; document in manifest as `"scale_to": null` / `op: copy_raw`.

**NPCs:** BarMan_Idle, TentacleButcher_Idle, ShieldMan_Idle, Librarian_Idle (strip_v).

**Audio:** a few sword swings/hits, `Arch_Magical_Shoot_01`, block, UI click, loot pickup, one dungeon ambience, one town ambience, one monster growl/death.

## Gameplay data

JSON under `data/`:

- `classes.json` — hp, resource (rage|mana), speed, abilities[], sprite id
- `abilities.json` — id, kind (`melee_arc`|`projectile`|`nova`|`dash`|`self_buff`|`ground_aoe`), damage, cost, cooldown, range, vfx, sfx, icon
- `monsters.json` — stats, aggro, attack, loot_table, sprites, vfx
- `loot_tables.json` — weighted drops
- `items.json` — materials, equipment slots, sell value, affix pool
- `recipes.json` — inputs → equipment
- `maps.json` or generated maps in code with a seed + tile palette ids
- `asset_manifest.json` — baker jobs
- `input.json` — bindings (WASD, LMB attack, 1–4 skills, I inventory, C craft, Esc)

Ability IDs are frozen as in AGENTS.md (`fighter.slash`, `mage.fireball`, …).

### Combat

- Hold LMB: repeat primary toward cursor when cooldown ready.
- Keys 1–4: class skills.
- Rage: +on dealing hit, decay over time; mana: regen slow, spend on skills (mage primary also costs mana).
- Status: stun (bash), slow/freeze (ice), ward absorb (cleric).
- Ghost / necromancer take 1.5× from `cleric.consecrate` and smite (undead tag).

### Economy

Ground drops magnetize at ~48 px. Inventory grid. Vendor buys materials at `sell_value`, equipment at 50%. Craft consumes stacks; output is identified gear. Equip if `class` in `ok_classes` (v1: hard gate, no off-class).

Recipes (v1):

1. 3× `monster_bone` + 1× `whetstone` → common sword (fighter)
2. 2× `coal` + 1× `ruby` → common fire focus (mage)
3. 2× `ghost_ectoplasm` + 1× rune → common holy symbol (cleric)
4. 1× `dragon_scale` + 1× `ruby` + 1× rune → rare chest (any)

## Maps

**Town (seeded, ~24×16 tiles):** grass + path from Beowulf grass block, 3 NPC markers (vendor, inn, craft). Exit rectangle → dungeon.

**Crypt (seeded drunk-walk or rooms, ~40×30):** gray dungeon walls/floors, spawn packs of fodder + named ghosts/sals, one necromancer as act elite. Stairs back to town.

Camera follows player, clamped.

## Phases

Do not skip ahead of a playable slice. Each phase must be runnable.

### Phase 0 — Plan (this file)

Write `PLAN.md`, push.

### Phase 1 — Scaffold + baker + tests

- `requirements.txt` (`pygame==2.6.1`, `Pillow==10.2.0`, `pytest`)
- `src/grok_rpg` package, `python -m grok_rpg` entry (can no-op until Phase 2)
- `tools/bake_assets.py` + `data/asset_manifest.json`
- Probe Beowulf tileset; commit chosen `(col,row)` palette in the manifest
- Tests: 16→128, 64→128, 128→128 copy; missing env fails
- README “when code exists” section becomes true

**Done when:** `python tools/bake_assets.py` fills `assets/baked/` on this machine.

### Phase 2 — Window, camera, tilemap, player move

- Integer-scale presenter
- Load baked tiles, draw a crypt (or placeholder rect tiles if bake skipped in CI)
- WASD + click-to-move
- Collide with wall tiles
- Title screen class select (three portraits = first idle frame)

**Done when:** you can walk a fighter around a dungeon without blur.

### Phase 3 — One class, one monster, one loot (vertical slice)

- Fighter `slash` + Attack Slash VFX
- Ghost AI (chase + attack)
- Death drop `ghost_ectoplasm`, magnet into inventory
- HP bar (simple rect ok if chrome not baked yet)

**Done when:** kill ghost → loot in inventory.

### Phase 4 — Three classes + named roster + skills

- Mage fireball/ice/lightning/blink with mapped VFX
- Cleric smite/heal/ward/consecrate with mapped VFX
- Beaver, salamander, enemy mage, necromancer, 3 minions
- Resource (rage/mana) UI

**Done when:** AGENTS.md ability VFX checks pass for all three classes.

### Phase 5 — Town, vendor, crafting, HUD

- Town map + NPCs
- Vendor sell
- Craft station + recipes
- Inventory / equipment panel using GUI Pro frames
- Skill bar icons
- Audio: combat, UI, ambience

**Done when:** sell a drop and craft a sword/focus/symbol and equip it.

### Phase 6 — Save, feel, polish

- Save/load JSON in `saves/` (gitignored)
- Damage numbers, loot labels
- Death/respawn
- README screenshots optional
- Balance pass

## Test strategy

CI-friendly tests **must not** require the asset bundle or a display:

- Baker unit tests with tiny synthetic PNGs in `tests/fixtures/`
- Data JSON schema: every ability id referenced by a class exists; every vfx id exists in manifest
- Inventory add/remove, recipe consume, loot table with seeded RNG
- Combat: slash hits AABB, fireball travels and explodes

Manual (this machine): bake + play the loop.

Headless pygame: `SDL_VIDEODRIVER=dummy` if a smoke test opens a surface.

## Risks

| Risk | Mitigation |
| --- | --- |
| Irregular strips (Druid 32×831, Beaver 64×872) | Drop remainder; square frames of `min(w, declared frame)` |
| Tileset is a collage, not a packed grid | Probe opaque 16×16 cells; store explicit indices |
| 128 px sprites dwarf 32–48 hitboxes | Draw sprite centered on feet; debug hitbox toggle `F3` |
| pygame mixer fails without audio device | Catch init error; run silent |
| Bundle path differs on Windows | `GROK_RPG_ASSETS` then `I:\...` then `/mnt/i/...` |

## Implementation order for the first coding session

After this plan is on `main`, implement Phase 1–5 in one pass as far as they stay coherent: baker + engine + three classes + town economy. Stop at a runnable `python -m grok_rpg`. Phase 6 can follow.

## PR Plan

Single-repo sequential stack (each PR assumes the previous is merged). Fine to land as sequential commits on `main` instead of GitHub PRs.

### PR 1: Scaffold, baker, and synthetic tests

- **Description:** Package layout, requirements, asset baker, manifest for v1 ids, tests that 16/64/128 sources bake to 128×128 without the full bundle (fixtures). Probe script notes for Beowulf tile indices.
- **Files/components affected:** `requirements.txt`, `pyproject.toml`, `src/grok_rpg/__init__.py`, `src/grok_rpg/__main__.py`, `src/grok_rpg/paths.py`, `tools/bake_assets.py`, `data/asset_manifest.json`, `tests/test_baker.py`, `tests/fixtures/`, `README.md`, `.gitignore`
- **Dependencies:** None

### PR 2: Display, camera, tilemap, player locomotion

- **Description:** Integer-scale renderer, tile world from baked palette, WASD and click-move, wall collision, class-select title.
- **Files/components affected:** `src/grok_rpg/game.py`, `src/grok_rpg/render.py`, `src/grok_rpg/world.py`, `src/grok_rpg/entities.py`, `src/grok_rpg/scenes.py`, `src/grok_rpg/data_load.py`, `data/maps.json`, `data/input.json`, `data/classes.json`
- **Dependencies:** PR 1

### PR 3: Fighter slash, ghost, loot pickup

- **Description:** Combat AABB, fighter.slash + slash VFX, ghost enemy, ground loot magnet, inventory component, HP bar.
- **Files/components affected:** `src/grok_rpg/combat.py`, `src/grok_rpg/inventory.py`, `src/grok_rpg/ui.py`, `data/abilities.json`, `data/monsters.json`, `data/items.json`, `data/loot_tables.json`
- **Dependencies:** PR 2

### PR 4: Mage, cleric, remaining named monsters and skills

- **Description:** All 12 abilities with AGENTS.md VFX maps; beaver, salamander, enemy mage, necromancer, three dungeon minions; rage/mana.
- **Files/components affected:** `data/abilities.json`, `data/monsters.json`, `data/classes.json`, `src/grok_rpg/combat.py`, `src/grok_rpg/entities.py`, `src/grok_rpg/ui.py`
- **Dependencies:** PR 3

### PR 5: Town, vendor, crafting, HUD chrome, audio

- **Description:** Town scene, vendor sell, craft recipes, equipment slots, GUI Pro HUD, pygame.mixer hooks.
- **Files/components affected:** `src/grok_rpg/vendor.py`, `src/grok_rpg/crafting.py`, `src/grok_rpg/audio.py`, `src/grok_rpg/ui.py`, `data/recipes.json`, `data/asset_manifest.json`
- **Dependencies:** PR 4

### PR 6: Save/load and combat juice

- **Description:** JSON saves, damage pops, death/respawn, seeded map regen, balance.
- **Files/components affected:** `src/grok_rpg/save.py`, `src/grok_rpg/ui.py`, `src/grok_rpg/world.py`, `.gitignore`
- **Dependencies:** PR 5
```
