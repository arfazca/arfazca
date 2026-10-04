#!/usr/bin/env python3
import datetime

W, H = 1200, 142
TRACK_Y, TRACK_H = 32, 44
DAY = 24 * 60

COLORS = {
    "dark": {"clear": "#8fb4e3", "cloudy": "#6c7889", "drizzle": "#6d9bd6", "rain": "#4b74b3",
             "storm": "#e2b44f", "text": "#8798ae", "strong": "#e5eaf0", "now": "#f0f6fc"},
    "light": {"clear": "#7fa3cf", "cloudy": "#98a3b3", "drizzle": "#5e8cc4", "rain": "#34588c",
              "storm": "#c08a1e", "text": "#56667a", "strong": "#1f2328", "now": "#1f2328"},
}
ORDER = ["clear", "cloudy", "drizzle", "rain", "storm"]
WET = {"drizzle", "rain", "storm"}
MONO = "ui-monospace,'SF Mono','SFMono-Regular','JetBrains Mono',Menlo,Consolas,monospace"


def hhmm(m):
    return f"{m // 60:02d}:{m % 60:02d}"


def merged(segments):
    out = []
    for s in segments:
        if out and out[-1]["state"] == s["state"]:
            out[-1] = dict(out[-1], end=s["end"])
        else:
            out.append(dict(s))
    return out


def bar(segments, mode, now_minute=None):
    c = COLORS[mode]
    segments = merged(segments)
    x = lambda m: m / DAY * W
    rects = "".join(
        f'<rect x="{x(s["start"]):.2f}" y="{TRACK_Y}" width="{max(x(s["end"]) - x(s["start"]) - 1.5, 0.5):.2f}" '
        f'height="{TRACK_H}" fill="{c[s["state"]]}"/>' for s in segments)
    ticks = "".join(
        f'<text x="{min(max(x(h * 60), 27), W - 27):.0f}" y="{TRACK_Y + TRACK_H + 24}" text-anchor="middle">'
        f'{h:02d}:00</text>' for h in range(0, 25, 3))
    share = {k: 0 for k in ORDER}
    for s in segments:
        share[s["state"]] += s["end"] - s["start"]
    lx, legend = 0, []
    for k in ORDER:
        label = f'{k} {round(share[k] / DAY * 100)}%'
        legend.append(f'<rect x="{lx}" y="{H - 15}" width="12" height="12" rx="2" fill="{c[k]}"/>'
                      f'<text x="{lx + 18}" y="{H - 4}">{label}</text>')
        lx += 18 + len(label) * 9.6 + 26
    now = ""
    if now_minute is not None:
        nx = x(now_minute)
        now = (f'<g id="now"><rect x="{nx - 1.5:.1f}" y="{TRACK_Y - 10}" width="3" height="{TRACK_H + 20}" rx="1.5" fill="{c["now"]}"/>'
               f'<text x="{min(max(nx, 20), W - 20):.0f}" y="{TRACK_Y - 15}" text-anchor="middle" fill="{c["strong"]}" '
               f'font-family="{MONO}" font-size="15">now</text></g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="The day\'s weather, hour by hour">'
            f'<defs><clipPath id="t"><rect y="{TRACK_Y}" width="{W}" height="{TRACK_H}" rx="9"/></clipPath></defs>'
            f'<g clip-path="url(#t)">{rects}</g>'
            f'<g font-family="{MONO}" font-size="16" fill="{c["text"]}">{ticks}{"".join(legend)}</g>'
            f'{now}</svg>\n')


CHANGE = {
    ("clear", "cloudy"): "Clouds roll in and the stars go",
    ("cloudy", "clear"): "Clears up; stars and moon are back",
    ("cloudy", "drizzle"): "Rain clouds drift over and it starts to drizzle",
    ("drizzle", "cloudy"): "The drizzle stops but it stays overcast",
    ("drizzle", "rain"): "Picks up into steady rain",
    ("rain", "drizzle"): "Eases back to a drizzle",
    ("rain", "storm"): "Turns into a storm: downpour and lightning",
    ("storm", "rain"): "The storm moves on, still raining",
}
OPENING = {
    "clear": "Starts clear, with stars and a thin moon",
    "cloudy": "Starts overcast",
    "drizzle": "Starts with a drizzle",
    "rain": "Starts in steady rain",
    "storm": "Starts in the middle of a storm",
}
NAME = {"clear": "clear", "cloudy": "overcast", "drizzle": "drizzle", "rain": "rain", "storm": "storm"}
PARTS = [("Night", 0, 360), ("Morning", 360, 720), ("Afternoon", 720, 1080), ("Evening", 1080, DAY)]


def _dur(m):
    h, mm = divmod(m, 60)
    return f"{h} h {mm} min" if h and mm else (f"{h} h" if h else f"{mm} min")


def summary(segs):
    wet = sum(s["end"] - s["start"] for s in segs if s["state"] in WET)
    spells, run = [], None
    for s in segs:
        if s["state"] in WET:
            run = [run[0], s["end"]] if run else [s["start"], s["end"]]
        elif run:
            spells.append(run)
            run = None
    if run:
        spells.append(run)
    storms = sum(1 for i, s in enumerate(segs) if s["state"] == "storm" and (i == 0 or segs[i - 1]["state"] != "storm"))
    if not spells:
        return f"A dry day: {_dur(DAY - wet)} without a drop."
    longest = max(spells, key=lambda r: r[1] - r[0])
    line = (f"Dry for {_dur(DAY - wet)}, wet for {_dur(wet)}. Rain comes through "
            f"{len(spells)} time{'s' if len(spells) != 1 else ''}, the longest spell from "
            f"{hhmm(longest[0])} to {'midnight' if longest[1] == DAY else hhmm(longest[1])}")
    line += "." if not storms else f", and it turns stormy {storms} time{'s' if storms != 1 else ''}."
    return line


def markdown(d, segments, tzname, base):
    segs = merged(segments)
    title = f'{d.strftime("%A")}, {d.strftime("%B")} {d.day} {d.year}'
    rows = {name: [] for name, _, _ in PARTS}
    for i, s in enumerate(segs):
        what = OPENING[s["state"]] if i == 0 else CHANGE.get((segs[i - 1]["state"], s["state"]), NAME[s["state"]].capitalize())
        part = next(name for name, a, b in PARTS if a <= s["start"] < b)
        rows[part].append(f'| **{hhmm(s["start"])}** | {NAME[s["state"]]} | {what} | {_dur(s["end"] - s["start"])} |')
    out = [
        f"# {title}",
        "",
        f"The sky over the banner today, hour by hour. Times are {tzname}.",
        "",
        "<picture>",
        f'  <source media="(prefers-color-scheme: dark)" srcset="{base}/today-dark.svg" />',
        f'  <img width="100%" alt="Today\'s weather, hour by hour" src="{base}/today-light.svg" />',
        "</picture>",
        "",
        summary(segs),
        "",
    ]
    for name, a, b in PARTS:
        if not rows[name]:
            continue
        out += [f"## {name} · {hhmm(a)}–{hhmm(b) if b < DAY else '24:00'}", "",
                "| time | sky | what happens | for |", "|:--|:--|:--|--:|", *rows[name], ""]
    return "\n".join(out)


if __name__ == "__main__":
    import weather
    today = datetime.date.today()
    print(markdown(today, weather.plan(today), "Pacific", "https://example"))
