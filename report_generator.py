"""
日报生成器 - 从爬取数据生成 Markdown 日报
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime, date, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent))
from models import OperaHouse, Performance


def load_houses(raw_dir: str = "data/raw") -> list[OperaHouse]:
    """从 JSON 目录加载所有歌剧院数据"""
    houses = []
    summary_path = os.path.join(raw_dir, "_summary.json")
    if not os.path.exists(summary_path):
        print(f"[Report] No summary file at {summary_path}")
        return houses

    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    for h in summary.get("houses", []):
        if h.get("status") != "success":
            continue
        hp = os.path.join(raw_dir, f"{h['id']}.json")
        if os.path.exists(hp):
            try:
                house = OperaHouse.load_json(hp)
                houses.append(house)
            except Exception as e:
                print(f"[Report] Error loading {hp}: {e}")

    return houses


def load_summary(raw_dir: str = "data/raw") -> dict:
    """加载爬取摘要"""
    summary_path = os.path.join(raw_dir, "_summary.json")
    if os.path.exists(summary_path):
        with open(summary_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def generate_daily_report(results: list[dict] = None) -> str:
    """生成日报 Markdown 文件"""
    raw_dir = "data/raw"
    output = "docs/daily"
    os.makedirs(output, exist_ok=True)

    houses = load_houses(raw_dir)
    summary = load_summary(raw_dir)
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    week_from_now = today + timedelta(days=7)

    # Build report
    lines = []
    lines.append(f"# 🎭 全球歌剧院演出日报")
    lines.append(f"")
    lines.append(f"> **{today.strftime('%Y年%m月%d日')}**  |  涵盖 {len(houses)} 家歌剧院")
    lines.append(f"> 每日自动更新 · [数据来源](https://github.com/lishw/opera-daily)")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # Section 1: 今日/本周上演
    lines.append(f"## 📅 近期上演剧目")
    lines.append(f"")
    # Filter performances happening in the next 7 days
    upcoming = []
    for house in houses:
        for p in house.performances:
            try:
                pd_str = p.date[:10] if p.date else ""
                if pd_str:
                    pd = datetime.strptime(pd_str, "%Y-%m-%d").date()
                    if today <= pd <= week_from_now:
                        upcoming.append((house, p))
            except (ValueError, IndexError):
                continue

    upcoming.sort(key=lambda x: x[1].date)

    if upcoming:
        current_date = ""
        for house, p in upcoming:
            d = p.date[:10] if len(p.date) >= 10 else p.date
            if d != current_date:
                lines.append(f"### {d}")
                lines.append(f"")
                current_date = d

            # Emoji per venue
            venue_icon = "🏛️"
            if "bastille" in p.venue.lower():
                venue_icon = "🏗️"
            elif "garnier" in p.venue.lower():
                venue_icon = "✨"

            cast_info = ""
            if p.conductors:
                names = ", ".join(c.name for c in p.conductors[:2])
                cast_info = f" 🎵 指挥: {names}"
            if p.directors:
                names = ", ".join(c.name for c in p.directors[:2])
                cast_info += f" 🎬 导演: {names}"

            composer_info = f" — *{p.composer}*" if p.composer else ""
            venue_name = f" @ {p.venue}" if p.venue else ""
            time_info = f" ⏰ {p.time}" if p.time else ""

            lines.append(f"- **{p.title}**{composer_info}{venue_name}{time_info}{cast_info}")
            if p.description and len(p.description) > 10:
                lines.append(f"  - {p.description[:120]}...")
            lines.append(f"")
    else:
        lines.append(f"暂无近7天演出的详细数据")
        lines.append(f"")

    # Section 2: 各家歌剧院汇总
    lines.append(f"## 🏛️ 各剧院演出排期一览")
    lines.append(f"")
    for house in houses:
        name = house.name
        city = house.city
        country = house.country
        perf_count = len(house.performances)
        flag = _get_country_flag(country)
        lines.append(f"### {flag} {name} (*{city}*)")
        lines.append(f"")
        lines.append(f"近期共 <b>{perf_count}</b> 场演出")
        lines.append(f"")

        # Group by month
        perfs_by_month = {}
        for p in house.performances:
            try:
                month_key = p.date[:7] if len(p.date) >= 7 else "未知"
            except:
                month_key = "未知"
            perfs_by_month.setdefault(month_key, []).append(p)

        for month in sorted(perfs_by_month.keys()):
            month_perfs = perfs_by_month[month]
            lines.append(f"<details>")
            lines.append(f"<summary><b>{month}</b> ({len(month_perfs)} 场)</summary>")
            lines.append(f"")
            lines.append(f"| 日期 | 剧目 | 作曲家 | 时间 | 场地 |")
            lines.append(f"|------|------|--------|------|------|")
            for p in month_perfs:
                d = p.date[:10] if len(p.date) >= 10 else (p.date or "-")
                t = p.time or "-"
                v = p.venue[:20] if p.venue else "-"
                composer_short = p.composer[:15] + "..." if len(p.composer) > 15 else (p.composer or "-")
                lines.append(f"| {d} | {p.title} | {composer_short} | {t} | {v} |")
            lines.append(f"")
            lines.append(f"</details>")
            lines.append(f"")

    # Section 3: 重要艺术家动态
    lines.append(f"## ⭐ 艺术家动态")
    lines.append(f"")
    artists_seen = set()
    artist_lines = []
    for house in houses:
        for p in house.performances:
            for cond in p.conductors:
                key = f"{cond.name}|{house.name}"
                if key not in artists_seen:
                    artists_seen.add(key)
                    artist_lines.append(f"- 🎵 **{cond.name}** — 指挥 *{p.title}* @ {house.name} ({p.date[:10]})")
            for dir_ in p.directors:
                key = f"{dir_.name}|{house.name}"
                if key not in artists_seen:
                    artists_seen.add(key)
                    artist_lines.append(f"- 🎬 **{dir_.name}** — 导演 *{p.title}* @ {house.name} ({p.date[:10]})")
            for cast_member in p.cast[:3]:  # Limit to 3 per performance
                key = f"{cast_member.name}|{house.name}|{p.title}"
                if key not in artists_seen and cast_member.role:
                    artists_seen.add(key)
                    artist_lines.append(f"- 🎤 **{cast_member.name}** — {cast_member.role} in *{p.title}* @ {house.name}")

    if artist_lines:
        lines.extend(artist_lines[:30])  # Cap at 30 entries
        if len(artist_lines) > 30:
            lines.append(f"- ... 及另外 {len(artist_lines) - 30} 位艺术家")
    else:
        lines.append(f"（暂无详细艺术家数据）")
    lines.append(f"")

    # Section 4: 统计信息
    lines.append(f"## 📊 统计概览")
    lines.append(f"")
    total = summary.get("total_performances", sum(len(h.performances) for h in houses))
    success = summary.get("success_count", len(houses))
    total_h = summary.get("total_houses", len(houses))
    update_time = summary.get("updated_at", "")

    lines.append(f"| 指标 | 数值 |")
    lines.append(f"|------|------|")
    lines.append(f"| 覆盖歌剧院 | {success}/{total_h} |")
    lines.append(f"| 总演出数 | {total} |")
    lines.append(f"| 最近更新 | {update_time[:19]} |")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"*本日报由 [Opera Daily](https://github.com/lishw/opera-daily) 自动生成 · "
                 f"数据仅供参考，请以各剧院官网为准*")
    lines.append(f"")

    content = "\n".join(lines)

    # Write to file
    filename = f"opera-daily-{today_str}.md"
    filepath = os.path.join(output, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    # Also update latest.md (for GitHub Pages)
    latest_path = os.path.join(output, "latest.md")
    with open(latest_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[Report] ✅ 日报已生成: {filepath}")
    print(f"[Report] ✅ 最新版: {latest_path}")
    return filepath


def _get_country_flag(country: str) -> str:
    """获取国家对应的国旗 emoji"""
    flag_map = {
        "美国": "🇺🇸", "意大利": "🇮🇹", "奥地利": "🇦🇹",
        "法国": "🇫🇷", "英国": "🇬🇧", "德国": "🇩🇪",
        "澳大利亚": "🇦🇺", "中国": "🇨🇳", "西班牙": "🇪🇸",
        "日本": "🇯🇵", "俄罗斯": "🇷🇺",
    }
    return flag_map.get(country, "🌍")


if __name__ == "__main__":
    generate_daily_report()