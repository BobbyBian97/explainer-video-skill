# Pipeline internals

这份文档解释流水线的时间模型、渲染循环和混音细节，便于改引擎或排查不同步问题。

## 1. 时间轴

`engine/build.py` 是唯一的时间源。所有时间单位为秒，帧率固定 30。

```
cursor = lead                      # 第一场音频开始时间（默认 0.9）
for scene in scenes:
    scene.start = cursor
    scene.dur   = TTS 音频实际时长
    cursor     += scene.dur + gap
total = cursor - gap + tail
```

所以：

- 第 0 场音频从 `lead` 开始，不是 0；片头动画有 0.9s 预滚动。
- 场景之间的空档是 `gap`（默认 0.45s），片尾额外留 `tail`（默认 1.6s）。
- `timeline.json` 中每场的 `start` 是**绝对时间**，`sentences[].start/end` 与 `cues[]` 是**相对本场音频开始**的时间。

### 句子与字幕

- edge-tts 中文音色只返回 `SentenceBoundary`，`WordBoundary` 通常为空。
- `ensure_sentences()` 把句子边界转成 `{start, duration}`；若没有边界，按标点长度比例切分。
- `build_cues()` 在句子内部再按 `，、；：` 切子句，按**有效字符数**（汉字/字母/数字）分配时长，然后合并过短子句（<6 字）避免字幕闪烁。
- SRT 用绝对时间（`scene.start + cue.start`），视频内字幕用相对时间。

### 场景 0 的特殊偏移

`engine/render.py::scene_ctx`：

```python
active_start = 0.0 if idx == 0 else scene["start"]
shift = scene["start"] - active_start
```

- 普通场景：`active_start = start`，`shift = 0`，`t` 从 0 开始，`beat()` 直接取句子时间。
- 场景 0：`active_start = 0`，`shift = lead = 0.9`，`t` 从 0 开始，但 `beat()` 返回 `0.9 + 句子时间`，与配音对齐。片头标题等预动画用原始 `t`。

## 2. 渲染循环

```
for frame i in range(round((end-start)*fps)):
    t = start + i/fps
    img = bg.copy()                      # 预渲染的背景，避免每帧重算渐变
    d = ImageDraw.Draw(img, "RGBA")
    chrome(...)                          # 页眉、进度点
    scene = active_scene(t)
    scenes[visual](img, d, ctx, t - active_start)
    subtitle(img, d, cue, t - scene.start)
    progress_bar(d, t / total)
    proc.stdin.write(img.tobytes())      # rgb24 原始帧 → ffmpeg
```

- 背景 `graphics.bg_image()` 只在开始时算一次，包含渐变、网格和两个角落光晕。
- `active_scene` 选择「最后一个 start <= t」的场景；场景内函数负责自己的淡入淡出，引擎不做交叉转场。
- 字幕只在 cue 区间内绘制，两端 0.12s 透明度淡入淡出。
- 进度条按全局时间比例。

### 编码参数

```
libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -movflags +faststart
```

纯色/文字画面在 CRF 20 下码率很低（示例全片 130kbps 视频码率），但主观无损；`yuv420p` 保证全平台兼容；`faststart` 把 moov 移到文件头，支持边下边播。

## 3. 混音

```
[v] narration.wav  volume=1.0
[b] bgm.wav        volume=0.75
[v][b] amix=inputs=2:normalize=0
       → alimiter=0.95
       → loudnorm=I=-16:TP=-1.5:LRA=11
       → AAC 192k / 48kHz / stereo
```

- BGM 由 `make_bgm()` 合成：Am–F–C–G 循环长音 pad + 每 1.6s 一个稀疏拨弦，一阶低通软化高频，峰值归一到 0.055。
- 人声原始 RMS 约 -24 dBFS，经 loudnorm 提升到 -16 LUFS；BGM 相应保持约 14 dB 以下。
- 单遍 `loudnorm` 内部重采样到 192k，会产生约 **0.1s 音频延迟**。旁白型视频无口型，可忽略；若做口播数字人，应改用两遍 loudnorm 并在视频侧补偿。
- `-shortest` 以视频长度为准截断音频。

## 4. 可复现性

- TTS 缓存的 key 是 `sha1(voice|rate|text)`，存在 `out/audio/<scene>.json`。文本、音色、语速不变就完全跳过网络请求。
- 示例项目在干净目录重跑 `build.py`，得到与首版逐帧一致的时间轴（edge-tts 对同一文本输出稳定）。
- 改文案后只有该场景重新合成，其余场景时间轴整体平移，动画自动跟随。

## 5. 性能

示例环境（Windows 10、Python 3.13、单线程 Pillow）：

- 绘制：19–23 fps（1080P）
- 6:49 / 12258 帧：约 9–10 分钟
- BGM 合成：约 10–20 秒（numpy 逐样本一阶滤波）
- TTS：12 场约 40–60 秒（首次），缓存后秒级
- 成片：17MB，6:49

优化方向：提高渲染并发（多进程分段渲染再 concat）、把 BGM 低通改成 scipy、把静态卡片预渲染成贴图。当前单线程足够，优先保证代码可读。

## 6. 扩展

- **换分辨率**：`graphics.py` 的 `W,H` 是全局常量，改 4K 需要同步缩放所有布局常量；不建议，1080P 已满足 B站。
- **帧率**：`timeline.json` 的 `fps` 与 `encode` 共用，改 60 会让渲染时间翻倍。
- **新图形**：在 `graphics.py` 增加函数，保持「接受 `alpha`、返回 None」的约定，场景里用 `prog()` 控制出现。
- **多语言**：换 `voice`（如 `en-US-*`），但字幕切分规则按中文标点设计，需要调整 `split_clauses`。

## 7. 排查不同步

1. `python engine/build.py` 打印的每场 `start/dur` 与预期是否一致？
2. 抽帧时间用绝对时间（`timeline.json` 的 `scene.start + 偏移`），不要用场景内时间。
3. 动画元素是否直接用了固定秒数？改成 `beat(ctx, i)`。
4. 第 0 场是否漏加 `ctx["shift"]`？
5. 字幕与配音差 0.1s：检查是否使用了 loudnorm（见上）。
6. 画面元素出现顺序对、但整体偏晚：`beat` 索引通常差 1（0-based）。
