#!/usr/bin/env python3
import base64
import math
import os
import random
import struct

from wordmark_path import WORDMARK_CAP, WORDMARK_PATH, WORDMARK_WIDTH

HERE = os.path.dirname(os.path.abspath(__file__))
SPRITES = os.path.join(HERE, "sprites")

WIDTH = 1200
HEIGHT = 480

MONO = "ui-monospace,'SF Mono','SFMono-Regular','JetBrains Mono',Menlo,Consolas,monospace"

MARK_CAP = 82.0
MARK_BASELINE = 236.0
STAT_Y = 452.0

RIDGE_DRIFT_S = [72, 52, 38, 26]

RIM = 1.6
METAL = 6.5
GLASS = 1.2
FRAME = round(RIM + METAL + GLASS, 3)
BEZEL_R = 16
CHIN = 4

SPRITE_SCALE = 0.66


class Ridge:
    def __init__(self, seed, octaves=4, lattice=5, gain=0.5):
        self.octaves = []
        self.norm = 0.0
        amp = 1.0
        for o in range(octaves):
            rng = random.Random(seed + o * 9781)
            n = lattice * (2**o)
            table = [rng.random() for _ in range(n + 1)]
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
        t = f * f * (3 - 2 * f)
        return table[i] + (table[i + 1] - table[i]) * t

    def at(self, x):
        return sum(amp * self._sample(tbl, x) for amp, tbl in self.octaves) / self.norm


def _fold(h, sharpness):
    if not sharpness:
        return h
    return (1 - sharpness) * h + sharpness * (1 - abs(2 * h - 1))


def ridge_path(seed, base_y, amp, sharpness=0.0, lattice=5, step=7):
    noise = Ridge(seed, lattice=lattice)
    span = WIDTH * 2
    xs = [x * 1.0 for x in range(0, span, step)] + [float(span)]
    pts = [(x, base_y - amp * _fold(noise.at((x / WIDTH) % 1.0), sharpness)) for x in xs]
    d = ["M0 %d" % HEIGHT]
    d += [f"L{px:.1f} {py:.1f}" for px, py in pts]
    d.append(f"L{span} {HEIGHT}Z")
    return "".join(d)


THEMES = {
    "dark": {
        "sky": ["#070c14", "#0e1826", "#1b2a3f"],
        "glow": "#4a6f9e",
        "ridges": ["#334566", "#24334b", "#151e2c", "#080d15"],
        "mark": "#eceae5",
        "stat_key": "#61748c",
        "stat_val": "#a8bdd6",
        "grain": (255, 255, 255),
        "grain_bias": -0.22,
        "grain_opacity": 0.44,
        "rim": "#5d636c",
        "plate": ("#363a41", "#2c2f35"),
    },
    "light": {
        "sky": ["#eceae5", "#dee1e5", "#c6cfd7"],
        "glow": "#f4e6d1",
        "ridges": ["#bcc6d0", "#9aa8b6", "#75869a", "#4e6076"],
        "mark": "#141920",
        "stat_key": "#c3d0dc",
        "stat_val": "#f2f6fa",
        "grain": (18, 24, 32),
        "grain_bias": -0.24,
        "grain_opacity": 0.40,
        "rim": "#c3c7cd",
        "plate": ("#e4e7ea", "#d6d9dd"),
    },
}

RIDGE_LAYERS = [
    (1301, 298, 72, 0.15, 7),
    (2609, 344, 62, 0.35, 5),
    (3517, 392, 68, 0.55, 6),
    (4703, 450, 76, 0.75, 7),
]
_RIDGES = [ridge_path(*layer) for layer in RIDGE_LAYERS]


def kf(name, cycle, pts, prop="opacity"):
    pts = sorted(pts, key=lambda p: p[0])
    if pts[0][0] > 0:
        pts.insert(0, (0, pts[0][1]))
    if pts[-1][0] < cycle:
        pts.append((cycle, pts[-1][1]))
    body, last = [], -1.0
    for s, v in pts:
        p = max(round(100 * s / cycle, 3), last + 0.001)
        last = p
        body.append(f"{p:g}%{{{v if prop is None else f'{prop}:{v}'}}}")
    return f"@keyframes {name}{{{''.join(body)}}}"


def anim(sel, name, cycle, delay=0.0, timing="linear"):
    return f"{sel}{{animation:{name} {cycle}s {timing} infinite;animation-delay:{delay:.2f}s}}"


def once(sel, name, secs, delay, timing="ease-out"):
    return f"{sel}{{animation:{name} {secs}s {timing} {delay:.2f}s both}}"


def flicker(at, peak=1.0):
    return [(at - 0.01, 0), (at + 0.03, peak), (at + 0.09, peak * 0.12),
            (at + 0.15, peak * 0.95), (at + 0.32, peak * 0.3), (at + 0.7, 0)]


class Scene:
    def __init__(self, mode):
        self.mode = mode
        self.t = THEMES[mode]
        rules = [f".r{i}{{animation:drift {s}s linear infinite}}" for i, s in enumerate(RIDGE_DRIFT_S)]
        rules.append(f"@keyframes drift{{from{{transform:translateX(0)}}to{{transform:translateX(-{WIDTH}px)}}}}")
        self.css = rules
        self.defs = []
        self.sky = []
        self.front = []
        self.over = []
        self.top = []

    def _base_defs(self):
        t = self.t
        sky = t["sky"]
        gr, gg, gb = t["grain"]
        return [
            '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{sky[0]}"/><stop offset="0.55" stop-color="{sky[1]}"/>'
            f'<stop offset="1" stop-color="{sky[2]}"/></linearGradient>',
            '<radialGradient id="glow" cx="0.62" cy="0.74" r="0.55">'
            f'<stop offset="0" stop-color="{t["glow"]}" stop-opacity="0.55"/>'
            f'<stop offset="1" stop-color="{t["glow"]}" stop-opacity="0"/></radialGradient>',
            '<filter id="grain" x="0" y="0" width="100%" height="100%">'
            '<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="29" result="n"/>'
            '<feColorMatrix in="n" type="matrix" values="'
            f"0 0 0 0 {gr / 255:.4f} 0 0 0 0 {gg / 255:.4f} 0 0 0 0 {gb / 255:.4f} "
            f'0.62 0.26 0 0 {t["grain_bias"]:.2f}"/></filter>',
            f'<clipPath id="slab"><path d="{_lid(0, HEIGHT)}"/></clipPath>',
        ]

    def render(self, age):
        t = self.t
        rm = "@media(prefers-reduced-motion:reduce){*{animation:none!important}}"
        scale = MARK_CAP / WORDMARK_CAP
        mark_x = (WIDTH - WORDMARK_WIDTH * scale) / 2
        ridges = [f'<path class="r{i}" d="{d}" fill="{fill}"/>' for i, (d, fill) in enumerate(zip(_RIDGES, t["ridges"]))]
        scene = [
            f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#sky)"/>',
            f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#glow)"/>',
            *self.sky, *ridges, *self.front,
            f'<g transform="translate({mark_x:.2f} {MARK_BASELINE}) scale({scale:.5f})">'
            f'<path d="{WORDMARK_PATH}" fill="{t["mark"]}"/></g>',
            f'<text x="{WIDTH / 2:.0f}" y="{STAT_Y:.0f}" text-anchor="middle" xml:space="preserve" '
            f'font-family="{MONO}" font-size="15" letter-spacing="1.9">'
            f'<tspan fill="{t["stat_val"]}">software development engineer</tspan>'
            f'<tspan fill="{t["stat_key"]}">     uptime </tspan>'
            f'<tspan fill="{t["stat_val"]}" id="age_data">{age}</tspan>'
            "</text>",
            *self.over,
            f'<rect width="{WIDTH}" height="{HEIGHT}" filter="url(#grain)" opacity="{t["grain_opacity"]}"/>',
        ]
        g = round(RIM + METAL, 3)
        glass = _rrect(g, g, WIDTH - 2 * g, HEIGHT - CHIN - g, BEZEL_R - g)
        screen = _rrect(FRAME, FRAME, WIDTH - 2 * FRAME, HEIGHT - CHIN - g - 2 * GLASS, BEZEL_R - FRAME)
        p0, _ = t["plate"]
        out = [
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Arfaz Hussain">',
            "<title>Arfaz Hussain</title>",
            "<style>" + "".join(self.css) + rm + "</style>",
            "<defs>", *self._base_defs(), *self.defs, "</defs>",
            '<g clip-path="url(#slab)">', *scene, "</g>",
            f'<g transform="translate(0 {FRAME:g})">', *self.top, "</g>",
            f'<path d="{_lid(0, HEIGHT)}{_lid(RIM, HEIGHT)}" fill="{t["rim"]}" fill-rule="evenodd"/>',
            f'<path d="{_lid(RIM, HEIGHT)}{glass}" fill="{p0}" fill-rule="evenodd"/>',
            f'<path d="{glass}{screen}" fill="#000" fill-rule="evenodd"/>',
            "</svg>",
        ]
        return "\n".join(out) + "\n"


def _lid(a, bottom):
    r = BEZEL_R - a
    return (f"M{a} {bottom}V{a + r}A{r} {r} 0 0 1 {a + r} {a}H{WIDTH - a - r}"
            f"A{r} {r} 0 0 1 {WIDTH - a} {a + r}V{bottom}Z")


def _rrect(x, y, w, h, r):
    return (f"M{x + r} {y}H{x + w - r}A{r} {r} 0 0 1 {x + w} {y + r}V{y + h - r}"
            f"A{r} {r} 0 0 1 {x + w - r} {y + h}H{x + r}A{r} {r} 0 0 1 {x} {y + h - r}"
            f"V{y + r}A{r} {r} 0 0 1 {x + r} {y}Z")


STAR_COLORS = ["#ffffff", "#e4ecff", "#cfdcff", "#fff3e0", "#ffe6c7"]
NOTCH_BOX = (400, 0, 800, 60)
WORDMARK_INK = (280.1, 149.1, 919.9, 257.9)


def _in_box(x, y, box, pad=0):
    x0, y0, x1, y1 = box
    return x0 - pad <= x <= x1 + pad and y0 - pad <= y <= y1 + pad


def stars(sc, seed=41, n=165, ymax=300, bright=9, glints=3):
    rng = random.Random(seed)
    sc.defs.append(
        '<radialGradient id="halo"><stop offset="0" stop-color="#dfe9ff" stop-opacity=".6"/>'
        '<stop offset=".3" stop-color="#dfe9ff" stop-opacity=".14"/>'
        '<stop offset="1" stop-color="#dfe9ff" stop-opacity="0"/></radialGradient>')
    durs = [1.9, 2.7, 3.6, 4.9, 6.4]
    sc.css += [f".t{k}{{animation:tw {d}s ease-in-out infinite}}" for k, d in enumerate(durs)]
    sc.css.append("@keyframes tw{0%,100%{opacity:1}45%{opacity:.22}60%{opacity:.85}}"
                  ".gl{transform-box:fill-box;transform-origin:center;animation:gl 5.3s ease-in-out infinite}"
                  "@keyframes gl{0%,100%{transform:scale(1);opacity:1}50%{transform:scale(.62);opacity:.7}}")
    out, placed = [], 0
    while placed < n:
        x = rng.uniform(6, WIDTH - 6)
        y = 4 + (ymax - 4) * (rng.random() ** 1.3)
        if _in_box(x, y, NOTCH_BOX):
            continue
        tier = "bright" if placed < bright else ("mid" if rng.random() < 0.3 else "faint")
        if tier == "bright" and _in_box(x, y, WORDMARK_INK, 30):
            continue
        placed += 1
        fade = 1 - 0.65 * (y / ymax) ** 2
        col = rng.choice(STAR_COLORS)
        delay = -rng.uniform(0, 6)
        tw = f' class="t{rng.randrange(len(durs))}" style="animation-delay:{delay:.2f}s"'
        if tier in ("faint", "mid"):
            lo, hi, olo, ohi, p = (0.6, 0.95, 0.45, 0.75, .35) if tier == "faint" else (0.95, 1.35, 0.7, 0.95, .6)
            r, fo = rng.uniform(lo, hi), rng.uniform(olo, ohi) * fade
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="{col}" fill-opacity="{fo:.2f}"'
                       f'{tw if rng.random() < p else ""}/>')
        else:
            r = rng.uniform(1.45, 2.0)
            g = [f'<circle r="{r * 6:.1f}" fill="url(#halo)"/>']
            if placed <= glints:
                L, w = rng.uniform(9, 13), 0.55
                g.append(f'<g class="gl" style="animation-delay:{delay:.2f}s">'
                         f'<path d="M{-L:.1f} 0L0 {-w}L{L:.1f} 0L0 {w}ZM0 {-L:.1f}L{w} 0L0 {L:.1f}L{-w} 0Z" '
                         f'fill="{col}" fill-opacity=".85"/></g>')
            g.append(f'<circle r="{r:.2f}" fill="{col}"/>')
            out.append(f'<g transform="translate({x:.1f} {y:.1f})"><g{tw}>{"".join(g)}</g></g>')
    return "".join(out)


def moon(sc):
    sc.defs.append('<radialGradient id="moonhalo"><stop offset="0" stop-color="#d9e3f2" stop-opacity=".35"/>'
                   '<stop offset=".25" stop-color="#d9e3f2" stop-opacity=".1"/>'
                   '<stop offset="1" stop-color="#d9e3f2" stop-opacity="0"/></radialGradient>'
                   '<mask id="cres"><circle cx="150" cy="64" r="10" fill="#fff"/>'
                   '<circle cx="155.5" cy="61" r="9.2" fill="#000"/></mask>')
    return ('<circle cx="150" cy="64" r="78" fill="url(#moonhalo)"/>'
            '<circle cx="150" cy="64" r="10" fill="#c9d3e3" fill-opacity=".1"/>'
            '<circle cx="150" cy="64" r="10" fill="#f3efe4" mask="url(#cres)"/>')


def venus(sc):
    sc.defs.append('<radialGradient id="venus"><stop offset="0" stop-color="#fff" stop-opacity=".95"/>'
                   '<stop offset=".25" stop-color="#fff6e6" stop-opacity=".35"/>'
                   '<stop offset="1" stop-color="#fff6e6" stop-opacity="0"/></radialGradient>')
    sc.css.append(".venus{animation:venus 4.2s ease-in-out infinite}@keyframes venus{0%,100%{opacity:1}50%{opacity:.6}}")
    return ('<g class="venus"><circle cx="985" cy="92" r="16" fill="url(#venus)"/>'
            '<circle cx="985" cy="92" r="2.1" fill="#fffdf6"/></g>')


def meteor(sc, cls, x, y, ang, length, travel, cycle, first_at, dur=0.85):
    local = cycle * 0.5
    sc.css.append(kf(cls, cycle, [
        (local - 0.01, "transform:translateX(0);opacity:0"),
        (local + 0.1, f"transform:translateX({travel * 0.1 / dur:.1f}px);opacity:1"),
        (local + dur * 0.7, f"transform:translateX({travel * 0.7:.1f}px);opacity:.9"),
        (local + dur, f"transform:translateX({travel:.1f}px);opacity:0"),
    ], prop=None) + anim(f".{cls}", cls, cycle, first_at - local))
    return (f'<g transform="translate({x:.0f} {y:.0f}) rotate({ang:.0f})"><g class="{cls}" opacity="0">'
            f'<path d="M0 -1.2L{-length:.0f} 0L0 1.2Z" fill="url(#mtail)"/>'
            f'<circle r="1.5" fill="#fff"/><circle r="5" fill="#fff" fill-opacity=".18"/></g></g>')


def _sprite(name, mode):
    raw = open(os.path.join(SPRITES, f"{name}-{mode}.png"), "rb").read()
    w, h = struct.unpack(">II", raw[16:24])
    return w / SPRITE_SCALE, h / SPRITE_SCALE, base64.b64encode(raw).decode()


def _use(name, size, x, y, s, mirror=False, extra=""):
    w, _ = size
    tx = x + w * s if mirror else x
    return (f'<use xlink:href="#c-{name}" transform="translate({tx:.1f} {y:.1f}) '
            f'scale({-s if mirror else s:.3f} {s:.3f})"{extra}/>')


def drift_css(cls, secs, phase=0.0):
    return (f".{cls}{{animation:{cls} {secs}s linear infinite;animation-delay:{-phase * secs:.1f}s}}"
            f"@keyframes {cls}{{to{{transform:translateX(-{WIDTH}px)}}}}")


def tiled(items, sizes):
    out = []
    for name, x, y, s, op, mir in items:
        w, _ = sizes[name]
        for k in (-1, 0, 1, 2):
            xx = x + k * WIDTH
            if xx + w * s > 0 and xx < 2 * WIDTH:
                out.append(_use(name, sizes[name], xx, y, s, mir, f' opacity="{op:.2f}"'))
    return "".join(out)


def rain_pattern(sc, pid, seed, tw, th, n, lmin, lmax, sw, color, op):
    rng = random.Random(seed)
    lines = []
    for _ in range(n):
        x, y, L = rng.uniform(0, tw), rng.uniform(0, th), rng.uniform(lmin, lmax)
        for dy in ((0, -th) if y + L > th else (0,)):
            lines.append(f'<line x1="{x:.1f}" y1="{y + dy:.1f}" x2="{x:.1f}" y2="{y + dy + L:.1f}"/>')
    sc.defs.append(f'<pattern id="{pid}" width="{tw}" height="{th}" patternUnits="userSpaceOnUse">'
                   f'<g stroke="{color}" stroke-width="{sw}" stroke-opacity="{op}" stroke-linecap="round">'
                   f'{"".join(lines)}</g></pattern>')


def fall_css(cls, th, secs):
    return f".{cls}{{animation:{cls} {secs}s linear infinite}}@keyframes {cls}{{to{{transform:translateY({th}px)}}}}"


def _bolt_pts(rng, x0, y0, x1, y1, levels, disp):
    pts = [(x0, y0), (x1, y1)]
    for _ in range(levels):
        nxt = [pts[0]]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            L = math.hypot(bx - ax, by - ay) or 1
            off = rng.gauss(0, 1) * L * disp
            nxt += [((ax + bx) / 2 - (by - ay) / L * off, (ay + by) / 2 + (bx - ax) / L * off), (bx, by)]
        pts = nxt
    return pts


def _d(pts):
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts)


def bolt(seed, x0, y0, x1, y1, core, glow, branches=3):
    rng = random.Random(seed)
    main = _bolt_pts(rng, x0, y0, x1, y1, 7, 0.2)
    br = []
    for _ in range(branches):
        i = rng.randrange(len(main) // 8, int(len(main) * 0.6))
        bx, by = main[i]
        ex, ey = bx + rng.choice((-1, 1)) * rng.uniform(35, 95), by + rng.uniform(45, 110)
        br.append(_d(_bolt_pts(rng, bx, by, ex, ey, 5, 0.24)))
    md, bd = _d(main), "".join(br)
    return (f'<g fill="none" stroke-linecap="round" stroke-linejoin="round">'
            f'<path d="{md}{bd}" stroke="{glow}" stroke-width="12" stroke-opacity=".12"/>'
            f'<path d="{md}{bd}" stroke="{glow}" stroke-width="5" stroke-opacity=".34"/>'
            f'<path d="{bd}" stroke="{core}" stroke-width="1.1" stroke-opacity=".8"/>'
            f'<path d="{md}" stroke="{core}" stroke-width="2"/></g>')


NOTCH_KEY = "#61748c"
NOTCH_VAL = "#a8bdd6"
NOTCH_BOLD = "#eef3f8"
NOTCH_W, NOTCH_H = 340, 36
NOTCH_FS = 14


def notch_path(cx, w, h, rf=10, rb=14):
    l, r, k = cx - w / 2, cx + w / 2, 0.5523
    return (f"M{l - rf:.1f} -2L{l - rf:.1f} 0C{l - rf + rf * k:.1f} 0 {l:.1f} {rf - rf * k:.1f} {l:.1f} {rf}"
            f"L{l:.1f} {h - rb}C{l:.1f} {h - rb + rb * k:.1f} {l + rb - rb * k:.1f} {h} {l + rb:.1f} {h}"
            f"L{r - rb:.1f} {h}C{r - rb + rb * k:.1f} {h} {r:.1f} {h - rb + rb * k:.1f} {r:.1f} {h - rb}"
            f"L{r:.1f} {rf}C{r:.1f} {rf - rf * k:.1f} {r + rf - rf * k:.1f} 0 {r + rf:.1f} 0L{r + rf:.1f} -2Z")


def notch_text(parts, x, y):
    spans = []
    for text, kind, pid in parts:
        fill = {"key": NOTCH_KEY, "val": NOTCH_VAL, "bold": NOTCH_BOLD}[kind]
        weight = ' font-weight="700"' if kind == "bold" else ""
        ident = f' id="{pid}"' if pid else ""
        spans.append(f'<tspan fill="{fill}"{weight}{ident}>{text}</tspan>')
    return (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" xml:space="preserve" font-family="{MONO}" '
            f'font-size="{NOTCH_FS}" letter-spacing="1.9">{"".join(spans)}</text>')


STATUS = {
    "clear": [("clear", "bold", None), (" skies", "val", None), (" now", "key", None)],
    "cloudy": [("overcast", "bold", None), (", dry", "val", None), (" now", "key", None)],
    "drizzle": [("drizzle", "bold", None), (", light", "val", None), (" now", "key", None)],
    "rain": [("rain", "bold", None), (", steady", "val", None), (" now", "key", None)],
    "storm": [("storm", "bold", None), (", heavy rain", "val", None), (" now", "key", None)],
}


def _icon(state, mode):
    v, b = NOTCH_VAL, NOTCH_BOLD
    cloud = f'<path d="M-7 1a5 5 0 0 1 2-8a6 6 0 0 1 11 1a4 4 0 0 1 1 7Z" fill="{v}"/>'
    drops = {"drizzle": (-3, 2), "rain": (-4.5, 0.5, 5.5), "storm": (-4.5, 5.5)}
    if state == "clear":
        if mode == "dark":
            return f'<path d="M2 -7a7 7 0 1 0 5 11a6 6 0 0 1 -5 -11Z" fill="{v}"/>'
        rays = "".join(f"M{math.cos(a) * 6:.1f} {math.sin(a) * 6:.1f}L{math.cos(a) * 8.5:.1f} {math.sin(a) * 8.5:.1f}"
                       for a in [i * math.pi / 4 for i in range(8)])
        return f'<circle r="3.6" fill="{v}"/><path d="{rays}" stroke="{v}" stroke-width="1.4" stroke-linecap="round"/>'
    g = cloud
    if state in drops:
        d = "".join(f"M{x} 5l-1.4 3.6" for x in drops[state])
        g += f'<path d="{d}" stroke="{b}" stroke-width="1.6" stroke-linecap="round" fill="none"/>'
    if state == "storm":
        g += f'<path d="M1 4l-2.5 4h2.5l-1.5 4" stroke="#ffd36a" stroke-width="1.4" fill="none" stroke-linejoin="round"/>'
    return g


def notch(sc, state, day, mode):
    sc.defs.append('<filter id="nsh" x="-20%" y="-50%" width="140%" height="220%">'
                   '<feGaussianBlur stdDeviation="5"/></filter>')
    w, h, rf, rb, bump = NOTCH_W, NOTCH_H, 10, 14, 14
    l, r, k = 600 - w / 2, 600 + w / 2, 0.5523
    left = (f"M{l - rf} -2L{l - rf} 0C{l - rf + rf * k:.1f} 0 {l} {rf - rf * k:.1f} {l} {rf}"
            f"L{l} {h - rb}C{l} {h - rb + rb * k:.1f} {l + rb - rb * k:.1f} {h} {l + rb} {h}L{l + rb + 2} {h}"
            f"L{l + rb + 2} -2Z")
    right = (f"M{r + rf} -2L{r + rf} 0C{r + rf - rf * k:.1f} 0 {r} {rf - rf * k:.1f} {r} {rf}"
             f"L{r} {h - rb}C{r} {h - rb + rb * k:.1f} {r - rb + rb * k:.1f} {h} {r - rb} {h}L{r - rb - 2} {h}"
             f"L{r - rb - 2} -2Z")
    mid_w = w - 2 * rb
    sb = (mid_w + 2 * bump) / mid_w
    cyc, on, off = 17, 3.2, 7.6

    def spring(t, a, b):
        return [(t - 0.01, a), (t + 0.22, b), (t + 0.6, a)]
    sc.css += [
        kf("nl", cyc, spring(on, "transform:translateX(0)", f"transform:translateX({-bump}px)")
           + spring(off, "transform:translateX(0)", f"transform:translateX({-bump}px)"), None),
        kf("nr", cyc, spring(on, "transform:translateX(0)", f"transform:translateX({bump}px)")
           + spring(off, "transform:translateX(0)", f"transform:translateX({bump}px)"), None),
        kf("nm", cyc, spring(on, "transform:scaleX(1)", f"transform:scaleX({sb:.4f})")
           + spring(off, "transform:scaleX(1)", f"transform:scaleX({sb:.4f})"), None),
        kf("ndate", cyc, [(on + 0.05, 1), (on + 0.2, 0), (off + 0.25, 0), (off + 0.45, 1)]),
        kf("nwx", cyc, [(on + 0.25, 0), (on + 0.45, 1), (off + 0.05, 1), (off + 0.2, 0)]),
        "".join(anim(f".{c}", c, cyc, 0, "ease-out") for c in ("nl", "nr", "nm", "ndate", "nwx")),
        ".nm{transform-origin:600px 0px}",
        ".boot{transform-origin:600px 0px;animation:boot 1.1s cubic-bezier(.3,1.35,.5,1) .25s both}"
        "@keyframes boot{from{transform:scale(.32,.55)}to{transform:scale(1,1)}}"
        ".bootT{animation:bootT .5s ease-out .95s both}"
        "@keyframes bootT{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:none}}",
    ]
    by = h / 2 + NOTCH_FS * 0.36
    status = STATUS[state]
    n = sum(len(t) for t, _, _ in status)
    tx = 600 + 12
    gx = tx - n * (NOTCH_FS * 0.602 + 1.9) / 2 - 16
    sc.top.append(
        '<g class="boot">'
        f'<path d="{notch_path(600, w, h)}" fill="#000" opacity=".45" transform="translate(0 3)" filter="url(#nsh)"/>'
        f'<path class="nl" d="{left}" fill="#000"/>'
        f'<rect class="nm" x="{l + rb}" y="-2" width="{mid_w}" height="{h + 2}" fill="#000"/>'
        f'<path class="nr" d="{right}" fill="#000"/>'
        '<g class="bootT">'
        '<g class="ndate">' + notch_text([(day["dow"], "bold", "date_dow"), (", " + day["md"], "val", "date_md"),
                                          (" " + day["year"], "key", "date_year")], 600, by) + "</g>"
        f'<g class="nwx" opacity="0"><g transform="translate({gx:.1f} {h / 2 - 1})">{_icon(state, mode)}</g>'
        + notch_text(status, tx, by) + "</g></g></g>")


STATES = {
    "clear":   {"cover": 0.18, "rain": 0, "deck": 0.00},
    "cloudy":  {"cover": 0.85, "rain": 0, "deck": 0.55},
    "drizzle": {"cover": 0.90, "rain": 1, "deck": 0.70},
    "rain":    {"cover": 1.00, "rain": 2, "deck": 0.85},
    "storm":   {"cover": 1.00, "rain": 3, "deck": 1.00},
}


def render(mode, state, variant, day):
    dark = mode == "dark"
    P = STATES[state]
    rng = random.Random(f"{state}/{variant}/{mode}")
    sc = Scene(mode)
    used = ["mid", "small", "flat"] + (["storm"] if P["deck"] or P["rain"] else [])
    sizes = {}
    for name in used:
        w, h, b = _sprite(name, mode)
        sizes[name] = (w, h)
        sc.defs.append(f'<image id="c-{name}" width="{w:.1f}" height="{h:.1f}" preserveAspectRatio="none" '
                       f'xlink:href="data:image/png;base64,{b}"/>')
    rain_col = "#b4c6de" if dark else "#56667a"
    flash_c = "#cfe0ff" if dark else "#ffffff"

    if dark:
        sc.defs.append(
            '<filter id="mw" x="0" y="0" width="100%" height="100%">'
            '<feTurbulence type="fractalNoise" baseFrequency="0.012 0.03" numOctaves="4" seed="5" result="n"/>'
            '<feColorMatrix in="n" type="matrix" values="0 0 0 0 .78 0 0 0 0 .84 0 0 0 0 1 1.3 0 0 0 -.55"/></filter>'
            '<linearGradient id="mwband" x1="0" y1="1" x2="1" y2="0">'
            '<stop offset=".25" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".9"/>'
            '<stop offset=".72" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            f'<mask id="mwm"><rect width="{WIDTH}" height="{HEIGHT}" fill="url(#mwband)"/></mask>')
        sky_vis = 1 - 0.8 * P["cover"]
        sc.sky.append(f'<g mask="url(#mwm)" opacity="{0.28 * sky_vis:.2f}"><rect width="{WIDTH}" height="320" filter="url(#mw)"/></g>')
        sc.sky.append(f'<g opacity="{max(sky_vis, 0.15):.2f}">{stars(sc)}</g>')
        sc.sky.append(f'<g opacity="{1 - 0.55 * P["cover"]:.2f}">{moon(sc)}</g>')
        if state in ("clear", "cloudy"):
            sc.defs.append('<linearGradient id="mtail" x1="0" y1="0" x2="1" y2="0">'
                           '<stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                           '<stop offset=".8" stop-color="#fff" stop-opacity=".5"/>'
                           '<stop offset="1" stop-color="#fff" stop-opacity="1"/></linearGradient>')
            plan = [(41, 3.5), (67, 21.0), (97, 47.0)] if state == "clear" else [(89, 12.0)]
            for i, (cyc, first) in enumerate(plan):
                left = rng.random() < 0.5
                x = rng.uniform(220, 420) if left else rng.uniform(820, 1040)
                ang = rng.uniform(22, 34) if left else rng.uniform(146, 158)
                sc.sky.append(meteor(sc, f"m{i}", x, rng.uniform(20, 60), ang, rng.uniform(90, 140),
                                     rng.uniform(220, 300), cyc, first))
    elif state in ("clear", "cloudy"):
        sc.sky.append(f'<g opacity="{1 - 0.6 * P["cover"]:.2f}">{venus(sc)}</g>')
    if not dark and P["deck"]:
        sc.defs.append('<linearGradient id="tint" x1="0" y1="0" x2="0" y2="1">'
                       '<stop offset="0" stop-color="#4c5869" stop-opacity=".8"/>'
                       '<stop offset=".62" stop-color="#6b7787" stop-opacity=".35"/>'
                       '<stop offset="1" stop-color="#6b7787" stop-opacity="0"/></linearGradient>')
        sc.sky.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#tint)" opacity="{P["deck"]:.2f}"/>')

    bolts, bolts_svg = [], []
    if state == "storm":
        for gid, cx in (("fA", 0.18), ("fB", 0.82), ("fC", 0.5), ("hz", 0.5)):
            sc.defs.append(f'<radialGradient id="{gid}" cx="{cx}" cy="{".75" if gid == "hz" else ".25"}" r=".75">'
                           f'<stop offset="0" stop-color="{flash_c}"/>'
                           f'<stop offset="1" stop-color="{flash_c}" stop-opacity="0"/></radialGradient>')
        bolts = [("bA", rng.uniform(140, 260), 19, 9.0, "fA"), ("bB", rng.uniform(940, 1080), 29, 15.5, "fB"),
                 ("bC", rng.uniform(560, 680), 43, 24.0, "fC")]
        for cls, x, cyc, first, gid in bolts:
            sc.css.append(kf(cls, cyc, flicker(cyc / 2) + ([] if cyc < 25 else flicker(cyc / 2 + 0.9, 0.7)))
                          + anim(f".{cls}", cls, cyc, first - cyc / 2))
            sc.sky.append(f'<rect class="{cls}" width="{WIDTH}" height="{HEIGHT}" fill="url(#{gid})" opacity="0"/>')
            bolts_svg.append(f'<g class="{cls}" opacity="0">'
                             + bolt(int(x * 7), x, rng.uniform(105, 135), x + rng.uniform(-30, 30), 318, "#f6f9ff",
                                    "#a8c8ff" if dark else "#2f3b4c") + "</g>")
        sc.css.append(kf("hz", 11, flicker(5.5, 0.35)) + anim(".hz", "hz", 11, 2.5 - 5.5)
                      + kf("hz2", 17, flicker(8.5, 0.45)) + anim(".hz2", "hz2", 17, 6.2 - 8.5))
        sc.sky.append('<ellipse class="hz" cx="760" cy="300" rx="380" ry="95" fill="url(#hz)" opacity="0"/>'
                      '<ellipse class="hz2" cx="330" cy="305" rx="320" ry="85" fill="url(#hz)" opacity="0"/>')

    def field(n, ys, ss, ops, period_seed):
        frng = random.Random(f"field/{state}/{variant}/{period_seed}")
        items, slot = [], WIDTH / max(n, 1)
        for i in range(n):
            name = frng.choice(["mid", "small", "flat"] if ys[0] < 140 else ["small", "flat"])
            items.append((name, i * slot + frng.uniform(0, slot * 0.6), frng.uniform(*ys),
                          frng.uniform(*ss), frng.uniform(*ops), frng.random() < 0.5))
        return items
    n_far = round(1 + 4 * P["cover"])
    n_near = round(1 + 5 * P["cover"])
    sc.css.append(drift_css("dfar", 520, rng.random()) + drift_css("dnear", 300, rng.random()))
    far = tiled(field(n_far, (150, 200), (.5, .72), (.35, .55), "far"), sizes)
    near = tiled(field(n_near, (18, 120), (.8, 1.15), (.72, .95), "near"), sizes)
    sc.sky.append(f'<g class="dfar">{far}</g>')
    if P["deck"]:
        drng = random.Random(f"deck/{state}/{variant}")
        deck = [("storm", i * 300 + drng.uniform(-40, 40), drng.uniform(-95, -60), drng.uniform(1.25, 1.5),
                 P["deck"], drng.random() < 0.5) for i in range(4)]
        sc.css.append(drift_css("ddeck", 420, rng.random()))
        sc.sky.append(f'<g class="ddeck">{tiled(deck, sizes)}</g>')
    sc.sky.append(f'<g class="dnear">{near}</g>')
    sc.sky += bolts_svg

    if P["rain"]:
        sw, sh = sizes["storm"]
        rain_pattern(sc, "rz1", 501, 120, 170, 14, 8, 14, 1.0, rain_col, 0.75)
        rain_pattern(sc, "rz2", 502, 110, 190, 18, 10, 18, 0.9, rain_col, 0.6)
        rain_pattern(sc, "rz3", 503, 100, 230, 30, 16, 30, 1.1, rain_col, 0.7)
        sc.css.append(fall_css("rf1", 170, .9) + fall_css("rf2", 190, .62) + fall_css("rf3", 230, .45))
        veil = "#2a3446" if dark else "#6f7c8e"
        sc.defs.append('<radialGradient id="rfade" cx=".5" cy=".06" r=".62">'
                       '<stop offset="0" stop-color="#fff"/><stop offset=".55" stop-color="#fff" stop-opacity=".8"/>'
                       '<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
                       f'<linearGradient id="veil" x1="0" y1="0" x2="0" y2="1">'
                       f'<stop offset="0" stop-color="{veil}" stop-opacity="0"/>'
                       f'<stop offset=".25" stop-color="{veil}" stop-opacity=".55"/>'
                       f'<stop offset="1" stop-color="{veil}" stop-opacity="0"/></linearGradient>'
                       f'<radialGradient id="cglow"><stop offset="0" stop-color="{flash_c}" stop-opacity=".95"/>'
                       f'<stop offset=".5" stop-color="{flash_c}" stop-opacity=".35"/>'
                       f'<stop offset="1" stop-color="{flash_c}" stop-opacity="0"/></radialGradient>')
        ramps = {1: (0.4, 2.6), 2: (3.0, 3.5), 3: (6.5, 4.0)}
        for lvl, (start, secs) in ramps.items():
            if lvl <= P["rain"]:
                sc.css.append(f"@keyframes in{lvl}{{from{{opacity:0}}to{{opacity:1}}}}" + once(f".in{lvl}", f"in{lvl}", secs, start))
        veil_peak = {1: .25, 2: .55, 3: .9}[P["rain"]]
        sc.css.append(f"@keyframes inv{{from{{opacity:0}}to{{opacity:{veil_peak}}}}}" + once(".inv", "inv", 8, 0.5))
        heroes = []
        hrng = random.Random(f"heroes/{state}/{variant}")
        for i in range(2):
            s = hrng.uniform(0.95, 1.15)
            heroes.append((i * 600 + hrng.uniform(40, 260), hrng.uniform(-20, 0), s, hrng.random() < 0.5))
        for i, (hx, hy, s, mir) in enumerate(heroes):
            cw, ch = sw * s, sh * s
            base_y = ch * 0.8
            rx0, rw = cw * 0.2, cw * 0.6
            rh = 330 - (hy + base_y) + 40
            layers = ""
            for lvl, pid, cls, th in ((1, "rz1", "rf1", 170), (2, "rz2", "rf2", 190), (3, "rz3", "rf3", 230)):
                if lvl <= P["rain"]:
                    layers += (f'<g class="in{lvl}" opacity="0"><rect class="{cls}" x="{rx0 - 60:.0f}" y="{-th}" '
                               f'width="{rw + 120:.0f}" height="{rh + th + 40:.0f}" fill="url(#{pid})"/></g>')
            sc.defs.append(f'<mask id="hm{i}" maskUnits="userSpaceOnUse" x="{rx0 - 80:.0f}" y="-20" '
                           f'width="{rw + 160:.0f}" height="{rh + 60:.0f}"><rect x="{rx0 - 30:.0f}" y="0" '
                           f'width="{rw + 60:.0f}" height="{rh:.0f}" fill="url(#rfade)"/></mask>')
            glow = front = ""
            if state == "storm":
                cyc, first = (13, 4.5) if i == 0 else (23, 12.0)
                sc.css.append(kf(f"cg{i}", cyc, flicker(cyc / 2)) + anim(f".cg{i}", f"cg{i}", cyc, first - cyc / 2))
                glow = (f'<ellipse class="cg{i}" cx="{cw * .5:.0f}" cy="{ch * .5:.0f}" rx="{cw * .5:.0f}" '
                        f'ry="{ch * .42:.0f}" fill="url(#cglow)" opacity="0"/>')
                front = (f'<ellipse class="cg{i}" cx="{cw * .48:.0f}" cy="{ch * .62:.0f}" rx="{cw * .3:.0f}" '
                         f'ry="{ch * .2:.0f}" fill="url(#cglow)" opacity="0"/>')
            hero = (f'{glow}<g transform="translate(0 {base_y - 6:.0f})"><g mask="url(#hm{i})">'
                    f'<g class="inv" opacity="0"><rect x="{rx0:.0f}" width="{rw:.0f}" height="{rh:.0f}" fill="url(#veil)"/></g>'
                    f'<g transform="rotate(7 {cw / 2:.0f} 0)">{layers}</g></g></g>'
                    f'{_use("storm", sizes["storm"], 0, 0, s, mir)}{front}')
            copies = "".join(f'<g transform="translate({hx + k * WIDTH:.1f} {hy:.1f})">{hero}</g>'
                             for k in (-1, 0, 1, 2) if hx + k * WIDTH + cw > 0 and hx + k * WIDTH < 2 * WIDTH)
            sc.sky.append(f'<g class="dhero">{copies}</g>')
        sc.css.append(drift_css("dhero", 480, rng.random()))

    if state == "storm":
        sc.sky.append(f'<rect class="bA" width="{WIDTH}" height="{HEIGHT}" fill="{flash_c}" fill-opacity=".12" opacity="0"/>')

    if P["rain"]:
        def sheet(cls, pid, th, secs, slant):
            sc.css.append(fall_css(cls, th, secs))
            return (f'<g transform="rotate({slant} 600 240)"><rect class="{cls}" x="-500" y="{-500 - th}" '
                    f'width="2200" height="{1400 + th}" fill="url(#{pid})"/></g>')
        sheets = []
        if P["rain"] <= 2:
            rain_pattern(sc, "dfn", 404, 140, 160, 16, 6, 11, 0.8, rain_col, 0.5)
            sheets.append(("insf", sheet("pf", "dfn", 160, 0.8, 6), 0.8, 1.0))
        if P["rain"] >= 2:
            rain_pattern(sc, "dra", 401, 150, 200, 34, 10, 18, 0.8, rain_col, 0.45)
            sheets.append(("insa", sheet("pa", "dra", 200, 0.5, 12), 0.45 if P["rain"] == 2 else 1.0, 4.0))
        if P["rain"] == 3:
            rain_pattern(sc, "drb", 402, 210, 300, 22, 18, 32, 1.1, rain_col, 0.65)
            sheets.append(("insb", sheet("pb", "drb", 300, 0.34, 12), 1.0, 7.0))
        for cls, svg, peak, start in sheets:
            sc.css.append(f"@keyframes {cls}{{from{{opacity:0}}to{{opacity:{peak}}}}}" + once(f".{cls}", cls, 4, start))
            sc.front.append(f'<g class="{cls}" opacity="0">{svg}</g>')
    if P["rain"]:
        dim = {1: .05, 2: .12, 3: .22}[P["rain"]]
        sc.css.append(f"@keyframes indim{{from{{opacity:0}}to{{opacity:{dim}}}}}" + once(".indim", "indim", 7, 0.5))
        sc.front.append(f'<rect class="indim" width="{WIDTH}" height="{HEIGHT}" fill="{"#03060b" if dark else "#7a8696"}" opacity="0"/>')

    notch(sc, state, day, mode)
    return sc.render(day["uptime"])
