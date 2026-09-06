# Asset credits

This file is the inventory of **where every asset used by Grok RPG came from**. The game does not ship original pixel art. Code in this repository is original.

Machine-readable bake list: `src/grok_rpg/manifest.py` (copied into `assets/baked/` at bake time). Do not treat README pack lists as “everything is used”; this file is the source of truth for **what is actually baked**.

## Two origins

1. **Complete RPG Creator Bundle** (commercial marketplace pack, local disk only).  
   Path: `I:\game assets\complete rpg creator bundle` / `/mnt/i/game assets/complete rpg creator bundle` (`GROK_RPG_ASSETS`).  
   Raw packs are **not** in git. The baker copies only listed frames into `assets/baked/` (gitignored). You must own the bundle to bake those files. Redistribution of the raw packs is not granted by this repo.

2. **CC0 / public-domain music** downloaded at bake time into `third_party/music/` (binaries gitignored; see that folder’s `CREDITS.md`).

Python, pygame, and Pillow are third-party software with their own licenses (not game art).

---

## Complete RPG Creator Bundle (used)

Folder names are as they appear under the bundle root.

### Characters, monsters, VFX — AfGameAssets

Publisher contact in pack: `afgameassets@gmail.com` (Unity Asset Store listings).

| Bundle folder | Pack title | Used as |
| --- | --- | --- |
| `pixel art rpg top down characters` | Pixel Art Top-Down RPG Characters — AfGameAssets V2 Walking 4 Directions | **Fighter** = `Viking/`; **mage** = `BloodMage/` (incl. `Effect_BloodBubble`); **cleric** = `Druid/` (incl. heal sheet) |
| `pixel art rpg top down enemies` | Pixel Art Top-Down RPG Enemies — AfGameAssets V2 Walking | `Ghost`, `Salamander`, `Mage`, `Necromancer`, `Beaver` |
| `pixel art rpg npc` | Pixel Art Top-Down RPG NPC — AfGameAssets V1 | Town NPCs: TentacleButcher (vendor), BarMan (inn), ShieldMan, Librarian (craft) |
| `pixel art rpg vfx` | Pixel Art RPG VFX — AfGameAssets V3 | Ability/monster FX: slash, fire, ice, holy, lightning, void, earth, wind, explosions |

`MagicRogue` is in the character pack but is **not** a playable class (mage uses BloodMage).

### Tiles, loot, runes, fodder — Beowulf

Itch: https://beowulf.itch.io/ — GameDevMarket: https://www.gamedevmarket.net/member/xbeowulf

| Bundle folder | Pack title | Used as |
| --- | --- | --- |
| `beowulfs rpg dungeon tilesets` | Beowulf Mini Dungeons v2.1 `(FULL)TILESET_MINI_DUNGEONS.png` | Town grass/path; **crypt** gray dungeon tiles; **castle** fire-dungeon cells |
| `beowulfs rpg monster loots` | Beowulf RPG Monsters Loot `monster_loots_size_128x128` | Material / potion / gem icons (already 128×128) |
| `magic runes pixel art asset pack` | Beowulf’s Magic Runes `runes_size_xxx_128x128` | Craft rune icon |
| `pixel rpg dungeons monsters` | Individual monsters v1.3 | Fodder `Monster_01`–`Monster_08` spritesheets |

### Mana Seed — Seliel the Shaper

https://seliel-the-shaper.itch.io/

| Bundle folder | Pack | Used as |
| --- | --- | --- |
| `mana seed pixel art tileset collection` | `19.10a - Muddy Cave` / `muddy cave 16x16 v1.png` | **Cave** act floor/wall tiles |

The rest of the Mana Seed collection (forests, thatch homes, castle interiors, eternal dungeon sheets) is **in the bundle but not baked** for the current game.

### UI, icons, portraits

| Bundle folder | Pack / files | Used as |
| --- | --- | --- |
| `gui pro_fantasy rpg_gamedevmarket` | GUI Pro-FantasyRPG 2.0 PNG Component | Equip icons (`Icon_EquipIcons/NoShadow/128`); HUD chrome: frame, slot, popup, slider, button (`copy_raw`) |
| `2d minimal skill icons` | Round/128 | Ability bar icons (`Skill_Attack`, heal, ice, lightning, …) |
| `2d minimal stat icons` | 128 | Attack/defense icons |
| `spells and ability icons_windows` | `png/128x128` | Extra skill icons (fire, ice, lightning, sword) |
| `fantasy character avatars` | `png/square_512x512` | Title portraits: `human_male` (fighter), `elf_male` (mage), `dwarf_male` (cleric) |

### Audio — The Sound Guild

Included PDF: “Free SFX and Music (The Sound Guild)”. Combat / UI / monster / ambience WAVs at 44.1 kHz 16-bit.

| Bundle folder | Pack | Used as |
| --- | --- | --- |
| `combat sounds bundle collection` | Combat Sounds Bundle | Sword hit/swing/block; `Arch_Magical_Shoot` for spells |
| `user interface sfx bundle` | User Interface SFX Bundle | Click, coins, bag, shop |
| `monster sounds volume1` | Monster Sounds Volume 01 | `Aggressive_01` on kills |
| `ambience sounds pack` | Ambience Sounds | Town forest; crypt/castle dungeon loops; cave `Deep` loop; **music fallbacks** `Dark_Fantasy_01/02_Loop`, `Magic_Ethereal_Aura_Loop` if CC0 files are missing |

---

## CC0 music (OpenGameArt)

Fetched by `python3 tools/fetch_music.py` into `third_party/music/`. Public domain; attribution not required. Full table: [`third_party/music/CREDITS.md`](third_party/music/CREDITS.md).

| Game use | File | Author | Listing |
| --- | --- | --- | --- |
| Title | `title.ogg` (`Menu Song.ogg`) | Kosmo The Cat | https://opengameart.org/content/calm-and-simple-title-music |
| Town | `town.mp3` (`homestead.mp3`) | troubadour | https://opengameart.org/content/fantasy-song-pack-volume-1 |
| Crypt | `crypt.mp3` (`wandering_woodlands.mp3`) | troubadour | same pack |
| Cave | `cave.mp3` (`back_to_nature.mp3`) | troubadour | same pack |
| Castle | `castle.mp3` (`jaunt.mp3`) | troubadour | same pack |
| Boss | `boss.mp3` (`rbl.mp3`) | iamoneabe | https://opengameart.org/content/rpg-battle-loop |

---

## In the bundle, not used by the current bake

These appear in AGENTS.md / README as related packs. They are **not** copied by `manifest.py` today:

- `2d top down character bundle` (ITS 2048×8192 warrior/wizard/priest sheets and named monster pack)
- `mini adventure heroes humans` / elves
- Mana Seed summer forest, thatch/timber homes, castle interiors, eternal dungeon (except muddy cave 16×16)
- `pixel art medieval interiors_windows`
- `fantasy spellbook` UI
- Side-view `2d fantasy characters pack_V2` (optional hit sparks only, unused)
- Sci-fi, cyberpunk, children, girl-power, robot packs (out of scope)
- Human vocals / old magician voice packs
- Khron Studio spell variation audio zips

---

## Engine / libraries

| Software | Role |
| --- | --- |
| Python 3.12 | Game and baker |
| pygame 2.6 | Window, sprites, mixer |
| Pillow | Slice and nearest-neighbor scale to 128×128 |

---

## License reminder

- **Grok RPG code** in this git repo: owner’s license (see README).
- **Bundle art and Sound Guild audio:** remain under the licenses that came with the Complete RPG Creator Bundle. This project does not relicense them.
- **OpenGameArt music:** CC0 as stated on each listing.
