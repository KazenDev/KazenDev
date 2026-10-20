#!/usr/bin/env python3
"""Regenera assets/activity.svg con los datos reales de GitHub."""
import base64
import json
import os
import sys
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "assets/fonts"
OUT = ROOT / "assets" / "activity.svg"

LOGIN = os.environ.get("GH_LOGIN", "KazenDev")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

DISPLAY = "'Space Grotesk', 'Segoe UI', Helvetica, Arial, sans-serif"
CYAN = "#33D5FF"
BLUE = "#1F6FEB"
BG = "#0D1117"
BORDER = "#21262D"
MUTED = "#8B949E"
LEVELS = ["#1B232E", "#0E3B4A", "#116B85", "#1FA3C4", "#33D5FF"]
MONTHS = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalRepositoryContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def fetch() -> dict:
    if not TOKEN:
        sys.exit("Falta GH_TOKEN (PAT con scope read:user).")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if "errors" in payload:
        sys.exit(f"GraphQL: {payload['errors']}")
    return payload["data"]["user"]["contributionsCollection"]


def b64(name: str) -> str:
    return base64.b64encode((FONTS / name).read_bytes()).decode()


def level(count: int) -> int:
    if count <= 0:
        return 0
    if count <= 2:
        return 1
    if count <= 8:
        return 2
    if count <= 20:
        return 3
    return 4


def build(data: dict) -> str:
    cal = data["contributionCalendar"]
    weeks = cal["weeks"]
    total = cal["totalContributions"]

    x0, y0, pitch, size = 110, 178, 20, 16
    cells, month_labels = [], []
    prev_month = None

    for wi, week in enumerate(weeks):
        month = int(week["contributionDays"][0]["date"][5:7])
        if month != prev_month:
            month_labels.append((x0 + wi * pitch, MONTHS[month - 1]))
            prev_month = month
        for day in week["contributionDays"]:
            weekday = (date.fromisoformat(day["date"]).weekday() + 1) % 7
            cells.append(
                f'<rect x="{x0 + wi * pitch}" y="{y0 + weekday * pitch}" '
                f'width="{size}" height="{size}" rx="3" '
                f'fill="{LEVELS[level(int(day["contributionCount"]))]}"/>'
            )

    months = "\n  ".join(
        f'<text x="{x}" y="{y0 - 14}" font-family="{DISPLAY}" font-size="10.5" font-weight="700" letter-spacing="1.4" fill="{MUTED}">{m}</text>'
        for x, m in month_labels
    )
    weekdays = "\n  ".join(
        f'<text x="{x0 - 14}" y="{y0 + r * pitch + 12}" text-anchor="end" font-family="{DISPLAY}" font-size="10.5" font-weight="700" letter-spacing="1.2" fill="{MUTED}">{label}</text>'
        for r, label in [(1, "LUN"), (3, "MI&#201;"), (5, "VIE")]
    )

    stats = [
        ("CONTRIBUCIONES", total),
        ("COMMITS", data["totalCommitContributions"]),
        ("PULL REQUESTS", data["totalPullRequestContributions"]),
        ("REPOS", data["totalRepositoryContributions"]),
    ]
    stat_svg = []
    for i, (label, value) in enumerate(stats):
        x = 110 + i * 275
        stat_svg.append(
            f'<text x="{x}" y="82" font-family="{DISPLAY}" font-size="40" font-weight="700" letter-spacing="0.5" fill="#FFFFFF">{value}</text>'
            f'\n  <text x="{x}" y="106" font-family="{DISPLAY}" font-size="11" font-weight="700" letter-spacing="1.8" fill="{MUTED}">{label}</text>'
        )
        if i:
            stat_svg.append(f'<rect x="{x - 30}" y="52" width="1" height="54" fill="{BORDER}"/>')

    legend_x = 1040
    legend = "\n  ".join(
        f'<rect x="{legend_x + i * 22}" y="333" width="14" height="14" rx="3" fill="{LEVELS[i]}"/>'
        for i in range(5)
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="368" viewBox="0 0 1280 368" fill="none" role="img" aria-label="Actividad de contribuciones">
  <defs>
    <style>
    @font-face {{
      font-family: 'Space Grotesk';
      font-weight: 700;
      font-style: normal;
      src: url('data:font/woff;base64,{b64("space-700.woff")}') format('woff');
    }}
    @font-face {{
      font-family: 'Space Grotesk';
      font-weight: 400;
      font-style: normal;
      src: url('data:font/woff;base64,{b64("space-400.woff")}') format('woff');
    }}
    </style>
    <linearGradient id="aline" x1="0" y1="0" x2="1280" y2="0" gradientUnits="userSpaceOnUse">
      <stop stop-color="{CYAN}" stop-opacity="0.85"/>
      <stop offset="0.45" stop-color="{BLUE}" stop-opacity="0.6"/>
      <stop offset="1" stop-color="{CYAN}" stop-opacity="0.1"/>
    </linearGradient>
    <radialGradient id="aglow" cx="0" cy="0" r="1" gradientTransform="translate(1120 10) rotate(120) scale(260 320)" gradientUnits="userSpaceOnUse">
      <stop stop-color="{CYAN}" stop-opacity="0.10"/>
      <stop offset="1" stop-color="{CYAN}" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <rect x="0.5" y="0.5" width="1279" height="367" rx="18" fill="{BG}" stroke="{BORDER}"/>
  <rect x="1" y="1" width="1278" height="367" rx="18" fill="url(#aglow)"/>
  <rect x="1" y="1" width="1278" height="3" rx="1.5" fill="url(#aline)"/>

  {chr(10).join(stat_svg)}

  {months}
  {weekdays}

  {chr(10).join(cells)}

  <text x="110" y="345" font-family="{DISPLAY}" font-size="10.5" font-weight="700" letter-spacing="2" fill="{MUTED}">&#218;LTIMOS 12 MESES</text>
  <text x="{legend_x - 16}" y="345" text-anchor="end" font-family="{DISPLAY}" font-size="10.5" font-weight="700" letter-spacing="1.4" fill="{MUTED}">MENOS</text>
  {legend}
  <text x="{legend_x + 5 * 22 + 12}" y="345" font-family="{DISPLAY}" font-size="10.5" font-weight="700" letter-spacing="1.4" fill="{MUTED}">M&#193;S</text>
</svg>
'''


def main() -> None:
    data = fetch()
    svg = build(data)
    OUT.write_text(svg, encoding="utf-8")
    cal = data["contributionCalendar"]
    print(f"OK · {cal['totalContributions']} contribuciones · {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
