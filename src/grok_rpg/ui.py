from __future__ import annotations

from typing import Any

import pygame

from grok_rpg.constants import VIEW_W, VIEW_H
from grok_rpg.inventory import SLOTS


def draw_bar(surf: pygame.Surface, x: int, y: int, w: int, h: int, frac: float, fg: tuple[int, int, int], bg=(30, 20, 20)) -> None:
    pygame.draw.rect(surf, bg, (x, y, w, h))
    pygame.draw.rect(surf, fg, (x, y, int(w * max(0.0, min(1.0, frac))), h))
    pygame.draw.rect(surf, (240, 220, 160), (x, y, w, h), 1)


def blit_icon(surf: pygame.Surface, icon: pygame.Surface | None, x: int, y: int, size: int = 48) -> None:
    if icon is None:
        pygame.draw.rect(surf, (50, 40, 30), (x, y, size, size))
        pygame.draw.rect(surf, (180, 150, 80), (x, y, size, size), 1)
        return
    scaled = pygame.transform.scale(icon, (size, size))
    surf.blit(scaled, (x, y))


def hud(surf: pygame.Surface, player: Any, abilities: dict, bank: Any, font: pygame.font.Font) -> None:
    draw_bar(surf, 16, 16, 220, 16, player.hp / max(1, player.hp_max), (180, 40, 40))
    label = "HP"
    surf.blit(font.render(f"{label} {int(player.hp)}/{int(player.hp_max)}", True, (255, 230, 200)), (16, 34))
    color = (80, 140, 220) if player.resource_name == "mana" else (200, 90, 40)
    draw_bar(surf, 16, 54, 220, 14, player.resource / max(1, player.resource_max), color)
    surf.blit(font.render(f"{player.resource_name} {int(player.resource)}", True, (220, 210, 180)), (16, 70))
    surf.blit(font.render(f"Gold {player.inv.gold}", True, (240, 210, 80)), (16, 90))
    if player.shield > 0:
        surf.blit(font.render(f"Ward {int(player.shield)}", True, (180, 220, 255)), (16, 108))

    x = VIEW_W // 2 - 120
    y = VIEW_H - 70
    for i, aid in enumerate(player.ability_ids):
        icon_id = abilities[aid].get("icon")
        icon = bank.first(icon_id) if icon_id else None
        blit_icon(surf, icon, x + i * 58, y, 48)
        ready = player.cooldowns.ready(aid, player.now)
        if not ready:
            overlay = pygame.Surface((48, 48), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            surf.blit(overlay, (x + i * 58, y))
        surf.blit(font.render(str(i + 1), True, (255, 255, 220)), (x + i * 58 + 2, y + 32))


def panel_inventory(surf: pygame.Surface, player: Any, items: dict, bank: Any, font: pygame.font.Font) -> None:
    box = pygame.Rect(80, 60, VIEW_W - 160, VIEW_H - 140)
    pygame.draw.rect(surf, (18, 12, 10), box)
    pygame.draw.rect(surf, (180, 150, 80), box, 2)
    surf.blit(font.render("Inventory  [I close]  click item: use/equip   vendor/craft nearby with E", True, (240, 220, 180)), (box.x + 12, box.y + 10))
    x, y = box.x + 16, box.y + 40
    i = 0
    player._inv_hit = []
    for item_id, qty in player.inv.stacks.items():
        spec = items[item_id]
        icon = bank.first(spec["icon"])
        r = pygame.Rect(x, y, 52, 52)
        blit_icon(surf, icon, x, y, 48)
        surf.blit(font.render(str(qty), True, (255, 255, 255)), (x + 32, y + 34))
        player._inv_hit.append((r, item_id))
        x += 56
        i += 1
        if i % 10 == 0:
            x = box.x + 16
            y += 58
    ey = box.bottom - 90
    surf.blit(font.render("Equipped", True, (240, 220, 180)), (box.x + 16, ey - 18))
    x = box.x + 16
    for slot in SLOTS:
        item_id = player.inv.equipped.get(slot)
        icon = bank.first(items[item_id]["icon"]) if item_id else None
        blit_icon(surf, icon, x, ey, 40)
        surf.blit(font.render(slot[:3], True, (180, 160, 120)), (x, ey + 42))
        x += 48


def panel_vendor(surf: pygame.Surface, player: Any, items: dict, bank: Any, font: pygame.font.Font) -> None:
    box = pygame.Rect(200, 80, 880, 700)
    pygame.draw.rect(surf, (16, 12, 10), box)
    pygame.draw.rect(surf, (180, 150, 80), box, 2)
    surf.blit(font.render("Butcher — click a stack to sell   [Esc close]", True, (240, 220, 180)), (box.x + 16, box.y + 12))
    x, y = box.x + 16, box.y + 50
    player._vendor_hit = []
    for item_id, qty in player.inv.stacks.items():
        spec = items[item_id]
        if spec.get("kind") == "gold":
            continue
        icon = bank.first(spec["icon"])
        r = pygame.Rect(x, y, 400, 40)
        pygame.draw.rect(surf, (40, 28, 18), r)
        blit_icon(surf, icon, x, y, 36)
        price = int(spec.get("sell", 1))
        if spec.get("kind") == "equipment":
            price = max(1, price // 2)
        surf.blit(font.render(f"{spec['name']} x{qty}   {price}g each", True, (240, 220, 180)), (x + 44, y + 10))
        player._vendor_hit.append((r, item_id))
        y += 44
        if y > box.bottom - 60:
            break


def panel_craft(surf: pygame.Surface, player: Any, recipes: dict, items: dict, bank: Any, font: pygame.font.Font) -> None:
    box = pygame.Rect(200, 80, 880, 700)
    pygame.draw.rect(surf, (16, 12, 10), box)
    pygame.draw.rect(surf, (180, 150, 80), box, 2)
    surf.blit(font.render("Artificer — click a recipe to craft   [Esc close]", True, (240, 220, 180)), (box.x + 16, box.y + 12))
    y = box.y + 50
    player._craft_hit = []
    for rid, rec in recipes.items():
        out = items[rec["output"]]
        can = player.inv.can_craft(rec)
        r = pygame.Rect(box.x + 16, y, 840, 70)
        pygame.draw.rect(surf, (40, 50, 28) if can else (40, 20, 18), r)
        icon = bank.first(out["icon"])
        blit_icon(surf, icon, r.x + 8, r.y + 10, 48)
        need = ", ".join(f"{q} {items[i]['name']}" for i, q in rec["inputs"].items())
        surf.blit(font.render(f"{out['name']}  ({out.get('rarity', 'common')})", True, (240, 220, 180)), (r.x + 64, r.y + 10))
        surf.blit(font.render(need, True, (200, 190, 160)), (r.x + 64, r.y + 36))
        player._craft_hit.append((r, rid))
        y += 80
