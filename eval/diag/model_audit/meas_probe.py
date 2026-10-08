"""Model audit (2026-10-09), DIAGNOSTIC: the measurement noise each estimator's CODE actually applies (item 2).

UKF: for flow (x, y), range, heading and the tag position/yaw, the innovation covariance S computed by the code's own
     sigma-point machinery (ukf_core._sigma_points + the same h) at a cruise state, minus the linearised H P H^T
     (central differences of the same h): R_eff = S - H P H^T, against the stated R.
FGO: each factor built by factors.py with the noise model fgo_core uses, linearised at a cruise state: the whitened
     Jacobian A against the unwhitened numerical Jacobian H gives sigma_eff = |H| / |A| per row.
Usage (~/venv-fgo): python3 meas_probe.py OUT.json"""
import sys, os, json, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
EST = os.path.join(HERE, "..", "..", "..", "src", "estimators")
sys.path.insert(0, EST); sys.path.insert(0, os.path.join(EST, "fgo"))
import ukf_core as U
import measurement_models as M
import gtsam
from gtsam.symbol_shorthand import X, V, B
import factors as F

out = {}
# ---------- UKF ----------
p = U.make_params(dt=0.015)
x = np.zeros(U.N); x[2] = 2.31; x[3] = 0.5; x[6], x[7], x[8] = 0.002, -0.003, 0.05
P = np.diag([0.04, 0.04, 0.0025, 0.01, 0.01, 0.002, 1e-5, 1e-5, 4e-4,
             (5e-4 * 0.015) ** 2, (5e-4 * 0.015) ** 2, (1.6e-3 * 0.015) ** 2, (0.05 * 0.015) ** 2, (0.05 * 0.015) ** 2,
             (0.01 * 0.015) ** 2])
om = np.array([0.01, -0.02, 0.003])


def ukf_S(h):
    sig, Wm, Wc = U._sigma_points(x, P, p)
    Z = np.array([h(s) for s in sig]); zp = Wm @ Z
    return float(Wc @ ((Z - zp) ** 2))


def lin_HPH(h):
    H = np.zeros(U.N)
    for j in range(U.N):
        d = np.zeros(U.N); d[j] = 1e-6
        H[j] = (h(x + d) - h(x - d)) / 2e-6
    return float(H @ P @ H)


cases = {
    "flow_x": (lambda s: M.h_flow(s, om)[0], p["FLOW_M_NSE"] ** 2),
    "flow_y": (lambda s: M.h_flow(s, om)[1], p["FLOW_M_NSE"] ** 2),
    "range": (lambda s: M.h_range(s)[0], p["RNG_M_NSE"] ** 2),
    "heading_closed_loop_5deg": (lambda s: U._wrap(s[8] - x[8]), math.radians(5.0) ** 2),
    "heading_offline_fwdc": (lambda s: U._wrap(s[8] - x[8]), M.FWD_SIGMA["fwdc"]["psi"] ** 2),
    "tag_pos_T": (lambda s: s[0], M.TAG_SIGMA_POS ** 2),
    "tag_yaw": (lambda s: U._wrap(s[8] - x[8]), M.TAG_SIGMA_YAW ** 2),
}
ukf = {}
for k, (h, R) in cases.items():
    S_spread = ukf_S(h); HPH = lin_HPH(h)
    S_code = S_spread + R                              # the code adds R to the sigma spread (ukf_core._update_scalar / update_heading)
    ukf[k] = dict(R_stated=R, S_code=S_code, HPH_lin=HPH, R_eff=S_code - HPH, ratio_R_eff_over_stated=(S_code - HPH) / R,
                  sigma_spread_over_lin=S_spread / HPH if HPH > 0 else None)
# heading through the real function, to read its logged S
U.update_heading(x.copy(), P.copy(), x[8], math.radians(5.0), 9.0, p)
ukf["heading_closed_loop_5deg"]["S_update_heading_last_S"] = U.update_heading.last_S
out["ukf"] = ukf

# ---------- FGO ----------
pose = gtsam.Pose3(gtsam.Rot3.Ypr(0.05, 0.003, 0.002), np.array([1.0, 2.0, 2.31]))
vel = np.array([0.5, 0.0, 0.0]); bias = gtsam.imuBias.ConstantBias(np.zeros(3), np.array([1e-3, -1e-3, 2e-3]))
vals = gtsam.Values(); vals.insert(X(1), pose); vals.insert(V(1), vel); vals.insert(B(1), bias)
fac = {
    "flow": (F.flow_factor(gtsam.noiseModel.Isotropic.Sigma(2, 0.25), X(1), V(1), B(1), np.array([0.02, 0.17]), om), 0.25),
    "range": (F.range_factor(gtsam.noiseModel.Isotropic.Sigma(1, 0.5), X(1), 2.19), 0.5),
    "yaw_cap": (F.yaw_prior_factor(gtsam.noiseModel.Isotropic.Sigma(1, 0.5), X(1), 0.05), 0.5),
    "heading_closed_loop_5deg": (F.heading_factor(gtsam.noiseModel.Isotropic.Sigma(1, math.radians(5.0)), X(1), 0.06),
                                 math.radians(5.0)),
    "tag_H_0.02": (F.tag_factor(gtsam.noiseModel.Diagonal.Sigmas(np.array([0.02, 0.02, M.TAG_SIGMA_YAW])), X(1),
                                (1.01, 2.0, 0.06)), [0.02, 0.02, M.TAG_SIGMA_YAW]),
}
fgo = {}
for k, (f, sig) in fac.items():
    jf = f.linearize(vals)
    A = jf.jacobian()[0]                               # whitened Jacobian, columns in jf.keys() order
    # unwhitened Jacobian by central differences on the same factor
    keys = list(jf.keys()); H = []
    for key in keys:
        c = chr(gtsam.Symbol(key).chr())
        dim = 6 if c in ("x", "b") else 3
        cols = []
        for j in range(dim):
            dv = np.zeros(dim); dv[j] = 1e-6
            def mk(sgn):
                # fresh Values (Values.update picks the fixed-size Vector3 overload for the dynamic velocity and throws)
                pp, vv, bb = pose, vel.copy(), bias
                if c == "x":
                    pp = pose.retract(sgn * dv)
                elif c == "v":
                    vv = vel + sgn * dv
                else:
                    bb = gtsam.imuBias.ConstantBias(bias.accelerometer() + sgn * dv[:3], bias.gyroscope() + sgn * dv[3:])
                w = gtsam.Values(); w.insert(X(1), pp); w.insert(V(1), vv); w.insert(B(1), bb)
                return w
            vp, vm = mk(1.0), mk(-1.0)
            cols.append((f.unwhitenedError(vp) - f.unwhitenedError(vm)) / 2e-6)
        H.append(np.array(cols).T)
    H = np.hstack(H)
    rows = []
    for r in range(A.shape[0]):
        rows.append(float(np.linalg.norm(H[r]) / np.linalg.norm(A[r])) if np.linalg.norm(A[r]) > 0 else None)
    fgo[k] = dict(sigma_stated=sig, sigma_eff_per_row=rows)
out["fgo"] = fgo
for k, v in out.items():
    print(k)
    for kk, vv in v.items():
        print("  ", kk, {a: (round(b, 6) if isinstance(b, float) else b) for a, b in vv.items()})
json.dump(out, open(sys.argv[1], "w"), indent=1)
