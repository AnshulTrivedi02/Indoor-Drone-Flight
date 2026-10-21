"""E5 (tier-1 extension experiment, pre-registered): the variable-size UKF core for the "UKF with tag landmarks (loop
closure)", a SEPARATE estimator from the thesis UKF. Design: docs/thesis/tier1/e5_design.md (signed off 2026-10-22,
with amendment 5). PURE functions, numpy in, numpy out; no ROS, no bag, no I/O.

State: the thesis UKF's 15 vehicle states (measurement_models layout), then one block [x_j, y_j, psi_j] per landmark
in the state, in order of first sighting (e5_design §3). psi_j is an ANGLE state: every function takes `ang`, the
tuple of angle indices (6, 7, 8, then 15 + 3k + 2 per landmark k), used by the circular mean, the wrapped residual
and the post-update wrap, exactly as ukf_core uses 6-8.

What is re-implemented and what is called (e5_design §1):
  * re-implemented for a variable n: the sigma points, the state mean and the state residual (ukf_core's use the
    module-global N = 15), and the scalar update / predict / RTS loops that call them. Each mirrors ukf_core
    OPERATION BY OPERATION, so at n = 15 (no landmarks) the results equal ukf_core's bit for bit (test_ukf_lm.py
    test 1);
  * CALLED unchanged: ukf_core._process (the vehicle process model), ukf_core.make_params, ukf_core.init_state,
    measurement_models.h_flow / h_range (the flow and range models; they read only the vehicle block).
Landmark rows: identity process, zero process noise (tags are fixed on the floor; e5_design §10.1). The joint sigma
set spans the full augmented state (§10.1).
"""
import sys
import numpy as np
import ukf_core as U
from measurement_models import N as NV, BG_SLICE, h_range, h_flow

VEH_ANG = (6, 7, 8)
CHOL_JITTER_LADDER = U.CHOL_JITTER_LADDER          # (0, 1e-12, 1e-9, 1e-6), e5_design §9
CHOL_STATS = {"calls": 0, "retry": 0, "eig_fallback": 0}
_wrap = U._wrap


def ang_indices(n_lm):
    """Angle-state indices for a state with n_lm landmarks in it."""
    return VEH_ANG + tuple(NV + 3 * k + 2 for k in range(n_lm))


# ---------- sigma points, mean, residual (ukf_core.py:61-106 with N -> n) ----------
def sigma_points(x, P, p):
    n = x.shape[0]
    lam = p['alpha']**2 * (n + p['kappa']) - n
    c = n + lam
    Psym = 0.5*(P + P.T)
    CHOL_STATS["calls"] += 1
    S = None
    for k, jit in enumerate(CHOL_JITTER_LADDER):
        try:
            S = np.linalg.cholesky(c * (Psym + jit*np.eye(n)) if jit else c * Psym)
        except np.linalg.LinAlgError:
            continue
        if k > 0:
            CHOL_STATS["retry"] += 1
            if CHOL_STATS["retry"] == 1:
                print(f"[ukf_lm] WARNING: Cholesky needed jitter {jit:g} (first fallback; counted in CHOL_STATS)",
                      file=sys.stderr)
        break
    if S is None:
        CHOL_STATS["eig_fallback"] += 1
        w, V = np.linalg.eigh(c * Psym)
        S = V @ np.diag(np.sqrt(np.clip(w, 1e-12, None)))
    sig = np.zeros((2*n+1, n)); sig[0] = x
    for i in range(n):
        sig[i+1] = x + S[:, i]
        sig[n+1+i] = x - S[:, i]
    Wm = np.full(2*n+1, 1.0/(2*c)); Wc = Wm.copy()
    Wm[0] = lam/c; Wc[0] = lam/c + (1 - p['alpha']**2 + p['beta'])
    return sig, Wm, Wc


def state_residual(a, b, ang):
    r = a - b
    for i in ang:
        r[i] = _wrap(r[i])
    return r


def state_mean(sig, Wm, ang):
    m = Wm @ sig
    for i in ang:                        # circular mean for angles
        m[i] = np.arctan2(Wm @ np.sin(sig[:, i]), Wm @ np.cos(sig[:, i]))
    return m


def _wrap_state(xn, ang):
    for i in ang:
        xn[i] = _wrap(xn[i])
    return xn


# ---------- predict (ukf_core.predict_rts, landmark rows identity, Q zero-padded) ----------
def _f(s, da, dv, dt):
    if s.shape[0] == NV:
        return U._process(s, da, dv, dt)
    return np.concatenate((U._process(s[:NV], da, dv, dt), s[NV:]))


def predict(x, P, da, dv, p, ang, dt=None):
    """Returns (x-, P-, D) with D = cov(x, x-) for the RTS smoother (as ukf_core.predict_rts)."""
    n = x.shape[0]
    sig, Wm, Wc = sigma_points(x, P, p)
    dt = p['dt'] if dt is None else dt
    fs = np.array([_f(s, da, dv, dt) for s in sig])
    xm = state_mean(fs, Wm, ang)
    if n == NV:
        Pm = p['Q'].copy()
    else:
        Pm = np.zeros((n, n)); Pm[:NV, :NV] = p['Q']
    D = np.zeros((n, n))
    for i in range(2*n+1):
        r = state_residual(fs[i], xm, ang)
        Pm += Wc[i]*np.outer(r, r)
        D += Wc[i]*np.outer(state_residual(sig[i], x, ang), r)
    return xm, 0.5*(Pm+Pm.T), D


# ---------- scalar gated update (ukf_core._update_scalar) ----------
def update_scalar(x, P, z, hfun, R_scalar, gate_c, p, ang):
    """1-D UKF update with the EKF3-style NIS gate. Returns (x, P, accepted, testRatio)."""
    n = x.shape[0]
    sig, Wm, Wc = sigma_points(x, P, p)
    Z = np.array([hfun(s) for s in sig])
    zpred = Wm @ Z
    dz = Z - zpred
    S = Wc @ (dz*dz) + R_scalar
    nu = z - zpred
    test = (nu*nu) / (gate_c * S)
    if test > 1.0 or not np.isfinite(test):
        return x, P, False, float(test)
    Pxz = np.zeros(n)
    for i in range(2*n+1):
        Pxz += Wc[i]*state_residual(sig[i], x, ang)*dz[i]
    K = Pxz / S
    xn = x + K*nu
    _wrap_state(xn, ang)
    Pn = P - np.outer(K, K)*S
    return xn, 0.5*(Pn+Pn.T), True, float(test)


def update_range(x, P, rng, p, ang):
    """ukf_core.update_range. Returns (x, P, accepted, testRatio or None if outside the valid window)."""
    if not (p['RNG_MIN'] <= rng <= p['RNG_MAX']) or not np.isfinite(rng):
        return x, P, False, None
    gate_c = (0.01*p['RNG_GATE'])**2
    return update_scalar(x, P, rng, lambda s: h_range(s)[0], p['RNG_M_NSE']**2, gate_c, p, ang)


def update_flow(x, P, flow_xy, omega_body, valid, inlier_ratio, p, ang):
    """ukf_core.update_flow. Returns (x, P, (acc_x, acc_y), (test_x, test_y)); tests None if pre-gate rejected."""
    if not valid or inlier_ratio <= 0.0:
        return x, P, (False, False), (None, None)
    if abs(flow_xy[0]) >= p['FLOW_MAX'] or abs(flow_xy[1]) >= p['FLOW_MAX']:
        return x, P, (False, False), (None, None)
    gate_c = (0.01*p['FLOW_GATE'])**2
    R_flow = p['FLOW_M_NSE']**2
    acc = [False, False]; tests = [None, None]
    for ax in (0, 1):
        x, P, a, tr = update_scalar(x, P, flow_xy[ax], lambda s, ax=ax: h_flow(s, omega_body)[ax], R_flow, gate_c, p, ang)
        acc[ax] = a; tests[ax] = tr
    return x, P, tuple(acc), tuple(tests)


def update_yaw_pseudo(x, P, p, ang):
    """ukf_core.update_yaw_pseudo (variance-gated zero-innovation yaw; used before the anchor only)."""
    n = x.shape[0]
    if P[6, 6] + P[7, 7] + P[8, 8] <= p['ATT_VAR_GATE']:
        return x, P, False
    sig, Wm, Wc = sigma_points(x, P, p)
    Zr = np.array([_wrap(s[8] - x[8]) for s in sig])
    zpred = Wm @ Zr
    S = Wc @ ((Zr - zpred)**2) + p['YAW_M_NSE']**2
    Pxz = np.zeros(n)
    for i in range(2*n+1):
        Pxz += Wc[i]*state_residual(sig[i], x, ang)*(Zr[i] - zpred)
    K = Pxz / S
    xn = x + K*(0.0 - zpred)
    _wrap_state(xn, ang)
    Pn = P - np.outer(K, K)*S
    return xn, 0.5*(Pn+Pn.T), True


# ---------- tag measurement: vehicle (x, y, yaw) in the landmark frame (e5_design §4) ----------
def _lm_of(s, lm):
    """Landmark pose (x, y, psi) for state/sigma vector s. lm = ('fixed', (x, y, psi)) or ('state', i0)."""
    if lm[0] == "fixed":
        return lm[1]
    i0 = lm[1]
    return s[i0], s[i0 + 1], s[i0 + 2]


def h_tag_rel(s, lm):
    """(h_x, h_y, h_psi): the FGO landmark factor's err + meas (lc_fgo_replay.py:132-135)."""
    xl, yl, pl = _lm_of(s, lm)
    c, sn = np.cos(pl), np.sin(pl)
    dx, dy = s[0] - xl, s[1] - yl
    return np.array([c*dx + sn*dy, -sn*dx + c*dy, _wrap(s[8] - pl)])


def update_heading_rel(x, P, z_psi, sigma, p, ang, lm):
    """Scalar yaw-in-landmark-frame update, h = wrap(psi_v - psi_L), in ukf_core.update_heading's relative form
    (sigma points taken relative to the mean relative yaw), NO gate. Returns (x, P)."""
    n = x.shape[0]
    sig, Wm, Wc = sigma_points(x, P, p)
    rel0 = x[8] - _lm_of(x, lm)[2]
    Zr = np.array([_wrap((s[8] - _lm_of(s, lm)[2]) - rel0) for s in sig])
    zpred = Wm @ Zr
    dz = Zr - zpred
    S = Wc @ (dz * dz) + sigma ** 2
    nu = _wrap(z_psi - rel0) - zpred
    Pxz = np.zeros(n)
    for i in range(2 * n + 1):
        Pxz += Wc[i] * state_residual(sig[i], x, ang) * dz[i]
    K = Pxz / S
    xn = x + K * nu
    _wrap_state(xn, ang)
    Pn = P - np.outer(K, K) * S
    return xn, 0.5 * (Pn + Pn.T)


def update_tag_rel(x, P, z, sig_pos, sig_yaw, p, ang, lm, mode="sequential"):
    """One tag detection z = (m_x, m_y, m_psi) against landmark lm. NO gate, no robust weighting (e5_design §4).
    mode "sequential" (DECIDED, §10.4): x, then y (scalar, R = sig_pos^2), then yaw (update_heading_rel), the tag-frame
    analogue of ukf_core.update_tag. mode "joint": one 3-D unscented update with the yaw innovation wrapped (the
    design's alternative; not used by any pre-registered run). Returns (x, P)."""
    if mode == "sequential":
        for i in (0, 1):
            x, P, _, _ = update_scalar(x, P, z[i], lambda s, i=i: h_tag_rel(s, lm)[i], sig_pos ** 2, np.inf, p, ang)
        return update_heading_rel(x, P, z[2], sig_yaw, p, ang, lm)
    if mode != "joint":
        raise ValueError(mode)
    n = x.shape[0]
    sig, Wm, Wc = sigma_points(x, P, p)
    rel0 = x[8] - _lm_of(x, lm)[2]
    Z = np.array([h_tag_rel(s, lm) for s in sig])
    Z[:, 2] = [_wrap((s[8] - _lm_of(s, lm)[2]) - rel0) for s in sig]
    zpred = Wm @ Z
    dz = Z - zpred
    S = (Wc[:, None] * dz).T @ dz + np.diag([sig_pos ** 2, sig_pos ** 2, sig_yaw ** 2])
    nu = np.array([z[0] - zpred[0], z[1] - zpred[1], _wrap(z[2] - rel0) - zpred[2]])
    Pxz = np.zeros((n, 3))
    for i in range(2 * n + 1):
        Pxz += Wc[i] * np.outer(state_residual(sig[i], x, ang), dz[i])
    K = np.linalg.solve(S.T, Pxz.T).T
    xn = x + K @ nu
    _wrap_state(xn, ang)
    Pn = P - K @ S @ K.T
    return xn, 0.5 * (Pn + Pn.T)


# ---------- augmentation and removal (e5_design §3, §6, §7) ----------
def inverse_tag(pv_x, pv_y, psi_v, m):
    """Landmark pose from a vehicle pose and a tag-relative measurement: lc_fgo_replay.lm_from (:153-155)."""
    psiL = _wrap(psi_v - m[2]); c, s = np.cos(psiL), np.sin(psiL)
    return np.array([pv_x - (c * m[0] - s * m[1]), pv_y - (s * m[0] + c * m[1]), psiL])


def augment_unscented(x, P, z, R_tag, p, ang):
    """First sighting of a non-gauge landmark (§3b): joint sigma set over [x; w], w ~ N(0, R_tag), pushed through
    g(x, w) = [x; inverse(x, z + w)]. The vehicle/existing block keeps (x, P) exactly (its unscented mean and covariance
    equal them in exact arithmetic: the transform is the identity there); P_LL and the cross block P_xL come from the
    sigma points (no Jacobian). The measurement is NOT fused again (§3c).
    Returns (x+, P+, D) with D = cov(x, x+) = [P, P_xL] for the RTS transition node."""
    n = x.shape[0]
    xa = np.concatenate((x, np.zeros(3)))
    Pa = np.zeros((n + 3, n + 3)); Pa[:n, :n] = P; Pa[n:, n:] = R_tag
    sig, Wm, Wc = sigma_points(xa, Pa, p)
    Ls = np.array([inverse_tag(s[0], s[1], s[8], np.asarray(z, float) + s[n:]) for s in sig])
    Lm = state_mean(Ls, Wm, (2,))
    PLL = np.zeros((3, 3)); PxL = np.zeros((n, 3))
    for i in range(2 * n + 7):
        rL = state_residual(Ls[i], Lm, (2,))
        PLL += Wc[i] * np.outer(rL, rL)
        PxL += Wc[i] * np.outer(state_residual(sig[i][:n], x, ang), rL)
    xn = np.concatenate((x, Lm))
    Pn = np.zeros((n + 3, n + 3)); Pn[:n, :n] = P; Pn[:n, n:] = PxL; Pn[n:, :n] = PxL.T; Pn[n:, n:] = 0.5 * (PLL + PLL.T)
    D = Pn[:n, :].copy()
    return xn, Pn, D


def augment_fixed(x, P, pose, var):
    """V-E5c: append a landmark AT a given pose with variance var (m^2, rad^2) and no cross-covariance.
    Returns (x+, P+, D)."""
    n = x.shape[0]
    xn = np.concatenate((x, np.asarray(pose, float)))
    Pn = np.zeros((n + 3, n + 3)); Pn[:n, :n] = P; Pn[n:, n:] = var * np.eye(3)
    return xn, Pn, Pn[:n, :].copy()


def remove_block(x, P, i0):
    """Marginalise the landmark block [i0, i0+3) out (no-LC finished pass, §6): a selection transition x+ = S x.
    Returns (x+, P+, D) with D = P S^T, P+ = S P S^T (symmetrised)."""
    keep = np.r_[0:i0, i0 + 3:x.shape[0]]
    Pn = P[np.ix_(keep, keep)]
    return x[keep].copy(), 0.5 * (Pn + Pn.T), P[:, keep].copy()


# ---------- RTS over a chain whose dimension changes (e5_design §7) ----------
def rts_backward(nodes, x_final, P_final, out_dims=NV):
    """Unscented RTS backward pass over a chain of transition nodes. Each node is a tuple
    (xf, Pf, ang_f, xp, Pp, D, ang_p): the filtered state BEFORE the transition (dim n_k, angle set ang_f), the
    transition's output (xp, Pp; dim n_{k+1}, angle set ang_p: a predict, an augmentation or a removal) and
    D = cov(xf, xp) (n_k x n_{k+1}). The filtered state that FOLLOWS node k (after its updates) is the xf of node
    k+1, or (x_final, P_final) after the last node. The gain G = D Pp^-1 is solved on the diagonally scaled matrix
    exactly as ukf_core.rts_smooth (ukf_core.py:177-180); x^s_k = xf + G (x^s_{k+1} [-] xp), P^s_k = Pf + G (P^s_{k+1}
    - Pp) G^T, with [-] wrapping ang_p and the result wrapping ang_f (ukf_core.py:181-184). At constant dimension this
    is ukf_core.rts_smooth line for line. Returns the smoothed xf[:out_dims] per node (list), plus the final."""
    xs_next, Ps_next = x_final, P_final
    out = [None] * len(nodes)
    for k in range(len(nodes) - 1, -1, -1):
        xf, Pf, ang_f, xp, Pp, D, ang_p = nodes[k]
        sc = np.sqrt(np.clip(np.diag(Pp), 1e-300, None))
        G = np.linalg.solve((Pp / np.outer(sc, sc)).T, (D / sc[None, :]).T).T / sc[None, :]
        xs = xf + G @ state_residual(xs_next, xp, ang_p)
        for j in ang_f:
            xs[j] = _wrap(xs[j])
        Ps = Pf + G @ (Ps_next - Pp) @ G.T
        out[k] = xs[:out_dims].copy()
        xs_next, Ps_next = xs, Ps
    return out, x_final[:out_dims].copy()
