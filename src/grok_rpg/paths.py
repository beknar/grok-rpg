from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
BAKED_DIR = REPO_ROOT / "assets" / "baked"
SAVES_DIR = REPO_ROOT / "saves"
TESTS_DIR = REPO_ROOT / "tests"

_BUNDLE_CANDIDATES = (
    Path("/mnt/i/game assets/complete rpg creator bundle"),
    Path(r"I:\game assets\complete rpg creator bundle"),
    Path("/mnt/e/game assets/complete rpg creator bundle"),
)


def bundle_root() -> Path | None:
    env = os.environ.get("GROK_RPG_ASSETS")
    if env:
        p = Path(env)
        if p.is_dir():
            return p
        return None
    for cand in _BUNDLE_CANDIDATES:
        if cand.is_dir():
            return cand
    return None


def require_bundle() -> Path:
    root = bundle_root()
    if root is None:
        raise FileNotFoundError(
            "GROK_RPG_ASSETS is missing or not a directory. "
            "Set it to the Complete RPG Creator Bundle path."
        )
    return root
