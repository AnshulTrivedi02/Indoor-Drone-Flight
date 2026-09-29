#!/usr/bin/env python3
"""Phase 2 (`fwd_*`) scoring against the pre-registered criteria.

METHODOLOGY "Phase 2 — `fwd_*` dataset: pre-registration" is the only source of the
bands below; nothing here is tuned after seeing the data. PRIMARY criteria (P1, P3,
P4) are judged per trial. DIAGNOSTICS are reported and never gate (P2 by the user's
2026-09-24 ruling; RTF; forward-image and /imu/time_ref rates; every UKF metric; evo -a
(cruise) on transition and blank).

Inputs (all already computed; this script only applies bands):
  eval/results/input_timing_p2fwd.json   eval/input_timing.py on the nine fwd bags
  eval/results/input_timing_linmap.json  same, dsn_* (corrected clock map) -> P2 limits
  eval/results/flow_quality_p2fwd.json   eval/flow_quality.py on the nine fwd bags
  eval/results/flow_quality_dsn.json     same, dsn_* -> P3 reference means
  eval/results/phase2_fwd_evo.json       eval/three_way_eval.py on the nine fwd bags
  <trial>/logs/fly_trial.log, <trial>/bag/metadata.yaml   RTF and topic rates

Also scores the plain-wall sets (METHODOLOGY Phase 2b and its Phase 1 check) with the
same bands: --trials picks the trials, and --timing / --flow / --evo the result files.

Usage (any python3 with PyYAML):
  python3 eval/phase2_score.py [--json OUT]                               (Phase 2, fwd_*)
  python3 eval/phase2_score.py --trials fwdplain --timing input_timing_fwdplain.json \
      --flow flow_quality_fwdplain.json --evo fwdplain_evo.json [--json OUT]
"""
import argparse, json, os, re, statistics as st
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
TRIALS_DIR = os.path.expanduser("~/thesis_data/trials")
WORLDS = ("tex", "trans", "blank")

# P4 bands, verbatim from the Phase 2 pre-registration table.
P4 = {
    "EKF3": {"tex": {"ate": (1.26, 8.13)},
             "trans": {"ratio": (0.51, 0.63), "onset": (96, 108)},
             "blank": {"ratio": (0.12, 0.27), "onset": (13, 24)}},
    "FGO": {"tex": {"ate": (4.17, 5.14)},
            "trans": {"ratio": (0.67, 0.78), "onset": (90, 101)},
            "blank": {"ratio": (1.45, 1.60), "onset": (28, 42)}},
}


def load(name):
    return json.load(open(os.path.join(RES, name)))


def inband(x, lo, hi):
    return x is not None and lo <= x <= hi


def world(trial):
    return next(x for x in trial.split("_") if x in WORLDS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--trials", default="fwd",
                    help="dataset prefix (<p>_{tex,trans,blank}_r{1,2,3}, flight order) or a comma list of trial names")
    ap.add_argument("--timing", default="input_timing_p2fwd.json")
    ap.add_argument("--flow", default="flow_quality_p2fwd.json")
    ap.add_argument("--evo", default="phase2_fwd_evo.json")
    ap.add_argument("--p4-bands", default=os.environ.get("P4_BANDS"),
                    help="JSON from eval/rerun_bands.py; overrides the Phase 2 P4 table (consolidated re-run)")
    a = ap.parse_args()
    if a.p4_bands:
        nb = json.load(open(a.p4_bands))
        for est in P4:
            for w in P4[est]:
                P4[est][w] = {k: tuple(v) for k, v in nb[est][w].items() if not k.startswith("n3") and v is not None}
        print(f"P4 bands from {a.p4_bands}")
    trials = [x for x in a.trials.split(",") if x] if "," in a.trials else \
        [f"{a.trials}_{w}_r{r}" for r in (1, 2, 3) for w in WORLDS]

    it, it_dsn = load(a.timing), load("input_timing_linmap.json")
    fq, fq_dsn = load(a.flow), load("flow_quality_dsn.json")
    evo = load(a.evo)["trials"]

    def dsn_mean(src, w, key):
        return st.mean(src[f"dsn_{w}_r{r}"][key] for r in (1, 2, 3))

    out, any_primary_fail, any_pending = {}, False, False
    for t in trials:
        w = world(t)
        chk = {}   # name -> (value, band text, pass, primary?)

        # ── P1: estimator-input header timing (PRIMARY) ──
        ins = it[t]["inputs"]
        for top in ("/optical_flow/measurement", "/downward_lidar/range"):
            r, late = ins[top]["rate_hz"], ins[top]["pct_gap_gt_1.5x"]
            chk[f"P1 {top} rate"] = (round(r, 3), "30.30 Hz ± 0.1%", abs(r / 30.30303 - 1) <= 0.001, True)
            chk[f"P1 {top} >1.5x"] = (round(late, 3), "≤ 0.5%", late <= 0.5, True)
        imu = ins["/imu/data_raw"]
        chk["P1 IMU gap mean"] = (round(imu["gap_mean_ms"], 4), "3.0005 ± 0.003 ms",
                                  abs(imu["gap_mean_ms"] - 3.0005) <= 0.003, True)
        chk["P1 IMU gap p99"] = (round(imu["gap_p99_ms"], 2), "≤ 10 ms", imu["gap_p99_ms"] <= 10, True)

        # ── P3: downward-flow conditions vs same-world dsn n=3 mean (PRIMARY) ──
        f = fq[t]
        ref = lambda k: dsn_mean(fq_dsn, w, k)
        chk["P3 inlier mean"] = (round(f["inlier_mean"], 4), f"{ref('inlier_mean'):.4f} ± 0.01",
                                 abs(f["inlier_mean"] - ref("inlier_mean")) <= 0.01, True)
        chk["P3 % below 0.5"] = (round(f["inlier_pct_below_0.5"], 2), f"{ref('inlier_pct_below_0.5'):.2f} ± 3 pp",
                                 abs(f["inlier_pct_below_0.5"] - ref("inlier_pct_below_0.5")) <= 3, True)
        chk["P3 features"] = (round(f["features_mean"], 2), f"{ref('features_mean'):.2f} ± 5%",
                              abs(f["features_mean"] / ref("features_mean") - 1) <= 0.05, True)
        fy, fy_ref = f["flow_y_raw_mean"], ref("flow_y_raw_mean")
        if w == "blank":
            chk["P3 flow_y_raw"] = (round(fy, 2), f"{fy_ref:.2f} ± 5 px/s", abs(fy - fy_ref) <= 5, True)
        else:
            chk["P3 flow_y_raw"] = (round(fy, 2), f"{fy_ref:.2f} ± 2%", abs(fy / fy_ref - 1) <= 0.02, True)
        gx = max(abs(v) for v in f["gt_x_range"])
        chk["P3 GT |x|"] = (round(gx, 4), "≤ 0.05 m", gx <= 0.05, True)
        if w == "trans":
            chk["P3 switch bin"] = (f["switch_gt_y"], "80–82 m", inband(f["switch_gt_y"], 80, 82), True)
            for k in ("inlier_y<75", "inlier_y>85"):
                chk[f"P3 level {k}"] = (round(f[k], 4), f"{ref(k):.4f} ± 0.01", abs(f[k] - ref(k)) <= 0.01, True)

        # ── P4: EKF3 and FGO outcome (PRIMARY) ──
        e = evo[t]["est"]
        pending = []   # estimators with no result (replay refused): NOT EVALUATED, never pass/fail
        for est in ("EKF3", "FGO"):
            b = P4[est][w]
            if est not in e:
                chk[f"P4 {est}"] = ("—", "NOT EVALUATED (pending ruling)", None, True)
                pending.append(est)
                continue
            if w == "tex":
                v = e[est]["ate_a_cruise"]["+0.00"]
                chk[f"P4 {est} evo -a (cruise)"] = (round(v, 3), f"[{b['ate'][0]}, {b['ate'][1]}] m", inband(v, *b["ate"]), True)
            else:
                fl = e[est]["failure"]
                chk[f"P4 {est} ratio"] = (round(fl["disp_ratio"], 3), f"[{b['ratio'][0]}, {b['ratio'][1]}]",
                                          inband(fl["disp_ratio"], *b["ratio"]), True)
                on = fl["onset_gt_dist"]
                if "onset" in b:
                    chk[f"P4 {est} onset"] = (None if on is None else round(on, 1), f"[{b['onset'][0]}, {b['onset'][1]}] m",
                                              inband(on, *b["onset"]), True)
                else:
                    chk[f"P4 {est} onset"] = (None if on is None else round(on, 1), "no band (a dsn repeat never diverged)", None, False)

        # ── DIAGNOSTICS (never gate) ──
        lat = it[t]["flow_to_ekf3"]
        dl = [it_dsn[f"dsn_{w}_r{r}"]["flow_to_ekf3"] for r in (1, 2, 3)]
        lim_med = st.mean(x["lat_median_ms"] for x in dl) + 12.5
        lim_p95 = st.mean(x["lat_p95_ms"] for x in dl) + 12.5
        lim_match = min(x["matched_pct"] for x in dl) - 5
        chk["P2 latency median"] = (round(lat["lat_median_ms"], 1), f"≤ {lim_med:.1f} ms", lat["lat_median_ms"] <= lim_med, False)
        chk["P2 latency p95"] = (round(lat["lat_p95_ms"], 1), f"≤ {lim_p95:.1f} ms", lat["lat_p95_ms"] <= lim_p95, False)
        chk["P2 matched"] = (round(lat["matched_pct"], 1), f"≥ {lim_match:.1f}%", lat["matched_pct"] >= lim_match, False)
        m = re.search(r"Cruise complete - ([\d.]+)s sim time elapsed \(([\d.]+)s wall-clock\)",
                      open(f"{TRIALS_DIR}/{t}/logs/fly_trial.log").read())
        chk["diag RTF (cruise)"] = (round(float(m[1]) / float(m[2]), 3), "report", None, False)
        bm = yaml.safe_load(open(f"{TRIALS_DIR}/{t}/bag/metadata.yaml"))["rosbag2_bagfile_information"]
        dur = bm["duration"]["nanoseconds"] / 1e9
        rates = {x["topic_metadata"]["name"]: x["message_count"] / dur for x in bm["topics_with_message_count"]}
        chk["diag forward image rate"] = (round(rates.get("/forward_camera/image", 0), 2), "30.30 Hz expected", None, False)
        chk["diag /imu/time_ref rate"] = (round(rates.get("/imu/time_ref", 0), 2), "present, ≈ IMU rate", None, False)
        if "UKF" in e:
            chk["diag UKF evo -a (cruise)"] = (round(e["UKF"]["ate_a_cruise"]["+0.00"], 3), "report", None, False)
        else:
            chk["diag UKF"] = ("—", "NOT EVALUATED (pending ruling)", None, False)
        if w != "tex":
            if "UKF" in e:
                fl = e["UKF"]["failure"]
                chk["diag UKF ratio / onset"] = (f"{fl['disp_ratio']:.3f} / {fl['onset_gt_dist'] and round(fl['onset_gt_dist'], 1)}", "report", None, False)
            for est in [x for x in ("EKF3", "FGO") if x in e]:
                chk[f"diag {est} evo -a (cruise)"] = (round(e[est]["ate_a_cruise"]["+0.00"], 3), "report", None, False)

        fails = [k for k, (_, _, ok, prim) in chk.items() if prim and ok is False]
        any_primary_fail |= bool(fails)
        any_pending |= bool(pending)
        verdict = "FAIL" if fails else ("INCOMPLETE" if pending else "PASS")
        out[t] = {"primary": verdict, "primary_fails": fails, "not_evaluated": pending,
                  "checks": {k: {"value": v, "band": b, "pass": ok, "primary": p} for k, (v, b, ok, p) in chk.items()}}

        extra = (": " + ", ".join(fails)) if fails else (f" (not evaluated: {', '.join(pending)})" if pending else "")
        print(f"\n=== {t}: PRIMARY {verdict}{extra}")
        for k, (v, b, ok, p) in chk.items():
            if p:
                tag = "NOT EVALUATED" if ok is None else ("pass" if ok else "FAIL")
            else:
                tag = "diag" if ok is None else ("diag ok" if ok else "diag EXCEEDS")
            print(f"  {k:32} {str(v):>14}  {b:24} {tag}")

    overall = "MISS(ES)" if any_primary_fail else ("INCOMPLETE" if any_pending else "ALL PASS")
    print(f"\nPrimary criteria ({len(trials)} trials): {overall}")
    if a.json:
        json.dump({"overall": overall, "trials": out}, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
