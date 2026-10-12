#!/usr/bin/env python3
"""Rung-1 Replay-fidelity gate (pre-registration sec. 5): the onboard EKF3 (XKF1 core 0) against the replayed EKF3
(XKF1 core 100) in ONE Replay output log, over the armed period. PASS if max horizontal position difference <= 0.01 m,
max height difference <= 0.01 m and max yaw difference <= 0.1 deg (the bounds are confirmed or widened ONCE on the
verification logs, sec. 5 [TBD-V]; pass them with --bounds).

WHY THIS TOOL (2026-10-12): sec. 5 named ArduPilot's Tools/Replay/check_replay.py, which reads through pymavlink. On the
thesis fork's Replay output of a stock-flown log (the UKF records are written without FMT) pymavlink exits or reads
~15 XKF1 per core (handover docs/handovers/2026-10-12_r1_scoring_items.md, section C), so the gate is computed here with
eval/df_reader.py. The criterion is unchanged; check_replay.py remains usable on a STOCK Replay's output.

  python3 eval/replay_gate.py <replay_output.BIN> [--core 0] [--bounds 0.01 0.01 0.1] [--json OUT]
"""
import argparse, json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from df_reader import read_records


def gate(recs, core=0, bounds=(0.01, 0.01, 0.1)):
    on = [r for r in recs["XKF1"] if r["C"] == core]; rp = [r for r in recs["XKF1"] if r["C"] == core + 100]
    if not on or not rp:
        raise SystemExit(f"XKF1 core {core} ({len(on)}) or {core + 100} ({len(rp)}) missing: not a Replay output log?")
    ta, tb = np.array([r["TimeUS"] for r in on]), np.array([r["TimeUS"] for r in rp])
    if len(ta) != len(tb) or not np.array_equal(ta, tb):
        raise SystemExit(f"XKF1@{core} ({len(ta)}) and @{core + 100} ({len(tb)}) TimeUS sequences differ: the log counts "
                         "as incomplete for replay (prereg sec. 3.3 item 2)")
    arm = [r["TimeUS"] for r in recs["ARM"] if r["ArmState"] == 1]
    dis = [r["TimeUS"] for r in recs["ARM"] if r["ArmState"] == 0]
    if not arm:
        raise SystemExit("no ARM record: the armed period is undefined")
    t0 = arm[0]; t1 = next((d for d in dis if d > t0), int(ta[-1]))
    w = (ta >= t0) & (ta <= t1)
    f = lambda rs, k: np.array([r[k] for r in rs])[w]
    dh = np.hypot(f(on, "PN") - f(rp, "PN"), f(on, "PE") - f(rp, "PE"))
    dz = np.abs(f(on, "PD") - f(rp, "PD"))
    dy = np.abs((f(on, "Yaw") - f(rp, "Yaw") + 180.0) % 360.0 - 180.0)
    out = {"core": core, "armed_span_us": [int(t0), int(t1)], "n": int(w.sum()),
           "max_horizontal_m": float(dh.max()), "max_height_m": float(dz.max()), "max_yaw_deg": float(dy.max()),
           "bounds": {"horizontal_m": bounds[0], "height_m": bounds[1], "yaw_deg": bounds[2]}}
    out["pass"] = bool(out["max_horizontal_m"] <= bounds[0] and out["max_height_m"] <= bounds[1]
                       and out["max_yaw_deg"] <= bounds[2])
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0]); ap.add_argument("bin")
    ap.add_argument("--core", type=int, default=0); ap.add_argument("--bounds", type=float, nargs=3, default=[0.01, 0.01, 0.1])
    ap.add_argument("--json"); a = ap.parse_args(argv)
    recs, info = read_records(a.bin, ["XKF1", "ARM"])
    out = gate(recs, a.core, tuple(a.bounds))
    out["reader"] = {k: info[k] for k in ("undeclared_types", "skipped_bytes", "n_resyncs")}
    print(json.dumps(out, indent=1))
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1)
    return out


if __name__ == "__main__":
    main()
