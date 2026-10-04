#!/usr/bin/env python3
import datetime
import random
import sys

EPOCH = datetime.date(2026, 1, 1)
FIRST = "clear"
VARIANTS = 3

NEXT = {
    "clear":   [("cloudy", 0.5), ("clear", 0.5)],
    "cloudy":  [("drizzle", 0.4), ("clear", 0.4), ("cloudy", 0.2)],
    "drizzle": [("rain", 0.45), ("cloudy", 0.45), ("drizzle", 0.1)],
    "rain":    [("storm", 0.3), ("drizzle", 0.6), ("rain", 0.1)],
    "storm":   [("rain", 0.9), ("storm", 0.1)],
}
HOLD = {"clear": (15, 30), "cloudy": (10, 25), "drizzle": (10, 20), "rain": (10, 25), "storm": (10, 18)}

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
        dur = rng.randint(lo, hi)
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
