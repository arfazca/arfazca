#!/usr/bin/env python3
import datetime
import random
import sys

EPOCH = datetime.date(2026, 1, 1)
FIRST = "clear"
VARIANTS = 3

# Every hold ends in a different state, so the sky changes every 10-20 minutes.
# Weighted toward rain and storms: roughly 15-20 storms a day.
NEXT = {
    "clear":   [("cloudy", 1.0)],
    "cloudy":  [("drizzle", 0.6), ("clear", 0.4)],
    "drizzle": [("rain", 0.6), ("cloudy", 0.4)],
    "rain":    [("storm", 0.55), ("drizzle", 0.45)],
    "storm":   [("rain", 1.0)],
}
HOLD = {"clear": (10, 20), "cloudy": (10, 20), "drizzle": (10, 20), "rain": (10, 20), "storm": (10, 20)}

DAY = 24 * 60


def _pick(rng, options):
    r, acc = rng.random(), 0.0
    for state, w in options:
        acc += w
        if r < acc:
            return state
    return options[-1][0]


def _day(state, d):
    rng = random.Random(f"weather/{d.isoformat()}")
    segs, t = [], 0
    while t < DAY:
        lo, hi = HOLD[state]
        dur, left = rng.randint(lo, hi), DAY - t
        if 0 < left - dur < lo:  # never leave a sliver before midnight
            dur = left if left <= hi else left - lo
        segs.append({"start": t, "end": min(t + dur, DAY), "state": state, "variant": rng.randrange(VARIANTS)})
        t += dur
        state = _pick(rng, NEXT[state])
    return segs, state


def plan(d):
    state, day = FIRST, EPOCH
    while day < d:
        _, state = _day(state, day)
        day += datetime.timedelta(days=1)
    return _day(state, d)[0]


def at(d, minute):
    for seg in plan(d):
        if seg["start"] <= minute < seg["end"]:
            return seg
    return plan(d)[-1]


if __name__ == "__main__":
    d = datetime.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else datetime.date.today()
    for s in plan(d):
        print(f'{s["start"] // 60:02d}:{s["start"] % 60:02d}-{s["end"] // 60:02d}:{s["end"] % 60:02d}  '
              f'{s["state"]:8s} v{s["variant"]}')
