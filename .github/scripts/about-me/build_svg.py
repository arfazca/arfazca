#!/usr/bin/env python3
"""
Builds about-dark.svg / about-light.svg (neofetch-style About Me card) from
ascii-art.txt + the FIELDS content below. Static personal fields are baked in
here; the values with an `id=` (uptime + GitHub stats) are left as
placeholders and overwritten in-place by generate.py at CI time, mirroring
https://github.com/Andrew6rant/Andrew6rant's today.py svg_overwrite() approach.
"""
import math
import os
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))


def color_ramp(c_from, c_to, n):
    """n-step linear RGB interpolation from c_from (edge/shadow) to c_to (interior/lit)."""
    a = tuple(int(c_from[i:i + 2], 16) for i in (1, 3, 5))
    b = tuple(int(c_to[i:i + 2], 16) for i in (1, 3, 5))
    steps = []
    for i in range(n):
        t = i / (n - 1)
        rgb = tuple(round(a[k] + (b[k] - a[k]) * t) for k in range(3))
        steps.append("#{:02x}{:02x}{:02x}".format(*rgb))
    return steps


ASCII_TIERS = 7  # matches the '.',':','-','=','+','*','#' density levels in ascii-art.txt

with open(os.path.join(HERE, "ascii-art.txt"), encoding="utf-8") as f:
    ASCII_LINES = f.read().rstrip("\n").split("\n")

ASCII_FONT_SIZE = 15
ASCII_LINE_HEIGHT = 18
ASCII_X = 24
ASCII_Y0 = 40

PANEL_X = 24 + 66 * 9 + 40  # ascii width (66 cols * ~9px) + gutter
FONT_SIZE = 13.5
LINE_HEIGHT = 20
PANEL_Y0 = 40

THEMES = {
    "dark": {
        "border": "#30363d",
        "header": "#e6edf3",
        "key": "#79c0ff",
        "value": "#7ee787",
        "dim": "#8b949e",
        "add": "#3fb950",
        "del": "#f85149",
        "ascii": "#c9d1d9",
        # per-face gradient, edge -> interior, keyed by the density character
        # already chosen for edge-distance when the logo was built: the
        # silhouette rim goes dark/shadowed and each face brightens to a
        # vivid, fully-saturated tone toward its own center - that's the bulk
        # of the shape, so it has to read as solid color, not a pale wash.
        "ascii_shade": {
            "left": color_ramp("#0c2d6b", "#79c0ff", ASCII_TIERS),
            "right": color_ramp("#061a3d", "#388bfd", ASCII_TIERS),
        },
    },
    "light": {
        "border": "#d0d7de",
        "header": "#24292f",
        "key": "#0969da",
        "value": "#1a7f37",
        "dim": "#57606a",
        "add": "#1a7f37",
        "del": "#cf222e",
        "ascii": "#57606a",
        "ascii_shade": {
            "left": color_ramp("#bfe0ff", "#0550ae", ASCII_TIERS),
            "right": color_ramp("#d9edff", "#0969da", ASCII_TIERS),
        },
    },
}

FONT_STACK = "ui-monospace,'SF Mono','SFMono-Regular','JetBrains Mono','Fira Code',Menlo,Consolas,'Liberation Mono',monospace"

# ---------------------------------------------------------------------------
# Right-panel content. Each row is one of:
#   ("kv", key, value, dots_len, value_id)      -> ". key: ....... value"
#   ("kv2", k1, v1, id1, k2, v2, id2)            -> ". k1: v1 | k2: v2" (stats rows)
#   ("header", text)                              -> "- text -------------"
#   ("blank",)
# dots_len is the target column width used to right-pad the dot leader.
# ---------------------------------------------------------------------------
ROWS = [
    ("header", "arfaz@github"),
    ("kv", "OS", "macOS Tahoe 26.5.2 (M1, M2)", None),
    ("kv", "Uptime", "", "age_data"),
    ("kv", "Devices.Home Server", "Arch Linux, Hyprland v0.56.1, GNU/Linux", None),
    ("kv", "Devices.Work", "Windows 11 — Megabyte Systems, Inc.", None),
    ("kv", "IDE", "Neovim (LazyVim), WezTerm", None),
    ("blank",),
    ("kv", "Languages.Programming", "TypeScript, Rust, C#/.NET", None),
    ("kv", "Languages.Real", "English (C1), Bangla (C2), French (A2)", None),
    ("blank",),
    ("kv", "Hobbies.Making", "Building Things, Graphic Design, Software", None),
    ("kv", "Hobbies.Community", "Volunteering, Community Work", None),
    ("blank",),
    ("header", "Contact"),
    ("kv", "Email", "root@arfaz.ca", None),
    ("kv", "LinkedIn", "arfazca", None),
    ("kv", "GitHub", "arfazca", None),
    ("kv", "X", "@arfazca", None),
    ("blank",),
    ("header", "Links"),
    ("kv", "Web", "https://arfaz.ca", None),
    ("kv", "Blog", "https://arfaz.ca/blog", None),
    ("kv", "Resume", "https://arfaz.ca/resume", None),
    ("kv", "Portfolio", "https://arfaz.ca/portfolio", None),
    ("blank",),
    ("header", "GitHub Stats"),
    ("kv2", "Repos", "repo_data", "Contributed", "contrib_data", "Stars", "star_data"),
    ("kv", "Commits", "", "commit_data"),
    ("loc",),
]

# Every row's value column lines up at the same character offset from PANEL_X
# (". " + key + ":" + dots), instead of hand-tuned per-row dot counts that
# drift out of alignment whenever a key's text changes length.
VALUE_COL = 40
SEP_DOTS = 2  # small fixed leader for secondary inline fields (Contributed/Stars)


def dots(n):
    if n <= 0:
        return ""
    if n == 1:
        return " "
    if n == 2:
        return ". "
    return " " + ("." * n) + " "


def dots_for_key(key):
    # chars before the value = ". " (2) + key + ":" (1) + dots string
    return dots(VALUE_COL - 3 - len(key))


def esc(s):
    return escape(str(s))


ASCII_COLS = 66
ASCII_SPLIT = ASCII_COLS // 2  # left/right halves shaded differently for a 3D lit/shadow-face look
ASCII_CHAR_W = 9  # approx monospace advance width at ASCII_FONT_SIZE, matches the PANEL_X gutter math
ASCII_CENTER_X = ASCII_X + (ASCII_COLS * ASCII_CHAR_W) / 2
ASCII_CENTER_Y = ASCII_Y0 + (len(ASCII_LINES) * ASCII_LINE_HEIGHT) / 2


def spin_keyframes(steps=12):
    # scaleX(cos(theta)) fakes a Y-axis turntable spin on flat 2D content:
    # theta=0 -> full width (face on), theta=90 -> collapsed to a sliver
    # (edge-on), theta=180 -> full width again but mirrored (the back face,
    # which - since the left/right halves are colored differently - actually
    # shows the opposite lit/shadow side, selling the turn), theta=270 ->
    # sliver again, back to theta=360=0.
    lines = []
    for i in range(steps + 1):
        pct = i * 100 / steps
        theta = i * 360 / steps
        scale = math.cos(math.radians(theta))
        lines.append(f"{pct:g}%{{transform:scaleX({scale:.3f})}}")
    return "".join(lines)


# '.' (nearest edge) through '#' (deepest interior) distance tiers baked into
# ascii-art.txt by the logo generator, reused here as a shading index.
ASCII_TIER = {ch: i for i, ch in enumerate(".:-=+*#")}


def render_ascii(theme):
    shade = theme["ascii_shade"]
    out = []
    y = ASCII_Y0
    for i, line in enumerate(ASCII_LINES):
        delay = round(i * 0.012, 3)
        runs = []
        for col, ch in enumerate(line):
            side = "left" if col < ASCII_SPLIT else "right"
            color = shade[side][ASCII_TIER.get(ch, ASCII_TIERS - 1)]
            if runs and runs[-1][0] == color:
                runs[-1][1] += ch
            else:
                runs.append([color, ch])
        tspans = "".join(f'<tspan fill="{c}">{esc(chars)}</tspan>' for c, chars in runs)
        out.append(
            f'<text x="{ASCII_X}" y="{y}" xml:space="preserve" '
            f'style="animation-delay:{delay}s" class="ln">{tspans}</text>'
        )
        y += ASCII_LINE_HEIGHT
    return "\n".join(out)


def render_panel(theme):
    out = []
    y = PANEL_Y0
    for row in ROWS:
        kind = row[0]
        if kind == "blank":
            y += LINE_HEIGHT
            continue
        if kind == "header":
            text = row[1]
            rule_len = 46
            rule = "—" * rule_len
            out.append(
                f'<text x="{PANEL_X}" y="{y}" xml:space="preserve">'
                f'<tspan fill="{theme["header"]}" font-weight="600">{esc(text)}</tspan> '
                f'<tspan fill="{theme["dim"]}">{rule}</tspan></text>'
            )
            y += LINE_HEIGHT
            continue
        if kind == "kv":
            _, key, value, value_id = row
            id_attr = f' id="{value_id}"' if value_id else ""
            dots_id_attr = f' id="{value_id}_dots"' if value_id else ""
            out.append(
                f'<text x="{PANEL_X}" y="{y}" xml:space="preserve">'
                f'<tspan fill="{theme["dim"]}">. </tspan>'
                f'<tspan fill="{theme["key"]}">{esc(key)}</tspan>'
                f'<tspan fill="{theme["dim"]}">:</tspan>'
                f'<tspan fill="{theme["dim"]}"{dots_id_attr}>{esc(dots_for_key(key))}</tspan>'
                f'<tspan fill="{theme["value"]}"{id_attr}>{esc(value)}</tspan></text>'
            )
            y += LINE_HEIGHT
            continue
        if kind == "kv2":
            _, k1, id1, k2, id2, k3, id3 = row
            out.append(
                f'<text x="{PANEL_X}" y="{y}" xml:space="preserve">'
                f'<tspan fill="{theme["dim"]}">. </tspan>'
                f'<tspan fill="{theme["key"]}">{esc(k1)}</tspan>'
                f'<tspan fill="{theme["dim"]}">:</tspan>'
                f'<tspan fill="{theme["dim"]}" id="{id1}_dots">{dots_for_key(k1)}</tspan>'
                f'<tspan fill="{theme["value"]}" id="{id1}">0</tspan>'
                f'<tspan fill="{theme["dim"]}"> {{</tspan>'
                f'<tspan fill="{theme["key"]}">{esc(k2)}</tspan>'
                f'<tspan fill="{theme["dim"]}">: </tspan>'
                f'<tspan fill="{theme["value"]}" id="{id2}">0</tspan>'
                f'<tspan fill="{theme["dim"]}">}} | </tspan>'
                f'<tspan fill="{theme["key"]}">{esc(k3)}</tspan>'
                f'<tspan fill="{theme["dim"]}">:</tspan>'
                f'<tspan fill="{theme["dim"]}" id="{id3}_dots">{dots(SEP_DOTS)}</tspan>'
                f'<tspan fill="{theme["value"]}" id="{id3}">0</tspan></text>'
            )
            y += LINE_HEIGHT
            continue
        if kind == "loc":
            key = "Lines of Code on GitHub"
            out.append(
                f'<text x="{PANEL_X}" y="{y}" xml:space="preserve">'
                f'<tspan fill="{theme["dim"]}">. </tspan>'
                f'<tspan fill="{theme["key"]}">{esc(key)}</tspan>'
                f'<tspan fill="{theme["dim"]}">:</tspan>'
                f'<tspan fill="{theme["dim"]}" id="loc_data_dots">{esc(dots_for_key(key))}</tspan>'
                f'<tspan fill="{theme["value"]}" id="loc_data">0</tspan>'
                f'<tspan fill="{theme["dim"]}"> ( </tspan>'
                f'<tspan fill="{theme["add"]}" id="loc_add">0</tspan>'
                f'<tspan fill="{theme["add"]}">++</tspan>'
                f'<tspan fill="{theme["dim"]}">, </tspan>'
                f'<tspan fill="{theme["dim"]}" id="loc_del_dots"> </tspan>'
                f'<tspan fill="{theme["del"]}" id="loc_del">0</tspan>'
                f'<tspan fill="{theme["del"]}">--</tspan>'
                f'<tspan fill="{theme["dim"]}"> )</tspan></text>'
            )
            y += LINE_HEIGHT
            continue
    return "\n".join(out), y


def build(mode):
    theme = THEMES[mode]
    panel_svg, end_y = render_panel(theme)
    ascii_svg = render_ascii(theme)
    ascii_end_y = ASCII_Y0 + len(ASCII_LINES) * ASCII_LINE_HEIGHT
    height = max(end_y, ascii_end_y) + 24
    width = PANEL_X + 660
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" font-family="{FONT_STACK}" font-size="{FONT_SIZE}px">
<title>About Me — Arfaz Hussain</title>
<style>
.ln{{opacity:0;animation:rv .5s ease forwards}}
@keyframes rv{{from{{opacity:0;transform:translateX(-6px)}}to{{opacity:1;transform:translateX(0)}}}}
text,tspan{{white-space:pre}}
.spin3d{{transform-origin:{ASCII_CENTER_X}px {ASCII_CENTER_Y}px;animation:spin3d 20s linear infinite}}
@keyframes spin3d{{{spin_keyframes()}}}
</style>
<rect x="0.75" y="0.75" width="{width - 1.5}" height="{height - 1.5}" rx="20" ry="20" fill="none" stroke="{theme['border']}" stroke-width="1.5"/>
<g font-size="{ASCII_FONT_SIZE}px" class="spin3d">
{ascii_svg}
</g>
<g font-size="{FONT_SIZE}px">
{panel_svg}
</g>
</svg>
'''
    return svg


if __name__ == "__main__":
    for mode in ("dark", "light"):
        out = build(mode)
        out_path = os.path.join(HERE, f"about-{mode}.template.svg")
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(out)
        print("wrote", out_path)
