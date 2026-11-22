#!/usr/bin/env python3
"""IPLS stage 2 (D152/D153 preregistration, docs/thesis/iterated_smoother/preregistration.md): per-run G1/G2 gate
check for src/estimators/room_ukf_ipls_replay.py's output.

  G1: the forward pass (<trial>/room_ukf_ipls/ukf_live_check.tum) reproduces the stored
      <trial>/room_ukf/ukf_live.tum (max horizontal difference <= 1e-6 m).
  G2: iteration 0 (<trial>/room_ukf_ipls/ukf_ipls_iter0.tum) reproduces the stored
      <trial>/room_ukf/ukf_rts.tum (max horizontal difference <= 1e-6 m).

Also checks (pre-check, not part of G1/G2 itself, per room_ukf_ipls_replay.py's own docstring):
  - room_ukf_ipls/stats.json's t_anchor, n_tag_fused, dt_step_ms, tag_sigma_pos, rts_nodes match the stored
    room_ukf/stats.json exactly;
  - src_dirty == "" (the replay ran against a clean checkout).

Read-only: never writes into room_ukf/ or room_ukf_ipls/. Usage: python3 eval/ipls_gates.py TRIAL [TRIAL...]
Exit status: 0 iff every named trial passes both G1 and G2 and both pre-checks; prints one line per trial per gate."""
import json, math, os, sys

import numpy as np


def load_tum(path):
    x = np.loadtxt(path, ndmin=2)
    return x[:, 0], x[:, 1], x[:, 2]


def max_horiz_diff(path_a, path_b):
    ta, ea, na = load_tum(path_a)
    tb, eb, nb = load_tum(path_b)
    if len(ta) != len(tb):
        return None, f"row count mismatch: {len(ta)} vs {len(tb)}"
    if not np.array_equal(ta, tb):
        dt = np.max(np.abs(ta - tb))
        return None, f"timestamps differ (max |dt|={dt:.6g})"
    d = np.hypot(ea - eb, na - nb)
    return float(np.max(d)), None


def check_trial(trial):
    D = os.path.expanduser(f"~/thesis_data/trials/{trial}")
    out = {"trial": trial}
    ipls_dir, live_dir = f"{D}/room_ukf_ipls", f"{D}/room_ukf"

    g1, err1 = max_horiz_diff(f"{ipls_dir}/ukf_live_check.tum", f"{live_dir}/ukf_live.tum")
    out["G1_max_horiz_diff_m"] = g1
    out["G1_error"] = err1
    out["G1_PASS"] = (err1 is None) and (g1 <= 1e-6)

    g2, err2 = max_horiz_diff(f"{ipls_dir}/ukf_ipls_iter0.tum", f"{live_dir}/ukf_rts.tum")
    out["G2_max_horiz_diff_m"] = g2
    out["G2_error"] = err2
    out["G2_PASS"] = (err2 is None) and (g2 <= 1e-6)

    s_ipls = json.load(open(f"{ipls_dir}/stats.json"))
    s_live = json.load(open(f"{live_dir}/stats.json"))
    precheck_keys = ("t_anchor", "n_tag_fused", "dt_step_ms", "tag_sigma_pos", "rts_nodes")
    mismatches = {k: (s_ipls.get(k), s_live.get(k)) for k in precheck_keys if s_ipls.get(k) != s_live.get(k)}
    out["stats_precheck_PASS"] = not mismatches
    out["stats_precheck_mismatches"] = mismatches
    out["src_dirty"] = s_ipls.get("src_dirty")
    out["src_dirty_PASS"] = s_ipls.get("src_dirty") == ""
    out["ALL_PASS"] = out["G1_PASS"] and out["G2_PASS"] and out["stats_precheck_PASS"] and out["src_dirty_PASS"]
    return out


def main():
    trials = sys.argv[1:]
    if not trials:
        raise SystemExit(__doc__)
    all_ok = True
    results = []
    for t in trials:
        r = check_trial(t)
        results.append(r)
        all_ok &= r["ALL_PASS"]
        print(f"{t}: G1={'PASS' if r['G1_PASS'] else 'FAIL'} ({r['G1_max_horiz_diff_m']}) "
              f"G2={'PASS' if r['G2_PASS'] else 'FAIL'} ({r['G2_max_horiz_diff_m']}) "
              f"stats_precheck={'PASS' if r['stats_precheck_PASS'] else 'FAIL'} "
              f"src_dirty={'PASS' if r['src_dirty_PASS'] else 'FAIL'} ({r['src_dirty']!r}) "
              f"=> {'PASS' if r['ALL_PASS'] else 'FAIL'}")
        if r["stats_precheck_mismatches"]:
            print(f"    mismatches: {r['stats_precheck_mismatches']}")
    print(json.dumps(results, indent=1))
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
