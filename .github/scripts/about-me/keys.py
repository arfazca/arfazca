#!/usr/bin/env python3
"""
The link row under the banner: the bottom half of a laptop.

The banner is the lid (black glass, aluminium rim, notch, and a strip of
aluminium under the glass); this row is the keyboard below it: one plate
with the keys set into it, black keys in Space Grey for dark mode, white keys
in silver for light mode. The plate's top edge is square and carries straight
on from the banner's chin, its side rims carry on from the lid's, and only
its bottom corners are round, so the two images read as one laptop. Each key
is a lowercase legend bottom-left with a glyph top-right, like command and
option; the email gets a wide return key. In dark mode the legends are
faintly backlit, and now and then a key presses itself.

The row is laid out on the card's own 1200-unit grid and cut into five
images at the middle of each gap. Each image paints its own stretch of the
plate, so side by side they read as one deck. In the README each image gets
a percentage width, and the five add up to just under 100%, so at any screen
width the row stays on one line and spans exactly the card. (A table would
add GitHub's grey grid, and fixed pixel widths wrap on narrow screens.)

    links/<slug>-<mode>.svg
"""
from banner import BEZEL_R, CHIN, METAL, RIM, THEMES

MONO = "ui-monospace,'SF Mono','SFMono-Regular','JetBrains Mono',Menlo,Consolas,monospace"

# Every band of bare aluminium is the banner's METAL wide: between the screen
# and the keys, between keys, and between a key and the deck's edge. Each key
# sits in a hole WELL wider than itself, the way the screen sits in its glass.
ROW_W = 1200          # the card's width, so the two scale together
WELL = 2.5
GAP = METAL + 2 * WELL               # key to key
PAD = round(RIM + METAL + WELL, 3)   # image edge to key at the row's two ends
KEY_H, RADIUS = 74, 9
KEY_Y = round(METAL - CHIN + WELL, 3)  # the banner's CHIN is the rest of the metal above
HEIGHT = round(KEY_Y + KEY_H + WELL + METAL + RIM, 3)

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
LEGEND_FS, LEGEND_LS = 18, 0.5

# The plate and rim colours are the banner's (THEMES), so the two halves match.
# well: the shadowed hole round each key. cap: gradient, outline, shine,
# legend, glyph, backlight (None for none), shadow under the cap.
STYLE = {
    "dark": {
        "well": ("#08090b", 0.9),
        "cap": ("#202329", "#121418", "#0b0c0f"), "cap_edge": ("#000", 1), "cap_shine": 0.10,
        "legend": "#dbe2ea", "glyph": "#dbe2ea", "backlight": "#9fc3ff", "shadow": 0.6,
    },
    "light": {
        "well": ("#8d939b", 0.55),
        "cap": ("#ffffff", "#f8f9fa", "#eef0f2"), "cap_edge": ("#000", 0.2), "cap_shine": 0.9,
        "legend": "#2b3038", "glyph": "#464c55", "backlight": None, "shadow": 0.25,
    },
}


def slug(name):
    return "".join(c if c.isalnum() else "-" for c in name).strip("-")


def layout():
    """[(name, href, glyph, image x0, image width, key x0 within the image, key width)]

    Images are cut at the middle of each gap. The end images also carry the
    deck's metal past the end keys, so the plate spans the full row."""
    units = sum(span for _, _, _, span in KEYS)
    inner = sum(span - 1 for _, _, _, span in KEYS)
    u = (ROW_W - 2 * PAD - GAP * (len(KEYS) - 1) - GAP * inner) / units
    out, x = [], 0.0
    for i, (name, href, glyph, span) in enumerate(KEYS):
        kw = span * u + (span - 1) * GAP
        left = PAD if i == 0 else GAP / 2
        right = PAD if i == len(KEYS) - 1 else GAP / 2
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
    return (f'<text x="{x:.1f}" y="{y}" font-family="{MONO}" font-size="{LEGEND_FS}" letter-spacing="{LEGEND_LS}" '
            f'textLength="{len(name) * (LEGEND_FS * 0.6 + LEGEND_LS):.1f}" lengthAdjust="spacing" '
            f'fill="{color}"{extra}>{name}</text>')


def _deck(W, a, first, last):
    """This image's stretch of the deck, inset by a on the bottom and on the
    row's outer ends (not the top, which the banner continues, nor a cut side).
    Square on top, round only at the row's two bottom corners."""
    r, b = BEZEL_R - a, HEIGHT - a
    x0, x1 = (a if first else 0), (W - a if last else W)
    right = f"V{b - r:.3f}A{r} {r} 0 0 1 {x1 - r:.3f} {b:.3f}" if last else f"V{b:.3f}"
    left = f"H{x0 + r:.3f}A{r} {r} 0 0 1 {x0:.3f} {b - r:.3f}" if first else f"H{x0:.3f}"
    return f"M{x0:.3f} 0H{x1:.3f}{right}{left}Z"


def build(name, glyph, W, kx, kw, mode, first, last):
    s = STYLE[mode]
    cyc, start = PRESS[name]
    at = 6.0
    p0, p1, p2 = at / cyc * 100, (at + 0.09) / cyc * 100, (at + 0.24) / cyc * 100
    style = (f".k{{animation:k {cyc}s ease-out infinite;animation-delay:{start - at:.2f}s}}"
             f"@keyframes k{{0%,{p0:.3f}%,{p2:.3f}%,100%{{transform:none}}{p1:.3f}%{{transform:translateY(1.6px)}}}}"
             "@media(prefers-reduced-motion:reduce){*{animation:none!important}}")
    x, y, r, kh = kx, KEY_Y, RADIUS, KEY_H
    (p0c, p1c), rim, (wc, wo) = THEMES[mode]["plate"], THEMES[mode]["rim"], s["well"]
    plate = (f'<path d="{_deck(W, 0, first, last)}" fill="{rim}"/>'
             f'<path d="{_deck(W, RIM, first, last)}" fill="url(#pg)"/>'
             # the hole the key sits in
             f'<rect x="{x - WELL:.3f}" y="{y - WELL:g}" width="{kw + 2 * WELL:.3f}" height="{kh + 2 * WELL:g}" rx="{r + WELL:g}" '
             f'fill="{wc}" opacity="{wo:g}"/>'
             f'<rect x="{x + 1:.3f}" y="{y + 1.5}" width="{kw - 2:.3f}" height="{kh}" rx="{r}" fill="#000" '
             f'opacity="{s["shadow"]:g}" filter="url(#sh)"/>')
    lx, ly, gx, gy = x + 20, y + kh - 17, x + kw - 28, y + 23
    glow = ""
    if s["backlight"]:  # a soft halo under the legend
        glow = (_legend(name, lx, ly, s["backlight"], ' opacity=".55" filter="url(#bl)"')
                + _glyph(glyph, gx, gy, s["backlight"], ' opacity=".5" filter="url(#bl)"'))
    c0, c1, c2 = s["cap"]
    cc, co = s["cap_edge"]
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.3f}" height="{HEIGHT}" viewBox="0 0 {W:.3f} {HEIGHT}" '
        f'role="img" aria-label="{name}"><title>{name}</title><style>{style}</style>'
        '<defs>'
        f'<linearGradient id="pg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{p0c}"/>'
        f'<stop offset="1" stop-color="{p1c}"/></linearGradient>'
        f'<linearGradient id="kg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c0}"/>'
        f'<stop offset=".55" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient>'
        '<filter id="bl" x="-20%" y="-60%" width="140%" height="220%"><feGaussianBlur stdDeviation="2.4"/></filter>'
        '<filter id="sh" x="-5%" y="-10%" width="110%" height="130%"><feGaussianBlur stdDeviation=".8"/></filter>'
        '</defs>'
        + plate +
        f'<g class="k"><rect x="{x + 0.5:.3f}" y="{y + 0.5}" width="{kw - 1:.3f}" height="{kh - 1}" rx="{r}" '
        f'fill="url(#kg)" stroke="{cc}" stroke-opacity="{co:g}" stroke-width="1"/>'
        f'<path d="M{x + r:.3f} {y + 1.6}H{x + kw - r:.3f}" stroke="#fff" stroke-opacity="{s["cap_shine"]:g}" stroke-width="1.4"/>'
        + glow + _glyph(glyph, gx, gy, s["glyph"]) + _legend(name, lx, ly, s["legend"])
        + "</g></svg>\n")


def all_keys():
    """{(slug, mode): svg}"""
    rows = layout()
    return {(slug(n), mode): build(n, g, W, kx, kw, mode, i == 0, i == len(rows) - 1)
            for i, (n, _, g, _, W, kx, kw) in enumerate(rows) for mode in ("dark", "light")}


def readme_row(base):
    """The README paragraph. One line on purpose: whitespace between the links
    would add gaps and could let the row wrap. Widths are percentages of the
    README column, rounded down so their sum never tips over 100%; no height,
    so each key keeps its proportions as it scales. align="top" (which GitHub
    keeps) pins every key's top to the line's top, so all five meet the
    banner's chin on the same pixel row."""
    cells = []
    for n, href, _, _, W, _, _ in layout():
        s = slug(n)
        pct = int(W / ROW_W * 100000) / 1000
        cells.append(f'<a href="{href}"><picture><source media="(prefers-color-scheme: dark)" '
                     f'srcset="{base}/links/{s}-dark.svg" /><img src="{base}/links/{s}-light.svg" '
                     f'width="{pct:g}%" align="top" alt="{n}" /></picture></a>')
    return '<p align="center">' + "".join(cells) + "</p>"
