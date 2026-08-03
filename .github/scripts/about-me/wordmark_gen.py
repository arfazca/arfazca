#!/usr/bin/env python3
"""
Dev-time tool: bakes a fixed string into an SVG path.

GitHub renders README SVGs through camo as <img>, where no web font ever
loads and @font-face with a data: URI is unreliable - so the only way to show
a typeface that is not already on the viewer's machine is to ship the
outlines. Both strings baked here are fixed, so this runs once and its output
is committed; build_svg.py then needs neither fontTools nor the .ttf.

This only works for fixed text. Anything generate.py substitutes at CI time
(commit counts, uptime) has to stay live <text> in a system font stack,
because there is no glyph to bake ahead of time.

Usage:
    pip install fonttools

    # the blackletter wordmark
    curl -sSL -o UnifrakturMaguntia-Book.ttf \
      https://raw.githubusercontent.com/google/fonts/main/ofl/unifrakturmaguntia/UnifrakturMaguntia-Book.ttf
    python3 wordmark_gen.py UnifrakturMaguntia-Book.ttf "arfaz hussain" \
      --prefix WORDMARK > wordmark_path.py

    # the email, in Fira Code
    curl -sSL -o 'FiraCode[wght].ttf' \
      'https://raw.githubusercontent.com/google/fonts/main/ofl/firacode/FiraCode%5Bwght%5D.ttf'
    python3 wordmark_gen.py 'FiraCode[wght].ttf' "root@arfaz.ca" \
      --prefix EMAIL --wght 500 --tracking 0.035 > email_path.py

Fonts: UnifrakturMaguntia by j. 'mach' wust; Fira Code by Nikita Prokopov and
contributors. Both SIL Open Font License 1.1.
"""
import argparse

from fontTools.misc.transform import Transform
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

# Cap height the output is normalised to, in SVG user units. Callers scale
# from here, so a round number keeps the baked path readable.
TARGET_CAP = 100.0


def kerning_pairs(font):
    """Flat (left, right) -> value map from GPOS pair positioning, if present."""
    pairs = {}
    if "GPOS" not in font:
        return pairs
    try:
        gpos = font["GPOS"].table
        for lookup in gpos.LookupList.Lookup:
            if lookup.LookupType != 2:  # pair adjustment
                continue
            for sub in lookup.SubTable:
                if sub.Format != 1:
                    continue
                for first, pairset in zip(sub.Coverage.glyphs, sub.PairSet):
                    for rec in pairset.PairValueRecord:
                        val = getattr(rec.Value1, "XAdvance", 0) or 0
                        if val:
                            pairs[(first, rec.SecondGlyph)] = val
    except AttributeError:
        pass
    return pairs


def load(font_path, wght):
    """Open the font, pinning a variable-font instance when asked.

    Fira Code ships variable with a wght default of 300, which is too light to
    hold up at small size over grain, so the email is pinned heavier.
    """
    font = TTFont(font_path)
    if wght is not None and "fvar" in font:
        from fontTools.varLib import instancer

        font = instancer.instantiateVariableFont(font, {"wght": wght})
    return font


def build(font_path, text, tracking_em, wght):
    font = load(font_path, wght)
    upem = font["head"].unitsPerEm
    cmap = font.getBestCmap()
    glyphset = font.getGlyphSet()
    hmtx = font["hmtx"]
    kern = kerning_pairs(font)

    cap = getattr(font.get("OS/2"), "sCapHeight", 0) or int(upem * 0.7)
    scale = TARGET_CAP / cap

    names = []
    for ch in text:
        if ch == " ":
            names.append(None)
            continue
        if ord(ch) not in cmap:
            raise SystemExit(f"glyph missing for {ch!r}")
        names.append(cmap[ord(ch)])

    tracking = tracking_em * upem
    space_adv = hmtx["space"][0] if "space" in hmtx.metrics else upem * 0.25

    parts = []
    pen_x = 0.0
    prev = None
    for name in names:
        if name is None:
            pen_x += space_adv + tracking
            prev = None
            continue
        if prev is not None:
            pen_x += kern.get((prev, name), 0)
        # Font units are Y-up, SVG is Y-down, so the transform flips Y as well
        # as scaling - the baked path then drops in with no wrapper transform.
        t = Transform(scale, 0, 0, -scale, pen_x * scale, 0)
        # 2dp is well below a pixel at display size and cuts the committed
        # path to about a third of its raw length.
        spen = SVGPathPen(glyphset, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
        glyphset[name].draw(TransformPen(spen, t))
        d = spen.getCommands()
        if d:
            parts.append(d)
        pen_x += hmtx[name][0] + tracking
        prev = name

    # Trailing tracking is not part of the mark's width.
    width = (pen_x - tracking) * scale
    return " ".join(parts), width


def emit_multi(args):
    """Bake several words into one dict, for the link row.

    All words share a cap height, so their widths differ; build_svg.py centres
    each in an identical canvas to keep the table cells equal.
    """
    rows = []
    for text in args.multi:
        d, width = build(args.font, text, args.tracking, args.wght)
        rows.append((text, d, width))

    out = [
        '"""Generated by wordmark_gen.py --multi - do not edit by hand.',
        "",
        f"Font : {args.font}" + (f" (wght {args.wght:g})" if args.wght else ""),
        "",
        "Baseline at y=0, cap height normalised to"
        f" {TARGET_CAP:g}, Y pointing down.",
        '"""',
        f"{args.prefix}_CAP = {TARGET_CAP:.2f}",
        f"{args.prefix} = {{",
    ]
    for text, d, width in rows:
        out.append(f"    {text!r}: {{")
        out.append(f'        "width": {width:.2f},')
        out.append('        "path": (')
        for i in range(0, len(d), 100):
            out.append(f"            {d[i:i + 100]!r}")
        out.append("        ),")
        out.append("    },")
    out.append("}")
    print("\n".join(out))


def main():
    ap = argparse.ArgumentParser(description="Bake a fixed string to an SVG path.")
    ap.add_argument("font")
    ap.add_argument("text", nargs="?")
    ap.add_argument("--multi", nargs="+", help="bake several words into one dict")
    ap.add_argument("--prefix", default="WORDMARK", help="constant-name prefix")
    ap.add_argument("--tracking", type=float, default=0.02, help="extra tracking, in em")
    ap.add_argument("--wght", type=float, default=None, help="pin a variable-font weight")
    args = ap.parse_args()

    if args.multi:
        emit_multi(args)
        return
    if not args.text:
        ap.error("provide TEXT, or --multi WORD [WORD ...]")

    d, width = build(args.font, args.text, args.tracking, args.wght)
    p = args.prefix

    out = [
        '"""Generated by wordmark_gen.py - do not edit by hand.',
        "",
        f"Text : {args.text!r}",
        f"Font : {args.font}" + (f" (wght {args.wght:g})" if args.wght else ""),
        "",
        "Coordinates are in SVG user units with the baseline at y=0 and the cap",
        f"height normalised to {TARGET_CAP:g}. Y already points down.",
        '"""',
        f"{p}_TEXT = {args.text!r}",
        f"{p}_WIDTH = {width:.2f}",
        f"{p}_CAP = {TARGET_CAP:.2f}",
        f"{p}_PATH = (",
    ]
    for i in range(0, len(d), 100):  # wrapped to keep the committed file diff-friendly
        out.append(f"    {d[i:i + 100]!r}")
    out.append(")")
    print("\n".join(out))


if __name__ == "__main__":
    main()
