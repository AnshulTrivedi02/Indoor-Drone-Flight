#!/usr/bin/env python3
"""Part-3 report runs (no band): the live IMU-stamp modes on the raw tapes, each run one heavy step through heavy.py.
Usage: run_live_reports.py <scratch_dir> <build_dir>"""
import os, subprocess, sys
S, B = sys.argv[1:3]
HERE = os.path.dirname(os.path.abspath(__file__))
HEAVY = [sys.executable, os.path.join(HERE, "heavy.py"), "--wait-s", "3000"]
runs = [("dsn_tex_r1", "dump2/dsn_tex_r1", "dump2/cpp_dsn_tex_r1", []),
        ("fwdc_tex_r1", "dump2/fwdc_tex_r1_heading", "dump2/cpp_fwdc_tex_r1_heading",
         ["--heading", "--heading-sigma-rad", "0.0025830872929516074"])]
for bag, exp, ref, extra in runs:
    for mode in ("time_ref", "causal"):
        out = f"{S}/live/R_{bag}_{mode}"
        subprocess.run(HEAVY + [f"live replay {bag} {mode}", "--", f"{B}/fgo_cpp_live_replay", f"{S}/live/{bag}.raw.tape",
                                f"{S}/{exp}.init.json", out, "--imu-stamp", mode, "--arm-source", "param", "--delay", "0.20"]
                       + extra, check=True)
        print(f"==== {bag} imu_stamp={mode} vs export-driven C++ (report, no band)", flush=True)
        subprocess.run([os.path.expanduser("~/venv-ardupilot/bin/python"), os.path.join(HERE, "compare_live.py"),
                        f"{S}/live/{bag}.raw.tape", out, f"{S}/{ref}"], check=False)
