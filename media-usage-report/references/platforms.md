# 平台与数据源

按平台和设备选择最完整的数据源。优先级：平台账号同步历史 / 平台数据导出 > App 内历史页截图或手动导出 > PC/平板浏览器历史。

不要把“某个渠道没有记录”解释成“用户没有消费”。浏览器历史只覆盖对应设备上的网页访问；手机、平板、桌面客户端或 App 内行为通常要靠账号历史、导出包、截图/OCR、系统屏幕使用时间或用户手动记录补齐。

## B站（哔哩哔哩）

**首选：账号观看历史页** `https://www.bilibili.com/history`

- 跨设备同步：包含手机 App、桌面浏览器、客户端的所有观看记录，是唯一能覆盖手机端的数据源。
- 需要登录态（浏览器已登录 B站 账号）。
- 页面按「今天 / 昨天 / 近一周」分组；滚动到底部可加载更多，多滚几次以覆盖目标周期。
- DOM 解析要点（用 Playwright `evaluate`）：
  - 分组：`.history-timeline-item`，组名在 `.section-title`
  - 卡片：组内的 `.history-card` 或 `.bili-video-card`
  - 链接：`a[href*='/video/']`，从中提取 `BV[0-9A-Za-z]{10}`
  - 标题：卡片内 `img[alt]` 最可靠
  - 进度：`.bili-cover-card__stat span`（如 `00:02/03:02` 或「已看完」）
  - 完整文本：`card.innerText`，格式通常为 `进度 | 标题 | UP主 | 时间`
- 页面 URL 会重定向到 `https://www.bilibili.com/history`（`/account/history` 也可用）。
- 单页记录多时去重以 BV 号为准；同一 BV 可能因播放页跳转出现多条，保留一条即可。

## 抖音 / 小红书 / 快手 / 微博

这些平台没有公开的、可跨设备同步的观看历史网页接口，主要数据来源是浏览器历史：

- 抖音：视频页 URL 形如 `https://www.douyin.com/video/7xxxx`，标题含作者与文案。
- 小红书：笔记页 URL 形如 `https://www.xiaohongshu.com/explore/6xxxx` 或 `discovery/item/6xxxx`，标题即笔记标题。
- 快手：`https://www.kuaishou.com/short-video/3xxxx`。
- 微博：`https://weibo.com/tv/show/...` 或正文页。
- 部分平台个人中心有「浏览记录」页面，但通常只展示少量最近记录且仅限登录后的网页会话，可作为补充。

分类时同样用 `scripts/classify.py`；注意小红书标题常含「种草 / 测评 / 教程」等词，抖音标题常含话题标签（`#xxx`），可先清理话题标签再分类。

## 音乐 / 播客平台

适用于网易云音乐、QQ 音乐、酷狗、Apple Music、Spotify、小宇宙、喜马拉雅等。

- 优先来源：账号播放历史、最近播放、收听报告、歌单、收藏、平台个人数据导出。
- 网页历史只能证明用户访问过歌曲、专辑、歌单或播客页面，不能覆盖 App 内播放，也不能可靠表示完整收听。
- 记录字段建议保留：`title`（歌曲/节目名）、`creator`（歌手/主播/播客名）、`album`、`content_type`（`music` / `podcast` / `audio`）、`progress` 或 `duration`、`source_device`、`source_channel`。
- 网易云音乐常见网页 URL：`music.163.com/song?id=...`、`/album?id=...`、`/playlist?id=...`、`/program?id=...`。

## 小说 / 阅读平台

适用于番茄小说、起点中文网、微信读书、晋江文学城、掌阅等。

- 优先来源：账号阅读历史、最近阅读、书架、阅读时长统计、阅读报告、平台个人数据导出。
- App 内阅读通常不会出现在浏览器历史里；如果没有导出能力，可让用户提供截图、CSV、复制文本或手动整理表。
- 记录字段建议保留：`title`（书名或章节名）、`creator`（作者）、`book`、`chapter`、`content_type`（`novel` / `book` / `article`）、`progress`、`source_device`、`source_channel`。
- 番茄小说、起点、微信读书的网页 URL 可作为辅助证据，但不能替代 App 阅读历史。

## YouTube / 其他外网平台

- 仅浏览器历史可覆盖；`queries` 用域名关键词（如 `youtube.com`）。
- 标题即视频标题，分类规则通用。
- 如果平台账号提供观看历史或数据导出，优先使用账号数据，浏览器历史作为补充。

## 浏览器历史（兜底）

`browser.user.history({ from, to, queries, limit })` 返回 `{url, title, dateVisited}`。

- 覆盖网页访问，但只含当前浏览器所在设备的记录；App 内观看、收听、阅读不会出现。
- 用 `queries` 过滤目标平台域名，或拉取全量后自行过滤。
- 时间用 ISO8601 UTC，转换到本地时区（如 Asia/Shanghai, UTC+8）再统计。
- 该调用需要用户审批，见 [browser-history.md](browser-history.md)。
