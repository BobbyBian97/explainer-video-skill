# 示例：分布式锁讲解视频

这是技能附带的完整参考项目，也是线上成片的源工程。

- 成片：6:49 / 1920×1080 / 30fps
- 源：`script.json` + `scenes.py` + `cover.py`

## 运行

```bash
# 在仓库根目录
python engine/build.py  --project examples/distributed-lock
python engine/render.py --project examples/distributed-lock --times 20,118,265
python engine/render.py --project examples/distributed-lock
python engine/cover.py  --project examples/distributed-lock
```

首次运行会重新调用 edge-tts（12 场，约 1 分钟）；之后有缓存，改一句只重跑一句。

## 场景表

| # | 章节 | 时长 | 画面要点 |
|---|---|---|---|
| 00 | 开场 | 18.7s | 库存 100 → -3 滚动，红色「超卖」印章 |
| 01 | 单机锁的边界 | 32.6s | 单 JVM vs 双 JVM + 负载均衡 |
| 02 | 四个条件 | 31.3s | 互斥 / 防死锁 / 防误删 / 高可用 |
| 03 | SETNX 的进化 | 39.5s | 两条命令 vs `SET NX EX` 原子命令 |
| 04 | 误删与 Lua | 38.0s | 30s TTL 与 35s 业务的时间线冲突 |
| 05 | 看门狗与可重入 | 32.4s | 30s 租期、每 10s 续期、Hash 重入计数 |
| 05b | Redisson 实战 | 36.8s | `RLock` 代码、tryLock、订阅解锁 |
| 06 | Redlock 争议 | 39.1s | 主从切换丢锁、五节点过半、两种结论 |
| 06b | 选型对比 | 40.2s | Redis / ZooKeeper / etcd / 数据库 |
| 07 | 生产实践 | 41.0s | 五条落地清单 + 更简单的替代 |
| 08 | 面试模板 | 38.4s | 结论 → 演进 → 边界 三步法 |
| 09 | 收尾 | 13.0s | 四句口诀卡片 |

## 可复用的构图

`scenes.py` 里可以直接抄的组件：

- 数字滚动 + 阈值变色 + 印章（`s00` 的库存卡）
- 左右对比卡片与连接箭头（`s01` 的双 JVM）
- 编号规则卡（`s02` 四条件）
- 终端命令面板与高亮（`s03`、`s05b`）
- 横向时间线 + 事件区间（`s04`）
- 时钟/续期循环（`s05`）
- 五节点互联网状图（`s06`）
- 多列对比表（`s06b`）
- 清单 + 侧栏建议卡（`s07`）
- 三列方法论 + 底部徽章（`s08`）
- 四张口诀卡（`s09`）

## 改这个示例

- 换主题：改 `script.json` 的所有 `narration`，同步调整 `scenes.py` 的文字与图形。
- 换音色：`python engine/build.py --project . --voice zh-CN-YunjianNeural --rate -8%`。
- 加场景：在 `scenes` 数组插入一项（`visual` 新 key），在 `scenes.py` 写函数并注册到 `SCENES`。
- 换封面：改 `cover.py::render`，保持返回 1920×1080 / 1920×1200 的图。

## 线上发布

`out/distributed-lock.mp4` 已 `+faststart`，直接放静态服务器即可拖动播放。示例页面（播放器 + 章节跳转 + 字幕下载）见原工程的 `web/index.html`，未包含在本仓库中。
