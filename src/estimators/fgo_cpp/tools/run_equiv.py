#!/usr/bin/env python3
"""Run the C++ replay on an exported event stream and compare it with the Python FGO (compare_kf.py).

Usage: run_equiv.py <build_dir> <dump_prefix> <out_prefix> [python_timing_npz]
Refuses to run while a simulator is flying (CPU discipline); runs single-threaded at nice 19."""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
for pat in ("[a]rducopter", "[g]z sim"):
    if subprocess.run(["pgrep", "-f", pat], capture_output=True).returncode == 0:
        sys.exit("a simulator is running: refusing (CPU discipline)")
build, dump, out = sys.argv[1:4]
env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
subprocess.run([os.path.join(build, "fgo_cpp_replay"), dump, out], check=True, env=env, preexec_fn=lambda: os.nice(19))
subprocess.run([sys.executable, os.path.join(HERE, "compare_kf.py"), dump, out] + sys.argv[4:5], env=env)
same = open(dump + ".kf.f64", "rb").read() == open(out + ".kf.f64", "rb").read()
print(f"per-keyframe export bit-identical to Python: {same}")
