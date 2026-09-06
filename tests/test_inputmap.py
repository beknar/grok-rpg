from __future__ import annotations

import pygame

from grok_rpg.data_load import catalog
from grok_rpg.inputmap import keydown_action, keys_for


def test_skills_include_qrf() -> None:
    binds = catalog()["input"]
    assert pygame.K_q in keys_for(binds, "skill1")
    assert pygame.K_r in keys_for(binds, "skill3")
    assert pygame.K_f in keys_for(binds, "skill4")
    assert pygame.K_e in keys_for(binds, "interact")
    assert pygame.K_e not in keys_for(binds, "skill2")


def test_keydown_spellbook() -> None:
    binds = catalog()["input"]
    assert keydown_action(pygame.K_b, binds, "spellbook")
