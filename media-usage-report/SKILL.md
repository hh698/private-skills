---
name: media-usage-report
description: "Use when analyzing a user's streaming and content-consumption preferences across video, social, music, reading, and audio platforms such as Bilibili/B站, Douyin/抖音, Xiaohongshu/小红书, Weibo/微博, YouTube, NetEase Cloud Music/网易云音乐, QQ音乐, Spotify, 番茄小说, 起点, or 微信读书, including PC, phone, and tablet history from browser, account, app, export, or manual records."
---

# Media Usage Report

生成用户在某时间段内（一天 / 一周 / 自定义区间）的流媒体与内容消费偏好画像，覆盖观看、浏览、收听、阅读等行为，输出简短的文字总结和一份自包含的可视化 HTML 报告。

## Workflow

1. **确定范围**：确认平台（B站/抖音/小红书/微博/网易云音乐/番茄小说等）、内容形态（视频/图文/音乐/播客/小说/直播等）、时间窗口（今天/最近一周/自定义日期区间）、设备范围（PC/手机/平板）和数据来源（浏览器历史、平台账号历史、App 内历史、平台数据导出或用户手动记录）。
2. **采集数据**：按平台选择数据源，见 [references/platforms.md](references/platforms.md)。
3. **合并多端记录**：把 PC、手机、平板的数据统一成记录数组；保留 `source_device`、`source_channel`、`content_type` 等字段，避免把某个渠道缺失误判为真实偏好。
4. **分析画像**：按标题、作者、歌手、主播、书名、标签等信息归类内容领域，统计每日/时段活跃度、高频创作者/账号/歌手/作者、观看/收听/阅读进度。分类规则见 [references/categories.md](references/categories.md)。
5. **生成报告**：运行 `scripts/build_report.py` 从采集的记录生成自包含 HTML（深色主题、KPI 卡片、领域分布、每日/时段图表、创作者排行、消费明细），并写一段 3–5 句的偏好总结。
6. **交付**：报告为单文件 HTML（如 `media-usage-report.html`），离线可打开；可选部署到 Netlify，见 [references/deploy.md](references/deploy.md)。

## 数据采集核心经验

采集过程最容易卡在浏览器安全审批上，务必先读 [references/browser-history.md](references/browser-history.md)。要点：

- 读取浏览器历史 `browser.user.history()` 会触发审批，需要 node_repl 的 `createElicitation` 能力；MCP 客户端必须在 initialize 时声明 `capabilities: { elicitation: {} }`，否则审批通道不可用。
- 审批请求以 `elicitation/create` 消息到达客户端，需要回复 `accept` 才能继续；仅在用户本次任务明确要求读取其数据时代为接受。
- 环境变量需要 `CODEX_CLI_PATH`、`SKY_CUA_NATIVE_PIPE`/`SKY_CUA_NATIVE_PIPE_DIRECTORY`，以及正确的 `x-codex-turn-metadata`（`session_id`/`turn_id`/`thread_id`，从 `~/.codex/sessions/.../rollout-*.jsonl` 取最新值）。
- node_repl 内核写文件常被沙箱拒绝（EPERM）：让外层 MCP 客户端把结果写入文件，不要在内核里写。
- PowerShell 重定向 `*>` 会把长行截断/转码：优先让客户端直接写文件，或按 UTF-16 解码并去掉行内换行再解析。

## 报告生成

### 输入格式

`scripts/build_report.py` 接受多种记录格式的 JSON 数组（可混合）。视频/图文平台可直接复用现有字段；音乐、小说等平台应尽量补充 `content_type`、`creator`、`source_device`、`source_channel` 等字段，脚本暂未使用的字段也要保留在原始数据里，方便后续扩展。

**浏览器历史格式**（来自 `browser.user.history()`）：
```json
[{"url": "https://www.bilibili.com/video/BV1xxxx", "title": "视频标题", "dateVisited": "2026-08-05T10:02:36.204Z"}]
```

**平台账号历史格式**（来自 B站观看历史页 DOM）：
```json
[{"bv": "BV1xxxx", "group": "今天", "title": "视频标题", "up": "UP主名", "time_str": "今天23:13", "progress": "00:02/03:02"}]
```

**通用内容消费格式**（来自音乐、小说、播客、App 导出或手动记录）：
```json
[{"url": "https://music.163.com/song?id=123", "title": "歌曲名", "creator": "歌手名", "content_type": "music", "source_device": "phone", "source_channel": "account_history", "dateVisited": "2026-08-05T10:02:36.204Z"}]
```

### 用法

```bash
python scripts/build_report.py input.json -o report.html --platform bilibili --range "2026-07-31..2026-08-07"
```

详细参数与模板定制见 [references/report.md](references/report.md)。

## 平台数据源

- **B站**：优先用账号观看历史页 `https://www.bilibili.com/history`（跨设备同步，含手机 App），解析 `.history-timeline-item` 下的卡片。详见 [references/platforms.md](references/platforms.md)。
- **抖音 / 小红书 / 快手 / 微博等**：网页版无统一公开历史接口，主要依赖浏览器历史；部分平台个人中心有浏览记录页。详见 [references/platforms.md](references/platforms.md)。
- **网易云音乐 / QQ 音乐 / Spotify 等**：优先用账号播放历史、最近播放、歌单、年度报告、平台数据导出；PC 浏览器历史只能证明网页访问，不能代表 App 内收听。
- **番茄小说 / 起点 / 微信读书等**：优先用账号阅读历史、书架、最近阅读、阅读时长或平台数据导出；浏览器历史只能覆盖网页阅读。
- **浏览器历史兜底**：`browser.user.history({from, to, queries, limit})` 可覆盖网页访问，但只包含对应设备的浏览器记录，不能覆盖手机/平板 App 内行为。

## 提示

- 数据只来自用户授权范围内：读取用户自己的浏览/观看记录前，先确认用户在本次请求中明确要求了这些数据。
- 手机和平板 App 数据通常要通过平台账号同步历史、App 内历史页、平台数据导出、截图/OCR 或用户手动导出才能拿到；浏览器历史不含 App 内观看、收听或阅读。
- 浏览历史只有打开时间，无法精确统计观看/收听/阅读时长；报告以记录条数 + 时段活跃度为主，并在报告中注明口径。
