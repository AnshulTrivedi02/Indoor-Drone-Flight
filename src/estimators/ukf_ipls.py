"""Unscented iterated posterior linearisation smoother (IPLS) for the 15-state UKF.

Garcia-Fernandez, Svensson & Sarkka, "Iterated posterior linearization smoother",
IEEE TAC 2017. Pre-registered in docs/thesis/iterated_smoother/preregistration.md
(EXPLORATORY, decision D152). This module is PURE (numpy in, numpy out, no I/O);
the recording/replay harness is src/estimators/room_ukf_ipls_replay.py.

---------------------------------------------------------------------------------
THE CHAIN. From the re-anchor on, room_ukf_replay.py's forward pass is a sequence
of n predict steps (each ukf_core.predict_rts, inputs da/dv/dt) interleaved with
measurement updates (ukf_core.update_range / update_flow / update_tag /
update_yaw_pseudo). Define:
  V_0       = the state fed into the FIRST predict_rts call after re-anchor (FIXED:
              never re-estimated by this smoother, in any iteration -- there is no
              "node -1" to smooth, matching ukf_core.rts_smooth's own convention
              that D[0]/Pp[0] are recorded by room_ukf_replay.py but never read by
              the backward pass). This is room_ukf_replay.py's own xa[0] (raw), NOT
              simply "immediately after re-anchor": any range/flow/tag update that
              lands between the re-anchor event and that first predict runs through
              the ordinary forward code path exactly like any other update (the
              anchor-vs-first-predict ordering is a property of the bag's own event
              timing, not controlled), so V_0 already bakes those updates in. They
              are therefore NOT recorded as ops (nothing to re-linearise: they sit
              inside the fixed V_0, never iterated) -- see
              room_ukf_ipls_replay.py's `chain_started` guard.
  V_{k+1}   = the filtered state after predict step k (0-indexed, k=0..n-1) AND
              every measurement update that follows it, up to (not including) the
              next predict -- i.e. V_{k+1} is exactly room_ukf_replay.py's XA[k],
              and node_t[k] is V_{k+1}'s time. V_1..V_n are the rows ukf_rts.tum
              carries; V_0 is never written (same row count as the stored file).

LINEARISATION POINT (the ambiguity the pre-registration explicitly flags, resolved
here, ONE call per predict and ONE call per accepted measurement, exactly as
pre-registered -- "every predict step ... and every measurement update ... about
the smoothed marginal at that step"):
  * Predict step k (maps V_k -> V_{k+1}'s PRIOR) is linearised by unscented SLR
    about the iteration-(j-1) smoothed marginal of V_k -- i.e. about the state the
    predict step actually READS. (For k=0 this is the fixed V_0, every iteration.)
  * Every measurement update belonging to node k+1 (the scalars that turn the
    prior into V_{k+1}: range, each flow axis, each tag component, the pseudo-yaw
    cap) is linearised by unscented SLR about the SAME point -- the iteration-(j-1)
    smoothed marginal of V_{k+1}, the state the update actually CONDITIONS. All
    measurements belonging to one node therefore share one reference point (there
    is exactly one smoothed marginal per node; room_ukf_replay.py does not record
    a marginal between e.g. the flow_x and flow_y sub-updates of the same node,
    so none is invented here). This is the standard IPLS formulation (one joint
    measurement per node, here applied as independent per-axis SLRs about that
    same node's reference, each then run as its own linear Kalman update in
    forward-pass order) -- a deliberate, documented simplification of "every
    measurement update ... about the smoothed marginal at that step" down to
    "about that step's node", since no finer-grained smoothed marginal exists.
    This does NOT reproduce the forward UKF's own intra-node sequential
    re-linearisation (see ITERATION 0 below for why that does not matter).

ITERATION 0 is NOT built from this machinery. ukf_core.rts_smooth, given the
EXACT recorded forward-pass arrays (XA, PA, XP, PP, DD -- the same arrays
room_ukf_replay.py builds), reproduces the stored ukf_rts.tum bitwise BY
CONSTRUCTION (same function, same inputs). Iteration 0 is exactly that call.
"The forward UKF's own linearisation" (pre-registration) is therefore not
something this module re-derives -- it is the existing recorded Jacobian-like
fit ukf_core.predict_rts/_update_scalar already computed, reused verbatim. This
is also why the per-node (not per-sub-step) reference point for j>=1 above is
harmless: it only ever applies from iteration 1 on, where IPLS is already an
approximation to the smoothing posterior, not an identity.

PSEUDO-YAW / TAG-YAW PIVOT. ukf_core.update_yaw_pseudo and update_heading both
take sigma points relative to the CURRENT mean's own yaw (to keep the spread
small and avoid wrap ambiguity), not an absolute target. Reproduced here as
h(x) = wrap(x[8] - ref_m[8]) (pivot = the SLR reference's own yaw, i.e.
self-referential, not a value frozen from the forward pass): for update_tag's
yaw sub-update the frozen absolute reading z=psi gives target = wrap(psi-pivot);
for the pseudo-yaw cap the frozen target is z=0 exactly (a zero-innovation
regulariser, not evidence about the world -- the EKF3 mechanism it mirrors, see
ukf_core.update_yaw_pseudo's docstring). Every other frozen measurement input
(range value, flow_xy + omega_body after ground-proximity replacement, tag
E/N/yaw) is recorded from the forward pass and never recomputed.

GATES. accept/reject decisions (flow per-axis, range) are taken from the forward
pass and frozen: a rejected scalar never appears in an iteration's operation
list, in any iteration (no re-gating).

SLR mechanics: same ukf_core._sigma_points (same alpha/beta/kappa from
ukf_core.make_params) and the same correlation-scaled linear solve
ukf_core.rts_smooth uses (bias-state variances ~1e-14 against yaw ~1 -- see
ukf_core.rts_smooth's own comment on why the unscaled solve is unusable).

COST (pre-registration: "sum of squared whitened residuals"; the MAP objective
at the smoothed means, nonlinear f/h, UN-inflated Q/R -- no linearisation-error
term, i.e. not the Ω/Qtot/Rtot used for the Kalman gains during an iteration):
  cost = _state_residual(V_0, V_0)^T P_anchor^-1 (...)            [formally 0]
       + sum_k  _state_residual(V_{k+1}, process(V_k))^T Q^-1 (...)
       + sum over accepted scalars  (z - h_nonlinear(V_node))^2 / R
  (the pseudo-yaw cap contributes exactly 0: its own h is defined relative to the
  evaluation point's own yaw, so z - h = 0 identically, included for uniformity
  rather than special-cased out).

  AMBIGUITY, not resolved here (report it; do not pick a definition after seeing a
  result): the pre-registration says "cost = sum of squared whitened residuals" but
  does not say against WHICH point. This module uses the MAP objective at the
  smoothed means with the EXACT nonlinear f/h (above). IPLS's own fixed point is not
  generally the MAP point -- unscented SLR propagates E[f(x)], not f(E[x]), so even a
  converged IPLS run can sit at a nonzero MAP cost (observed on the G3(b) toy: the
  smoothed trajectory converges cleanly, iteration-to-iteration changes shrinking by
  orders of magnitude, to a MAP cost of ~0.44 while the true generating trajectory's
  MAP cost is 0). A different "cost" -- e.g. the whitened residuals of the LINEARISED
  model actually used for that iteration's Kalman updates (H/A, Qtot/Rtot), which IS
  what IPLS's forward/backward recursion itself is consistent with -- could behave
  differently (e.g. be guaranteed non-increasing, as in ordinary Gauss-Newton on its
  own linearised subproblem). This module does not implement that alternative; it is
  flagged here as a pre-registration ambiguity for its owner to rule on.

STOPPING (pre-registered): iterate until the largest change in smoothed
horizontal position (V_1..V_n only; V_0 never moves) between successive
iterations is < 1 mm, or 10 iterations, whichever first. A cost increase or a
non-converged run is reported, never damped or re-run with different settings.
"""
import numpy as np
import ukf_core as U


def _solve_sym(P, B):
    """inv(P) @ B via the SAME correlation-scaled solve as ukf_core.rts_smooth's gain
    (P's diagonal spans ~1e-14, delta-form bias states, to ~1, yaw/position -- the
    unscaled solve is ill-conditioned). B: (N,) vector or (N, M) matrix."""
    sc = np.sqrt(np.clip(np.diag(P), 1e-300, None))
    Pc = P / np.outer(sc, sc)
    if B.ndim == 1:
        return np.linalg.solve(Pc, B / sc) / sc
    return np.linalg.solve(Pc, B / sc[:, None]) / sc[:, None]


def slr_process(ref_m, ref_P, da, dv, dt, p):
    """Unscented SLR of x_{k+1} = ukf_core._process(x_k, da, dv, dt) about N(ref_m, ref_P).
    Returns (A, ybar, D, Qlin) s.t. ybar + A @ state_residual(x, ref_m) ~= _process(x, ...).
    D = Cov(x_k, x_{k+1}), the SAME cross-covariance ukf_core.predict_rts computes (D).
    Qlin = the linearisation-error covariance (module docstring)."""
    sig, Wm, Wc = U._sigma_points(ref_m, ref_P, p)
    fs = np.array([U._process(s, da, dv, dt) for s in sig])
    ybar = U._state_mean(fs, Wm)
    Pyy = np.zeros((U.N, U.N))
    D = np.zeros((U.N, U.N))
    for i in range(len(Wc)):
        rin = U._state_residual(sig[i], ref_m)
        rout = U._state_residual(fs[i], ybar)
        Pyy += Wc[i] * np.outer(rout, rout)
        D += Wc[i] * np.outer(rin, rout)
    A = _solve_sym(ref_P, D).T
    Qlin = Pyy - A @ D                      # == Pyy - A @ ref_P @ A.T (D == ref_P @ A.T exactly)
    return A, ybar, D, 0.5 * (Qlin + Qlin.T)


def slr_measure(ref_m, ref_P, p, hfun):
    """Unscented SLR of a SCALAR z = hfun(x) about N(ref_m, ref_P). hfun(sigma_row) -> float
    (already pivoted/wrapped by the caller for an angle measurement -- module docstring).
    Returns (H, hbar, Pxz, Rlin) s.t. hbar + H @ state_residual(x, ref_m) ~= hfun(x)."""
    sig, Wm, Wc = U._sigma_points(ref_m, ref_P, p)
    Z = np.array([hfun(s) for s in sig])
    hbar = Wm @ Z
    Pzz = 0.0
    Pxz = np.zeros(U.N)
    for i in range(len(Wc)):
        rin = U._state_residual(sig[i], ref_m)
        dz = Z[i] - hbar
        Pzz += Wc[i] * dz * dz
        Pxz += Wc[i] * rin * dz
    H = _solve_sym(ref_P, Pxz)
    Rlin = Pzz - H @ Pxz                    # == Pzz - H @ ref_P @ H (Pxz == ref_P @ H exactly)
    return H, hbar, Pxz, float(Rlin)


def _hfun_for(op, ref_m):
    """One recorded measurement op -> (hfun, target, R, is_angle) for slr_measure + the
    generic linear update below. op = (kind, z, R, aux); aux = omega_body for flow, else None."""
    kind, z, R, aux = op
    if kind == "rng":
        return (lambda s: U.h_range(s)[0]), float(z), R, False
    if kind == "flow_x":
        return (lambda s: U.h_flow(s, aux)[0]), float(z), R, False
    if kind == "flow_y":
        return (lambda s: U.h_flow(s, aux)[1]), float(z), R, False
    if kind == "tag_pE":
        return (lambda s: s[0]), float(z), R, False
    if kind == "tag_pN":
        return (lambda s: s[1]), float(z), R, False
    if kind == "tag_yaw":
        piv = ref_m[8]
        return (lambda s, piv=piv: U._wrap(s[8] - piv)), float(U._wrap(z - piv)), R, True
    if kind == "pseudo_yaw":
        piv = ref_m[8]
        return (lambda s, piv=piv: U._wrap(s[8] - piv)), 0.0, R, True
    raise ValueError(f"unknown op kind {kind!r}")


def ipls_iteration(anchor_m, anchor_P, predict_ops, batch_ops, Vs_prev, Ps_prev, p):
    """One IPLS forward (linear KF) + backward (ukf_core.rts_smooth) pass, iteration j>=1.

    predict_ops: list of (da, dv, dt), length n. batch_ops: list of op-lists, length n;
    batch_ops[k] = the accepted measurement ops belonging to V_{k+1} (module docstring).
    Vs_prev/Ps_prev: length n+1, index 0 = anchor_m/anchor_P (always), index k = the
    iteration-(j-1) smoothed marginal of V_k.
    Returns (Vs_new, Ps_new) of the same length n+1 (index 0 unchanged), plus the raw
    (XA, PA, XP, PP, DD) arrays for diagnostics."""
    n = len(predict_ops)
    m, P = anchor_m.copy(), anchor_P.copy()
    XA, PA, XP, PP, DD = [], [], [], [], []
    for k in range(n):
        da, dv, dt = predict_ops[k]
        A, ybar, D, Qlin = slr_process(Vs_prev[k], Ps_prev[k], da, dv, dt, p)
        dev = U._state_residual(m, Vs_prev[k])
        m_pred = ybar + A @ dev
        m_pred[6], m_pred[7], m_pred[8] = U._wrap(m_pred[6]), U._wrap(m_pred[7]), U._wrap(m_pred[8])
        P_pred = A @ P @ A.T + (p['Q'] + Qlin)
        P_pred = 0.5 * (P_pred + P_pred.T)
        Dfwd = P @ A.T                      # forward cross-cov Cov(V_k_this_iter, V_{k+1}_prior_this_iter)
        XP.append(m_pred.copy()); PP.append(P_pred.copy()); DD.append(Dfwd.copy())
        m, P = m_pred, P_pred
        ref_node, Pref_node = Vs_prev[k + 1], Ps_prev[k + 1]
        for op in batch_ops[k]:
            hfun, target, Rmeas, angle = _hfun_for(op, ref_node)
            H, hbar, Pxz, Rlin = slr_measure(ref_node, Pref_node, p, hfun)
            Rtot = Rmeas + Rlin
            dev2 = U._state_residual(m, ref_node)
            hpred = hbar + H @ dev2
            nu = target - hpred
            if angle:
                nu = U._wrap(nu)
            S = H @ P @ H + Rtot
            K = (P @ H) / S
            m = m + K * nu
            m[6], m[7], m[8] = U._wrap(m[6]), U._wrap(m[7]), U._wrap(m[8])
            P = P - np.outer(K, K) * S
            P = 0.5 * (P + P.T)
        XA.append(m.copy()); PA.append(P.copy())
    XA, PA = np.array(XA), np.array(PA)
    XP, PP, DD = np.array(XP), np.array(PP), np.array(DD)
    xs, Ps = U.rts_smooth(XA, PA, XP, PP, DD)
    Vs_new = [anchor_m.copy()] + list(xs)
    Ps_new = [anchor_P.copy()] + list(Ps)
    return Vs_new, Ps_new, (XA, PA, XP, PP, DD)


def max_horizontal_change(Vs_a, Vs_b):
    """Max hypot(d p_E, d p_N) over V_1..V_n (V_0 is fixed, excluded)."""
    A = np.array(Vs_a[1:]); B = np.array(Vs_b[1:])
    d = A[:, :2] - B[:, :2]
    return float(np.max(np.hypot(d[:, 0], d[:, 1]))) if len(d) else 0.0


def map_cost(Vs, anchor_m, anchor_P, predict_ops, batch_ops, p):
    """MAP objective at the smoothed means, nonlinear f/h, un-inflated Q/R (module docstring)."""
    dev0 = U._state_residual(Vs[0], anchor_m)
    cost = float(dev0 @ _solve_sym(anchor_P, dev0))
    n = len(predict_ops)
    for k in range(n):
        da, dv, dt = predict_ops[k]
        pred = U._process(Vs[k], da, dv, dt)
        r = U._state_residual(Vs[k + 1], pred)
        cost += float(r @ _solve_sym(p['Q'], r))
        s = Vs[k + 1]
        for op in batch_ops[k]:
            kind, z, R, aux = op
            if kind == "rng":
                res = z - U.h_range(s)[0]
            elif kind == "flow_x":
                res = z - U.h_flow(s, aux)[0]
            elif kind == "flow_y":
                res = z - U.h_flow(s, aux)[1]
            elif kind == "tag_pE":
                res = z - s[0]
            elif kind == "tag_pN":
                res = z - s[1]
            elif kind == "tag_yaw":
                res = U._wrap(z - s[8])
            elif kind == "pseudo_yaw":
                res = 0.0        # zero-innovation regulariser about its own evaluation point: no MAP evidence
            else:
                raise ValueError(f"unknown op kind {kind!r}")
            cost += float(res * res / R)
    return cost


def run_ipls(anchor_m, anchor_P, predict_ops, batch_ops, XA_fwd, PA_fwd, XP_fwd, PP_fwd, DD_fwd,
             p, max_iter=10, tol_m=1e-3):
    """Full IPLS run. Iteration 0 = ukf_core.rts_smooth on the RECORDED forward-pass arrays
    (bitwise == the stored ukf_rts.tum; module docstring). Iterations 1..max_iter use
    ipls_iteration. Stops on max_horizontal_change < tol_m (default 1 mm) or max_iter.
    Returns (Vs_final, Ps_final, history, converged); history[0] is iteration 0 (no
    max_change_m: there is no iteration -1 to compare against)."""
    xs0, Ps0 = U.rts_smooth(XA_fwd, PA_fwd, XP_fwd, PP_fwd, DD_fwd)
    Vs = [anchor_m.copy()] + list(xs0)
    Ps = [anchor_P.copy()] + list(Ps0)
    history = [{"iter": 0, "cost": map_cost(Vs, anchor_m, anchor_P, predict_ops, batch_ops, p),
                "max_change_m": None, "chol_calls": None, "chol_retry": None, "chol_eig_fallback": None}]
    converged = False
    for j in range(1, max_iter + 1):
        c0 = dict(U.CHOL_STATS)
        Vs_new, Ps_new, _ = ipls_iteration(anchor_m, anchor_P, predict_ops, batch_ops, Vs, Ps, p)
        c1 = dict(U.CHOL_STATS)
        chg = max_horizontal_change(Vs, Vs_new)
        cst = map_cost(Vs_new, anchor_m, anchor_P, predict_ops, batch_ops, p)
        history.append({"iter": j, "cost": cst, "max_change_m": chg,
                         "chol_calls": c1["calls"] - c0["calls"],
                         "chol_retry": c1["retry"] - c0["retry"],
                         "chol_eig_fallback": c1["eig_fallback"] - c0["eig_fallback"]})
        Vs, Ps = Vs_new, Ps_new
        if chg < tol_m:
            converged = True
            break
    return Vs, Ps, history, converged
