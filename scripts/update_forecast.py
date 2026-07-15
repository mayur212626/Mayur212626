#!/usr/bin/env python3
"""Sync the Live Forecast section of the profile README with the latest
World Cup 2026 odds from fifa-wc2026-predictor. Falls back gracefully:
tries FORECAST_API_URL (if set) -> repo CSV."""
import csv, io, json, os, re, sys, urllib.request
from datetime import datetime, timezone

CSV_URL = os.environ.get(
    "FORECAST_CSV_URL",
    "https://raw.githubusercontent.com/mayur212626/fifa-wc2026-predictor/main/reports/simulation_2026.csv",
)
API_URL = os.environ.get("FORECAST_API_URL", "")
README = os.environ.get("README_PATH", "README.md")
TOP_N = int(os.environ.get("FORECAST_TOP_N", "8"))
START, END = "<!--FORECAST:START-->", "<!--FORECAST:END-->"
REPO = "https://github.com/mayur212626/fifa-wc2026-predictor"
DASH = "https://wc2026-title-race.onrender.com"


def fetch_rows():
    if API_URL:
        try:
            with urllib.request.urlopen(API_URL, timeout=30) as r:
                data = json.load(r)
            rows = [
                {"team": d["team"], "sf": float(d.get("sf", 0)),
                 "final": float(d.get("final", 0)),
                 "champion": float(d.get("champion", d.get("win", 0)))}
                for d in data
            ]
            if rows:
                print(f"Fetched {len(rows)} teams from API")
                return rows
        except Exception as e:
            print("API fetch failed, falling back to CSV:", e)
    with urllib.request.urlopen(CSV_URL, timeout=30) as r:
        text = r.read().decode("utf-8")
    rows = [
        {"team": rec["team"], "sf": float(rec["sf"]),
         "final": float(rec["final"]), "champion": float(rec["champion"])}
        for rec in csv.DictReader(io.StringIO(text))
    ]
    print(f"Fetched {len(rows)} teams from CSV")
    return rows


def bar(pct, leader, width=10):
    filled = max(1, round(pct / leader * width)) if leader > 0 else 0
    return "█" * filled + "░" * (width - filled)


def build_section(rows):
    rows = sorted(rows, key=lambda r: r["champion"], reverse=True)[:TOP_N]
    leader = rows[0]["champion"] if rows else 1
    ts = datetime.now(timezone.utc).strftime("%b %d, %Y · %H:%M UTC")
    lines = [
        "<div align=\"center\">",
        "",
        "| # | Team | Semis | Final | 🏆 Title odds |",
        "|:-:|:-----|:-----:|:-----:|:--------------|",
    ]
    for i, r in enumerate(rows, 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, str(i))
        lines.append(
            f"| {medal} | **{r['team']}** | {r['sf']:.1f}% | {r['final']:.1f}% "
            f"| `{bar(r['champion'], leader)}` **{r['champion']:.1f}%** |"
        )
    lines += [
        "",
        f"*Last synced: **{ts}** · refreshed automatically by GitHub Actions · "
        f"5,000 Monte Carlo simulations per run*",
        "",
        f"[**Model & code**]({REPO}) · [**Live dashboard**]({DASH})",
        "",
        "</div>",
    ]
    return "\n".join(lines)


def main():
    with open(README, encoding="utf-8") as f:
        content = f.read()
    if START not in content or END not in content:
        sys.exit(f"Markers {START} / {END} not found in {README}")
    section = f"{START}\n{build_section(fetch_rows())}\n{END}"
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: section, content, flags=re.S)
    with open(README, "w", encoding="utf-8") as f:
        f.write(new)
    print("README forecast section updated")


if __name__ == "__main__":
    main()
