"""Baseline UKF core — PURE functions (numpy in, numpy out).

No ROS, no bag, no sim-time, no I/O. State is a 15-vector (measurement_models
layout). The replay harness (and a future live/HW node) are thin wrappers that
only call predict()/update_range()/update_flow() and never reach inside.

15-state IMU-driven UKF, ENU/FLU, ZYX Euler, delta-form biases matching EKF3.
Predict at dt = 0.0125 s (80 Hz). Process noise Q and measurement R/gates copied
from EKF3 unchanged (see make_params). Per-axis sequential flow gating.
"""
import numpy as np
from measurement_models import (N, P_SLICE, V_SLICE, A_SLICE, BG_SLICE, BA_SLICE,
                                 R_world_body, h_range, h_flow)

G_ENU = np.array([0.0, 0.0, -9.80665])
_ANG = [6, 7, 8]


# ---------- params (locked constants) ----------
DT_REF = 0.0125     # EKF3's prediction period (EKF_TARGET_DT accumulation: 5 x 2.5 ms frames)


def make_params(dt=0.0125):
    GYRO_P_NSE, ACC_P_NSE = 0.015, 0.35            # EKF3, rad/s and m/s^2
    GBIAS_P_NSE, ABIAS_P_NSE = 0.001, 0.02         # EKF3, rad/s/s and m/s/s/s
    # D27 (ruled 2026-10-01): EKF3's per-step forms (dt*NSE)^2 and (dt^2*NSE)^2 accumulate dt*NSE^2 per second,
    # i.e. they are rate-dependent. Every estimator must carry the SAME per-second noise densities (sensor noise is
    # a sensor property, D18): EKF3's at its own DT_REF = 12.5 ms, as the UKF port (12.5 ms steps) and the FGO
    # (sigma_c = NSE*sqrt(DT_REF)) do. At a step dt the per-step form is therefore scaled by DT_REF/dt; at
    # dt = DT_REF this is EKF3's form exactly. (From correction (ii), 2026-09-29, until D27 the offline UKF used
    # dt = 15 ms unscaled: 1.2x the per-second noise of the FGO and the port.)
    k = DT_REF / dt
    q_att = (dt * GYRO_P_NSE) ** 2 * k
    q_vel = (dt * ACC_P_NSE) ** 2 * k
    q_bg = (dt * dt * GBIAS_P_NSE) ** 2 * k      # delta-form bias: rate-bias variance dt*DT_REF*NSE^2 per step
    q_ba = (dt * dt * ABIAS_P_NSE) ** 2 * k
    Q = np.diag([1e-8, 1e-8, 1e-8,                 # position (from velocity prop.)
                 q_vel, q_vel, q_vel,
                 q_att, q_att, q_att,
                 q_bg, q_bg, q_bg,
                 q_ba, q_ba, q_ba])
    return dict(dt=dt, Q=Q,
                FLOW_M_NSE=0.25, FLOW_GATE=300, FLOW_MAX=2.5,
                RNG_M_NSE=0.5, RNG_GATE=500, RNG_MIN=0.05, RNG_MAX=40.0,
                YAW_M_NSE=max(0.5, 0.05), YAW_DT=0.14,   # EK3_YAW_M_NSE 0.5, 7 Hz check
                ATT_VAR_GATE=0.04,                       # see update_yaw_pseudo (derived from EKF3's 0.01)
                alpha=1e-3, beta=2.0, kappa=0.0)


# ---------- sigma points (Van der Merwe) ----------
def _sigma_points(x, P, p):
    lam = p['alpha']**2 * (N + p['kappa']) - N
    c = N + lam
    Psym = 0.5*(P + P.T) + 1e-12*np.eye(N)
    try:
        S = np.linalg.cholesky(c * Psym)
    except np.linalg.LinAlgError:
        w, V = np.linalg.eigh(c * Psym)
        S = V @ np.diag(np.sqrt(np.clip(w, 1e-12, None)))
    sig = np.zeros((2*N+1, N)); sig[0] = x
    for i in range(N):
        sig[i+1] = x + S[:, i]
        sig[N+1+i] = x - S[:, i]
    Wm = np.full(2*N+1, 1.0/(2*c)); Wc = Wm.copy()
    Wm[0] = lam/c; Wc[0] = lam/c + (1 - p['alpha']**2 + p['beta'])
    return sig, Wm, Wc


def _wrap(a):
    return (a + np.pi) % (2*np.pi) - np.pi


def _state_residual(a, b):
    r = a - b
    for i in _ANG:
        r[i] = _wrap(r[i])
    return r


def _state_mean(sig, Wm):
    m = Wm @ sig
    for i in _ANG:                       # circular mean for angles
        m[i] = np.arctan2(Wm @ np.sin(sig[:, i]), Wm @ np.cos(sig[:, i]))
    return m


# ---------- process model ----------
def _rotvec_to_R(v):
    th = np.linalg.norm(v)
    if th < 1e-9:
        return np.eye(3) + _skew(v)
    k = v/th; K = _skew(k)
    return np.eye(3) + np.sin(th)*K + (1-np.cos(th))*(K@K)


def _skew(v):
    return np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])


def _euler_from_R(R):
    pitch = -np.arcsin(np.clip(R[2, 0], -1.0, 1.0))
    roll = np.arctan2(R[2, 1], R[2, 2])
    yaw = np.arctan2(R[1, 0], R[0, 0])
    return roll, pitch, yaw


def _process(x, da, dv, dt):
    """One 80 Hz step. da: accumulated delta-angle (rad, FLU body over dt).
    dv: accumulated delta-velocity (m/s, FLU body over dt)."""
    y = x.copy()
    da_c = da - x[BG_SLICE]
    dv_c = dv - x[BA_SLICE]
    R = R_world_body(x[6], x[7], x[8])
    y[6], y[7], y[8] = _euler_from_R(R @ _rotvec_to_R(da_c))
    dv_world = R @ dv_c + G_ENU*dt
    y[P_SLICE] = x[P_SLICE] + x[V_SLICE]*dt          # p += v_old * dt
    y[V_SLICE] = x[V_SLICE] + dv_world
    return y


def predict(x, P, da, dv, p, dt=None):
    """dt: the ACTUAL accumulated interval of this step (batched correction (ii),
    2026-09-29); defaults to p['dt'], which the harness sets to the actual step."""
    sig, Wm, Wc = _sigma_points(x, P, p)
    dt = p['dt'] if dt is None else dt
    fs = np.array([_process(s, da, dv, dt) for s in sig])
    xm = _state_mean(fs, Wm)
    Pm = p['Q'].copy()
    for i in range(2*N+1):
        r = _state_residual(fs[i], xm)
        Pm += Wc[i]*np.outer(r, r)
    return xm, 0.5*(Pm+Pm.T)


# ---------- scalar gated update (used by range and each flow axis) ----------
def _update_scalar(x, P, z, hfun, R_scalar, gate_c, p):
    """1-D UKF update with EKF3-style NIS gate. Returns (x, P, accepted, testRatio)."""
    sig, Wm, Wc = _sigma_points(x, P, p)
    Z = np.array([hfun(s) for s in sig])             # (2N+1,)
    zpred = Wm @ Z
    dz = Z - zpred
    S = Wc @ (dz*dz) + R_scalar
    nu = z - zpred
    test = (nu*nu) / (gate_c * S)
    if test > 1.0 or not np.isfinite(test):
        return x, P, False, float(test)
    Pxz = np.zeros(N)
    for i in range(2*N+1):
        Pxz += Wc[i]*_state_residual(sig[i], x)*dz[i]
    K = Pxz / S
    xn = x + K*nu
    xn[6], xn[7], xn[8] = _wrap(xn[6]), _wrap(xn[7]), _wrap(xn[8])
    Pn = P - np.outer(K, K)*S
    return xn, 0.5*(Pn+Pn.T), True, float(test)


def update_range(x, P, rng, p):
    if not (p['RNG_MIN'] <= rng <= p['RNG_MAX']) or not np.isfinite(rng):
        return x, P, False
    gate_c = (0.01*p['RNG_GATE'])**2
    x, P, acc, _ = _update_scalar(x, P, rng, lambda s: h_range(s)[0],
                                  p['RNG_M_NSE']**2, gate_c, p)
    return x, P, acc


def update_yaw_pseudo(x, P, p):
    """Zero-innovation yaw pseudo-measurement — caps yaw variance WITHOUT
    injecting any heading information, matching EKF3's fuseEulerYaw(PREDICTED)
    (AP_NavEKF3_MagFusion.cpp:275-277): "prevent uncontrolled yaw variance growth
    that can destabilise the covariance matrix by fusing a zero innovation."
    Fairness, not a fix: EKF3 caps yaw this way in the no-mag case, so a UKF that
    lets yaw variance grow unbounded would differ by omission, not formulation.
    R = EK3_YAW_M_NSE^2 (AP_NavEKF3.cpp:446, 0.5 rad floored to 0.05).

    VARIANCE-GATED FIRING (matches EKF3, not a fixed rate). EKF3 checks this fire
    opportunity every 140 ms (MagFusion.cpp:263) but only actually fuses when the
    attitude covariance has grown past a threshold (MagFusion.cpp:274):
        `onGround || PV_AidingMode == AID_NONE || (P[0][0]+P[1][1]+P[2][2]+P[3][3] > 0.01f)`
    i.e. the trace of the quaternion (states 0-3) covariance exceeds 0.01 rad^2.
    Between fires yaw variance is allowed to grow, which is what lets the flow
    updates inject gyro-z-bias observability. Firing unconditionally every 140 ms
    (the previous behaviour) over-caps yaw variance and suppresses that weak
    observability.

    Threshold conversion, quaternion -> Euler (derived, not tuned). For a small
    attitude error the quaternion vector part is dq_vec ~= 0.5*dtheta and the
    scalar part q0 is constant to first order, so trace(P_quat[0..3]) ~=
    0.25*(sigma_roll^2 + sigma_pitch^2 + sigma_yaw^2) = 0.25*trace(P_att). EKF3's
    `> 0.01` therefore maps to trace(P_att) > 0.04 rad^2 on this UKF's Euler
    attitude block (states 6,7,8) — that is ATT_VAR_GATE. Roll/pitch stay small
    (accel-constrained), so in practice the gate triggers on yaw growth, exactly
    as intended. AID_NONE / onGround are airborne-aided here, so only the
    covariance term is active. The 140 ms cadence stays in the harness; this
    function decides whether to fuse. Returns (x, P, fired).

    THE FGO MUST MATCH THIS: attach a weak yaw prior (soft anchor) factor to each
    keyframe's Pose3 rotation with the same 0.5 rad sigma on the yaw DOF, so the
    smoother's yaw marginal is likewise bounded and doesn't free-drift. Documented
    in FGO_DESIGN.md."""
    if P[6, 6] + P[7, 7] + P[8, 8] <= p['ATT_VAR_GATE']:
        return x, P, False                               # attitude cov still tight — let yaw grow
    sig, Wm, Wc = _sigma_points(x, P, p)
    # measure yaw relative to the current mean -> z_rel = 0 (zero innovation),
    # linear residual (no angle wrap), mean preserved, only the covariance shrinks.
    Zr = np.array([_wrap(s[8] - x[8]) for s in sig])
    zpred = Wm @ Zr
    S = Wc @ ((Zr - zpred)**2) + p['YAW_M_NSE']**2
    Pxz = np.zeros(N)
    for i in range(2*N+1):
        Pxz += Wc[i]*_state_residual(sig[i], x)*(Zr[i] - zpred)
    K = Pxz / S
    xn = x + K*(0.0 - zpred)                          # z_rel = 0
    xn[6], xn[7], xn[8] = _wrap(xn[6]), _wrap(xn[7]), _wrap(xn[8])
    Pn = P - np.outer(K, K)*S
    return xn, 0.5*(Pn+Pn.T), True


def update_flow(x, P, flow_xy, omega_body, valid, inlier_ratio, p):
    """Per-axis sequential flow update, EKF3-style independent X/Y gating."""
    if not valid or inlier_ratio <= 0.0:
        return x, P, (False, False)
    if abs(flow_xy[0]) >= p['FLOW_MAX'] or abs(flow_xy[1]) >= p['FLOW_MAX']:
        return x, P, (False, False)
    gate_c = (0.01*p['FLOW_GATE'])**2
    R_flow = p['FLOW_M_NSE']**2
    acc = [False, False]
    for ax in (0, 1):                                # X first, then Y (sequential)
        x, P, a, _ = _update_scalar(x, P, flow_xy[ax],
                                    lambda s, ax=ax: h_flow(s, omega_body)[ax],
                                    R_flow, gate_c, p)
        acc[ax] = a
    return x, P, tuple(acc)


# ---------- initialisation (gravity levelling + first range) ----------
def init_state(accel_body_mean, first_range, dt=0.0125):
    """roll/pitch from static gravity vector; p_U from first LiDAR range + lever.
    yaw0 = 0 (unobservable). p_E,p_N,v,biases = 0. Bias states are DELTA form
    (per predict step), so EKF3's rate-form init 1σ are scaled by dt."""
    ax, ay, az = accel_body_mean
    roll0 = np.arctan2(ay, az)
    pitch0 = np.arctan2(-ax, np.hypot(ay, az))
    bg0 = 0.043633 * dt                              # gyro bias delta 1σ (EKF3 2.5 deg/s · dt)
    ba0 = 0.2 * dt                                   # accel bias delta 1σ (EKF3 0.2 m/s² · dt)
    x = np.zeros(N)
    x[2] = first_range + 0.12                        # base_link height
    x[6], x[7], x[8] = roll0, pitch0, 0.0
    P = np.diag([1e-3, 1e-3, 0.5**2,                 # x,y gauge-tight; z from RNG_M_NSE
                 0.1**2, 0.1**2, 0.1**2,             # velocity
                 np.radians(5)**2, np.radians(5)**2, np.radians(1)**2,  # att
                 bg0**2, bg0**2, bg0**2,             # gyro bias (delta form)
                 ba0**2, ba0**2, ba0**2])            # accel bias (delta form)
    return x, P


# ---------- forward camera (Phase 4): heading and yaw-rate updates ----------
def update_heading(x, P, psi, sigma, gate, p):
    """Scalar heading update, h = yaw (measurement_models.h_heading), with the
    innovation wrapped (sigma points taken relative to the mean yaw, as in
    update_yaw_pseudo). chi-square gate nu^2/S <= gate, identical to the FGO's.
    Returns (x, P, accepted, nis)."""
    sig, Wm, Wc = _sigma_points(x, P, p)
    Zr = np.array([_wrap(s[8] - x[8]) for s in sig])
    zpred = Wm @ Zr
    dz = Zr - zpred
    S = Wc @ (dz * dz) + sigma ** 2
    nu = _wrap(psi - x[8]) - zpred
    nis = nu * nu / S
    update_heading.last_S = float(S)             # innovation covariance, for diagnostics (Phase 5b)
    if not np.isfinite(nis) or nis > gate:
        return x, P, False, float(nis)
    Pxz = np.zeros(N)
    for i in range(2 * N + 1):
        Pxz += Wc[i] * _state_residual(sig[i], x) * dz[i]
    K = Pxz / S
    xn = x + K * nu
    xn[6], xn[7], xn[8] = _wrap(xn[6]), _wrap(xn[7]), _wrap(xn[8])
    Pn = P - np.outer(K, K) * S
    return xn, 0.5 * (Pn + Pn.T), True, float(nis)


def update_yawrate(x, P, omega_meas, gyro_z_avg, sigma, gate, p):
    """Scalar yaw-rate update, h = gyro_z_avg - bg_z/dt (measurement_models.h_yawrate;
    the bias state is delta-form per predict step). Same chi-square gate.
    Returns (x, P, accepted, nis)."""
    from measurement_models import h_yawrate
    bz = BG_SLICE.start + 2
    xn, Pn, acc, test = _update_scalar(x, P, omega_meas,
                                       lambda s: h_yawrate(gyro_z_avg, s[bz] / p['dt']),
                                       sigma ** 2, gate, p)
    return xn, Pn, acc, float(test * gate)
