#!/usr/bin/env python3
"""G3 (pre-registration §4): synthetic gates for ukf_ipls.py, run BEFORE any trial replay.

(a) LINEAR-GAUSSIAN: U._process with da == 0 every step is EXACTLY linear (roll/pitch/yaw
    and both bias blocks pass through _process unchanged; R stays the fixed initial rotation
    since _rotvec_to_R(0) == I exactly, so p/v are an exact linear map of the previous p/v/ba).
    U.h_range is already exactly linear (x[2] - 0.12). On this model, iteration 0 (the
    ukf_core.rts_smooth bypass) is ALREADY the exact Gaussian smoother -- there is zero
    linearisation error anywhere, by construction -- so a correctly-implemented IPLS
    iteration 1 must reproduce iteration 0 to numerical precision (<= 1e-9), and
    history[1]["max_change_m"] must be <= 1e-9. This is the pre-registered "converges in
    one iteration to the exact linear RTS" gate, exercised through the REAL ukf_ipls
    machinery (ipls_iteration/run_ipls), not a separate hand-rolled KF.
(b) NONLINEAR TOY: real U._process (nonzero da, genuine rotation) and U.h_flow (rotation-
    coupled), noiseless targets taken from a true trajectory, fixed before running (no
    randomness, no re-design after seeing the result). Checks only that the MAP cost
    (ukf_ipls.map_cost) does not increase between successive iterations.
Run: <venv-evo python> test_ipls_g3.py   (prints PASS/FAIL per sub-gate; exit 1 on any FAIL)
"""
import sys
import numpy as np
import ukf_core as U
import ukf_ipls as IPLS

FAILS = []


def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print(f"[{tag}] {name}" + (f" -- {detail}" if detail else ""))
    if not cond:
        FAILS.append(name)


def make_anchor():
    x = np.zeros(U.N)
    x[0:3] = [1.0, -0.5, 2.0]          # p_E, p_N, p_U
    x[3:6] = [0.1, -0.05, 0.0]         # v
    x[6:9] = [0.05, -0.03, 0.4]        # roll, pitch, yaw (rad) -- nonzero, fixed throughout (a)
    x[9:12] = [1e-5, -1e-5, 2e-5]      # gyro bias (delta form)
    x[12:15] = [1e-4, 1e-4, -1e-4]     # accel bias (delta form)
    P = np.diag([0.01, 0.01, 0.05,
                 0.01, 0.01, 0.01,
                 np.radians(2) ** 2, np.radians(2) ** 2, np.radians(5) ** 2,
                 1e-12, 1e-12, 1e-14,
                 1e-12, 1e-12, 1e-14])
    return x, P


# ---------------------------------------------------------------------------------------- G3(a)
def g3a():
    p = U.make_params(dt=0.0125)
    anchor_m, anchor_P = make_anchor()
    n = 6
    dv = np.array([0.02, -0.01, 0.005])         # constant per step -> time-invariant linear system
    predict_ops = [(np.zeros(3), dv.copy(), p['dt']) for _ in range(n)]

    # ground-truth NOISELESS trajectory (da == 0 keeps roll/pitch/yaw, R, bg, ba all fixed, so
    # p/v evolve by the EXACT closed-form linear recursion _process implements)
    true_states = [anchor_m.copy()]
    s = anchor_m.copy()
    for da, dv_, dt in predict_ops:
        s = U._process(s, da, dv_, dt)
        true_states.append(s.copy())

    # precondition check: _process really is affine on this input family (zero curvature) --
    # probe two points, confirm a THIRD point's output matches the affine combination
    rng = np.random.default_rng(0)
    da0 = np.zeros(3)
    x1 = anchor_m + rng.normal(scale=0.01, size=U.N) * (np.arange(U.N) < 6)   # perturb p,v only
    x2 = anchor_m + rng.normal(scale=0.01, size=U.N) * (np.arange(U.N) < 6)
    xm = 0.5 * (x1 + x2)
    f1, f2, fm = (U._process(xx, da0, dv, p['dt']) for xx in (x1, x2, xm))
    check("g3a precondition: U._process affine when da==0", np.allclose(fm, 0.5 * (f1 + f2), atol=1e-10),
          f"max diff {np.max(np.abs(fm - 0.5*(f1+f2))):.3e}")

    batch_ops = [[("rng", float(U.h_range(true_states[k + 1])[0]), 0.25, None)] for k in range(n)]

    Vs, Ps, history, converged = IPLS.run_ipls(anchor_m, anchor_P, predict_ops, batch_ops,
                                                *_fwd_arrays(anchor_m, anchor_P, predict_ops, batch_ops, p),
                                                p, max_iter=5, tol_m=1e-12)
    check("g3a: at least one iteration ran", len(history) >= 2, f"history has {len(history)} entries")
    # direct check against iteration 0's own trajectory, stored by run_ipls's bypass internally;
    # re-derive it identically here (same pure call) for the comparison
    XA, PA, XP, PP, DD = _fwd_arrays(anchor_m, anchor_P, predict_ops, batch_ops, p)
    xs0, _ = U.rts_smooth(XA, PA, XP, PP, DD)
    iter1_vs0 = np.max(np.abs(np.array(Vs[1:]) - xs0)) if converged or len(history) >= 2 else np.inf
    check("g3a: iteration >=1 reproduces iteration 0 (<= 1e-9)", iter1_vs0 <= 1e-9, f"max abs diff {iter1_vs0:.3e}")
    check("g3a: converges within 1 iteration (max_change_m <= 1e-9)",
          len(history) >= 2 and history[1]["max_change_m"] <= 1e-9,
          f"history[1]={history[1] if len(history) >= 2 else None}")


def _fwd_arrays(anchor_m, anchor_P, predict_ops, batch_ops, p):
    """Build the (XA, PA, XP, PP, DD) a real forward UKF pass over this exact operation
    sequence would produce, by literally running ukf_core.predict_rts/update_range/update_flow.

    A flow_x/flow_y pair recorded from the SAME /optical_flow/measurement message (as g3b
    constructs them: always adjacent, same aux/omega_body) MUST be replayed through ONE
    U.update_flow(x, P, [zx, zy], ...) call, exactly as room_ukf_ipls_replay.py's real
    recording loop does -- update_flow fuses BOTH axes per call (X then Y, sequentially on
    the SAME call), so replaying flow_x and flow_y as two SEPARATE update_flow calls (each
    padding the other axis with a fake 0.0) is not "the forward UKF": it fuses a bogus
    zero-flow measurement on the other axis each time. (Found 2026-11-22: this bug inflated
    g3b's iteration-0 cost to ~16226 instead of 0; fixed here, the toy itself unchanged.)"""
    n = len(predict_ops)
    x, P = anchor_m.copy(), anchor_P.copy()
    XA, PA, XP, PP, DD = [], [], [], [], []
    for k in range(n):
        da, dv, dt = predict_ops[k]
        x, P, Dk = U.predict_rts(x, P, da, dv, p, dt=dt)
        XP.append(x.copy()); PP.append(P.copy()); DD.append(Dk.copy())
        ops = batch_ops[k]
        i = 0
        while i < len(ops):
            kind, z, R, aux = ops[i]
            if kind == "rng":
                x, P, acc = U.update_range(x, P, z, p)
                assert acc, "g3 harness: rng unexpectedly rejected by the forward UKF"
                i += 1
            elif kind in ("flow_x", "flow_y"):
                zx = z if kind == "flow_x" else 0.0
                zy = z if kind == "flow_y" else 0.0
                want_x, want_y = kind == "flow_x", kind == "flow_y"
                j = i + 1
                if j < len(ops) and ops[j][0] in ("flow_x", "flow_y") and ops[j][0] != kind:
                    k2, z2, _, _ = ops[j]
                    if k2 == "flow_x":
                        zx, want_x = z2, True
                    else:
                        zy, want_y = z2, True
                    i = j + 1
                else:
                    i += 1
                x, P, acc = U.update_flow(x, P, np.array([zx, zy]), aux, True, 1.0, p)
                if want_x:
                    assert acc[0], "g3 harness: flow_x unexpectedly rejected by the forward UKF"
                if want_y:
                    assert acc[1], "g3 harness: flow_y unexpectedly rejected by the forward UKF"
            else:
                raise ValueError(kind)
        XA.append(x.copy()); PA.append(P.copy())
    return np.array(XA), np.array(PA), np.array(XP), np.array(PP), np.array(DD)


# ---------------------------------------------------------------------------------------- G3(b)
def g3b():
    p = U.make_params(dt=0.0125)
    anchor_m, anchor_P = make_anchor()
    n = 8
    da = np.array([0.001, -0.0005, 0.002]) * p['dt']   # small constant body rates -> genuine rotation
    dv = np.array([0.03, 0.0, -0.01])
    predict_ops = [(da.copy(), dv.copy(), p['dt']) for _ in range(n)]
    omega_body = da / p['dt']

    true_states = [anchor_m.copy()]
    s = anchor_m.copy()
    for da_, dv_, dt in predict_ops:
        s = U._process(s, da_, dv_, dt)
        true_states.append(s.copy())

    batch_ops = []
    for k in range(n):
        s = true_states[k + 1]
        fx, fy = U.h_flow(s, omega_body)
        batch_ops.append([("flow_x", float(fx), p['FLOW_M_NSE'] ** 2, omega_body.copy()),
                           ("flow_y", float(fy), p['FLOW_M_NSE'] ** 2, omega_body.copy()),
                           ("rng", float(U.h_range(s)[0]), p['RNG_M_NSE'] ** 2, None)])

    XA, PA, XP, PP, DD = _fwd_arrays(anchor_m, anchor_P, predict_ops, batch_ops, p)
    Vs, Ps, history, converged = IPLS.run_ipls(anchor_m, anchor_P, predict_ops, batch_ops,
                                                XA, PA, XP, PP, DD, p, max_iter=10, tol_m=1e-6)
    costs = [h["cost"] for h in history]
    non_increasing = all(costs[i + 1] <= costs[i] + 1e-9 for i in range(len(costs) - 1))
    check("g3b: cost does not increase across iterations", non_increasing, f"costs={costs}")
    check("g3b: at least 2 iterations observed", len(history) >= 2, f"{len(history)} entries")


if __name__ == "__main__":
    g3a()
    g3b()
    if FAILS:
        print(f"\nG3 FAILED: {FAILS}")
        sys.exit(1)
    print("\nG3: all sub-gates PASS")
