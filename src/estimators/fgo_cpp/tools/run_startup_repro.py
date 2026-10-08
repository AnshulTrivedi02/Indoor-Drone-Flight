#!/usr/bin/env python3
"""Re-run the time_ref start-up regression (docs/handovers/2026-10-08_fgo_cpp_timeref_fix.md) from a trial bag, each
heavy step through heavy.py. For every variant tape and every binary dir given, replays in time_ref (and, for the
plain ramp, causal) mode and scores it.

usage: run_startup_repro.py <trial_dir> <work_dir> <bin_dir> [<bin_dir> ...]
  e.g. run_startup_repro.py ~/thesis_data/trials/fgo_cpp_shadow_ii /tmp/w <baseline build> ~/opt/fgo_cpp/bin
Variants: real (the bag tape), ramp (0.55 s backlog draining over 1.5 s), burst (0.55 s in one receipt instant,
IMU before time_ref), ramp_gap (ramp + a 25 ms IMU gap inside the backlog, before the clock settles), ramp_gap_late
(ramp + a 25 ms gap at th0 + 12 s, after the settle, on the ground). Delay 0.10 s, arming from t_armed_header."""
import json, os, subprocess, sys
D, W, bins = os.path.expanduser(sys.argv[1]), sys.argv[2], sys.argv[3:]
HERE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.expanduser("~/venv-fgo/bin/python")
HEAVY = [sys.executable, os.path.join(HERE, "heavy.py")]
os.makedirs(W, exist_ok=True)
t_arm = json.load(open(os.path.join(D, "fgo_node_stats.json")))["t_armed_header"]
tape = f"{W}/real.tape"
if not os.path.exists(tape):
    subprocess.run(HEAVY + ["startup repro: tape", "--", PY, f"{HERE}/make_tape.py", f"{D}/bag", tape, "--armed-at", repr(t_arm)], check=True)
variants = {"real": None, "ramp": ["ramp"], "burst": ["burst"], "ramp_gap": ["ramp", "--gap-at", "0.8"],
            "ramp_gap_late": ["ramp", "--gap-at", "12.0"]}
for v, args in variants.items():
    if args and not os.path.exists(f"{W}/{v}.tape"):
        subprocess.run([PY, f"{HERE}/make_startup_repro.py", tape, f"{W}/{v}.tape"] + args, check=True)
cfg = f"{W}/live.init.json"
json.dump({"mode": "corridor", "window": 0.25, "kf_dt": 1.0 / 30.0, "lm_iters": 2, "t_arm": None, "fwd_sigma_psi": None},
          open(cfg, "w"))
gt = f"{W}/gt.npz"
for i, b in enumerate(bins):
    for v in variants:
        for mode in (("time_ref", "causal") if v == "ramp" else ("time_ref",)):
            pre = f"{W}/b{i}_{v}_{mode}"
            log = subprocess.run(HEAVY + [f"startup repro: replay {v} {mode}", "--", f"{b}/fgo_cpp_live_replay", f"{W}/{v}.tape",
                                          cfg, pre, "--imu-stamp", mode, "--delay", "0.10", "--arm-source", "heartbeat"],
                                 check=True, capture_output=True, text=True).stdout
            src = gt if os.path.exists(gt) else f"{D}/bag"
            sc = subprocess.run(HEAVY + [f"startup repro: score {v} {mode}", "--", PY, f"{HERE}/score_startup_repro.py",
                                         f"{W}/{v}.tape", pre, src] + ([] if src == gt else ["--cache", gt]),
                                check=True, capture_output=True, text=True).stdout
            print(f"==== bin {i} ({b}) {v} {mode}")
            print("\n".join(l for l in log.splitlines() if l.startswith(("[live]", "[tref]"))))
            print(sc.strip().splitlines()[-1], flush=True)
