#!/usr/bin/env python3
"""SITL ONLY (bench 2c): per-test timelines and intervals for one watcher-bench session directory.

  python3 -m realflight.sitl_bench.analyse ~/thesis_data/wbench/wbench_<session>_<stamp>

Clocks (pre-registered, handover §1.1): W = wall clock (injections, the watcher, the flight script); F = the FC clock
(dataflash TimeUS, SYSTEM_TIME.time_boot_ms; SITL sim time). F -> W: per event, a linear fit over the SYSTEM_TIME
samples within +-10 s of F, on the lower envelope (minimum W - F per 1 s bin), i.e. the least-delayed receipts. Each
dataflash file is one FC boot; it is matched to the SYSTEM_TIME segment of the same boot (boot_ms resets on reboot).
Writes <session>/analysis/<test>.txt (merged timeline) and analysis/summary.json.
"""
import glob
import json
import os
import re
import sys

import numpy as np
from pymavlink import DFReader

ERR = {5: "FAILSAFE_RADIO", 8: "FAILSAFE_GCS", 16: "EKFCHECK", 17: "FAILSAFE_EKFINAV", 10: "FLIGHT_MODE",
       24: "EKF_PRIMARY", 26: "FAILSAFE_SENSORS", 31: "FAILSAFE_DEADRECKON"}
MODES = {0: "STABILIZE", 2: "ALT_HOLD", 4: "GUIDED", 9: "LAND", 3: "AUTO", 5: "LOITER", 6: "RTL"}
RSN = {1: "RC_COMMAND", 2: "GCS_COMMAND", 3: "RADIO_FAILSAFE", 5: "GCS_FAILSAFE", 6: "EKF_FAILSAFE", 26: "INITIALISED",
       31: "STARTUP"}


class ClockMap:
    def __init__(self, w, f):
        self.w, self.f = np.asarray(w), np.asarray(f)

    def _fit(self, f0):
        sel = np.abs(self.f - f0) < 10.0
        if sel.sum() < 5:
            sel = np.argsort(np.abs(self.f - f0))[:50]
        fw, ff = self.w[sel], self.f[sel]
        d = fw - ff
        bins = np.floor(ff)
        keep_f, keep_d = [], []
        for b in np.unique(bins):
            m = bins == b
            i = np.argmin(d[m])
            keep_f.append(ff[m][i]); keep_d.append(d[m][i])
        keep_f, keep_d = np.array(keep_f), np.array(keep_d)
        if len(keep_f) >= 2:
            k, c = np.polyfit(keep_f, keep_d, 1)
        else:
            k, c = 0.0, keep_d[0]
        return k, c

    def f2w(self, f):
        k, c = self._fit(f)
        return f + k * f + c

    def w2f(self, w):
        f = w - np.median(self.w - self.f)
        for _ in range(3):
            k, c = self._fit(f)
            f = (w - c) / (1 + k)
        return f


def boots(sess):
    rows = [tuple(map(float, l.split(","))) for l in open(os.path.join(sess, "op_systime.csv"))]
    segs, cur, last = [], [], None
    for w, b in rows:
        f = b / 1000.0
        if last is not None and f < last - 1.0:
            segs.append(cur); cur = []
        cur.append((w, f)); last = f
    if cur:
        segs.append(cur)
    return [ClockMap([x[0] for x in s], [x[1] for x in s]) for s in segs]


def df_events(path, cm):
    r = DFReader.DFReader_binary(path)
    out = []
    while True:
        m = r.recv_match(type=["MODE", "EV", "ERR", "MSG"])
        if m is None:
            break
        f = m.TimeUS / 1e6
        t = m.get_type()
        if t == "MODE":
            s = f"MODE {MODES.get(int(m.ModeNum), m.ModeNum)} reason {RSN.get(int(m.Rsn), m.Rsn)}"
        elif t == "EV":
            s = {10: "EV ARMED", 11: "EV DISARMED", 18: "EV LAND_COMPLETE", 17: "EV LAND_COMPLETE_MAYBE"}.get(
                int(m.Id), f"EV {m.Id}")
        elif t == "ERR":
            s = f"ERR {ERR.get(int(m.Subsys), m.Subsys)} code {m.ECode}"
        else:
            s = f"MSG {m.Message}"
        out.append((cm.f2w(f), f, "FC", s))
    return out


def text_events(sess):
    ev = []
    for name in ("watcher", "observer"):
        p = os.path.join(sess, name, "STOP_LOG.txt")
        if os.path.exists(p):
            for l in open(p):
                parts = l.split(" ", 2)
                try:
                    ev.append((float(parts[1]), None, name.upper(), parts[2].strip()))
                except (ValueError, IndexError):
                    pass
    for p in sorted(glob.glob(os.path.join(sess, "fs*.log"))):
        fsn = os.path.basename(p)[:-4]
        for l in open(p):
            m = re.match(r"\[flight_script (\d+\.\d+)\] (.*)", l)
            if m:
                ev.append((float(m.group(1)), None, fsn, m.group(2)))
    p = os.path.join(sess, "relay_events.txt")
    if os.path.exists(p):
        for l in open(p):
            parts = l.split(" ", 1)
            ev.append((float(parts[0]), None, "RELAY", parts[1].strip()))
    for l in open(os.path.join(sess, "op_events.csv")):
        w, kind, txt = l.rstrip("\n").split(",", 2)
        if kind in ("TEXT", "HB", "OP", "PARAM", "ACK"):
            ev.append((float(w), None, f"op.{kind}", txt.strip('"')))
    for l in open(os.path.join(sess, "forwarder.csv")):
        if ",CTL," in l:
            w, _, c = l.split(",", 2)
            ev.append((float(w), None, "FWD", c.strip().strip(",")))
    return ev


def last_frames(sess):
    """Per-destination send times (dest 0 only), for 'last frame before a stop'."""
    t = []
    for l in open(os.path.join(sess, "forwarder.csv")):
        p = l.split(",")
        if len(p) > 4 and p[1] == "0":
            t.append((float(p[0]), p[4], p[5]))
    return t


def main(sess):
    cms = boots(sess)
    bins = sorted(glob.glob(os.path.join(sess, "dataflash", "*.BIN")))
    # SITL's soft reboot keeps the simulation clock running (no reset of time_boot_ms was seen), so a boot is matched
    # by order only when the clock did reset; otherwise every file uses the one continuous map
    if len(cms) == len(bins):
        pairs = list(zip(bins, cms))
    else:
        print(f"note: {len(bins)} dataflash files, {len(cms)} SYSTEM_TIME clock segment(s): using the last segment")
        pairs = [(b, cms[-1]) for b in bins]
    fc = []
    for b, cm in pairs:
        fc += df_events(b, cm)
    ev = sorted(fc + text_events(sess), key=lambda x: x[0])
    tests = [json.loads(l) for l in open(os.path.join(sess, "tests.jsonl"))]
    os.makedirs(os.path.join(sess, "analysis"), exist_ok=True)
    allcm = pairs[-1][1] if pairs else None
    summary = {}
    for i, t in enumerate(tests):
        if t["test"].startswith("param_snapshot"):
            continue
        ts = [v for k, v in t.items() if k.startswith("t_") and isinstance(v, (int, float)) and v]
        if not ts:
            ts = [x["t_send_w"] for x in t.get("commands", [])]
        if not ts:
            continue
        a, b = min(ts) - 15, max(ts) + 25
        lines = [f"# {t['test']}  {json.dumps(t)[:2000]}"]
        inj = sorted((v, k) for k, v in t.items() if k.startswith("t_") and isinstance(v, (int, float)) and v)
        for w, f, src, s in ev:
            if a <= w <= b:
                fs = f"F={f:9.3f}" if f is not None else " " * 11
                rel = "  ".join(f"{k[2:-2]}{w - v:+.3f}" for v, k in inj if abs(w - v) < 30)[:120]
                lines.append(f"{w:.3f} {fs} {src:9s} {s[:160]}   [{rel}]")
        open(os.path.join(sess, "analysis", f"{i:02d}_{t['test']}.txt"), "w").write("\n".join(lines) + "\n")
        summary[t["test"]] = {"window": [a, b]}
    json.dump(summary, open(os.path.join(sess, "analysis", "summary.json"), "w"), indent=1)
    # helper for F-clock intervals
    with open(os.path.join(sess, "analysis", "clockmap.txt"), "w") as f:
        for k, cm in enumerate(cms):
            r = cm.w - cm.f
            f.write(f"boot {k}: n={len(cm.w)} F {cm.f.min():.1f}..{cm.f.max():.1f}  "
                    f"W-F spread {np.percentile(r, 1):.3f}..{np.percentile(r, 99):.3f}\n")
    print(f"analysis written to {sess}/analysis")


if __name__ == "__main__":
    main(sys.argv[1])
