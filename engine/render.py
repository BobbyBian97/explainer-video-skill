# -*- coding: utf-8 -*-
"""Render an explainer-video project to MP4.

Usage:
    python engine/render.py --project examples/distributed-lock --times 20,180
    python engine/render.py --project examples/distributed-lock --seconds 30
    python engine/render.py --project examples/distributed-lock

The project directory must contain scenes.py exposing SCENES = {"visual": fn}
and an out/timeline.json produced by engine/build.py.
"""
import argparse
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

import imageio_ffmpeg
from PIL import ImageDraw

ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(ENGINE))

import graphics  # noqa: E402
from graphics import H, W, chrome, progress_bar, subtitle  # noqa: E402

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def load_scenes(project: Path):
    path = project / "scenes.py"
    if not path.exists():
        raise SystemExit(f"scenes.py not found in {project}")
    if str(ENGINE) not in sys.path:
        sys.path.insert(0, str(ENGINE))
    spec = importlib.util.spec_from_file_location("project_scenes", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["project_scenes"] = mod
    spec.loader.exec_module(mod)
    if not hasattr(mod, "SCENES"):
        raise SystemExit("scenes.py must define SCENES = {'visual_name': draw_fn}")
    return mod.SCENES


def load_timeline(project: Path):
    path = project / "out" / "timeline.json"
    if not path.exists():
        raise SystemExit(f"timeline not found: {path} (run engine/build.py first)")
    return json.loads(path.read_text(encoding="utf-8"))


def scene_ctx(scene, idx):
    # Scene 0 animates during the pre-roll lead; its beats are absolute audio times.
    active_start = 0.0 if idx == 0 else float(scene["start"])
    return {
        "dur": float(scene["dur"]),
        "shift": float(scene["start"]) - active_start,
        "sentences": scene["sentences"],
        "cues": scene["cues"],
        "scene": scene,
    }


def active_scene(tl, t):
    idx = 0
    for i, s in enumerate(tl["scenes"]):
        if t >= s["start"] - 0.001:
            idx = i
        else:
            break
    return idx


def current_cue(scene, t):
    if t < scene["start"]:
        return None
    lt = t - scene["start"]
    for c in scene["cues"]:
        if c["start"] - 0.001 <= lt <= c["end"]:
            return c
    return None


def render_frame(tl, bg, scenes, t):
    idx = active_scene(tl, t)
    scene = tl["scenes"][idx]
    img = bg.copy()
    d = ImageDraw.Draw(img, "RGBA")
    chrome(d, scene["chapter"], tl["series"], idx, len(tl["scenes"]))
    ctx = scene_ctx(scene, idx)
    active_start = 0.0 if idx == 0 else float(scene["start"])
    scenes[scene["visual"]](img, d, ctx, t - active_start)
    cue = current_cue(scene, t)
    if cue is not None:
        subtitle(img, d, cue, t - scene["start"])
    progress_bar(d, t / max(0.001, tl["total"]))
    return img


def preview(project, scenes, times):
    tl = load_timeline(project)
    bg = graphics.bg_image()
    frames = project / "out" / "frames"
    frames.mkdir(exist_ok=True, parents=True)
    for t in times:
        t0 = time.time()
        img = render_frame(tl, bg, scenes, t)
        p = frames / f"preview_{t:07.2f}.png"
        img.save(p)
        print(f"t={t:7.2f}s  -> {p}  ({time.time() - t0:.2f}s)", flush=True)


def encode(project, scenes, tl, start=0.0, end=None, dest=None):
    fps = int(tl["fps"])
    if int(tl.get("width", W)) != W or int(tl.get("height", H)) != H:
        raise SystemExit(f"timeline is {tl.get('width')}x{tl.get('height')}, renderer supports {W}x{H}")
    total = float(tl["total"])
    end = total if end is None else min(float(end), total)
    n_frames = int(round((end - start) * fps))
    dest = dest or (project / "out" / "video_silent.mp4")
    cmd = [
        FFMPEG, "-y", "-loglevel", "warning",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(fps), "-i", "-",
        "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(dest),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    bg = graphics.bg_image()
    t_start = time.time()
    try:
        for i in range(n_frames):
            t = start + i / fps
            img = render_frame(tl, bg, scenes, t)
            proc.stdin.write(img.tobytes())
            if i % 150 == 0 and i:
                elapsed = time.time() - t_start
                print(f"  {i}/{n_frames} frames  ({i / elapsed:.1f} fps)  t={t:6.1f}s", flush=True)
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
        proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg encode failed: {proc.returncode}")
    print(f"video -> {dest}  ({time.time() - t_start:.1f}s)", flush=True)


def mux(project, dest=None):
    dest = dest or (project / "out" / f"{project.name}.mp4")
    silent = project / "out" / "video_silent.mp4"
    narration = project / "out" / "narration.wav"
    bgm = project / "out" / "bgm.wav"
    for p in (silent, narration, bgm):
        if not p.exists():
            raise SystemExit(f"missing {p}")
    cmd = [
        FFMPEG, "-y", "-loglevel", "warning",
        "-i", str(silent), "-i", str(narration), "-i", str(bgm),
        "-filter_complex",
        "[1:a]aresample=48000,volume=1.0[v];"
        "[2:a]aresample=48000,volume=0.75[b];"
        "[v][b]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
        # Platform-friendly loudness; single-pass loudnorm adds ~0.1s latency,
        # which is inaudible against narration-only animation.
        "alimiter=limit=0.95,loudnorm=I=-16:TP=-1.5:LRA=11[a]",
        "-map", "0:v", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-shortest", "-movflags", "+faststart", str(dest),
    ]
    subprocess.run(cmd, check=True)
    print(f"final -> {dest}", flush=True)


def main():
    ap = argparse.ArgumentParser(description="Render frames with Pillow and encode with ffmpeg")
    ap.add_argument("--project", default=".", help="project directory with scenes.py and out/timeline.json")
    ap.add_argument("--times", help="comma separated preview timestamps (seconds)")
    ap.add_argument("--seconds", type=float, help="render the first N seconds to out/sample.mp4")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float)
    ap.add_argument("--mux", action="store_true", help="only mux existing video_silent.mp4 + audio")
    args = ap.parse_args()

    project = Path(args.project).resolve()
    if args.mux:
        mux(project)
        return

    scenes = load_scenes(project)
    if args.times:
        preview(project, scenes, [float(x) for x in args.times.split(",") if x.strip()])
        return

    tl = load_timeline(project)
    if args.seconds:
        encode(project, scenes, tl, 0.0, args.seconds, project / "out" / "sample.mp4")
        return

    encode(project, scenes, tl, args.start, args.end)
    if args.start == 0 and args.end is None:
        mux(project)


if __name__ == "__main__":
    main()
