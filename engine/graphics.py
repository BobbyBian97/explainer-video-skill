# -*- coding: utf-8 -*-
"""Shared drawing primitives for explainer videos."""
import math
import os
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080

BG_TOP = (252, 253, 255)
BG_BOTTOM = (241, 245, 250)
GRID = (205, 216, 229)
INK = (15, 23, 42)
MUTED = (100, 116, 139)
FAINT = (148, 163, 184)
BLUE = (37, 99, 235)
BLUE_D = (29, 78, 216)
BLUE_L = (219, 234, 254)
PURPLE = (124, 58, 237)
PURPLE_L = (237, 233, 254)
GREEN = (22, 163, 74)
GREEN_L = (220, 252, 231)
RED = (220, 38, 38)
RED_L = (254, 226, 226)
AMBER = (217, 119, 6)
AMBER_L = (254, 243, 199)
WHITE = (255, 255, 255)
LINE = (226, 232, 240)
PANEL = (255, 255, 255)
NAVY = (15, 23, 42)

FONT_DIR = Path(os.environ.get("EXPLAINER_FONT_DIR", "C:/Windows/Fonts"))
_FONT_CACHE = {}


def _first_existing(candidates):
    for c in candidates:
        p = Path(c).expanduser()
        if not p.is_absolute():
            p = FONT_DIR / p
        if p.exists():
            return str(p)
    return None


# Fonts are resolved once at import time. Override with env vars if your OS
# has different Chinese fonts (e.g. PingFang on macOS, Noto CJK on Linux).
_FONT_REG = os.environ.get("EXPLAINER_FONT_REGULAR") or _first_existing([
    "msyh.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
]) or "msyh.ttc"
_FONT_BOLD = os.environ.get("EXPLAINER_FONT_BOLD") or _first_existing([
    "msyhbd.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    _FONT_REG,
]) or _FONT_REG
_FONT_CODE = os.environ.get("EXPLAINER_FONT_CODE") or _first_existing([
    "consola.ttf",
    "/System/Library/Fonts/Menlo.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]) or "consola.ttf"
_FONT_CODE_B = os.environ.get("EXPLAINER_FONT_CODE_BOLD") or _first_existing([
    "consolab.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    _FONT_CODE,
]) or _FONT_CODE


def font(size, weight="r", code=False):
    if code:
        name = _FONT_CODE_B if weight == "b" else _FONT_CODE
    else:
        name = _FONT_BOLD if weight == "b" else _FONT_REG
    key = (name, size)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(name, size, index=0)
    return _FONT_CACHE[key]


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = clamp(x)
    return 3 * x * x - 2 * x * x * x


def prog(t, start, dur=0.5):
    return ease_out((t - start) / dur) if dur > 0 else float(t >= start)


def rgba(color, alpha=1.0):
    if len(color) == 4:
        r, g, b, a = color
        return (r, g, b, int(a * clamp(alpha)))
    return (color[0], color[1], color[2], int(255 * clamp(alpha)))


def text(d, xy, s, size=36, weight="r", color=INK, anchor="lt", alpha=1.0, code=False):
    f = font(size, weight, code)
    d.text(xy, s, font=f, fill=rgba(color, alpha), anchor=anchor)
    return f


def textlen(d, s, size=36, weight="r", code=False):
    return d.textlength(s, font=font(size, weight, code))


def wrap(d, s, size=36, weight="r", max_width=1000, code=False):
    f = font(size, weight, code)
    lines, cur = [], ""
    for ch in s:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
        test = cur + ch
        if d.textlength(test, font=f) > max_width and cur:
            # Prefer a space break over splitting an English word.
            cut = cur.rfind(" ")
            if cut > max(2, len(cur) * 0.3):
                lines.append(cur[:cut])
                cur = cur[cut + 1 :] + ch
            else:
                lines.append(cur)
                cur = ch
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines


def multiline(d, xy, s, size=34, weight="r", color=INK, anchor="la", alpha=1.0, max_width=1000, line_gap=10, code=False):
    lines = wrap(d, s, size, weight, max_width, code)
    f = font(size, weight, code)
    lh = size + line_gap
    x, y = xy
    for i, ln in enumerate(lines):
        d.text((x, y + i * lh), ln, font=f, fill=rgba(color, alpha), anchor=anchor)
    return len(lines) * lh


def shadow(d, box, radius, color, alpha=1.0, blur=10, offset=(0, 8)):
    x1, y1, x2, y2 = box
    ox, oy = offset
    for i in range(blur, 0, -1):
        a = alpha * 0.055 * (1 - i / (blur + 1))
        spread = i
        d.rounded_rectangle(
            [x1 + ox - spread * 0.3, y1 + oy - spread * 0.3, x2 + ox + spread * 0.3, y2 + oy + spread * 0.3],
            radius + spread * 0.3,
            fill=rgba((15, 23, 42), a),
        )


def card(img, d, xy, w, h, radius=20, fill=PANEL, border=LINE, alpha=1.0, sh=True, bw=2):
    x, y = xy
    box = [x, y, x + w, y + h]
    if sh:
        shadow(d, box, radius, fill, alpha=alpha, blur=12, offset=(0, 10))
    d.rounded_rectangle(box, radius=radius, fill=rgba(fill, alpha), outline=rgba(border, alpha), width=bw)
    return box


def chip(d, xy, s, size=25, fg=MUTED, bg=None, alpha=1.0, padx=16, pady=9, radius=999, weight="r", anchor="lt"):
    f = font(size, weight)
    tw = d.textlength(s, font=f)
    x, y = xy
    h = size + pady * 2
    w = tw + padx * 2
    if anchor == "mm":
        x, y = x - w / 2, y - h / 2
    if bg is not None:
        d.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=rgba(bg, alpha))
    d.text((x + padx, y + h / 2), s, font=f, fill=rgba(fg, alpha), anchor="lm")
    return w, h


def arrow(d, p1, p2, color=BLUE, width=4, head=16, alpha=1.0, dashed=False):
    x1, y1 = p1
    x2, y2 = p2
    dx, dy = x2 - x1, y2 - y1
    dist = math.hypot(dx, dy) or 1
    ux, uy = dx / dist, dy / dist
    ex, ey = x2 - ux * head * 0.6, y2 - uy * head * 0.6
    if dashed:
        n = int(dist / 22)
        for i in range(n):
            if i % 2 == 0:
                a = i / n
                b = min(1, (i + 1) / n)
                d.line([x1 + dx * a, y1 + dy * a, x1 + dx * b, y1 + dy * b], fill=rgba(color, alpha), width=width)
    else:
        d.line([x1, y1, ex, ey], fill=rgba(color, alpha), width=width)
    nx, ny = -uy, ux
    tip = (x2, y2)
    left = (ex + nx * head * 0.55, ey + ny * head * 0.55)
    right = (ex - nx * head * 0.55, ey - ny * head * 0.55)
    d.polygon([tip, left, right], fill=rgba(color, alpha))


def bezier(points, n=40):
    pts = np.array(points, dtype=float)
    out = []
    for i in range(n + 1):
        t = i / n
        p = (1 - t) ** 3 * pts[0] + 3 * (1 - t) ** 2 * t * pts[1] + 3 * (1 - t) * t * t * pts[2] + t**3 * pts[3]
        out.append(tuple(p))
    return out


def curve_arrow(d, points, color=BLUE, width=4, head=16, alpha=1.0):
    pts = bezier(points, 48)
    d.line(pts, fill=rgba(color, alpha), width=width, joint="curve")
    (x1, y1), (x2, y2) = pts[-6], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    dist = math.hypot(dx, dy) or 1
    ux, uy = dx / dist, dy / dist
    nx, ny = -uy, ux
    ex, ey = x2 - ux * head * 0.6, y2 - uy * head * 0.6
    d.polygon([(x2, y2), (ex + nx * head * 0.55, ey + ny * head * 0.55), (ex - nx * head * 0.55, ey - ny * head * 0.55)], fill=rgba(color, alpha))


def icon_lock(d, cx, cy, s=64, color=INK, alpha=1.0, width=None):
    wd = width or max(3, int(s * 0.09))
    d.rounded_rectangle([cx - s * 0.36, cy - s * 0.02, cx + s * 0.36, cy + s * 0.42], radius=s * 0.12, outline=rgba(color, alpha), width=wd)
    d.arc([cx - s * 0.26, cy - s * 0.48, cx + s * 0.26, cy + s * 0.14], 180, 360, fill=rgba(color, alpha), width=wd)
    d.ellipse([cx - s * 0.055, cy + s * 0.12, cx + s * 0.055, cy + s * 0.23], fill=rgba(color, alpha))
    d.line([cx, cy + s * 0.2, cx, cy + s * 0.31], fill=rgba(color, alpha), width=wd)


def icon_clock(d, cx, cy, s=64, color=INK, alpha=1.0, width=None):
    wd = width or max(3, int(s * 0.08))
    d.ellipse([cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2], outline=rgba(color, alpha), width=wd)
    d.line([cx, cy, cx, cy - s * 0.30], fill=rgba(color, alpha), width=wd)
    d.line([cx, cy, cx + s * 0.22, cy + s * 0.14], fill=rgba(color, alpha), width=wd)


def icon_shield(d, cx, cy, s=64, color=INK, alpha=1.0):
    pts = [(cx, cy - s * 0.46), (cx + s * 0.38, cy - s * 0.30), (cx + s * 0.34, cy + s * 0.22), (cx, cy + s * 0.48), (cx - s * 0.34, cy + s * 0.22), (cx - s * 0.38, cy - s * 0.30)]
    d.polygon(pts, outline=rgba(color, alpha), width=max(3, int(s * 0.07)))
    d.line([cx - s * 0.15, cy + s * 0.02, cx - s * 0.02, cy + s * 0.16, cx + s * 0.20, cy - s * 0.12], fill=rgba(color, alpha), width=max(3, int(s * 0.07)), joint="curve")


def icon_server(d, cx, cy, s=64, color=INK, alpha=1.0):
    wd = max(3, int(s * 0.06))
    for i in (-1, 0, 1):
        y = cy + i * s * 0.28
        d.rounded_rectangle([cx - s * 0.42, y - s * 0.11, cx + s * 0.42, y + s * 0.11], radius=s * 0.08, outline=rgba(color, alpha), width=wd)
        d.ellipse([cx - s * 0.30, y - s * 0.035, cx - s * 0.23, y + s * 0.035], fill=rgba(color, alpha))


def icon_key(d, cx, cy, s=64, color=INK, alpha=1.0):
    wd = max(3, int(s * 0.08))
    d.ellipse([cx - s * 0.42, cy - s * 0.26, cx + s * 0.06, cy + s * 0.22], outline=rgba(color, alpha), width=wd)
    d.line([cx - s * 0.12, cy - s * 0.02, cx + s * 0.45, cy - s * 0.02], fill=rgba(color, alpha), width=wd)
    d.line([cx + s * 0.30, cy - s * 0.02, cx + s * 0.30, cy + s * 0.18], fill=rgba(color, alpha), width=wd)
    d.line([cx + s * 0.40, cy - s * 0.02, cx + s * 0.40, cy + s * 0.12], fill=rgba(color, alpha), width=wd)


def icon_check(d, cx, cy, s=56, color=GREEN, alpha=1.0, width=None):
    wd = width or max(4, int(s * 0.11))
    d.line([cx - s * 0.34, cy + s * 0.02, cx - s * 0.08, cy + s * 0.28, cx + s * 0.36, cy - s * 0.28], fill=rgba(color, alpha), width=wd, joint="curve")


def icon_cross(d, cx, cy, s=56, color=RED, alpha=1.0, width=None):
    wd = width or max(4, int(s * 0.11))
    d.line([cx - s * 0.28, cy - s * 0.28, cx + s * 0.28, cy + s * 0.28], fill=rgba(color, alpha), width=wd)
    d.line([cx + s * 0.28, cy - s * 0.28, cx - s * 0.28, cy + s * 0.28], fill=rgba(color, alpha), width=wd)


def cylinder(d, xy, w, h, fill=WHITE, border=LINE, alpha=1.0, top=0.18):
    x, y = xy
    d.ellipse([x, y, x + w, y + h * top * 2], fill=rgba(fill, alpha), outline=rgba(border, alpha), width=2)
    d.rectangle([x, y + h * top, x + w, y + h - h * top], fill=rgba(fill, alpha))
    d.line([x, y + h * top, x, y + h - h * top], fill=rgba(border, alpha), width=2)
    d.line([x + w, y + h * top, x + w, y + h - h * top], fill=rgba(border, alpha), width=2)
    d.arc([x, y + h - h * top * 2, x + w, y + h], 0, 180, fill=rgba(border, alpha), width=2)


def stamp(img, center, s, color=RED, size=48, angle=-8, alpha=1.0, weight="b"):
    f = font(size, weight)
    pad = 26
    tw = int(f.getlength(s)) + pad * 2
    th = size + pad
    tile = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile)
    td.rounded_rectangle([0, 0, tw - 1, th - 1], radius=16, outline=rgba(color, 1), width=4)
    td.text((tw / 2, th / 2), s, font=f, fill=rgba(color, 1), anchor="mm")
    tile = tile.rotate(angle, expand=True, resample=Image.BICUBIC)
    if alpha < 1:
        a = tile.getchannel("A").point(lambda v: int(v * alpha))
        tile.putalpha(a)
    img.paste(tile, (int(center[0] - tile.width / 2), int(center[1] - tile.height / 2)), tile)


KW = {"SET", "NX", "EX", "PX", "GET", "DEL", "SETNX", "EXPIRE", "if", "then", "end", "return", "local", "else", "and", "or", "not", "try", "finally", "new", "public", "private", "void", "long", "static", "class"}
CODE_TOKEN = re.compile(r"--[^\n]*|'[^']*'|\"[^\"]*\"|\b\d+\b|[A-Za-z_][A-Za-z0-9_.]*|\s+|.")


def code_tokens(line):
    out = []
    for tok in CODE_TOKEN.findall(line):
        if tok.startswith("--"):
            c = (100, 116, 139)
        elif tok.startswith(("'", '"')):
            c = (253, 186, 116)
        elif tok in KW:
            c = (147, 197, 253)
        elif tok == "redis.call":
            c = (196, 181, 253)
        elif tok.isdigit():
            c = (251, 191, 36)
        else:
            c = (226, 232, 240)
        out.append((tok, c))
    return out


def code_panel(d, xy, w, h, lines, title="redis-cli", alpha=1.0, size=30, highlight=None, line_gap=14, pad=28):
    x, y = xy
    shadow(d, [x, y, x + w, y + h], 18, NAVY, alpha=alpha, blur=14, offset=(0, 10))
    d.rounded_rectangle([x, y, x + w, y + h], radius=18, fill=rgba((15, 23, 42), alpha))
    d.rounded_rectangle([x, y, x + w, y + 54], radius=18, fill=rgba((30, 41, 59), alpha))
    d.rectangle([x, y + 40, x + w, y + 54], fill=rgba((30, 41, 59), alpha))
    for i, c in enumerate([(248, 113, 113), (251, 191, 36), (74, 222, 128)]):
        d.ellipse([x + 22 + i * 24, y + 20, x + 34 + i * 24, y + 32], fill=rgba(c, alpha))
    text(d, (x + w - 20, y + 27), title, 20, "r", MUTED, anchor="rm", alpha=alpha)
    f = font(size, "r", code=True)
    lh = size + line_gap
    cy = y + 80
    for i, line in enumerate(lines):
        if highlight and i in highlight:
            p = highlight[i] if isinstance(highlight, dict) else 1.0
            d.rounded_rectangle([x + 12, cy - 4, x + w - 12, cy + lh - 6], radius=8, fill=rgba((37, 99, 235), 0.16 * p * alpha))
        cx = x + pad
        for tok, col in code_tokens(line):
            d.text((cx, cy), tok, font=f, fill=rgba(col, alpha), anchor="la")
            cx += d.textlength(tok, font=f)
        cy += lh


def bg_image():
    yy = np.linspace(0, 1, H)[:, None]
    top = np.array(BG_TOP, dtype=np.float64)
    bot = np.array(BG_BOTTOM, dtype=np.float64)
    arr = top * (1 - yy) + bot * yy
    arr = np.repeat(arr[:, None, :], W, axis=1)
    # Soft glows in opposite corners.
    gy, gx = np.mgrid[0:H, 0:W]
    for (cx, cy, radius, color, strength) in [
        (W * 0.86, H * 0.10, 620, (37, 99, 235), 0.055),
        (W * 0.10, H * 0.92, 700, (124, 58, 237), 0.040),
    ]:
        dist = np.sqrt((gx - cx) ** 2 + (gy - cy) ** 2)
        glow = np.clip(1 - dist / radius, 0, 1) ** 2 * strength
        arr += np.array(color)[None, None, :] * glow[:, :, None]
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(img, "RGBA")
    step = 80
    for x in range(0, W + 1, step):
        major = (x % 400 == 0)
        d.line([x, 0, x, H], fill=rgba(GRID, 0.30 if major else 0.16), width=1)
    for y in range(0, H + 1, step):
        major = (y % 400 == 0)
        d.line([0, y, W, y], fill=rgba(GRID, 0.30 if major else 0.16), width=1)
    # Corner crop marks for a designed feel.
    d.line([70, 70, 106, 70], fill=rgba(FAINT, 0.55), width=2)
    d.line([70, 70, 70, 106], fill=rgba(FAINT, 0.55), width=2)
    d.line([W - 70, H - 70, W - 106, H - 70], fill=rgba(FAINT, 0.55), width=2)
    d.line([W - 70, H - 70, W - 70, H - 106], fill=rgba(FAINT, 0.55), width=2)
    return img


def chrome(d, chapter, series, idx, total_scenes):
    text(d, (110, 58), "●", 24, "r", BLUE, alpha=0.9)
    text(d, (134, 54), chapter, 25, "r", MUTED)
    text(d, (W - 110, 54), series, 25, "r", FAINT, anchor="ra")
    # A restrained progress indicator, bottom-right.
    x2 = W - 110
    for i in range(total_scenes):
        x = x2 - (total_scenes - 1 - i) * 16
        on = i <= idx
        d.ellipse([x - 4, H - 52, x + 4, H - 44], fill=rgba(BLUE if on else FAINT, 1 if on else 0.35))


def progress_bar(d, p):
    y = H - 18
    d.rounded_rectangle([110, y, W - 110, y + 4], radius=2, fill=rgba(LINE, 1))
    end = 110 + (W - 220) * clamp(p)
    if end > 112:
        d.rounded_rectangle([110, y, end, y + 4], radius=2, fill=rgba(BLUE, 0.9))
        d.ellipse([end - 7, y - 3, end + 7, y + 11], fill=rgba(BLUE, 1))
        d.ellipse([end - 3, y + 1, end + 3, y + 7], fill=rgba(WHITE, 1))


def subtitle(img, d, cue, local_t):
    if not cue:
        return
    a = clamp(min((local_t - cue["start"]) / 0.12, (cue["end"] - local_t) / 0.12))
    if a <= 0:
        return
    s = cue["text"].strip()
    f = font(34, "r")
    max_w = 1480
    lines = wrap(d, s, 34, "r", max_w)
    if len(lines) > 2:
        # Keep at most two balanced lines.
        mid = len(s) // 2
        lines = wrap(d, s[:mid], 34, "r", max_w) + wrap(d, s[mid:], 34, "r", max_w)
        lines = lines[:2]
    lh = 44
    tw = max(d.textlength(ln, font=f) for ln in lines)
    th = len(lines) * lh
    w = tw + 64
    h = th + 30
    cx = W / 2
    bottom = 1024
    top = bottom - h
    d.rounded_rectangle([cx - w / 2, top, cx + w / 2, bottom], radius=16, fill=rgba((15, 23, 42), 0.84 * a))
    for i, ln in enumerate(lines):
        d.text((cx, top + 15 + i * lh + lh / 2), ln, font=f, fill=rgba(WHITE, a), anchor="mm")
