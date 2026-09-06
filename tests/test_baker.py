from __future__ import annotations

from pathlib import Path

from PIL import Image

from grok_rpg.baker import bake_all, bake_job, detect_frame_h, fit_to_cell


def _png(path: Path, w: int, h: int, color=(255, 0, 0, 255)) -> None:
    Image.new("RGBA", (w, h), color).save(path)


def test_fit_16_to_128() -> None:
    im = Image.new("RGBA", (16, 16), (10, 20, 30, 255))
    out = fit_to_cell(im, 128)
    assert out.size == (128, 128)
    # nearest 8x: solid fill
    assert out.getpixel((0, 0))[:3] == (10, 20, 30)
    assert out.getpixel((127, 127))[:3] == (10, 20, 30)


def test_fit_64_to_128() -> None:
    im = Image.new("RGBA", (64, 64), (1, 2, 3, 255))
    out = fit_to_cell(im, 128)
    assert out.size == (128, 128)
    assert out.getpixel((0, 0))[:3] == (1, 2, 3)


def test_fit_128_unchanged() -> None:
    im = Image.new("RGBA", (128, 128), (9, 8, 7, 255))
    out = fit_to_cell(im, 128)
    assert out.size == (128, 128)
    assert out.getpixel((4, 4))[:3] == (9, 8, 7)


def test_strip_and_copy(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    dest = tmp_path / "baked"
    bundle.mkdir()
    strip = Image.new("RGBA", (64, 192), (0, 0, 0, 0))
    for i, c in enumerate([(255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255)]):
        for y in range(i * 64, i * 64 + 64):
            for x in range(64):
                strip.putpixel((x, y), c)
    src = bundle / "strip.png"
    strip.save(src)
    icon = bundle / "icon.png"
    _png(icon, 128, 128, (4, 5, 6, 255))

    jobs = [
        {"id": "hero.idle", "category": "characters", "source": "strip.png", "op": "strip_v", "frame": 64, "fps": 8},
        {"id": "item.gem", "category": "icons", "source": "icon.png", "op": "copy"},
    ]
    index = bake_all(jobs, bundle=bundle, dest_root=dest, write_manifest_copy=False)
    idle = index["by_id"]["hero.idle"]
    assert len(idle["frames"]) == 3
    gem = Image.open(dest / index["by_id"]["item.gem"]["frames"][0])
    assert gem.size == (128, 128)
    frame0 = Image.open(dest / idle["frames"][0])
    assert frame0.size == (128, 128)
    assert frame0.getpixel((10, 10))[:3] == (255, 0, 0)


def test_detects_tall_frames_not_square_halves() -> None:
    im = Image.new("RGBA", (32, 256), (0, 0, 0, 0))
    for i in range(4):
        y0 = i * 64
        for y in range(y0 + 16, y0 + 32):
            for x in range(8, 24):
                im.putpixel((x, y), (255, 255, 255, 255))
        for y in range(y0 + 32, y0 + 48):
            for x in range(8, 24):
                im.putpixel((x, y), (255, 255, 255, 255))
    assert detect_frame_h(im, 32) == 64


def test_strip_frame_h(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    dest = tmp_path / "baked"
    bundle.mkdir()
    strip = Image.new("RGBA", (32, 128), (0, 0, 0, 0))
    for i, c in enumerate([(255, 0, 0, 255), (0, 255, 0, 255)]):
        for y in range(i * 64, i * 64 + 64):
            for x in range(32):
                strip.putpixel((x, y), c)
    (bundle / "tall.png").parent.mkdir(parents=True, exist_ok=True)
    strip.save(bundle / "tall.png")
    jobs = [{"id": "hero.idle", "category": "c", "source": "tall.png", "op": "strip_v", "frame": 32, "frame_h": 64}]
    index = bake_all(jobs, bundle=bundle, dest_root=dest, write_manifest_copy=False)
    assert len(index["by_id"]["hero.idle"]["frames"]) == 2


def test_missing_bundle_job(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    dest = tmp_path / "baked"
    job = {"id": "nope", "category": "x", "source": "missing.png", "op": "copy"}
    try:
        bake_job(job, bundle=bundle, dest_root=dest)
        raised = False
    except FileNotFoundError:
        raised = True
    assert raised
