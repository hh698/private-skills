# 报告生成与定制

`scripts/build_report.py` 生成深色主题、自包含（无外部依赖）的单文件 HTML，离线可打开。

## 基本用法

```bash
python scripts/build_report.py history.json -o media-report.html \
  --platform "B站" --range "2026-07-31..2026-08-07" \
  --title "我的 B 站一周使用报告" --subtitle "统计范围：最近一周"
```

## 参数

| 参数 | 说明 |
|---|---|
| `input` | JSON 数组文件（多种记录格式可混合，见 SKILL.md） |
| `-o / --output` | 输出 HTML 路径，默认 `report.html` |
| `--platform` | 平台名或平台集合名，用于 logo 圆标（如 B站 / 抖音 / 小红书 / 网易云音乐 / 番茄小说 / 综合内容消费） |
| `--range` | 数据范围文案，显示在副标题 |
| `--summary` | 偏好总结文字（3–5 句），渲染为页面顶部解读卡片 |
| `--title` | 页面标题 |
| `--subtitle` | 副标题 |
| `--no-dedup` | 不去重（默认按 BV/URL 去重） |

## 报告内容

- KPI 卡片：记录条数、活跃天数、最活跃时段、最常消费的创作者/歌手/作者
- 内容类型分布（横向条形图，按 `classify.py` 归类）
- 每日活跃（柱状日历）
- 时段分布（24 小时热力条）
- 常消费创作者 TOP 12
- 消费抽样明细表（按时间倒序前 12 条）
- 数据说明与口径提示

音乐、小说、播客等非视频字段（如 `content_type`、`creator`、`album`、`book`、`source_device`、`source_channel`）应保留在输入数据中；当前报告会优先使用通用标题和创作者字段，更多专用维度可在后续脚本扩展时接入。

## 定制模板

页面样式集中在 `build_html()` 内的 `<style>`；如需品牌色或布局调整，直接修改该函数。
报告应保持单文件、离线可用；不要引入 CDN 依赖（用户环境可能无法访问外网资源）。

## 交付

- 文件名建议 `media-usage-report.html` 或按平台命名（如 `bilibili-usage-report.html`）。
- 生成后可在浏览器中本地打开验证渲染（如用 `file://` 或本地 HTTP 服务 + 浏览器截图/DOM 检查）。
- 可选发布到 Netlify，见 [deploy.md](deploy.md)。
