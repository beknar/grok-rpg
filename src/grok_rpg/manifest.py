from __future__ import annotations

from typing import Any

CHAR = (
    "pixel art rpg top down characters/"
    "Pixel Art Top-Down RPG Characters - AfGameAssets - V2 Walking 4 Directions"
)
ENEMY = (
    "pixel art rpg top down enemies/"
    "Pixel Art Top-Down RPG Enemies - AfGameAssets - V2 - Walking"
)
VFX = "pixel art rpg vfx/Pixel Art RPG VFX - AfGameAssets - V3"
TILESET = (
    "beowulfs rpg dungeon tilesets/Beowulf_Mini_Dungeons_v 2.1/"
    "( MINI DUNGEON TILESET )/(Tileset)/(FULL)TILESET_MINI_DUNGEONS.png"
)
LOOT = "beowulfs rpg monster loots/Beowulf_RPG_Monsters_Loot/monster_loots_size_128x128"
SKILL = "2d minimal skill icons/Round/128"
SPELL = "spells and ability icons_windows/png/128x128"
EQUIP = (
    "gui pro_fantasy rpg_gamedevmarket/GUI Pro-FantasyRPG_2.0/PNG/Component/"
    "Icon_EquipIcons/NoShadow/128"
)
STAT = "2d minimal stat icons/128"
RUNE = "magic runes pixel art asset pack/Beowulf's_Magic_Runes/runes_size_xxx_128x128"
NPC = "pixel art rpg npc/Pixel Art Top-Down RPG NPC - AfGameAssets - V1"
GUI = "gui pro_fantasy rpg_gamedevmarket/GUI Pro-FantasyRPG_2.0/PNG/Component"
MINION = "pixel rpg dungeons monsters/(INDIVIDUAL MONSTERS) v1.3"
SFX_ROOT = (
    "combat sounds bundle collection/The_Sound_Guild_Combat_Sounds_Bundle/"
    "WAV - 44100 Hz - 16 Bit"
)
UI_SFX = (
    "user interface sfx bundle/The_Sound_Guild_User_Interface_SFX_Bundle/"
    "WAV - 44100 Hz - 16 Bit"
)
AMB = (
    "ambience sounds pack/The_Sound_Guild_Ambience_Sounds/"
    "WAV - 44100 Hz - 16 Bit"
)
MON_SFX = (
    "monster sounds volume1/The_Sound_Guild_Monster_Sounds_Volume_01/"
    "WAV - 44100 Hz - 16 Bit"
)


def _strip(job_id: str, source: str, *, category: str, frame: int | None = None, fps: int = 8, loop: bool = True) -> dict[str, Any]:
    job: dict[str, Any] = {
        "id": job_id,
        "category": category,
        "source": source,
        "op": "strip_v",
        "fps": fps,
        "loop": loop,
        "scale_to": 128,
    }
    if frame is not None:
        job["frame"] = frame
    return job


def _copy(job_id: str, source: str, *, category: str) -> dict[str, Any]:
    return {
        "id": job_id,
        "category": category,
        "source": source,
        "op": "copy",
        "scale_to": 128,
        "fps": 0,
        "loop": False,
    }


def _audio(job_id: str, source: str) -> dict[str, Any]:
    return {"id": job_id, "source": source, "op": "audio_copy", "required": False}


def default_jobs() -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []

    fighter = {
        "idle": "Viking/VikingIdle.png",
        "walk_down": "Viking/Viking_Walk_Down.png",
        "walk_left": "Viking/Viking_Walk_Left.png",
        "walk_right": "Viking/Viking_Walk_Right.png",
        "walk_up": "Viking/Viking_Walk_Up.png",
        "attack": "Viking/Viking_Attack_01.png",
        "dead": "Viking/VikingDead.png",
        "hit": "Viking/VikingAttacked.png",
    }
    for anim, rel in fighter.items():
        jobs.append(_strip(f"char.fighter.{anim}", f"{CHAR}/{rel}", category="characters/fighter", fps=10 if "walk" in anim or anim == "idle" else 14, loop=anim not in ("dead", "attack")))

    mage = {
        "idle": "BloodMage/BloodMage_Idle.png",
        "walk_down": "BloodMage/BloodMage_Walking_Down.png",
        "walk_left": "BloodMage/BloodMage_Walking_Side_Left.png",
        "walk_right": "BloodMage/BloodMage_Walking_Side_Right.png",
        "walk_up": "BloodMage/BloodMage_Walking_Up.png",
        "attack": "BloodMage/BloodMage_Attack_01.png",
        "dead": "BloodMage/BloodMage_Dead.png",
        "charge": "BloodMage/Effect_BloodBubble.png",
    }
    for anim, rel in mage.items():
        jobs.append(_strip(f"char.mage.{anim}", f"{CHAR}/{rel}", category="characters/mage", fps=10, loop=anim not in ("dead", "attack")))

    cleric = {
        "idle": ("Druid/Druid_Idle.png", 32),
        "walk_down": ("Druid/Druid_Walk_Down.png", 32),
        "walk_left": ("Druid/Druid_Walk_Left.png", 32),
        "walk_right": ("Druid/Druid_Walk_Right.png", 32),
        "walk_up": ("Druid/Druid_Walk_Up.png", 32),
        "attack": ("Druid/Druid_Attack_01.png", 64),
        "dead": ("Druid/Druid_Dead.png", 64),
    }
    for anim, (rel, frame) in cleric.items():
        jobs.append(_strip(f"char.cleric.{anim}", f"{CHAR}/{rel}", category="characters/cleric", frame=frame, fps=10, loop=anim not in ("dead", "attack")))
    jobs.append({
        "id": "char.cleric.heal_fx",
        "category": "characters/cleric",
        "source": f"{CHAR}/Druid/Effect_Heal_Poison.png",
        "op": "strip_h",
        "frame": 64,
        "fps": 10,
        "loop": False,
        "scale_to": 128,
    })

    monsters = {
        "undead_ghost": {
            "idle": "Ghost/Ghost_Idle.png",
            "walk": "Ghost/Ghost_Walk.png",
            "attack": "Ghost/Ghost_Attack.png",
            "hit": "Ghost/Ghost_Hit.png",
            "dead": "Ghost/Ghost_Dead.png",
        },
        "elemental_salamander": {
            "idle": "Salamander/Salamander_Idle.png",
            "walk": "Salamander/Salamander_Walk.png",
            "attack": "Salamander/Salamander_Attack.png",
            "hit": "Salamander/Salamander_Hit.png",
            "dead": "Salamander/Salamander_Dead.png",
        },
        "enemy_mage": {
            "idle": "Mage/Mage_Idle.png",
            "walk": "Mage/Mage_Walk.png",
            "attack": "Mage/Mage_Attack.png",
            "hit": "Mage/Mage_Hit.png",
            "dead": "Mage/Mage_Dead.png",
        },
        "necromancer": {
            "idle": "Necromancer/Necromancer_Switch_Idle.png",
            "walk": "Necromancer/Necromancer_Walk.png",
            "attack": "Necromancer/Necromancer_Attack.png",
            "hit": "Necromancer/Necromancer_Hit.png",
        },
        "beast_beaver": {
            "idle": "Beaver/Beaver_Walk.png",
            "walk": "Beaver/Beaver_Walk.png",
            "attack": "Beaver/Beaver_Attack_Idle.png",
            "hit": "Beaver/Beaver_Hit.png",
            "dead": "Beaver/Beaver_Dead.png",
        },
    }
    for mid, anims in monsters.items():
        for anim, rel in anims.items():
            jobs.append(_strip(
                f"mon.{mid}.{anim}",
                f"{ENEMY}/{rel}",
                category=f"monsters/{mid}",
                fps=10,
                loop=anim not in ("dead", "attack", "hit"),
            ))

    for n in (1, 2, 3, 4, 5, 6, 7, 8):
        jobs.append({
            "id": f"mon.dungeon_minion_{n:02d}.idle",
            "category": f"monsters/minion_{n:02d}",
            "source": f"{MINION}/Monster_{n:02d}/png_spritesheet/spr_pixel_mini_dungeon_monster_{n:02d}-Sheet.png",
            "op": "strip_h",
            "frame": 16,
            "fps": 6,
            "loop": True,
            "scale_to": 128,
            "required": n <= 3,
        })

    vfx_files = {
        "vfx.slash": f"{VFX}/Attack Slash/Slash_attack_001.png",
        "vfx.slash2": f"{VFX}/Attack Slash/Slash_attack_002.png",
        "vfx.slash3": f"{VFX}/Attack Slash/Slash_attack_003.png",
        "vfx.fireball": f"{VFX}/Fire/FireBall.png",
        "vfx.fire_explode": f"{VFX}/Fire/FireExplosion1.png",
        "vfx.ice_spike": f"{VFX}/Ice/IceSpike.png",
        "vfx.ice_slam": f"{VFX}/Ice/IceSlam.png",
        "vfx.lightning": f"{VFX}/Electricity/ElectricLighting1.png",
        "vfx.electric_ball": f"{VFX}/Electricity/ElectricBall.png",
        "vfx.holy_slash": f"{VFX}/Holy/HolySlash.png",
        "vfx.holy_bless": f"{VFX}/Holy/HolyBlessing.png",
        "vfx.holy_shield": f"{VFX}/Holy/HolyShield.png",
        "vfx.holy_cross": f"{VFX}/Holy/HolyCross.png",
        "vfx.void_portal": f"{VFX}/Void/VoidPortal.png",
        "vfx.earth_shield": f"{VFX}/Earth/EarthShield.png",
        "vfx.earth_spin": f"{VFX}/Earth/EarthSpin.png",
        "vfx.earth_grow": f"{VFX}/Earth/EarthGrow.png",
        "vfx.earth_heal": f"{VFX}/Earth/EarthHeal.png",
        "vfx.wind_slash": f"{VFX}/Wind/WindSlash.png",
        "vfx.explosion": f"{VFX}/Explosion/Explosion_01.png",
        "vfx.fire_slash": f"{VFX}/Fire/FireSlash.png",
        "vfx.void_slash": f"{VFX}/Void/VoidSlash.png",
    }
    for vid, src in vfx_files.items():
        jobs.append(_strip(vid, src, category="vfx", fps=12, loop=False))

    jobs.append({
        "id": "tile.palette",
        "category": "tiles",
        "source": TILESET,
        "op": "grid_cells",
        "cell": 16,
        "cells": [
            [64, 3],   # 0 dungeon floor
            [65, 3],   # 1 dungeon floor variant
            [70, 3],   # 2 wall
            [81, 3],   # 3 wall solid
            [75, 3],   # 4 wall inner
            [5, 23],   # 5 grass
            [8, 23],   # 6 grass 2
            [12, 24],  # 7 dirt/path
            [16, 24],  # 8 dirt 2
            [70, 7],   # 9 wall top-ish
            [77, 9],   # 10 deco
            [64, 9],   # 11 floor dark
        ],
        "fps": 0,
        "loop": False,
        "scale_to": 128,
    })
    jobs.append({
        "id": "tile.crypt",
        "category": "tiles",
        "source": TILESET,
        "op": "grid_cells",
        "cell": 16,
        "cells": [[64, 3], [65, 3], [70, 3], [81, 3], [75, 3], [5, 23], [8, 23], [12, 24], [16, 24], [70, 7], [77, 9], [64, 9]],
        "fps": 0,
        "loop": False,
        "scale_to": 128,
    })
    jobs.append({
        "id": "tile.town",
        "category": "tiles",
        "source": TILESET,
        "op": "grid_cells",
        "cell": 16,
        "cells": [[64, 3], [65, 3], [70, 3], [81, 3], [75, 3], [5, 23], [8, 23], [12, 24], [16, 24], [70, 7], [77, 9], [64, 9]],
        "fps": 0,
        "loop": False,
        "scale_to": 128,
    })
    jobs.append({
        "id": "tile.cave",
        "category": "tiles",
        "source": (
            "mana seed pixel art tileset collection/19.10a - Muddy Cave/"
            "packaged/muddy cave sheets/muddy cave 16x16 v1.png"
        ),
        "op": "grid_cells",
        "cell": 16,
        "cells": [[0, 0], [1, 0], [2, 0], [3, 0], [4, 0]],
        "fps": 0,
        "loop": False,
        "scale_to": 128,
    })
    jobs.append({
        "id": "tile.castle",
        "category": "tiles",
        "source": TILESET,
        "op": "grid_cells",
        "cell": 16,
        "cells": [[34, 3], [35, 3], [40, 3], [47, 3]],
        "fps": 0,
        "loop": False,
        "scale_to": 128,
    })
    portraits = {
        "portrait.fighter": "fantasy character avatars/png/square_512x512/human_male.png",
        "portrait.mage": "fantasy character avatars/png/square_512x512/elf_male.png",
        "portrait.cleric": "fantasy character avatars/png/square_512x512/dwarf_male.png",
    }
    for pid, src in portraits.items():
        jobs.append(_copy(pid, src, category="portraits"))

    loot_files = {
        "item.ghost_ectoplasm": "monloot_16_ghost_ectoplasm_xxx.png",
        "item.red_meat": "monloot_11_red_meat_xxx.png",
        "item.fur_tuft": "monloot_33_fur_tuft_xxx.png",
        "item.monster_bone": "monloot_28_monster_bone_xxx.png",
        "item.monster_scale": "monloot_40_monster_scale_xxx.png",
        "item.coal": "monloot_44_coal_xxx.png",
        "item.human_skull": "monloot_31_human_skull_xxx.png",
        "item.monster_core": "monloot_26_monster_core_xxx.png",
        "item.whetstone": "monloot_45_whetstone_xxx.png",
        "item.ruby": "monloot_50_ruby_xxx.png",
        "item.health_potion": "monloot_88_health_potion_xxx.png",
        "item.mana_potion": "monloot_87_mana_potion_xxx.png",
        "item.dragon_scale": "monloot_17_dragon_scale_xxx.png",
        "item.bear_paw": "monloot_37_bear_paw_xxx.png",
    }
    for iid, name in loot_files.items():
        jobs.append(_copy(iid, f"{LOOT}/{name}", category="icons/loot"))

    skill_files = {
        "icon.skill_attack": f"{SKILL}/Skill_Attack.png",
        "icon.skill_precision": f"{SKILL}/Skill_Precision-Strike.png",
        "icon.skill_stone": f"{SKILL}/Skill_Stone.png",
        "icon.skill_rush": f"{SKILL}/Skill_Rabbit_Rush.png",
        "icon.skill_meteor": f"{SKILL}/Skill_Meteor.png",
        "icon.skill_ice": f"{SKILL}/Skill_Ice.png",
        "icon.skill_lightning": f"{SKILL}/Skill_Lightning.png",
        "icon.skill_blackhole": f"{SKILL}/Skill_Blackhole.png",
        "icon.skill_heaven": f"{SKILL}/Skill_Heaven.png",
        "icon.skill_heal": f"{SKILL}/Skill_Heal.png",
        "icon.skill_vaccine": f"{SKILL}/Skill_Vaccine.png",
        "icon.skill_gold": f"{SKILL}/Skill_Gold.png",
        "icon.skill_health_up": f"{SKILL}/Skill_Health_Up.png",
        "icon.fire": f"{SPELL}/1_fire_1.png",
        "icon.ice": f"{SPELL}/1_ice_1.png",
        "icon.lightning": f"{SPELL}/1_lightning_1.png",
        "icon.sword": f"{SPELL}/1_weapon_sword.png",
    }
    for iid, src in skill_files.items():
        jobs.append(_copy(iid, src, category="icons/skills"))

    for iid, name in {
        "icon.equip_axe": "equip_icon_axe_0.png",
        "icon.equip_hammer": "equip_icon_hammer_0.png",
        "icon.equip_crystal": "equip_icon_cyristal.png",
        "icon.equip_gem": "equip_icon_gem_red.png",
        "icon.equip_shield": "equip_icon_shield_wood.png",
        "icon.equip_ring": "equip_icon_ring_gold.png",
        "icon.equip_stone": "equip_icon_stone.png",
        "icon.equip_potion_red": "equip_icon_potion_red_0.png",
        "icon.equip_potion_blue": "equip_icon_potion_blue_0.png",
    }.items():
        jobs.append(_copy(iid, f"{EQUIP}/{name}", category="icons/equip"))

    jobs.append(_copy("icon.rune_1", f"{RUNE}/spr_rune_xxx_1.png", category="icons/runes"))
    jobs.append(_copy("icon.stat_attack", f"{STAT}/Stat_Attack_01.png", category="icons/stats"))
    jobs.append(_copy("icon.stat_defense", f"{STAT}/Stat_Defense.png", category="icons/stats"))

    for nid, fname in {
        "npc.vendor": "TentacleButcher_Idle.png",
        "npc.inn": "BarMan_Idle.png",
        "npc.trainer": "ShieldMan_Idle.png",
        "npc.librarian": "Librarian_Idle.png",
    }.items():
        jobs.append(_strip(nid, f"{NPC}/{fname}", category="npcs", fps=6, loop=True))

    jobs.append({
        "id": "ui.frame",
        "category": "ui",
        "source": f"{GUI}/Frame/BasicFrame_Square_m.png",
        "op": "copy_raw",
        "required": False,
    })
    jobs.append({
        "id": "ui.slot",
        "category": "ui",
        "source": f"{GUI}/Frame/SlotFrame_Square_02_Bg.png",
        "op": "copy_raw",
        "required": False,
    })
    jobs.append({
        "id": "ui.popup",
        "category": "ui",
        "source": f"{GUI}/Popup/Popup_02_White_Bg.png",
        "op": "copy_raw",
        "required": False,
    })
    jobs.append({
        "id": "ui.bar_bg",
        "category": "ui",
        "source": f"{GUI}/Slider/Slider_Batteary_Bg.png",
        "op": "copy_raw",
        "required": False,
    })
    jobs.append({
        "id": "ui.bar_fill",
        "category": "ui",
        "source": f"{GUI}/Slider/Slider_Batteary_Fill.png",
        "op": "copy_raw",
        "required": False,
    })
    jobs.append({
        "id": "ui.button",
        "category": "ui",
        "source": f"{GUI}/Button/Button_Rectangle_01_Convex_White_Bg.png",
        "op": "copy_raw",
        "required": False,
    })

    jobs.extend([
        _audio("sfx.sword_hit", f"{SFX_ROOT}/Sword_Combat_Sounds/Big_Hit_Target_01.wav"),
        _audio("sfx.sword_swing", f"{SFX_ROOT}/Sword_Combat_Sounds/Block_With_Sword_01.wav"),
        _audio("sfx.block", f"{SFX_ROOT}/Sword_Combat_Sounds/Block_Metal_Armour_01.wav"),
        _audio("sfx.magic", f"{SFX_ROOT}/Fantasy_Combat_Sounds_01/Arch_Magical_Shoot_01.wav"),
        _audio("sfx.click", f"{UI_SFX}/Clicks_Sounds/Click_Elegant_01.wav"),
        _audio("sfx.coins", f"{UI_SFX}/Coins_Sounds/Cool_Coins_Obtain_01.wav"),
        _audio("sfx.bag", f"{UI_SFX}/RPG_Inventory_Sounds/Bag_Interaction_Soft_01.wav"),
        _audio("sfx.shop", f"{UI_SFX}/RPG_Shop_Sounds/Box_01.wav"),
        _audio("sfx.monster", f"{MON_SFX}/Aggressive_01.wav"),
        _audio("amb.dungeon", f"{AMB}/Ambience_Dungeon_01_Loop.wav"),
        _audio("amb.town", f"{AMB}/Ambience_Forest_Loop.wav"),
    ])
    return jobs
