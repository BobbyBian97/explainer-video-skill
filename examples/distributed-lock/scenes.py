# -*- coding: utf-8 -*-
"""Scene compositions for the distributed-lock explainer."""
import math

from PIL import ImageDraw

from graphics import (
    AMBER, AMBER_L, BLUE, BLUE_D, BLUE_L, FAINT, GREEN, GREEN_L, H, INK, LINE,
    MUTED, NAVY, PANEL, PURPLE, PURPLE_L, RED, RED_L, W, WHITE,
    arrow, card, chip, code_panel, curve_arrow, cylinder, icon_check, icon_clock,
    icon_cross, icon_key, icon_lock, icon_server, icon_shield, multiline, prog,
    stamp, text, textlen, wrap,
)


def beat(ctx, i, fallback=0.75):
    ss = ctx["sentences"]
    if i < len(ss):
        return ss[i]["start"] + ctx["shift"]
    return ctx["dur"] * fallback + ctx["shift"]


def scene_header(d, ctx, title, sub=None, t=0.0, start=0.35, color=INK, sub_color=MUTED):
    p = prog(t, start, 0.55)
    if p <= 0:
        return
    y = 118 - (1 - p) * 16
    text(d, (110, y), title, 54, "b", color, alpha=p)
    if sub:
        text(d, (114, y + 74), sub, 28, "r", sub_color, alpha=p)
    d.rounded_rectangle([112, y + 66, 112 + 74 * p, y + 70], radius=2, fill=(BLUE[0], BLUE[1], BLUE[2], int(220 * p)))


# ---------------------------------------------------------------- 00 hook
def s00(img, d, ctx, t):
    dur = ctx["dur"]
    p0 = prog(t, 0.10, 0.7)
    chip(d, (140, 238), "双十一 · 00:00", 25, BLUE_D, BLUE_L, alpha=p0, weight="b")
    y = 306 - (1 - p0) * 24
    text(d, (132, y), "分布式锁", 138, "b", INK, alpha=p0)
    p1 = prog(t, 0.55, 0.65)
    sub = "为什么 synchronized 锁不住你的集群？"
    lines = wrap(d, sub, 47, "b", 900)
    for i, ln in enumerate(lines):
        text(d, (142, 512 + i * 62 - (1 - p1) * 18), ln, 47, "b", (51, 65, 85), alpha=p1)
    p2 = prog(t, 0.9, 0.6)
    d.rounded_rectangle([142, 672, 142 + 210 * p2, 679], radius=3, fill=(BLUE[0], BLUE[1], BLUE[2], int(230 * p2)))
    text(d, (142, 714), "从超卖事故，到 Redisson 与 Redlock", 29, "r", MUTED, alpha=p2)
    text(d, (142, 766), "Redis 分布式锁 · 7 分钟讲透", 27, "r", FAINT, alpha=p2)

    # Inventory card
    pa = prog(t, 0.45, 0.6)
    if pa <= 0:
        return
    x, y0 = 1160, 238
    dy = (1 - pa) * 26
    card(img, d, (x, y0 + dy), 620, 520, 24, WHITE, LINE, alpha=pa, sh=True)
    text(d, (x + 40, y0 + 34 + dy), "实时库存", 27, "r", MUTED, alpha=pa)
    chip(d, (x + 40, y0 + 78 + dy), "order:1001", 23, MUTED, (241, 245, 249), alpha=pa, weight="r")
    # Counter
    start = beat(ctx, 0) + 0.55
    end = beat(ctx, 2) + 1.0
    pcount = max(0.0, min(1.0, (t - start) / max(0.1, end - start)))
    n = int(round(100 - 103 * pcount))
    color = RED if n < 0 else INK
    size = 132 if n >= 0 else 146
    text(d, (x + 310, y0 + 300 + dy), f"{n}", size, "b", color, anchor="mm", alpha=pa)
    text(d, (x + 450, y0 + 336 + dy), "件", 30, "r", MUTED, anchor="mm", alpha=pa)
    # Stock bar
    bw, bh = 500, 18
    bx, by = x + 60, y0 + 400 + dy
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=9, fill=(226, 232, 240, int(255 * pa)))
    fill = max(0, min(100, n)) / 100 * bw
    if fill > 0:
        d.rounded_rectangle([bx, by, bx + fill, by + bh], radius=9, fill=(37, 99, 235, int(255 * pa)))
    text(d, (bx, by + 40), f"已售 {max(0, 100 - n) if n >= 0 else 103}", 26, "r", MUTED, alpha=pa)
    text(d, (bx + bw, by + 40), f"剩余 {n}", 26, "r", RED if n < 0 else MUTED, anchor="rt", alpha=pa)
    if n <= -1:
        stamp(img, (x + 500, y0 + 112 + dy), "超卖", RED, 50, -9, alpha=pa)
    # Thin tick marks
    for i in range(11):
        tx = bx + i * bw / 10
        d.line([tx, by - 12, tx, by - 6], fill=(148, 163, 184, int(180 * pa)), width=2)


# ---------------------------------------------------------------- 01 single vs cluster
def s01(img, d, ctx, t):
    scene_header(d, ctx, "单机锁，锁不住两台机器", "synchronized 锁的是 JVM 内的对象", t)
    pL = prog(t, beat(ctx, 1), 0.6)
    pR = prog(t, beat(ctx, 3), 0.6)
    pBad = prog(t, beat(ctx, 4) + 0.1, 0.5)
    pNote = prog(t, beat(ctx, 5), 0.6)

    # Left: single JVM
    if pL > 0:
        card(img, d, (120, 258), 730, 540, 22, WHITE, LINE, alpha=pL)
        chip(d, (156, 292), "单体应用 · 1 个 JVM", 24, GREEN, GREEN_L, alpha=pL, weight="b")
        d.rounded_rectangle([156, 356, 814, 730], radius=20, outline=(22, 163, 74, int(120 * pL)), width=3, fill=(240, 253, 244, int(200 * pL)))
        text(d, (180, 372), "JVM", 24, "r", GREEN, alpha=pL, code=True)
        icon_lock(d, 250, 500, 80, GREEN, alpha=pL)
        text(d, (250, 570), "synchronized", 24, "r", GREEN, anchor="mt", alpha=pL, code=True)
        # threads
        for i, label in enumerate(["T1", "T2"]):
            ty = 450 + i * 130
            d.rounded_rectangle([336, ty, 436, ty + 66], radius=12, fill=(219, 234, 254, int(255 * pL)))
            text(d, (386, ty + 33), label, 26, "b", BLUE_D, anchor="mm", alpha=pL)
            arrow(d, (442, ty + 33), (520, ty + 33), GREEN, 3, 12, alpha=pL)
        d.rounded_rectangle([526, 430, 790, 646], radius=16, fill=(220, 252, 231, int(255 * pL)), outline=(22, 163, 74, int(160 * pL)), width=2)
        text(d, (658, 500), "临界区", 32, "b", GREEN, anchor="mm", alpha=pL)
        text(d, (658, 548), "同一时刻只进一个线程", 22, "r", (21, 128, 61), anchor="mm", alpha=pL)
        icon_check(d, 760, 690, 42, GREEN, alpha=pL)
        text(d, (786, 690), "没有超卖", 24, "r", GREEN, anchor="lm", alpha=pL)

    # Right: cluster
    if pR > 0:
        card(img, d, (1070, 258), 730, 540, 22, WHITE, LINE, alpha=pR)
        chip(d, (1106, 292), "集群部署 · 2 个 JVM", 24, RED, RED_L, alpha=pR, weight="b")
        # Load balancer
        cx, cy = 1435, 386
        d.ellipse([cx - 52, cy - 52, cx + 52, cy + 52], fill=(219, 234, 254, int(255 * pR)), outline=(37, 99, 235, int(180 * pR)), width=3)
        text(d, (cx, cy), "LB", 26, "b", BLUE_D, anchor="mm", alpha=pR)
        for dx in (-150, 150):
            arrow(d, (cx + dx * 0.28, cy + 38), (cx + dx * 0.72, cy + 92), BLUE, 3, 13, alpha=pR)
        for i, x in enumerate([1120, 1470]):
            d.rounded_rectangle([x, 476, x + 270, 700], radius=16, fill=(255, 251, 251, int(255 * pR)), outline=(248, 113, 113, int(120 * pR)), width=2)
            text(d, (x + 18, 490), f"JVM-{i + 1}", 22, "r", MUTED, alpha=pR, code=True)
            icon_lock(d, x + 56, 566, 52, RED, alpha=pR)
            text(d, (x + 92, 566), f"lock-{i + 1}", 22, "r", RED, anchor="lm", alpha=pR, code=True)
            text(d, (x + 20, 630), "stock 1 → 0", 24, "r", (51, 65, 85), alpha=pR)
        if pBad > 0:
            stamp(img, (1435, 700), "超卖 -1", RED, 40, -7, alpha=pBad)
    if pNote > 0:
        y = 826
        d.rounded_rectangle([110, y, 1810, y + 66], radius=16, fill=(239, 246, 255, int(255 * pNote)), outline=(191, 219, 254, int(255 * pNote)), width=2)
        text(d, (W / 2, y + 33), "锁的作用域 = 一个 JVM   ≠   整个集群", 30, "b", BLUE_D, anchor="mm", alpha=pNote)


# ---------------------------------------------------------------- 02 four rules
def s02(img, d, ctx, t):
    scene_header(d, ctx, "合格分布式锁的四个条件", "缺一不可，后面的演进都是补丁", t)
    items = [
        ("01", "互斥", "同一时刻，只能有一个\n客户端持有锁。", BLUE, BLUE_L, "lock"),
        ("02", "防死锁", "客户端宕机，锁必须能\n自动释放。", AMBER, AMBER_L, "clock"),
        ("03", "防误删", "只能释放自己加的那把锁。", PURPLE, PURPLE_L, "key"),
        ("04", "高可用", "锁服务挂了，业务不能\n跟着挂。", GREEN, GREEN_L, "server"),
    ]
    for i, (num, title, desc, col, col_l, ic) in enumerate(items):
        p = prog(t, beat(ctx, i + 1), 0.55)
        if p <= 0:
            continue
        x = 110 + i * 430
        y = 286 + (1 - p) * 24
        card(img, d, (x, y), 400, 452, 22, WHITE, LINE, alpha=p)
        text(d, (x + 30, y + 24), num, 26, "b", col, alpha=p, code=True)
        # icon plate
        d.rounded_rectangle([x + 30, y + 70, x + 118, y + 158], radius=20, fill=(*col_l, int(255 * p)))
        if ic == "lock":
            icon_lock(d, x + 74, y + 118, 54, col, alpha=p)
        elif ic == "clock":
            icon_clock(d, x + 74, y + 114, 52, col, alpha=p)
        elif ic == "key":
            icon_key(d, x + 74, y + 114, 52, col, alpha=p)
        else:
            icon_server(d, x + 74, y + 114, 52, col, alpha=p)
        text(d, (x + 30, y + 194), title, 42, "b", INK, alpha=p)
        for j, ln in enumerate(desc.split("\n")):
            text(d, (x + 30, y + 266 + j * 40), ln, 27, "r", MUTED, alpha=p)
    p = prog(t, beat(ctx, 5), 0.6)
    if p > 0:
        y = 794
        phrase = "互斥   ·   过期   ·   归属   ·   容灾"
        tw = textlen(d, phrase, 30, "b")
        d.rounded_rectangle([W / 2 - tw / 2 - 36, y, W / 2 + tw / 2 + 36, y + 62], radius=31, fill=(15, 23, 42, int(235 * p)))
        text(d, (W / 2, y + 31), phrase, 30, "b", WHITE, anchor="mm", alpha=p)


# ---------------------------------------------------------------- 03 SETNX
def s03(img, d, ctx, t):
    scene_header(d, ctx, "从 SETNX 到一条原子命令", "Redis 2.6.12+  ·  SET lock value NX EX 30", t)
    pR = prog(t, 0.6, 0.6)
    if pR > 0:
        cylinder(d, (150, 390), 250, 300, WHITE, (203, 213, 225), alpha=pR)
        text(d, (275, 520), "Redis", 34, "b", INK, anchor="mm", alpha=pR)
        text(d, (275, 566), "单线程执行命令", 21, "r", MUTED, anchor="mm", alpha=pR)
        d.rounded_rectangle([176, 660, 374, 716], radius=14, fill=(219, 234, 254, int(255 * pR)))
        text(d, (275, 688), "lock  →  order:1001", 22, "r", BLUE_D, anchor="mm", alpha=pR)

    # v1
    p1 = prog(t, 0.5, 0.55)
    if p1 > 0:
        y = 262
        card(img, d, (480, y), 1320, 258, 20, WHITE, LINE, alpha=p1)
        text(d, (512, y + 22), "v1 · 两条命令", 26, "b", MUTED, alpha=p1)
        code_panel(d, (512, y + 66), 690, 160, ["SETNX lock 1", "EXPIRE lock 30"], "redis-cli", alpha=p1, size=30, line_gap=16)
        pC = prog(t, beat(ctx, 2), 0.5)
        if pC > 0:
            icon_cross(d, 1240, y + 130, 46, RED, alpha=pC)
            text(d, (1276, y + 108), "中间宕机", 30, "b", RED, alpha=pC)
            text(d, (1276, y + 152), "只执行第一条 → 锁永不过期", 25, "r", RED, alpha=pC)

    # v2
    p2 = prog(t, beat(ctx, 3), 0.55)
    if p2 > 0:
        y = 558
        card(img, d, (480, y), 1320, 268, 20, (248, 250, 252), (191, 219, 254), alpha=p2)
        text(d, (512, y + 22), "v2 · 一条命令", 26, "b", BLUE_D, alpha=p2)
        code_panel(d, (512, y + 66), 690, 170, ["SET lock 8f3a NX EX 30"], "redis-cli", alpha=p2, size=31, line_gap=16, highlight={0: prog(t, beat(ctx, 4), 0.5)})
        pG = prog(t, beat(ctx, 4), 0.5)
        if pG > 0:
            icon_check(d, 1240, y + 130, 50, GREEN, alpha=pG)
            text(d, (1278, y + 108), "原子执行", 30, "b", GREEN, alpha=pG)
            text(d, (1278, y + 152), "NX 保互斥  ·  EX 防死锁", 25, "r", (21, 128, 61), alpha=pG)


# ---------------------------------------------------------------- 04 wrong delete
def s04(img, d, ctx, t):
    scene_header(d, ctx, "锁为什么会误删？", "TTL 到期后，A 删掉了 B 的锁", t)
    pA = prog(t, 0.5, 0.55)
    pTTL = prog(t, beat(ctx, 2), 0.5)
    pB = prog(t, beat(ctx, 2), 0.5)
    pDel = prog(t, beat(ctx, 3), 0.45)
    pUuid = prog(t, beat(ctx, 4), 0.55)
    pLua = prog(t, beat(ctx, 6), 0.55)

    x0, x1 = 160, 1760
    axis_y = 500
    tmax = 40.0

    def X(sec):
        return x0 + (x1 - x0) * (sec / tmax)

    if pA > 0:
        d.line([x0, axis_y, x0 + (x1 - x0) * pA, axis_y], fill=(148, 163, 184, int(255 * pA)), width=3)
        for sec in (0, 10, 20, 30, 40):
            xx = X(sec)
            d.line([xx, axis_y - 7, xx, axis_y + 7], fill=(148, 163, 184, int(220 * pA)), width=2)
            text(d, (xx, axis_y + 18), f"{sec}s", 21, "r", FAINT, anchor="mt", alpha=pA, code=True)
        # A bar
        ax2 = X(35 * pA)
        d.rounded_rectangle([X(0), 380, ax2, 444], radius=14, fill=(37, 99, 235, int(235 * pA)))
        text(d, (X(1.2), 412), "A 执行业务 · 35s", 25, "r", WHITE, anchor="lm", alpha=pA)
        icon_lock(d, X(2.6), 336, 48, BLUE, alpha=pA)
        text(d, (X(2.6) + 34, 336), "A 持锁", 23, "r", BLUE, anchor="lm", alpha=pA)

    if pTTL > 0:
        xx = X(30)
        d.line([xx, 270, xx, axis_y], fill=(220, 38, 38, int(220 * pTTL)), width=3)
        d.rounded_rectangle([xx - 84, 218, xx + 84, 264], radius=12, fill=(254, 226, 226, int(255 * pTTL)))
        text(d, (xx, 241), "TTL 30s 到期", 22, "b", RED, anchor="mm", alpha=pTTL)

    if pB > 0:
        bx1 = X(30)
        bx2 = X(30 + 10 * pB)
        d.rounded_rectangle([bx1, 286, bx2, 350], radius=14, fill=(124, 58, 237, int(235 * pB)))
        text(d, (bx1 + 14, 318), "B 拿到锁", 25, "r", WHITE, anchor="lm", alpha=pB)
        icon_lock(d, X(36), 388, 40, PURPLE, alpha=pB)

    if pDel > 0:
        # A wakes up and deletes B's lock.
        arrow(d, (X(35), 430), (X(37), 356), RED, 4, 16, alpha=pDel)
        icon_cross(d, X(37.2), 350, 38, RED, alpha=pDel)
        d.rounded_rectangle([X(37.0) - 110, 384, X(37.0) + 150, 440], radius=12, fill=(254, 226, 226, int(240 * pDel)))
        text(d, (X(37.0) + 20, 412), "A 执行 DEL，删了 B 的锁", 21, "b", RED, anchor="mm", alpha=pDel)

    # UUID cards
    if pUuid > 0:
        uy = 600
        d.rounded_rectangle([150, uy, 470, uy + 128], radius=16, fill=(239, 246, 255, int(255 * pUuid)), outline=(191, 219, 254, int(255 * pUuid)), width=2)
        text(d, (174, uy + 22), "A 的 value", 21, "r", MUTED, alpha=pUuid)
        text(d, (174, uy + 58), "8f3a", 38, "b", BLUE_D, alpha=pUuid, code=True)
        d.rounded_rectangle([492, uy, 812, uy + 128], radius=16, fill=(250, 245, 255, int(255 * pUuid)), outline=(221, 214, 254, int(255 * pUuid)), width=2)
        text(d, (516, uy + 22), "B 的 value", 21, "r", MUTED, alpha=pUuid)
        text(d, (516, uy + 58), "2c91", 38, "b", PURPLE, alpha=pUuid, code=True)
    # Lua panel
    if pLua > 0:
        code_panel(
            d, (860, 590), 950, 288,
            [
                "if redis.call('GET', KEYS[1]) == ARGV[1] then",
                "    return redis.call('DEL', KEYS[1])",
                "end",
            ],
            "Lua · 比较 + 删除 = 原子", alpha=pLua, size=26, line_gap=18,
        )
        text(d, (884, 846), "只删除 value 等于自己的锁", 23, "r", GREEN, alpha=pLua)


# ---------------------------------------------------------------- 05 watchdog
def s05(img, d, ctx, t):
    scene_header(d, ctx, "Redisson：看门狗与可重入", "TTL 30s，每 10s 自动续期", t)
    pL = prog(t, beat(ctx, 1), 0.55)
    pW = prog(t, beat(ctx, 2), 0.55)
    pR = prog(t, beat(ctx, 3), 0.55)

    if pL > 0:
        card(img, d, (120, 258), 780, 600, 22, WHITE, LINE, alpha=pL)
        chip(d, (156, 292), "看门狗 Watch Dog", 24, BLUE_D, BLUE_L, alpha=pL, weight="b")
        # lock card
        d.rounded_rectangle([250, 360, 740, 520], radius=22, fill=(248, 250, 252, int(255 * pL)), outline=(191, 219, 254, int(255 * pL)), width=2)
        icon_lock(d, 316, 440, 72, BLUE, alpha=pL)
        text(d, (380, 404), "lock:order:1001", 23, "r", MUTED, alpha=pL, code=True)
        text(d, (380, 442), "TTL = 30s", 38, "b", INK, alpha=pL)
        # circular renewal arrow
        if pW > 0:
            d.arc([232, 336, 758, 548], 205, 335, fill=(37, 99, 235, int(235 * pW)), width=5)
            # arrow head at the arc end
            ang = math.radians(335)
            cx, cy = 495, 442
            ex, ey = cx + 263 * math.cos(ang), cy + 106 * math.sin(ang)
            arrow(d, (ex - 10, ey - 14), (ex + 10, ey + 2), BLUE, 4, 14, alpha=pW)
            chip(d, (492, 322), "每 10s 续期一次", 23, BLUE_D, (239, 246, 255), alpha=pW, weight="b", anchor="mm")
        # timeline
        ty = 620
        d.line([190, ty, 830, ty], fill=(203, 213, 225, int(255 * pL)), width=3)
        for sec in (0, 10, 20, 30, 40, 50):
            xx = 190 + (830 - 190) * sec / 50
            d.line([xx, ty - 7, xx, ty + 7], fill=(148, 163, 184, int(255 * pL)), width=2)
            text(d, (xx, ty + 16), f"{sec}s", 19, "r", FAINT, anchor="mt", alpha=pL, code=True)
        for sec in (0, 10, 20, 30, 40):
            xx = 190 + (830 - 190) * sec / 50
            d.ellipse([xx - 7, ty - 7, xx + 7, ty + 7], fill=(37, 99, 235, int(255 * pW)))
        text(d, (510, ty + 56), "只要进程活着，锁就不会过期", 24, "r", MUTED, anchor="mt", alpha=pW)
        d.rounded_rectangle([190, 720, 560, 778], radius=14, fill=(254, 243, 199, int(255 * pW)))
        text(d, (375, 749), "续期间隔 = TTL / 3", 25, "b", AMBER, anchor="mm", alpha=pW)

    if pR > 0:
        card(img, d, (960, 258), 840, 600, 22, WHITE, LINE, alpha=pR)
        chip(d, (996, 292), "可重入 Reentrant", 24, PURPLE, PURPLE_L, alpha=pR, weight="b")
        text(d, (996, 348), "同一个线程可以重复加锁", 25, "r", MUTED, alpha=pR)
        # Hash table
        hx, hy, hw = 996, 402, 768
        d.rounded_rectangle([hx, hy, hx + hw, hy + 210], radius=16, fill=(250, 245, 255, int(255 * pR)), outline=(221, 214, 254, int(255 * pR)), width=2)
        text(d, (hx + 24, hy + 20), "lock:order:1001", 23, "r", PURPLE, alpha=pR, code=True)
        d.line([hx, hy + 64, hx + hw, hy + 64], fill=(221, 214, 254, int(200 * pR)), width=2)
        text(d, (hx + 24, hy + 84), "thread-7", 22, "r", MUTED, alpha=pR, code=True)
        text(d, (hx + 380, hy + 84), "count = 2", 26, "b", INK, alpha=pR)
        text(d, (hx + 24, hy + 148), "thread-9", 22, "r", MUTED, alpha=pR, code=True)
        text(d, (hx + 380, hy + 148), "count = 1", 26, "b", INK, alpha=pR)
        # reentrant sequence
        seq = ["lock()", "lock()", "unlock()", "unlock()"]
        counts = ["1", "2", "1", "0"]
        for i, (s, c) in enumerate(zip(seq, counts)):
            bx = 996 + i * 192
            by = 660
            col = BLUE if s.startswith("lock") else PURPLE
            d.rounded_rectangle([bx, by, bx + 168, by + 58], radius=12, fill=(*((219, 234, 254) if s.startswith("lock") else (237, 233, 254)), int(255 * pR)))
            text(d, (bx + 84, by + 29), s, 21, "r", col, anchor="mm", alpha=pR, code=True)
            text(d, (bx + 84, by + 82), f"count={c}", 22, "b", INK, anchor="mm", alpha=pR)
            if i < 3:
                arrow(d, (bx + 168, by + 29), (bx + 190, by + 29), FAINT, 2, 9, alpha=pR)
        text(d, (1380, 806), "计数归零，才真正释放锁", 22, "r", MUTED, anchor="mm", alpha=pR)


# ---------------------------------------------------------------- 05b Redisson code
def s05b(img, d, ctx, t):
    scene_header(d, ctx, "Redisson 实战：三行代码", "getLock → lock → finally unlock", t)
    pCode = prog(t, beat(ctx, 0), 0.55)
    pFlow = prog(t, beat(ctx, 1), 0.55)
    pWarn = prog(t, beat(ctx, 3), 0.5)
    pTry = prog(t, beat(ctx, 4), 0.5)
    pPub = prog(t, beat(ctx, 5), 0.5)

    if pCode > 0:
        code_panel(
            d, (130, 282), 910, 440,
            [
                'RLock lock = redisson.getLock("order:" + id);',
                "lock.lock();",
                "try {",
                "    stockService.deduct(id);",
                "} finally {",
                "    lock.unlock();",
                "}",
            ],
            "OrderService.java", alpha=pCode, size=27, line_gap=16,
            highlight={1: prog(t, beat(ctx, 2), 0.5), 5: prog(t, beat(ctx, 2) + 0.3, 0.5)},
        )

    if pFlow > 0:
        card(img, d, (1090, 282), 720, 520, 22, WHITE, LINE, alpha=pFlow)
        text(d, (1122, 308), "一次 lock() 背后发生了什么", 26, "b", MUTED, alpha=pFlow)
        steps = [
            ("1", "getLock(order:1001)", "拿到 RLock 对象", BLUE),
            ("2", "lock()", "尝试加锁，失败则等待", PURPLE),
            ("3", "SET order:1001 <uuid> NX EX 30", "Redis 原子写入", RED),
            ("4", "看门狗每 10s 续期", "不传 leaseTime 才生效", GREEN),
        ]
        for i, (n, title, sub, col) in enumerate(steps):
            y = 360 + i * 104 - (1 - pFlow) * 12
            d.ellipse([1122, y, 1170, y + 48], fill=(*col, int(235 * pFlow)))
            text(d, (1146, y + 24), n, 20, "b", WHITE, anchor="mm", alpha=pFlow, code=True)
            text(d, (1184, y + 8), title, 22, "r", INK, alpha=pFlow)
            text(d, (1184, y + 38), sub, 20, "r", MUTED, alpha=pFlow)
        if pWarn > 0:
            d.rounded_rectangle([1122, 742, 1780, 790], radius=12, fill=(254, 243, 199, int(250 * pWarn)))
            text(d, (1451, 766), "传了 leaseTime → 看门狗不生效", 21, "b", AMBER, anchor="mm", alpha=pWarn)

    if pTry > 0:
        d.rounded_rectangle([130, 760, 1000, 820], radius=14, fill=(239, 246, 255, int(255 * pTry)), outline=(191, 219, 254, int(255 * pTry)), width=2)
        text(d, (154, 790), "tryLock(waitTime, leaseTime, unit)：拿不到就快速失败", 22, "r", BLUE_D, anchor="lm", alpha=pTry)

    if pPub > 0:
        d.rounded_rectangle([130, 838, 1810, 896], radius=14, fill=(250, 245, 255, int(255 * pPub)), outline=(221, 214, 254, int(255 * pPub)), width=2)
        text(d, (W / 2, 867), "等待线程不空转：订阅解锁消息，锁释放时被唤醒", 23, "b", PURPLE, anchor="mm", alpha=pPub)


# ---------------------------------------------------------------- 06b selection
def s06b(img, d, ctx, t):
    scene_header(d, ctx, "怎么选？四种方案对比", "没有银弹，只有取舍", t)
    xs = [130, 470, 830, 1120]
    headers = ["方案", "一致性", "性能", "适用场景"]
    widths = [340, 360, 290, 690]
    pHead = prog(t, 0.35, 0.5)
    if pHead > 0:
        for x, hd, wd in zip(xs, headers, widths):
            text(d, (x + 6, 270), hd, 23, "b", MUTED, alpha=pHead)
        d.line([130, 310, 1810, 310], fill=(203, 213, 225, int(220 * pHead)), width=2)
    rows = [
        ("Redis", "最终一致 · 主从异步", "极高", "缓存型业务，允许极低概率重复", RED, RED_L),
        ("ZooKeeper", "强一致 · ZAB", "中等", "金融级，对正确性要求极高", BLUE, BLUE_L),
        ("etcd", "强一致 · Raft", "较高", "云原生，配置 / 服务发现同栈", PURPLE, PURPLE_L),
        ("数据库", "强一致 · 事务 / 唯一索引", "较低", "并发不高，冲突可预期", GREEN, GREEN_L),
    ]
    for i, (name, cons, perf, fit, col, col_l) in enumerate(rows):
        p = prog(t, beat(ctx, i + 1), 0.5)
        if p <= 0:
            continue
        y = 330 + i * 112 - (1 - p) * 12
        d.rounded_rectangle([130, y, 1810, y + 96], radius=16, fill=(255, 255, 255, int(245 * p)), outline=(226, 232, 240, int(255 * p)), width=2)
        d.rounded_rectangle([148, y + 20, 300, y + 76], radius=12, fill=(*col_l, int(255 * p)))
        text(d, (224, y + 48), name, 25, "b", col, anchor="mm", alpha=p)
        text(d, (476, y + 34), cons, 23, "r", INK, alpha=p)
        text(d, (836, y + 34), perf, 23, "r", INK, alpha=p)
        text(d, (1126, y + 34), fit, 23, "r", (51, 65, 85), alpha=p)
        if i < 3:
            d.line([148, y + 98, 1792, y + 98], fill=(241, 245, 249, int(255 * p)), width=1)
    p = prog(t, beat(ctx, 5), 0.55)
    if p > 0:
        phrase = "能用数据库约束解决的，别急着上分布式锁。"
        tw = textlen(d, phrase, 30, "b")
        d.rounded_rectangle([W / 2 - tw / 2 - 38, 810, W / 2 + tw / 2 + 38, 872], radius=31, fill=(15, 23, 42, int(235 * p)))
        text(d, (W / 2, 841), phrase, 30, "b", WHITE, anchor="mm", alpha=p)


# ---------------------------------------------------------------- 06 Redlock
def s06(img, d, ctx, t):
    scene_header(d, ctx, "主从切换，锁会丢吗？", "异步复制留下的时间窗", t)
    pL = prog(t, 0.6, 0.55)
    pR = prog(t, beat(ctx, 2), 0.55)
    pV = prog(t, beat(ctx, 4), 0.55)

    if pL > 0:
        card(img, d, (120, 258), 880, 600, 22, WHITE, LINE, alpha=pL)
        chip(d, (156, 292), "Redis 主从 · 异步复制", 24, RED, RED_L, alpha=pL, weight="b")
        # master
        d.rounded_rectangle([190, 352, 510, 470], radius=16, fill=(255, 251, 251, int(255 * pL)), outline=(248, 113, 113, int(180 * pL)), width=2)
        text(d, (214, 372), "Master", 26, "b", INK, alpha=pL, code=True)
        icon_lock(d, 260, 424, 38, RED, alpha=pL)
        text(d, (290, 424), "lock 已写入", 22, "r", RED, anchor="lm", alpha=pL)
        # replica
        d.rounded_rectangle([190, 556, 510, 674], radius=16, fill=(240, 253, 244, int(255 * pL)), outline=(134, 239, 172, int(200 * pL)), width=2)
        text(d, (214, 576), "Replica", 26, "b", INK, alpha=pL, code=True)
        text(d, (214, 624), "升主 → 可以再次加锁", 22, "r", GREEN, alpha=pL)
        # replication arrow
        arrow(d, (350, 476), (350, 548), MUTED, 3, 12, alpha=pL, dashed=True)
        pX = prog(t, beat(ctx, 1) + 0.4, 0.45)
        if pX > 0:
            icon_cross(d, 350, 512, 34, RED, alpha=pX)
            text(d, (380, 512), "未同步", 21, "b", RED, anchor="lm", alpha=pX)
        # client B
        pB = prog(t, beat(ctx, 1), 0.5)
        if pB > 0:
            d.rounded_rectangle([620, 556, 890, 674], radius=16, fill=(250, 245, 255, int(255 * pB)), outline=(221, 214, 254, int(255 * pB)), width=2)
            text(d, (644, 576), "Client B", 24, "b", PURPLE, alpha=pB, code=True)
            text(d, (644, 624), "也拿到了 lock", 22, "r", PURPLE, alpha=pB)
            arrow(d, (516, 610), (608, 610), PURPLE, 3, 12, alpha=pB)
            d.rounded_rectangle([190, 712, 810, 774], radius=14, fill=(254, 226, 226, int(245 * pB)))
            text(d, (500, 743), "两个客户端同时持锁 = 互斥失效", 24, "b", RED, anchor="mm", alpha=pB)

    if pR > 0:
        card(img, d, (1040, 258), 760, 600, 22, WHITE, LINE, alpha=pR)
        chip(d, (1076, 292), "Redlock · 多数派", 24, BLUE_D, BLUE_L, alpha=pR, weight="b")
        nodes = [(1100, 372), (1230, 372), (1360, 372), (1490, 372), (1620, 372)]
        for i, (nx, ny) in enumerate(nodes):
            ok = i < 3
            col, bg = (GREEN, (240, 253, 244)) if ok else (FAINT, (248, 250, 252))
            d.rounded_rectangle([nx, ny, nx + 88, ny + 96], radius=14, fill=(*bg, int(255 * pR)), outline=(*col, int(220 * pR)), width=2)
            icon_server(d, nx + 44, ny + 40, 32, col, alpha=pR)
            text(d, (nx + 44, ny + 78), f"R{i + 1}", 18, "r", col, anchor="mm", alpha=pR, code=True)
        text(d, (1400, 504), "3 / 5 成功 → 加锁成功", 30, "b", GREEN, anchor="mm", alpha=pR)
        # verdicts
        vy = 566
        d.rounded_rectangle([1076, vy, 1764, vy + 100], radius=16, fill=(240, 253, 244, int(255 * pV)), outline=(134, 239, 172, int(220 * pV)), width=2)
        text(d, (1100, vy + 20), "强一致", 22, "b", GREEN, alpha=pV)
        text(d, (1100, vy + 50), "→ ZooKeeper / etcd", 24, "r", (21, 128, 61), alpha=pV)
        d.rounded_rectangle([1076, vy + 118, 1764, vy + 218], radius=16, fill=(255, 251, 235, int(255 * pV)), outline=(253, 230, 138, int(240 * pV)), width=2)
        text(d, (1100, vy + 138), "可接受极小概率", 22, "b", AMBER, alpha=pV)
        text(d, (1100, vy + 168), "→ Redis + 幂等兜底", 24, "r", (146, 64, 14), alpha=pV)
        text(d, (1420, 832), "取舍，不是站队", 22, "r", MUTED, anchor="mm", alpha=pV)


# ---------------------------------------------------------------- 07 production
def s07(img, d, ctx, t):
    scene_header(d, ctx, "生产落地的 5 件事", "锁是优化，幂等才是底线", t)
    rows = [
        ("01", "锁粒度", "按订单号 / 用户 ID 加锁，别一把大锁锁全表。", BLUE),
        ("02", "超时设置", "按业务 P99 评估，不能拍脑袋。", PURPLE),
        ("03", "幂等兜底", "锁不是正确性的唯一保障。", GREEN),
        ("04", "降级策略", "重试、排队，还是快速失败？", AMBER),
        ("05", "监控告警", "锁等待时间、获取失败率。", RED),
    ]
    for i, (num, title, desc, col) in enumerate(rows):
        p = prog(t, beat(ctx, i + 1), 0.5)
        if p <= 0:
            continue
        y = 258 + i * 118 - (1 - p) * 14
        d.rounded_rectangle([130, y, 1320, y + 96], radius=18, fill=(255, 255, 255, int(245 * p)), outline=(226, 232, 240, int(255 * p)), width=2)
        d.ellipse([154, y + 22, 206, y + 74], fill=(*col, int(235 * p)))
        text(d, (180, y + 48), num, 20, "b", WHITE, anchor="mm", alpha=p, code=True)
        text(d, (230, y + 48), title, 32, "b", INK, anchor="lm", alpha=p)
        text(d, (410, y + 49), desc, 25, "r", MUTED, anchor="lm", alpha=p)

    p = prog(t, beat(ctx, 3), 0.55)
    if p > 0:
        card(img, d, (1370, 310), 430, 470, 22, (248, 250, 252), LINE, alpha=p)
        text(d, (1400, 338), "更简单的替代", 26, "b", MUTED, alpha=p)
        items = [("唯一索引", icon_key, BLUE), ("乐观锁", icon_check, GREEN), ("状态机", icon_shield, PURPLE)]
        for i, (name, ic, col) in enumerate(items):
            y = 410 + i * 112
            d.rounded_rectangle([1400, y, 1770, y + 88], radius=14, fill=(255, 255, 255, int(255 * p)), outline=(226, 232, 240, int(255 * p)), width=2)
            ic(d, 1446, y + 44, 40, col, alpha=p)
            text(d, (1496, y + 44), name, 27, "b", INK, anchor="lm", alpha=p)
        text(d, (1585, 760), "先问：真的需要分布式锁吗？", 22, "r", MUTED, anchor="mm", alpha=p)


# ---------------------------------------------------------------- 08 interview
def s08(img, d, ctx, t):
    scene_header(d, ctx, "面试怎么答？三步就够", "结论 → 演进 → 边界", t)
    cols = [
        ("1", "先给结论", ["多进程互斥机制", "SET NX EX 加锁", "UUID 标识归属", "Lua 原子释放", "Redisson 续期 + 可重入"], BLUE, BLUE_L),
        ("2", "再讲演进", ["SETNX + EXPIRE 非原子", "→ SET NX EX 一条命令", "→ 误删：UUID + Lua", "→ 续期：看门狗"], PURPLE, PURPLE_L),
        ("3", "最后补边界", ["主从切换丢锁", "Redlock 的争议", "强一致选 ZK / etcd", "幂等兜底"], GREEN, GREEN_L),
    ]
    for i, (num, title, bullets, col, col_l) in enumerate(cols):
        p = prog(t, beat(ctx, [1, 3, 4][i]), 0.55)
        if p <= 0:
            continue
        x = 110 + i * 590
        y = 272 + (1 - p) * 22
        card(img, d, (x, y), 550, 480, 22, WHITE, LINE, alpha=p)
        d.ellipse([x + 28, y + 26, x + 88, y + 86], fill=(*col, int(240 * p)))
        text(d, (x + 58, y + 56), num, 27, "b", WHITE, anchor="mm", alpha=p, code=True)
        text(d, (x + 108, y + 56), title, 34, "b", INK, anchor="lm", alpha=p)
        for j, b in enumerate(bullets):
            by = y + 130 + j * 58
            d.ellipse([x + 32, by + 18, x + 42, by + 28], fill=(*col, int(220 * p)))
            lines = wrap(d, b, 25, "r", 466)
            for k, ln in enumerate(lines[:2]):
                text(d, (x + 56, by + k * 32), ln, 25, "r", (51, 65, 85), alpha=p)
    p = prog(t, beat(ctx, 5), 0.55)
    if p > 0:
        phrase = "30 秒答完 · 比背八股高一个层次"
        tw = textlen(d, phrase, 28, "b")
        d.rounded_rectangle([W / 2 - tw / 2 - 34, 804, W / 2 + tw / 2 + 34, 864], radius=30, fill=(15, 23, 42, int(235 * p)))
        text(d, (W / 2, 834), phrase, 28, "b", WHITE, anchor="mm", alpha=p)


# ---------------------------------------------------------------- 09 outro
def s09(img, d, ctx, t):
    p0 = prog(t, 0.15, 0.6)
    text(d, (W / 2, 210 - (1 - p0) * 18), "记住这四句", 70, "b", INK, anchor="mm", alpha=p0)
    text(d, (W / 2, 292), "面试答题时，一句一句往外抛", 28, "r", MUTED, anchor="mm", alpha=p0)
    items = [
        ("加锁要原子", "SET NX EX", BLUE, BLUE_L),
        ("过期要续期", "Watch Dog", PURPLE, PURPLE_L),
        ("释放要校验", "UUID + Lua", AMBER, AMBER_L),
        ("失败要幂等", "Idempotent", GREEN, GREEN_L),
    ]
    for i, (title, sub, col, col_l) in enumerate(items):
        p = prog(t, 0.5 + i * 0.38, 0.55)
        if p <= 0:
            continue
        x = 110 + i * 430
        y = 360 + (1 - p) * 22
        card(img, d, (x, y), 400, 280, 22, WHITE, LINE, alpha=p)
        d.rounded_rectangle([x + 30, y + 32, x + 370, y + 40], radius=4, fill=(*col, int(230 * p)))
        text(d, (x + 200, y + 104), title, 42, "b", INK, anchor="mm", alpha=p)
        text(d, (x + 200, y + 178), sub, 24, "r", col, anchor="mm", alpha=p, code=True)
    p2 = prog(t, beat(ctx, 1), 0.6)
    if p2 > 0:
        text(d, (W / 2, 742), "分布式锁不是银弹，想清楚边界，再用它。", 44, "b", INK, anchor="mm", alpha=p2)
        line_w = 260 * p2
        d.rounded_rectangle([W / 2 - line_w, 792, W / 2 + line_w, 797], radius=3, fill=(37, 99, 235, int(200 * p2)))
        text(d, (W / 2, 852), "Redis 分布式锁 · 从原理到落地", 26, "r", MUTED, anchor="mm", alpha=p2)
        text(d, (W / 2, 900), "点赞 · 收藏 · 关注，我们下期见", 24, "r", FAINT, anchor="mm", alpha=p2)


SCENES = {
    "hook": s00,
    "single_vs_cluster": s01,
    "four_rules": s02,
    "setnx": s03,
    "wrong_delete": s04,
    "watchdog": s05,
    "redisson": s05b,
    "redlock": s06,
    "selection": s06b,
    "production": s07,
    "interview": s08,
    "outro": s09,
}
