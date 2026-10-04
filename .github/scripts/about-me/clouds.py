#!/usr/bin/env python3
import os
import random
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SPR = os.path.join(HERE, "sprites")
SCALE = 0.66
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

CLOUDS = {
    "mid":   (340, 160, 23, 18, 0.80, 0.30),
    "small": (220, 110, 37, 11, 0.78, 0.15),
    "flat":  (420, 120, 41, 20, 0.76, 0.00),
    "storm": (520, 220, 59, 34, 0.82, 0.48),
}
DARKEN = {"storm": (0.66, 0.40)}

PALETTE = {
    "dark":  {"shadow": (0.06, 0.075, 0.105), "lit": (0.45, 0.50, 0.59), "base": 0.55},
    "light": {"shadow": (0.52, 0.56, 0.62), "lit": (1.0, 0.985, 0.965), "base": 0.80},
}


def silhouette(name):
    w, h, seed, n, bf, tower = CLOUDS[name]
    rng = random.Random(seed)
    base_y = h * bf
    out = []
    out.append(f'<ellipse cx="{w / 2:.1f}" cy="{base_y - h * 0.12:.1f}" rx="{w * 0.36:.1f}" ry="{h * 0.14:.1f}"/>')
    for _ in range(n):
        t = rng.uniform(-1, 1)
        x = w / 2 + t * w * 0.33
        bell = 1 - abs(t) ** 1.4
        r = h * (0.07 + 0.11 * bell + tower * 0.12 * bell * rng.random()) * rng.uniform(0.75, 1.2)
        y = base_y - r * rng.uniform(0.55, 0.95) - h * tower * 0.35 * bell * rng.random()
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}"/>')
    return w, h, base_y, "".join(out)


def svg_for(name, mode):
    w, h, base_y, shapes = silhouette(name)
    seed = CLOUDS[name][2]
    p = dict(PALETTE[mode])
    if name in DARKEN:
        k, b = DARKEN[name]
        p["shadow"] = tuple(c * k for c in p["shadow"])
        p["lit"] = tuple(c * k for c in p["lit"])
        p["base"] = b
    (sr, sg, sb), (lr, lg, lb) = p["shadow"], p["lit"]
    ct = "".join(
        f'<feFunc{c} type="linear" slope="{l - s:.3f}" intercept="{s:.3f}"/>'
        for c, s, l in (("R", sr, lr), ("G", sg, lg), ("B", sb, lb)))
    pad = 30
    W, H = w + 2 * pad, h + 2 * pad
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="{-pad} {-pad} {W} {H}">
<defs>
<clipPath id="base"><rect x="-200" y="-200" width="{w + 400}" height="{base_y + 200:.1f}"/></clipPath>
<filter id="f" x="{-pad}" y="{-pad}" width="{W}" height="{H}" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB">
  <feTurbulence type="fractalNoise" baseFrequency="0.011" numOctaves="5" seed="{seed}" result="noise"/>
  <feGaussianBlur in="SourceGraphic" stdDeviation="9" result="soft"/>
  <feDisplacementMap in="soft" in2="noise" scale="62" xChannelSelector="R" yChannelSelector="G" result="shape"/>
  <feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="4" seed="{seed + 7}" result="fine"/>
  <feColorMatrix in="fine" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1.5 0 0 0 -0.1" result="fa"/>
  <feComposite in="shape" in2="fa" operator="arithmetic" k1="0.35" k2="0.85" k3="0" k4="0" result="dens"/>
  <feGaussianBlur in="shape" stdDeviation="7" result="h"/>
  <feDiffuseLighting in="h" surfaceScale="2.6" diffuseConstant="1.05" lighting-color="#ffffff" result="lit">
    <feDistantLight azimuth="225" elevation="50"/>
  </feDiffuseLighting>
  <feComponentTransfer in="lit" result="col">{ct}</feComponentTransfer>
  <feComposite in="col" in2="dens" operator="in"/>
</filter>
</defs>
<g filter="url(#f)"><g clip-path="url(#base)" fill="#fff">{shapes}</g></g>
</svg>
'''


def render(name, mode):
    src = os.path.join(SPR, f"{name}-{mode}.svg")
    png = os.path.join(SPR, f"{name}-{mode}.png")
    with open(src, "w") as f:
        f.write(svg_for(name, mode))
    w, h = CLOUDS[name][:2]
    W, H = w + 60, h + 60
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--default-background-color=00000000", f"--window-size={W},{H}",
                    f"--screenshot={png}", "file://" + src],
                   check=True, capture_output=True)
    bf = CLOUDS[name][4]
    k = int(255 * (DARKEN[name][1] if name in DARKEN else PALETTE[mode]["base"]))
    top = 30 + int(h * 0.42)
    ramp = 30 + int(h * bf) + 6 - top
    rest = H - top - ramp
    subprocess.run(["magick", png,
                    "(", "-clone", "0", "-alpha", "extract", ")",
                    "(", "-clone", "0", "-alpha", "off",
                         "(", "-size", f"{W}x{top}", "xc:white",
                              "-size", f"{W}x{ramp}", f"gradient:white-rgb({k},{k},{min(255, k + 4)})",
                              "-size", f"{W}x{max(rest, 1)}", f"xc:rgb({k},{k},{min(255, k + 4)})",
                              "-append", "-crop", f"{W}x{H}+0+0", "+repage", ")",
                         "-compose", "multiply", "-composite", ")",
                    "-delete", "0", "+swap", "-compose", "copy_opacity", "-composite", "-compose", "over",
                    "-trim", "+repage", "-bordercolor", "none", "-border", "4", "-resize", f"{int(SCALE * 100)}%",
                    "-define", "png:compression-level=9", "-strip", png], check=True)
    return png


if __name__ == "__main__":
    os.makedirs(SPR, exist_ok=True)
    for mode in ("dark", "light"):
        for name in CLOUDS:
            p = render(name, mode)
            print(p, os.path.getsize(p) // 1024, "KB")
