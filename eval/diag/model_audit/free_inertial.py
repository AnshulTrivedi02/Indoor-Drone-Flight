"""Model audit (2026-10-09), DIAGNOSTIC: free-inertial covariance growth of EKF3, the UKF and the FGO on the SAME 10 s
of recorded IMU data, with no aiding, against the analytic growth from the stated noise densities (items 1 and 3).

Every estimator runs its OWN code path:
  EKF3     ekf3_cov_harness (EKF3's generated CovariancePrediction block copied verbatim from the pinned source, plus
           its noise set-up and ConstrainVariances), on the IMU re-binned to EKF3's 12.5 ms prediction period (FRD).
  UKF off  ukf_core.make_params(dt=DT_STEP) + ukf_core.predict, accumulated exactly as ukf_replay.py (5 dejittered
           samples = 15.003 ms per step, D27 per-second scaling).
  UKF port the same Python core at the port's 12.5 ms cadence (the port's Q is (d*NSE)^2 with d the actual ~12.5 ms
           step; equal to make_params(dt=0.0125); the port's sigma-point jitter c*1e-12 is the same as the Python's).
  FGO      fgo_core.make_pim_params() (the corrected params, setBiasAccOmegaInit = 0), a chain of CombinedImuFactor at
           the replay's 1/30 s IMU-clock keyframes from priors on X(0), V(0), B(0); gtsam.Marginals at each checkpoint.
           With no measurement factors the fixed-lag marginalisation is exact, so the full chain gives the smoother's
           marginal.
Analytic: the continuous linear INS error model (attitude, velocity, position, rate-form gyro and accel bias) at the
window's mean attitude and specific force, discretised exactly (Van Loan) at 12.5 ms, with the stated densities
q = NSE^2 * 0.0125 (CLAUDE.md "GTSAM IMU Preintegration - noise conversion"), from the SAME initial covariance.

Cases:
  A  common initial covariance: attitude 1e-5 rad, velocity / position 1e-2 (EKF3's 1e-4 variance floors), gyro bias
     1e-6 rad/s, accel bias at EKF3's floor 5e-9 (m/s)^2 delta = (5.657e-3 m/s^2)^2 rate (below it EKF3 RESETS the
     accel-bias covariance to 0.2 m/s^2). Yaw-bounding mechanisms OFF.
  B  as A, but each estimator's CONFIGURED initial bias sigmas (EKF3 2.5 deg/s, 0.2 m/s^2; UKF 0.043633*dt, 0.2*dt
     delta; FGO B(0) 0.043633, 0.2): a unit check of the delta/rate conversions.
  C  as A, with the yaw-bounding mechanisms ON: UKF update_yaw_pseudo every 140 ms (variance-gated), FGO yaw cap
     factor (sigma 0.5 rad); EKF3's fuseEulerYaw(PREDICTED) is variance-gated like the UKF's (its gate is reported
     from the harness's quaternion trace, not simulated).
  D  (yaw-cap gate stage, 2026-10-09) POSITIVE CONTROL: case B's configured bias sigmas with the yaw-bounding
     mechanisms ON, so that the gates must open (attitude variance grows with the 2.5 deg/s gyro-bias sigma).
FGO rows since the yaw-cap gate stage (2026-10-09, ruling "MODEL AUDIT RESULT ... RULINGS" item 2):
  fgo           fgo_core.FGO ITSELF (window 0.25 s, LM 2) driven keyframe by keyframe with no measurements, initialised
                with the case's priors (harness copy of FGO.init with those sigmas); its gate decides the cap. Values:
                the core's gate-only filtering covariance (cov_gate) at each keyframe.
  fgo_chain     the full-chain gtsam.Marginals (as the audit's FGO row) with the cap at exactly the keyframes where the
                core fired: checks the recursion against the smoother's marginal.
  fgo_ungated   case C/D only: the old behaviour, the cap at EVERY keyframe (full chain), for before/after.
Usage (~/venv-fgo): python3 free_inertial.py WINDOW.npz HARNESS OUT.json [T_TOTAL]"""
import sys, os, json, subprocess, math
import numpy as np


def expm(A):
    """Matrix exponential, scaling and squaring + 20-term Taylor (no scipy in ~/venv-fgo)."""
    s = max(0, int(np.ceil(np.log2(max(np.abs(A).sum(1).max(), 1e-300)))) + 1)
    As = A / 2.0 ** s
    E = np.eye(A.shape[0]); term = np.eye(A.shape[0])
    for k in range(1, 21):
        term = term @ As / k; E = E + term
    for _ in range(s):
        E = E @ E
    return E

HERE = os.path.dirname(os.path.abspath(__file__))
EST = os.path.join(HERE, "..", "..", "..", "src", "estimators")
sys.path.insert(0, EST); sys.path.insert(0, os.path.join(EST, "fgo"))
import ukf_core as U
from measurement_models import R_world_body
import gtsam
from gtsam.symbol_shorthand import X, V, B
import fgo_core
import factors as F

win, harness, out = sys.argv[1], sys.argv[2], sys.argv[3]
T_TOTAL = float(sys.argv[4]) if len(sys.argv) > 4 else 10.0
d = np.load(win)
t, acc, gyro = d["t"], d["acc"], d["gyro"]
period = float(d["period_ms"]) / 1e3
t = t[t <= t[0] + T_TOTAL + 1e-9]; n = len(t); acc = acc[:n]; gyro = gyro[:n]
dts = np.r_[period, np.diff(t)]                      # sample i covers (t[i-1], t[i]] (replay convention)
T0 = t[0] - period
CHK = [1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
CHK = [c for c in CHK if c <= T_TOTAL + 1e-6]

# ---------- stated densities (per second), CLAUDE.md ----------
DTR = 0.0125
QG, QA = 0.015 ** 2 * DTR, 0.35 ** 2 * DTR           # rad^2/s, (m/s)^2/s
QBG, QBA = 0.001 ** 2 * DTR, 0.02 ** 2 * DTR         # (rad/s)^2/s, (m/s^2)^2/s
g = 9.80665

# ---------- initial covariances (rate form, common) ----------
S_ATT, S_V, S_P = 1e-5, 1e-2, 1e-2
S_BG_A, S_BA_A = 1e-6, math.sqrt(5e-9) / DTR         # Case A biases
S_BG_B_EKF, S_BA_B = math.radians(2.5), 0.2          # Case B: EKF3 configured
S_BG_B_OURS = 0.043633                               # UKF/FGO configured (EKF3's 2.5 deg/s, rounded)

# ---------- 12.5 ms re-binning (EKF3, UKF port) ----------
cum_t = np.r_[T0, t]
cum_g = np.vstack([np.zeros(3), np.cumsum(gyro * dts[:, None], axis=0)])
cum_a = np.vstack([np.zeros(3), np.cumsum(acc * dts[:, None], axis=0)])
edges = np.arange(T0, t[-1] + 1e-12, DTR)
def cum_at(e, c):
    return np.array([np.interp(e, cum_t, c[:, k]) for k in range(3)]).T
G_e, A_e = cum_at(edges, cum_g), cum_at(edges, cum_a)
bin_da, bin_dv = np.diff(G_e, axis=0), np.diff(A_e, axis=0)   # FLU
bin_t = edges[1:] - T0

# mean attitude / specific force (levelled, as the estimators' init)
am = acc.mean(0)
roll0 = math.atan2(am[1], am[2]); pitch0 = math.atan2(-am[0], math.hypot(am[1], am[2]))


def metrics(var_tilt, var_yaw, var_vh, var_vz, var_ph, var_pz, var_bg, var_ba):
    return dict(tilt=math.sqrt(var_tilt), yaw=math.sqrt(var_yaw), vh=math.sqrt(var_vh), vz=math.sqrt(var_vz),
                ph=math.sqrt(var_ph), pz=math.sqrt(var_pz), bg=math.sqrt(var_bg), ba=math.sqrt(var_ba))


def pick(times, rows):
    res = {}
    for c in CHK:
        k = int(np.argmin(np.abs(np.asarray(times) - c)))
        res[f"{c:g}"] = dict(rows[k], t=float(times[k]))
    return res


# ---------- analytic (Van Loan, ENU, rate biases) ----------
def analytic(s_bg, s_ba, time_varying=False):
    """Linear error model with the stated densities. time_varying=False: fixed level attitude and the mean specific
    force. time_varying=True: linearised along the free-running MEAN trajectory that every estimator integrates
    (attitude strapped down from the levelled start through the recorded gyro, specific force of each 12.5 ms bin);
    over long windows the mean attitude drifts with the real gyro bias, which couples yaw error into velocity."""
    C0 = R_world_body(roll0, pitch0, 0.0)
    I3 = np.eye(3)
    sk = lambda v: np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    Qc = np.zeros((15, 15))
    Qc[0:3, 0:3] = QG * I3; Qc[3:6, 3:6] = QA * I3; Qc[9:12, 9:12] = QBG * I3; Qc[12:15, 12:15] = QBA * I3
    C = C0

    def disc(fb):
        Fm = np.zeros((15, 15))
        Fm[0:3, 9:12] = -C                     # attitude <- gyro bias
        Fm[3:6, 0:3] = -sk(C @ fb)             # velocity <- attitude (tilt x specific force)
        Fm[3:6, 12:15] = -C                    # velocity <- accel bias
        Fm[6:9, 3:6] = I3
        M = np.zeros((30, 30)); M[:15, :15] = -Fm; M[:15, 15:] = Qc; M[15:, 15:] = Fm.T
        E = expm(M * DTR); Phi = E[15:, 15:].T
        return Phi, Phi @ E[:15, 15:]
    Phi, Qd = disc(am)
    P = np.diag([S_ATT**2] * 3 + [S_V**2] * 3 + [S_P**2] * 3 + [s_bg**2] * 3 + [s_ba**2] * 3)
    times, rows = [], []
    for k in range(int(round(T_TOTAL / DTR))):
        if time_varying and k < len(bin_dv):
            C = C @ U._rotvec_to_R(bin_da[k])          # strapdown of the mean attitude (bias 0)
            Phi, Qd = disc(bin_dv[k] / DTR)
        P = Phi @ P @ Phi.T + Qd
        times.append((k + 1) * DTR)
        rows.append(metrics((P[0, 0] + P[1, 1]) / 2, P[2, 2], (P[3, 3] + P[4, 4]) / 2, P[5, 5], (P[6, 6] + P[7, 7]) / 2,
                            P[8, 8], np.trace(P[9:12, 9:12]) / 3, np.trace(P[12:15, 12:15]) / 3))
    return pick(times, rows)


# ---------- EKF3 harness ----------
def qmul(a, b):
    return np.array([a[0]*b[0]-a[1]*b[1]-a[2]*b[2]-a[3]*b[3], a[0]*b[1]+a[1]*b[0]+a[2]*b[3]-a[3]*b[2],
                     a[0]*b[2]-a[1]*b[3]+a[2]*b[0]+a[3]*b[1], a[0]*b[3]+a[1]*b[2]-a[2]*b[1]+a[3]*b[0]])


def ekf3(s_bg, s_ba, constrain=1):
    # NED <- FRD at yaw 0: FRD roll = FLU roll, FRD pitch = -FLU pitch (as the port's levelling, AP_NavUKF.cpp:257-258)
    cr, sr, cp, sp = math.cos(roll0/2), math.sin(roll0/2), math.cos(-pitch0/2), math.sin(-pitch0/2)
    q = np.array([cr*cp, sr*cp, cr*sp, -sr*sp])
    Jq = np.zeros((4, 3))                   # quaternion perturbation for an earth-frame rotation dtheta: dq = 0.5*[0,dth] x q
    for k in range(3):
        e = np.zeros(4); e[1 + k] = 1.0
        Jq[:, k] = 0.5 * qmul(e, q)
    Pq = Jq @ (np.eye(3) * S_ATT**2) @ Jq.T
    diag = [S_V**2] * 3 + [S_P**2] * 3 + [(s_bg * DTR) ** 2] * 3 + [(s_ba * DTR) ** 2] * 3
    lines = [f"{q[0]:.15g} {q[1]:.15g} {q[2]:.15g} {q[3]:.15g} {constrain} {DTR}",
             " ".join(f"{v:.9e}" for v in list(np.diag(Pq)) + diag)]
    # NOTE: only the diagonal of the initial quaternion block is passed (the harness reads 16 diagonal variances);
    # at S_ATT = 1e-5 rad the initial attitude term is negligible against the 10 s growth.
    da_frd = bin_da * np.array([1, -1, -1]); dv_frd = bin_dv * np.array([1, -1, -1])
    for k in range(len(bin_t)):
        lines.append(f"{DTR:.9f} " + " ".join(f"{v:.12e}" for v in np.r_[da_frd[k], dv_frd[k]]))
    r = subprocess.run([harness], input="\n".join(lines) + "\n", capture_output=True, text=True, check=True)
    times, rows, qtr = [], [], []
    iu = np.triu_indices(16)
    for ln in r.stdout.strip().split("\n"):
        v = np.array(ln.split(), float)
        P = np.zeros((16, 16)); P[iu] = v[5:]; P = P + P.T - np.diag(np.diag(P))
        qq = v[1:5]
        # earth-frame rotation vector: dtheta = 2*vec(dq x q*)  (linear in dq)
        Jt = np.zeros((3, 4)); qc = qq * np.array([1, -1, -1, -1])
        for j in range(4):
            e = np.zeros(4); e[j] = 1.0
            Jt[:, j] = 2 * qmul(e, qc)[1:]
        Pth = Jt @ P[0:4, 0:4] @ Jt.T        # NED
        times.append(v[0]); qtr.append(float(np.trace(P[0:4, 0:4])))
        rows.append(metrics((Pth[0, 0] + Pth[1, 1]) / 2, Pth[2, 2], (P[4, 4] + P[5, 5]) / 2, P[6, 6], (P[7, 7] + P[8, 8]) / 2,
                            P[9, 9], np.trace(P[10:13, 10:13]) / 3 / DTR**2, np.trace(P[13:16, 13:16]) / 3 / DTR**2))
    t_open = next((tt for tt, q_ in zip(times, qtr) if q_ > 0.01), None)
    return pick(times, rows), dict(stderr=r.stderr.strip(), quat_trace_max=max(qtr), yaw_gate_quat_trace=0.01,
                                   gate_first_open_t=t_open)


# ---------- UKF (offline cadence and port cadence) ----------
def ukf(s_bg, s_ba, cadence, yawcap=False):
    if cadence == "offline":
        nstep = int(math.ceil(0.0125 / period - 1e-9)); DT = nstep * period
    else:
        DT = DTR
    p = U.make_params(dt=DT)
    x, _ = U.init_state(am, 2.0, dt=DT)
    P = np.diag([S_P**2] * 3 + [S_V**2] * 3 + [S_ATT**2] * 3 + [(s_bg * DT) ** 2] * 3 + [(s_ba * DT) ** 2] * 3)
    times, rows = [], []; fired = 0; tc = 0.0; t_first = None
    def rec(tt):
        rows.append(metrics((P[6, 6] + P[7, 7]) / 2, P[8, 8], (P[3, 3] + P[4, 4]) / 2, P[5, 5], (P[0, 0] + P[1, 1]) / 2, P[2, 2],
                            np.trace(P[9:12, 9:12]) / 3 / DT**2, np.trace(P[12:15, 12:15]) / 3 / DT**2)); times.append(tt)
    if cadence == "offline":
        da = np.zeros(3); dv = np.zeros(3); adt = 0.0
        for i in range(n):
            da += gyro[i] * dts[i]; dv += acc[i] * dts[i]; adt += dts[i]
            if adt >= 0.0125 - 1e-9:
                x, P = U.predict(x, P, da, dv, p, dt=adt)
                if yawcap and t[i] - T0 - tc >= p["YAW_DT"]:
                    x, P, f = U.update_yaw_pseudo(x, P, p); fired += f; tc = t[i] - T0
                    t_first = t_first if (t_first is not None or not f) else t[i] - T0
                rec(t[i] - T0); da = np.zeros(3); dv = np.zeros(3); adt = 0.0
    else:
        for k in range(len(bin_t)):
            x, P = U.predict(x, P, bin_da[k], bin_dv[k], p, dt=DTR)
            if yawcap and bin_t[k] - tc >= p["YAW_DT"]:
                x, P, f = U.update_yaw_pseudo(x, P, p); fired += f; tc = bin_t[k]
                t_first = t_first if (t_first is not None or not f) else bin_t[k]
            rec(bin_t[k])
    return pick(times, rows), dict(step_ms=1e3 * DT, yaw_pseudo_fired=fired, first_fire_t=t_first)


# ---------- FGO ----------
def fgo(s_bg, s_ba, yawcap=False, cap_keys=None):
    """Full chain + gtsam.Marginals. yawcap=True: the cap at EVERY keyframe (the pre-2026-10-09 behaviour);
    cap_keys: the cap only at these keyframe indices (the core's fired keyframes).
    Yaw-cap gate stage (2026-10-09): the marginal at each checkpoint is now taken from the chain TRUNCATED at that
    keyframe (the FILTERING marginal, what a fixed-lag smoother holds at its newest keyframe). The audit's version took
    every checkpoint from the full chain (the SMOOTHED marginal); the two differ only where later factors inform earlier
    states, i.e. with yaw caps (case C's FGO at 10 s), and agree at the last checkpoint."""
    pim = gtsam.PreintegratedCombinedMeasurements(fgo_core.make_pim_params(), gtsam.imuBias.ConstantBias())
    pose0 = gtsam.Pose3(gtsam.Rot3.Ypr(0.0, pitch0, roll0), np.array([0.0, 0.0, 2.0]))
    graph = gtsam.NonlinearFactorGraph(); vals = gtsam.Values()
    graph.add(gtsam.PriorFactorPose3(X(0), pose0, gtsam.noiseModel.Diagonal.Sigmas(np.array([S_ATT] * 3 + [S_P] * 3))))
    graph.add(gtsam.PriorFactorVector(V(0), np.zeros(3), gtsam.noiseModel.Isotropic.Sigma(3, S_V)))
    graph.add(gtsam.PriorFactorConstantBias(B(0), gtsam.imuBias.ConstantBias(),
                                            gtsam.noiseModel.Diagonal.Sigmas(np.array([s_ba] * 3 + [s_bg] * 3))))
    vals.insert(X(0), pose0); vals.insert(V(0), np.zeros(3)); vals.insert(B(0), gtsam.imuBias.ConstantBias())
    yaw_noise = gtsam.noiseModel.Isotropic.Sigma(1, 0.5)
    k = 0; pose, vel = pose0, np.zeros(3); kf_next = T0 + 1.0 / 30.0; kts = []
    want = {max(1, int(round(c * 30.0))) for c in CHK}
    times, rows = [], []
    for i in range(n):
        pim.integrateMeasurement(acc[i], gyro[i], dts[i])
        if t[i] >= kf_next - 1e-9:
            nk = pim.predict(gtsam.NavState(pose, vel), gtsam.imuBias.ConstantBias())
            k += 1
            graph.add(gtsam.CombinedImuFactor(X(k - 1), V(k - 1), X(k), V(k), B(k - 1), B(k), pim))
            if yawcap or (cap_keys is not None and k in cap_keys):
                graph.add(F.yaw_prior_factor(yaw_noise, X(k), nk.pose().rotation().yaw()))
            pose, vel = nk.pose(), nk.velocity()
            vals.insert(X(k), pose); vals.insert(V(k), vel); vals.insert(B(k), gtsam.imuBias.ConstantBias())
            kts.append((k, t[i] - T0)); pim.resetIntegration(); kf_next += 1.0 / 30.0
            if k not in want:
                continue
            kk, tt = k, t[i] - T0
            marg = gtsam.Marginals(graph, vals)            # chain up to keyframe k: the filtering marginal
            Rk = vals.atPose3(X(kk)).rotation().matrix()
            Cp = marg.marginalCovariance(X(kk)); Cv = marg.marginalCovariance(V(kk)); Cb = marg.marginalCovariance(B(kk))
            Cth = Rk @ Cp[0:3, 0:3] @ Rk.T; Ct = Rk @ Cp[3:6, 3:6] @ Rk.T
            rows.append(metrics((Cth[0, 0] + Cth[1, 1]) / 2, Cth[2, 2], (Cv[0, 0] + Cv[1, 1]) / 2, Cv[2, 2],
                                (Ct[0, 0] + Ct[1, 1]) / 2, Ct[2, 2], np.trace(Cb[3:6, 3:6]) / 3, np.trace(Cb[0:3, 0:3]) / 3))
            times.append(tt)
    return pick(times, rows), dict(keyframes=k)


def fgo_core_run(s_bg, s_ba, yawcap):
    """fgo_core.FGO itself, no measurements, keyframes at the replay's 1/30 s IMU-clock schedule. FGO.init is copied
    here only to set the case's prior sigmas (the core's own init uses the configured ones); everything after init
    (keyframe(), the gate, the cap, the recursion) is the core's code."""
    f = fgo_core.FGO(window=0.25, kf_dt=1.0 / 30.0, lm_maxiter=2)
    f.no_yawcap = not yawcap
    pose0 = gtsam.Pose3(gtsam.Rot3.Ypr(0.0, pitch0, roll0), np.array([0.0, 0.0, 2.0]))
    bias0 = gtsam.imuBias.ConstantBias(np.zeros(3), np.zeros(3))
    pose_sig = np.array([S_ATT] * 3 + [S_P] * 3); vel_sig = np.array([S_V] * 3); bias_sig = np.array([s_ba] * 3 + [s_bg] * 3)
    g0 = gtsam.NonlinearFactorGraph(); v0 = gtsam.Values()
    g0.add(gtsam.PriorFactorPose3(X(0), pose0, gtsam.noiseModel.Diagonal.Sigmas(pose_sig)))
    g0.add(gtsam.PriorFactorVector(V(0), np.zeros(3), gtsam.noiseModel.Diagonal.Sigmas(vel_sig)))
    g0.add(gtsam.PriorFactorConstantBias(B(0), bias0, gtsam.noiseModel.Diagonal.Sigmas(bias_sig)))
    v0.insert(X(0), pose0); v0.insert(V(0), np.zeros(3)); v0.insert(B(0), bias0)
    f.smoother.update(g0, v0, fgo_core._tsmap({X(0): T0, V(0): T0, B(0): T0}))
    f.cov_gate = np.diag(np.concatenate([pose_sig, vel_sig, bias_sig]) ** 2)
    if not yawcap:     # cap off: the gate recursion does not run, so read the same recursion through log_cov
        f.log_cov = True; f.cov_prev = f.cov_gate.copy()
    f.t_yawchk = T0
    f.prev_pose, f.prev_vel, f.prev_bias = pose0, np.zeros(3), bias0
    f.t_last = T0; f.last = (T0, pose0, np.zeros(3))
    times, rows = [], []
    kf_next = T0 + 1.0 / 30.0
    for i in range(n):
        f.integrate_imu(acc[i], gyro[i], dts[i])
        if t[i] >= kf_next - 1e-9:
            f.keyframe(kf_next)
            C = f.cov_gate; Rk = f.prev_pose.rotation().matrix()
            Cth = Rk @ C[0:3, 0:3] @ Rk.T; Ct = Rk @ C[3:6, 3:6] @ Rk.T
            rows.append(metrics((Cth[0, 0] + Cth[1, 1]) / 2, Cth[2, 2], (C[6, 6] + C[7, 7]) / 2, C[8, 8],
                                (Ct[0, 0] + Ct[1, 1]) / 2, Ct[2, 2], np.trace(C[12:15, 12:15]) / 3, np.trace(C[9:12, 9:12]) / 3))
            times.append(kf_next - T0)
            kf_next += 1.0 / 30.0
    fired = [(e[0] - T0, e[1]) for e in f.yawgate_log if e[3]]
    tr = [e[2] for e in f.yawgate_log]
    return pick(times, rows), dict(keyframes=f.k, checks=f.n_yaw_check, fired=f.n_yaw_fire,
                                   first_fire_t=(fired[0][0] if fired else None), trace_max=(max(tr) if tr else None),
                                   gate=fgo_core.ATT_VAR_GATE, yaw_dt=fgo_core.YAW_DT), {k_ for _, k_ in fired}


_SIGMA_ORIG = U._sigma_points


def _sigma_points_nojitter(x, P, p):
    """DIAGNOSTIC copy of ukf_core._sigma_points with the 1e-12*I jitter removed (attribution test only)."""
    lam = p['alpha']**2 * (U.N + p['kappa']) - U.N
    c = U.N + lam
    Psym = 0.5*(P + P.T)
    try:
        S = np.linalg.cholesky(c * Psym)
    except np.linalg.LinAlgError:
        w, Vv = np.linalg.eigh(c * Psym)
        S = Vv @ np.diag(np.sqrt(np.clip(w, 0.0, None)))
    sig = np.zeros((2*U.N+1, U.N)); sig[0] = x
    for i in range(U.N):
        sig[i+1] = x + S[:, i]
        sig[U.N+1+i] = x - S[:, i]
    Wm = np.full(2*U.N+1, 1.0/(2*c)); Wc = Wm.copy()
    Wm[0] = lam/c; Wc[0] = lam/c + (1 - p['alpha']**2 + p['beta'])
    return sig, Wm, Wc


res = {"window": win, "t_total_s": T_TOTAL, "n_imu": int(n), "imu_period_ms": 1e3 * period,
       "roll0_deg": math.degrees(roll0), "pitch0_deg": math.degrees(pitch0), "mean_acc_flu": am.tolist(),
       "stated": dict(QG=QG, QA=QA, QBG=QBG, QBA=QBA), "cases": {}}
for case, (sbg_e, sba_e, sbg_o, sba_o, yc) in {"A": (S_BG_A, S_BA_A, S_BG_A, S_BA_A, False),
                                                 "B": (S_BG_B_EKF, S_BA_B, S_BG_B_OURS, S_BA_B, False),
                                                 "C": (S_BG_A, S_BA_A, S_BG_A, S_BA_A, True),
                                                 "D": (S_BG_B_EKF, S_BA_B, S_BG_B_OURS, S_BA_B, True)}.items():
    if case in ("B", "D") and T_TOTAL > 10.0:
        continue
    r = {}
    r["analytic"] = analytic(sbg_o, sba_o)
    if case == "A":
        r["analytic_tv"] = analytic(sbg_o, sba_o, time_varying=True)
    if case in ("B", "D"):
        r["analytic_ekf3init"] = analytic(sbg_e, sba_e)
    r["ekf3"], r["ekf3_info"] = ekf3(sbg_e, sba_e, constrain=1)
    if case == "A":
        r["ekf3_noconstrain"], _ = ekf3(sbg_e, sba_e, constrain=0)
    r["ukf_offline"], r["ukf_offline_info"] = ukf(sbg_o, sba_o, "offline", yawcap=yc)
    r["ukf_port"], r["ukf_port_info"] = ukf(sbg_o, sba_o, "port", yawcap=yc)
    if case == "A":                                   # attribution test: the same UKF with the sigma-point jitter removed
        U._sigma_points = _sigma_points_nojitter
        r["ukf_offline_nojitter"], _ = ukf(sbg_o, sba_o, "offline")
        r["ukf_port_nojitter"], _ = ukf(sbg_o, sba_o, "port")
        U._sigma_points = _SIGMA_ORIG
    r["fgo"], r["fgo_info"], fired_keys = fgo_core_run(sbg_o, sba_o, yawcap=yc)
    r["fgo_chain"], r["fgo_chain_info"] = fgo(sbg_o, sba_o, cap_keys=fired_keys)
    if yc:
        r["fgo_ungated"], r["fgo_ungated_info"] = fgo(sbg_o, sba_o, yawcap=True)
    res["cases"][case] = r
    print(f"== case {case}")
    for est in [k for k in r if not k.endswith("_info")]:
        for c, m in r[est].items():
            print(f"  {est:18s} t={c:>4s}  " + "  ".join(f"{q}={m[q]:.4g}" for q in ("tilt", "yaw", "vh", "vz", "ph", "pz", "bg", "ba")))
    for est in [k for k in r if k.endswith("_info")]:
        print("  ", est, r[est])
json.dump(res, open(out, "w"), indent=1)
