"""Model audit (2026-10-09), DIAGNOSTIC: the UKF's in-flight gyro/accel-bias variance from a UKF_DUMP replay (scratch),
cruise 60-300 s, against the per-step jitter (1e-12) and the stated per-step random walk.
Usage (~/venv-fgo): python3 ukf_dump_bias.py DUMP.npz OUT.json [DT_STEP]"""
import sys, json
import numpy as np
d = np.load(sys.argv[1])["x"]
DT = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0150028434
t = d[:, 0]; Pd = d[:, 16:31]
m = (t > 60) & (t < 300)
bg = np.median(Pd[m, 9:12], axis=0); ba = np.median(Pd[m, 12:15], axis=0)
# D27 form: q_bg = (dt^2*NSE)^2 * DT_REF/dt = dt^3 * DT_REF * NSE^2 (delta units)
q_bg_step = DT ** 3 * 0.0125 * 0.001 ** 2
out = {"n": int(m.sum()), "dt_step_s": DT,
       "gyro_bias_var_delta_median_xyz": bg.tolist(), "gyro_bias_sigma_rate_median_xyz": (np.sqrt(bg) / DT).tolist(),
       "accel_bias_sigma_rate_median_xyz": (np.sqrt(ba) / DT).tolist(),
       "jitter_per_step": 1e-12, "stated_gyro_bias_rw_per_step_delta": q_bg_step,
       "jitter_over_stated_per_step": 1e-12 / q_bg_step,
       "jitter_per_second_over_gyro_bias_var_xyz": ((1e-12 / DT) / bg).tolist()}
for k, v in out.items():
    print(k, v)
json.dump(out, open(sys.argv[2], "w"), indent=1)
