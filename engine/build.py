# -*- coding: utf-8 -*-
"""Build narration, timeline, subtitles and BGM for an explainer-video project.

Usage:
    python engine/build.py --project examples/distributed-lock

Reads <project>/script.json, writes <project>/out/:
    audio/<scene>.mp3/.json/.wav, narration.wav, bgm.wav,
    timeline.json, subtitles.srt
"""
import argparse
import asyncio
import hashlib
import json
import re
import subprocess
import sys
import wave
from pathlib import Path

import edge_tts
import imageio_ffmpeg
import numpy as np
from mutagen.mp3 import MP3

SR = 48000
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def char_weight(s: str) -> int:
    return max(1, len(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]", s)))


def split_clauses(text: str):
    text = text.strip()
    if not text:
        return []
    parts = re.split(r"(?<=[，、；：,;:])", text)
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        while len(p) > 24:
            cut = p.rfind(" ", 0, 24)
            if cut < 10:
                cut = 24
            out.append(p[:cut].strip())
            p = p[cut:].strip()
        if p:
            out.append(p)
    merged = []
    for p in out:
        if merged and char_weight(merged[-1]) < 6 and char_weight(merged[-1]) + char_weight(p) <= 28:
            merged[-1] += p
        else:
            merged.append(p)
    return merged


async def synth_scene(scene, voice, rate, mp3_path):
    text = scene["narration"]
    key = hashlib.sha1(f"{voice}|{rate}|{text}".encode("utf-8")).hexdigest()[:16]
    meta_path = mp3_path.with_suffix(".json")
    if mp3_path.exists() and meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("key") == key:
            return meta

    last_err = None
    for attempt in range(4):
        try:
            com = edge_tts.Communicate(text, voice, rate=rate)
            boundaries = []
            with open(mp3_path, "wb") as f:
                async for chunk in com.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                    elif chunk["type"] in ("SentenceBoundary", "WordBoundary"):
                        boundaries.append(
                            {
                                "type": chunk["type"],
                                "offset": int(chunk["offset"]) / 1e7,
                                "duration": int(chunk["duration"]) / 1e7,
                                "text": chunk.get("text", ""),
                            }
                        )
            duration = float(MP3(mp3_path).info.length)
            # Chinese edge-tts voices usually emit SentenceBoundary only.
            sentences = [b for b in boundaries if b["type"] == "SentenceBoundary"]
            if not sentences:
                sentences = [b for b in boundaries if b["type"] == "WordBoundary"]
            sentences.sort(key=lambda x: x["offset"])
            meta = {"key": key, "voice": voice, "rate": rate, "duration": duration, "sentences": sentences}
            meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
            return meta
        except Exception as e:  # network hiccups / 429
            last_err = e
            print(f"  retry {attempt + 1}/4: {e}", flush=True)
            await asyncio.sleep(2.0 + attempt * 2)
    raise RuntimeError(f"TTS failed for {scene['id']}: {last_err}")


def ensure_sentences(narration, meta):
    dur = meta["duration"]
    sents = meta.get("sentences") or []
    if not sents:
        # Proportional fallback based on punctuation.
        parts = [p for p in re.split(r"(?<=[。！？!?])", narration) if p.strip()]
        weights = [char_weight(p) for p in parts]
        total = sum(weights) or 1
        out, t = [], 0.0
        for p, w in zip(parts, weights):
            d = dur * w / total
            out.append({"text": p, "offset": t, "duration": d})
            t += d
        return out
    out = []
    for i, s in enumerate(sents):
        start = max(0.0, min(s["offset"], dur))
        if i + 1 < len(sents):
            end = min(sents[i + 1]["offset"], dur)
        else:
            end = dur
        end = max(end, start + 0.4)
        out.append({"text": s["text"].strip(), "offset": start, "duration": end - start})
    return out


def build_cues(sentences):
    cues = []
    for s in sentences:
        clauses = split_clauses(s["text"])
        if not clauses:
            continue
        weights = [char_weight(c) for c in clauses]
        total = sum(weights) or 1
        t = s["offset"]
        for c, w in zip(clauses, weights):
            d = s["duration"] * w / total
            cues.append({"start": t, "end": t + d, "text": c})
            t += d
    # Merge very short neighbours so subtitles don't flicker.
    merged = []
    for c in cues:
        if merged and char_weight(merged[-1]["text"]) < 6 and char_weight(merged[-1]["text"]) + char_weight(c["text"]) <= 26:
            merged[-1]["text"] += c["text"]
            merged[-1]["end"] = c["end"]
        else:
            merged.append(dict(c))
    return merged


def fmt_srt(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def decode_to_wav(mp3_path, wav_path):
    cmd = [FFMPEG, "-y", "-loglevel", "error", "-i", str(mp3_path), "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", str(wav_path)]
    subprocess.run(cmd, check=True)
    with wave.open(str(wav_path), "rb") as w:
        assert w.getframerate() == SR and w.getnchannels() == 1 and w.getsampwidth() == 2
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    return data


def write_wav(path, mono):
    pcm = np.clip(mono, -1.0, 1.0)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((pcm * 32767.0).astype(np.int16).tobytes())


def make_bgm(total, path):
    """A quiet, warm ambient bed: slow pads + sparse plucked notes."""
    n = int(total * SR)
    t = np.arange(n, dtype=np.float64) / SR
    chords = [
        [110.00, 130.81, 164.81],  # Am
        [87.31, 110.00, 130.81],   # F
        [130.81, 164.81, 196.00],  # C
        [98.00, 123.47, 146.83],   # G
    ]
    seg = 8.0
    mix = np.zeros(n, dtype=np.float64)
    idx = 0
    pos = 0.0
    while pos < total:
        chord = chords[idx % len(chords)]
        start = int(pos * SR)
        length = min(int((seg + 2.2) * SR), n - start)
        if length <= 0:
            break
        lt = np.arange(length) / SR
        env = np.minimum(1.0, lt / 2.2) * np.minimum(1.0, np.maximum(0.0, (seg + 2.2 - lt) / 2.2))
        env = env * (0.85 + 0.15 * np.sin(2 * np.pi * 0.07 * lt + idx))
        sig = np.zeros(length)
        for f in chord:
            sig += 0.5 * np.sin(2 * np.pi * f * lt)
            sig += 0.18 * np.sin(2 * np.pi * f * 2 * lt)
            sig += 0.08 * np.sin(2 * np.pi * f * 3 * lt)
        mix[start:start + length] += sig * env * 0.09
        pos += seg
        idx += 1

    note_pos = 1.2
    note_i = 0
    order = [0, 2, 1, 2, 0, 1, 2, 1]
    while note_pos < total - 1.0:
        chord = chords[int(note_pos // seg) % len(chords)]
        f = chord[order[note_i % len(order)]] * 2
        start = int(note_pos * SR)
        length = min(int(1.8 * SR), n - start)
        lt = np.arange(length) / SR
        env = np.exp(-lt / 0.55) * np.minimum(1.0, lt / 0.012)
        tone = np.sin(2 * np.pi * f * lt) + 0.25 * np.sin(2 * np.pi * f * 2 * lt)
        mix[start:start + length] += tone * env * 0.035
        note_pos += 1.6
        note_i += 1

    # Gentle one-pole low-pass.
    a = 0.08
    y = np.zeros_like(mix)
    acc = 0.0
    for i in range(n):
        acc += a * (mix[i] - acc)
        y[i] = acc
    mix = y
    peak = np.max(np.abs(mix)) or 1.0
    mix = mix / peak * 0.055
    fade = int(2.5 * SR)
    if n > 2 * fade:
        mix[:fade] *= np.linspace(0, 1, fade)
        mix[-fade:] *= np.linspace(1, 0, fade)
    write_wav(path, mix)


async def build(project: Path, voice_override=None, rate_override=None):
    cfg = json.loads((project / "script.json").read_text(encoding="utf-8"))
    voice = voice_override or cfg["voice"]
    rate = rate_override or cfg.get("rate", "+0%")
    scenes = cfg["scenes"]
    out = project / "out"
    audio_dir = out / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    timeline_scenes = []
    cursor = float(cfg.get("lead", 0.9))
    gap = float(cfg.get("gap", 0.45))
    narration_parts = []
    srt_lines = []
    srt_no = 0

    for i, scene in enumerate(scenes):
        sid = scene["id"]
        mp3_path = audio_dir / f"{sid}.mp3"
        print(f"[{i + 1}/{len(scenes)}] TTS {sid} ...", flush=True)
        meta = await synth_scene(scene, voice, rate, mp3_path)
        scene_dur = float(meta["duration"])
        sentences = ensure_sentences(scene["narration"], meta)
        cues = build_cues(sentences)
        for c in cues:
            c["start"] = max(0.0, min(c["start"], scene_dur))
            c["end"] = max(c["start"] + 0.25, min(c["end"], scene_dur + 0.15))

        audio = decode_to_wav(mp3_path, audio_dir / f"{sid}.wav")
        f = min(int(0.025 * SR), len(audio) // 2)
        if f > 0:
            audio[:f] *= np.linspace(0, 1, f)
            audio[-f:] *= np.linspace(1, 0, f)
        narration_parts.append((cursor, audio))

        timeline_scenes.append(
            {
                "id": sid,
                "chapter": scene["chapter"],
                "visual": scene["visual"],
                "narration": scene["narration"],
                "audio": f"out/audio/{sid}.mp3",
                "start": round(cursor, 3),
                "dur": round(scene_dur, 3),
                "sentences": [
                    {"start": round(s["offset"], 3), "end": round(s["offset"] + s["duration"], 3), "text": s["text"]}
                    for s in sentences
                ],
                "cues": [
                    {"start": round(c["start"], 3), "end": round(c["end"], 3), "text": c["text"]}
                    for c in cues
                ],
            }
        )
        for c in cues:
            srt_no += 1
            srt_lines.append(str(srt_no))
            srt_lines.append(f"{fmt_srt(cursor + c['start'])} --> {fmt_srt(cursor + c['end'])}")
            srt_lines.append(c["text"])
            srt_lines.append("")
        cursor += scene_dur + gap
        await asyncio.sleep(0.25)

    total = cursor - gap + float(cfg.get("tail", 1.6))
    total_samples = int(total * SR)
    narration = np.zeros(total_samples, dtype=np.float32)
    for start, audio in narration_parts:
        s = int(start * SR)
        e = min(total_samples, s + len(audio))
        narration[s:e] += audio[: e - s]

    write_wav(out / "narration.wav", narration)
    print("building BGM ...", flush=True)
    make_bgm(total, out / "bgm.wav")

    timeline = {
        "title": cfg["title"],
        "series": cfg["series"],
        "voice": voice,
        "rate": rate,
        "fps": 30,
        "width": 1920,
        "height": 1080,
        "lead": cfg.get("lead", 0.9),
        "gap": gap,
        "total": round(total, 3),
        "scenes": timeline_scenes,
    }
    (out / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "subtitles.srt").write_text("\n".join(srt_lines), encoding="utf-8")

    mins, secs = divmod(int(round(total)), 60)
    print(f"DONE total={mins}:{secs:02d}  scenes={len(scenes)}  -> {out / 'timeline.json'}", flush=True)
    for s in timeline_scenes:
        print(f"  {s['id']}  start={s['start']:7.2f}  dur={s['dur']:6.2f}  sentences={len(s['sentences'])}  cues={len(s['cues'])}", flush=True)


def main():
    ap = argparse.ArgumentParser(description="Build TTS + timeline + subtitles + BGM")
    ap.add_argument("--project", default=".", help="project directory containing script.json")
    ap.add_argument("--voice", help="override edge-tts voice, e.g. zh-CN-YunxiNeural")
    ap.add_argument("--rate", help="override speech rate, e.g. -6%%")
    args = ap.parse_args()
    project = Path(args.project).resolve()
    if not (project / "script.json").exists():
        raise SystemExit(f"script.json not found in {project}")
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(build(project, args.voice, args.rate))


if __name__ == "__main__":
    main()
