#!/usr/bin/env python3
"""
Builds about-dark.svg / about-light.svg (neofetch-style About Me card) from
ascii-art.txt + the FIELDS content below. Static personal fields are baked in
here; the values with an `id=` (uptime + GitHub stats) are left as
placeholders and overwritten in-place by generate.py at CI time, mirroring
https://github.com/Andrew6rant/Andrew6rant's today.py svg_overwrite() approach.
"""
import os
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "ascii-art.txt")) as f:
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
    ("kv", "OS", "macOS Tahoe 26.5.2 (M1, M2)", 34, None),
    ("kv", "Uptime", "", 28, "age_data"),
    ("kv", "Devices.Home Server", "Arch Linux, Hyprland v0.56.1, GNU/Linux", 4, None),
    ("kv", "Devices.Work", "Windows 11 — Megabyte Systems, Inc.", 14, None),
    ("kv", "IDE", "Neovim (LazyVim), WezTerm", 33, None),
    ("blank",),
    ("kv", "Languages.Programming", "TypeScript, Rust, C#/.NET", 2, None),
    ("kv", "Languages.Real", "English (C1), Bangla (C2), French (A2)", 12, None),
    ("blank",),
    ("kv", "Hobbies.Making", "Building Things, Graphic Design, Software", 12, None),
    ("kv", "Hobbies.Community", "Volunteering, Community Work", 8, None),
    ("blank",),
    ("header", "Contact"),
    ("kv", "Email", "root@arfaz.ca", 31, None),
    ("kv", "LinkedIn", "arfazca", 28, None),
    ("kv", "GitHub", "arfazca", 30, None),
    ("kv", "X", "@arfazca", 35, None),
    ("blank",),
    ("header", "Links"),
    ("kv", "Web", "https://arfaz.ca", 33, None),
    ("kv", "Blog", "https://arfaz.ca/blog", 32, None),
    ("kv", "Resume", "https://arfaz.ca/resume", 30, None),
    ("kv", "Portfolio", "https://arfaz.ca/portfolio", 27, None),
    ("blank",),
    ("header", "GitHub Stats"),
    ("kv2", "Repos", "repo_data", 6, "Contributed", "contrib_data", None, "Stars", "star_data", 14),
    ("kv2b", "Commits", "commit_data", 22, "Followers", "follower_data", 10),
    ("loc",),
]


def dots(n):
    if n <= 0:
        return ""
    if n == 1:
        return " "
    if n == 2:
        return ". "
    return " " + ("." * n) + " "


def esc(s):
    return escape(str(s))


def render_ascii(theme):
    out = []
    y = ASCII_Y0
    for i, line in enumerate(ASCII_LINES):
        delay = round(i * 0.012, 3)
        out.append(
            f'<text x="{ASCII_X}" y="{y}" xml:space="preserve" fill="{theme["ascii"]}" '
            f'style="animation-delay:{delay}s" class="ln">{esc(line)}</text>'
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
            _, key, value, dots_len, value_id = row
            id_attr = f' id="{value_id}"' if value_id else ""
            dots_id_attr = f' id="{value_id}_dots"' if value_id else ""
            out.append(
                f'<text x="{PANEL_X}" y="{y}" xml:space="preserve">'
                f'<tspan fill="{theme["dim"]}">. </tspan>'
                f'<tspan fill="{theme["key"]}">{esc(key)}</tspan>'
                f'<tspan fill="{theme["dim"]}">:</tspan>'
                f'<tspan fill="{theme["dim"]}"{dots_id_attr}>{esc(dots(dots_len))}</tspan>'
                f'<tspan fill="{theme["value"]}"{id_attr}>{esc(value)}</tspan></text>'
            )
            y += LINE_HEIGHT
            continue
        if kind == "kv2":
            _, k1, id1, dl1, k2, id2, dl2b, k3, id3, dl3 = row
            out.append(
                f'<text x="{PANEL_X}" y="{y}" xml:space="preserve">'
                f'<tspan fill="{theme["dim"]}">. </tspan>'
                f'<tspan fill="{theme["key"]}">{esc(k1)}</tspan>'
                f'<tspan fill="{theme["dim"]}">:</tspan>'
                f'<tspan fill="{theme["dim"]}" id="{id1}_dots">{dots(dl1)}</tspan>'
                f'<tspan fill="{theme["value"]}" id="{id1}">0</tspan>'
                f'<tspan fill="{theme["dim"]}"> {{</tspan>'
                f'<tspan fill="{theme["key"]}">{esc(k2)}</tspan>'
                f'<tspan fill="{theme["dim"]}">: </tspan>'
                f'<tspan fill="{theme["value"]}" id="{id2}">0</tspan>'
                f'<tspan fill="{theme["dim"]}">}} | </tspan>'
                f'<tspan fill="{theme["key"]}">{esc(k3)}</tspan>'
                f'<tspan fill="{theme["dim"]}">:</tspan>'
                f'<tspan fill="{theme["dim"]}" id="{id3}_dots">{dots(dl3)}</tspan>'
                f'<tspan fill="{theme["value"]}" id="{id3}">0</tspan></text>'
            )
            y += LINE_HEIGHT
            continue
        if kind == "kv2b":
            _, k1, id1, dl1, k2, id2, dl2 = row
            out.append(
                f'<text x="{PANEL_X}" y="{y}" xml:space="preserve">'
                f'<tspan fill="{theme["dim"]}">. </tspan>'
                f'<tspan fill="{theme["key"]}">{esc(k1)}</tspan>'
                f'<tspan fill="{theme["dim"]}">:</tspan>'
                f'<tspan fill="{theme["dim"]}" id="{id1}_dots">{dots(dl1)}</tspan>'
                f'<tspan fill="{theme["value"]}" id="{id1}">0</tspan>'
                f'<tspan fill="{theme["dim"]}"> | </tspan>'
                f'<tspan fill="{theme["key"]}">{esc(k2)}</tspan>'
                f'<tspan fill="{theme["dim"]}">:</tspan>'
                f'<tspan fill="{theme["dim"]}" id="{id2}_dots">{dots(dl2)}</tspan>'
                f'<tspan fill="{theme["value"]}" id="{id2}">0</tspan></text>'
            )
            y += LINE_HEIGHT
            continue
        if kind == "loc":
            out.append(
                f'<text x="{PANEL_X}" y="{y}" xml:space="preserve">'
                f'<tspan fill="{theme["dim"]}">. </tspan>'
                f'<tspan fill="{theme["key"]}">Lines of Code on GitHub</tspan>'
                f'<tspan fill="{theme["dim"]}">:</tspan>'
                f'<tspan fill="{theme["dim"]}" id="loc_data_dots">. </tspan>'
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
    width = PANEL_X + 630
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" font-family="{FONT_STACK}" font-size="{FONT_SIZE}px">
<title>About Me — Arfaz Hussain</title>
<style>
.ln{{opacity:0;animation:rv .5s ease forwards}}
@keyframes rv{{from{{opacity:0;transform:translateX(-6px)}}to{{opacity:1;transform:translateX(0)}}}}
text,tspan{{white-space:pre}}
</style>
<rect x="0.75" y="0.75" width="{width - 1.5}" height="{height - 1.5}" rx="20" ry="20" fill="none" stroke="{theme['border']}" stroke-width="1.5"/>
<g font-size="{ASCII_FONT_SIZE}px">
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
        with open(out_path, "w") as f:
            f.write(out)
        print("wrote", out_path)
