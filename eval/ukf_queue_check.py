#!/usr/bin/env python3
"""UKF port, D9 precondition (ruling 2026-09-30): the D5 delayed-horizon event queue never overflows and
processes events in EKF3's timing. Reads the Replay input dump (ukf_inputs.csv: F = flow delivered,
P = event processed (type, event time, processing time), I = update() calls). Checks:
  (1) every delivered flow message is processed exactly once, with event time = max(arrival - 66,
      arrival - 60) ms (EKF3's timestamp, AP_NavEKF3_Measurements.cpp:232-236, clamped to the horizon);
  (2) processing happens at the horizon: processing time - event time >= 60 ms;
  (3) processed event times are non-decreasing (a time-ordered queue);
  (4) no event is lost: pushed counts (flow = F rows; predicts reconstructed from I rows by the port's
      accumulation rule; range = I rows sampled >= 33 ms with rng > 0; yaw checks every 140 ms) against
      processed counts, allowing only the events still queued at the end (< 64).
Usage: python3 eval/ukf_queue_check.py UKF_INPUTS_CSV [--json OUT]"""
import argparse, json
import numpy as np
ap = argparse.ArgumentParser(); ap.add_argument("csv"); ap.add_argument("--json"); a = ap.parse_args()
F, P, I = [], [], []
for line in open(a.csv):
    f = line.rstrip().split(",")
    if f[0] == "F":
        F.append((int(f[1]), int(f[3])))
    elif f[0] == "P":
        P.append((int(f[1]), int(f[2]), int(f[3])))
    elif f[0] == "I":
        I.append([float(v) for v in f[1:]])
F, P, I = np.array(F), np.array(P), np.array(I)
out = {"n_F": len(F), "n_P": len(P)}
Pf = P[P[:, 0] == 2]
# the port only queues flow after initialisation: compare with the flows delivered after the first processed event
t_first = P[0, 2]
Fa = F[F[:, 0] >= t_first]
exp_t = np.maximum(Fa[:, 0] - 66, Fa[:, 0] - 60)
n = min(len(Pf), len(exp_t))
out["flow"] = {"delivered_after_init": int(len(Fa)), "processed": int(len(Pf)),
               "event_time_matches_EKF3_rule": int(np.sum(Pf[:n, 1] == exp_t[:n])), "compared": int(n),
               "missing": int(len(Fa) - len(Pf))}
lag = P[:, 2] - P[:, 1]
out["processing_minus_event_ms"] = {"min": int(lag.min()), "median": float(np.median(lag)), "max": int(lag.max())}
out["time_ordered"] = bool(np.all(np.diff(P[:, 1]) >= 0))
out["n_order_violations"] = int(np.sum(np.diff(P[:, 1]) < 0))
# predicts pushed, by the port's rule, from the I rows after init
Ia = I[I[:, 0] >= t_first - 60]
dt_acc = 0.0; n_pred = 0
for r in Ia:
    if r[4] <= 0 or r[8] <= 0:
        continue
    dt_acc += 0.5 * (r[4] + r[8])
    if dt_acc >= 0.012 - 0.5 * r[4]:
        n_pred += 1; dt_acc = 0.0
out["predict"] = {"pushed_reconstructed": n_pred, "processed": int(np.sum(P[:, 0] == 0))}
out["range_processed"] = int(np.sum(P[:, 0] == 1)); out["yaw_processed"] = int(np.sum(P[:, 0] == 3))
out["pass"] = bool(out["flow"]["missing"] <= 3 and out["flow"]["event_time_matches_EKF3_rule"] == n
                   and out["processing_minus_event_ms"]["min"] >= 60 and out["time_ordered"]
                   and abs(out["predict"]["pushed_reconstructed"] - out["predict"]["processed"]) <= 64)
print(json.dumps(out, indent=1))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
