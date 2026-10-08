#!/usr/bin/env python3
"""(~/venv-fgo) Build a live-timing reproduction tape from a bag tape (tools/make_tape.py): a synthetic imu_bridge
start-up backlog, as the live node sees it but the bag (which starts later) does not.

usage: make_startup_repro.py <in.tape> <out.tape> <ramp|burst|none> [--e0 0.55] [--T 1.5] [--gap-at S --gap-len L]
  ramp : IMU + time_ref rows with th < th0 + T get th' = th + E0 * (1 - (th - th0) / T) (receipt stamps late by a
         backlog that drains linearly); they move to their new arrival position.
  burst: IMU + time_ref rows with th < th0 + E0 all get th' = th0 + E0 (one receipt instant, duplicate header
         stamps) and arrive as all the IMU rows first, then all the time_ref rows (the worst live executor order).
  none : no backlog.
  --gap-at S --gap-len L: first remove the IMU + time_ref rows with th0 + S <= th < th0 + S + L (an IMU gap seen by
         the causal gap rule; S relative to the first IMU header stamp th0).
Other rows keep their order (arrival key = running max of their own stamps). th0 = the first IMU header stamp."""
import argparse
import numpy as np
ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("dst"); ap.add_argument("mode", choices=["ramp", "burst", "none"])
ap.add_argument("--e0", type=float, default=0.55); ap.add_argument("--T", type=float, default=1.5)
ap.add_argument("--gap-at", type=float); ap.add_argument("--gap-len", type=float, default=0.025)
a = ap.parse_args()
R = np.fromfile(a.src).reshape(-1, 9).copy()
k = R[:, 0].astype(int)
th0 = R[k == 0, 1].min()
if a.gap_at is not None:
    cut = np.isin(k, (0, 7)) & (R[:, 1] >= th0 + a.gap_at) & (R[:, 1] < th0 + a.gap_at + a.gap_len)
    R = R[~cut]; k = k[~cut]
    print(f"[repro] gap: removed {cut.sum()} IMU/time_ref rows at th0 + {a.gap_at} s for {a.gap_len} s")
key = np.empty(len(R)); sub = np.zeros(len(R))
span = {"ramp": a.T, "burst": a.e0, "none": -1.0}[a.mode]
aff = np.isin(k, (0, 7)) & (R[:, 1] < th0 + span)
run = -np.inf
for i in range(len(R)):
    if not aff[i]:
        run = max(run, R[i, 1]); key[i] = run
if a.mode == "ramp":
    R[aff, 1] = R[aff, 1] + a.e0 * (1 - (R[aff, 1] - th0) / a.T)
    key[aff] = R[aff, 1]
elif a.mode == "burst":
    R[aff, 1] = th0 + a.e0
    key[aff] = th0 + a.e0
    sub[aff & (k == 7)] = 1          # all burst IMU rows before all burst time_ref rows
# affected rows sort after unaffected rows of equal key (they arrive late)
order = np.lexsort((np.arange(len(R)), sub, aff.astype(int), key))
R[order].tofile(a.dst)
print(f"[repro] {a.mode}: {aff.sum()} rows re-stamped (E0 {a.e0} s, th0 {th0:.3f}); {len(R)} rows")
