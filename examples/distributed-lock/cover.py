# -*- coding: utf-8 -*-
"""Cover design for the distributed-lock example (Bilibili 16:9 / 16:10)."""
import numpy as np
from PIL import Image, ImageDraw

import graphics as g
from graphics import (
    BLUE, BLUE_D, BLUE_L, FAINT, GRID, INK, LINE, MUTED, RED, RED_L, WHITE,
    card, chip, stamp, text,
)

CHIPS = ["SET NX EX", "UUID + Lua", "Redisson 看门狗"]


def cover_bg(w, h):
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
        d.line([x, 0, x, h], fill=g.rgba(GRID, 0.30 if major else 0.16), width=1)
    for y in range(0, h + 1, 80):
        major = (y % 400 == 0)
        d.line([0, y, w, y], fill=g.rgba(GRID, 0.30 if major else 0.16), width=1)
    return img


def render(w, h):
    off = (h - 1080) / 2
    img = cover_bg(w, h)
    d = ImageDraw.Draw(img, "RGBA")

    text(d, (120, 78 + off), "●", 26, "r", BLUE, alpha=0.9)
    text(d, (146, 74 + off), "Redis 分布式锁 · 7 分钟讲透", 27, "r", MUTED)
    text(d, (w - 120, 74 + off), "原理 → 坑 → 实战 → 选型", 27, "r", FAINT, anchor="ra")

    chip(d, (128, 196 + off), "双十一 · 超卖事故", 25, RED, RED_L, weight="b")
    text(d, (120, 258 + off), "分布式锁", 164, "b", INK)
    text(d, (128, 482 + off), "为什么 synchronized", 54, "b", (51, 65, 85))
    text(d, (128, 554 + off), "锁不住你的集群？", 54, "b", (51, 65, 85))
    d.rounded_rectangle([128, 650 + off, 128 + 220, 657 + off], radius=3, fill=g.rgba(BLUE, 0.9))
    text(d, (128, 686 + off), "从超卖事故，到 Redisson 与 Redlock", 30, "r", MUTED)

    cx = 128
    for s in CHIPS:
        cw, ch = chip(d, (cx, 760 + off), s, 26, BLUE_D, BLUE_L, weight="b")
        cx += cw + 16

    x, y0 = 1152, 196 + off
    card(img, d, (x, y0), 648, 700, 26, WHITE, LINE, sh=True)
    text(d, (x + 44, y0 + 38), "实时库存", 28, "r", MUTED)
    chip(d, (x + 44, y0 + 84), "order:1001", 23, MUTED, (241, 245, 249))
    stamp(img, (x + 512, y0 + 118), "超卖", RED, 54, -9)
    text(d, (x + 324, y0 + 306), "-3", 176, "b", RED, anchor="mm")
    text(d, (x + 470, y0 + 350), "件", 32, "r", MUTED, anchor="mm")
    bx, by, bw, bh = x + 60, y0 + 448, 528, 20
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=10, fill=(226, 232, 240, 255))
    text(d, (bx, by + 46), "已售 103", 27, "r", MUTED)
    text(d, (bx + bw, by + 46), "剩余 -3", 27, "r", RED, anchor="rt")
    text(d, (x + 324, y0 + 596), "锁失效，库存被重复扣减", 27, "r", (185, 28, 28), anchor="mm")

    pill_w, pill_h = 560, 74
    px, py = w - 120 - pill_w, h - 96 - pill_h
    d.rounded_rectangle([px, py, px + pill_w, py + pill_h], radius=18, fill=g.rgba((15, 23, 42), 1))
    text(d, (px + 28, py + pill_h / 2), "SET lock 8f3a NX EX 30", 28, "r", (226, 232, 240), anchor="lm", code=True)
    return img
