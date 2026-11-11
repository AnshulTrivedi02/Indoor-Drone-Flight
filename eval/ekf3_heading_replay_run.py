#!/usr/bin/env python3
"""Replay driver for arms (i) EKF3 baseline and (ii) EKF3 + injected camera heading, and
the round-trip check's Replay-level field comparison
(docs/thesis/ekf3_heading_replay/preregistration.md). NOT RUN by Stage 1 -- written and
reviewed only; the coordinator releases runs after the round-trip check (preregistration
section 8.3) passes.

Three subcommands:

  run --arm baseline BAG        Arm (i): plain Replay of BAG's own ardupilot.bin, no
                                 injection. Scored against the bag's own STORED EKF3
                                 evo -a (cruise) score (eval/results/phase4_<ds>_evo.json,
                                 the same file eval/phase4_eval.py writes) -- must match
                                 to <= 1 mm (METHODOLOGY D8's own reproduction claim).

  run --arm heading BAG         Arm (ii): Replay of a REPH-injected copy of BAG's
    --records R.json              ardupilot.bin, EK3_SRC1_YAW=6 forced via --parm.
    --require-roundtrip-ok G.json  Refuses without an explicit --placement-latency-ms
    [--placement-latency-ms MS]    UNLESS every record already carries rfrf_count_before
                                    (Mode 1 -- only meaningful for a log replaying its
                                    own history, not a real arm (ii) use); refuses
                                    without --require-roundtrip-ok pointing at a JSON
                                    file containing {"round_trip_check": "PASS"} (the
                                    preregistration's stop rule, enforced here).

  compare BIN_A BIN_B            The round-trip check's OWN comparison (preregistration
                                  section 8.3 step 5): Replay BOTH bin files (through
                                  heavy.py, one at a time) with IDENTICAL --parm, then
                                  diff XKF1 (core 100, and separately core 101 if
                                  present -- never merged into one series, matching
                                  eval/d8_ekf3_retime.py's own C==100 convention: that
                                  script does not score core 101 at all, so this
                                  comparison reports it but does not claim a verdict on
                                  it), XKF4 and XKFS field-for-field. Operates on
                                  arbitrary .bin paths, NOT trial names, and calls
                                  NEITHER eval/three_way_eval.ekf3_tums() NOR
                                  eval/input_timing.sim_truth() -- both cache a derived
                                  file under <trial>/ekf3/ on first call, which would be
                                  a write into trials/ for the round-trip check's
                                  cl_bcpp_tex_r1_half input (preregistration section
                                  8.3's documented hazard). This is why `compare` is
                                  separate from `run`'s scoring path, not a shared helper.

Every Replay invocation goes through heavy.py (one job at a time, per the brief), never
called directly. Every output path is checked to NOT be under ~/thesis_data/trials/.
"""
import argparse, hashlib, json, os, subprocess, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import reph_inject as R
import three_way_eval as T  # cruise_window / crop / write_tum / evo_ape_a (run only; compare never calls ekf3_tums/sim_truth)

REPLAY_BIN = os.path.expanduser("~/ardupilot_diag/build/sitl/tool/Replay")
HEAVY = os.path.expanduser("~/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py")
TRIALS_DIR = os.path.realpath(os.path.expanduser("~/thesis_data/trials"))
RESULTS_DIR = os.path.join(HERE, "results")
# Core XKF* fields the round-trip check must agree on (position/velocity/attitude state
# plus the yaw-fusion-relevant innovation/status fields named in the preregistration).
XKF1_FIELDS = ["TimeUS", "Roll", "Pitch", "Yaw", "VN", "VE", "VD", "PN", "PE", "PD"]
# Field names verified against AP_NavEKF3/LogStructure.h (not assumed): XKF4 has no
# "YAW_FUSION" field -- the yaw/mag-relevant ones are SS (solution status bitmask), FS
# (fault status), TS (timeout status, bit 3 = magnetometer), SM (mag field variance).
# XKFS's yaw/mag-relevant field is MAG_FUSION (0=not fusing/1=fuse yaw/2=fuse mag) --
# the same field CLAUDE.md's no-compass verification already reads.
XKF4_FIELDS = ["TimeUS", "SS", "FS", "TS", "SM"]
XKFS_FIELDS = ["TimeUS", "MAG_FUSION"]


def replay_binary_hash():
    h = hashlib.sha256()
    with open(REPLAY_BIN, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _refuse_trials_path(p, what):
    rp = os.path.realpath(p)
    if rp == TRIALS_DIR or rp.startswith(TRIALS_DIR + os.sep):
        raise SystemExit(f"refusing: {what} ({p}) is under {TRIALS_DIR} (never write there)")


def run_replay(bin_path, out_dir, extra_parms=()):
    """One Replay invocation, through heavy.py (one job at a time). extra_parms:
    [(NAME, VALUE), ...] passed as --parm NAME=VALUE pairs, as d8_ekf3_retime.py does.
    Strips D8_FLOW_DT_AVG_MS from the environment (as d8_ekf3_retime.replay() does) --
    this diag binary reads that variable to re-time flow fusion, and it must be unset
    for arms (i)/(ii), which are not the D8 re-timing experiment."""
    _refuse_trials_path(out_dir, "Replay output dir")
    os.makedirs(out_dir, exist_ok=True)
    extra = []
    for name, value in extra_parms:
        extra += ["--parm", f"{name}={value}"]
    cmd = ["python3", HEAVY, f"ekf3_heading_replay Replay {os.path.basename(bin_path)}", "--",
           "nice", "-n", "10", REPLAY_BIN, *extra, bin_path]
    log_path = os.path.join(out_dir, "replay.log")
    env = {k: v for k, v in os.environ.items() if k != "D8_FLOW_DT_AVG_MS"}
    with open(log_path, "w") as log:
        r = subprocess.run(cmd, cwd=out_dir, stdout=log, stderr=subprocess.STDOUT, env=env)
    log_text = open(log_path).read()
    if r.returncode != 0 or "PANIC" in log_text:
        raise SystemExit(f"Replay failed (rc {r.returncode}, PANIC={'PANIC' in log_text}); see {log_path}")
    logs_dir = os.path.join(out_dir, "logs")
    logs = sorted((os.path.join(logs_dir, f) for f in os.listdir(logs_dir) if f.endswith(".BIN")),
                  key=os.path.getmtime)
    if not logs:
        raise SystemExit(f"Replay produced no .BIN output in {logs_dir}; see {log_path}")
    return logs[-1]


def _recv_rows(bin_path, msg_type, fields, core_filter=None):
    """[(field values...), ...] for every msg_type row, optionally filtered to a given
    "C" (core) value. Field order as given; missing attribute -> None."""
    from pymavlink import mavutil
    m = mavutil.mavlink_connection(bin_path)
    out = []
    while True:
        x = m.recv_match(type=[msg_type])
        if x is None:
            break
        if core_filter is not None and int(getattr(x, "C", -1)) != core_filter:
            continue
        out.append(tuple(getattr(x, f, None) for f in fields))
    return out


def score_arm_i_or_ii(bin_path, bag, outdir):
    """Score the REPLAYED core 100 (matching eval/d8_ekf3_retime.py's own C==100
    convention exactly -- core 101, if present, is reported, never merged in, and never
    scored, same as d8). evo -a (cruise), against the bag's own ground_truth.tum."""
    rows = _recv_rows(bin_path, "XKF1", ["TimeUS", "PN", "PE", "PD"], core_filter=100)
    if not rows:
        raise SystemExit(f"{bin_path}: no replayed (C==100) XKF1 rows -- Replay did not run EKF3 as expected")
    xk = np.array([(t / 1e6, pn, pe, pd) for t, pn, pe, pd in rows])
    gt_path = os.path.expanduser(f"~/thesis_data/trials/{bag}/ekf3/ground_truth.tum")
    if not os.path.exists(gt_path):
        T.ekf3_tums(bag)  # bag is one of the 18 Phase-4 trials, which already have this cache (preregistration section 8.3) -- never cl_bcpp_tex_r1_half
    sim = np.loadtxt(gt_path)
    t0, t1 = T.cruise_window(bag)
    ref = T.crop(sim, t0, t1)
    est = T.crop(np.c_[xk[:, 0], xk[:, 1:4], np.tile([0., 0., 0., 1.], (len(xk), 1))], t0, t1)
    rp, ep = os.path.join(outdir, "_ref.tum"), os.path.join(outdir, "_est.tum")
    T.write_tum(rp, ref)
    T.write_tum(ep, est)
    return T.evo_ape_a(rp, ep)


def stored_ekf3_score(bag):
    """The bag's own already-computed EKF3 evo -a (cruise) score, from
    eval/results/phase4_<fwdc|fwdplainc>_evo.json (eval/phase4_eval.py's own output) --
    arm (i)'s <= 1 mm reproduction target. None if the bag is not in either file."""
    ds = "fwdc" if bag.startswith("fwdc_") else "fwdplainc" if bag.startswith("fwdplainc_") else None
    if ds is None:
        return None
    p = os.path.join(RESULTS_DIR, f"phase4_{ds}_evo.json")
    if not os.path.exists(p):
        return None
    d = json.load(open(p))
    cell = d.get("trials", {}).get(bag, {}).get("est", {}).get("EKF3", {}).get("ate_a_cruise", {})
    return cell.get("+0.00")


def cmd_run(a):
    out_root = os.path.realpath(a.out_root)
    _refuse_trials_path(out_root, "--out-root")
    src_bin = os.path.expanduser(f"~/thesis_data/trials/{a.bag}/ardupilot.bin")
    if not os.path.exists(src_bin):
        raise SystemExit(f"{src_bin} does not exist")
    bag_out = os.path.join(out_root, a.bag, a.arm)
    if os.path.exists(bag_out):
        raise SystemExit(f"refusing to overwrite existing output dir {bag_out}")
    os.makedirs(bag_out, exist_ok=True)

    manifest = {"bag": a.bag, "arm": a.arm, "replay_binary": REPLAY_BIN,
                "replay_binary_sha256": replay_binary_hash(), "started_local": time.strftime("%Y-%m-%dT%H:%M:%S")}

    if a.arm == "baseline":
        input_bin, extra_parms = src_bin, []
    else:
        if not a.records:
            raise SystemExit("--arm heading requires --records (a reph_inject.py-format REPH records JSON)")
        if not a.require_roundtrip_ok:
            raise SystemExit("--arm heading requires --require-roundtrip-ok POINTING AT a JSON file recording "
                              "that the preregistration's round-trip check (section 8.3) PASSED -- this is "
                              "the document's stop rule, enforced here, not left to convention")
        gate = json.load(open(a.require_roundtrip_ok))
        if gate.get("round_trip_check") != "PASS":
            raise SystemExit(f"round-trip check gate is not PASS ({gate.get('round_trip_check')!r}); "
                              "refusing to run arm (ii). See preregistration section 8.3's stop rule.")
        records = json.load(open(a.records))
        is_mode1 = len(records) > 0 and all("rfrf_count_before" in r for r in records)
        if not is_mode1 and a.placement_latency_ms is None:
            raise SystemExit("records do not carry rfrf_count_before (the normal case for a brand-new "
                              "measurement, preregistration section 8.2 Mode 2) -- --placement-latency-ms "
                              "is required and has no default (preregistration section 8.4: open item)")
        injected_bin = os.path.join(bag_out, "injected.bin")
        R.inject(src_bin, injected_bin, records,
                  placement_latency_ms=None if is_mode1 else a.placement_latency_ms)
        input_bin, extra_parms = injected_bin, [("EK3_SRC1_YAW", "6")]
        manifest["records_file"] = a.records
        manifest["n_records_injected"] = len(records)
        manifest["placement_latency_ms"] = a.placement_latency_ms

    manifest["extra_parms"] = extra_parms
    replayed_bin = run_replay(input_bin, bag_out, extra_parms)
    manifest["result_evo_a_cruise"] = score_arm_i_or_ii(replayed_bin, a.bag, bag_out)
    if a.arm == "baseline":
        stored = stored_ekf3_score(a.bag)
        manifest["stored_ekf3_evo_a_cruise"] = stored
        if stored is not None:
            diff_m = abs(manifest["result_evo_a_cruise"] - stored)
            manifest["reproduction_diff_m"] = diff_m
            manifest["reproduction_pass_le_1mm"] = diff_m <= 0.001
    manifest["finished_local"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    json.dump(manifest, open(os.path.join(bag_out, "manifest.json"), "w"), indent=1)
    print(json.dumps(manifest, indent=1))


def cmd_compare(a):
    out_dir = os.path.realpath(a.out_dir)
    _refuse_trials_path(out_dir, "--out-dir")
    os.makedirs(out_dir, exist_ok=True)
    extra_parms = [tuple(p.split("=", 1)) for p in (a.parm or [])]
    dir_a, dir_b = os.path.join(out_dir, "a"), os.path.join(out_dir, "b")
    replayed_a = run_replay(a.bin_a, dir_a, extra_parms)
    replayed_b = run_replay(a.bin_b, dir_b, extra_parms)

    report = {"bin_a": a.bin_a, "bin_b": a.bin_b, "replay_binary": REPLAY_BIN,
              "replay_binary_sha256": replay_binary_hash(), "extra_parms": extra_parms, "fields": {}}
    all_pass = True
    for msg, fields in (("XKF1", XKF1_FIELDS), ("XKF4", XKF4_FIELDS), ("XKFS", XKFS_FIELDS)):
        cores = (100, 101) if msg == "XKF1" else (None,)
        for core in cores:
            rows_a = _recv_rows(replayed_a, msg, fields, core_filter=core)
            rows_b = _recv_rows(replayed_b, msg, fields, core_filter=core)
            key = f"{msg}" + (f"_core{core}" if core is not None else "")
            identical = rows_a == rows_b
            report["fields"][key] = {"n_a": len(rows_a), "n_b": len(rows_b), "field_for_field_identical": identical}
            if msg == "XKF1" and core == 101 and (rows_a or rows_b):
                report["fields"][key]["note"] = "core 101 reported, not scored -- eval/d8_ekf3_retime.py's own convention scores core 100 only"
            elif not identical:
                all_pass = False
    report["round_trip_check"] = "PASS" if all_pass else "FAIL"
    out_path = os.path.join(out_dir, "compare_result.json")
    json.dump(report, open(out_path, "w"), indent=1)
    print(json.dumps(report, indent=1))
    print(f"-> {out_path}  (this IS the file --require-roundtrip-ok should point at)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)

    r = sp.add_parser("run")
    r.add_argument("bag", help="trial name, e.g. fwdc_tex_r1 (NOT a path; must exist under ~/thesis_data/trials)")
    r.add_argument("--arm", choices=["baseline", "heading"], required=True)
    r.add_argument("--out-root", default=os.path.expanduser("~/thesis_data/ekf3_heading_replay"))
    r.add_argument("--records", help="arm=heading only: reph_inject.py-format JSON of records to inject")
    r.add_argument("--placement-latency-ms", type=float, default=None,
                   help="arm=heading only, Mode 2 (records without rfrf_count_before): required, no default")
    r.add_argument("--require-roundtrip-ok",
                    help="arm=heading only: a JSON file (e.g. this script's own `compare` output) this script "
                         'requires to contain {"round_trip_check": "PASS"} before running')
    r.set_defaults(func=cmd_run)

    c = sp.add_parser("compare", help="the round-trip check's own Replay + field diff, on arbitrary .bin paths")
    c.add_argument("bin_a"); c.add_argument("bin_b")
    c.add_argument("--out-dir", required=True)
    c.add_argument("--parm", action="append", help="NAME=VALUE, applied identically to both Replay runs")
    c.set_defaults(func=cmd_compare)

    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
