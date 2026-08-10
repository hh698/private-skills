# -*- coding: utf-8 -*-
"""Build a self-contained HTML usage report from platform history records.

Input: JSON array of records. Supports mixed platform records:
  - browser history: {"url", "title", "dateVisited"} (ISO8601 UTC)
  - account history: {"bv"/"url", "group", "title", "up", "time_str", "progress"}
  - generic content history: {"title", "creator", "content_type", "source_device", "source_channel", "dateVisited"}
Output: a single dark-themed HTML file with KPI cards, domain bars, day/hour
charts, top creators, and a sample detail table.

Usage:
  python build_report.py input.json -o report.html
    [--platform bilibili] [--range 2026-07-31..2026-08-07] [--summary "text"]
    [--title "我的 B 站一周使用报告"] [--subtitle "..."]
"""

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

try:
    from classify import classify
except ImportError:
    sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__ else __file__.rsplit("/", 1)[0])
    from classify import classify


def parse_ts(s):
    """Parse ISO8601 timestamp to local-time datetime, or None."""
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo:
            dt = dt.astimezone(timezone(timedelta(hours=8)))
            dt = dt.replace(tzinfo=None)
        return dt
    except Exception:
        return None


def parse_time_str(s, today=None):
    """Parse account-history time strings like 今天23:13 / 昨天21:41 / 08-05 20:00."""
    if not s:
        return None
    today = today or datetime(2026, 8, 7)
    m = re.match(r"今天(\d{1,2}):(\d{2})", s)
    if m:
        return today.replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0)
    m = re.match(r"昨天(\d{1,2}):(\d{2})", s)
    if m:
        return (today - timedelta(days=1)).replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0)
    m = re.match(r"(\d{2})-(\d{2}) (\d{1,2}):(\d{2})", s)
    if m:
        return datetime(2026, int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)))
    return None


def normalize(records):
    """Normalize mixed record shapes into a common list of dicts."""
    out = []
    for r in records:
        url = r.get("url") or ""
        title = (r.get("title") or "").strip()
        dt = parse_ts(r.get("dateVisited")) or parse_time_str(r.get("time_str"))
        if not title:
            continue
        bv = r.get("bv") or (re.search(r"BV[0-9A-Za-z]{10}", url).group(0) if re.search(r"BV[0-9A-Za-z]{10}", url) else None)
        up = (r.get("up") or r.get("creator") or r.get("artist") or r.get("author") or r.get("主播") or "").strip()
        if not up and "|" in title:
            # account-history fullText style: progress | title | up | time
            parts = [p.strip() for p in title.split("|")]
            if len(parts) >= 3 and len(parts[-2]) <= 30:
                up = parts[-2]
                title = parts[-3]
        classify_text = " ".join(str(r.get(k) or "") for k in [
            "title", "creator", "artist", "author", "album", "book", "chapter", "tags", "content_type"
        ]).strip() or title
        out.append({
            "url": url,
            "bv": bv,
            "title": title,
            "classify_text": classify_text,
            "up": up,
            "dt": dt,
            "progress": r.get("progress") or "",
        })
    return out


def domain_palette():
    return [
        "#FB7299", "#F9844A", "#00A1D6", "#90BE6D", "#9B5DE5", "#F9C74F",
        "#4CC3E8", "#6D8BFF", "#FF8FA3", "#B07CE8", "#8A8FA3", "#5FB0A8",
        "#E8A838", "#E56B9A", "#7E8CE0", "#58C4A8", "#555c6e",
    ]


def build_html(entries, platform, range_label, summary, title, subtitle, dedup=True):
    # dedupe by bv/url
    seen = set()
    uniq = []
    for e in entries:
        key = e["bv"] or e["url"]
        if dedup and key and key in seen:
            continue
        if key:
            seen.add(key)
        uniq.append(e)
    entries = uniq

    total = len(entries)
    domains = Counter(classify(e.get("classify_text") or e["title"]) for e in entries)
    days = Counter((e["dt"].date().isoformat() if e["dt"] else "") for e in entries if e["dt"])
    hours = Counter((e["dt"].hour if e["dt"] else -1) for e in entries)
    ups = Counter(e["up"] for e in entries if e["up"])

    domain_rows = ""
    dm = max(domains.values()) if domains else 1
    pal = domain_palette()
    for i, (name, cnt) in enumerate(domains.most_common()):
        pct = round(cnt / total * 100) if total else 0
        w = max(4, round(cnt / dm * 100))
        c = pal[i % len(pal)]
        domain_rows += (
            f'<div class="bar-row"><div class="bar-label">{name}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{w}%;background:{c}">{cnt}</div></div>'
            f'<div class="bar-pct">{pct}%</div></div>'
        )

    day_cells = ""
    if days:
        dmday = max(days.values())
        for d in sorted(days):
            h = round(days[d] / dmday * 100) if dmday else 0
            day_cells += (
                f'<div class="day-cell"><div class="d">{d[5:].replace("-", "/")}</div>'
                f'<div class="n">{days[d]}</div><div class="bar-mini"><i style="width:{h}%"></i></div></div>'
            )

    hour_cells = ""
    if hours:
        mh = max(hours.values())
        for i in range(24):
            h = hours.get(i, 0)
            pct = round(h / mh * 100) if mh else 0
            hour_cells += (
                f'<div class="hour-cell"><div class="box"><i style="height:{pct}%"></i></div>'
                f'<div class="t">{i:02d}</div></div>'
            )

    up_rows = ""
    if ups:
        mu = max(ups.values())
        upc = ["#FB7299", "#00A1D6", "#F9C74F", "#90BE6D", "#F9844A", "#9B5DE5", "#4CC3E8", "#FF8FA3"]
        for i, (name, cnt) in enumerate(ups.most_common(12)):
            w = max(8, round(cnt / mu * 100))
            c = upc[i % len(upc)]
            up_rows += (
                f'<div class="up"><div class="avatar" style="background:linear-gradient(135deg,{c},#333)">{name[0]}</div>'
                f'<div style="flex:1"><div class="name">{name}</div>'
                f'<div class="bar-track" style="height:8px;margin-top:4px">'
                f'<div class="bar-fill" style="width:{w}%;background:{c};font-size:10px">{cnt}</div></div></div></div>'
            )

    sample_rows = ""
    for e in sorted(entries, key=lambda x: x["dt"] or datetime.min, reverse=True)[:12]:
        ts = e["dt"].strftime("%m/%d %H:%M") if e["dt"] else "-"
        dom = classify(e["title"])
        c = pal[list(domains).index(dom) % len(pal)] if dom in domains else "#555c6e"
        sample_rows += (
            f"<tr><td style=\"white-space:nowrap\">{ts}</td><td>{e['title'][:80]}</td>"
            f"<td><span class=\"tag\" style=\"background:{c}\">{dom}</span></td>"
            f"<td style=\"color:var(--muted)\">{e['up'] or '-'}</td></tr>"
        )

    active_days = len(days)
    peak_hour = max(hours, key=hours.get) if hours else "-"
    top_up = ups.most_common(1)[0] if ups else "-"
    top_up_name = top_up[0] if top_up != "-" else "-"
    top_up_cnt = top_up[1] if top_up != "-" else ""

    summary_html = ""
    if summary:
        summary_html = (
            f'<div class="summary"><h2>🎯 该账号喜欢看的视频类型（简短解读）</h2><p>{summary}</p></div>'
        )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
:root {{ --pink:#FB7299; --blue:#00A1D6; --bg:#0f1117; --card:#1a1d27; --card2:#222633;
 --text:#e8eaf0; --muted:#9aa0b0; --border:#2c3140; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:"PingFang SC","Microsoft YaHei","Noto Sans SC",sans-serif; background:var(--bg);
 color:var(--text); line-height:1.6; padding:24px; }}
.wrap {{ max-width:1180px; margin:0 auto; }}
header {{ display:flex; align-items:center; gap:14px; margin-bottom:8px; }}
.logo {{ width:44px; height:44px; border-radius:12px; background:linear-gradient(135deg,var(--pink),var(--blue));
 display:flex; align-items:center; justify-content:center; font-size:24px; color:#fff; flex-shrink:0; }}
h1 {{ font-size:26px; font-weight:700; }}
.subtitle {{ color:var(--muted); font-size:14px; margin-bottom:20px; }}
.kpis {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:18px; }}
.kpi {{ background:var(--card); border:1px solid var(--border); border-radius:14px; padding:16px 18px; }}
.kpi .label {{ color:var(--muted); font-size:13px; }}
.kpi .value {{ font-size:26px; font-weight:700; margin-top:2px; }}
.kpi .hint {{ font-size:12px; color:var(--muted); margin-top:2px; }}
.grid {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-bottom:18px; }}
.card {{ background:var(--card); border:1px solid var(--border); border-radius:14px; padding:18px; }}
.card h2 {{ font-size:16px; margin-bottom:14px; }}
.full {{ grid-column:1/-1; }}
.bar-row {{ display:flex; align-items:center; gap:10px; margin-bottom:9px; }}
.bar-label {{ width:150px; font-size:13px; color:var(--muted); text-align:right; flex-shrink:0; }}
.bar-track {{ flex:1; height:22px; background:var(--card2); border-radius:6px; overflow:hidden; }}
.bar-fill {{ height:100%; border-radius:6px; min-width:2px; display:flex; align-items:center;
 justify-content:flex-end; padding-right:8px; font-size:12px; font-weight:600; color:#fff; }}
.bar-pct {{ width:46px; font-size:13px; text-align:right; }}
.day-grid {{ display:grid; grid-template-columns:repeat(7,1fr); gap:8px; }}
.day-cell {{ background:var(--card2); border-radius:10px; padding:10px 6px; text-align:center; }}
.day-cell .d {{ font-size:12px; color:var(--muted); }}
.day-cell .n {{ font-size:20px; font-weight:700; margin-top:4px; }}
.day-cell .bar-mini {{ height:4px; border-radius:2px; margin-top:8px; background:var(--border); }}
.day-cell .bar-mini i {{ display:block; height:100%; border-radius:2px; background:var(--pink); }}
.hour-grid {{ display:grid; grid-template-columns:repeat(12,1fr); gap:6px; }}
.hour-cell {{ text-align:center; }}
.hour-cell .box {{ height:44px; border-radius:6px; background:var(--card2);
 display:flex; align-items:flex-end; overflow:hidden; }}
.hour-cell .box i {{ display:block; width:100%; background:var(--blue); border-radius:4px 4px 0 0; }}
.hour-cell .t {{ font-size:10px; color:var(--muted); margin-top:4px; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th {{ text-align:left; color:var(--muted); font-weight:500; padding:8px 10px;
 border-bottom:1px solid var(--border); }}
td {{ padding:9px 10px; border-bottom:1px solid #242836; vertical-align:top; }}
.tag {{ display:inline-block; padding:2px 10px; border-radius:20px; font-size:12px; font-weight:600; color:#fff; }}
.up {{ display:flex; align-items:center; gap:10px; margin-bottom:12px; }}
.up .avatar {{ width:40px; height:40px; border-radius:50%; flex-shrink:0; display:flex;
 align-items:center; justify-content:center; font-size:18px; font-weight:700; color:#fff; }}
.up .name {{ font-weight:600; font-size:15px; }}
.note {{ font-size:12px; color:var(--muted); background:var(--card2); border-radius:10px;
 padding:12px 14px; margin-top:14px; }}
.summary {{ background:linear-gradient(135deg,rgba(251,114,153,.12),rgba(0,161,214,.12));
 border:1px solid rgba(251,114,153,.35); border-radius:14px; padding:18px 20px; margin-bottom:18px; }}
.summary h2 {{ font-size:17px; margin-bottom:8px; color:var(--pink); }}
.summary p {{ font-size:14px; line-height:1.8; }}
.footer {{ text-align:center; color:#666e80; font-size:12px; margin-top:20px; }}
@media (max-width:800px) {{ .kpis {{ grid-template-columns:repeat(2,1fr); }} .grid {{ grid-template-columns:1fr; }}
 .hour-grid {{ grid-template-columns:repeat(6,1fr); }} .day-grid {{ grid-template-columns:repeat(4,1fr); }}
 .bar-label {{ width:110px; }} }}
</style>
</head>
<body>
<div class="wrap">
  <header><div class="logo">{platform}</div>
    <div><h1>{title}</h1><div class="subtitle">{subtitle} · 数据范围：{range_label}</div></div>
  </header>
  <div class="kpis">
    <div class="kpi"><div class="label">观看 / 访问记录</div><div class="value">{total} <small>条</small></div>
      <div class="hint">去重后计数</div></div>
    <div class="kpi"><div class="label">活跃天数</div><div class="value">{active_days} <small>天</small></div>
      <div class="hint">有记录的天数</div></div>
    <div class="kpi"><div class="label">最活跃时段</div><div class="value" style="font-size:22px">{peak_hour} 点</div>
      <div class="hint">按记录条数</div></div>
    <div class="kpi"><div class="label">最常消费创作者</div><div class="value" style="font-size:20px">{top_up_name}</div>
      <div class="hint">{top_up_cnt} 次</div></div>
  </div>
  {summary_html}
  <div class="grid">
    <div class="card"><h2>📊 内容类型分布</h2><div id="domainBars">{domain_rows}</div>
      <div class="note">类型按标题关键词自动归类；「其他」包含难以归类的短内容。</div></div>
    <div class="card"><h2>📅 每日活跃</h2><div class="day-grid">{day_cells}</div></div>
  </div>
  <div class="grid">
    <div class="card"><h2>🕐 时段分布（小时）</h2><div class="hour-grid">{hour_cells}</div></div>
    <div class="card"><h2>⭐ 常消费创作者 TOP</h2>{up_rows}</div>
  </div>
  <div class="card full"><h2>📋 消费抽样（代表性内容）</h2>
    <div style="overflow-x:auto"><table><thead><tr><th>时间</th><th>内容</th><th>类型</th><th>创作者</th></tr></thead>
    <tbody>{sample_rows}</tbody></table></div>
  </div>
  <div class="card full"><h2>ℹ️ 数据说明</h2>
    <div class="note">数据来源：浏览器历史 / 平台账号历史 / App 历史 / 数据导出 / 手动记录等用户授权数据。
    浏览器历史只记录网页打开时间，无法精确统计实际观看、收听或阅读时长，本报告以记录条数与时段活跃度为主。</div>
  </div>
  <div class="footer">由 Codex 根据用户授权数据自动生成 · 仅供个人使用分析</div>
</div>
</body>
</html>"""
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="JSON file with history records")
    ap.add_argument("-o", "--output", default="report.html")
    ap.add_argument("--platform", default="B站")
    ap.add_argument("--range", default="自定义区间")
    ap.add_argument("--summary", default="")
    ap.add_argument("--title", default="我的媒体使用报告")
    ap.add_argument("--subtitle", default="基于浏览与观看记录生成")
    ap.add_argument("--no-dedup", action="store_true")
    args = ap.parse_args()

    records = json.load(open(args.input, encoding="utf-8"))
    entries = normalize(records)
    html = build_html(
        entries,
        platform=args.platform,
        range_label=args.range,
        summary=args.summary,
        title=args.title,
        subtitle=args.subtitle,
        dedup=not args.no_dedup,
    )
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"OK: {len(entries)} entries -> {args.output}")


if __name__ == "__main__":
    main()
