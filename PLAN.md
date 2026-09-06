# Grok RPG — Implementation Plan

Source of truth for *what* the game is: [AGENTS.md](AGENTS.md) and [README.md](README.md). Asset provenance: [CREDITS.md](CREDITS.md). This file is *how* we build it, in order, without leaving the Diablo loop (kill → loot → sell → craft).

**Progress:** v1–v3 are in the tree, including scene and boss music. Later: ITS identity sheets, remaining fodder, balance.

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
- `src/grok_rpg` package, `python3 -m grok_rpg` entry (can no-op until Phase 2)
- `tools/bake_assets.py` + `data/asset_manifest.json`
- Probe Beowulf tileset; commit chosen `(col,row)` palette in the manifest
- Tests: 16→128, 64→128, 128→128 copy; missing env fails
- README “when code exists” section becomes true

**Done when:** `python3 tools/bake_assets.py` fills `assets/baked/` on this machine.

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

- Save/load JSON in `saves/` (gitignored). Slot `saves/slot1.json`. F5 save, F9 load, auto-save when entering town.
- Persist: class, inventory, equipped, gold, HP/resource, map kind, position, `world_seed`.
- Seeded maps: town = `Random(world_seed)`, crypt = `Random(world_seed + 1)`. Same seed ⇒ same layout.
- Damage numbers (floaters) on hit/heal; loot name labels on ground drops.
- Death: keep gold/loot/gear, respawn in town, HP full, increment `deaths`.
- Headless `Game(headless=True)` for integration tests (`SDL_VIDEODRIVER=dummy`).
- `cast_at(ability_id, x, y)` so combat can be driven without a mouse.

**Done when:** F5/F9 round-trips a fighter with crafted gear, death keeps inventory, pytest unit+integration pass without the art bundle.

### Phase 7 — Test matrix (unit + integration)

Land the lists below. Markers: `@pytest.mark.unit` and `@pytest.mark.integration`.

```bash
PYTHONPATH=src python3 -m pytest -q -m unit
PYTHONPATH=src python3 -m pytest -q -m integration
PYTHONPATH=src python3 -m pytest -q
```

**Done when:** CI-style `pytest -q` is green with no `GROK_RPG_ASSETS` and no real display.

## Test strategy

Two layers. **Neither requires the Complete RPG Creator Bundle or a real window.** Integration tests may use pygame with `SDL_VIDEODRIVER=dummy` / `SDL_AUDIODRIVER=dummy` (set in `tests/conftest.py` before importing game code).

Baked art is optional: placeholders (colored rects) are valid. If `assets/baked/index.json` exists locally, integration may load it but must not fail when it is missing.

### Unit tests (fast, no pygame display)

| Area | File | Must cover |
| --- | --- | --- |
| Baker | `tests/test_baker.py` | 16→128, 64→128, 128 copy unchanged, vertical strip frame count, missing source raises |
| Data | `tests/test_data.py` | class→ability ids exist; loot tables→items; recipes→items; every ability `vfx` id is in `default_jobs()` |
| Combat | `tests/test_combat.py` | slash AABB hit + `vfx.slash`; fireball spawns projectile `vfx.fireball`; heal `vfx.holy_bless`; smite undead multiplier; ward absorbs; cooldowns; insufficient resource does not fire |
| Economy | `tests/test_economy.py` | craft consume; vendor 50% on equipment; class equip gate; seeded loot tables |
| World | `tests/test_world.py` | same seed ⇒ identical town/dungeon tiles + spawns; wall `clamp_move` does not walk through solids; portal/NPC markers present |
| Save | `tests/test_save.py` | dump/load dict round-trip; missing file raises; version field |

### Integration tests (headless pygame)

File: `tests/test_integration_loop.py`. Drive `Game(headless=True)` with `dt` ticks, no event pump required.

| Scenario | Assert |
| --- | --- |
| Boot | title mode; `start_class("fighter")` lands in town with HP and starter items |
| Loot magnet | spawn `GroundLoot` on the player; after simulate, stack count increases |
| Kill → drop | set a ghost to 0 HP; `on_kill` path runs; gold or ground loot appears |
| Vendor | add a material, `inv.sell`; gold up, stack down |
| Craft + equip | give recipe inputs, `inv.craft` bone_sword, `try_equip` on fighter |
| Death | set HP 0, simulate; map is town, HP full, inventory kept |
| Save/load | mutate gold, `save_to`, new `Game`, `load_from`; gold/class/seed match |
| Mage/cleric boot | `start_class` for each remaining class without exception |

Manual (this machine, not CI): bake + play the loop, F5/F9, die in the crypt, confirm town respawn.

## Risks

| Risk | Mitigation |
| --- | --- |
| Irregular strips (Druid 32×831, Beaver 64×872) | Drop remainder; square frames of `min(w, declared frame)` |
| Tileset is a collage, not a packed grid | Probe opaque 16×16 cells; store explicit indices |
| 128 px sprites dwarf 32–48 hitboxes | Draw sprite centered on feet; debug hitbox toggle `F3` |
| pygame mixer fails without audio device | Catch init error; run silent |
| Bundle path differs on Windows | `GROK_RPG_ASSETS` then `I:\...` then `/mnt/i/...` |

## v2

v1 is the one-crypt loop. v2 is the next playable expansion from leftover AGENTS.md items. Still **not** v2: ITS 2048×8192 identity sheets, all 117 fodder, mining sim.

### v2 features

1. **Three acts** — town portals: Crypt (Beowulf gray), Muddy Cave (Mana Seed 16×16 cave tiles), Castle (Beowulf fire-dungeon tiles). Killing the act elite unlocks the next portal.
2. **Affixes** — magic / rare / legendary gear rolls 1–3 stat affixes (`data/affixes.json`). Elites can drop gear; crafting rolls rarity.
3. **Input map** — `data/input.json` drives keys. Skills: 1–4 plus Q/R/F (E stays interact). B = spellbook.
4. **Necromancer summons** — elite periodically spawns fodder (cap 3).
5. **More fodder** — minions 04–08.
6. **Letterbox** — resizable window, integer scale, black bars, mouse mapped through the letterbox.
7. **Portraits** — title cards use fantasy avatar icons (fighter/mage/cleric).
8. **GUI chrome** — vendor/craft/inventory/spellbook blit baked GUI Pro popup/frame.
9. **Mage charge VFX** — projectile casts spawn `char.mage.charge`.
10. **Spellbook** — B lists class abilities with icons.

Save version **2** (v1 files still load). Tests: affix roll seeded, act unlock, summon cap, input bindings, letterbox mapping.

### PR 8: v2 acts, affixes, input, summons, HUD

- **Description:** Implement the v2 list above with unit + integration coverage.
- **Files/components affected:** `PLAN.md`, `src/grok_rpg/*`, `data/*`, `tests/*`, `README.md`, `AGENTS.md`
- **Dependencies:** PR 7

## v3

v2 is the three-act ARPG. v3 is **game music**. The Complete RPG Creator Bundle has ambience and dark-fantasy loops, not a full soundtrack; v3 also pulls **CC0** RPG loops (OpenGameArt) when the network is available.

### v3 features

1. **Scene BGM** — looping music for title, town, crypt, cave, castle.
2. **Boss BGM** — switch to a battle loop while an elite is in aggro range; restore scene music after.
3. **Layered ambience** — forest/dungeon/cave beds on a reserved mixer channel so they sit under the music (not instead of it).
4. **Mute** — `M` toggles music+ambience (SFX stay). Persisted on save.
5. **Volumes** — `data/music.json` music/ambience/sfx levels.
6. **Fetch + bake** — `tools/fetch_music.py` downloads CC0 files into `third_party/music/` (gitignored binaries). Baker copies those, with Sound Guild `Dark_Fantasy_*` / `Magic_Ethereal_*` as fallbacks.

Tests: scene→track map, mute, boss switch, baker audio_copy of a tiny wav. Headless Game must not crash when mixer is dummy.

### PR 9: Game music

- **Description:** Implement the v3 music list.
- **Files/components affected:** `PLAN.md`, `data/music.json`, `data/acts.json`, `data/input.json`, `src/grok_rpg/audio.py`, `src/grok_rpg/game.py`, `src/grok_rpg/manifest.py`, `src/grok_rpg/baker.py`, `tools/fetch_music.py`, `tests/test_music.py`, `README.md`, `AGENTS.md`
- **Dependencies:** PR 8

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

- **Description:** JSON saves, damage pops, loot labels, death/respawn, seeded map regen, headless Game, F5/F9.
- **Files/components affected:** `src/grok_rpg/save.py`, `src/grok_rpg/game.py`, `src/grok_rpg/world.py`, `src/grok_rpg/ui.py`, `.gitignore`
- **Dependencies:** PR 5

### PR 7: Unit and integration tests

- **Description:** Expand unit coverage (world seed, save, combat edge cases, vfx ids in manifest). Add headless integration loop tests. pytest markers `unit` and `integration`. conftest sets dummy SDL.
- **Files/components affected:** `tests/conftest.py`, `tests/test_world.py`, `tests/test_save.py`, `tests/test_combat.py`, `tests/test_data.py`, `tests/test_integration_loop.py`, `pyproject.toml`, `README.md`, `PLAN.md`
- **Dependencies:** PR 6
```
