# Grok RPG

A **128×128 pixel-art Diablo-style ARPG**: slay monsters, pick up loot, sell it, and craft equipment. Three classes — **fighter**, **mage**, **cleric**.

This repository is the game project. Art and audio come from the **Complete RPG Creator Bundle** on disk. They are not stored in git.

**Status:** implementation in progress. Read [PLAN.md](PLAN.md) for phases, then [AGENTS.md](AGENTS.md) for asset and class rules.

## What you will play

Top-down real-time combat. You pick a class, fight through dungeon acts from a town hub, and grow power through drops and crafted gear.

| Class | Feel | v1 body | Signature kit |
| --- | --- | --- | --- |
| **Fighter** | Melee, rage, armor | AFGame **Viking** | Slash, cleave, shield bash, leap |
| **Mage** | Ranged spells, mana | AFGame **BloodMage** | Fireball, ice nova, lightning, blink |
| **Cleric** | Holy damage + heal | AFGame **Druid** (priest identity from ITS `male_priest`) | Smite, heal, ward, consecrate |

Named monsters in the first slice: beaver, ghost, salamander, enemy mage, necromancer, plus Beowulf’s mini dungeon fodder. Elites (skeleton, slime, golem, dragon, …) come from the ITS monster sheets.

## Resolution

Every baked sprite, tile, VFX frame, and icon is **128×128** pixels, scaled with **nearest-neighbor** only.

- Beowulf tiles and mini monsters are 16×16 in the pack → scaled **×8**.
- AFGame characters and VFX frames are 64×64 → scaled **×2**.
- Loot, runes, skill icons, and equip icons already ship at 128×128 → copied as-is.

The *window* is larger than 128×128 so a Diablo-style battlefield fits on screen. Default logical view: **10×7 tiles (1280×896)**, integer-scaled (1× or 2×).

## Why Python + pygame

On this machine the following are already installed and free:

- Python 3.12
- pygame 2.6 (SDL2, image, mixer, TTF)
- Pillow 10 (asset baker)

No extra engine download is required. The baker and the game share one language.

## Asset bundle

Set the bundle path if it is not the default:

```bash
# WSL / Linux
export GROK_RPG_ASSETS="/mnt/i/game assets/complete rpg creator bundle"

# Windows
set GROK_RPG_ASSETS=I:\game assets\complete rpg creator bundle
```

Default lookup is `I:\game assets\complete rpg creator bundle` / `/mnt/i/game assets/complete rpg creator bundle`.

The baker (to be added) will copy **only** the frames listed in a manifest into `assets/baked/`. Do not commit the raw 80-pack bundle.

### Packs this game is built from

**Characters and monsters**

- `pixel art rpg top down characters` — Viking, BloodMage, Druid, MagicRogue
- `pixel art rpg top down enemies` — Beaver, Ghost, Mage, Necromancer, Salamander
- `2d top down character bundle` (ITS zip) — warrior / wizard / priest identity + named monsters
- `mini adventure heroes humans` — 16×16 knight / wizard alts
- `pixel rpg dungeons monsters` — 117 fodder sprites
- `pixel art rpg npc` — vendor and town NPCs

**World**

- `beowulfs rpg dungeon tilesets` — crypt tilemap
- `mana seed pixel art tileset collection` — forest town, caves, castle dungeon
- `pixel art medieval interiors_windows` — shop / craft rooms

**FX, items, UI**

- `pixel art rpg vfx` — slash, fire, ice, holy, lightning, void, earth, wind
- `beowulfs rpg monster loots` (`monster_loots_size_128x128`)
- `magic runes pixel art asset pack` (`runes_size_xxx_128x128`)
- `2d minimal skill icons` / `2d minimal stat icons` (128 folders)
- `spells and ability icons_windows/png/128x128`
- `gui pro_fantasy rpg_gamedevmarket` — HUD, equipment icons
- `fantasy spellbook` — tome UI

**Audio**

- `combat sounds bundle collection`
- `monster sounds volume1`
- `user interface sfx bundle`
- `ambience sounds pack`

Cyberpunk, sci-fi, children, and side-view platformer hero packs are out of scope.

## Planned controls

| Input | Action |
| --- | --- |
| WASD or LMB ground | Move |
| Mouse aim + LMB | Primary attack (slash / fireball / smite) |
| 1–4 or QERF | Class abilities |
| Tab or I | Inventory |
| C | Character / craft (at station) |
| Esc | Pause / town map |

Exact bindings will live in data when the input module exists.

## Planned loop

1. Choose fighter, mage, or cleric.
2. Leave town into a dungeon act.
3. Kill monsters; loot materials and gear on the ground.
4. Return to town: sell junk (`TentacleButcher` / `BarMan`), craft at the bench (materials + GUI Pro equip icons).
5. Wear better gear; next act.

## Run

This machine provides `python3`, not `python`. Use `python3` everywhere.

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python3 -m pip install -r requirements.txt
export GROK_RPG_ASSETS="/mnt/i/game assets/complete rpg creator bundle"
export PYTHONPATH=src
python3 tools/bake_assets.py
python3 -m grok_rpg
```

Tests (no bundle, no window). This host has `python3` only:

```bash
PYTHONPATH=src python3 -m pytest -q
PYTHONPATH=src python3 -m pytest -q -m unit
PYTHONPATH=src python3 -m pytest -q -m integration
```

In-game: **F5** save, **F9** load (`saves/slot1.json`). Death returns you to town with loot kept.

## For implementers

Read **[AGENTS.md](AGENTS.md)** before writing code. It is the source of truth for class–VFX maps, baker rules, folder layout, and what not to touch.

## License

Code in this repo: to be decided by the owner.

Third-party art and audio remain under their original marketplace licenses. You must own the Complete RPG Creator Bundle to bake and run the game with those assets.
```
