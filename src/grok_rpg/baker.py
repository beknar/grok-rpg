from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from PIL import Image

from grok_rpg.manifest import default_jobs
from grok_rpg.paths import BAKED_DIR, DATA_DIR, require_bundle


CELL = 128


def fit_to_cell(im: Image.Image, size: int = CELL) -> Image.Image:
    """Uniform nearest-neighbor scale into a transparent size×size canvas."""
    im = im.convert("RGBA")
    w, h = im.size
    if w == size and h == size:
        return im
    scale = min(size / w, size / h)
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    resized = im.resize((nw, nh), Image.NEAREST)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(resized, ((size - nw) // 2, (size - nh) // 2), resized)
    return canvas


def _slice_strip_v(im: Image.Image, frame_w: int, frame_h: int | None = None) -> list[Image.Image]:
    w, h = im.size
    if frame_w <= 0:
        frame_w = w
    if frame_h is None or frame_h <= 0:
        frame_h = frame_w
    frames = []
    y = 0
    while y < h:
        remaining = h - y
        if remaining < frame_h * 0.5:
            break
        fh = min(frame_h, remaining)
        frames.append(im.crop((0, y, min(frame_w, w), y + fh)))
        y += frame_h
    if not frames:
        frames.append(im)
    return frames


def _frame_is_half(fr: Image.Image) -> bool:
    fr = fr.convert("RGBA")
    w, h = fr.size
    pix = list(fr.getdata())
    rows = [i // w for i, p in enumerate(pix) if p[3] > 20]
    if not rows:
        return True
    top, bot = min(rows), max(rows)
    span = bot - top + 1
    if span / h > 0.65:
        return False
    return top >= h * 0.35 or bot <= h * 0.65


def detect_frame_h(im: Image.Image, frame_w: int) -> int:
    """If square slices alternate top/bottom halves, the real frame is 2× width."""
    square = _slice_strip_v(im, frame_w, frame_w)
    if len(square) < 4:
        return frame_w
    halves = sum(1 for fr in square if _frame_is_half(fr))
    if halves >= max(3, int(len(square) * 0.4)):
        return frame_w * 2
    return frame_w


def _slice_strip_h(im: Image.Image, frame: int) -> list[Image.Image]:
    w, h = im.size
    if frame <= 0:
        frame = h
    frames = []
    x = 0
    while x + frame <= w:
        frames.append(im.crop((x, 0, x + frame, min(frame, h))))
        x += frame
    if not frames:
        frames.append(im)
    return frames


def resolve_source(bundle: Path, spec: str) -> Path:
    path = bundle / spec
    if path.is_file():
        return path
    matches = list(bundle.glob(spec))
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise FileNotFoundError(f"Source glob matched {len(matches)} files: {spec}")
    raise FileNotFoundError(f"Source not found: {spec}")


def bake_job(
    job: dict[str, Any],
    *,
    bundle: Path,
    dest_root: Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    op = job["op"]
    job_id = job["id"]
    category = job.get("category", "misc")
    out_dir = dest_root / category / job_id.replace("/", "_")
    scale_to = job.get("scale_to", CELL)

    if op == "audio_copy":
        src = resolve_source(bundle, job["source"])
        dest = dest_root / "audio" / Path(src.name)
        if dry_run:
            return {"id": job_id, "frames": [str(dest.relative_to(dest_root))], "kind": "audio"}
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        return {"id": job_id, "frames": [str(dest.relative_to(dest_root))], "kind": "audio", "fps": 0}

    if op == "copy_raw":
        src = resolve_source(bundle, job["source"])
        dest = dest_root / category / src.name
        if dry_run:
            return {"id": job_id, "frames": [str(dest.relative_to(dest_root))], "kind": "raw"}
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        return {"id": job_id, "frames": [str(dest.relative_to(dest_root))], "kind": "raw", "fps": 0}

    src = resolve_source(bundle, job["source"])
    im = Image.open(src).convert("RGBA")
    pieces: list[Image.Image] = []
    if op == "copy":
        pieces = [im]
    elif op == "strip_v":
        frame_w = int(job.get("frame") or im.size[0])
        frame_h = job.get("frame_h")
        if frame_h is None:
            frame_h = detect_frame_h(im, frame_w)
        pieces = _slice_strip_v(im, frame_w, int(frame_h))
    elif op == "strip_h":
        frame = int(job.get("frame") or im.size[1])
        pieces = _slice_strip_h(im, frame)
    elif op == "grid_cells":
        cell = int(job.get("cell", 16))
        for col, row in job["cells"]:
            x, y = int(col) * cell, int(row) * cell
            pieces.append(im.crop((x, y, x + cell, y + cell)))
    else:
        raise ValueError(f"Unknown op {op} for job {job_id}")

    rels: list[str] = []
    if not dry_run:
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
    for i, piece in enumerate(pieces):
        if scale_to:
            piece = fit_to_cell(piece, int(scale_to))
        name = f"frame_{i:03d}.png"
        rel = f"{category}/{job_id.replace('/', '_')}/{name}"
        rels.append(rel)
        if not dry_run:
            piece.save(out_dir / name)
    return {
        "id": job_id,
        "frames": rels,
        "kind": "sprite",
        "fps": int(job.get("fps", 8)),
        "loop": bool(job.get("loop", True)),
        "pingpong": bool(job.get("pingpong", False)),
    }


def bake_all(
    jobs: list[dict[str, Any]] | None = None,
    *,
    bundle: Path | None = None,
    dest_root: Path | None = None,
    dry_run: bool = False,
    write_manifest_copy: bool = False,
) -> dict[str, Any]:
    jobs = jobs if jobs is not None else default_jobs()
    bundle = bundle or require_bundle()
    dest_root = dest_root or BAKED_DIR
    index: dict[str, Any] = {"jobs": []}
    errors: list[str] = []
    for job in jobs:
        try:
            result = bake_job(job, bundle=bundle, dest_root=dest_root, dry_run=dry_run)
            index["jobs"].append(result)
        except FileNotFoundError as exc:
            errors.append(f"{job.get('id')}: {exc}")
            if job.get("required", True):
                raise
    index["errors"] = errors
    index_by_id = {j["id"]: j for j in index["jobs"]}
    index["by_id"] = index_by_id
    if not dry_run:
        dest_root.mkdir(parents=True, exist_ok=True)
        (dest_root / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
        if write_manifest_copy:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            (DATA_DIR / "asset_manifest.json").write_text(
                json.dumps(jobs, indent=2), encoding="utf-8"
            )
    return index


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bake Complete RPG Creator Bundle frames to 128×128.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        bundle = require_bundle()
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 2
    dest = args.out or BAKED_DIR
    print(f"bundle: {bundle}")
    print(f"out:    {dest}")
    index = bake_all(bundle=bundle, dest_root=dest, dry_run=args.dry_run)
    print(f"baked {len(index['jobs'])} jobs")
    if index.get("errors"):
        print("skipped optional:", *index["errors"], sep="\n  ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
