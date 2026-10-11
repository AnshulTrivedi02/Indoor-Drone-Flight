#!/usr/bin/env python3
"""Rung 1 (2026-10-11): the UKF port in Replay against the FLYING port's own logged state.

Pairs each row of a Replay's ukf_shadow.csv with the flying port's XUKF row of the SAME TimeUS (both are the
fusion-horizon state, logged by the same NavUKF::log_state), and scores the differences with the bands of the port
equivalence harness (METHODOLOGY "UKF port validation, step 1", pre-registered 2026-09-30 for port vs offline):
  E1 3-D position: max <= 0.05 m, rms <= 0.01 m;  E3 yaw: max <= 0.05 deg;
  E5 gate decisions: accepted flow-X / flow-Y / range counts equal to within 0.1 % (from XUKS vs the CSV counters).
E4 (biases) cannot be scored: ukf_shadow.csv carries no bias column (XUKF.GBZ is reported for the flying side only).
NOTE: those bands were registered for IDENTICAL inputs (port vs offline Python). Replay vs flying differs in the
input path by construction where the derotation rule changed; the bands are applied as the existing ones, not re-registered.

Windows: the whole overlap, and "cruise" = SIM ground speed > 0.3 m/s (first to last such sample), as
ukf_shadow_replay_check.py. Usage (pymavlink): ukf_replay_vs_flying.py ORIGINAL_BIN SHADOW_CSV [--json OUT]
"""
import argparse, json, math
import numpy as np
from pymavlink import DFReader

ap = argparse.ArgumentParser()
ap.add_argument("bin"); ap.add_argument("csv"); ap.add_argument("--json")
a = ap.parse_args()

c = np.genfromtxt(a.csv, delimiter=",", names=True)
r = DFReader.DFReader_binary(a.bin)
xf, xs, sim = [], [], []
while True:
    m = r.recv_match(type=["XUKF", "XUKS", "SIM"])
    if m is None:
        break
    t = m.get_type()
    if t == "XUKF":
        xf.append((m.TimeUS, m.PN, m.PE, m.PD, m.VN, m.VE, m.VD, m.Roll, m.Pitch, m.Yaw, m.GBZ))
    elif t == "XUKS":
        xs.append((m.TimeUS, m.FXa, m.FYa, m.Ra))
    else:
        sim.append((m.TimeUS, m.Lat, m.Lng))
xf = np.array(xf, dtype=float); xs = np.array(xs, dtype=float); sim = np.array(sim, dtype=float)

# exact TimeUS pairing
ct = c["TimeUS"].astype(np.int64); ft = xf[:, 0].astype(np.int64)
common, ic, jf = np.intersect1d(ct, ft, return_indices=True)
lat, lng = sim[:, 1], sim[:, 2]
if abs(lat).max() > 1000:
    lat = lat / 1e7; lng = lng / 1e7
N = np.radians(lat - lat[0]) * 6378137
E = np.radians(lng - lng[0]) * 6378137 * math.cos(math.radians(lat.mean()))
ts = sim[:, 0] / 1e6
sp = np.hypot(np.gradient(N, ts), np.gradient(E, ts))
sp = np.convolve(sp, np.ones(25) / 25, "same")
fast = ts[sp > 0.3]


def score(mask):
    i, j = ic[mask], jf[mask]
    dp = np.stack([c["PN"][i] - xf[j, 1], c["PE"][i] - xf[j, 2], c["PD"][i] - xf[j, 3]], 1)
    d3 = np.linalg.norm(dp, axis=1)
    dyaw = (c["Yaw"][i] - xf[j, 9] + 180) % 360 - 180
    droll = c["Roll"][i] - xf[j, 7]; dpit = c["Pitch"][i] - xf[j, 8]
    dv = np.linalg.norm(np.stack([c["VN"][i] - xf[j, 4], c["VE"][i] - xf[j, 5], c["VD"][i] - xf[j, 6]], 1), axis=1)
    k = int(np.argmax(d3))
    return {"n": int(len(i)),
            "t_s": [float(common[mask][0] / 1e6), float(common[mask][-1] / 1e6)],
            "E1_pos3d_max_m": float(d3.max()), "E1_pos3d_rms_m": float(np.sqrt((d3 ** 2).mean())),
            "E1_pass": bool(d3.max() <= 0.05 and np.sqrt((d3 ** 2).mean()) <= 0.01),
            "pos3d_p95_m": float(np.percentile(d3, 95)), "pos3d_final_m": float(d3[-1]),
            "pos3d_argmax_t_s": float(common[mask][k] / 1e6),
            "E3_yaw_max_deg": float(abs(dyaw).max()), "E3_pass": bool(abs(dyaw).max() <= 0.05),
            "yaw_p95_deg": float(np.percentile(abs(dyaw), 95)),
            "roll_max_deg": float(abs(droll).max()), "pitch_max_deg": float(abs(dpit).max()),
            "vel3d_max_mps": float(dv.max())}


out = {"bin": a.bin, "csv": a.csv, "csv_rows": int(len(ct)), "xukf_rows": int(len(ft)), "paired": int(len(common)),
       "csv_first_s": float(ct[0] / 1e6), "xukf_first_s": float(ft[0] / 1e6)}
out["all"] = score(np.ones(len(common), bool))
if len(fast):
    out["cruise"] = score((common / 1e6 >= fast[0]) & (common / 1e6 <= fast[-1]))
# E5: accepted counters (flying XUKS vs Replay CSV), as INCREMENTS over the paired window (first to last common
# time): the two runs initialise at different instants, so their cumulative totals start from different points
t0, tl = common[0], common[-1]
ks0 = np.searchsorted(xs[:, 0], t0, side="right") - 1
ks = np.searchsorted(xs[:, 0], tl, side="right") - 1
kc0 = int(np.where(ct == t0)[0][0]); kc = int(np.where(ct == tl)[0][0])
e5 = {}
for name, col in (("flowX", 1), ("flowY", 2), ("range", 3)):
    cc = c[{"flowX": "FXa", "flowY": "FYa", "range": "Ra"}[name]]
    fv, rv = float(xs[ks, col] - xs[ks0, col]), float(cc[kc] - cc[kc0])
    e5[name] = {"flying": fv, "replay": rv, "rel_diff": abs(fv - rv) / max(fv, 1.0),
                "cumulative_flying_replay": [float(xs[ks, col]), float(cc[kc])]}
out["E5_accepted_increments_over_paired_window"] = e5
out["E5_pass"] = all(v["rel_diff"] <= 0.001 for v in e5.values())
out["flying_GBZ_rad_s_last"] = float(xf[-1, 10])     # XUKF.GBZ = x[11] / 0.0125 (rad/s)
print(json.dumps(out, indent=1))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
