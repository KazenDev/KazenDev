#!/usr/bin/env python3
"""
Regenera el panel de actividad (assets/activity.svg)
con los datos reales de GitHub, incluidas las contribuciones privadas: por eso
necesita un token de la propia cuenta (GH_TOKEN, scope read:user).

Lo ejecuta a diario .github/workflows/activity.yml. Usa el tema y las fuentes de
scripts/build_profile.py.
"""
import json
import os
import sys
import urllib.request
from datetime import date

from build_profile import MONO, SANS, ROOT, THEMES, Svg, card, heat, width

LOGIN = os.environ.get("GH_LOGIN", "KazenDev")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
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


def build(data: dict, t: dict) -> Svg:
    cal = data["contributionCalendar"]
    weeks = cal["weeks"]
    levels = heat(t)
    s = Svg(1280, 470, f'{cal["totalContributions"]} contribuciones en los últimos 12 meses')
    card(s, t)

    stats = [
        (cal["totalContributions"], "contribuciones"),
        (data["totalCommitContributions"], "commits"),
        (data["totalPullRequestContributions"], "pull requests"),
        (data["totalRepositoryContributions"], "repos nuevos"),
    ]
    for i, (value, label) in enumerate(stats):
        x = 76 + i * 290
        s.text(x, 112, f"{value:,}".replace(",", "."), MONO, 800, 52, t["accent"] if i == 0 else t["text"])
        s.text(x, 150, label, SANS, 400, 24, t["muted"])

    pitch, size = 20, 16
    x0 = 1280 - 76 - len(weeks) * pitch + (pitch - size)
    y0 = 224
    prev, last_x = None, -99
    for wi, week in enumerate(weeks):
        month = int(week["contributionDays"][0]["date"][5:7])
        if month != prev:
            if wi < len(weeks) - 2 and wi - last_x >= 3:
                s.text(x0 + wi * pitch, y0 - 16, MONTHS[month - 1], MONO, 400, 16, t["faint"])
                last_x = wi
            prev = month
        for day in week["contributionDays"]:
            row = (date.fromisoformat(day["date"]).weekday() + 1) % 7
            fill = levels[level(int(day["contributionCount"]))]
            s.add(f'<rect x="{x0 + wi * pitch}" y="{y0 + row * pitch}" width="{size}" height="{size}" rx="4" fill="{fill}"/>')
    for row, label in ((1, "lun"), (3, "mié"), (5, "vie")):
        s.text(x0 - 16, y0 + row * pitch + 13, label, MONO, 400, 16, t["faint"], anchor="end")

    yb = 418
    s.text(76, yb, "últimos 12 meses, con las privadas", SANS, 400, 22, t["faint"])
    lx = 1280 - 76 - width("más", MONO, 400, 16) - 14 - 5 * 22
    s.text(lx - 14, yb - 1, "menos", MONO, 400, 16, t["faint"], anchor="end")
    for i, c in enumerate(levels):
        s.add(f'<rect x="{lx + i * 22}" y="{yb - 15}" width="16" height="16" rx="4" fill="{c}"/>')
    s.text(1280 - 76, yb - 1, "más", MONO, 400, 16, t["faint"], anchor="end")
    return s


def main() -> None:
    data = fetch()
    out = ROOT / "assets" / "activity.svg"
    out.write_text(build(data, THEMES["dark"]).render(), encoding="utf-8")
    print(f"OK · {data['contributionCalendar']['totalContributions']} contribuciones")


if __name__ == "__main__":
    main()
