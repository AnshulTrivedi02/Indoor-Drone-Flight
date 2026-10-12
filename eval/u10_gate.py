#!/usr/bin/env python3
"""U10: the Replay gate on rung-1 logs (docs/u10_replay_gate_band.md, FOR FINAL SIGN-OFF 2026-10-12). Criteria G1-G6
per flight and the set rule, EXACTLY as that document's §4 defines them; nothing here may differ from it.

NOT eval/replay_gate.py: that tool is the rung-1 §5 EKF3 Replay-fidelity check (XKF1@0 vs XKF1@100). U10 reports its
result per flight; it is not a U10 criterion.

  # one flight (all inputs are the outputs of ONE Replay run of that flight, and the rung-1 score of that run):
  python3 eval/u10_gate.py flight --replay-dir DIR --score SCORE.json --d-max M [--g6-bands E1MAX E1RMS E3 E5]
                                  [--name FLIGHT] [--json OUT]
      DIR: the Replay run directory: ukf_shadow.csv, ukf_geometry.csv, ukf_stats.csv, replay.log, logs/<one>.BIN
      SCORE.json: eval/real_score.py's output for the same Replay output log (labels EKF3 = XKF1@100, UKF = XUKO);
                  omitted ONLY for the hand-carried log H (plumbing: G1 and G3, verdict "PLUMBING PASS/FAIL")
  # the set (every usable result flight):
  python3 eval/u10_gate.py set FLIGHT1.json FLIGHT2.json ... [--json OUT]

Data sources (record / file names exact):
  G1 ukf_geometry.csv (mode, resolved_at_ms, the source labels, warning_late_parm rows); ukf_shadow.csv first row (the
     UKF's first initialised state); the Replay output log's ARM records (first ArmState = 1).
  G2 ukf_shadow.csv columns SS (bit 3 = horiz_pos_rel), Healthy, FlowAgeMs, over W = SCORE.json window_s.
  G3 ukf_stats.csv row n_chol_fail (and n_chol_retry, reported). A missing file or a missing row FAILS G3 (U10 rule 1).
  G4 SCORE.json estimators.UKF.evo_ape_a_se3.rmse_m (record XUKO, read from message RUKO) and
     estimators.EKF3.evo_ape_a_se3.rmse_m (record XKF1@100).
  G5 SCORE.json estimators.UKF.drift_start_aligned.final_h_m.
  G6 the Replay output log: RUKF/RUKS (replayed) against XUKF/XUKS (onboard, copied through from a fork-flown input).
     Applies only when the log holds onboard XUKF records.
"""
import argparse, csv, glob, hashlib, json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from df_reader import read_records

MIN_FLIGHTS = 4                          # set rule: fewer usable result flights -> NOT EVALUABLE
G2_SS_BIT = 3                            # nav_filter_status bit 3 = horiz_pos_rel (AP_Nav_Common.h)
G2_FLOW_AGE_MS = 5000                    # AID_TIMEOUT_MS: a 5 s aiding gap commands LAND in closed loop
G4_FACTOR, G4_FLOOR_M = 2.0, 0.10        # UKF <= max(2.0 * EKF3_R, EKF3_R + 0.10 m)
G6_DEFAULT = (0.05, 0.01, 0.05, 0.001)   # E1 3-D max m, E1 rms m, E3 yaw max deg, E5 rel increment; [TBD-V] once on H/V
G6_START_AFTER_INIT_S = 10.0             # pairing from the LATER of the two initialisations + 10 s
LEVER_PARAM_PREFIXES = ("FLOW_POS_", "INS_POS")     # lever arms: per sample from the sensor records, not from PARM


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read_geometry(path):
    rows = [r for r in csv.reader(open(path)) if r]
    g = {"rows": rows, "late": [], "mode": None, "resolved_at_ms": None, "sources": {}, "values": {}}
    for r in rows:
        k = r[0]
        if k == "mode":
            g["mode"] = r[1]
        elif k == "resolved_at_ms":
            g["resolved_at_ms"] = int(r[1])
        elif k == "flow_delay_ms":
            g["values"]["EK3_FLOW_DELAY"] = float(r[1]); g["sources"]["EK3_FLOW_DELAY"] = r[2]
        elif k == "horizon_ms":           # horizon_ms,H,hgt_delay,V,SRC,bcn_delay,V,SRC
            g["values"]["EK3_HGT_DELAY"] = float(r[3]); g["sources"]["EK3_HGT_DELAY"] = r[4]
            g["values"]["EK3_BCN_DELAY"] = float(r[6]); g["sources"]["EK3_BCN_DELAY"] = r[7]
        elif k == "rng1_min_max":
            g["values"]["RNGFND1_MIN"] = float(r[1]); g["values"]["RNGFND1_MAX"] = float(r[2])
            g["sources"]["RNGFND1_MIN_MAX"] = r[3]
        elif k == "warning_late_parm":
            g["late"].append({"ms": int(r[1]), "name": r[2], "value": float(r[3])})
    return g


def g1(geom_path, shadow, arm_us):
    out = {"geometry_file": geom_path}
    if not os.path.exists(geom_path):
        return {**out, "pass": False, "why": "ukf_geometry.csv missing"}
    g = read_geometry(geom_path)
    out.update({"mode": g["mode"], "resolved_at_ms": g["resolved_at_ms"], "sources": g["sources"]})
    why = []
    if g["mode"] != "log":
        why.append(f"mode {g['mode']!r}, not 'log'")
    if g["resolved_at_ms"] is None:
        why.append("geometry never resolved")
    need = ("EK3_FLOW_DELAY", "EK3_HGT_DELAY", "EK3_BCN_DELAY", "RNGFND1_MIN_MAX")
    bad = {k: g["sources"].get(k) for k in need if g["sources"].get(k) != "log_parm"}
    if bad:
        why.append(f"geometry sources not log_parm: {bad}")
    late = []
    for w in g["late"]:
        n = w["name"]
        if n in g["values"]:
            ok = abs(w["value"] - g["values"][n]) <= 1e-6 * max(1.0, abs(g["values"][n]))
            late.append({**w, "used_value": g["values"][n], "changes_a_value": not ok})
        elif n.startswith(LEVER_PARAM_PREFIXES) or (n.startswith("RNGFND") and "_POS_" in n):
            late.append({**w, "changes_a_value": False, "note": "lever arm: per sample from the sensor records"})
        else:                              # e.g. RNGFND2..9 MIN/MAX: not in the report; cannot be shown unchanged
            late.append({**w, "changes_a_value": None, "note": "not shown to leave a used value unchanged"})
    out["late_parm"] = late
    if any(x["changes_a_value"] is not False for x in late):
        why.append("a late-PARM warning that changes (or is not shown not to change) a value")
    t_init = int(shadow["TimeUS"][0]) if shadow is not None and len(shadow["TimeUS"]) else None
    out["ukf_first_row_us"] = t_init; out["first_arm_us"] = arm_us
    if t_init is None:
        why.append("the UKF never initialised (no ukf_shadow.csv row)")
    elif arm_us is None:
        out["init_before_arming"] = "not applicable: no ARM record (disarmed log)"
    else:
        out["init_before_arming"] = bool(t_init < arm_us and g["resolved_at_ms"] is not None
                                         and g["resolved_at_ms"] * 1000 < arm_us)
        if not out["init_before_arming"]:
            why.append("the UKF initialised (or resolved its geometry) after the first arming")
    out["pass"] = not why; out["why"] = why
    return out


def read_shadow(path):
    if not os.path.exists(path):
        return None
    a = np.genfromtxt(path, delimiter=",", names=True)
    return {k: np.atleast_1d(a[k]) for k in a.dtype.names}


def g2(sh, w, max_gap_s):
    if sh is None:
        return {"pass": False, "why": ["ukf_shadow.csv missing"]}
    t = sh["TimeUS"] / 1e6; m = (t >= w[0]) & (t <= w[1])
    n = int(m.sum())
    if n == 0:
        return {"pass": False, "n_rows_in_W": 0, "why": ["no ukf_shadow.csv row in W"]}
    tw = t[m]; edges = np.r_[w[0], tw, w[1]]; gap = float(np.diff(edges).max())
    ss = sh["SS"][m].astype(np.int64)
    bad_ss = int(np.sum(((ss >> G2_SS_BIT) & 1) == 0)); bad_h = int(np.sum(sh["Healthy"][m] != 1))
    age = sh["FlowAgeMs"][m]; bad_age = int(np.sum(age >= G2_FLOW_AGE_MS))
    why = []
    if bad_ss: why.append(f"SS bit {G2_SS_BIT} clear on {bad_ss} rows")
    if bad_h: why.append(f"Healthy != 1 on {bad_h} rows")
    if bad_age: why.append(f"FlowAgeMs >= {G2_FLOW_AGE_MS} on {bad_age} rows")
    if gap > max_gap_s: why.append(f"rows do not cover W: longest gap {gap:.3f} s > {max_gap_s} s")
    return {"pass": not why, "why": why, "W_s": list(w), "n_rows_in_W": n, "rows_without_horiz_pos_rel": bad_ss,
            "rows_unhealthy": bad_h, "rows_flow_age_ge_5000ms": bad_age, "flow_age_max_ms": float(age.max()),
            "longest_gap_incl_W_edges_s": gap, "max_gap_s": max_gap_s}


def g3(stats_path, replay_log):
    out = {"stats_file": stats_path}
    if not os.path.exists(stats_path):
        return {**out, "pass": False, "why": ["ukf_stats.csv missing: the Replay run did not end normally (U10 rule 1)"]}
    v = {r["name"]: r["value"] for r in csv.DictReader(open(stats_path))}
    if "n_chol_fail" not in v:
        return {**out, "pass": False, "why": ["ukf_stats.csv has no n_chol_fail row"]}
    out["n_chol_fail"] = int(v["n_chol_fail"]); out["n_chol_retry"] = int(v["n_chol_retry"]) if "n_chol_retry" in v else None
    if replay_log and os.path.exists(replay_log):
        out["replay_log_end_of_run"] = next((l.strip() for l in open(replay_log, errors="replace")
                                             if "end of run: n_chol_retry" in l), None)
    out["pass"] = out["n_chol_fail"] == 0
    out["why"] = [] if out["pass"] else [f"n_chol_fail = {out['n_chol_fail']}"]
    return out


def score_rows(score, bin_sha):
    e = score["estimators"]; why = []
    for lab, rec, phys in (("UKF", "XUKO", "RUKO"), ("EKF3", "XKF1@100", "XKF1")):
        if lab not in e:
            why.append(f"score has no {lab} row")
        elif e[lab]["record"] != rec or e[lab].get("physical_record") != phys:
            why.append(f"score {lab} is {e[lab]['record']}/{e[lab].get('physical_record')}, not {rec}/{phys}")
        elif e[lab]["sha256"] != bin_sha:
            why.append(f"score {lab} was computed on a different log (sha256)")
    return why


def g4(score):
    u = score["estimators"]["UKF"]["evo_ape_a_se3"]["rmse_m"]; k = score["estimators"]["EKF3"]["evo_ape_a_se3"]["rmse_m"]
    band = max(G4_FACTOR * k, k + G4_FLOOR_M)
    return {"pass": bool(u <= band), "ukf_evo_a_m": u, "ekf3_r_evo_a_m": k, "band_m": band,
            "why": [] if u <= band else [f"UKF {u:.4f} m > band {band:.4f} m"]}


def g5(score, d_max):
    d = score["estimators"]["UKF"].get("drift_start_aligned") or {}
    if "final_h_m" not in d:
        return {"pass": False, "d_max_m": d_max, "why": [f"drift not computable ({d.get('error', 'missing')}): G5 FAILS"]}
    f = d["final_h_m"]
    return {"pass": bool(f <= d_max), "final_h_m": f, "d_max_m": d_max, "segment_fc_s": d.get("segment_fc_s"),
            "why": [] if f <= d_max else [f"start-aligned horizontal drift {f:.3f} m > D_max {d_max} m"]}


def g6(recs, bands):
    xf, rf, xs, rs = recs["XUKF"], recs["RUKF"], recs["XUKS"], recs["RUKS"]
    if not xf:
        return {"applies": False, "pass": True, "why": [], "note": "no onboard XUKF: stock-flown, G6 does not apply"}
    if not rf:
        return {"applies": True, "pass": False, "why": ["no replayed RUKF in the Replay output"]}
    tx = np.array([r["TimeUS"] for r in xf], np.int64); tr = np.array([r["TimeUS"] for r in rf], np.int64)
    t0 = max(tx[0], tr[0]) + int(G6_START_AFTER_INIT_S * 1e6)
    common, i, j = np.intersect1d(tr, tx, return_indices=True)
    k = common >= t0; common, i, j = common[k], i[k], j[k]
    if len(common) < 2:
        return {"applies": True, "pass": False, "why": ["fewer than 2 exact-TimeUS pairs after the pairing start"]}
    g = lambda rs_, key, ix: np.array([rs_[q][key] for q in ix], float)
    d3 = np.linalg.norm(np.stack([g(rf, c, i) - g(xf, c, j) for c in ("PN", "PE", "PD")], 1), axis=1)
    dy = np.abs((g(rf, "Yaw", i) - g(xf, "Yaw", j) + 180.0) % 360.0 - 180.0)
    a, b = int(common[0]), int(common[-1])

    def inc(series, key):
        t = np.array([r["TimeUS"] for r in series]); p = np.searchsorted(t, a, "right") - 1; q = np.searchsorted(t, b, "right") - 1
        if p < 0:
            return None
        return float(series[q][key] - series[p][key])
    e5 = {}
    for key in ("FXa", "FYa", "Ra"):
        f, r = inc(xs, key), inc(rs, key)
        e5[key] = {"flying": f, "replay": r,
                   "rel_diff": None if f is None or r is None else abs(f - r) / max(f, 1.0)}
    e1max, e1rms, e3, e5b = bands
    res = {"applies": True, "pairing_start_us": int(t0), "paired": int(len(common)), "paired_span_us": [a, b],
           "E1_pos3d_max_m": float(d3.max()), "E1_pos3d_rms_m": float(np.sqrt(np.mean(d3 ** 2))),
           "E3_yaw_max_deg": float(dy.max()), "E5_increments": e5,
           "bands": {"E1_max_m": e1max, "E1_rms_m": e1rms, "E3_deg": e3, "E5_rel": e5b}}
    why = []
    if res["E1_pos3d_max_m"] > e1max or res["E1_pos3d_rms_m"] > e1rms: why.append("E1 outside its band")
    if res["E3_yaw_max_deg"] > e3: why.append("E3 outside its band")
    if any(v["rel_diff"] is None or v["rel_diff"] > e5b for v in e5.values()): why.append("E5 outside its band")
    res["pass"] = not why; res["why"] = why
    return res


def flight(a):
    d = a.replay_dir
    bins = sorted(glob.glob(os.path.join(d, "logs", "*.BIN")))
    if len(bins) != 1:
        raise SystemExit(f"{d}/logs: expected exactly one Replay output .BIN, found {len(bins)}")
    binp = bins[0]; bsha = sha256(binp)
    recs, info = read_records(binp, ["ARM", "XUKF", "RUKF", "XUKS", "RUKS"])
    integrity = {k: info[k] for k in ("undeclared_types", "skipped_bytes", "bad_fmt", "redeclared_ids")}
    score = json.load(open(a.score)) if a.score else None
    sh = read_shadow(os.path.join(d, "ukf_shadow.csv"))
    arm = next((int(r["TimeUS"]) for r in recs["ARM"] if r["ArmState"] == 1), None)
    out = {"flight": a.name or os.path.basename(os.path.normpath(d)), "replay_dir": os.path.abspath(d),
           "replay_bin": binp, "replay_bin_sha256": bsha, "score": os.path.abspath(a.score) if a.score else None,
           "score_sha256": sha256(a.score) if a.score else None,
           "replay_binary_md5": open(os.path.join(d, "binary.md5")).read().split()[0] if os.path.exists(os.path.join(d, "binary.md5")) else None,
           "log_integrity": integrity}
    pre_why = score_rows(score, bsha) if score else []
    if integrity["redeclared_ids"] or integrity["undeclared_types"] or integrity["bad_fmt"]:
        pre_why.append("Replay output log integrity (undeclared types, bad FMT or re-declared type ids)")
    out["preconditions"] = {"pass": not pre_why, "why": pre_why}
    out["G1"] = g1(os.path.join(d, "ukf_geometry.csv"), sh, arm)
    if score is None:                     # the hand-carried log H: plumbing only, G1 and G3 (no window, no mocap score)
        out["mode"] = "plumbing (H log): G1 and G3 only"
        out["G3"] = g3(os.path.join(d, "ukf_stats.csv"), os.path.join(d, "replay.log"))
        out["pass"] = bool(out["preconditions"]["pass"] and out["G1"]["pass"] and out["G3"]["pass"])
        out["verdict"] = ("PLUMBING PASS" if out["pass"] else "PLUMBING FAIL: " + ", ".join(
            g for g in ("preconditions", "G1", "G3") if not out[g]["pass"]))
        return out
    out["mode"] = "gated flight"
    w = score["window_s"]; max_gap = float(score["prereg"]["resolved"]["metrics"]["max_gap_s"])
    out["G2"] = g2(sh, w, max_gap)
    out["G3"] = g3(os.path.join(d, "ukf_stats.csv"), os.path.join(d, "replay.log"))
    out["G4"] = g4(score) if not pre_why else {"pass": False, "why": ["preconditions failed"]}
    out["G5"] = g5(score, a.d_max) if not pre_why else {"pass": False, "why": ["preconditions failed"]}
    out["G6"] = g6(recs, tuple(a.g6_bands))
    out["pass"] = bool(out["preconditions"]["pass"] and all(out[g]["pass"] for g in ("G1", "G2", "G3", "G4", "G5", "G6")))
    out["verdict"] = "PASS" if out["pass"] else "FAIL: " + ", ".join(
        g for g in ("preconditions", "G1", "G2", "G3", "G4", "G5", "G6") if not out[g]["pass"])
    return out


def gate_set(paths):
    fl = [json.load(open(p)) for p in paths]
    if any(f.get("mode") != "gated flight" for f in fl):
        raise SystemExit("the set takes gated result flights only (a plumbing H record was given)")
    names = [f["flight"] for f in fl]
    if len(set(names)) != len(names):
        raise SystemExit(f"duplicate flights: {names}")
    md5 = sorted({f.get("replay_binary_md5") for f in fl})
    out = {"flights": {f["flight"]: f["verdict"] for f in fl}, "n_usable": len(fl), "min_flights": MIN_FLIGHTS,
           "replay_binary_md5s": md5}
    if len(md5) != 1:
        out["verdict"] = "INVALID: the flights were replayed with different binaries"
    elif len(fl) < MIN_FLIGHTS:
        out["verdict"] = f"NOT EVALUABLE: {len(fl)} usable flights < {MIN_FLIGHTS}"
    else:
        out["verdict"] = "PASS" if all(f["pass"] for f in fl) else "FAIL"
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0]); sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("flight"); f.add_argument("--replay-dir", required=True); f.add_argument("--score", help="real_score.py output; omit ONLY for the H log (plumbing: G1, G3)")
    f.add_argument("--d-max", type=float, required=True, help="G5 bound in metres ([TBD-S]; no default)")
    f.add_argument("--g6-bands", type=float, nargs=4, default=list(G6_DEFAULT), metavar=("E1MAX", "E1RMS", "E3", "E5"))
    f.add_argument("--name"); f.add_argument("--json")
    s = sub.add_parser("set"); s.add_argument("flights", nargs="+"); s.add_argument("--json")
    a = ap.parse_args(argv)
    out = flight(a) if a.cmd == "flight" else gate_set(a.flights)
    print(json.dumps(out, indent=1, default=str))
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1, default=str)
    return out


if __name__ == "__main__":
    main()
