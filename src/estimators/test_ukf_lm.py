#!/usr/bin/env python3
"""Synthetic unit tests for the E5 landmark UKF (ukf_lm.py), its harness book-keeping (lc_ukf_replay.py) and the V-E5
comparator (eval/e5_val_compare.py). docs/thesis/tier1/e5_design.md §1, §11. No bag, no replay, no simulator: synthetic
data only, a few seconds in total. Plain asserts (no pytest on this machine).
Usage (~/venv-evo): python3 src/estimators/test_ukf_lm.py"""
import os, sys, math, tempfile, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (HERE, os.path.join(HERE, "fgo"), os.path.join(HERE, "..", "tags"), os.path.join(HERE, "..", "..", "eval")):
    sys.path.insert(0, _p)
import ukf_core as U
import ukf_lm as LM
import lc_ukf_replay as R
import e5_val_compare as C
from measurement_models import h_flow, N as NV, TAG_SIGMA_POS, TAG_SIGMA_YAW

DT = 0.015
P_ = U.make_params(dt=DT)
RTAG = np.diag([TAG_SIGMA_POS ** 2, TAG_SIGMA_POS ** 2, TAG_SIGMA_YAW ** 2])


def eq(a, b, what):
    assert np.array_equal(np.asarray(a), np.asarray(b)), f"{what}: not bit-identical (max |d| {np.max(np.abs(np.asarray(a) - np.asarray(b)))})"


def init():
    x, P = U.init_state(np.array([0.02, -0.01, 9.81]), 1.88, dt=DT)
    x[3:6] = [0.3, 0.4, 0.0]; x[8] = 0.6
    return x, P


def imu(rng):
    da = 1e-3 * rng.normal(size=3)
    dv = np.array([0.0, 0.0, 9.80665 * DT]) + 2e-3 * rng.normal(size=3)
    return da, dv


# ------------------------------------------------------------------ test 1
def test_n15_bit_identical_to_ukf_core():
    """With no landmark in the state, ukf_lm's predict, range, flow, pseudo-yaw, tag (fixed landmark at the origin with
    yaw 0) and RTS equal ukf_core's BIT FOR BIT on a synthetic sequence."""
    rng = np.random.default_rng(0)
    xc, Pc = init(); xl, Pl = xc.copy(), Pc.copy(); ang = LM.ang_indices(0)
    xa, Pa, xp, Pp, Dc, nodes = [], [], [], [], [], []
    n_acc = n_rej = n_yaw = 0
    for k in range(160):
        da, dv = imu(rng)
        xa.append(xc.copy()); Pa.append(Pc.copy())
        xc2, Pc2, D2 = U.predict_rts(xc, Pc, da, dv, P_, dt=DT)
        xq, Pq = U.predict(xc, Pc, da, dv, P_, dt=DT)
        eq(xc2, xq, "predict vs predict_rts mean"); eq(Pc2, Pq, "predict vs predict_rts cov")
        xl2, Pl2, Dl2 = LM.predict(xl, Pl, da, dv, P_, ang, dt=DT)
        eq(xl2, xc2, "predict mean"); eq(Pl2, Pc2, "predict cov"); eq(Dl2, D2, "predict cross-cov")
        nodes.append((xl.copy(), Pl.copy(), ang, xl2.copy(), Pl2.copy(), Dl2.copy(), ang))
        xp.append(xc2.copy()); Pp.append(Pc2.copy()); Dc.append(D2)
        xc, Pc, xl, Pl = xc2, Pc2, xl2, Pl2
        if k % 2 == 0:
            r = 1.88 + 0.05 * rng.normal() + (0.0 if k % 10 else 10.0)   # every 5th range is an outlier (gate)
            xc, Pc, a1 = U.update_range(xc, Pc, r, P_)
            xl, Pl, a2, tr = LM.update_range(xl, Pl, r, P_, ang)
            assert a1 == a2; n_acc += a1; n_rej += (not a1)
            eq(xl, xc, "range mean"); eq(Pl, Pc, "range cov")
        if k % 3 == 0:
            om = 0.05 * rng.normal(size=3); fxy = h_flow(xc, om) + 0.05 * rng.normal(size=2)
            if k % 9 == 0:
                fxy = fxy + np.array([1.2, 0.0])                         # X-axis gate rejection
            xc, Pc, a1 = U.update_flow(xc, Pc, fxy, om, True, 0.9, P_)
            xl, Pl, a2, trs = LM.update_flow(xl, Pl, fxy, om, True, 0.9, P_, ang)
            assert tuple(a1) == tuple(a2) and trs[0] is not None
            eq(xl, xc, "flow mean"); eq(Pl, Pc, "flow cov")
        if k % 7 == 0:
            Pc = Pc.copy(); Pc[8, 8] += 0.05; Pl = Pl.copy(); Pl[8, 8] += 0.05   # push the attitude trace over 0.04
            xc, Pc, f1 = U.update_yaw_pseudo(xc, Pc, P_)
            xl, Pl, f2 = LM.update_yaw_pseudo(xl, Pl, P_, ang)
            assert f1 and f2; n_yaw += 1
            eq(xl, xc, "pseudo-yaw mean"); eq(Pl, Pc, "pseudo-yaw cov")
        if k % 11 == 5:
            z = (xc[0] + 0.03, xc[1] - 0.02, float(U._wrap(xc[8] + 0.04)))
            xc, Pc = U.update_tag(xc, Pc, z, TAG_SIGMA_POS, TAG_SIGMA_YAW, P_)
            xl, Pl = LM.update_tag_rel(xl, Pl, z, TAG_SIGMA_POS, TAG_SIGMA_YAW, P_, ang, ("fixed", (0.0, 0.0, 0.0)))
            eq(xl, xc, "tag (origin) mean"); eq(Pl, Pc, "tag (origin) cov")
    assert n_acc > 0 and n_rej > 0, (n_acc, n_rej)
    # RTS: room_ukf_replay's convention (node i = xa[i+1]) against the generic backward pass
    XA = np.array(xa[1:] + [xc]); PA = np.array(Pa[1:] + [Pc])
    xs, _ = U.rts_smooth(XA, PA, np.array(xp), np.array(Pp), np.array(Dc))
    out, xfin = LM.rts_backward(nodes, xl, Pl)
    for i in range(len(xs) - 1):
        eq(out[i + 1], xs[i], f"RTS node {i}")
    eq(xfin, xs[-1], "RTS final")
    print(f"test 1  n=15 bit-identical to ukf_core: 160 predicts, range {n_acc} acc / {n_rej} rej, {n_yaw} pseudo-yaw, "
          f"tags, RTS over {len(xs)} nodes  OK")


def test_known_map_rotated_equals_world():
    """V-E5b premise: the tag-frame sequential update against a FIXED landmark at a general map pose equals
    ukf_core.update_tag in the world frame up to round-off (linear in the state: the UT is exact; <= 1e-8 m)."""
    rng = np.random.default_rng(1)
    worst = 0.0
    for trial in range(20):
        x, P = init(); x[0], x[1] = rng.normal(size=2) * 3
        tag = {"p": np.array([rng.uniform(-3, 3), rng.uniform(-3, 3), 0.001]), "yaw": rng.uniform(-math.pi, math.pi)}
        z_w = (x[0] + 0.04 * rng.normal(), x[1] + 0.04 * rng.normal(), float(U._wrap(x[8] + 0.05 * rng.normal())))
        xc, Pc = U.update_tag(x.copy(), P.copy(), z_w, TAG_SIGMA_POS, TAG_SIGMA_YAW, P_)
        z_r = R.world_to_tagrel(*z_w, tag)
        xl, Pl = LM.update_tag_rel(x.copy(), P.copy(), z_r, TAG_SIGMA_POS, TAG_SIGMA_YAW, P_, LM.ang_indices(0),
                                   ("fixed", (tag["p"][0], tag["p"][1], tag["yaw"])))
        worst = max(worst, np.abs(xl - xc).max(), np.abs(Pl - Pc).max())
        # the design's alternative (joint 3-D update, not used by any pre-registered run): x, y are linear, so it
        # matches in position; yaw differs only through the sigma-point redraw (second order)
        xj, Pj = LM.update_tag_rel(x.copy(), P.copy(), z_r, TAG_SIGMA_POS, TAG_SIGMA_YAW, P_, LM.ang_indices(0),
                                   ("fixed", (tag["p"][0], tag["p"][1], tag["yaw"])), mode="joint")
        assert np.abs(xj[:2] - xc[:2]).max() < 1e-6 and abs(U._wrap(xj[8] - xc[8])) < 1e-6, (xj[:2] - xc[:2], xj[8] - xc[8])
    # round-off only: with alpha = 1e-3 the UT mean weight Wm[0] is about -1e6, so zpred = Wm @ Z carries about
    # 1e6 x 1e-16 x |h| (metres) of cancellation error, in both frames, differently: about 1e-9 m, 6 orders below 1 mm
    assert worst < 1e-8, worst
    print(f"test 1b known-map tag-frame update == world update to {worst:.1e}  OK")


# ------------------------------------------------------------------ test 2
def test_augmentation_shapes_and_crosscov():
    rng = np.random.default_rng(2)
    x, P = init(); ang = LM.ang_indices(0)
    for _ in range(5):
        x, P, _ = LM.predict(x, P, *imu(rng), P_, ang, dt=DT)
    z = (0.7, -0.4, 0.3)
    xn, Pn, D = LM.augment_unscented(x, P, z, RTAG, P_, ang)
    assert xn.shape == (NV + 3,) and Pn.shape == (NV + 3, NV + 3) and D.shape == (NV, NV + 3)
    eq(xn[:NV], x, "vehicle block mean kept"); eq(Pn[:NV, :NV], P, "vehicle block cov kept"); eq(D[:, :NV], P, "D = [P, PxL]")
    assert np.allclose(Pn, Pn.T, atol=0) and np.linalg.eigvalsh(Pn).min() > 0
    # Monte Carlo reference for the unscented augmentation: L = g(x, w), x ~ N(x, P), w ~ N(0, R_tag). The UT mean
    # carries the second-order term (E cos(psi + d) = cos psi (1 - s^2/2)): a few mm here, which the inverse model at the
    # mean (the FGO's initial VALUE, lc_fgo_replay.py:255) does not.
    mc = np.random.default_rng(22); Nmc = 200_000
    xs_ = mc.multivariate_normal(x, 0.5 * (P + P.T), size=Nmc, method="eigh"); ws_ = mc.multivariate_normal(np.zeros(3), RTAG, size=Nmc)
    psiL = U._wrap(xs_[:, 8] - (z[2] + ws_[:, 2])); mxw, myw = z[0] + ws_[:, 0], z[1] + ws_[:, 1]
    Ls_ = np.c_[xs_[:, 0] - (np.cos(psiL) * mxw - np.sin(psiL) * myw), xs_[:, 1] - (np.sin(psiL) * mxw + np.cos(psiL) * myw), psiL]
    Lmc = Ls_.mean(0); Lmc[2] = math.atan2(np.sin(psiL).mean(), np.cos(psiL).mean())
    dL = Ls_ - Lmc; dL[:, 2] = U._wrap(dL[:, 2]); PLL_mc = dL.T @ dL / Nmc; PxL_mc = (xs_ - x).T @ dL / Nmc
    assert np.abs(xn[NV:] - Lmc).max() < 5e-4, (xn[NV:], Lmc)
    rel = lambda a, b: np.abs(a - b).max() / np.abs(b).max()
    assert rel(Pn[NV:, NV:], PLL_mc) < 0.02 and rel(Pn[:NV, NV:][[0, 1, 8]], PxL_mc[[0, 1, 8]]) < 0.02, \
        (rel(Pn[NV:, NV:], PLL_mc), rel(Pn[:NV, NV:][[0, 1, 8]], PxL_mc[[0, 1, 8]]))
    shift = np.abs(xn[NV:NV + 2] - LM.inverse_tag(x[0], x[1], x[8], z)[:2]).max()
    assert np.abs(Pn[:NV, NV:]).max() > 1e-4                              # a real cross-covariance (vehicle x, y, yaw)
    # second landmark and an update against the first: shapes, angle set
    ang1 = LM.ang_indices(1); assert ang1 == (6, 7, 8, NV + 2)
    x2, P2, D2 = LM.augment_unscented(xn, Pn, (-0.5, 0.9, -1.0), RTAG, P_, ang1)
    assert x2.shape == (NV + 6,) and D2.shape == (NV + 3, NV + 6)
    eq(P2[:NV + 3, :NV + 3], Pn, "existing block kept on 2nd augmentation")
    x3, P3 = LM.update_tag_rel(x2, P2, (0.68, -0.41, 0.31), TAG_SIGMA_POS, TAG_SIGMA_YAW, P_, LM.ang_indices(2), ("state", NV))
    assert x3.shape == x2.shape and P3.shape == P2.shape
    assert np.trace(P3[NV:NV + 3, NV:NV + 3]) < np.trace(P2[NV:NV + 3, NV:NV + 3])
    # V-E5c augmentation at a fixed pose: no cross-covariance, the stated variance
    xf, Pf, Df = LM.augment_fixed(x, P, (1.0, 2.0, 0.5), 1e-10)
    assert np.all(Pf[:NV, NV:] == 0) and np.allclose(np.diag(Pf)[NV:], 1e-10) and Df.shape == (NV, NV + 3)
    print(f"test 2  augmentation: shapes, kept vehicle block, mean/PLL/PxL vs Monte Carlo (2e5; <2% rel), UT mean - inverse-at-mean {shift*1e3:.1f} mm, 2nd landmark  OK")


def test_augmented_known_map_close_to_fixed():
    """V-E5c premise: a landmark augmented AT the map pose with variance 1e-10 gives the same vehicle estimate as the
    fixed landmark, far below 1 um."""
    rng = np.random.default_rng(3)
    x, P = init(); tag = (1.5, -2.0, 0.8)
    xf, Pf = x.copy(), P.copy()
    xa, Pa, _ = LM.augment_fixed(x, P, tag, 1e-10)
    worst = 0.0
    for k in range(60):
        da, dv = imu(rng)
        xf, Pf, _ = LM.predict(xf, Pf, da, dv, P_, LM.ang_indices(0), dt=DT)
        xa, Pa, _ = LM.predict(xa, Pa, da, dv, P_, LM.ang_indices(1), dt=DT)
        if k % 5 == 0:
            zw = (xf[0] + 0.02, xf[1] - 0.01, float(U._wrap(xf[8] + 0.02)))
            zr = R.world_to_tagrel(*zw, {"p": np.array(tag[:2] + (0.0,)), "yaw": tag[2]})
            xf, Pf = LM.update_tag_rel(xf, Pf, zr, TAG_SIGMA_POS, TAG_SIGMA_YAW, P_, LM.ang_indices(0), ("fixed", tag))
            xa, Pa = LM.update_tag_rel(xa, Pa, zr, TAG_SIGMA_POS, TAG_SIGMA_YAW, P_, LM.ang_indices(1), ("state", NV))
        worst = max(worst, np.hypot(*(xa[:2] - xf[:2])))
    assert worst < 1e-6, worst
    print(f"test 2b augmented-at-map (1e-10) vs fixed landmark: max horizontal difference {worst:.1e} m  OK")


# ------------------------------------------------------------------ test 3
def test_landmark_yaw_wrapping():
    # circular mean across +-pi
    sig = np.zeros((3, NV + 3)); sig[:, NV + 2] = [math.pi - 0.01, -math.pi + 0.01, math.pi - 0.005]
    m = LM.state_mean(sig, np.array([0.5, 0.25, 0.25]), LM.ang_indices(1))
    assert abs(abs(m[NV + 2]) - math.pi) < 0.02, m[NV + 2]
    r = LM.state_residual(np.r_[np.zeros(NV), 0, 0, math.pi - 0.01], np.r_[np.zeros(NV), 0, 0, -math.pi + 0.01], LM.ang_indices(1))
    assert abs(r[NV + 2] - (-0.02)) < 1e-12, r[NV + 2]
    # an update where psi_v - psi_L crosses +-pi: the correction must be small and every angle wrapped
    x, P = init(); x[8] = -math.pi + 0.02
    xn, Pn = LM.augment_fixed(x, P, (0.0, 0.0, math.pi - 0.02), 0.01)[:2]
    rel = float(U._wrap(xn[8] - xn[NV + 2]))                               # +0.04 rad (wrapped)
    z = (xn[0], xn[1], float(U._wrap(rel + 0.03)))
    xu, Pu = LM.update_tag_rel(xn, Pn, z, TAG_SIGMA_POS, TAG_SIGMA_YAW, P_, LM.ang_indices(1), ("state", NV))
    for i in LM.ang_indices(1):
        assert -math.pi <= xu[i] < math.pi, (i, xu[i])
    d_rel = float(U._wrap((xu[8] - xu[NV + 2]) - rel))
    assert 0.0 < d_rel < 0.03, d_rel                                       # moved toward +0.03, not by ~2 pi
    # the same problem rotated so that nothing wraps gives the same relative correction
    x2 = xn.copy(); x2[8] = float(U._wrap(x2[8] - 1.0)); x2[NV + 2] = float(U._wrap(x2[NV + 2] - 1.0))
    xu2, _ = LM.update_tag_rel(x2, Pn, z, TAG_SIGMA_POS, TAG_SIGMA_YAW, P_, LM.ang_indices(1), ("state", NV))
    d_rel2 = float(U._wrap((xu2[8] - xu2[NV + 2]) - rel))
    assert abs(d_rel - d_rel2) < 1e-9, (d_rel, d_rel2)
    # inverse model wraps psi_L
    assert -math.pi <= LM.inverse_tag(0, 0, math.pi - 0.01, (0, 0, -0.05))[2] < math.pi
    print(f"test 3  landmark yaw wrapping: circular mean, residual, update across +-pi (d_rel {d_rel:.4f} = {d_rel2:.4f})  OK")


# ------------------------------------------------------------------ test 4
def synthetic_events(t0=0.0, t_end=12.0, dets=()):
    """IMU at 3 ms from t0; plus tagrel detections (t, tid)."""
    ev = [(t0 + 0.003 * i, "imu", None) for i in range(int((t_end - t0) / 0.003))]
    ev += [(t, "tagrel", (tid, 0.0, 0.0, 0.0)) for t, tid in dets]
    ev.sort(key=lambda e: e[0])
    return ev


def test_tag0_anchor_handling():
    t_init = 0.5
    dets = [(0.2, 0), (1.0, 3), (1.20, 0), (1.30, 0), (2.0, 5), (5.0, 0), (5.01, 3)]
    ev = synthetic_events(dets=dets)
    i_a, t_a, lab = R.keyframe_prepass(ev, t_init, 0, t_max=None)
    assert t_a == 1.20 and ev[i_a][1] == "tagrel" and ev[i_a][2][0] == 0    # the 0.2 s one is before t_init; tag 3 at 1.0 ignored
    assert all(j > i_a for j in lab if j != i_a) and lab[i_a] is not None
    # label = the keyframe time t_init + k/30 at or after the detection (the next keyframe the FGO would run)
    for j, L in lab.items():
        assert L is not None and L >= ev[j][0] - 1e-12 and L - ev[j][0] < 1.0 / 30.0 + 0.0031, (ev[j][0], L)
    # PassBook: key 0 = the anchoring gauge pass; lc keeps tag 0 at key 0
    for mode in ("lc", "nolc"):
        b = R.PassBook(mode); keys = []
        seq = [(1.2, 0), (1.3, 0), (2.0, 5), (5.0, 0), (5.01, 3)]
        for t, tid in seq:
            keys.append(b.on_detection(tid, t)[0])
        assert keys[:3] == [0, 0, 1] and keys[3] == (0 if mode == "lc" else 2), (mode, keys)
    # re-anchor: x, y, yaw := the measurement, velocity rotated, P diagonal with the tag noise
    x, P = init(); P = P + 1e-6 * np.ones_like(P)
    xr, Pr = R.reanchor(x, P, (0.4, -0.3), 0.2)
    assert xr[0] == 0.4 and xr[1] == -0.3 and xr[8] == 0.2
    d = 0.2 - x[8]; assert np.allclose(xr[3:5], [math.cos(d) * x[3] - math.sin(d) * x[4], math.sin(d) * x[3] + math.cos(d) * x[4]])
    assert np.count_nonzero(Pr - np.diag(np.diag(Pr))) == 0
    assert Pr[0, 0] == Pr[1, 1] == TAG_SIGMA_POS ** 2 and Pr[8, 8] == TAG_SIGMA_YAW ** 2
    # quaternion -> R (Eigen formula; checked against gtsam separately): a pure yaw
    a = 0.7; Rq = R.quat_to_R(math.cos(a / 2), 0.0, 0.0, math.sin(a / 2))
    assert np.allclose(Rq, [[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]], atol=1e-15)
    print("test 4  tag-0 anchor: first central gauge detection after t_init, keyframe labels, key 0 fixed (lc/nolc), "
          "re-anchor  OK")


# ------------------------------------------------------------------ test 5
def test_nolc_drop():
    # book-keeping: finished passes on the keyframe time base
    b = R.PassBook("nolc"); b.on_detection(0, 1.0); k3, _ = b.on_detection(3, 2.0); b.on_detection(3, 2.5)
    assert b.finished(3.5, [k3]) == [] and b.finished(3.5 + 1e-9, [k3]) == [k3]   # strict > PASS_GAP_S
    assert R.PassBook("lc").finished(100.0, [1, 2]) == []
    k3b, new = b.on_detection(3, 3.6); assert new and k3b != k3 and b.finished(3.6, [k3]) == [k3]
    # the cut: a detection whose keyframe never runs before the break is excluded (label None)
    ev = synthetic_events(t_end=4.0, dets=[(1.0, 0), (2.0, 3), (3.005, 3), (3.02, 3)])
    _, t_a, lab = R.keyframe_prepass(ev, 0.5, 0, t_max=2.01)          # cut at 3.01 s; next keyframe 3.033 s
    js = {ev[j][0]: L for j, L in lab.items()}
    assert js[2.0] is not None and js[3.005] is None and 3.02 not in js, js
    # filter: dropping a landmark that is never observed again leaves the vehicle estimate unchanged to (alpha sqrt n)^2
    rng = np.random.default_rng(5)
    x, P = init(); ang0 = LM.ang_indices(0)
    xk, Pk, _ = LM.augment_unscented(x, P, (0.5, 0.2, 0.1), RTAG, P_, ang0)
    xk, Pk = LM.update_tag_rel(xk, Pk, (0.52, 0.19, 0.12), TAG_SIGMA_POS, TAG_SIGMA_YAW, P_, LM.ang_indices(1), ("state", NV))
    xd, Pd, Dd = LM.remove_block(xk, Pk, NV)
    assert xd.shape == (NV,) and Dd.shape == (NV + 3, NV)
    eq(xd, xk[:NV], "removal keeps the vehicle mean"); eq(Pd, Pk[:NV, :NV], "removal keeps the vehicle cov")
    worst = 0.0
    for k in range(80):
        da, dv = imu(rng)
        xk, Pk, _ = LM.predict(xk, Pk, da, dv, P_, LM.ang_indices(1), dt=DT)
        xd, Pd, _ = LM.predict(xd, Pd, da, dv, P_, ang0, dt=DT)
        if k % 2 == 0:
            r = 1.88 + 0.03 * rng.normal()
            xk, Pk, _, _ = LM.update_range(xk, Pk, r, P_, LM.ang_indices(1)); xd, Pd, _, _ = LM.update_range(xd, Pd, r, P_, ang0)
        if k % 3 == 0:
            om = 0.03 * rng.normal(size=3); f = h_flow(xd, om) + 0.03 * rng.normal(size=2)
            xk, Pk, _, _ = LM.update_flow(xk, Pk, f, om, True, 0.9, P_, LM.ang_indices(1))
            xd, Pd, _, _ = LM.update_flow(xd, Pd, f, om, True, 0.9, P_, ang0)
        worst = max(worst, np.hypot(*(xk[:2] - xd[:2])), abs(U._wrap(xk[8] - xd[8])))
    assert worst < 1e-6, worst
    print(f"test 5  no-LC: pass end strict > 1.0 s, cut exclusion, removal keeps the vehicle block; kept vs dropped "
          f"vehicle differs by {worst:.1e} over 80 steps  OK")


# ------------------------------------------------------------------ test 6
def test_rts_growing_state_linear_exact():
    """rts_backward over a chain with an augmentation and a removal equals the batch (joint-Gaussian) posterior of the
    same linear-Gaussian model, exactly up to round-off; and equals the chain that keeps the landmark to the end."""
    rng = np.random.default_rng(6)
    dt, K, m, r_ = 0.1, 40, 12, 25                   # augment after the update at step m, remove after step r_
    F = np.array([[1, dt], [0, 1.0]]); Q = np.diag([1e-4, 4e-3]); m0 = np.array([0.0, 0.5]); P0 = np.diag([0.04, 0.09])
    rw, rp, rl = 0.02, 0.05, 0.01                    # landmark init noise, position meas, relative meas variances
    yp = rng.normal(size=K + 1) * 0.2; yl = {k: rng.normal() * 0.1 + 1.0 for k in range(m + 1, r_ + 1)}
    yl[m] = 1.0                                       # the augmentation "measurement": l = v0[0] - y + w (inverse model)

    def run(keep):
        x, P = m0.copy(), P0.copy(); nodes = []; pred_idx = []; has_l = False
        for k in range(K + 1):
            if k > 0:                                                    # predict k-1 -> k
                n = len(x); Fa = np.eye(n); Fa[:2, :2] = F; Qa = np.zeros((n, n)); Qa[:2, :2] = Q
                xp_, Pp_ = Fa @ x, Fa @ P @ Fa.T + Qa
                nodes.append((x, P, (), xp_, Pp_, P @ Fa.T, ())); pred_idx.append(len(nodes) - 1); x, P = xp_, Pp_
            H = np.zeros(len(x)); H[0] = 1.0                             # position measurement
            S = H @ P @ H + rp; Kg = P @ H / S; x = x + Kg * (yp[k] - H @ x); P = P - np.outer(Kg, Kg) * S
            if has_l and k in yl and k > m:                              # relative measurement v[0] - l
                H = np.zeros(len(x)); H[0] = 1.0; H[2] = -1.0
                S = H @ P @ H + rl; Kg = P @ H / S; x = x + Kg * (yl[k] - H @ x); P = P - np.outer(Kg, Kg) * S
            if k == m:                                                   # augmentation l = v[0] - y_m + w
                A = np.zeros(len(x)); A[0] = 1.0
                xn = np.r_[x, A @ x - yl[m]]; Pn = np.zeros((3, 3)); Pn[:2, :2] = P; Pn[:2, 2] = P @ A; Pn[2, :2] = P @ A
                Pn[2, 2] = A @ P @ A + rw; nodes.append((x, P, (), xn, Pn, Pn[:2, :].copy(), ())); x, P = xn, Pn; has_l = True
            if k == r_ and not keep:                                     # removal
                xn, Pn, Dn = LM.remove_block(x, P, 2)
                nodes.append((x, P, (), xn, Pn, Dn, ())); x, P = xn, Pn; has_l = False
        sm, xfin = LM.rts_backward(nodes, x, P, out_dims=2)
        return [sm[j] for j in pred_idx[1:]] + [xfin], sm[0]          # smoothed v_k for k = 1..K, and v_0

    sm_drop, v0_drop = run(False); sm_keep, v0_keep = run(True)
    # batch: Z = [v0 (2), q_0..q_{K-1} (2K), w (1)]; v_k = F^k v0 + sum F^{k-1-j} q_j; l = v_m[0] - y_m + w
    nz = 2 + 2 * K + 1
    T = [np.zeros((2, nz)) for _ in range(K + 1)]; T[0][:, :2] = np.eye(2)
    for k in range(1, K + 1):
        T[k] = F @ T[k - 1]; T[k][:, 2 + 2 * (k - 1):2 + 2 * k] += np.eye(2)
    Tl = T[m][0].copy(); Tl[-1] += 1.0; cl = -yl[m]
    mz = np.r_[m0, np.zeros(2 * K + 1)]
    Pz = np.zeros((nz, nz)); Pz[:2, :2] = P0
    for k in range(K):
        Pz[2 + 2 * k:4 + 2 * k, 2 + 2 * k:4 + 2 * k] = Q
    Pz[-1, -1] = rw
    rows, ys, rs = [], [], []
    for k in range(K + 1):
        rows.append(T[k][0]); ys.append(yp[k]); rs.append(rp)
        if m < k <= r_:
            rows.append(T[k][0] - Tl); ys.append(yl[k] + cl); rs.append(rl)
    M = np.array(rows); S = M @ Pz @ M.T + np.diag(rs)
    mpost = mz + Pz @ M.T @ np.linalg.solve(S, np.array(ys) - M @ mz)
    batch = [T[k] @ mpost for k in range(K + 1)]
    err_d = max(np.abs(sm_drop[k - 1] - batch[k]).max() for k in range(1, K + 1))
    err_k = max(np.abs(sm_keep[k - 1] - batch[k]).max() for k in range(1, K + 1))
    err_0 = max(np.abs(v0_drop - batch[0]).max(), np.abs(v0_keep - batch[0]).max())
    assert err_d < 1e-9 and err_k < 1e-9 and err_0 < 1e-9, (err_d, err_k, err_0)
    print(f"test 6  RTS over a growing/shrinking state == batch posterior: drop {err_d:.1e}, keep {err_k:.1e}, "
          f"v0 {err_0:.1e}  OK")


def test_rts_ukf_chain_and_store():
    """The UKF chain with an augmentation and a removal runs through rts_backward (shapes, wrapping), and the NodeStore
    memmap spill reads back exactly what was stored."""
    rng = np.random.default_rng(7)
    with tempfile.TemporaryDirectory() as td:
        store = R.NodeStore(td, spill_bytes=60_000)                     # spill after a few nodes
        x, P = init(); nodes_ram = []
        def add(*nd):
            store.add(*nd); nodes_ram.append(tuple(a.copy() if isinstance(a, np.ndarray) else a for a in nd))
        lay = 0
        for k in range(30):
            ang = LM.ang_indices(lay)
            if k == 8:
                xn, Pn, D = LM.augment_unscented(x, P, (0.3, 0.1, 3.1), RTAG, P_, ang); lay = 1
                add(x, P, ang, xn, Pn, D, LM.ang_indices(lay)); x, P = xn, Pn; ang = LM.ang_indices(lay)
            if k == 20:
                xn, Pn, D = LM.remove_block(x, P, NV); lay = 0
                add(x, P, ang, xn, Pn, D, LM.ang_indices(lay)); x, P = xn, Pn; ang = LM.ang_indices(lay)
            xn, Pn, D = LM.predict(x, P, *imu(rng), P_, ang, dt=DT)
            add(x, P, ang, xn, Pn, D, ang); x, P = xn, Pn
            if 8 < k < 20 and k % 2:
                x, P = LM.update_tag_rel(x, P, (x[0] - x[NV] + 0.01, 0.0, 0.0), TAG_SIGMA_POS, TAG_SIGMA_YAW, P_, ang, ("state", NV))
        assert store.n_spilled > 0 and len(store) == len(nodes_ram)
        for k in range(len(store)):
            a, b = store[k], nodes_ram[k]
            for u, v in zip(a, b):
                if isinstance(v, np.ndarray):
                    eq(u, v, f"store node {k}")
        sm1, f1 = LM.rts_backward(R._NodeView(store), x, P)
        sm2, f2 = LM.rts_backward(nodes_ram, x, P)
        for u, v in zip(sm1, sm2):
            eq(u, v, "RTS from the store")
        assert all(s.shape == (NV,) for s in sm1) and all(-math.pi <= s[8] < math.pi for s in sm1)
        store.close()
    print(f"test 6b UKF chain with augmentation + removal through rts_backward; NodeStore memmap spill "
          f"({store.n_spilled} of {len(nodes_ram)} nodes) reads back exactly  OK")


# ------------------------------------------------------------------ harness, end to end on synthetic events
def _synthetic_bag(kind, seed=8, T=14.0):
    """A hover-and-drift synthetic event stream (no bag): IMU 333 Hz, flow and range 30 Hz, attitude 50 Hz, and tag
    events every 0.2 s from t = 2 s: /tags/sent world fixes (kind "sent", ids cycling, the vehicle near the origin) or
    /tags/raw tag-relative detections (kind "raw": tag 0 first, then passes over 3 and 5, tag 0 again after a gap)."""
    rng = np.random.default_rng(seed); ev = []
    for i in range(int(T / 0.003)):
        t = 0.003 * i + 1e-4 * rng.normal()
        ev.append((t, "imu", (np.array([0.0, 0.0, 9.80665]) + 0.02 * rng.normal(size=3), 0.002 * rng.normal(size=3))))
    for i in range(int(T * 30)):
        t = i / 30.0 + 0.001
        ev.append((t, "rng", 0.075 if t < 1.5 else 1.78 + 0.01 * rng.normal()))
        ev.append((t + 0.0005, "flow", (0.02 * rng.normal(size=2), True, 0.9)))
    ev += [(i / 50.0, "att", 0.002 * rng.normal(size=3)) for i in range(int(T * 50))]
    tmap = R.TM.load_map(R.MAP_PATH)
    for j, t in enumerate(np.arange(2.0, T - 0.5, 0.2)):
        if kind == "sent":
            ev.append((float(t), "tag", (0.01 * rng.normal(), 0.01 * rng.normal(), 0.005 * rng.normal(), int(j % 4) * 2)))
        else:
            tid = 0 if t < 4.0 else (3 if t < 6.0 else (5 if t < 8.0 else (0 if t < 10.0 else 3)))
            ev.append((float(t), "tagrel", (tid, 0.3 + 0.01 * rng.normal(), -0.2 + 0.01 * rng.normal(), 0.1 + 0.005 * rng.normal())))
    return ev       # bag order is not time order here; the harness sorts after dejitter, as the replays do


def test_harness_synthetic_end_to_end():
    """lc_ukf_replay.run on synthetic event streams (read_events and the output guard monkeypatched to a temp dir):
    every task runs; V-E5b (known map) and V-E5c (augmented, 1e-10) reproduce V-E5a (ukf_core) live and RTS rows 1:1,
    far inside 1 mm; result modes write live/hindsight with one row per predict step from the anchor."""
    orig_read, orig_res = R.read_events, R.T1.resolve_out
    out = {}
    with tempfile.TemporaryDirectory() as td:
        try:
            for task, kind in (("world", "sent"), ("known-map", "sent"), ("augmented", "sent"), ("lc", "raw"), ("nolc", "raw")):
                R.read_events = lambda bag, topic, kind=kind: (_synthetic_bag(kind), 0, 0)
                R.T1.resolve_out = lambda trial, base, root: (os.makedirs(os.path.join(td, base), exist_ok=True), os.path.join(td, base))[1]
                try:
                    o, st = R.run("SYNTH_NO_SUCH_TRIAL", task, td, t_max=9.0)
                except SystemExit as e:                                   # result modes: no stored FGO run -> exit 3
                    assert task in ("lc", "nolc") and e.code == 3, (task, e.code)
                    o = os.path.join(td, f"lc_ukf_{task}_t9"); st = json.load(open(f"{o}/stats.json"))
                out[task] = (o, st)
        finally:
            R.read_events, R.T1.resolve_out = orig_read, orig_res
        w_dir = out["world"][0]; worst = {}
        for task in ("known-map", "augmented"):
            for f in ("ukf_live.tum", "ukf_rts.tum"):
                r = C.compare_track(f"{w_dir}/{f}", f"{out[task][0]}/{f}", (0.0, 1e9))
                assert r["rows_match"] and r["max_all_m"] < 1e-5, (task, f, r); worst[(task, f)] = r["max_all_m"]
            g = C.compare_gates(f"{w_dir}/gate_log.npz", f"{out[task][0]}/gate_log.npz")
            assert g["pass"] and g["n_flips"] == 0, g
            assert out[task][1]["t_anchor"] == out["world"][1]["t_anchor"] and out[task][1]["n_tag_fused"] == out["world"][1]["n_tag_fused"]
        assert out["augmented"][1]["n_landmarks_augmented"] == 4 and out["augmented"][1]["max_state_dim"] == NV + 12
        for mode in ("lc", "nolc"):
            o, st = out[mode]
            nl = sum(1 for _ in open(f"{o}/live.tum")); nh = sum(1 for _ in open(f"{o}/hindsight.tum"))
            assert nl == nh == st["rts_nodes"] and nl > 100, (mode, nl, nh)
            assert st["invariants"]["pass"] is False
        # lc: keys 0 (tag 0), 3, 5 -> 3 landmarks; nolc: tag 0 pass 1 (fixed), 3, 5, tag 0 pass 2, 3 pass 2 -> 5 (cut 11 s)
        assert out["lc"][1]["landmarks"] == 3 and out["nolc"][1]["landmarks"] == 5, (out["lc"][1]["landmarks"], out["nolc"][1]["landmarks"])
        assert out["nolc"][1]["landmarks_dropped"] == 3 and out["lc"][1]["landmarks_dropped"] == 0
    print(f"test H  harness end to end (synthetic events): V-E5b/c vs V-E5a rows 1:1, max horizontal difference "
          f"{ {k[0] + ' ' + k[1]: f'{v:.1e}' for k, v in worst.items()} } m (6-dp files), equal gate "
          "decisions; lc 3 / nolc 5 landmarks, nolc drops finished passes; live = hindsight rows  OK")


# ------------------------------------------------------------------ comparator
def test_comparator():
    with tempfile.TemporaryDirectory() as td:
        def tum(path, rows):
            with open(path, "w") as f:
                for t, x, y in rows:
                    f.write(f"{t:.6f} {x:.6f} {y:.6f} 0 0 0 0 1\n")
        base = [(10 + 0.015 * i, 0.001 * i, -0.002 * i) for i in range(400)]
        tum(f"{td}/ref.tum", base)
        tum(f"{td}/ok.tum", [(t, x + 0.0004, y) for t, x, y in base])
        tum(f"{td}/far.tum", [(t, x + (0.0025 if i == 200 else 0), y) for i, (t, x, y) in enumerate(base)])
        tum(f"{td}/rows.tum", base[:-1])
        w = (11.0, 15.0)
        assert C.compare_track(f"{td}/ref.tum", f"{td}/ref.tum", w)["byte_identical"]
        assert C.compare_track(f"{td}/ref.tum", f"{td}/ok.tum", w)["pass"]
        assert not C.compare_track(f"{td}/ref.tum", f"{td}/far.tum", w)["pass"]        # max > 2 mm
        assert not C.compare_track(f"{td}/ref.tum", f"{td}/rows.tum", w)["pass"]
        def npz(path, acc, test):
            np.savez(path, t=np.arange(5.0), code=np.array([0, 1, 2, 0, 1]), test=np.array(test), accepted=np.array(acc))
        npz(f"{td}/a.npz", [1, 1, 1, 0, 1], [0.1, 0.2, 0.3, 1.0 + 5e-10, 0.4])
        npz(f"{td}/b.npz", [1, 1, 1, 1, 1], [0.1, 0.2, 0.3, 1.0 - 5e-10, 0.4])
        npz(f"{td}/c.npz", [1, 1, 0, 0, 1], [0.1, 0.2, 1.3, 1.0 + 5e-10, 0.4])
        g1 = C.compare_gates(f"{td}/a.npz", f"{td}/b.npz"); g2 = C.compare_gates(f"{td}/a.npz", f"{td}/c.npz")
        assert g1["pass"] and g1["n_roundoff_flips"] == 1 and not g2["pass"]
        # judge(): the directory layout of the gates, with a synthetic ground truth for |dRMSE|
        for d_ in ("in/T/lc_ukf_val_world", "in/T/lc_ukf_val_knownmap", "tr/T/room_ukf", "ex"):
            os.makedirs(f"{td}/{d_}")
        for f in ("ukf_live.tum", "ukf_rts.tum"):
            tum(f"{td}/tr/T/room_ukf/{f}", base); tum(f"{td}/in/T/lc_ukf_val_knownmap/{f}", [(t, x + 0.0004, y) for t, x, y in base])
        st_ = {"t_anchor": 10.0, "n_tag_fused": 7}
        for d_ in ("tr/T/room_ukf", "in/T/lc_ukf_val_knownmap"):
            json.dump(st_, open(f"{td}/{d_}/stats.json", "w"))
        json.dump({"window_s": [11.0, 15.0]}, open(f"{td}/ex/T.json", "w"))
        npz(f"{td}/in/T/lc_ukf_val_world/gate_log.npz", [1, 1, 1, 0, 1], [0.1, 0.2, 0.3, 0.9, 0.4])
        npz(f"{td}/in/T/lc_ukf_val_knownmap/gate_log.npz", [1, 1, 1, 0, 1], [0.1, 0.2, 0.3, 0.9, 0.4])
        gt = np.array([(10 + 0.01 * i, 0.001 * i * 1.5, -0.002 * i * 1.5) for i in range(700)])
        res = C.judge("T", "knownmap", f"{td}/in", f"{td}/tr", f"{td}/ex", gt)
        assert res["PASS"] and abs(res["live"]["rmse_vs_gt_m"]["abs_delta"]) <= 0.0004 + 1e-9, res["live"]
        json.dump({"t_anchor": 10.0, "n_tag_fused": 8}, open(f"{td}/in/T/lc_ukf_val_knownmap/stats.json", "w"))
        assert not C.judge("T", "knownmap", f"{td}/in", f"{td}/tr", f"{td}/ex")["PASS"]   # tag count differs
    print("test C  comparator: row match, 1 mm / 2 mm bounds, round-off flip vs real flip  OK")


if __name__ == "__main__":
    test_n15_bit_identical_to_ukf_core()
    test_known_map_rotated_equals_world()
    test_augmentation_shapes_and_crosscov()
    test_augmented_known_map_close_to_fixed()
    test_landmark_yaw_wrapping()
    test_tag0_anchor_handling()
    test_nolc_drop()
    test_rts_growing_state_linear_exact()
    test_rts_ukf_chain_and_store()
    test_harness_synthetic_end_to_end()
    test_comparator()
    print("ALL OK")
