#!/usr/bin/env python3
"""Experiment H, S2 gate, UKF tier A (docs/h_backends_tag_input.md section 1.1, PRE-REGISTERED): compare the C++ port's
states (UKF_Equiv on the export of eval/ukf_tag_event_export.py) with the offline ROOM UKF's, per event, over the
WHOLE replay (initialisation to the end):
  UA1 3-D position difference max <= 1 mm
  UA2 yaw difference max <= 0.01 deg
  UA3 gyro-z bias (rate form) |d| <= 0.1 deg/min; accel bias |d| <= 0.001 m/s^2
  UA4 gate decisions (flow X/Y, range, pseudo-yaw firings) >= 99.9% identical; accepted counts within 0.1%
  UA5 the re-anchor is the first tag event on both sides; the state right after it agrees to <= 1e-9 (m, rad);
      every tag event is fused (no gate); 0 pseudo-yaw fusions after the anchor on both sides
Also reported per predict step (the state after each predict).
Usage (~/venv-evo): python3 eval/ukf_tag_equivalence.py PREFIX [--json OUT]   (PREFIX.npz, PREFIX_port.bin)"""
import argparse, json, math
import numpy as np

ap = argparse.ArgumentParser(); ap.add_argument("prefix"); ap.add_argument("--json"); a = ap.parse_args()
e = np.load(a.prefix + ".npz")
typ, inp, xp, flp, tev = e["type"], e["inputs"], e["x_after"], e["flags"], e["time"]
n = len(typ)
raw = np.fromfile(a.prefix + "_port.bin", dtype=np.uint8)
rec = 15 * 8 + 2
assert raw.size == n * rec, (raw.size, n * rec)
raw = raw.reshape(n, rec)
xc = raw[:, :120].copy().view(np.float64).reshape(n, 15)
flc = raw[:, 120:].astype(np.int8)

dpos = np.linalg.norm(xc[:, 0:3] - xp[:, 0:3], axis=1)
dyaw = np.degrees(np.abs((xc[:, 8] - xp[:, 8] + math.pi) % (2 * math.pi) - math.pi))
pred = typ == 0
dt_step = inp[pred, 6].mean()
dbgz = np.abs(xc[:, 11] - xp[:, 11]) / dt_step * (180 / math.pi) * 60
dba = np.abs(xc[:, 12:15] - xp[:, 12:15]).max(1) / dt_step
out = {"events": int(n), "predict_steps": int(pred.sum()), "dt_step_s": float(dt_step), "live_tum_identical": bool(e["live_tum_identical"])}
out["UA1"] = {"max_m": float(dpos.max()), "rms_m": float(np.sqrt(np.mean(dpos ** 2))), "max_m_predict_steps": float(dpos[pred].max()),
              "end_m": float(dpos[-1]), "band": "max <= 1e-3 m"}
out["UA1"]["pass"] = out["UA1"]["max_m"] <= 1e-3
out["UA2"] = {"max_deg": float(dyaw.max()), "max_deg_predict_steps": float(dyaw[pred].max()), "band": "max <= 0.01 deg"}
out["UA2"]["pass"] = out["UA2"]["max_deg"] <= 0.01
out["UA3"] = {"max_gyro_z_bias_deg_per_min": float(dbgz.max()), "max_accel_bias_mps2": float(dba.max())}
out["UA3"]["pass"] = out["UA3"]["max_gyro_z_bias_deg_per_min"] <= 0.1 and out["UA3"]["max_accel_bias_mps2"] <= 0.001
UA4, ok = {}, True
for name, tsel, col in (("flow_x", 2, 0), ("flow_y", 2, 1), ("range", 1, 0), ("yaw_pseudo", 3, 0)):
    s = typ == tsel
    same = float(np.mean(flp[s, col] == flc[s, col])) if s.any() else 1.0
    ap_, ac_ = int(flp[s, col].sum()), int(flc[s, col].sum())
    rel = abs(ap_ - ac_) / max(ap_, 1)
    UA4[name] = {"n": int(s.sum()), "identical_frac": same, "accepted_python": ap_, "accepted_port": ac_, "count_rel_diff": rel}
    ok = ok and same >= 0.999 and rel <= 0.001
UA4["pass"] = ok
out["UA4"] = UA4
tag_ev = np.where((typ == 4) | (typ == 5))[0]
i_anc = np.where(typ == 5)[0]
first_is_anchor = len(i_anc) == 1 and tag_ev[0] == i_anc[0]
ia = int(i_anc[0])
d_anchor = np.abs(xc[ia] - xp[ia]); d_anchor[6:9] = np.abs((xc[ia, 6:9] - xp[ia, 6:9] + math.pi) % (2 * math.pi) - math.pi)
yaw_after_py = int(((typ == 3) & (np.arange(n) > ia) & (flp[:, 0] == 1)).sum())
yaw_after_port = int(((typ == 3) & (np.arange(n) > ia) & (flc[:, 0] == 1)).sum())
yaw_checks_after = int(((typ == 3) & (np.arange(n) > ia)).sum())
fix_match = np.allclose(xc[ia, [0, 1]], inp[ia, [0, 1]], atol=0, rtol=0) and abs(xc[ia, 8] - inp[ia, 2]) == 0
out["UA5"] = {"anchor_event": ia, "anchor_t": float(tev[ia]), "first_tag_event_is_anchor": bool(first_is_anchor),
              "anchor_state_max_abs_diff": float(d_anchor.max()), "port_state_equals_fix_exactly": bool(fix_match),
              "tag_events": int(len(tag_ev)), "tag_fused_python": int(flp[tag_ev, 0].sum()), "tag_fused_port": int(flc[tag_ev, 0].sum()),
              "pseudo_yaw_checks_after_anchor_in_stream": yaw_checks_after,
              "pseudo_yaw_fusions_after_anchor": {"python": yaw_after_py, "port": yaw_after_port}}
out["UA5"]["pass"] = bool(first_is_anchor and d_anchor.max() <= 1e-9 and flp[tag_ev, 0].sum() == len(tag_ev)
                          and flc[tag_ev, 0].sum() == len(tag_ev) and yaw_after_py == 0 and yaw_after_port == 0)
post = np.arange(n) > ia
out["diag_after_anchor"] = {"dpos_max_m": float(dpos[post].max()), "dyaw_max_deg": float(dyaw[post].max())}
out["diag_before_anchor"] = {"dpos_max_m": float(dpos[~post].max()), "dyaw_max_deg": float(dyaw[~post].max())}
bad = np.where((dpos > 1e-6) | (dyaw > 1e-6))[0]
out["diag_first_divergence_1e-6"] = None if not len(bad) else {"event": int(bad[0]), "type": int(typ[bad[0]]), "t": float(tev[bad[0]]),
                                                                 "dpos_m": float(dpos[bad[0]]), "dyaw_deg": float(dyaw[bad[0]])}
out["pass"] = all(out[k]["pass"] for k in ("UA1", "UA2", "UA3", "UA4", "UA5"))
print(json.dumps(out, indent=1))
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
