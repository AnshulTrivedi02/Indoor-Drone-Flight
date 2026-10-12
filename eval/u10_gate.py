#!/usr/bin/env python3
"""U10: the Replay gate on rung-1 logs (docs/u10_replay_gate_band.md, SIGNED OFF by the user 2026-10-12, including
N1-N6, D_max = 1.0 m). Criteria G1-G6 per flight and the set rule, EXACTLY as that document's §4 / §4.1 define them;
nothing here may differ from it. A mismatch is fixed HERE, never in the document (a document change is a dated
amendment, §10).

NOT eval/replay_gate.py: that tool is the rung-1 §5 EKF3 Replay-fidelity check (XKF1@0 vs XKF1@100). U10 reports its
result per flight; it is not a U10 criterion.

  # one flight (all inputs are the outputs of ONE Replay run of that flight, and the rung-1 score of that run):
  python3 eval/u10_gate.py flight --replay-dir DIR --score SCORE.json [--d-max 1.0] [--g6-bands E1MAX E1RMS E3 E5]
                                  [--verification] [--name FLIGHT] [--json OUT]
      DIR: the Replay run directory: ukf_shadow.csv, ukf_geometry.csv, ukf_stats.csv, replay.log, binary.md5,
           logs/<one>.BIN
      SCORE.json: eval/real_score.py's output for the same Replay output log (labels EKF3 = XKF1@100, UKF = XUKO);
                  omitted ONLY for the hand-carried log H (§2 item 1, plumbing: G1 and G3, "PLUMBING PASS/FAIL").
      --verification: the first-hover log(s) V (§7 step 2): G1-G3 judged; G4-G6 computed and REPORTED, not judged
                  (V confirms the [TBD-V] G6 bands once); verdict "VERIFICATION PASS/FAIL". Never a set member.
      --d-max: SIGNED at 1.0 m (§4 G5). It is the default; any other value is refused (a changed band is a dated
                  amendment, §1/§10, not a command-line choice).
  # the set (every usable result flight, gated mode only):
  python3 eval/u10_gate.py set FLIGHT1.json FLIGHT2.json ... [--json OUT]

One function per criterion (traceability: docs/handovers/2026-10-12_u10_g5_audit_rebase.md; tests:
eval/u10_gate_test.py, a pass and a fail case for every row):
  preconditions()  §4.1 preconditions = N5 (each score on its own Replay log; UKF = XUKO/RUKO, EKF3 = XKF1@100/XKF1)
                   and the log integrity (0 undeclared types, 0 bad FMT, 0 re-declared ids; rule 2's RUK* names)
  g1()             G1, with N3 (g1_late_parm(), g1_before_arming())
  g2()             G2, with N2 (g2_coverage())
  g3()             G3, with U10 rule 1 (a missing ukf_stats.csv or n_chol_fail row FAILS)
  g4()             G4 (not computable = not passed)
  g5()             G5, with N1 (not computable = FAIL) and D_max = 1.0 m
  g6()             G6, with N6 (E1 = 3-D) and rule 2 (RUKF/RUKS replayed vs XUKF/XUKS onboard in ONE log)
  gate_set()       the set rule: set_single_binary() (N4), set_distinct_logs() (each score on its own Replay log),
                   set_same_bands(), set_min_flights() (>= 4 usable), every flight PASS

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
import argparse, csv, glob, hashlib, json, math, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from df_reader import read_records

MIN_FLIGHTS = 4                          # set rule: fewer usable result flights -> NOT EVALUABLE
G2_SS_BIT = 3                            # nav_filter_status bit 3 = horiz_pos_rel (AP_Nav_Common.h)
G2_FLOW_AGE_MS = 5000                    # AID_TIMEOUT_MS: a 5 s aiding gap commands LAND in closed loop
G4_FACTOR, G4_FLOOR_M = 2.0, 0.10        # UKF <= max(2.0 * EKF3_R, EKF3_R + 0.10 m)
D_MAX_M = 1.0                            # G5 bound: SIGNED 2026-10-12 (half the 2 m clearance at every hold point)
G6_DEFAULT = (0.05, 0.01, 0.05, 0.001)   # E1 3-D max m, E1 rms m, E3 yaw max deg, E5 rel increment; [TBD-V] once on H/V
G6_START_AFTER_INIT_S = 10.0             # pairing from the LATER of the two initialisations + 10 s
LEVER_PARAM_PREFIXES = ("FLOW_POS_", "INS_POS")     # lever arms: per sample from the sensor records, not from PARM
RESOLVED_SOURCES = ("EK3_FLOW_DELAY", "EK3_HGT_DELAY", "EK3_BCN_DELAY", "RNGFND1_MIN_MAX")   # must be log_parm
REQUIRED_ROWS = (("UKF", "XUKO", "RUKO"), ("EKF3", "XKF1@100", "XKF1"))   # label, record, physical message (rule 2)
SHADOW_COLS = ("TimeUS", "SS", "Healthy", "FlowAgeMs")
MODE_GATED, MODE_VERIFY, MODE_PLUMB = "gated flight", "verification (V log): G1-G3 judged, G4-G6 reported", \
    "plumbing (H log): G1 and G3 only"


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _finite(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


# ---------------------------------------------------------------------------------------------- preconditions (N5)
def preconditions(score, bin_sha, integrity):
    """§4.1 preconditions. N5: the score was computed on THIS Replay output (`estimators.*.sha256` = the .BIN's sha256,
    for every row read from the log, i.e. every row with a physical_record; a TUM row such as FGO carries its own file's
    sha256 and is not a log row), with UKF = XUKO / message RUKO (rule 2) and EKF3 = XKF1@100 / XKF1. The log has 0
    undeclared types, 0 bad FMT and 0 re-declared type ids. score None = the H log (integrity only)."""
    why = []
    if score is not None:
        e = score.get("estimators")
        if not isinstance(e, dict):
            why.append("score has no estimators table")
            e = {}
        for lab, rec, phys in REQUIRED_ROWS:
            r = e.get(lab)
            if not isinstance(r, dict):
                why.append(f"score has no {lab} row")
            elif r.get("record") != rec or r.get("physical_record") != phys:
                why.append(f"score {lab} is {r.get('record')}/{r.get('physical_record')}, not {rec}/{phys}")
            elif r.get("sha256") != bin_sha:
                why.append(f"score {lab} was computed on a different log (sha256)")
        for lab, r in e.items():
            if isinstance(r, dict) and "physical_record" in r and lab not in {x[0] for x in REQUIRED_ROWS} \
                    and r.get("sha256") != bin_sha:
                why.append(f"score row {lab} (read from a log) was computed on a different log (sha256)")
    bad = {k: integrity.get(k) for k in ("undeclared_types", "bad_fmt", "redeclared_ids") if integrity.get(k)}
    if bad:
        why.append(f"Replay output log integrity: {sorted(bad)} not empty")
    return {"pass": not why, "why": why, "integrity_judged": ["undeclared_types", "bad_fmt", "redeclared_ids"],
            "skipped_bytes_reported": integrity.get("skipped_bytes")}


# ---------------------------------------------------------------------------------------------- G1 (with N3)
def read_geometry(path):
    rows = [r for r in csv.reader(open(path)) if r]
    g = {"rows": rows, "late": [], "mode": None, "resolved_at_ms": None, "sources": {}, "values": {}}
    for r in rows:
        k = r[0]
        try:
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
        except (IndexError, ValueError):
            g.setdefault("malformed", []).append(r)
    return g


def g1_late_parm(g):
    """N3: each warning_late_parm row 'does not change a value' only if it repeats the value in use of one of the five
    resolved parameters (tolerance 1e-6 * max(1, |value|)) or is a lever arm (FLOW_POS_*, INS_POS*, RNGFNDn_POS_*).
    Returns (listed rows, ok)."""
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
    return late, all(x["changes_a_value"] is False for x in late)


def g1_before_arming(t_init, resolved_at_ms, arm_us, need_arm):
    """§4.1 'before arming' + N3's missing-ARM rule. Returns (value for the output, reason or None)."""
    if t_init is None:
        return None, "the UKF never initialised (no ukf_shadow.csv row)"
    if arm_us is None and need_arm:
        return False, "no ARM record (ArmState = 1) in the Replay output of a gated flight"
    if arm_us is None:
        return "not applicable: no ARM record (H, disarmed log)", None
    ok = bool(t_init < arm_us and resolved_at_ms is not None and resolved_at_ms * 1000 < arm_us)
    return ok, None if ok else "the UKF initialised (or resolved its geometry) after the first arming"


def g1(geom_path, shadow, arm_us, need_arm):
    out = {"geometry_file": geom_path}
    if not os.path.exists(geom_path):
        return {**out, "pass": False, "why": ["ukf_geometry.csv missing"]}
    g = read_geometry(geom_path)
    out.update({"mode": g["mode"], "resolved_at_ms": g["resolved_at_ms"], "sources": g["sources"]})
    why = []
    if g.get("malformed"):
        why.append(f"malformed ukf_geometry.csv rows: {g['malformed']}")
    if g["mode"] != "log":
        why.append(f"mode {g['mode']!r}, not 'log'")
    if g["resolved_at_ms"] is None:
        why.append("geometry never resolved")
    bad = {k: g["sources"].get(k) for k in RESOLVED_SOURCES if g["sources"].get(k) != "log_parm"}
    if bad:
        why.append(f"geometry sources not log_parm: {bad}")
    out["late_parm"], late_ok = g1_late_parm(g)
    if not late_ok:
        why.append("a late-PARM warning that changes (or is not shown not to change) a value")
    t_init = int(shadow["TimeUS"][0]) if shadow is not None and len(shadow.get("TimeUS", ())) else None
    out["ukf_first_row_us"] = t_init; out["first_arm_us"] = arm_us
    out["init_before_arming"], r = g1_before_arming(t_init, g["resolved_at_ms"], arm_us, need_arm)
    if r:
        why.append(r)
    out["pass"] = not why; out["why"] = why
    return out


# ---------------------------------------------------------------------------------------------- G2 (with N2)
def read_shadow(path):
    """ukf_shadow.csv as {column: float array}; None if the file is missing. A header-only file gives empty arrays."""
    if not os.path.exists(path):
        return None
    with open(path) as f:
        rd = csv.DictReader(f)
        cols = rd.fieldnames or []
        rows = list(rd)
    out = {}
    for c in cols:
        try:
            out[c] = np.array([float(r[c]) for r in rows], float)
        except (TypeError, ValueError):
            out[c] = np.full(len(rows), np.nan)
    return out


def g2_coverage(tw, w, max_gap_s):
    """N2: the longest gap between consecutive rows in W, counting the gaps from W's start to the first row and from
    the last row to W's end, must be <= max_gap_s."""
    gap = float(np.diff(np.r_[w[0], tw, w[1]]).max())
    return gap, gap <= max_gap_s


def g2(sh, w, max_gap_s):
    if sh is None:
        return {"pass": False, "why": ["ukf_shadow.csv missing"]}
    miss = [c for c in SHADOW_COLS if c not in sh]
    if miss:
        return {"pass": False, "why": [f"ukf_shadow.csv lacks columns {miss}"]}
    t = sh["TimeUS"] / 1e6; m = (t >= w[0]) & (t <= w[1])
    n = int(m.sum())
    if n == 0:
        return {"pass": False, "n_rows_in_W": 0, "why": ["no ukf_shadow.csv row in W"]}
    gap, cov_ok = g2_coverage(t[m], w, max_gap_s)
    ssf = sh["SS"][m]
    bad_ss = int(np.sum(~np.isfinite(ssf))) + int(np.sum(((ssf[np.isfinite(ssf)].astype(np.int64) >> G2_SS_BIT) & 1) == 0))
    bad_h = int(np.sum(sh["Healthy"][m] != 1))
    age = sh["FlowAgeMs"][m]; bad_age = int(np.sum(~(age < G2_FLOW_AGE_MS)))   # NaN counts as bad
    why = []
    if bad_ss: why.append(f"SS bit {G2_SS_BIT} clear on {bad_ss} rows")
    if bad_h: why.append(f"Healthy != 1 on {bad_h} rows")
    if bad_age: why.append(f"FlowAgeMs >= {G2_FLOW_AGE_MS} on {bad_age} rows")
    if not cov_ok: why.append(f"rows do not cover W: longest gap {gap:.3f} s > {max_gap_s} s")
    return {"pass": not why, "why": why, "W_s": list(w), "n_rows_in_W": n, "rows_without_horiz_pos_rel": bad_ss,
            "rows_unhealthy": bad_h, "rows_flow_age_ge_5000ms": bad_age, "flow_age_max_ms": float(np.nanmax(age)),
            "longest_gap_incl_W_edges_s": gap, "max_gap_s": max_gap_s}


# ---------------------------------------------------------------------------------------------- G3 (rule 1)
def g3(stats_path, replay_log):
    out = {"stats_file": stats_path}
    if not os.path.exists(stats_path):
        return {**out, "pass": False, "why": ["ukf_stats.csv missing: the Replay run did not end normally (U10 rule 1)"]}
    try:
        v = {r["name"]: r["value"] for r in csv.DictReader(open(stats_path))}
    except (KeyError, csv.Error):
        v = {}
    if "n_chol_fail" not in v:
        return {**out, "pass": False, "why": ["ukf_stats.csv has no n_chol_fail row (U10 rule 1)"]}
    try:
        out["n_chol_fail"] = int(v["n_chol_fail"])
    except ValueError:
        return {**out, "pass": False, "why": [f"n_chol_fail is not an integer: {v['n_chol_fail']!r}"]}
    out["n_chol_retry"] = int(v["n_chol_retry"]) if v.get("n_chol_retry", "").strip().isdigit() else None
    if replay_log and os.path.exists(replay_log):
        out["replay_log_end_of_run"] = next((l.strip() for l in open(replay_log, errors="replace")
                                             if "end of run: n_chol_retry" in l), None)
    out["pass"] = out["n_chol_fail"] == 0
    out["why"] = [] if out["pass"] else [f"n_chol_fail = {out['n_chol_fail']}"]
    return out


# ---------------------------------------------------------------------------------------------- G4
def g4(score):
    """UKF (XUKO) evo -a <= max(2.0 x EKF3_R, EKF3_R + 0.10 m). A value that is missing or not finite cannot pass
    (§4.1 verdict: a flight passes only if every criterion passes)."""
    e = score.get("estimators", {})
    u = (e.get("UKF", {}).get("evo_ape_a_se3") or {}).get("rmse_m")
    k = (e.get("EKF3", {}).get("evo_ape_a_se3") or {}).get("rmse_m")
    if not (_finite(u) and _finite(k)):
        return {"pass": False, "ukf_evo_a_m": u, "ekf3_r_evo_a_m": k,
                "why": [f"G4 not computable (UKF {u!r}, EKF3_R {k!r}): not passed"]}
    band = max(G4_FACTOR * k, k + G4_FLOOR_M)
    return {"pass": bool(u <= band), "ukf_evo_a_m": u, "ekf3_r_evo_a_m": k, "band_m": band,
            "why": [] if u <= band else [f"UKF {u:.4f} m > band {band:.4f} m"]}


# ---------------------------------------------------------------------------------------------- G5 (N1, D_max)
def g5(score, d_max=D_MAX_M):
    """Start-aligned horizontal drift (rung-1 §4.3 rule, real_score.drift_start_aligned.final_h_m) <= D_max = 1.0 m.
    N1: not computable (the rung-1 rule refuses the segment, or the value is missing) = FAIL."""
    d = (score.get("estimators", {}).get("UKF", {}) or {}).get("drift_start_aligned") or {}
    f = d.get("final_h_m")
    if not _finite(f):
        return {"pass": False, "d_max_m": d_max, "not_computable": True,
                "rule_refusal": d.get("error", "missing"), "segment_fc_s": d.get("segment_fc_s"),
                "init_segment_extent_h_m": d.get("init_segment_extent_h_m"),
                "why": [f"drift not computable ({d.get('error', 'missing')}): G5 FAILS (N1)"]}
    return {"pass": bool(f <= d_max), "final_h_m": f, "d_max_m": d_max, "segment_fc_s": d.get("segment_fc_s"),
            "init_segment_extent_h_m": d.get("init_segment_extent_h_m"),
            "why": [] if f <= d_max else [f"start-aligned horizontal drift {f:.3f} m > D_max {d_max} m"]}


# ---------------------------------------------------------------------------------------------- G6 (N6, rule 2)
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
    d3 = np.linalg.norm(np.stack([g(rf, c, i) - g(xf, c, j) for c in ("PN", "PE", "PD")], 1), axis=1)   # N6: 3-D
    dy = np.abs((g(rf, "Yaw", i) - g(xf, "Yaw", j) + 180.0) % 360.0 - 180.0)
    a, b = int(common[0]), int(common[-1])

    def inc(series, key):
        if not series:
            return None
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


# ---------------------------------------------------------------------------------------------- one flight
def flight(a):
    if a.d_max != D_MAX_M:
        raise SystemExit(f"--d-max {a.d_max}: D_max is SIGNED at {D_MAX_M} m (docs/u10_replay_gate_band.md §4 G5); "
                         "a different value is a dated amendment (§10), never a command-line choice")
    if a.verification and not a.score:
        raise SystemExit("--verification (the V log) needs --score (G2 needs the window W)")
    d = a.replay_dir
    bins = sorted(glob.glob(os.path.join(d, "logs", "*.BIN")))
    if len(bins) != 1:
        raise SystemExit(f"{d}/logs: expected exactly one Replay output .BIN, found {len(bins)}")
    binp = bins[0]; bsha = sha256(binp)
    recs, info = read_records(binp, ["ARM", "XUKF", "RUKF", "XUKS", "RUKS"])
    integrity = {k: info[k] for k in ("undeclared_types", "skipped_bytes", "bad_fmt", "redeclared_ids")}
    score = json.load(open(a.score)) if a.score else None
    sh = read_shadow(os.path.join(d, "ukf_shadow.csv"))
    arm = next((int(r["TimeUS"]) for r in recs["ARM"] if r.get("ArmState") == 1), None)
    md5p = os.path.join(d, "binary.md5")
    md5 = open(md5p).read().split() if os.path.exists(md5p) else []
    out = {"flight": a.name or os.path.basename(os.path.normpath(d)), "replay_dir": os.path.abspath(d),
           "replay_bin": binp, "replay_bin_sha256": bsha, "score": os.path.abspath(a.score) if a.score else None,
           "score_sha256": sha256(a.score) if a.score else None, "replay_binary_md5": md5[0] if md5 else None,
           "d_max_m": a.d_max, "g6_bands": list(a.g6_bands), "log_integrity": integrity,
           "band_document": "docs/u10_replay_gate_band.md (SIGNED 2026-10-12)"}
    out["preconditions"] = pre = preconditions(score, bsha, integrity)
    out["G1"] = g1(os.path.join(d, "ukf_geometry.csv"), sh, arm, need_arm=score is not None)
    out["G3"] = g3(os.path.join(d, "ukf_stats.csv"), os.path.join(d, "replay.log"))
    if score is None:                     # the hand-carried log H: plumbing only, G1 and G3 (no window, no mocap score)
        out["mode"] = MODE_PLUMB
        judged = ("preconditions", "G1", "G3")
        out["pass"] = all(out[g]["pass"] for g in judged)
        out["verdict"] = "PLUMBING PASS" if out["pass"] else "PLUMBING FAIL: " + ", ".join(
            g for g in judged if not out[g]["pass"])
        return out
    w = score["window_s"]; max_gap = float(score["prereg"]["resolved"]["metrics"]["max_gap_s"])
    out["G2"] = g2(sh, w, max_gap)
    out["G4"] = g4(score) if pre["pass"] else {"pass": False, "why": ["preconditions failed"]}
    out["G5"] = g5(score, a.d_max) if pre["pass"] else {"pass": False, "why": ["preconditions failed"]}
    out["G6"] = g6(recs, tuple(a.g6_bands))
    if a.verification:                    # the V log: G1-G3 judged, G4-G6 reported only
        out["mode"] = MODE_VERIFY
        judged = ("preconditions", "G1", "G2", "G3")
        for gname in ("G4", "G5", "G6"):
            out[gname]["judged"] = False
        out["pass"] = all(out[g]["pass"] for g in judged)
        out["verdict"] = "VERIFICATION PASS" if out["pass"] else "VERIFICATION FAIL: " + ", ".join(
            g for g in judged if not out[g]["pass"])
        return out
    out["mode"] = MODE_GATED
    judged = ("preconditions", "G1", "G2", "G3", "G4", "G5", "G6")
    out["pass"] = all(out[g]["pass"] for g in judged)
    out["verdict"] = "PASS" if out["pass"] else "FAIL: " + ", ".join(g for g in judged if not out[g]["pass"])
    return out


# ---------------------------------------------------------------------------------------------- the set
def set_single_binary(fl):
    """N4: every flight carries a Replay md5 (binary.md5), and all are the same. Missing -> refused; mixed -> INVALID."""
    if any(not f.get("replay_binary_md5") for f in fl):
        raise SystemExit("a flight record has no replay_binary_md5 (binary.md5 missing in its Replay directory): the "
                         "single-binary rule cannot be checked")
    md5 = sorted({f["replay_binary_md5"] for f in fl})
    return md5, len(md5) == 1


def set_distinct_logs(fl):
    """Each score on its own Replay log: within a flight, N5 (the preconditions); across the set, no two flight records
    may share a name, a Replay output log (sha256) or a score file (sha256). Refused otherwise."""
    for key in ("flight", "replay_bin_sha256", "score_sha256"):
        v = [f.get(key) for f in fl]
        if any(x is None for x in v) or len(set(v)) != len(v):
            raise SystemExit(f"duplicate or missing {key} across the set: {v}")


def set_same_bands(fl):
    """Every flight gated with the signed D_max and with ONE set of G6 bands (confirmed once, [TBD-V]). Refused otherwise."""
    dm = {f.get("d_max_m") for f in fl}
    if dm != {D_MAX_M}:
        raise SystemExit(f"flights gated with D_max {sorted(map(str, dm))}, not the signed {D_MAX_M} m")
    gb = {tuple(f.get("g6_bands") or ()) for f in fl}
    if len(gb) != 1 or not next(iter(gb)):
        raise SystemExit(f"flights gated with different (or missing) G6 bands: {sorted(gb)}")


def set_min_flights(n):
    """>= 4 usable result flights, else NOT EVALUABLE."""
    return n >= MIN_FLIGHTS


def gate_set(paths):
    fl = [json.load(open(p)) for p in paths]
    if any(f.get("mode") != MODE_GATED for f in fl):
        raise SystemExit("the set takes gated result flights only (a plumbing H or verification V record was given)")
    set_distinct_logs(fl)
    md5, single = set_single_binary(fl)
    set_same_bands(fl)
    out = {"flights": {f["flight"]: f["verdict"] for f in fl}, "n_usable": len(fl), "min_flights": MIN_FLIGHTS,
           "replay_binary_md5s": md5, "d_max_m": D_MAX_M, "g6_bands": fl[0].get("g6_bands")}
    if not single:
        out["verdict"] = "INVALID: the flights were replayed with different binaries"
    elif not set_min_flights(len(fl)):
        out["verdict"] = f"NOT EVALUABLE: {len(fl)} usable flights < {MIN_FLIGHTS}"
    else:
        out["verdict"] = "PASS" if all(f.get("pass") is True for f in fl) else "FAIL"
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0]); sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("flight"); f.add_argument("--replay-dir", required=True)
    f.add_argument("--score", help="real_score.py output; omit ONLY for the H log (plumbing: G1, G3)")
    f.add_argument("--d-max", type=float, default=D_MAX_M,
                   help=f"G5 bound in metres: SIGNED at {D_MAX_M} (default); any other value is refused")
    f.add_argument("--g6-bands", type=float, nargs=4, default=list(G6_DEFAULT), metavar=("E1MAX", "E1RMS", "E3", "E5"))
    f.add_argument("--verification", action="store_true", help="the V log: G1-G3 judged, G4-G6 reported (§7 step 2)")
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
