#!/usr/bin/env python3
"""Replay driver for arms (i) EKF3 baseline and (ii) EKF3 + injected camera heading
(docs/thesis/ekf3_heading_replay/preregistration.md). NOT RUN by Stage 1 -- written and
reviewed only; the coordinator releases runs after the round-trip check (preregistration
section 8.3) passes.

Arm (i): plain Replay of a Phase-4 bag's own ardupilot.bin, no REPH injection. Must
reproduce the bag's own stored EKF3 evo -a (cruise) score to <= 1 mm (METHODOLOGY D8).
This is the SAME check eval/d8_ekf3_retime.py already runs for its own "baseline" arm --
reused directly, not reimplemented.

Arm (ii): Replay of a REPH-injected copy of the SAME bag's ardupilot.bin, with
EK3_SRC1_YAW=6 (ExternalNav) forced via --parm. REQUIRES an injected-records JSON
(reph_inject.py's format) that this script does not itself compute -- see
preregistration section 8.4 ("open items") for why: arrival time and delay are not yet
ruled on. Calling this script for arm (ii) without that file, or without the round-trip
check having passed, is refused (see --require-roundtrip-ok below).

Usage (NOT RUN):
  python3 eval/ekf3_heading_replay_run.py BAG --arm baseline --out-root ~/thesis_data/ekf3_heading_replay
  python3 eval/ekf3_heading_replay_run.py BAG --arm heading --records REPH_RECORDS.json \\
      --out-root ~/thesis_data/ekf3_heading_replay --require-roundtrip-ok ROUNDTRIP_PASS.json

Every Replay invocation goes through heavy.py (one job at a time, per the brief), never
called directly.
"""
import argparse, hashlib, json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import reph_inject as R
import three_way_eval as T  # cruise_window / crop / write_tum / evo_ape_a / ekf3_tums

REPLAY_BIN = os.path.expanduser("~/ardupilot_diag/build/sitl/tool/Replay")
HEAVY = os.path.expanduser("~/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py")
TRIALS_DIR = os.path.realpath(os.path.expanduser("~/thesis_data/trials"))


def replay_binary_hash():
    h = hashlib.sha256()
    with open(REPLAY_BIN, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def run_replay(bin_path, out_dir, extra_parms=()):
    """One Replay invocation, through heavy.py (one job at a time). extra_parms:
    [(NAME, VALUE), ...] passed as --parm NAME=VALUE pairs, as d8_ekf3_retime.py does."""
    os.makedirs(out_dir, exist_ok=True)
    extra = []
    for name, value in extra_parms:
        extra += ["--parm", f"{name}={value}"]
    cmd = ["python3", HEAVY, f"ekf3_heading_replay Replay {os.path.basename(bin_path)}", "--",
           "nice", "-n", "10", REPLAY_BIN, *extra, bin_path]
    log_path = os.path.join(out_dir, "replay.log")
    with open(log_path, "w") as log:
        r = subprocess.run(cmd, cwd=out_dir, stdout=log, stderr=subprocess.STDOUT)
    if r.returncode != 0:
        raise SystemExit(f"Replay failed (rc {r.returncode}); see {log_path}")
    logs = sorted((os.path.join(out_dir, "logs", f) for f in os.listdir(os.path.join(out_dir, "logs"))
                   if f.endswith(".BIN")), key=os.path.getmtime)
    if not logs:
        raise SystemExit(f"Replay produced no .BIN output in {out_dir}/logs; see {log_path}")
    return logs[-1]


def score(bin_path, trial, outdir):
    """Score the REPLAYED core (C==100, +100 if a second input core exists) against SIM
    truth, on the bag's own pinned cruise window -- exactly as d8_ekf3_retime.score()
    does (not reimplemented differently)."""
    from pymavlink import mavutil
    import numpy as np
    m = mavutil.mavlink_connection(bin_path)
    xk = []
    while True:
        x = m.recv_match(type=["XKF1"])
        if x is None:
            break
        if getattr(x, "C", 0) >= 100:
            xk.append((x.TimeUS / 1e6, x.PN, x.PE, x.PD, int(x.C)))
    if not xk:
        raise SystemExit(f"{bin_path}: no replayed (C>=100) XKF1 rows -- Replay did not run EKF3 as expected")
    xk = np.array([r[:4] for r in xk])
    T.ekf3_tums(trial)  # idempotent: no-op if <trial>/ekf3/ground_truth.tum already exists
    sim = __import__("numpy").loadtxt(os.path.expanduser(f"~/thesis_data/trials/{trial}/ekf3/ground_truth.tum"))
    t0, t1 = T.cruise_window(trial)
    ref = T.crop(sim, t0, t1)
    est = T.crop(__import__("numpy").c_[xk[:, 0], xk[:, 1:4], __import__("numpy").tile([0., 0., 0., 1.], (len(xk), 1))], t0, t1)
    rp, ep = os.path.join(outdir, "_ref.tum"), os.path.join(outdir, "_est.tum")
    T.write_tum(rp, ref)
    T.write_tum(ep, est)
    return T.evo_ape_a(rp, ep)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bag", help="trial name, e.g. fwdc_tex_r1 (NOT a path; must exist under ~/thesis_data/trials)")
    ap.add_argument("--arm", choices=["baseline", "heading"], required=True)
    ap.add_argument("--out-root", default=os.path.expanduser("~/thesis_data/ekf3_heading_replay"))
    ap.add_argument("--records", help="arm=heading only: reph_inject.py-format JSON of records to inject")
    ap.add_argument("--require-roundtrip-ok",
                     help="arm=heading only: a JSON file this script requires to contain "
                          '{"round_trip_check": "PASS"} before running -- the preregistration\'s '
                          "stop rule (section 8.3), enforced in code, not just by convention")
    a = ap.parse_args()

    out_root = os.path.realpath(a.out_root)
    if out_root == TRIALS_DIR or out_root.startswith(TRIALS_DIR + os.sep):
        raise SystemExit("refusing: --out-root is under ~/thesis_data/trials (never write there)")

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
        input_bin = src_bin
        extra_parms = []
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
        injected_bin = os.path.join(bag_out, "injected.bin")
        R.inject(src_bin, injected_bin, records,
                  placement_latency_ms=None if all("rfrf_count_before" in r for r in records) else
                  (_ for _ in ()).throw(SystemExit(
                      "arm (ii) records must carry an explicit, ruled-on placement -- "
                      "this script does not supply a default placement_latency_ms (preregistration "
                      "section 8.4: the value is an open item)")))
        input_bin = injected_bin
        extra_parms = [("EK3_SRC1_YAW", "6")]
        manifest["records_file"] = a.records
        manifest["n_records_injected"] = len(records)

    manifest["extra_parms"] = extra_parms
    replayed_bin = run_replay(input_bin, bag_out, extra_parms)
    result = score(replayed_bin, a.bag, bag_out)
    manifest["result_evo_a_cruise"] = result
    manifest["finished_local"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    json.dump(manifest, open(os.path.join(bag_out, "manifest.json"), "w"), indent=1)
    print(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    main()
