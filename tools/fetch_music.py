#!/usr/bin/env python3
"""Download CC0 RPG loops into third_party/music/."""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "third_party" / "music"

TRACKS = {
    "title.ogg": "https://opengameart.org/sites/default/files/Menu%20Song.ogg",
    "town.mp3": "https://opengameart.org/sites/default/files/homestead.mp3",
    "crypt.mp3": "https://opengameart.org/sites/default/files/wandering_woodlands.mp3",
    "cave.mp3": "https://opengameart.org/sites/default/files/back_to_nature.mp3",
    "castle.mp3": "https://opengameart.org/sites/default/files/jaunt.mp3",
    "boss.mp3": "https://opengameart.org/sites/default/files/rbl.mp3",
}


def fetch_all(*, force: bool = False) -> list[Path]:
    DEST.mkdir(parents=True, exist_ok=True)
    got: list[Path] = []
    for name, url in TRACKS.items():
        path = DEST / name
        if path.is_file() and path.stat().st_size > 1000 and not force:
            got.append(path)
            continue
        req = urllib.request.Request(url, headers={"User-Agent": "grok-rpg/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
        except OSError as exc:
            print(f"skip {name}: {exc}", file=sys.stderr)
            continue
        if len(data) < 1000:
            print(f"skip {name}: too small ({len(data)} bytes)", file=sys.stderr)
            continue
        path.write_bytes(data)
        print(f"saved {path} ({len(data)} bytes)")
        got.append(path)
    return got


def main() -> int:
    files = fetch_all()
    print(f"{len(files)}/{len(TRACKS)} tracks ready in {DEST}")
    return 0 if files else 1


if __name__ == "__main__":
    raise SystemExit(main())
