"""Model audit (2026-10-09), DIAGNOSTIC: heading innovation covariance S, UKF against the FGO before and after the
setBiasAccOmegaInit correction, offline heading arm on fwdc_tex_r1, cruise 60-300 s (bag clock).
Inputs: the trial's ukf_heading (D27, current) and fgo_heading (pre-correction) outputs, and a corrected-FGO replay run
to scratch (FGO_OUT_ROOT). Usage (~/venv-fgo): python3 heading_S.py CORRECTED_FGO_NPZ OUT.json"""
import sys, json, math
import numpy as np
R = 0.0025830872929516074 ** 2          # FWD_SIGMA fwdc psi (0.148 deg)


def rep(S, nis, t):
    S, nis = np.asarray(S), np.asarray(nis); m = (t > 60) & (t < 300)
    sp = np.sqrt(np.clip(S[m] - R, 0, None))
    return dict(n=int(m.sum()), S_median=float(np.median(S[m])), pred_yaw_sigma_deg_median=math.degrees(float(np.median(sp))),
                weight_median=float(np.median((S[m] - R) / S[m])), nis_mean=float(np.mean(nis[m])),
                nis_median=float(np.median(nis[m])), frac_nis_gt9=float(np.mean(nis[m] > 9)))


tr = "/home/makerspace/thesis_data/trials/fwdc_tex_r1"
u = np.load(f"{tr}/ukf_heading/timing_and_fwd.npz")
out = {"R_sigma_deg": math.degrees(math.sqrt(R)),
       "ukf_current": rep(u["S_psi"], u["nis_psi"][:, 1], u["nis_psi"][:, 0])}
for lab, path in (("fgo_pre_correction", f"{tr}/fgo_heading/timing_and_fwd.npz"), ("fgo_corrected", sys.argv[1])):
    d = np.load(path); fl = d["fwd_log"]; k = fl[:, 1] == 0
    out[lab] = rep(d["fwd_S"][k], fl[k, 2], fl[k, 0])
for k, v in out.items():
    print(k, v)
json.dump(out, open(sys.argv[2], "w"), indent=1)
