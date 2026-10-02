#!/usr/bin/env python3
"""ARM64 check of the C++ heading library (real-flight plan, tooling item 2). Extracts every Nth forward-camera frame
of a recorded bag (seed = frame index, as Phase 3), runs the SAME test driver built for x86 (cpp/heading_test_x86,
against cpp/libheading.so) and for ARM64 (cpp/aarch64/heading_test, under qemu-aarch64 here, or natively on a Pi with
--native), and compares every output. Writes eval/results/heading_aarch64_check.json.
Build first: src/forward_camera/cpp/build_aarch64.sh (ARM64) and the x86 driver (see docs/real_flights_pi_readiness.md).
Usage (venv-fwd): python3 tools/pi/heading_arm_check.py [--trial fwdc_tex_r1] [--every 50] [--native]"""
import argparse, csv, io, json, os, struct, subprocess, sys
import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore
ap = argparse.ArgumentParser(); ap.add_argument("--trial", default="fwdc_tex_r1"); ap.add_argument("--every", type=int, default=50)
ap.add_argument("--native", action="store_true", help="run the ARM64 driver natively (on a Pi), not under qemu")
ap.add_argument("--json", default="eval/results/heading_aarch64_check.json"); a = ap.parse_args()
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); CPP = os.path.join(ROOT, "src", "forward_camera", "cpp")
fz = json.load(open(os.path.join(ROOT, "eval", "results", "fwd_calibration.json")))["frozen"]
ts = get_typestore(Stores.ROS2_JAZZY); recs = []; w = h = None
with Reader(os.path.expanduser(f"~/thesis_data/trials/{a.trial}/bag")) as r:
    for k, (c, _, raw) in enumerate(r.messages(connections=[c for c in r.connections if c.topic == "/forward_camera/image"])):
        if k % a.every: continue
        m = ts.deserialize_cdr(raw, c.msgtype); w, h = m.width, m.height
        recs.append((k, np.ascontiguousarray(np.frombuffer(m.data, np.uint8).reshape(m.height, m.step)[:, :m.width])))
binf = os.path.join(CPP, "aarch64", f"frames_{a.trial}.bin")
with open(binf, "wb") as f:
    f.write(struct.pack("<iii", len(recs), w, h))
    for k, img in recs: f.write(struct.pack("<Q", k)); f.write(img.tobytes())
args = [binf, str(fz["inlier_deg"]), str(fz["s_min"])]
x86 = subprocess.run([os.path.join(CPP, "heading_test_x86")] + args, capture_output=True, text=True, check=True).stdout
armcmd = [os.path.join(CPP, "aarch64", "heading_test")] + args
arm = subprocess.run(armcmd if a.native else ["qemu-aarch64"] + armcmd, capture_output=True, text=True, check=True,
                     env={**os.environ, "QEMU_LD_PREFIX": "/usr/aarch64-linux-gnu"}).stdout
A, B = list(csv.DictReader(io.StringIO(x86))), list(csv.DictReader(io.StringIO(arm)))
FL, IN = ["psi_deg", "u", "v", "support", "len_inl"], ["has_vp", "n_inl", "n_left", "n_right", "valid", "quality"]
out = {"trial": a.trial, "every": a.every, "frames": len(A), "arm_run": "native" if a.native else "qemu-aarch64",
       "frames_with_vp": sum(x["has_vp"] == "1" for x in A), "frames_valid_x86": sum(x["valid"] == "1" for x in A),
       "integer_outputs_identical": sum(all(x[k] == y[k] for k in IN) for x, y in zip(A, B)),
       "all_outputs_bit_identical": sum(all(x[k] == y[k] for k in FL + IN) for x, y in zip(A, B)),
       "max_abs_dpsi_deg": max(abs(float(x["psi_deg"]) - float(y["psi_deg"])) for x, y in zip(A, B) if x["has_vp"] == "1"),
       "max_abs_dsupport_px": max(abs(float(x["support"]) - float(y["support"])) for x, y in zip(A, B)),
       "x86_proc_ms_median": float(np.median([1e3 * float(x["proc_s"]) for x in A]))}
if a.native:
    out["arm_proc_ms_median"] = float(np.median([1e3 * float(y["proc_s"]) for y in B]))
    out["arm_proc_ms_p99"] = float(np.percentile([1e3 * float(y["proc_s"]) for y in B], 99))
json.dump(out, open(os.path.join(ROOT, a.json), "w"), indent=1); print(json.dumps(out, indent=1))
