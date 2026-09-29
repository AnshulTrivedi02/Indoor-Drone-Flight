#!/usr/bin/env python3
"""P4 outcome bands recomputed from the RE-FLOWN dsn baseline with the pre-registered
formula (consolidated re-run, user ruling 2026-09-29; formula verbatim from METHODOLOGY
Phase 1/2 pre-registration and the dejittered-baseline rebase):
  textured, EKF3:   n=3 evo -a (cruise) range widened by one range-width each side
  textured, FGO:    n=3 range +- max(range, 0.40 m)   (0.40 m = measured IMU-timestamp sensitivity)
  transition/blank, EKF3 and FGO:
                    displacement ratio: n=3 range +- max(range, 0.05)   (window-sensitivity bound)
                    onset:              n=3 range +- max(range, 5 m)    (a third of the 15 m threshold)
Usage: python3 eval/rerun_bands.py DSN_EVO_JSON --json OUT
"""
import argparse, json
ap = argparse.ArgumentParser(); ap.add_argument("evo"); ap.add_argument("--json", required=True); a = ap.parse_args()
tr = json.load(open(a.evo))["trials"]
def widen(vals, floor):
    lo, hi = min(vals), max(vals); m = max(hi - lo, floor)
    return [round(lo - m, 3), round(hi + m, 3)]
out = {}
for est in ("EKF3", "FGO"):
    out[est] = {}
    for w in ("tex", "trans", "blank"):
        e = [tr[f"dsn_{w}_r{r}"]["est"][est] for r in (1, 2, 3)]
        if w == "tex":
            v = [x["ate_a_cruise"]["+0.00"] for x in e]
            out[est][w] = {"ate": widen(v, 0.0 if est == "EKF3" else 0.40), "n3": v}
        else:
            rat = [x["failure"]["disp_ratio"] for x in e]; on = [x["failure"]["onset_gt_dist"] for x in e]
            out[est][w] = {"ratio": widen(rat, 0.05), "n3_ratio": rat}
            if all(o is not None for o in on):
                out[est][w]["onset"] = widen(on, 5.0); out[est][w]["n3_onset"] = on
            else:
                out[est][w]["onset"] = None; out[est][w]["n3_onset"] = on   # no divergence in some repeat: onset band undefined
json.dump(out, open(a.json, "w"), indent=1)
for est, d in out.items():
    for w, b in d.items():
        print(est, w, {k: v for k, v in b.items() if not k.startswith("n3")})
