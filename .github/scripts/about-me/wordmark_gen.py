#!/usr/bin/env python3
import argparse

from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

TARGET_CAP = 100.0


def kerning_pairs(font):
    pairs = {}
    if "GPOS" not in font:
        return pairs
    try:
        gpos = font["GPOS"].table
        for lookup in gpos.LookupList.Lookup:
            if lookup.LookupType != 2:
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
    bounds = BoundsPen(glyphset)
    for name in names:
        if name is None:
            pen_x += space_adv + tracking
            prev = None
            continue
        if prev is not None:
            pen_x += kern.get((prev, name), 0)
        t = Transform(scale, 0, 0, -scale, pen_x * scale, 0)
        spen = SVGPathPen(glyphset, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
        glyphset[name].draw(TransformPen(spen, t))
        glyphset[name].draw(TransformPen(bounds, t))
        d = spen.getCommands()
        if d:
            parts.append(d)
        pen_x += hmtx[name][0] + tracking
        prev = name

    width = (pen_x - tracking) * scale
    return " ".join(parts), width, bounds.bounds


def emit_multi(args):
    rows = []
    for text in args.multi:
        d, width, bbox = build(args.font, text, args.tracking, args.wght)
        rows.append((text, d, width, bbox))

    f = load(args.font, args.wght)
    upem = f["head"].unitsPerEm
    cmap = f.getBestCmap()
    gs = f.getGlyphSet()
    cap = getattr(f.get("OS/2"), "sCapHeight", 0) or int(upem * 0.7)

    xheight = None
    for ch in "xnzu":
        if ord(ch) not in cmap:
            continue
        bp = BoundsPen(gs)
        gs[cmap[ord(ch)]].draw(bp)
        if bp.bounds:
            xheight = bp.bounds[3] * (TARGET_CAP / cap)
            break
    if xheight is None:
        xheight = TARGET_CAP * 0.72

    out = [
        f"{args.prefix}_CAP = {TARGET_CAP:.2f}",
        f"{args.prefix}_XHEIGHT = {xheight:.2f}",
        f"{args.prefix} = {{",
    ]
    for text, d, width, bbox in rows:
        xn, yn, xx, yx = bbox
        out.append(f"    {text!r}: {{")
        out.append(f'        "width": {width:.2f},')
        out.append(
            f'        "ink": ({xn:.2f}, {yn:.2f}, {xx:.2f}, {yx:.2f}),'
        )
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

    d, width, _ = build(args.font, args.text, args.tracking, args.wght)
    p = args.prefix

    out = [
        f"{p}_TEXT = {args.text!r}",
        f"{p}_WIDTH = {width:.2f}",
        f"{p}_CAP = {TARGET_CAP:.2f}",
        f"{p}_PATH = (",
    ]
    for i in range(0, len(d), 100):
        out.append(f"    {d[i:i + 100]!r}")
    out.append(")")
    print("\n".join(out))


if __name__ == "__main__":
    main()
