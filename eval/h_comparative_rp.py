#!/usr/bin/env python3
"""Experiment H comparative criteria (H-H2, P-H3, H-H4), re-flown with the CORRECTED FGO priors
(docs/thesis/refly_priors/preregistration.md; D127-D130, D138). Reuses eval/h_comparative.py's own
reduction (load/per_flight/criteria/EKF) -- h_comparative.py itself is NOT edited.

Step 1 (gate): rebuild the ORIGINAL table from eval/h_comparative.py's own SETS dict and compare it,
field for field, to the stored eval/results/expH/h_comparative_2026-10-11.json. If it is not an exact
match, STOP -- something about the reduction or the input files has drifted and the recompute below
would not be trustworthy.

Step 2 (recompute): the same reduction, with s3rp_r{1,2,3} (the corrected-prior FGO hold re-fly) in
place of s3v2_r{1,2,3}. EKF3 (s1far_r1, s1far_r2, s1far_r3b) and UKF (s2v2_r{1,2,3}) are unchanged,
paired by run index, exactly as h_comparative.py already does for S2v2/S3v2.

Usage:
  python3 eval/h_comparative_rp.py --check-only                 # step 1 only (pre-flight gate)
  python3 eval/h_comparative_rp.py --json OUT.json               # steps 1 and 2; stop if step 1 fails
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h_comparative as hc

HERE = hc.HERE
STORED_ORIGINAL = os.path.join(HERE, "h_comparative_2026-10-11.json")

NEW_SET_NAME = "re-flown (S2v2 jitter-corrected UKF, S3rp corrected-prior FGO)"
NEW_SETS = {NEW_SET_NAME: (["s2v2_r1", "s2v2_r2", "s2v2_r3"], ["s3rp_r1", "s3rp_r2", "s3rp_r3"])}


def build(sets):
    ekf = [hc.per_flight(n) for n in hc.EKF]
    res = {"EKF3 (S1 far, flying)": ekf, "sets": {}}
    for name, (s2, s3) in sets.items():
        ukf = [hc.per_flight(n) for n in s2]
        fgo = [hc.per_flight(n) for n in s3]
        res["sets"][name] = {"UKF": ukf, "FGO": fgo,
                              "criteria": hc.criteria(ekf, ukf, fgo),
                              "criteria_effective_jump": hc.criteria(ekf, ukf, fgo, "_eff")}
    return res


def gate():
    repro = build(hc.SETS)
    stored = json.load(open(STORED_ORIGINAL))
    if repro != stored:
        print("h_comparative_rp: REPRODUCTION of h_comparative_2026-10-11.json MISMATCH - stopping",
              file=sys.stderr)
        return None
    print("h_comparative_rp: reproduction of h_comparative_2026-10-11.json from the original files: EXACT MATCH")
    return repro


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--check-only", action="store_true", help="run the step-1 gate only, no recompute")
    a = ap.parse_args()

    if gate() is None:
        sys.exit(1)
    if a.check_only:
        return

    new_res = build(NEW_SETS)
    out = {"gate": "h_comparative_2026-10-11.json reproduced exactly", "new": new_res}
    print(json.dumps(new_res["sets"][NEW_SET_NAME]["criteria"], indent=1))
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1)
        print(f"h_comparative_rp: wrote {a.json}")


if __name__ == "__main__":
    main()
