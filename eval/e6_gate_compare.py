#!/usr/bin/env python3
"""E6 byte-identity gates G0-UKF and G-E4' (docs/thesis/tier1/e6_preregistration.md §7): the E6 branch's
room_ukf_replay.py / room_fgo_replay.py WITHOUT --tag-map must reproduce the stored Experiment 2 tracks byte for byte.
  G0-UKF: ~/thesis_data/tier1/e6_g0_ukf/<t>/room_ukf/{ukf_live,ukf_rts}.tum  vs ~/thesis_data/trials/<t>/room_ukf/
  G-E4' : ~/thesis_data/tier1/e6_g0_fgo/<t>/room_fgo_w0.25/fgo_live.tum      vs ~/thesis_data/trials/<t>/room_fgo/
          (+ t_anchor and n_tag_factors equal)
Reads only; writes --json (a NEW file). Exit 0 = every file identical."""
import argparse, hashlib, json, os, sys
ap = argparse.ArgumentParser(); ap.add_argument("--json", required=True); a = ap.parse_args()
if os.path.exists(a.json): sys.exit(f"refusing to overwrite {a.json}")
H = os.path.expanduser("~/thesis_data"); TR = [f"T_{c}_r{r}" for c in "ABCD" for r in (1, 2, 3)]
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None
rows = []
for t in TR:
    for f in ("ukf_live.tum", "ukf_rts.tum"):
        n, s = f"{H}/tier1/e6_g0_ukf/{t}/room_ukf/{f}", f"{H}/trials/{t}/room_ukf/{f}"
        rows.append({"gate": "G0-UKF", "trial": t, "file": f, "sha256_new": sha(n), "sha256_stored": sha(s)})
    n, s = f"{H}/tier1/e6_g0_fgo/{t}/room_fgo_w0.25/fgo_live.tum", f"{H}/trials/{t}/room_fgo/fgo_live.tum"
    r = {"gate": "G-E4'", "trial": t, "file": "fgo_live.tum", "sha256_new": sha(n), "sha256_stored": sha(s)}
    try:
        sn, ss = json.load(open(os.path.join(os.path.dirname(n), "stats.json"))), json.load(open(os.path.join(os.path.dirname(s), "stats.json")))
        r["t_anchor_equal"] = sn["t_anchor"] == ss["t_anchor"]; r["n_tag_factors_equal"] = sn["n_tag_factors"] == ss["n_tag_factors"]
        r["keyframe_failures"] = sn["keyframe_failures"]
    except (OSError, KeyError):
        r["t_anchor_equal"] = r["n_tag_factors_equal"] = False
    rows.append(r)
for r in rows:
    r["identical"] = r["sha256_new"] is not None and r["sha256_new"] == r["sha256_stored"] and r.get("t_anchor_equal", True) and r.get("n_tag_factors_equal", True)
out = {"rows": rows}
for g in ("G0-UKF", "G-E4'"):
    rr = [r for r in rows if r["gate"] == g]; out[g] = {"identical": sum(r["identical"] for r in rr), "of": len(rr)}
    print(f"{g}: {out[g]['identical']}/{out[g]['of']} identical")
out["pass"] = all(r["identical"] for r in rows)
json.dump(out, open(a.json, "w"), indent=1)
sys.exit(0 if out["pass"] else 1)
