# -*- coding: utf-8 -*-
"""Generate 16:9 and 16:10 cover images for a project.

Usage:
    python engine/cover.py --project examples/distributed-lock

If <project>/cover.py defines render(width, height) -> PIL.Image, it is used.
Otherwise a clean generic cover is generated from script.json.
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(ENGINE))

from graphics import BLUE, FAINT, GRID, INK, MUTED, card, chip, rgba, text, wrap  # noqa: E402


def gradient_bg(w, h):
    yy = np.linspace(0, 1, h)[:, None]
    top = np.array((252, 253, 255), dtype=np.float64)
    bot = np.array((241, 245, 250), dtype=np.float64)
    arr = top * (1 - yy) + bot * yy
    arr = np.repeat(arr[:, None, :], w, axis=1)
    gy, gx = np.mgrid[0:h, 0:w]
    for (cx, cy, radius, color, strength) in [
        (w * 0.86, h * 0.10, max(w, h) * 0.36, (37, 99, 235), 0.055),
        (w * 0.10, h * 0.92, max(w, h) * 0.40, (124, 58, 237), 0.040),
    ]:
        dist = np.sqrt((gx - cx) ** 2 + (gy - cy) ** 2)
        glow = np.clip(1 - dist / radius, 0, 1) ** 2 * strength
        arr += np.array(color)[None, None, :] * glow[:, :, None]
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(img, "RGBA")
    for x in range(0, w + 1, 80):
        major = (x % 400 == 0)
        d.line([x, 0, x, h], fill=rgba(GRID, 0.30 if major else 0.16), width=1)
    for y in range(0, h + 1, 80):
        major = (y % 400 == 0)
        d.line([0, y, w, y], fill=rgba(GRID, 0.30 if major else 0.16), width=1)
    return img


def default_cover(w, h, title, series):
    img = gradient_bg(w, h)
    d = ImageDraw.Draw(img, "RGBA")
    text(d, (120, 86), "●", 26, "r", BLUE, alpha=0.9)
    text(d, (146, 82), series, 27, "r", MUTED)
    text(d, (w - 120, 82), "EXPLAINER", 24, "r", FAINT, anchor="ra")

    x = 120
    y = 210
    max_w = int(w * 0.62)
    size = 92 if len(title) <= 16 else (78 if len(title) <= 26 else 64)
    lines = wrap(d, title, size, "b", max_w)
    for i, ln in enumerate(lines):
        text(d, (x, y + i * (size + 18)), ln, size, "b", INK)
    under = y + len(lines) * (size + 18) + 26
    d.rounded_rectangle([x, under, x + 210, under + 7], radius=3, fill=rgba(BLUE, 0.9))

    card(img, d, (x, under + 64), 560, 150, 18, (255, 255, 255), (226, 232, 240))
    text(d, (x + 34, under + 92), "AI 配音 · 逐帧渲染 · 1080P", 27, "r", MUTED)
    text(d, (x + 34, under + 138), "从脚本到成片，一条流水线", 24, "r", FAINT)
    return img


def load_cover(project: Path):
    path = project / "cover.py"
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location("project_cover", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["project_cover"] = mod
    spec.loader.exec_module(mod)
    if not hasattr(mod, "render"):
        raise SystemExit("cover.py must define render(width, height) -> PIL.Image")
    return mod.render


def main():
    ap = argparse.ArgumentParser(description="Generate 16:9 and 16:10 covers")
    ap.add_argument("--project", default=".")
    args = ap.parse_args()
    project = Path(args.project).resolve()
    cfg = json.loads((project / "script.json").read_text(encoding="utf-8"))
    out = project / "out"
    out.mkdir(exist_ok=True)
    render = load_cover(project) or (lambda w, h: default_cover(w, h, cfg["title"], cfg["series"]))
    for name, (w, h) in {"cover_16x9.png": (1920, 1080), "cover_16x10.png": (1920, 1200)}.items():
        p = out / name
        render(w, h).save(p)
        print(f"cover -> {p}")


if __name__ == "__main__":
    main()
