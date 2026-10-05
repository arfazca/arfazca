#!/usr/bin/env python3
import argparse
import datetime
import json
import os
import shutil
import sys
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import banner
import keys
import today as today_page
import weather

TZ = ZoneInfo("America/Vancouver")
BIRTHDAY = datetime.date(2002, 6, 15)
AHEAD = 2
SLOT = 10
LEAD = 2
MODES = ("dark", "light")
LIVE = "https://arfazca-banner.arfazhussain.workers.dev"


def _add_months(d, months):
    y, m = divmod(d.month - 1 + months, 12)
    return d.replace(year=d.year + y, month=m + 1)


def uptime(d, born=BIRTHDAY):
    months = (d.year - born.year) * 12 + d.month - born.month
    if _add_months(born, months) > d:
        months -= 1
    days = (d - _add_months(born, months)).days
    years, months = divmod(months, 12)

    def plural(n):
        return "s" if n != 1 else ""
    return f"{years} year{plural(years)}, {months} month{plural(months)}, {days} day{plural(days)}"


def day_info(d):
    return {"dow": d.strftime("%A").lower(), "md": f'{d.strftime("%B").lower()} {d.day}',
            "year": str(d.year), "uptime": uptime(d)}


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = text.encode()
    if os.path.exists(path) and open(path, "rb").read() == data:
        return False
    with open(path, "wb") as f:
        f.write(data)
    return True


def frame_name(seg, mode):
    return f'{seg["state"]}-{seg["variant"]}-{mode}.svg'


def render_day(gen, d, force=False):
    plan_path = os.path.join(gen, "schedule", f"{d.isoformat()}.json")
    fdir = os.path.join(gen, "frames", d.isoformat())
    segs = weather.plan(d)
    needed = {(s["state"], s["variant"]) for s in segs}
    have = all(os.path.exists(os.path.join(fdir, f"{st}-{v}-{m}.svg")) for st, v in needed for m in MODES)
    have = have and all(os.path.exists(os.path.join(fdir, f"bar-{m}.svg")) for m in MODES)
    if have and os.path.exists(plan_path) and not force:
        return False
    info = day_info(d)
    for st, v in sorted(needed):
        for m in MODES:
            _write(os.path.join(fdir, f"{st}-{v}-{m}.svg"), banner.render(m, st, v, info))
    for m in MODES:
        _write(os.path.join(fdir, f"bar-{m}.svg"), today_page.bar(segs, m, 0))
    for name in os.listdir(fdir):
        if name.endswith(".svg") and not name.startswith("bar-") and tuple(name.rsplit("-", 2)[:1] + [int(name.rsplit("-", 2)[1])]) not in needed:
            os.remove(os.path.join(fdir, name))
    _write(plan_path, json.dumps({"date": d.isoformat(), "tz": "America/Vancouver", "day": info,
                                  "segments": segs}, indent=1) + "\n")
    return True


def prune(gen, keep):
    for sub in ("frames", "schedule"):
        root = os.path.join(gen, sub)
        if not os.path.isdir(root):
            continue
        for name in os.listdir(root):
            if name.split(".")[0] not in keep:
                p = os.path.join(root, name)
                shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)


def write_keys(gen):
    want = {f"{s}-{m}.svg": svg for (s, m), svg in keys.all_keys().items()}
    root = os.path.join(gen, "links")
    os.makedirs(root, exist_ok=True)
    for name in os.listdir(root):
        if name not in want:
            os.remove(os.path.join(root, name))
    for name, svg in want.items():
        _write(os.path.join(root, name), svg)


def swap(gen, now):
    seg = weather.at(now.date(), now.hour * 60 + now.minute)
    for m in MODES:
        src = os.path.join(gen, "frames", now.date().isoformat(), frame_name(seg, m))
        _write(os.path.join(gen, f"about-{m}.svg"), open(src, encoding="utf-8").read())
    return seg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen", required=True, help="checkout of the generated branch")
    ap.add_argument("--force", action="store_true", help="re-render every day kept")
    ap.add_argument("--now", help="ISO time to act as, for testing (Vancouver time)")
    ap.add_argument("--message", help="write a commit message here")
    ap.add_argument("--docs", help="main's docs/ folder, for today.md")
    a = ap.parse_args()

    now = datetime.datetime.fromisoformat(a.now).replace(tzinfo=TZ) if a.now else datetime.datetime.now(TZ)
    today = now.date()
    days = [today + datetime.timedelta(days=i) for i in range(AHEAD + 1)]
    notes = []
    for d in days:
        if render_day(a.gen, d, a.force):
            notes.append(f"frames for {d}")
    prune(a.gen, {d.isoformat() for d in days})
    write_keys(a.gen)
    seg = swap(a.gen, now)
    segs = weather.plan(today)
    for m in MODES:
        _write(os.path.join(a.gen, f"today-{m}.svg"), today_page.bar(segs, m, now.hour * 60 + now.minute))
    if a.docs:
        at = now + datetime.timedelta(minutes=LEAD)
        start = at.hour * 60 + at.minute - at.minute % SLOT
        tz = f"Pacific ({at.tzname()})"
        page = today_page.markdown(at.date(), weather.plan(at.date()), tz, LIVE, (start, start + SLOT))
        if _write(os.path.join(a.docs, "today.md"), page):
            notes.append("docs/today.md")
    msg = f'banner: {seg["state"]} (variant {seg["variant"]}) at {now:%H:%M}'
    if notes:
        msg += " · " + ", ".join(notes)
    print(msg)
    if a.message:
        with open(a.message, "w") as f:
            f.write(msg + "\n")


if __name__ == "__main__":
    main()
