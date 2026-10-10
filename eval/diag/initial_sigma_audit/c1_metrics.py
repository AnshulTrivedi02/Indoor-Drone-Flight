#!/usr/bin/env python3
"""C1 verification metrics (venv-ardupilot): fwdplainc_tex_r1 FGO heading arm, for the stored output (1e-3 rad yaw / 2 deg
roll-pitch), the trace's F_YAW0 demonstration (y0s1), the yaw-only corrected core and the yaw + roll/pitch corrected core,
plus the stored UKF. Same metrics as eval/sens_yaw0_eval.py. Scratch paths as arguments: <trace_out> <isa_scratch>."""
import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import sens_yaw0_eval as S

tr, isa = sys.argv[1:3]
t = "fwdplainc_tex_r1"
res = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "results")
win = S.window(t, res)
rows = [("FGO stored (yaw 1e-3 rad, r/p 2 deg)", f"{S.TD}/{t}/fgo_heading", "fgo_traj.tum"),
        ("FGO trace y0s1 (F_YAW0 knob, 1 deg)", f"{tr}/{t}/fgo_heading_y0s1", "fgo_traj.tum"),
        ("FGO corrected, yaw only", f"{isa}/out_yawonly/{t}/fgo_heading", "fgo_traj.tum"),
        ("FGO corrected, yaw + roll/pitch 5 deg", f"{isa}/out_rp/{t}/fgo_heading", "fgo_traj.tum"),
        ("UKF stored", f"{S.TD}/{t}/ukf_heading", "ukf_traj.tum")]
with tempfile.TemporaryDirectory() as tmp:
    for lab, d, f in rows:
        m = S.metrics(t, d, f, win, tmp)
        print(f"{lab:40} evo -a (cruise) {m['evo_a_cruise']:8.3f} m  yaw rms {m['yaw_rms_deg']:8.3f} max {m['yaw_max_deg']:9.3f} deg  "
              f"bgz {m.get('bgz_mean_dpm', float('nan')):+8.2f} dpm  psi fused {m.get('psi_fused')}/{m.get('psi_valid')}")
