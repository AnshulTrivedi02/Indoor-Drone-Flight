#!/usr/bin/env python3
"""Experiment H comparative criteria (H-H2, P-H3, H-H4; pre-registered in docs/tag_hold_design.md §e) from the STORED
h_score.py outputs (eval/results/expH/*.json). No re-scoring: a reduction of the per-flight score files only.

Method, as for the adjudicated S2/S3 table (METHODOLOGY "H comparative criteria across S1 re-fly (EKF3 flying), S2 (UKF)
and S3 (FGO), paired by run index"); the script reproduces that table exactly from s2_r*/s3_r*:
  - hold error = mean of the vehicle hold-window means (hold_windows_vehicle[*].mean_m); gyro activity = mean of the
    windows' gyro_hp_rms_rad_s. Both are vehicle quantities, so each comes from the flight the estimator flew.
  - re-lock jump = jump_pos_m of the FLYING estimator (EKF3 in S1 far / r3b; UKF_port in S2*; FGO_flying in S3*) for
    the ~5 s and ~15 s losses (losses[0], losses[1]). Both readings (as scored, and 'effective') are kept.
  - EKF3 = the S1 far-spawn re-fly (s1far_r1, s1far_r2, s1far_r3b), paired by run index, as before.
Criteria (as worded):
  H-H2: FGO < EKF3 and FGO < UKF mean hold error, 3/3 flights.
  P-H3: gyro activity in the hold windows within 1.5x across estimators (max/min <= 1.5), per run.
  H-H4: (a) after the 15 s loss EKF3's jump > UKF's and > FGO's, 3/3; (b) after the 5 s loss the jumps within 1.5x, 3/3.
Usage: python3 eval/h_comparative.py [--json out.json]
"""
import argparse, json, os

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "expH")
EKF = ["s1far_r1", "s1far_r2", "s1far_r3b"]
SETS = {"earlier (S2 old UKF port, S3 FGO noise fix only)": (["s2_r1", "s2_r2", "s2_r3"], ["s3_r1", "s3_r2", "s3_r3"]),
        "re-flown (S2v2 jitter-corrected UKF, S3v2 final FGO, old priors)": (["s2v2_r1", "s2v2_r2", "s2v2_r3"],
                                                                             ["s3v2_r1", "s3v2_r2", "s3v2_r3"])}


def load(n):
    return json.load(open(os.path.join(HERE, n + ".json")))


def flying(d):
    for k in ("UKF_port", "FGO_flying"):
        if k in d["losses"][0]:
            return k
    return "EKF3"


def per_flight(n):
    d = load(n); k = flying(d); hw = d["hold_windows_vehicle"]
    out = {"file": n, "flying_key": k,
           "hold_mean_mm": 1e3 * sum(w["mean_m"] for w in hw) / len(hw),
           "gyro_hp_rms_rad_s": sum(w["gyro_hp_rms_rad_s"] for w in hw) / len(hw),
           "loss_durations_s": [round(L["duration_s"], 2) for L in d["losses"]]}
    for i, lab in ((0, "5s"), (1, "15s")):
        e = d["losses"][i][k]
        out[f"jump_{lab}_mm"] = 1e3 * e["jump_pos_m"]
        out[f"jump_{lab}_eff_mm"] = 1e3 * e["effective"]["jump_pos_m"]
    return out


def criteria(ekf, ukf, fgo, jkey=""):
    runs = []
    for e, u, f in zip(ekf, ukf, fgo):
        g = [e["gyro_hp_rms_rad_s"], u["gyro_hp_rms_rad_s"], f["gyro_hp_rms_rad_s"]]
        j5 = [e[f"jump_5s{jkey}_mm"], u[f"jump_5s{jkey}_mm"], f[f"jump_5s{jkey}_mm"]]
        runs.append({"hh2": f["hold_mean_mm"] < e["hold_mean_mm"] and f["hold_mean_mm"] < u["hold_mean_mm"],
                     "lowest_hold": min((e["hold_mean_mm"], "EKF3"), (u["hold_mean_mm"], "UKF"), (f["hold_mean_mm"], "FGO"))[1],
                     "ph3_ratio": max(g) / min(g), "ph3": max(g) / min(g) <= 1.5,
                     "hh4a": e[f"jump_15s{jkey}_mm"] > u[f"jump_15s{jkey}_mm"] and e[f"jump_15s{jkey}_mm"] > f[f"jump_15s{jkey}_mm"],
                     "hh4b_ratio": max(j5) / min(j5), "hh4b": max(j5) / min(j5) <= 1.5})
    n = lambda k: sum(r[k] for r in runs)
    return {"runs": runs,
            "H-H2": f"{'PASS' if n('hh2') == 3 else 'FAIL'} ({n('hh2')}/3 FGO lowest)",
            "P-H3": f"{'PASS' if n('ph3') == 3 else 'FAIL'} ({n('ph3')}/3 within 1.5x)",
            "H-H4 (15 s)": f"{'PASS' if n('hh4a') == 3 else 'FAIL'} ({n('hh4a')}/3 EKF3 largest)",
            "H-H4 (5 s)": f"{'PASS' if n('hh4b') == 3 else 'FAIL'} ({n('hh4b')}/3 within 1.5x)"}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--json"); a = ap.parse_args()
    ekf = [per_flight(n) for n in EKF]; res = {"EKF3 (S1 far, flying)": ekf, "sets": {}}
    for name, (s2, s3) in SETS.items():
        ukf = [per_flight(n) for n in s2]; fgo = [per_flight(n) for n in s3]
        res["sets"][name] = {"UKF": ukf, "FGO": fgo, "criteria": criteria(ekf, ukf, fgo),
                             "criteria_effective_jump": criteria(ekf, ukf, fgo, "_eff")}
        print(f"\n== {name}")
        print("run | hold mean EKF3/UKF/FGO (mm) | gyro hp rms (rad/s) | 15 s jump (mm) | 5 s jump (mm) [effective 15 s | 5 s]")
        for i in range(3):
            e, u, f = ekf[i], ukf[i], fgo[i]
            print(f"{i+1} | {e['hold_mean_mm']:.1f} / {u['hold_mean_mm']:.1f} / {f['hold_mean_mm']:.1f} | "
                  f"{e['gyro_hp_rms_rad_s']:.4f} / {u['gyro_hp_rms_rad_s']:.4f} / {f['gyro_hp_rms_rad_s']:.4f} | "
                  f"{e['jump_15s_mm']:.0f} / {u['jump_15s_mm']:.0f} / {f['jump_15s_mm']:.0f} | "
                  f"{e['jump_5s_mm']:.0f} / {u['jump_5s_mm']:.0f} / {f['jump_5s_mm']:.0f} [eff "
                  f"{e['jump_15s_eff_mm']:.0f}/{u['jump_15s_eff_mm']:.0f}/{f['jump_15s_eff_mm']:.0f} | "
                  f"{e['jump_5s_eff_mm']:.0f}/{u['jump_5s_eff_mm']:.0f}/{f['jump_5s_eff_mm']:.0f}]")
        c = res["sets"][name]["criteria"]; ce = res["sets"][name]["criteria_effective_jump"]
        for k in ("H-H2", "P-H3", "H-H4 (15 s)", "H-H4 (5 s)"):
            print(f"  {k}: {c[k]}" + (f"   [effective jump: {ce[k]}]" if k.startswith("H-H4") else ""))
        print("  lowest hold per run:", [r["lowest_hold"] for r in c["runs"]],
              " P-H3 max/min:", [round(r["ph3_ratio"], 2) for r in c["runs"]],
              " 5 s max/min:", [round(r["hh4b_ratio"], 2) for r in c["runs"]])
    if a.json:
        json.dump(res, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
