"""(~/venv-fgo) Score a fgo_cpp_live_replay output against its tape: future stamps (header clock and SITL clock) and delta_att.
usage: score_startup_repro.py <tape> <out_prefix> <bag_dir | GT.npz> [--cache GT.npz]
Ground truth: read from the bag (eval/fgo_cpp_sitl_check.read_bag; --cache also saves it as an .npz with array G),
or from such an .npz. Reports keyframes stamped ahead of the receipt clock and of the
SITL clock (the live XFGO.Age wrap), and delta_att (whole, and t_k > 45 s) as the stage-5 scorer computes it.
Used for the time_ref start-up fix (docs/handovers/2026-10-08_fgo_cpp_timeref_fix.md)."""
import sys, json, numpy as np
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "eval"))
import fgo_cpp_sitl_check as C
tape, pre, fg = sys.argv[1:4]
R = np.fromfile(tape).reshape(-1, 9)
R = R[R[:, 0] != 8]                         # 'armed' rows are not arrivals
L = np.fromfile(pre + ".live.f64").reshape(-1, 6)
# receipt clock at each arrival: running max of the IMU/time_ref receipt stamps (the other kinds carry capture stamps)
rec = np.where(np.isin(R[:, 0], (0, 7)), R[:, 1], -np.inf)
now_h = np.maximum.accumulate(rec)
ts = np.where(R[:, 0] == 7, R[:, 2], -np.inf)
now_s = np.maximum.accumulate(ts)          # newest SITL sensor time received
ai = L[:, 5].astype(int) - 1
ahead_h = L[:, 0] - now_h[ai]
sent = L[:, 2] > 0
ahead_s = L[sent, 3] / 1e6 - now_s[ai[sent]]
out = {"n_kf": int(len(L)), "n_sent": int(sent.sum()),
       "kf_ahead_of_receipt_clock": int((ahead_h > 0).sum()), "max_ahead_ms": round(1e3 * float(ahead_h.max()), 1),
       "sent_ahead_of_sitl_clock (would wrap XFGO.Age)": int((ahead_s > 0).sum()),
       "max_sent_ahead_ms": round(1e3 * float(ahead_s.max()), 1) if sent.any() else None,
       "median_output_age_ms (receipt clock)": round(-1e3 * float(np.median(ahead_h)), 1)}
if fg.endswith(".npz"):
    G = np.load(fg)["G"]
else:
    G = C.read_bag(fg)[1]
    if len(sys.argv) > 5 and sys.argv[4] == "--cache":
        np.savez(sys.argv[5], G=G)
K = C.kf_states(pre)
for lo in (0, 45):
    r = C.fit_delta(K[K[:, 0] > lo], G)
    out[f"delta_att_ms (t_k>{lo})"] = r.get("delta_att_ms")
    if lo == 0:
        out["delta_halves_ms"] = r.get("diag_delta_halves_ms")
print(json.dumps(out))
