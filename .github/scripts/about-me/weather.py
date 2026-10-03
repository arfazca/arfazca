#!/usr/bin/env python3
"""
The day's weather, planned ahead.

The banner can't read the clock, so weather that lasts has to be decided in
advance: a chain of states, each held 10-30 minutes, run forward from a fixed
epoch and seeded by date. Any day's plan can be recomputed exactly, and the
chain carries across midnight (each day starts where the last one ended).

Rain only ever arrives through drizzle and leaves through drizzle, and a
storm only grows out of rain, so nothing starts or stops abruptly.

    python3 weather.py 2026-10-04   # print a day's plan
"""
import datetime
import random
import sys

EPOCH = datetime.date(2026, 1, 1)
FIRST = "clear"
VARIANTS = 3  # frames per state per day; segments cycle through them

# state -> [(next state, weight)]
NEXT = {
    "clear":   [("cloudy", 0.5), ("clear", 0.5)],
    "cloudy":  [("drizzle", 0.4), ("clear", 0.4), ("cloudy", 0.2)],
    "drizzle": [("rain", 0.45), ("cloudy", 0.45), ("drizzle", 0.1)],
    "rain":    [("storm", 0.3), ("drizzle", 0.6), ("rain", 0.1)],
    "storm":   [("rain", 0.9), ("storm", 0.1)],
}
# minutes each state holds
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
    """Plan one day from `state` at midnight; returns (segments, state at end)."""
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
    """Segments for date d: [{'start', 'end' (minutes from midnight), 'state', 'variant'}]."""
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
