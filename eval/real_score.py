#!/usr/bin/env python3
"""Rung-1 scorer (real-flight plan item R9): the three estimators, all on the FC clock, against mocap, on ONE window
that is defined BY RULE in a pre-registration file written before flying.

Inputs (TUM: t x y z qx qy qz qw; all on the FC clock; z UP, gravity-aligned; any origin and heading):
  --mocap   mocap truth on the FC clock: eval/mocap_align.py's `mocap_fc_clock_est_frame.tum`.
  --est LABEL=PATH.tum           an estimator trajectory (e.g. the FGO from the dataflash converter), ENU.
  --est-bin LABEL=RECORD --bin LOG.bin
                                 an estimator read from a dataflash log (the Replay output): XKF1@100 (replayed core 0)
                                 or XKF1@0 (the flight's onboard core 0, also present in the Replay log) for EKF3,
                                 XUKO (the UKF's current-time output, the counterpart of XKF1) or XUKF (its fused state
                                 at the delayed horizon) for the UKF port, XFGO if present. NED -> ENU; written as TUM
                                 (identity quaternions) to --work-dir and scored from there; the record's Yaw is kept for
                                 the secondary metrics. Read with eval/df_reader.py, NOT pymavlink (2026-10-12: the
                                 fork's Replay of a stock-flown log writes the UKF records without FMT; pymavlink then
                                 exits or drops ~99.5% of the XKF1 records). Refused: XKF1@1xx whose TimeUS sequence
                                 differs from XKF1@(C-100)'s; a record with no FMT (XUKO in a stock-log Replay); a
                                 non-increasing XUKO/XUKF series (a fork-flown log: onboard and replayed interleaved).
                                 U10 rule 2 (2026-10-12): XUKO/XUKF mean the REPLAYED records and are read from the
                                 names the current Replay writes them under, RUKO/RUKF (port replay-rukx); the onboard
                                 records of a fork-flown log are XUKO@onboard/XUKF@onboard. The output JSON gives both
                                 the registered record and the physical message name read.
  --est-csv LABEL=PATH           the UKF port's current-time output as CSV with XUKO's exact columns (port spec 2026-10-12),
                                 only for a label registered as XUKO (its use instead of the log needs the user's ruling).
  --prereg  the pre-registration JSON. Its sha256 goes into the output. It is read STRICTLY (load_prereg): every key
            below is required, unknown keys are refused, and nothing is filled in from defaults, so the scored
            definitions are exactly the file's. Rung 1: docs/rung1_preregistration.json (signed off 2026-10-12).
  --mocap-align-json  mocap_align.py's JSON for this flight; required when the prereg has a `clock_map` section, whose
            rule it is checked against (default windows used, the same sync-wiggle thresholds).

PRE-REGISTRATION SCHEMA (2026-10-11; `secondary` added 2026-10-12):
  window             {"rule": "airborne" | "speed" | "fixed", + that rule's keys (below)}
  metrics            {"primary": "evo_ape_a_se3" | "ate_4dof", "t_max_diff_s": 0.05 (the only value: evo is called
                      exactly as three_way_eval), "max_gap_s", "max_mocap_interp_gap_s"}
  drift              {"segment_rule": "motion_onset_path" | "window_start_time", + that rule's keys (below)}
  estimator_records  {LABEL: "XKF1@<core>" | "XUKO" | "XUKF" | "XFGO" | "TUM"}: every scored label must be listed,
                      and a --est-bin LABEL=RECORD must name exactly this record (a TUM input needs "TUM"). XKF1 needs
                      its core: a Replay output log holds the onboard (C = 0) AND the replayed (C = 100) records.
  clock_map          optional {"rule": "disarmed_wiggles", "w_thr_rad_s", "pad_s", "merge_s", "min_burst_s"}
  secondary          REQUIRED {"heading_drift": {"window": "W", "sense": "NED", "wrap_limit_deg"},
                               "cross_track_drift": {"window": "W", "normal": "right_of_mocap_velocity", "min_speed_mps",
                                                     "smooth_s", "anchor": "takeoff_yaw", "anchor_avg_s"}}
  name, status, notes, rationale   free text (kept in the output)

WINDOW (computed from mocap ONLY, applied identically to every estimator):
  rule "airborne" (rung-1 default): height h = z - ground level (the `ground_percentile` percentile of mocap z over
      the WHOLE record: the vehicle rests at both ends, while the record may START with it held up for the sync
      wiggle); airborne = h > `airborne_height_m`; the LONGEST airborne run of at least `hold_s` is the flight;
      window = [take-off + `start_after_takeoff_s`, landing - `end_before_landing_s`]; refused if shorter than
      `min_duration_s`.
  rule "speed": three_way_eval's pinned cruise rule (largest run of smoothed horizontal speed > `speed_mps`).
  rule "fixed": `t0_s`, `t1_s` given (regression tests only; never for results).

METRICS per estimator, on the window (estimator samples inside it; mocap interpolated at their stamps, but ONLY where
the two bracketing mocap samples are <= `max_mocap_interp_gap_s` apart: across a mocap dropout the truth would be
invented, so those estimator samples are dropped from the in-house metrics and counted; evo is given the full set):
  evo_ape_a_se3        evo_ape -a (Umeyama SE(3), no scale), RMSE, t_max_diff from the prereg; the SAME call as
                       three_way_eval (the simulation's STANDING metric, "evo -a (cruise)").
  ate_4dof             yaw + translation fit over the window (both frames gravity-aligned), RMSE 3-D / horizontal /
                       vertical. The plan's "evo -a (4-DoF)": evo has no yaw-only alignment, so it is computed here.
  drift_start_aligned  4-DoF fit on an INITIAL SEGMENT ONLY, then the error over the whole window: RMSE, max, final,
                       and final horizontal error / mocap path length (% of distance). The segment (prereg `drift`):
                         motion_onset_path (rung 1): from the motion onset (the first time in the window the mocap
                           horizontal speed, boxcar `onset_smooth_s`, stays above `onset_speed_mps` for `onset_hold_s`)
                           until the mocap has travelled `init_path_m` horizontally: on the first leg, never in the
                           hover (fixes the draft's defect 1: [t_to + 25 s, t_to + 30 s] was inside the hover);
                         window_start_time: the first `init_segment_s` of the window (regression/tests).
                       The yaw of that fit is only defined if the segment MOVES horizontally: the metric is refused
                       when the segment's horizontal extent (largest distance from its first point) is below
                       `min_extent_m`.
  coverage             samples, longest gap, fraction of the window within `max_gap_s` of a sample.
  heading_drift        (secondary, 2026-10-12) the corridor's heading-drift rule, deg/min NED sense, UNALIGNED (slope of
                       the wrapped yaw error over the window; heading_drift()).
  cross_track_drift    (secondary, 2026-10-12) lateral position-error growth per cruise minute, right of the mocap
                       direction of travel, one take-off heading anchor, no fit (cross_track()). Needs each source's
                       heading to be its body-x heading in the frame of its own positions (true of XKF1/XUKO and the FGO
                       TUM; for mocap it needs the rigid body's x axis along the vehicle's nose, else a COMMON-MODE bias of
                       anchor_sensitivity_m_per_min_per_deg per degree, reported).
  The pre-registration names the PRIMARY metric (output `primary`); all are reported and labelled.

Usage (~/venv-ardupilot; evo_ape is called from ~/venv-evo):
  python3 eval/real_score.py --prereg PREREG.json --mocap MOCAP.tum --bin REPLAY.bin --est-bin EKF3=XKF1 \\
      --est-bin UKF=XUKO --est FGO=fgo_fc.tum --work-dir DIR --out score.json
"""
import argparse, hashlib, json, math, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cruise_window import cruise_bounds
from three_way_eval import evo_ape_a, crop, write_tum, T_MAX_DIFF   # identical evo call, TUM format, t_max_diff

DEFAULT_PREREG = {      # a COMPLETE, valid pre-registration for the tests; main() never fills anything in from it
    "window": {"rule": "airborne", "ground_percentile": 5.0, "airborne_height_m": 0.30, "hold_s": 1.0,
               "start_after_takeoff_s": 25.0, "end_before_landing_s": 5.0, "min_duration_s": 20.0},
    "metrics": {"primary": "evo_ape_a_se3", "t_max_diff_s": 0.05, "max_gap_s": 0.5, "max_mocap_interp_gap_s": 0.05},
    "drift": {"segment_rule": "motion_onset_path", "onset_speed_mps": 0.15, "onset_smooth_s": 1.0, "onset_hold_s": 1.0,
              "init_path_m": 2.0, "min_extent_m": 1.0},
    "estimator_records": {"EKF3": "XKF1@100", "UKF": "XUKO", "FGO": "TUM"},
    "secondary": {"heading_drift": {"window": "W", "sense": "NED", "wrap_limit_deg": 170.0},
                  "cross_track_drift": {"window": "W", "normal": "right_of_mocap_velocity", "min_speed_mps": 0.15,
                                        "smooth_s": 1.0, "anchor": "takeoff_yaw", "anchor_avg_s": 1.0}},
}

WINDOW_KEYS = {"airborne": {"ground_percentile", "airborne_height_m", "hold_s", "start_after_takeoff_s",
                            "end_before_landing_s", "min_duration_s"},
               "speed": {"speed_mps"}, "fixed": {"t0_s", "t1_s"}}
DRIFT_KEYS = {"motion_onset_path": {"onset_speed_mps", "onset_smooth_s", "onset_hold_s", "init_path_m", "min_extent_m"},
              "window_start_time": {"init_segment_s", "min_extent_m"}}
METRIC_KEYS = {"primary", "t_max_diff_s", "max_gap_s", "max_mocap_interp_gap_s"}
PRIMARY = ("evo_ape_a_se3", "ate_4dof")
RECORDS = ("XKF1", "XUKO", "XUKF", "XFGO", "TUM")     # XKF1 MUST carry its core: "XKF1@<C>" (see parse_record)
UKF_RENAMED = {"XUKO": "RUKO", "XUKF": "RUKF"}      # replayed UKF record -> its name in a Replay output (U10 rule 2)
REPLAY_ID_WINDOW = (220, 230)                       # AP_Logger_config.h REPLAY_LOG_NEW_MSG_MIN/MAX: Replay's own ids


def parse_record(rec):
    """'XKF1@100' -> ('XKF1', 100); 'XUKO' -> ('XUKO', None); 'XUKO@onboard' -> ('XUKO', 'onboard'). XKF1 needs an
    explicit core: an ArduPilot Replay output log holds BOTH the original onboard records (C = 0, 1, ...) and the
    replayed ones (C = 100 + core; AP_DAL logging_core, Tools/Replay/check_replay.py pairs C with C + 100), so a bare
    'XKF1' is ambiguous. Replayed EKF3 core 0 = 'XKF1@100'; the flight's own onboard EKF3 core 0 = 'XKF1@0'.
    The UKF (U10 rule 2, 2026-10-12): 'XUKO' / 'XUKF' are the REPLAYED records, as the signed rung-1 pre-registration
    means them. From the replay-rukx Replay on, Replay writes them under distinct names, RUKO / RUKF (physical_name), so
    they cannot interleave with the onboard XUKO / XUKF that a fork-flown input log carries. The flying port's own
    records are named explicitly: 'XUKO@onboard' / 'XUKF@onboard'."""
    base, _, core = str(rec).partition("@")
    if base not in RECORDS:
        raise SystemExit(f"record {rec!r}: not one of {RECORDS}")
    if base == "XKF1":
        if not core.isdigit():
            raise SystemExit(f"record {rec!r}: XKF1 needs its core, 'XKF1@100' (replayed core 0) or 'XKF1@0' (onboard)")
        return base, int(core)
    if base in UKF_RENAMED and core == "onboard":
        return base, "onboard"
    if core:
        raise SystemExit(f"record {rec!r}: only XKF1 carries a core; only XUKO/XUKF take '@onboard'")
    return base, None


def physical_name(base, sel):
    """The dataflash message name a parsed record is read from: the replayed UKF records are RUKO / RUKF."""
    if base in UKF_RENAMED and sel is None:
        return UKF_RENAMED[base]
    return base
CLOCK_KEYS = {"rule", "w_thr_rad_s", "pad_s", "merge_s", "min_burst_s"}
SECONDARY_KEYS = {"heading_drift": {"window", "sense", "wrap_limit_deg"},
                  "cross_track_drift": {"window", "normal", "min_speed_mps", "smooth_s", "anchor", "anchor_avg_s"}}
SECONDARY_FIXED = {("heading_drift", "window"): "W", ("heading_drift", "sense"): "NED",
                   ("cross_track_drift", "window"): "W", ("cross_track_drift", "normal"): "right_of_mocap_velocity",
                   ("cross_track_drift", "anchor"): "takeoff_yaw"}
TOP_KEYS = {"window", "metrics", "drift", "estimator_records", "secondary"}
TOP_OPTIONAL = {"clock_map", "name", "status", "notes", "rationale"}


def _exact(d, need, where):
    if not isinstance(d, dict):
        raise SystemExit(f"prereg {where}: must be an object")
    miss, extra = sorted(need - set(d)), sorted(set(d) - need)
    if miss or extra:
        raise SystemExit(f"prereg {where}: missing keys {miss}, unknown keys {extra}")


def load_prereg(src):
    """The pre-registration, validated STRICTLY (see the module docstring). src: a path or a dict. Nothing is defaulted."""
    pre = json.load(open(src)) if isinstance(src, str) else src
    miss, extra = sorted(TOP_KEYS - set(pre)), sorted(set(pre) - TOP_KEYS - TOP_OPTIONAL)
    if miss or extra:
        raise SystemExit(f"prereg: missing sections {miss}, unknown sections {extra}")
    w = pre["window"]
    if not isinstance(w, dict) or w.get("rule") not in WINDOW_KEYS:
        raise SystemExit(f"prereg window.rule must be one of {sorted(WINDOW_KEYS)}")
    _exact(w, WINDOW_KEYS[w["rule"]] | {"rule"}, "window")
    m = pre["metrics"]; _exact(m, METRIC_KEYS, "metrics")
    if m["primary"] not in PRIMARY:
        raise SystemExit(f"prereg metrics.primary must be one of {PRIMARY}")
    if float(m["t_max_diff_s"]) != float(T_MAX_DIFF):
        raise SystemExit(f"prereg metrics.t_max_diff_s must be {T_MAX_DIFF} (evo is called exactly as three_way_eval)")
    d = pre["drift"]
    if not isinstance(d, dict) or d.get("segment_rule") not in DRIFT_KEYS:
        raise SystemExit(f"prereg drift.segment_rule must be one of {sorted(DRIFT_KEYS)}")
    _exact(d, DRIFT_KEYS[d["segment_rule"]] | {"segment_rule"}, "drift")
    er = pre["estimator_records"]
    if not isinstance(er, dict) or not er:
        raise SystemExit(f"prereg estimator_records: {{LABEL: one of {RECORDS} (XKF1 as XKF1@<core>)}}")
    for v in er.values():
        parse_record(v)
    sec = pre["secondary"]; _exact(sec, set(SECONDARY_KEYS), "secondary")
    for k, need in SECONDARY_KEYS.items():
        _exact(sec[k], need, f"secondary.{k}")
    for (k, f), v in SECONDARY_FIXED.items():
        if sec[k][f] != v:
            raise SystemExit(f"prereg secondary.{k}.{f} must be {v!r}")
    if "clock_map" in pre:
        _exact(pre["clock_map"], CLOCK_KEYS, "clock_map")
        if pre["clock_map"]["rule"] != "disarmed_wiggles":
            raise SystemExit("prereg clock_map.rule must be 'disarmed_wiggles'")
    return pre


def check_clock_map(cm, align):
    """The flight's mocap_align JSON against the prereg clock_map: default windows, the same wiggle-burst rule."""
    src = align.get("window_sources") or {}
    bad = [k for k in ("early", "late") if not str(src.get(k, "")).startswith("default")]
    if bad:
        raise SystemExit(f"mocap_align windows {bad} were not the pre-registered default (window_sources {src})")
    rule = align.get("sync_window_rule") or {}
    want = {k: cm[k] for k in ("w_thr_rad_s", "pad_s", "merge_s", "min_burst_s")}
    if any(abs(float(rule.get(k, float("nan"))) - float(v)) > 1e-9 for k, v in want.items()):
        raise SystemExit(f"mocap_align sync_window_rule {rule} differs from the prereg clock_map {want}")
    clk = align.get("clock") or {}
    # 2026-10-12: which gyro fitted the map (RISI, or the ~25 Hz IMU fallback with its stated <= ~3.5 ms bias), reported
    return {"window_sources": src, "sync_window_rule": rule, "gyro_src": clk.get("gyro_src"),
            "gyro_src_auto": clk.get("gyro_src_auto")}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _sorted_unique(a):
    """load_tum's ordering rule (stable sort by time, strictly increasing stamps) on an in-memory array."""
    a = a[np.argsort(a[:, 0], kind="stable")]
    return a[np.r_[True, np.diff(a[:, 0]) > 0]]


def load_tum(path):
    a = np.loadtxt(path, ndmin=2)
    a = a[np.argsort(a[:, 0], kind="stable")]
    return a[np.r_[True, np.diff(a[:, 0]) > 0]]


# ---------------------------------------------------------------------------------------------- inputs
def bin_trajs(path, records, reader=None, info_out=None):
    """{record spec: (N, 5) [t, PN, PE, PD, Yaw_deg_NED]} from a dataflash log. 'XKF1@C' keeps only core C (parse_record).

    Default reader (2026-10-12): eval/df_reader.read_records, NOT pymavlink. The fork's Replay writes the UKF records
    without FMT on a stock-flown log, and pymavlink then exits or drops ~99.5% of the XKF1 records (df_reader docstring).
    INTEGRITY (refused otherwise): every replayed core XKF1@C (C >= 100) must have exactly the TimeUS sequence of its
    onboard core XKF1@(C - 100) in the same log (Replay steps on the logged frames; Tools/Replay/check_replay.py pairs C
    with C + 100); XUKO/XUKF/XFGO must have strictly increasing TimeUS (a Replay of a FORK-flown log carries the onboard
    XUKO copied through AND the replayed one, interleaved and indistinguishable: checked on d17_v2, 8 654 + 8 629);
    and a requested record whose type has NO FMT in the log is refused with the reason.
    U10 rule 2 (2026-10-12): 'XUKO'/'XUKF' (the replayed UKF) are read from RUKO/RUKF, the names the replay-rukx Replay
    writes them under; 'XUKO@onboard'/'XUKF@onboard' from XUKO/XUKF (refused if declared in Replay's own id window
    [220, 230], i.e. written by an older Replay). A log with no RUKO but an XUKO is refused with the reason (older
    Replay, or a flight log). A log with any type id re-declared under a different FMT is refused.
    reader: an object with recv_match(type=[...]) (tests, the old interface); then no integrity checks are possible."""
    specs = {r: parse_record(r) for r in records}
    phys = {r: physical_name(*specs[r]) for r in records}
    types = sorted(set(phys.values())); out = {r: [] for r in records}
    if reader is not None:
        while True:
            x = reader.recv_match(type=types)
            if x is None:
                break
            ty = x.get_type()
            for r, (b, core) in specs.items():
                if phys[r] == ty and (b != "XKF1" or getattr(x, "C", None) == core):
                    out[r].append((x.TimeUS / 1e6, x.PN, x.PE, x.PD, getattr(x, "Yaw", float("nan"))))
        return {k: np.array(v).reshape(-1, 5) for k, v in out.items()}
    from df_reader import read_records
    recs, info = read_records(path, types)
    if info_out is not None:
        info_out.update({k: info[k] for k in ("undeclared_types", "skipped_bytes", "n_resyncs", "bad_fmt",
                                               "redeclared_ids")})
    if info["redeclared_ids"]:
        raise SystemExit(f"{path}: type ids re-declared under a different FMT {info['redeclared_ids'][:5]}: the records "
                         "after the re-declaration decode under the wrong format, so the log is refused")
    for r, (b0, core) in specs.items():
        if b0 in UKF_RENAMED and core is None and phys[r] not in info["declared"] and b0 in info["declared"]:
            raise SystemExit(
                f"record {r}: no {phys[r]} in {path}. The replayed UKF record is {phys[r]} from the U10 rule-2 Replay "
                f"(port replay-rukx) on. This log has {b0}: either the ONBOARD record (a flight log, or one copied through "
                f"by Replay: name it '{b0}@onboard') or the replayed one from an older Replay (e82c050b or before): "
                "re-run the current Replay")
        if core == "onboard" and b0 in info["declared"]:
            bad = [i for i in info["type_ids"].get(b0, []) if REPLAY_ID_WINDOW[0] <= i <= REPLAY_ID_WINDOW[1]]
            if bad:
                raise SystemExit(f"record {r}: {b0} is declared with type id {bad}, inside Replay's own id window "
                                 f"{list(REPLAY_ID_WINDOW)}: it was written by an older Replay (replayed, not onboard)")
        b = phys[r]
        if b not in info["declared"]:
            why = (" The thesis fork's Replay writes XUKF/XUKO/XUKS without their FMT records when the input log does not "
                   "declare them (every stock-flown rung-1 log; undeclared type ids here: "
                   f"{sorted(info['undeclared_types'])}). XUKO is NOT scorable from this Replay output until the port "
                   "emits the FMT records in Replay or writes the current-time CSV (spec: docs/handovers/"
                   "2026-10-12_r1_scoring_items.md, section C); give it with --est-csv UKF=<ukf_output.csv>."
                   if b[1:3] == "UK" else "")
            raise SystemExit(f"record {r}: no FMT for {b} in {path}.{why}")
    by = {}
    for b in types:
        for x in recs[b]:
            by.setdefault((b, x.get("C") if b == "XKF1" else None), []).append(
                (x["TimeUS"] / 1e6, x["PN"], x["PE"], x["PD"], x.get("Yaw", float("nan"))))
    for r, (b, core) in specs.items():
        out[r] = np.array(by.get((phys[r], core if b == "XKF1" else None), [])).reshape(-1, 5)
    for r, (b, core) in specs.items():
        a = out[r]
        if b == "XKF1" and core >= 100:
            ref = np.array(by.get(("XKF1", core - 100), [])).reshape(-1, 5)
            if len(ref) != len(a) or not np.array_equal(ref[:, 0], a[:, 0]):
                raise SystemExit(f"record {r}: {len(a)} replayed samples against {len(ref)} onboard XKF1@{core - 100} with "
                                 f"{'equal' if len(ref) == len(a) else 'different'} counts; the TimeUS sequences differ, "
                                 "so the Replay output cannot be trusted (truncated, or misread)")
        elif b != "XKF1" and len(a) > 1 and not np.all(np.diff(a[:, 0]) > 0):
            raise SystemExit(f"record {r}: TimeUS not strictly increasing ({int(np.sum(np.diff(a[:, 0]) <= 0))} "
                             "repeats/reversals): two interleaved series, e.g. the onboard and the replayed UKF of a "
                             "fork-flown log, which cannot be told apart")
    return out


XUKO_COLUMNS = ["TimeUS", "PN", "PE", "PD", "VN", "VE", "VD", "Roll", "Pitch", "Yaw", "OV", "EvO", "EvMx", "GpT", "GpN"]


def csv_traj(path, record):
    """The UKF port's current-time output written by Replay as CSV (port spec 2026-10-12, handover section C): the
    header must be exactly XUKO's columns. Returns (N, 5) [t, PN, PE, PD, Yaw_deg_NED]."""
    if record != "XUKO":
        raise SystemExit(f"--est-csv is defined only for the XUKO record, not {record!r}")
    head = open(path).readline().strip().split(",")
    if head != XUKO_COLUMNS:
        raise SystemExit(f"{path}: header {head} is not XUKO's columns {XUKO_COLUMNS}")
    a = np.genfromtxt(path, delimiter=",", skip_header=1, ndmin=2)
    out = np.c_[a[:, 0] / 1e6, a[:, 1:4], a[:, 9]]
    if len(out) > 1 and not np.all(np.diff(out[:, 0]) > 0):
        raise SystemExit(f"{path}: TimeUS not strictly increasing")
    return out


def ned_tum(a):
    """[t, PN, PE, PD, ...] -> TUM ENU with identity quaternions (APE here is the translation part; the yaw is carried
    separately, so the evo input is unchanged from the 2026-10-11 scorer)."""
    return np.c_[a[:, 0], a[:, 2], a[:, 1], -a[:, 3], np.tile([0.0, 0.0, 0.0, 1.0], (len(a), 1))]


def yaw_ned_from_tum(a):
    """NED-sense heading (deg; clockwise from above positive) from TUM quaternions (ENU/FLU frames): 90 - ENU yaw. The
    ENU yaw is the 'xyz' Euler z angle, exactly as eval/d15_drift.py and eval/phase4_eval.py take it."""
    from scipy.spatial.transform import Rotation as Rot
    return 90.0 - np.degrees(Rot.from_quat(a[:, 4:8]).as_euler("xyz")[:, 2])


# ---------------------------------------------------------------------------------------------- window
def longest_run(mask):
    best, i, n = (0, 0), 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]:
                j += 1
            if j - i > best[1] - best[0]:
                best = (i, j)
            i = j
        else:
            i += 1
    return best


def window_from_rule(mo, w):
    t, z = mo[:, 0], mo[:, 3]
    if w["rule"] == "fixed":
        return float(w["t0_s"]), float(w["t1_s"]), {"rule": "fixed"}
    if w["rule"] == "speed":
        t0, t1 = cruise_bounds(t, mo[:, 1], mo[:, 2], w.get("speed_mps"))
        return t0, t1, {"rule": "speed", "speed_mps": w.get("speed_mps")}
    if w["rule"] != "airborne":
        raise SystemExit(f"unknown window rule {w['rule']}")
    g = float(np.percentile(z, w["ground_percentile"]))
    i, j = longest_run(z - g > w["airborne_height_m"])
    if j == i or t[j - 1] - t[i] < w["hold_s"]:
        raise SystemExit("no airborne segment in the mocap record")
    tk, tl = float(t[i]), float(t[j - 1])
    t0, t1 = tk + w["start_after_takeoff_s"], tl - w["end_before_landing_s"]
    info = {"rule": "airborne", "ground_level_m": g, "takeoff_s": tk, "landing_s": tl}
    if t1 - t0 < w["min_duration_s"]:
        raise SystemExit(f"window [{t0:.2f}, {t1:.2f}] shorter than min_duration_s = {w['min_duration_s']}")
    return t0, t1, info


# ---------------------------------------------------------------------------------------------- metrics
def fit_4dof(src, dst):
    """yaw + translation with dst ~= Rz src + t (both z up)."""
    cs, cd = src.mean(0), dst.mean(0); a, b = src[:, :2] - cs[:2], dst[:, :2] - cd[:2]
    yaw = math.atan2(np.sum(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]), np.sum(a[:, 0] * b[:, 0] + a[:, 1] * b[:, 1]))
    c, s = math.cos(yaw), math.sin(yaw); Rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])
    return yaw, Rz, cd - Rz @ cs


def err_stats(e):
    n3, nh = np.linalg.norm(e, axis=1), np.linalg.norm(e[:, :2], axis=1)
    return {"rmse_m": float(np.sqrt(np.mean(n3 ** 2))), "rmse_h_m": float(np.sqrt(np.mean(nh ** 2))),
            "rmse_v_m": float(np.sqrt(np.mean(e[:, 2] ** 2))), "max_m": float(n3.max())}


def drift_segment(mo, t0, t1, d):
    """(s0, s1, None) on the FC clock: the drift metric's initial segment, from MOCAP only; or (.., .., reason)."""
    if d["segment_rule"] == "window_start_time":
        return t0, t0 + d["init_segment_s"], None
    w = (mo[:, 0] >= t0) & (mo[:, 0] <= t1); t, xy = mo[w, 0], mo[w, 1:3]
    if len(t) < 10:
        return None, None, "fewer than 10 mocap samples in the window"
    sp = np.hypot(np.gradient(xy[:, 0], t), np.gradient(xy[:, 1], t))
    n = max(1, int(round(d["onset_smooth_s"] / float(np.median(np.diff(t))))))
    sp = np.convolve(sp, np.ones(n) / n, "same")
    hi = sp > d["onset_speed_mps"]; k = None; i = 0
    while i < len(t):
        if hi[i]:
            j = i
            while j < len(t) and hi[j]:
                j += 1
            if t[j - 1] - t[i] >= d["onset_hold_s"]:
                k = i
                break
            i = j
        else:
            i += 1
    if k is None:
        return None, None, (f"no motion onset (speed > {d['onset_speed_mps']} m/s for {d['onset_hold_s']} s) "
                            f"in the window")
    path = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(xy[k:], axis=0), axis=1))]
    m = np.where(path >= d["init_path_m"])[0]
    if not len(m):
        return float(t[k]), None, f"the mocap travels only {path[-1]:.2f} m after the onset (< init_path_m)"
    return float(t[k]), float(t[k + m[0]]), None


def drift_metric(gt, pe, te, mo, t0, t1, d):
    s0, s1, why = drift_segment(mo, t0, t1, d)
    if why:
        return {"error": why, "segment_rule": d["segment_rule"]}
    s = (te >= s0) & (te <= s1)
    if s.sum() < 5:
        return {"error": "fewer than 5 samples in the initial segment", "segment_fc_s": [s0, s1]}
    ext = float(np.max(np.linalg.norm(gt[s, :2] - gt[s][0, :2], axis=1)))
    if ext < d["min_extent_m"]:
        return {"error": f"initial segment moves only {ext:.3f} m horizontally (< min_extent_m = {d['min_extent_m']}): "
                         f"yaw undefined", "init_segment_extent_h_m": ext, "segment_fc_s": [s0, s1]}
    yaw0, R0, tr0 = fit_4dof(gt[s], pe[s]); r0 = pe - ((R0 @ gt.T).T + tr0)
    path = float(np.sum(np.linalg.norm(np.diff(gt[:, :2], axis=0), axis=1)))
    fh = float(np.linalg.norm(r0[-1, :2]))
    return {**err_stats(r0), "final_m": float(np.linalg.norm(r0[-1])), "final_h_m": fh, "mocap_path_length_h_m": path,
            "final_h_pct_of_path": 100.0 * fh / path if path > 0 else None, "segment_rule": d["segment_rule"],
            "segment_fc_s": [s0, s1], "init_segment_extent_h_m": ext, "yaw_deg": math.degrees(yaw0)}


# ---------------------------------------------------------------------------------------------- secondary (2026-10-12)
# Ruled BEFORE ANY DATA (METHODOLOGY "RULINGS (user, 2026-10-12)", item 2): cross-track drift per minute and heading
# drift in deg/min, both UNALIGNED, for comparability with the simulation corridor results. Definitions:
# docs/rung1_preregistration.md sec. 4.4.
def heading_drift(te, ye_ned, tm, ym_ned, t0, t1, wrap_limit_deg=170.0):
    """The corridor heading-drift rule (eval/d15_drift.py drift(); the same rule as phase4_eval and d15_port_score):
    yaw error = estimator heading - truth heading at the estimator stamps (both unwrapped over the WHOLE series first),
    wrapped to (-180, 180] unless it runs away (max |err - err[0]| >= wrap_limit_deg), then the least-squares slope
    against minutes since the first window sample. NED sense (clockwise positive; ENU-sense values are the negative).
    Unaligned: the slope does not depend on a constant heading offset, so no alignment enters."""
    ye = np.degrees(np.unwrap(np.radians(ye_ned))); yr = np.degrees(np.unwrap(np.radians(ym_ned)))
    w = (te >= t0) & (te <= t1)
    if w.sum() < 10:
        return {"error": f"only {int(w.sum())} samples with a heading in the window"}
    err = ye[w] - np.interp(te[w], tm, yr)
    runaway = bool(np.abs(err - err[0]).max() >= wrap_limit_deg)
    if not runaway:
        err = (err + 180) % 360 - 180
    slope = float(np.polyfit((te[w] - te[w][0]) / 60.0, err, 1)[0])
    return {"heading_drift_deg_per_min_ned": slope, "n": int(w.sum()), "window_min": float((te[w][-1] - te[w][0]) / 60),
            "err_first_deg": float(err[0]), "err_last_deg": float(err[-1]), "runaway_unwrapped": runaway}


def _boxcar_t(t, x, s):
    n = max(1, int(round(s / float(np.median(np.diff(t))))))
    return np.convolve(x, np.ones(n) / n, "same")


def cross_track(te, pe, ye_ned, tm, pm, ym_ned, t0, t1, cfg, t_anchor=None, mo_ok=None, ve_given=None):
    """Cross-track drift per minute, the corridor rule generalised to a closed path (docs/rung1_preregistration.md
    sec. 4.4). Corridor (eval/phase5_analysis.ekf3, `xtrack_err_m`): the integral over the pinned cruise window of the
    lateral (East, i.e. across the corridor) velocity error, est - truth, both in the shared world frame; per minute =
    that / window minutes. Rung 1:
      * lateral = the RIGHT normal of the MOCAP horizontal velocity direction (boxcar `smooth_s`), n = (u_y, -u_x) in ENU,
        so a northward leg has n = East: identical to the corridor's axis and sign on a straight northward path;
      * only CRUISE samples: mocap smoothed horizontal speed > `min_speed_mps` (the direction is undefined in a hover)
        and inside the window [t0, t1]; the integral runs over consecutive estimator samples that are both selected;
      * velocities: np.gradient of the POSITIONS, for every estimator (a TUM has no velocity). The integral is then the
        lateral POSITION-error growth over the cruise samples, the corridor's "position error growth re-referenced at
        cruise start" (eval/ukf_shadow_replay_check.py cross_E). The corridor's heading-share decomposition integrated
        EKF3's logged XKF1 VE instead, which is not integrally consistent with its PE (dsn_tex_r3: 40.19 m against
        36.51 m); `ve_given` reproduces that variant for the SITL regression only;
      * UNALIGNED, with one stated anchor: the estimator frame is rotated into the mocap frame by ONE yaw, the circular
        mean of (mocap heading - estimator heading) over the `anchor_avg_s` s ending at take-off (`anchor` takeoff_yaw;
        from mocap only, no fit). The corridor needed no anchor (both frames started on the true heading by
        construction); with no compass the real frames are unrelated, so this is the minimal stand-in. `identity`
        (no rotation) exists for the SITL regression only.
    Returns cross_track_m (signed: + = right of the direction of travel), cruise_s, the per-minute rate."""
    vm = np.c_[np.gradient(pm[:, 0], tm), np.gradient(pm[:, 1], tm)]
    vs = np.c_[_boxcar_t(tm, vm[:, 0], cfg["smooth_s"]), _boxcar_t(tm, vm[:, 1], cfg["smooth_s"])]
    ve = np.c_[np.gradient(pe[:, 0], te), np.gradient(pe[:, 1], te)] if ve_given is None else np.asarray(ve_given)[:, :2]
    if cfg["anchor"] == "identity":
        dpsi = 0.0
    elif cfg["anchor"] == "takeoff_yaw":
        a = (tm >= t_anchor - cfg["anchor_avg_s"]) & (tm <= t_anchor)
        if a.sum() < 3:
            return {"error": "fewer than 3 mocap samples in the anchor interval"}
        d = np.radians(np.interp(tm[a], te, np.degrees(np.unwrap(np.radians(ye_ned)))) - ym_ned[a])   # est - mocap, NED
        dpsi = float(np.arctan2(np.mean(np.sin(d)), np.mean(np.cos(d))))   # rotate est by +dpsi (ENU = -NED sense)
    else:
        raise SystemExit(f"cross_track anchor {cfg['anchor']!r}")
    c, s = math.cos(dpsi), math.sin(dpsi)
    ve = np.c_[c * ve[:, 0] - s * ve[:, 1], s * ve[:, 0] + c * ve[:, 1]]
    vmi = np.c_[np.interp(te, tm, vm[:, 0]), np.interp(te, tm, vm[:, 1])]
    vsi = np.c_[np.interp(te, tm, vs[:, 0]), np.interp(te, tm, vs[:, 1])]
    sp = np.hypot(vsi[:, 0], vsi[:, 1])
    sel = (te >= t0) & (te <= t1) & (sp > cfg["min_speed_mps"])
    if mo_ok is not None:
        sel &= mo_ok
    u = vsi / np.maximum(sp, 1e-9)[:, None]
    e = (ve[:, 0] - vmi[:, 0]) * u[:, 1] - (ve[:, 1] - vmi[:, 1]) * u[:, 0]     # (v_err) . (u_y, -u_x)
    both = sel[:-1] & sel[1:]
    dt = np.diff(te)
    xt = float(np.sum(0.5 * (e[:-1] + e[1:]) * dt * both)); cs = float(np.sum(dt * both))
    if cs < 1.0:
        return {"error": f"only {cs:.2f} s of cruise samples (mocap speed > {cfg['min_speed_mps']} m/s) in the window"}
    return {"cross_track_m": xt, "cruise_s": cs, "cross_track_m_per_min": xt / (cs / 60.0),
            "abs_cross_track_m_per_min": abs(xt) / (cs / 60.0), "anchor": cfg["anchor"],
            "anchor_yaw_deg_enu": math.degrees(dpsi), "n_selected": int(sel.sum())}


def score_one(mo, est, t0, t1, m, tmp, label, drift=None, est_yaw=None, secondary=None, t_anchor=None):
    drift = DEFAULT_PREREG["drift"] if drift is None else drift
    e = crop(est, t0, t1)
    e = e[(e[:, 0] >= mo[0, 0]) & (e[:, 0] <= mo[-1, 0])]
    if len(e) < 10:
        return {"error": f"only {len(e)} estimator samples inside the window"}
    # evo -a (SE(3)), the standing simulation metric: reference = mocap cropped to the same window. evo associates by
    # nearest stamp within t_max_diff (no interpolation), so it is given the full cropped estimate, as three_way_eval.
    rc, ec = f"{tmp}/{label}_ref.tum", f"{tmp}/{label}_est.tum"
    write_tum(rc, crop(mo, t0, t1)); write_tum(ec, e)
    out = {"n": int(len(e)), "evo_ape_a_se3": {"rmse_m": evo_ape_a(rc, ec), "t_max_diff_s": m["t_max_diff_s"]}}
    # in-house metrics: interpolate mocap only where it is bracketed closely (no truth invented across a dropout)
    j = np.searchsorted(mo[:, 0], e[:, 0]).clip(1, len(mo) - 1)
    ok = (mo[j, 0] - mo[j - 1, 0]) <= m["max_mocap_interp_gap_s"]
    ok |= np.isin(e[:, 0], mo[:, 0])                                   # exact stamp matches are always fine
    out["n_in_house"] = int(ok.sum()); out["n_dropped_mocap_gap"] = int((~ok).sum())
    e = e[ok]
    if len(e) < 10:
        out["error"] = f"only {len(e)} estimator samples with bracketing mocap"
        return out
    gt = np.c_[[np.interp(e[:, 0], mo[:, 0], mo[:, k]) for k in (1, 2, 3)]].T
    pe = e[:, 1:4]
    # 4-DoF over the window (mocap -> estimator frame)
    yaw, Rz, tr = fit_4dof(gt, pe); res = pe - ((Rz @ gt.T).T + tr)
    out["ate_4dof"] = {**err_stats(res), "yaw_deg": math.degrees(yaw)}
    # start-aligned drift
    out["drift_start_aligned"] = drift_metric(gt, pe, e[:, 0], mo, t0, t1, drift)
    # coverage
    st = np.r_[t0, e[:, 0], t1]; gaps = np.diff(st)
    out["coverage"] = {"longest_gap_s": float(gaps.max()),
                       "fraction_within_max_gap": float(1.0 - np.sum(gaps[gaps > m["max_gap_s"]]) / (t1 - t0)),
                       "first_s": float(e[0, 0]), "last_s": float(e[-1, 0])}
    if secondary is not None:
        out.update(secondary_metrics(mo, est, est_yaw, t0, t1, m, secondary, t_anchor))
    return out


def secondary_metrics(mo, est, yaw, t0, t1, m, sec, t_anchor):
    """Heading and cross-track drift (prereg `secondary`) on the FULL estimator series (heading is unwrapped over the
    whole series, as in the corridor), using only estimator samples whose mocap is bracketed closely (as score_one)."""
    j = np.searchsorted(mo[:, 0], est[:, 0]).clip(1, len(mo) - 1)
    ok = ((mo[j, 0] - mo[j - 1, 0]) <= m["max_mocap_interp_gap_s"]) | np.isin(est[:, 0], mo[:, 0])
    ok &= (est[:, 0] >= mo[0, 0]) & (est[:, 0] <= mo[-1, 0])
    out = {}
    if yaw is None or not np.all(np.isfinite(yaw[ok])):
        out["heading_drift"] = {"error": "the estimator source carries no heading"}
        out["cross_track_drift"] = {"error": "the estimator source carries no heading (needed for the anchor)"}
        return out
    ym = yaw_ned_from_tum(mo)
    h = sec["heading_drift"]
    out["heading_drift"] = {**heading_drift(est[ok, 0], yaw[ok], mo[:, 0], ym, t0, t1, h["wrap_limit_deg"]),
                            "sense": "NED (clockwise from above positive); ENU-sense figures are the negative"}
    x = sec["cross_track_drift"]
    r = cross_track(est[:, 0], est[:, 1:4], yaw, mo[:, 0], mo[:, 1:4], ym, t0, t1, x,
                    t_anchor=t0 if t_anchor is None else t_anchor, mo_ok=ok)
    if "error" not in r:
        sp = np.hypot(np.gradient(mo[:, 1], mo[:, 0]), np.gradient(mo[:, 2], mo[:, 0]))
        w = (mo[:, 0] >= t0) & (mo[:, 0] <= t1) & (sp > x["min_speed_mps"])
        # a constant error d in the anchor (e.g. the mocap rigid body's heading definition) adds speed * sin(d) of
        # lateral rate to EVERY estimator alike (common mode): reported so the absolute values can be read with it
        r["anchor_sensitivity_m_per_min_per_deg"] = float(np.mean(sp[w]) * math.radians(1.0) * 60.0) if w.any() else None
    out["cross_track_drift"] = r
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--prereg", required=True); ap.add_argument("--mocap", required=True)
    ap.add_argument("--mocap-align-json", help="mocap_align.py's JSON (required if the prereg has clock_map)")
    ap.add_argument("--est", action="append", default=[], help="LABEL=PATH.tum (FC clock, ENU)")
    ap.add_argument("--est-bin", action="append", default=[], help="LABEL=RECORD from --bin (XKF1, XUKO, XUKF, XFGO)")
    ap.add_argument("--est-csv", action="append", default=[],
                    help="LABEL=PATH: the UKF port's current-time CSV with XUKO's exact columns (record must be XUKO)")
    ap.add_argument("--bin"); ap.add_argument("--work-dir", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(argv); os.makedirs(a.work_dir, exist_ok=True)
    pre = load_prereg(a.prereg); er = pre["estimator_records"]
    clock = None
    if "clock_map" in pre:
        if not a.mocap_align_json:
            raise SystemExit("the prereg has clock_map: give --mocap-align-json")
        clock = check_clock_map(pre["clock_map"], json.load(open(a.mocap_align_json)))
    mo = load_tum(a.mocap)
    t0, t1, winfo = window_from_rule(mo, pre["window"])
    ests = {}
    for s in a.est:
        lab, p = s.split("=", 1)
        if er.get(lab) != "TUM":
            raise SystemExit(f"--est {lab}: the prereg's estimator_records has {lab} = {er.get(lab)!r}, not 'TUM'")
        tr = load_tum(p)
        has_q = tr.shape[1] >= 8 and not np.allclose(tr[:, 4:8], [0.0, 0.0, 0.0, 1.0])   # identity = no heading
        ests[lab] = {"source": os.path.abspath(p), "sha256": sha256(p), "traj": tr, "record": "TUM",
                     "yaw": yaw_ned_from_tum(tr) if has_q else None}
    for s in a.est_csv:
        lab, p = s.split("=", 1)
        if er.get(lab) != "XUKO":
            raise SystemExit(f"--est-csv {lab}: the prereg's estimator_records has {lab} = {er.get(lab)!r}, not 'XUKO'")
        c = _sorted_unique(csv_traj(p, "XUKO"))
        tp = f"{a.work_dir}/{lab}_XUKO_csv.tum"; write_tum(tp, ned_tum(c))
        ests[lab] = {"source": f"{os.path.abspath(p)} (XUKO columns, CSV)", "sha256": sha256(p), "traj": load_tum(tp),
                     "record": "XUKO", "yaw": c[:, 4]}
    bin_info = None
    if a.est_bin:
        if not a.bin:
            raise SystemExit("--est-bin needs --bin")
        pairs = [s.split("=", 1) for s in a.est_bin]
        for lab, rec in pairs:
            if er.get(lab) != rec:
                raise SystemExit(f"--est-bin {lab}={rec}: the prereg's estimator_records has {lab} = {er.get(lab)!r}")
        bin_info = {}
        tr = bin_trajs(a.bin, sorted({r for _, r in pairs}), info_out=bin_info)
        for lab, rec in pairs:
            if not len(tr[rec]):
                raise SystemExit(f"no {rec} records in {a.bin}")
            b = _sorted_unique(tr[rec])
            p = f"{a.work_dir}/{lab}_{rec.replace('@', '_C')}.tum"; write_tum(p, ned_tum(b))
            pn = physical_name(*parse_record(rec))
            ests[lab] = {"source": f"{os.path.abspath(a.bin)}:{rec}" + (f" (message {pn})" if pn != rec.split("@")[0] else ""),
                         "sha256": sha256(a.bin), "traj": load_tum(p), "record": rec, "physical_record": pn,
                         "yaw": b[:, 4]}
    prim = pre["metrics"]["primary"]
    out = {"prereg": {"path": os.path.abspath(a.prereg), "sha256": sha256(a.prereg), "resolved": pre},
           "mocap": {"path": os.path.abspath(a.mocap), "sha256": sha256(a.mocap), "n": int(len(mo))},
           "clock_map_check": clock, "window_s": [t0, t1], "window_info": winfo, "primary_metric": prim,
           "bin_reader": bin_info, "primary": {}, "estimators": {}}
    for lab, d in ests.items():
        if d["yaw"] is not None and len(d["yaw"]) != len(d["traj"]):
            raise SystemExit(f"{lab}: heading and trajectory rows differ")
        r = score_one(mo, d["traj"], t0, t1, pre["metrics"], a.work_dir, lab, pre["drift"], est_yaw=d["yaw"],
                      secondary=pre["secondary"], t_anchor=winfo.get("takeoff_s"))
        out["estimators"][lab] = {"source": d["source"], "record": d["record"], "sha256": d["sha256"], **r}
        if "physical_record" in d:
            out["estimators"][lab]["physical_record"] = d["physical_record"]
        out["primary"][lab] = r[prim]["rmse_m"] if prim in r else None
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1)
    print(f"window [{t0:.2f}, {t1:.2f}] s ({winfo['rule']}), primary metric {prim}")
    print(f"{'est':8}{'evo -a':>10}{'4DoF':>10}{'drift fin':>11}{'drift %':>9}{'hdg d/min':>11}{'xtrk m/min':>11}{'n':>7}")
    for lab, r in out["estimators"].items():
        if "error" in r:
            print(f"{lab:8} {r['error']}"); continue
        d = r["drift_start_aligned"]
        hd = r.get("heading_drift", {}).get("heading_drift_deg_per_min_ned", float("nan"))
        xt = r.get("cross_track_drift", {}).get("cross_track_m_per_min", float("nan"))
        print(f"{lab:8}{r['evo_ape_a_se3']['rmse_m']:10.3f}{r['ate_4dof']['rmse_m']:10.3f}"
              f"{d.get('final_m', float('nan')):11.3f}{(d.get('final_h_pct_of_path') or float('nan')):9.2f}"
              f"{hd:11.2f}{xt:11.3f}{r['n']:7d}")
    print(f"[out] {a.out}")
    return out


if __name__ == "__main__":
    main()
