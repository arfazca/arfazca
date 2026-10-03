#!/usr/bin/env python3
"""
The link row under the banner: a MacBook keyboard deck.

The banner is the display (black glass, aluminium rim, notch); this row is
the top case under it: one aluminium plate with the keys set into it, black
keys in Space Grey for dark mode, white keys in silver for light mode. Each
key is a lowercase legend bottom-left with a glyph top-right, like command
and option; the email gets a wide return key. In dark mode the legends are
faintly backlit, and now and then a key presses itself.

The row is laid out on the card's own 1200-unit grid and cut into five
images at the middle of each gap. Each image paints its own stretch of the
plate, rounded only at the row's two ends, so side by side they read as one
deck. In the README each image gets a percentage width, and the five add up
to just under 100%, so at any screen width the row stays on one line and
spans exactly the card. (A table would add GitHub's grey grid, and fixed
pixel widths wrap on narrow screens.)

    links/<slug>-<mode>.svg
"""
MONO = "ui-monospace,'SF Mono','SFMono-Regular','JetBrains Mono',Menlo,Consolas,monospace"

ROW_W = 1200          # the card's width, so the two scale together
GAP, PAD = 12, 10     # between keys, and between the end keys and the deck's ends
KEY_H, RADIUS = 74, 9
DECK_Y = 3            # a hairline of page between the display and the deck
DECK_R = 16           # the display's corner radius (banner.BEZEL_R)
KEY_Y = DECK_Y + 6.5  # the key's top, inside the plate
HEIGHT = 97           # deck: 3 to 96.5, so 6.5 units of metal above the keys, 7 below

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

# plate: gradient top to bottom, its outline, the shine along its top edge, and
# the shadowed hole round each key. cap: gradient, outline, shine, legend, glyph,
# backlight (None for none), shadow under the cap.
STYLE = {
    "dark": {
        "plate": ("#363a41", "#2c2f35"), "plate_edge": ("#000", 0.6), "plate_shine": 0.10,
        "well": ("#08090b", 0.9),
        "cap": ("#202329", "#121418", "#0b0c0f"), "cap_edge": ("#000", 1), "cap_shine": 0.10,
        "legend": "#dbe2ea", "glyph": "#dbe2ea", "backlight": "#9fc3ff", "shadow": 0.6,
    },
    "light": {
        "plate": ("#e4e7ea", "#d6d9dd"), "plate_edge": ("#000", 0.16), "plate_shine": 0.7,
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


def _plate(W, first, last):
    """This image's stretch of the deck: (fill path, outline path). Rounded
    only at the row's ends; no outline on a cut side, which would show as a
    seam between images."""
    y0, y1 = DECK_Y + 0.5, HEIGHT - 0.5
    lr, rr = (DECK_R if first else 0), (DECK_R if last else 0)
    top = f"M{lr} {y0}H{W - rr:.3f}"
    right = (f"A{rr} {rr} 0 0 1 {W:.3f} {y0 + rr}V{y1 - rr}A{rr} {rr} 0 0 1 {W - rr:.3f} {y1}" if rr
             else f"V{y1}")
    bottom = f"H{lr}"
    left = f"A{lr} {lr} 0 0 1 0 {y1 - lr}V{y0 + lr}A{lr} {lr} 0 0 1 {lr} {y0}" if lr else f"V{y0}"
    fill = top + right + bottom + left + "Z"
    if first and last:
        outline = fill
    elif first:
        outline = f"M{W:.3f} {y1}H{lr}{left}H{W:.3f}"
    elif last:
        outline = top + right + "H0"
    else:
        outline = f"M0 {y0}H{W:.3f}M0 {y1}H{W:.3f}"
    return fill, outline


def build(name, glyph, W, kx, kw, mode, first, last):
    s = STYLE[mode]
    cyc, start = PRESS[name]
    at = 6.0
    p0, p1, p2 = at / cyc * 100, (at + 0.09) / cyc * 100, (at + 0.24) / cyc * 100
    style = (f".k{{animation:k {cyc}s ease-out infinite;animation-delay:{start - at:.2f}s}}"
             f"@keyframes k{{0%,{p0:.3f}%,{p2:.3f}%,100%{{transform:none}}{p1:.3f}%{{transform:translateY(1.6px)}}}}"
             "@media(prefers-reduced-motion:reduce){*{animation:none!important}}")
    x, y, r, kh = kx, KEY_Y, RADIUS, KEY_H
    fill, outline = _plate(W, first, last)
    (p0c, p1c), (ec, eo), (wc, wo) = s["plate"], s["plate_edge"], s["well"]
    lr, rr = (DECK_R if first else 0), (DECK_R if last else 0)
    plate = (f'<path d="{fill}" fill="url(#pg)"/>'
             f'<path d="{outline}" fill="none" stroke="{ec}" stroke-opacity="{eo:g}" stroke-width="1"/>'
             f'<path d="M{lr + 2} {DECK_Y + 1.6}H{W - rr - 2:.3f}" stroke="#fff" stroke-opacity="{s["plate_shine"]:g}" stroke-width="1"/>'
             # the hole the key sits in
             f'<rect x="{x - 2.5:.3f}" y="{y - 2.5}" width="{kw + 5:.3f}" height="{kh + 5}" rx="{r + 2.5}" '
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
    so each key keeps its proportions as it scales."""
    cells = []
    for n, href, _, _, W, _, _ in layout():
        s = slug(n)
        pct = int(W / ROW_W * 100000) / 1000
        cells.append(f'<a href="{href}"><picture><source media="(prefers-color-scheme: dark)" '
                     f'srcset="{base}/links/{s}-dark.svg" /><img src="{base}/links/{s}-light.svg" '
                     f'width="{pct:g}%" alt="{n}" /></picture></a>')
    return '<p align="center">' + "".join(cells) + "</p>"
