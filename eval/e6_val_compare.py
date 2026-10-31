#!/usr/bin/env python3
"""E6 validation gate V-E6 (docs/thesis/tier1/e6_preregistration.md §7): the supplied-map path run with the TRUE
(surveyed) map must reproduce the stored Experiment 2 tracks. Compares, per flight:
  UKF: <in-root>/<trial>/room_ukf_e6_<name>/{ukf_live,ukf_rts}.tum  against ~/thesis_data/trials/<trial>/room_ukf/
  FGO: <in-root>/<trial>/room_fgo_e6_<name>/fgo_live.tum            against ~/thesis_data/trials/<trial>/room_fgo/
PASS iff, for every track: rows 1:1 with identical 6-dp timestamp strings; t_anchor and the tag count (n_tag_fused /
n_tag_factors) equal the stored stats.json; RMS horizontal difference <= 1.0 mm and max <= 2.0 mm over the rows inside
the scored lap window (eval/results/expT/<trial>.json window_s). The tolerances are V-E5b's (e5_design.md §8.4), for
the same reason: the re-expression p' = t + Rz(0)(p - t) can differ from p by one unit in the last place, which the
6-dp TUM rounding can turn into a 1 um step. Byte identity is reported, never the gate.
Usage: e6_val_compare.py TRIAL --name NAME [--est ukf|fgo|both] --json OUT (a NEW file under docs/thesis/tier1/ or
~/thesis_data/tier1/). Exit 0 = PASS, 1 = FAIL."""
import argparse, hashlib, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.join(HERE, "..")
RMS_TOL_M, MAX_TOL_M = 1.0e-3, 2.0e-3
ap = argparse.ArgumentParser(); ap.add_argument("trial"); ap.add_argument("--name", required=True)
ap.add_argument("--est", choices=["ukf", "fgo", "both"], default="both"); ap.add_argument("--json", required=True)
ap.add_argument("--in-root", default=os.path.expanduser("~/thesis_data/tier1"))
a = ap.parse_args()
_real = lambda p: os.path.realpath(os.path.expanduser(p))
_under = lambda p, r: _real(p) == _real(r) or _real(p).startswith(_real(r) + os.sep)
if not (_under(a.json, "~/thesis_data/tier1") or _under(a.json, os.path.join(REPO, "docs", "thesis", "tier1"))) or os.path.exists(a.json):
    sys.exit(f"[e6] REFUSED: --json must be a NEW file under ~/thesis_data/tier1 or docs/thesis/tier1/ (got {a.json!r})")
S = os.path.expanduser(f"~/thesis_data/trials/{a.trial}"); N = os.path.join(a.in_root, a.trial)
W = json.load(open(os.path.join(REPO, "eval", "results", "expT", f"{a.trial}.json")))["window_s"]


def rd(p):
    ts, xy = [], []
    for ln in open(p):
        f = ln.split()
        if f:
            ts.append(f[0]); xy.append((float(f[1]), float(f[2])))
    return ts, np.array(xy).reshape(-1, 2)


sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
pairs = []
if a.est in ("ukf", "both"):
    pairs += [("UKF live", f"{N}/room_ukf_e6_{a.name}/ukf_live.tum", f"{S}/room_ukf/ukf_live.tum", "ukf"),
              ("UKF RTS", f"{N}/room_ukf_e6_{a.name}/ukf_rts.tum", f"{S}/room_ukf/ukf_rts.tum", "ukf")]
if a.est in ("fgo", "both"):
    pairs += [("FGO live", f"{N}/room_fgo_e6_{a.name}/fgo_live.tum", f"{S}/room_fgo/fgo_live.tum", "fgo")]
out = {"trial": a.trial, "name": a.name, "window_s": W, "tol_rms_m": RMS_TOL_M, "tol_max_m": MAX_TOL_M, "tracks": {}}
ok_all = True
for lab, pn, ps, est in pairs:
    r = {"new": pn, "stored": ps}
    tn, xn = rd(pn); tsd, xs = rd(ps)
    r["rows_new"], r["rows_stored"] = len(tn), len(tsd); r["rows_1to1"] = tn == tsd
    r["byte_identical"] = sha(pn) == sha(ps)
    if r["rows_1to1"]:
        t = np.array([float(x) for x in tn]); w = (t >= W[0]) & (t <= W[1]); dd = np.hypot(*(xn - xs).T)
        r.update({"rms_window_m": float(np.sqrt(np.mean(dd[w] ** 2))), "max_window_m": float(dd[w].max()),
                  "rms_all_m": float(np.sqrt(np.mean(dd ** 2))), "max_all_m": float(dd.max())})
    sn = json.load(open(os.path.join(os.path.dirname(pn), "stats.json"))); ss = json.load(open(os.path.join(os.path.dirname(ps), "stats.json")))
    kt = "n_tag_fused" if est == "ukf" else "n_tag_factors"
    r["t_anchor_equal"] = sn["t_anchor"] == ss["t_anchor"]; r["tag_count_equal"] = sn[kt] == ss[kt]
    r["n_fixes_remapped"] = sn.get("e6", {}).get("n_fixes_remapped")
    r["pass"] = bool(r["rows_1to1"] and r["t_anchor_equal"] and r["tag_count_equal"] and r["rms_window_m"] <= RMS_TOL_M
                     and r["max_window_m"] <= MAX_TOL_M)
    ok_all &= r["pass"]; out["tracks"][lab] = r
    print(f"{a.trial} {lab:9s} {'PASS' if r['pass'] else 'FAIL'} rows {len(tn)}/{len(tsd)} byte-identical {r['byte_identical']} "
          f"rms {r.get('rms_window_m', float('nan')) * 1e6:.3f} um max {r.get('max_window_m', float('nan')) * 1e6:.3f} um")
out["pass"] = bool(ok_all)
json.dump(out, open(a.json, "w"), indent=1)
sys.exit(0 if ok_all else 1)
