#!/usr/bin/env python3
"""
The link row under the banner: black MacBook keycaps.

The banner is the display (hairline bezel, notch); this row is the keyboard
under it. Each key is a lowercase legend bottom-left with a glyph top-right,
like command and option; the email gets a wide return key. In dark mode the
legends are faintly backlit, and now and then a key presses itself.

The row is laid out on the card's own 1200-unit grid and cut into five
images at the middle of each gap. In the README each image gets a percentage
width, and the five add up to just under 100%, so at any screen width the
row stays on one line and spans exactly the card, outer key edges flush with
its frame. (A table would add GitHub's grey grid, and fixed pixel widths
wrap on narrow screens.)

    links/<slug>-<mode>.svg
"""
MONO = "ui-monospace,'SF Mono','SFMono-Regular','JetBrains Mono',Menlo,Consolas,monospace"

ROW_W = 1200          # the card's width, so the two scale together
U, GAP = 190, 12      # one key, and the gap between keys
KEY_H, TOP, RADIUS = 84, 2, 12
HEIGHT = TOP + KEY_H + 6   # room for the shadow under the caps

KEYS = [  # (legend, href, glyph, width in keys)
    ("site", "https://arfaz.ca", "arrow", 1),
    ("resume", "https://arfaz.ca/resume", "doc", 1),
    ("root@arfaz.ca", "mailto:root@arfaz.ca", "return", 2),
    ("linkedin", "https://linkedin.com/in/arfazca", "in", 1),
    ("desktop", "https://desktop.arfaz.ca", "cmd", 1),
]

# 24-unit glyphs centred on 0,0, stroked
GLYPH = {
    "arrow": "M-5 5L5 -5M-1 -5H5V1",
    "doc": "M-6 -9H3L7 -5V9H-6ZM3 -9V-5H7M-3 -1H4M-3 3H4M-3 -5H0",
    "return": "M7 -7V0Q7 2.5 4.5 2.5H-6M-2.5 -1L-6 2.5L-2.5 6",
    "in": "M-8 -9H8Q9 -9 9 -8V8Q9 9 8 9H-8Q-9 9 -9 8V-8Q-9 -9 -8 -9ZM-4.5 -1V5.5M-4.5 -4.6V-4.4M0 5.5V-1M0 2Q0 -1 3 -1Q5 -1 5 2V5.5",
    # lines through the centre, three-quarter loops at the corners
    "cmd": ("M-2.5 -2.5V-5A2.5 2.5 0 1 0 -5 -2.5H5A2.5 2.5 0 1 0 2.5 -5V5"
            "A2.5 2.5 0 1 0 5 2.5H-5A2.5 2.5 0 1 0 -2.5 5Z"),
}
# (cycle s, first press s after load): unrelated cycles so the presses never
# fall into a rhythm, and a ripple left to right just after load
PRESS = {"site": (17, 1.2), "resume": (23, 1.35), "root@arfaz.ca": (29, 1.5), "linkedin": (19, 1.65),
         "desktop": (31, 1.8)}
LEGEND = "#dbe2ea"
LEGEND_FS, LEGEND_LS = 18, 0.5


def slug(name):
    return "".join(c if c.isalnum() else "-" for c in name).strip("-")


def layout():
    """[(name, href, glyph, image x0, image width, key x0 within the image, key width)]

    Images are cut at the middle of each gap, so the first and last keys sit
    flush with the row's outer edges and every image carries half a gap on
    each inner side."""
    out, x = [], 0.0
    for i, (name, href, glyph, span) in enumerate(KEYS):
        kw = span * U + (span - 1) * GAP
        left = 0 if i == 0 else GAP / 2
        right = 0 if i == len(KEYS) - 1 else GAP / 2
        out.append((name, href, glyph, x, left + kw + right, left, kw))
        x += left + kw + right
    assert abs(x - ROW_W) < 1e-6, x
    return out


def _glyph(key, x, y, color, extra=""):
    s, sw = 1.0, 2.3
    return (f'<g transform="translate({x:.1f} {y:.1f}) scale({s})" fill="none" stroke="{color}" '
            f'stroke-width="{sw / s:.2f}" stroke-linecap="round" stroke-linejoin="round"{extra}>'
            f'<path d="{GLYPH[key]}"/></g>')


def _legend(name, x, y, color, extra=""):
    # textLength pins the run to one width whichever monospace font the
    # viewer has (Menlo, SF Mono, Consolas, DejaVu all differ slightly)
    return (f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{LEGEND_FS}" letter-spacing="{LEGEND_LS}" '
            f'textLength="{len(name) * (LEGEND_FS * 0.6 + LEGEND_LS):.1f}" lengthAdjust="spacing" '
            f'fill="{color}"{extra}>{name}</text>')


def build(name, glyph, W, kx, kw, mode):
    cyc, first = PRESS[name]
    at = 6.0
    p0, p1, p2 = at / cyc * 100, (at + 0.09) / cyc * 100, (at + 0.24) / cyc * 100
    style = (f".k{{animation:k {cyc}s ease-out infinite;animation-delay:{first - at:.2f}s}}"
             f"@keyframes k{{0%,{p0:.3f}%,{p2:.3f}%,100%{{transform:none}}{p1:.3f}%{{transform:translateY(2.4px)}}}}"
             "@media(prefers-reduced-motion:reduce){*{animation:none!important}}")
    x, r, top, kh = kx, RADIUS, TOP, KEY_H
    shadow = (f'<rect x="{x}" y="{top + 4}" width="{kw}" height="{kh}" rx="{r}" fill="#000" '
              f'opacity="{0.7 if mode == "dark" else 0.22}"/>')
    if mode == "light":
        shadow += f'<rect x="{x + 1}" y="{top + 5}" width="{kw - 2}" height="{kh + 1}" rx="{r}" fill="#000" opacity=".08"/>'
    lx, ly, gx, gy = x + 20, top + kh - 20, x + kw - 28, top + 26
    glow = ""
    if mode == "dark":  # backlight: a soft halo under the legend
        glow = (_legend(name, lx, ly, "#9fc3ff", ' opacity=".55" filter="url(#bl)"')
                + _glyph(glyph, gx, gy, "#9fc3ff", ' opacity=".5" filter="url(#bl)"'))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:g}" height="{HEIGHT}" viewBox="0 0 {W:g} {HEIGHT}" '
        f'role="img" aria-label="{name}"><title>{name}</title><style>{style}</style>'
        '<defs><linearGradient id="kg" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#202329"/><stop offset=".55" stop-color="#121418"/>'
        '<stop offset="1" stop-color="#0b0c0f"/></linearGradient>'
        '<filter id="bl" x="-20%" y="-60%" width="140%" height="220%"><feGaussianBlur stdDeviation="2.4"/></filter></defs>'
        + shadow +
        f'<g class="k"><rect x="{x + 0.5}" y="{top + 0.5}" width="{kw - 1}" height="{kh - 1}" rx="{r}" '
        f'fill="url(#kg)" stroke="#000" stroke-width="1"/>'
        f'<path d="M{x + r} {top + 1.6}H{x + kw - r}" stroke="#fff" stroke-opacity=".1" stroke-width="1.4"/>'
        + glow + _glyph(glyph, gx, gy, LEGEND) + _legend(name, lx, ly, LEGEND)
        + "</g></svg>\n")


def all_keys():
    """{(slug, mode): svg}"""
    return {(slug(n), mode): build(n, g, W, kx, kw, mode)
            for n, _, g, _, W, kx, kw in layout() for mode in ("dark", "light")}


def readme_row(base):
    """The README paragraph. One line on purpose: whitespace between the links
    would add gaps and could let the row wrap. Widths are percentages of the
    README column, rounded down so their sum never tips over 100%; no height,
    so each key keeps its proportions as it scales."""
    cells = []
    for n, href, _, _, W, _, _ in layout():
        s = slug(n)
        pct = int(W / ROW_W * 100000) / 1000
        cells.append(f'<a href="{href}"><picture><source media="(prefers-color-scheme: dark)" '
                     f'srcset="{base}/links/{s}-dark.svg" /><img src="{base}/links/{s}-light.svg" '
                     f'width="{pct:g}%" alt="{n}" /></picture></a>')
    return '<p align="center">' + "".join(cells) + "</p>"
