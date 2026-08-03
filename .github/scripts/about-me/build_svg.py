#!/usr/bin/env python3
"""
Builds about-dark.template.svg / about-light.template.svg: one sparse, grainy
panel - a procedural ridgeline horizon under a blackletter wordmark.

Almost nothing here is drawn by hand. The ridges come out of seeded 1D
fractal value noise, the sky and stars out of gradients and feTurbulence. The
only baked asset is the wordmark outline in wordmark_path.py, because GitHub
renders README SVGs through camo as <img>, where no web font ever loads.

The `id=` fields are placeholders overwritten in-place by generate.py at CI
time. generate.py silently skips ids it cannot find, so this template can use
a subset of them without any change on that side.

Regenerate with:  python3 build_svg.py
"""
import os
import random

from links_path import LINKS, LINKS_CAP, LINKS_XHEIGHT
from wordmark_path import WORDMARK_CAP, WORDMARK_PATH, WORDMARK_WIDTH

HERE = os.path.dirname(os.path.abspath(__file__))

WIDTH = 1200
HEIGHT = 480

MONO = "ui-monospace,'SF Mono','SFMono-Regular','JetBrains Mono',Menlo,Consolas,monospace"

# Cap height is the optical anchor rather than font size: the baked path is
# normalised so its cap height is WORDMARK_CAP units, so this scales cleanly.
MARK_CAP = 82.0
MARK_BASELINE = 236.0

STAT_Y = 452.0

# Seconds for one ridge layer to travel a full period. Far layers move
# slowest: that speed difference is the parallax, and it is the only thing
# giving a flat stack of fills any sense of depth in motion.
RIDGE_DRIFT_S = [180, 130, 95, 65]

# The link row under the banner: one small blackletter image per destination,
# so the row is set in the same face as the name. Every word is drawn at the
# same cap height into an identical canvas and centred, which is what keeps
# the markdown table's cells equal - the widest word ("portfolio") sets the
# canvas, the rest get more air around them.
LINK_CAP = 22.0
LINK_W = 132
LINK_H = 46
LINK_BASELINE = 30.0
# One neutral tone rather than a dark/light pair: these sit directly on
# GitHub's page background, and this reads on both #ffffff and #0d1117 at the
# 3:1 large-text threshold, so the row needs no <picture> switching.
LINK_COLOR = "#7f90a8"
LINK_ORDER = ["site", "resume", "root@arfaz.ca", "linkedin", "desktop"]
LINK_HREF = {
    "site": "https://arfaz.ca",
    "resume": "https://arfaz.ca/resume",
    "root@arfaz.ca": "mailto:root@arfaz.ca",
    "linkedin": "https://linkedin.com/in/arfazca",
    "desktop": "https://desktop.arfaz.ca",
}
# Words given a double-width canvas.
LINK_WIDE = {"root@arfaz.ca"}
# A table cell is its image plus GitHub's fixed chrome - 13px padding each
# side plus the collapsed border, 27px total, which does not scale with the
# image. So a merely-doubled image yields a cell only ~1.79x its neighbours.
# Two adjacent cells span 2*img + 54 less the one border they share; matching
# that with a single cell needs 2*img + 26.
LINK_CELL_CHROME = 27
LINK_WIDE_W = LINK_W * 2 + LINK_CELL_CHROME - 1


def link_slug(name):
    """Filename-safe form of a link word: 'root@arfaz.ca' -> 'root-arfaz-ca'."""
    return "".join(c if c.isalnum() else "-" for c in name).strip("-")


# ---------------------------------------------------------------------------
# Seeded 1D fractal value noise. Deterministic on purpose: a rebuild with no
# source change has to produce a byte-identical file, or the daily workflow
# would churn the generated branch with a new horizon every morning.
# ---------------------------------------------------------------------------
class Ridge:
    """Summed octaves of smoothstep-interpolated value noise over [0, 1]."""

    def __init__(self, seed, octaves=4, lattice=5, gain=0.5):
        self.octaves = []
        self.norm = 0.0
        amp = 1.0
        for o in range(octaves):
            rng = random.Random(seed + o * 9781)
            n = lattice * (2**o)
            table = [rng.random() for _ in range(n + 1)]
            # Close the lattice so noise(1) == noise(0). This is what makes
            # the drift animation loop without a visible seam: the ridge is
            # drawn two periods wide and slid by exactly one, so the frame it
            # snaps back to is pixel-identical to the one it left. Smoothstep
            # has zero slope at lattice points, so the wrap is C1 too - no
            # crease where the ends meet.
            table[-1] = table[0]
            self.octaves.append((amp, table))
            self.norm += amp
            amp *= gain

    @staticmethod
    def _sample(table, x):
        n = len(table) - 1
        p = x * n
        i = min(int(p), n - 1)
        f = p - i
        t = f * f * (3 - 2 * f)  # smoothstep: C1-continuous, no lattice creases
        return table[i] + (table[i + 1] - table[i]) * t

    def at(self, x):
        return sum(amp * self._sample(tbl, x) for amp, tbl in self.octaves) / self.norm


def _fold(h, sharpness):
    """Fold noise about its midpoint: rounded humps become peaked ridges.

    Blended rather than absolute so it can be dialled per layer - near ridges
    read sharp and rocky, distant ones stay soft and hazy.
    """
    if not sharpness:
        return h
    return (1 - sharpness) * h + sharpness * (1 - abs(2 * h - 1))


def ridge_path(seed, base_y, amp, sharpness=0.0, lattice=5, step=7):
    """Closed path spanning two periods, so it can be slid by one and loop.

    Only the first period is ever on screen at once; the second exists purely
    to fill the gap the drift opens up on the right.
    """
    noise = Ridge(seed, lattice=lattice)
    span = WIDTH * 2
    xs = [x * 1.0 for x in range(0, span, step)] + [float(span)]
    pts = [(x, base_y - amp * _fold(noise.at((x / WIDTH) % 1.0), sharpness)) for x in xs]

    d = ["M0 %d" % HEIGHT]
    d += [f"L{px:.1f} {py:.1f}" for px, py in pts]
    d.append(f"L{span} {HEIGHT}Z")
    return "".join(d)


# ---------------------------------------------------------------------------
# Themes. In both modes the far ridges sit lighter than the near ones: that is
# atmospheric perspective - more air between you and the ridge means more
# light scattered back - and it is what sells depth on flat fills.
# ---------------------------------------------------------------------------
THEMES = {
    "dark": {  # night
        "sky": ["#070c14", "#0e1826", "#1b2a3f"],
        "glow": "#4a6f9e",
        "ridges": ["#334566", "#24334b", "#151e2c", "#080d15"],
        "mark": "#eceae5",
        "stat_key": "#61748c",
        "stat_val": "#a8bdd6",
        "grain": (255, 255, 255),
        "grain_bias": -0.22,
        "grain_opacity": 0.44,
        "stars": True,
    },
    "light": {  # dawn fog
        "sky": ["#eceae5", "#dee1e5", "#c6cfd7"],
        "glow": "#f4e6d1",
        "ridges": ["#bcc6d0", "#9aa8b6", "#75869a", "#4e6076"],
        "mark": "#141920",
        "stat_key": "#c3d0dc",
        "stat_val": "#f2f6fa",
        "grain": (18, 24, 32),
        "grain_bias": -0.24,
        "grain_opacity": 0.40,
        "stars": False,
    },
}

# Ridge layers, far to near: (seed, base_y, amplitude, sharpness, lattice).
# Raised and spread relative to a flat stack so each silhouette clears the one
# behind it - overlapping layers of similar height just read as one grey mass.
RIDGE_LAYERS = [
    # The farthest layer carries a denser lattice than its distance suggests:
    # at low amplitude a coarse one flattens into a straight band, which reads
    # as a horizon line rather than as hills behind hills.
    (1301, 298, 72, 0.15, 7),
    (2609, 344, 62, 0.35, 5),
    (3517, 392, 68, 0.55, 6),
    (4703, 450, 76, 0.75, 7),
]


def style(theme):
    """Animation only. GitHub serves these as <img>, where script never runs
    but declarative CSS animation does.
    """
    rules = []
    for i, secs in enumerate(RIDGE_DRIFT_S):
        rules.append(f".r{i}{{animation:drift {secs}s linear infinite}}")
    # Sliding by exactly WIDTH lands on the next period of a path that is
    # periodic by construction, so the restart is invisible.
    rules.append(
        f"@keyframes drift{{from{{transform:translateX(0)}}"
        f"to{{transform:translateX(-{WIDTH}px)}}}}"
    )
    # Everything above is decorative drift, so it all collapses to a still
    # frame. Base opacity is already 1, so nothing vanishes when it stops.
    rules.append(
        "@media(prefers-reduced-motion:reduce){.r0,.r1,.r2,.r3{animation:none}}"
    )
    return "<style>" + "".join(rules) + "</style>"


def defs(theme):
    sky = theme["sky"]
    gr, gg, gb = theme["grain"]
    out = [
        "<defs>",
        '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">',
        f'<stop offset="0" stop-color="{sky[0]}"/>',
        f'<stop offset="0.55" stop-color="{sky[1]}"/>',
        f'<stop offset="1" stop-color="{sky[2]}"/>',
        "</linearGradient>",
        # Skyglow: a bloom just above the horizon, pushed off centre so the
        # composition does not mirror itself around the wordmark.
        '<radialGradient id="glow" cx="0.62" cy="0.74" r="0.55">',
        f'<stop offset="0" stop-color="{theme["glow"]}" stop-opacity="0.55"/>',
        f'<stop offset="1" stop-color="{theme["glow"]}" stop-opacity="0"/>',
        "</radialGradient>",
        # Grain, as coloured speckle rather than a flat grey wash: white over
        # the night scene, ink over the pale one. Driving alpha instead of
        # luminance keeps it from lifting the blacks into mud.
        '<filter id="grain" x="0" y="0" width="100%" height="100%">',
        '<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="29" result="n"/>',
        # Two independent controls, and they do different jobs. The bias sets
        # coverage - how much of the noise field clears zero alpha and shows
        # up as a speck at all - while grain_opacity sets how hard those
        # specks hit. Pushing opacity alone just makes sparse grain glaring;
        # raising coverage is what actually reads as heavier film stock.
        '<feColorMatrix in="n" type="matrix" values="'
        f"0 0 0 0 {gr / 255:.4f} "
        f"0 0 0 0 {gg / 255:.4f} "
        f"0 0 0 0 {gb / 255:.4f} "
        f'0.62 0.26 0 0 {theme["grain_bias"]:.2f}"/>',
        "</filter>",
    ]
    if theme["stars"]:
        out += [
            # Thresholded noise. The steep alpha slope on the last matrix row
            # turns a smooth field into discrete points: only samples above
            # ~0.72 survive, the rest clamp to fully transparent.
            '<filter id="stars" x="0" y="0" width="100%" height="100%">',
            # Deliberately coarser than the grain's 0.9. At the heavier grain
            # setting the two sat at the same scale and the stars read as more
            # grain; separating the frequencies keeps them legible as points
            # of light.
            '<feTurbulence type="fractalNoise" baseFrequency="0.5" numOctaves="1" seed="17" result="n"/>',
            '<feColorMatrix in="n" type="matrix" values="'
            "0 0 0 0 1 "
            "0 0 0 0 1 "
            "0 0 0 0 1 "
            '5.2 0 0 0 -3.55"/>',
            "</filter>",
            # Stars thin out toward the horizon the way real skyglow washes
            # them, so the field never fights the ridgeline for attention.
            '<linearGradient id="starfade" x1="0" y1="0" x2="0" y2="1">',
            '<stop offset="0" stop-color="#fff" stop-opacity="0.95"/>',
            '<stop offset="0.7" stop-color="#fff" stop-opacity="0.18"/>',
            '<stop offset="1" stop-color="#fff" stop-opacity="0"/>',
            "</linearGradient>",
            '<mask id="starmask">',
            f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#starfade)"/>',
            "</mask>",
        ]
    out.append("</defs>")
    return "\n".join(out)


def build(mode):
    theme = THEMES[mode]
    scale = MARK_CAP / WORDMARK_CAP
    mark_x = (WIDTH - WORDMARK_WIDTH * scale) / 2

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Arfaz Hussain">',
        "<title>Arfaz Hussain</title>",
        style(theme),
        defs(theme),
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#sky)"/>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#glow)"/>',
    ]

    if theme["stars"]:
        # A single static field. The ridges still drift, so the sky needs no
        # tiling and no second seeded field to cross-fade against.
        parts.append(
            f'<g mask="url(#starmask)">'
            f'<rect width="{WIDTH}" height="{HEIGHT}" filter="url(#stars)"/>'
            f"</g>"
        )

    for i, ((seed, base_y, amp, sharp, lattice), fill) in enumerate(
        zip(RIDGE_LAYERS, theme["ridges"])
    ):
        parts.append(
            f'<path class="r{i}" d="{ridge_path(seed, base_y, amp, sharp, lattice)}" fill="{fill}"/>'
        )

    parts.append(
        f'<g transform="translate({mark_x:.2f} {MARK_BASELINE}) scale({scale:.5f})">'
        f'<path d="{WORDMARK_PATH}" fill="{theme["mark"]}"/></g>'
    )

    # text-anchor=middle centres the whole run, so the row stays centred even
    # after generate.py swaps in live numbers of a different width.
    parts.append(
        f'<text x="{WIDTH / 2:.0f}" y="{STAT_Y:.0f}" text-anchor="middle" xml:space="preserve" '
        # README embeds this at 720px against a 1200px viewBox, so everything
        # renders at 0.6x - type sized by eye at native scale ends up
        # unreadable there. 15px here is ~9px as actually seen.
        f'font-family="{MONO}" font-size="15" letter-spacing="1.9">'
        f'<tspan fill="{theme["stat_val"]}">software development engineer</tspan>'
        # age_data is generate.py's uptime_string(), counted from
        # BIRTHDAY = 2002-06-15 down to the day. It is now the only live field
        # left in the card; generate.py still computes commits and lines, but
        # nothing here consumes them any more.
        f'<tspan fill="{theme["stat_key"]}">     uptime </tspan>'
        f'<tspan fill="{theme["stat_val"]}" id="age_data">0</tspan>'
        "</text>"
    )

    parts.append(
        f'<rect width="{WIDTH}" height="{HEIGHT}" filter="url(#grain)" '
        f'opacity="{theme["grain_opacity"]}"/>'
    )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def _ink(entry, cap):
    """Scaled ink box of a baked word: (width, height, xmin, ymin)."""
    s = cap / LINKS_CAP
    xn, yn, xx, yx = entry["ink"]
    return (xx - xn) * s, (yx - yn) * s, xn * s, yn * s, s


def _link_baseline():
    """Shared baseline that balances the row's per-word ink centres.

    The words keep one baseline - centring each on its own ink would put
    'resume' (no ascender, no descender) at a different height from
    'portfolio' (both) and the row would jitter. So the only choice is where
    that shared baseline sits, and every fixed reference tried is wrong for
    this face:

      combined ink box  -> the four words without descenders sit ~2.5px high
      ascender band     -> overcorrects, words sit ~1.8px low
      x-height          -> still ~2.5px high; most of these words carry
                           ascenders, and this font's OS/2 x-height is short
                           of what it actually draws anyway

    So solve it instead of guessing: place the baseline so the mean of the
    words' own ink centres lands exactly on the cell centre. The row is then
    balanced against the actual set of words in it, whatever letters they
    happen to contain.
    """
    s = LINK_CAP / LINKS_CAP
    centres = [
        (LINKS[n]["ink"][1] + LINKS[n]["ink"][3]) / 2 * s for n in LINK_ORDER
    ]
    return LINK_H / 2 - sum(centres) / len(centres)


def build_link(name):
    """One link word, centred in the shared canvas.

    Centred on the ink box rather than the advance box. A font's advance
    includes side bearings, and they are not symmetric, so centring on advance
    width leaves the word visibly off-centre in its cell; the same applies
    vertically for words that carry descenders ('github', 'portfolio') against
    ones that do not ('site').
    """
    canvas_w = LINK_WIDE_W if name in LINK_WIDE else LINK_W
    w, _h, xn, _yn, s = _ink(LINKS[name], LINK_CAP)
    x = (canvas_w - w) / 2 - xn
    # Horizontally each word is centred on its own ink; vertically they all
    # share one baseline instead. Centring each word's own ink box vertically
    # would put 'resume' (no ascender, no descender) at a different height
    # from 'portfolio' (both), and the row would visibly jitter. The shared
    # baseline is placed so the row's combined ink box is centred.
    y = _link_baseline()
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{LINK_H}" '
        f'viewBox="0 0 {canvas_w} {LINK_H}" role="img" aria-label="{name}">'
        f"<title>{name}</title>"
        f'<g transform="translate({x:.2f} {y:.2f}) scale({s:.5f})">'
        f'<path d="{LINKS[name]["path"]}" fill="{LINK_COLOR}"/></g>'
        "</svg>\n"
    )


if __name__ == "__main__":
    for mode in ("dark", "light"):
        out_path = os.path.join(HERE, f"about-{mode}.template.svg")
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(build(mode))
        print("wrote", out_path)

    link_dir = os.path.join(HERE, "links")
    os.makedirs(link_dir, exist_ok=True)
    for name in LINK_ORDER:
        out_path = os.path.join(link_dir, f"{link_slug(name)}.svg")
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(build_link(name))
        print("wrote", out_path)
