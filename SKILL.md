---
name: explainer-video
description: 制作带 AI 配音、中文字幕、逐帧动画的 1080P 横屏讲解视频（知识科普 / B站 / 技术面试向）。覆盖脚本撰写、edge-tts 配音与逐句时间戳、Pillow 场景动画、ffmpeg 合成、封面生成。当用户要求"做一个讲解视频 / 科普视频 / 知识动画 / 把内容做成视频 / B站视频"，或提供主题希望生成成片时使用。
---

# Explainer Video

把「主题或文稿」变成一条可直接上传的 1080P 讲解成片：AI 配音 + 逐句同步动画 + 烧录字幕 + 环境 BGM + 封面。

一套完整示例在 `examples/distributed-lock/`（6 分 49 秒，12 个场景）。成品预览：
<https://dl.ai-bong.cn/aireview/video/>

## 这个技能适合什么

- 6–10 分钟横屏知识讲解（B站/YouTube/课程/内部分享）
- 需要「一句文案对应一个动画节拍」的强同步视频
- 无人出镜、无录屏，纯图形化叙事
- 后续要改文案 → 一键重新配音、重新排版、重新出片

不适合：真人拍摄、复杂 3D、逐字卡拉 OK 字幕、需要口型同步的数字人。

## 环境

- Python 3.10+，Windows / macOS / Linux
- 依赖：`pip install -r requirements.txt`（edge-tts、Pillow、numpy、imageio-ffmpeg、mutagen）
- 中文字体：Windows 自动用微软雅黑；macOS/Linux 自动尝试 PingFang / Noto CJK / 文泉驿
- 可用环境变量覆盖字体：`EXPLAINER_FONT_REGULAR` / `EXPLAINER_FONT_BOLD` / `EXPLAINER_FONT_CODE`（传绝对路径）

ffmpeg 由 `imageio-ffmpeg` 自带，无需系统安装。

## 项目结构

每个视频是一个独立目录：

```
my-video/
├── script.json      # 文案 + 章节 + 音色
├── scenes.py        # 每个 visual 一个绘制函数
├── cover.py         # 可选：自定义封面
└── out/             # 构建产物（不要提交）
    ├── audio/       # 每场 mp3/json/wav
    ├── timeline.json
    ├── subtitles.srt
    ├── narration.wav / bgm.wav
    ├── cover_16x9.png / cover_16x10.png
    └── my-video.mp4
```

从零开始：新建目录，写 `script.json` 和 `scenes.py`。想先跑通，直接复制示例：

```bash
cp -r examples/distributed-lock my-video
```

## 工作流

### 1. 写 script.json

```json
{
  "title": "视频标题（也用于封面）",
  "series": "系列名 · 时长",
  "voice": "zh-CN-YunxiNeural",
  "rate": "-6%",
  "gap": 0.45,
  "lead": 0.9,
  "tail": 1.6,
  "scenes": [
    {
      "id": "s00",
      "chapter": "00 / 开场",
      "visual": "hook",
      "narration": "一句或几句完整口播。"
    }
  ]
}
```

- `scenes[].visual` 必须对应 `scenes.py` 里 `SCENES` 的 key。
- `lead`：片头留白（第一句配音延后 0.9s，画面先动）。
- `gap`：场景之间的停顿；`tail`：片尾留白。
- 中文 TTS 实测语速：`-6%` 下约 **230–260 字符/分钟**（含标点），纯汉字约 200 字/分钟。
  - 6 分钟 ≈ 1400–1600 汉字；7 分钟 ≈ 1650–1900 汉字；8 分钟 ≈ 1900–2200 汉字。
  - 先写内容，跑完 `build.py` 看实际时长，再增删场景，不要靠调语速凑时长。
- 音色推荐：`zh-CN-YunxiNeural`（年轻男声，技术讲解）、`zh-CN-YunjianNeural`（沉稳）、`zh-CN-XiaoxiaoNeural`（女声）。
- 每场 narration 建议 2–6 句、30–60 秒；太长会导致一个画面撑不住，太短会切得碎。

### 2. 写 scenes.py

每个场景函数签名固定：

```python
def my_scene(img, d, ctx, t):
    ...
```

- `img`：PIL RGB 画布（1920×1080），可直接 `paste` 旋转贴图
- `d`：`ImageDraw`（RGBA 模式，支持透明叠加）
- `ctx`：`{dur, shift, sentences, cues, scene}`
- `t`：本场景内的本地时间（秒）。**第 0 场例外**：本地时间从 0 开始，但 `ctx["shift"]=0.9`，让节拍对齐 0.9s 才开始的配音。

最小骨架：

```python
from graphics import BLUE, GREEN, INK, LINE, MUTED, WHITE, card, chip, icon_check, prog, text

def beat(ctx, i, fallback=0.75):
    """第 i 句配音的开始时间（含第 0 场的 0.9s 偏移）。"""
    ss = ctx["sentences"]
    if i < len(ss):
        return ss[i]["start"] + ctx["shift"]
    return ctx["dur"] * fallback + ctx["shift"]

def header(d, t, title, sub=None):
    p = prog(t, 0.35, 0.55)
    if p <= 0:
        return
    y = 118 - (1 - p) * 16
    text(d, (110, y), title, 54, "b", INK, alpha=p)
    if sub:
        text(d, (114, y + 74), sub, 28, "r", MUTED, alpha=p)

def hook(img, d, ctx, t):
    header(d, t, "一句话结论", "副标题")
    p = prog(t, beat(ctx, 0), 0.5)
    if p > 0:
        card(img, d, (480, 300), 960, 360, 20, WHITE, LINE, alpha=p)
        text(d, (540, 390), "核心观点", 56, "b", INK, alpha=p)
        icon_check(d, 560, 560, 46, GREEN, alpha=p)

SCENES = {"hook": hook}
```

关键规则：

1. **一切出现动画都挂在 `beat(ctx, i)` 上**，不要写死秒数。换音色、改语速后，句子长度会变，写死就会错位。
2. 第 0 场用 `t` 做片头预动画（0.1–0.9s），用 `beat()` 做配音同步内容。
3. 句数不够用时：`beat(ctx, i, fallback=0.8)` 会回退到「场景时长的 80%」，适合做收尾总结。
4. 布局安全区：标题 `y=118`；正文 `y≈240–930`；底部 930–990 留给进度条与字幕；左右边距 110。
5. 先画卡片/容器，再画内容；同一时刻最多 4–5 个视觉组在动，避免画面过吵。
6. 用 `prog(t, start, dur)` 做淡入 + 位移（内部 ease-out）；透明度统一传 `alpha=p`。
7. 中文不要用 `code=True`（等宽字体无中文，会变方框）；`code_panel` 的标题也已强制普通字体。

图形库速查（都在 `engine/graphics.py`）：

| API | 用途 |
|---|---|
| `card(img,d,xy,w,h,radius,fill,border,alpha)` | 圆角卡片 + 柔和阴影 |
| `chip(d,xy,text,size,fg,bg)` | 胶囊标签 |
| `arrow / curve_arrow` | 直线 / 贝塞尔箭头 |
| `icon_lock/clock/shield/server/key/check/cross` | 线性图标 |
| `code_panel(d,xy,w,h,lines,title,highlight=)` | 终端代码面板，带 token 高亮 |
| `multiline / wrap / textlen` | 中文换行与测量 |
| `stamp(img,center,text,color,size,angle)` | 旋转印章（"超卖""通过"） |
| `cylinder / bg_image / chrome / subtitle / progress_bar` | 数据库柱、背景、页眉、字幕、进度条 |

### 3. 配音 + 时间轴

```bash
python engine/build.py --project my-video
# 临时换音色/语速试听：
python engine/build.py --project my-video --voice zh-CN-YunjianNeural --rate -10%
```

产物：`out/audio/*.mp3`、`out/narration.wav`、`out/bgm.wav`、`out/timeline.json`、`out/subtitles.srt`。

- TTS 按 `sha1(voice|rate|text)` 缓存，只重跑改过的句子；网络失败自动重试 4 次。
- 中文 edge-tts 只发 `SentenceBoundary`，所以字幕按「句 → 逗号子句 → 字符权重」二次切分。
- 构建结束会打印每场的实际开始时间/时长/句数。**先读这个表**，再决定动画节拍。

### 4. 抽帧验收（必做）

```bash
python engine/render.py --project my-video --times 20,53,118,265,350
```

逐张检查：

- 每句配音说到的概念，画面是否在同一时间出现
- 有没有「开场只有标题、空屏太久」
- 文字是否压到字幕、进度条、页眉
- 中文有没有方框（字体问题）、代码面板是否溢出
- 卡片阴影是否过重、元素是否互相遮挡

发现错位就改 `scenes.py` 的 `beat(ctx, i)` 索引，不要改视频时间。

### 5. 渲染成片

```bash
python engine/render.py --project my-video
```

内部流程：Pillow 逐帧绘制 → 原始 RGB 管道 → libx264（CRF 20、yuv420p、faststart）→ 混入人声 + BGM → 响度归一化 → `out/<项目名>.mp4`。

- 渲染速度约 19–23 fps（1080P，单线程绘制），7 分钟视频约 9–11 分钟。
- 只想验证前 30 秒：`--seconds 30`，产出 `out/sample.mp4`。
- 只想重新混音：`--mux`。
- 默认人声 -16 LUFS、真峰 -1.5 dBTP，BGM 压在人声下约 14 dB。单遍 loudnorm 会带来约 0.1s 音频延迟，对旁白型视频不可感知。

### 6. 封面

```bash
python engine/cover.py --project my-video
```

- 有 `cover.py` 且定义 `render(width, height) -> PIL.Image` 时用它；否则根据 `title/series` 生成通用封面。
- 输出 `cover_16x9.png`（视频页）与 `cover_16x10.png`（B站信息流）。
- 封面示例见 `examples/distributed-lock/cover.py`。

### 7. 发布（可选）

静态托管即可在线播放：把 `out/<项目名>.mp4`、`out/cover.jpg`、`out/subtitles.srt` 和一个 HTML5 播放页放到任意静态服务器。MP4 已 `+faststart`，nginx 默认支持 Range，可拖动进度。

## 质量检查清单

- [ ] 总时长在目标区间（默认 6–8 分钟），信息密度均匀
- [ ] 每个场景的最后一句话说完后，画面至少再停 1s 才切
- [ ] 抽帧覆盖每个场景的开头/中段/结尾，无空屏、无重叠
- [ ] 字幕不超过两行，不与底部进度条重叠
- [ ] 代码示例拼写正确、关键字高亮、无中文豆腐块
- [ ] 音画同步：随机抽 3 处，人声关键词与画面元素同时出现
- [ ] 最终响度 -16 LUFS 左右，无削波
- [ ] 封面 16:9 与 16:10 都检查过

## 常见坑

| 现象 | 原因 / 解决 |
|---|---|
| 中文变方框 | 用了 `code=True` 或等宽字体；中文一律普通字体 |
| 动画越来越晚 | 节拍写成了固定秒数；改回 `beat(ctx, i)` |
| 第 0 场整体偏移 0.9s | 忘记加 `ctx["shift"]` |
| 画面空太久 | 第一句是引入句，内容却等到第 2 句才出现；把容器提前到 `t≈0.5`，内容再挂节拍 |
| 收尾元素不出现 | `beat` 索引超出句数；用 `beat(ctx, i, fallback=0.8)` |
| 字幕闪碎 | 子句太短；`build.py` 已自动合并 6 字以下相邻子句，仍碎就改文案断句 |
| TTS 429/超时 | 已自动重试；仍失败检查网络，或 `--voice` 换一个 |
| 渲染中途失败 | 看 ffmpeg 退出码；多半是磁盘空间或管道提前关闭 |
| 视频只有 6.5MB 担心糊 | 纯色/文字画面 CRF 20 码率很低但无损观感；需要更高码率可改 `-crf 18` |

## 示例项目

`examples/distributed-lock/` 是完整参考实现：

- 12 场：超卖 hook → 单机锁边界 → 四条件 → SETNX → 误删/Lua → 看门狗 → Redisson → Redlock → 选型 → 生产 → 面试 → 口诀
- 覆盖库存数字滚动、JVM 对比、时间线、代码面板、时钟续期、五节点图、对比表、印章等常用构图
- 学习顺序：先读 `script.json` 的节奏，再读 `scenes.py` 每场如何把 `beat()` 映射到元素出现

## 参考

- 视觉风格参考：B站「码上懂_」的 Redis 讲解视频（白底网格 + 极简深色标签 + AI 旁白）
- 技术栈：edge-tts、Pillow、numpy、ffmpeg/libx264
