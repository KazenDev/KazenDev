#!/usr/bin/env python3
"""
Genera las imágenes del perfil (assets/*.svg) a partir de los datos de abajo,
con el tema Catppuccin Mocha.

    python3 scripts/build_profile.py

El panel de actividad lo genera scripts/update_activity.py (necesita un token),
con este mismo tema y estas mismas fuentes.
"""
from __future__ import annotations

import base64
from functools import lru_cache
from html import escape
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "assets" / "fonts"
LOGOS = ROOT / "assets" / "logos"

# ---------------------------------------------------------------- tema

THEMES = {
    "dark": {  # Catppuccin Mocha
        "bg": "#1e1e2e", "panel": "#181825", "line": "#313244", "line2": "#45475a",
        "faint": "#7f849c", "muted": "#a6adc8", "text": "#cdd6f4",
        "accent": "#fab387", "accent2": "#cba6f7", "green": "#a6e3a1",
        "java": "#fab387", "cpp": "#f38ba8", "python": "#89b4fa",
        # gato
        "fur": "#9399b2", "stripe": "#585b70", "white": "#e6e9f8", "eye": "#a6e3a1",
        "pupil": "#11111b", "nose": "#f5c2e7", "ear": "#f2cdcd", "bow": "#fab387",
        "knot": "#c97b4a", "outline": "#11111b",
    },
}


def mix(a: str, b: str, t: float) -> str:
    pa = [int(a[i : i + 2], 16) for i in (1, 3, 5)]
    pb = [int(b[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(pa, pb))


def heat(t: dict) -> list[str]:
    """Cinco niveles de actividad: del borde al acento."""
    return [t["line"]] + [mix(t["line"], t["accent"], k) for k in (0.3, 0.55, 0.8, 1.0)]


# ---------------------------------------------------------------- fuentes

MONO = "Martian Mono"
SANS = "IBM Plex Sans"
FILES = {
    (MONO, 400): "martian-mono-400.woff",
    (MONO, 600): "martian-mono-600.woff",
    (MONO, 800): "martian-mono-800.woff",
    (SANS, 400): "ibm-plex-sans-400.woff",
    (SANS, 600): "ibm-plex-sans-600.woff",
}
STACK = {MONO: f"'{MONO}', ui-monospace, monospace", SANS: f"'{SANS}', 'Segoe UI', sans-serif"}


@lru_cache(None)
def _font(key: tuple[str, int]) -> TTFont:
    return TTFont(FONTS / FILES[key])


def width(s: str, family: str, weight: int, size: float) -> float:
    f = _font((family, weight))
    cmap, hmtx = f.getBestCmap(), f["hmtx"]
    upm = f["head"].unitsPerEm
    return sum(hmtx[cmap.get(ord(c), ".notdef")][0] for c in s) * size / upm


def wrap(s: str, family: str, weight: int, size: float, maxw: float) -> list[str]:
    lines, cur = [], ""
    for word in s.split():
        nxt = f"{cur} {word}".strip()
        if cur and width(nxt, family, weight, size) > maxw:
            lines.append(cur)
            cur = word
        else:
            cur = nxt
    return lines + [cur] if cur else lines


def font_css(used: set[tuple[str, int]]) -> str:
    out = []
    for fam, w in sorted(used):
        data = base64.b64encode((FONTS / FILES[(fam, w)]).read_bytes()).decode()
        out.append(
            f"@font-face{{font-family:'{fam}';font-weight:{w};font-style:normal;"
            f"src:url('data:font/woff;base64,{data}') format('woff')}}"
        )
    return "\n".join(out)


class Svg:
    """Un SVG que apunta qué fuentes usa, para incrustar solo esas."""

    def __init__(self, w: int, h: int, label: str):
        self.w, self.h, self.label = w, h, label
        self.parts: list[str] = []
        self.used: set[tuple[str, int]] = set()
        self.css: list[str] = []
        self.defs: list[str] = []

    def add(self, s: str) -> None:
        self.parts.append(s)

    def text(self, x, y, s, family=SANS, weight=400, size=24, fill="#000", anchor="start", extra=""):
        self.used.add((family, weight))
        a = f' text-anchor="{anchor}"' if anchor != "start" else ""
        self.add(
            f'<text x="{x:.1f}" y="{y:.1f}"{a} font-family="{STACK[family]}" font-weight="{weight}" '
            f'font-size="{size}" fill="{fill}"{extra}>{escape(s)}</text>'
        )

    def render(self) -> str:
        style = font_css(self.used) + "\n" + "\n".join(self.css)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}" fill="none" role="img" aria-label="{escape(self.label)}">\n'
            f"<defs><style>{style}</style>{''.join(self.defs)}</defs>\n" + "\n".join(self.parts) + "\n</svg>\n"
        )


def card(svg: Svg, t: dict, x=0.0, y=0.0, w=None, h=None, r=26) -> None:
    w = svg.w if w is None else w
    h = svg.h if h is None else h
    svg.add(f'<rect x="{x + 1}" y="{y + 1}" width="{w - 2}" height="{h - 2}" rx="{r}" fill="{t["bg"]}" stroke="{t["line"]}" stroke-width="2"/>')


# ---------------------------------------------------------------- el gato

# La mitad izquierda; la derecha es su espejo. Leyenda: f pelo, s raya, w blanco,
# e ojo, p pupila, n nariz, i oreja, b pajarita, k nudo.
CAT_HALF = [
    ".f.......",
    ".ff......",
    ".fif.....",
    ".fiif....",
    ".fiifffff",
    "ffffffsfs",
    "fffffsfww",
    "ffeeeffww",
    "ffepeffww",
    "ffeeefwww",
    "sffffwwww",
    "fsfwwwwwn",
    "ffwwwwwpw",
    ".ffwwwwww",
    "..ffwwwww",
    "..fwbbwww",
    "..fwbbbbk",
    "..fwbbwww",
    "..ffwwwww",
]
CAT_SHUT = {  # ojos cerrados (filas 7-9)
    7: "fffffffww",
    8: "fpppfffww",
    9: "ffffffwww",
}
CAT_KEYS = {"f": "fur", "s": "stripe", "w": "white", "e": "eye", "p": "pupil", "n": "nose", "i": "ear", "b": "bow", "k": "knot"}


def _rows(half: list[str]) -> list[str]:
    return ["." + r + r[::-1] + "." for r in half]


def _runs(rows: list[str], t: dict, px: float, ox: float, oy: float, only: range | None = None) -> str:
    out = []
    for y, row in enumerate(rows):
        if only is not None and y not in only:
            continue
        x = 0
        while x < len(row):
            c = row[x]
            n = 1
            while x + n < len(row) and row[x + n] == c:
                n += 1
            if c != ".":
                out.append(f'<rect x="{ox + x * px:.1f}" y="{oy + y * px:.1f}" width="{n * px:.1f}" height="{px:.1f}" fill="{t[CAT_KEYS[c]]}"/>')
            x += n
    return "".join(out)


def _outline(rows: list[str], t: dict, px: float, ox: float, oy: float) -> str:
    h, w = len(rows), len(rows[0])
    filled = lambda x, y: 0 <= y < h and 0 <= x < w and rows[y][x] != "."
    out = []
    for y in range(-1, h + 1):
        for x in range(-1, w + 1):
            if not filled(x, y) and any(filled(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out.append(f'<rect x="{ox + x * px:.1f}" y="{oy + y * px:.1f}" width="{px:.1f}" height="{px:.1f}"/>')
    return f'<g fill="{t["outline"]}">{"".join(out)}</g>'


def cat(svg: Svg, t: dict, ox: float, oy: float, px: float, asleep=False) -> None:
    rows = _rows(CAT_HALF)
    shut = [CAT_SHUT.get(i, r) for i, r in enumerate(CAT_HALF)]
    shut_rows = _rows(shut)
    svg.add(_outline(rows, t, px, ox, oy))
    if asleep:
        svg.add(_runs(shut_rows, t, px, ox, oy))
        return
    svg.add(_runs(rows, t, px, ox, oy))
    # Parpadeo: los ojos cerrados aparecen un instante cada pocos segundos.
    svg.add(f'<g class="blink">{_runs(shut_rows, t, px, ox, oy, range(7, 10))}</g>')
    svg.css.append(
        ".blink{opacity:0;animation:blink 5.2s steps(1) infinite}"
        "@keyframes blink{0%,91%{opacity:0}92%,95%{opacity:1}96%,100%{opacity:0}}"
        "@media (prefers-reduced-motion: reduce){.blink{animation:none}}"
    )


# ---------------------------------------------------------------- piezas

def hero(t: dict) -> Svg:
    s = Svg(1280, 430, "zKazen, desarrollador full-stack")
    card(s, t)
    x = 76
    s.text(x, 112, "hola, soy", MONO, 400, 24, t["muted"])
    s.text(x, 222, "zKazen", MONO, 800, 108, t["text"])
    cx = x + width("zKazen", MONO, 800, 108) + 14
    s.add(f'<rect class="cursor" x="{cx:.1f}" y="140" width="40" height="84" rx="3" fill="{t["accent"]}"/>')
    s.css.append(
        ".cursor{animation:cur 1.1s steps(1) infinite}@keyframes cur{50%{opacity:0}}"
        "@media (prefers-reduced-motion: reduce){.cursor{animation:none}}"
    )
    for i, line in enumerate(wrap("Desarrollador full-stack. Hago backends, bots, webs y plugins para Minecraft.", SANS, 400, 32, 760)):
        s.text(x, 290 + i * 44, line, SANS, 400, 32, t["muted"])
    stack = ["typescript", "java", "c++", "python", "php", "react", "node", "docker", "godot"]
    s.text(x, 380, "  ".join(stack), MONO, 400, 19, t["faint"])
    px = 12
    cat(s, t, 1280 - 76 - 20 * px, 430 - 30 - 19 * px, px)
    return s


def heading(t: dict, title: str) -> Svg:
    s = Svg(1280, 104, title)
    y = 68
    s.text(4, y, "##", MONO, 600, 30, t["accent"])
    tx = 4 + width("## ", MONO, 600, 30)
    s.text(tx, y, title, MONO, 600, 30, t["text"])
    lx = tx + width(title, MONO, 600, 30) + 28
    s.add(f'<rect class="rule" x="{lx:.1f}" y="{y - 11}" width="{1276 - lx:.1f}" height="2" rx="1" fill="{t["line"]}"/>')
    # Los títulos van sin fondo: en el tema claro de GitHub, colores de Latte.
    s.css.append(
        "@media (prefers-color-scheme: light){"
        "text{fill:#4c4f69}text:first-of-type{fill:#fe640b}.rule{fill:#ccd0da}}"
    )
    return s


def _logo(name: str) -> str:
    p = LOGOS / name
    mime = "image/svg+xml" if p.suffix == ".svg" else "image/png"
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"


def job(t: dict, j: dict) -> Svg:
    s = Svg(640, 220, f'{j["name"]}: {j["role"]}')
    card(s, t)
    lx, ly, ls = 38, 38, 88
    s.defs.append(f'<clipPath id="lc"><rect x="{lx}" y="{ly}" width="{ls}" height="{ls}" rx="22"/></clipPath>')
    s.add(f'<rect x="{lx}" y="{ly}" width="{ls}" height="{ls}" rx="22" fill="{j.get("tile", t["panel"])}"/>')
    pad = j.get("pad", 0)
    s.add(
        f'<image clip-path="url(#lc)" x="{lx + pad}" y="{ly + pad}" width="{ls - 2 * pad}" height="{ls - 2 * pad}" '
        f'preserveAspectRatio="xMidYMid meet" href="{_logo(j["logo"])}"/>'
    )
    tx = lx + ls + 26
    s.text(tx, 78, j["name"], SANS, 600, 34, t["text"])
    now = j["until"] is None
    s.text(tx, 118, j["role"], MONO, 400, 19, t["accent"] if now else t["muted"])
    s.text(lx, 182, j["site"], MONO, 400, 18, t["faint"])
    if now:
        w = width("ahora", MONO, 400, 18)
        s.add(f'<circle cx="{602 - w - 16:.1f}" cy="176" r="6" fill="{t["green"]}"/>')
        s.text(602, 182, "ahora", MONO, 400, 18, t["green"], anchor="end")
    else:
        s.text(602, 182, f'{j["since"]} – {j["until"]}', MONO, 400, 18, t["faint"], anchor="end")
    return s


def project(t: dict, p: dict) -> Svg:
    lines = wrap(p["desc"], SANS, 400, 27, 1080)
    h = 168 + 38 * len(lines)
    s = Svg(1280, h, f'{p["name"]}: {p["desc"]}')
    card(s, t)
    color = t[p["color"]]
    s.add(f'<rect x="42" y="46" width="6" height="{h - 92}" rx="3" fill="{color}"/>')
    x = 80
    s.text(x, 98, p["name"], MONO, 600, 40, t["text"])
    for i, line in enumerate(lines):
        s.text(x, 150 + i * 38, line, SANS, 400, 27, t["muted"])
    s.text(1280 - 56, 96, " · ".join(p["tags"]), MONO, 400, 19, t["faint"], anchor="end")
    return s


def more(t: dict) -> Svg:
    s = Svg(1280, 96, "Ver todos los repositorios")
    card(s, t, r=22)
    s.text(42, 58, "ver todos los repositorios", MONO, 400, 21, t["muted"])
    s.text(1280 - 42, 58, "→", MONO, 400, 24, t["accent"], anchor="end")
    return s


def footer(t: dict) -> Svg:
    s = Svg(1280, 230, "Disponible para colaboraciones, plugins a medida y desarrollo freelance.")
    card(s, t)
    px = 7
    cat(s, t, 60, 230 - 42 - 19 * px, px, asleep=True)
    zx, zy = 60 + 20 * px + 8, 64
    for i, (dx, dy, sz) in enumerate(((0, 18, 18), (20, 0, 23))):
        s.text(zx + dx, zy + dy, "z", MONO, 600, sz, t["faint"], extra=f' class="z z{i}"')
    s.css.append(
        ".z{animation:zz 3.2s ease-in-out infinite}.z1{animation-delay:1.6s}"
        "@keyframes zz{0%,100%{opacity:.25}50%{opacity:1}}"
        "@media (prefers-reduced-motion: reduce){.z{animation:none}}"
    )
    x = 60 + 20 * px + 90
    s.text(x, 106, "Disponible para colaboraciones, plugins", SANS, 600, 32, t["text"])
    s.text(x, 148, "a medida y desarrollo freelance.", SANS, 600, 32, t["text"])
    s.text(x, 190, "github.com/KazenDev", MONO, 400, 19, t["faint"])
    return s


# ---------------------------------------------------------------- datos

JOBS = [
    {"slug": "vampsclub", "name": "Vamps Club", "role": "Desarrollador web", "site": "vampsclub.shop",
     "since": None, "until": None, "logo": "vampsclub.svg", "tile": "#0a0a0a"},
    {"slug": "aiskaron", "name": "AIskaron", "role": "Contribuidor y ayudante · web", "site": "aiskaron.com",
     "since": "2026", "until": None, "logo": "aiskaron.svg", "tile": "#0d1117", "pad": 14},
    {"slug": "hidencloud", "name": "HidenCloud", "role": "Senior Support", "site": "hidencloud.com",
     "since": "ene 2025", "until": "jul 2026", "logo": "hidencloud.png"},
    {"slug": "netherhost", "name": "Nether Hosting", "role": "Staff", "site": "netherhost.cc",
     "since": "2025", "until": "2026", "logo": "netherhost.png"},
]

PROJECTS = [
    {"slug": "kira", "name": "Kira", "color": "python",
     "desc": "Una IA con cuerpo: te habla, te escucha y pone caras en una micro:bit. Se acuerda de vos y construye su personalidad charlando.",
     "tags": ["python", "fastapi", "react", "c++"]},
    {"slug": "jdevtools", "name": "JDevTools", "color": "java",
     "desc": "Desarrollo de plugins para servidores de Minecraft desde el propio juego: crea, compila y prueba plugins en Java sin IDE ni Maven.",
     "tags": ["java", "minecraft"]},
    {"slug": "kyra", "name": "Kyra-Qt", "color": "cpp",
     "desc": "Mascota de escritorio con Live2D, hecha con Qt y C++.",
     "tags": ["c++", "qt", "live2d"]},
]

HEADINGS = {"trayectoria": "trayectoria", "proyectos": "proyectos", "actividad": "actividad"}


def write(name: str, svg: Svg) -> None:
    out = ROOT / "assets" / f"{name}.svg"
    out.write_text(svg.render(), encoding="utf-8")


def main() -> None:
    t = THEMES["dark"]
    write("hero", hero(t))
    for slug, title in HEADINGS.items():
        write(f"h-{slug}", heading(t, title))
    for j in JOBS:
        write(f'job-{j["slug"]}', job(t, j))
    for p in PROJECTS:
        write(f'project-{p["slug"]}', project(t, p))
    write("more", more(t))
    write("footer", footer(t))
    print("OK")


if __name__ == "__main__":
    main()
