#!/usr/bin/env python3
"""Experiment H, S2 gate (docs/h_backends_tag_input.md, tier A): export the offline ROOM UKF's exact event stream
and states, tag fixes included, for the C++ port's UKF_Equiv harness.

As eval/ukf_event_export.py (step 2), but it runs the UNMODIFIED src/estimators/room_ukf_replay.py (runpy) and also
wraps ukf_core.predict_rts (used after the re-anchor; same x and P as predict), ukf_core.update_tag and
measurement_models.reanchor_jacobian (imported by name in the replay, so patched in the module BEFORE runpy).
Event types: 0 predict, 1 range, 2 flow, 3 yaw-pseudo check, 4 tag fix (N, E, yaw NED, R_pos, R_yaw), 5 re-anchor
(same inputs; the replay then sets P <- diag(J P J^T) with the fix variances, which the port's tag_reanchor does).

The trial directory is REDIRECTED: os.path.expanduser maps ~/thesis_data/trials/<trial> to a scratch directory that
holds symlinks to bag/ and imu_gaps.json, so <trial>/room_ukf/ is never written. --no-rts is passed (the live track
does not depend on it). The wrapped run's ukf_live.tum must be byte-identical to the stored one (checked here).
Usage (~/venv-evo): ROOM_TAG_SIGMA_POS=0.02 python3 eval/ukf_tag_event_export.py TRIAL OUT_PREFIX"""
import filecmp, math, os, runpy, struct, sys
import numpy as np

TRIAL, OUT = sys.argv[1], sys.argv[2]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "estimators"))
import ukf_core as U
import measurement_models as MM
from measurement_models import R_world_body

T = np.array([[0, 1, 0], [1, 0, 0], [0, 0, -1.0]])      # ENU vector -> NED vector
F = np.diag([1.0, -1.0, -1.0])                           # FRD <-> FLU
J = np.zeros((15, 15))
J[0:3, 0:3] = T; J[3:6, 3:6] = T
J[6, 6] = 1; J[7, 7] = -1; J[8, 8] = -1
J[9:12, 9:12] = F; J[12:15, 12:15] = F


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def to_ned(x):
    y = J @ x
    y[8] = wrap(math.pi / 2 - x[8])
    return y


def R_ned_frd(r, p, yw):
    cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(p), math.sin(p), math.cos(yw), math.sin(yw)
    return np.array([[cp * cy, sr * sp * cy - cr * sy, cr * sp * cy + sr * sy],
                     [cp * sy, sr * sp * sy + cr * cy, cr * sp * sy - sr * cy],
                     [-sp, sr * cp, cr * cp]])


rng = np.random.default_rng(0)
for _ in range(1000):
    e = rng.uniform([-0.5, -0.5, -math.pi], [0.5, 0.5, math.pi])
    xe = np.zeros(15); xe[6:9] = e
    assert np.allclose(T @ R_world_body(*e) @ F, R_ned_frd(*to_ned(xe)[6:9]), atol=1e-12), "Euler conversion check failed"


def reanchor_ned(x, P, pn, pe, yaw, rpos, ryaw):
    """The port's tag_reanchor, in numpy (AP_NavUKF.cpp), for the self-check below."""
    x = x.copy(); d = wrap(yaw - x[8]); c, s = math.cos(d), math.sin(d)
    vn, ve = x[3], x[4]
    x[0], x[1], x[8] = pn, pe, yaw
    x[3], x[4] = c * vn - s * ve, s * vn + c * ve
    dg = np.diag(P).copy()
    dg[3] = c * c * P[3, 3] - 2 * c * s * P[3, 4] + s * s * P[4, 4]
    dg[4] = s * s * P[3, 3] + 2 * s * c * P[3, 4] + c * c * P[4, 4]
    dg[0] = dg[1] = rpos; dg[8] = ryaw
    return x, np.diag(dg)


_orig_reanchor = MM.reanchor_jacobian
for _ in range(1000):                                    # NED re-anchor (state AND P rule) == Python ENU, converted
    xe = rng.normal(size=15) * 0.3; xe[8] = rng.uniform(-math.pi, math.pi)
    A = rng.normal(size=(15, 15)); Pe = A @ A.T * 0.01
    fE, fN, fy = rng.uniform(-3, 3), rng.uniform(-3, 3), rng.uniform(-math.pi, math.pi)
    xn_e, Jr = _orig_reanchor(xe, (fE, fN), fy)
    Pn_e = np.diag(np.diag(Jr @ Pe @ Jr.T)); Pn_e[0, 0] = Pn_e[1, 1] = 0.02 ** 2; Pn_e[8, 8] = 0.087 ** 2
    xp, Pp = reanchor_ned(to_ned(xe), J @ Pe @ J.T, fN, fE, wrap(math.pi / 2 - fy), 0.02 ** 2, 0.087 ** 2)
    assert np.allclose(to_ned(xn_e), xp, atol=1e-12) and np.allclose(J @ Pn_e @ J.T, Pp, atol=1e-12), "re-anchor check failed"
print("[export] ENU/FLU -> NED/FRD conversion and the NED re-anchor verified on 1000 random cases each")

rec = {"x0": None, "P0": None}
ev, tev = [], []
TAG_SIG_POS = float(os.environ.get("ROOM_TAG_SIGMA_POS", MM.TAG_SIGMA_POS)); TAG_SIG_YAW = float(MM.TAG_SIGMA_YAW)


def _t():
    return float(sys._getframe(2).f_globals.get("t", float("nan")))


_orig = {k: getattr(U, k) for k in ("init_state", "predict", "predict_rts", "update_range", "update_flow",
                                     "update_yaw_pseudo", "update_tag")}


def w_init(*a, **k):
    x, P = _orig["init_state"](*a, **k)
    rec["x0"], rec["P0"] = to_ned(x), J @ P @ J.T
    return x, P


def _pred_row(tt, xn, da, dv, d):
    tev.append(tt); ev.append((0, [da[0], -da[1], -da[2], dv[0], -dv[1], -dv[2], d], to_ned(xn), (0, 0)))


def w_predict(x, P, da, dv, p, dt=None):
    rec.setdefault("qdiag", np.diag(p["Q"]).copy())       # Python's per-step Q (D27-scaled, fixed at DT_STEP)
    xn, Pn = _orig["predict"](x, P, da, dv, p, dt=dt)
    _pred_row(_t(), xn, da, dv, p["dt"] if dt is None else dt)
    return xn, Pn


def w_predict_rts(x, P, da, dv, p, dt=None):
    rec.setdefault("qdiag", np.diag(p["Q"]).copy())
    xn, Pn, Dk = _orig["predict_rts"](x, P, da, dv, p, dt=dt)
    _pred_row(_t(), xn, da, dv, p["dt"] if dt is None else dt)
    return xn, Pn, Dk


def w_range(x, P, z, p):
    xn, Pn, acc = _orig["update_range"](x, P, z, p)
    tev.append(_t()); ev.append((1, [z, 0, 0, 0, 0, 0, 0], to_ned(xn), (int(acc), 0)))
    return xn, Pn, acc


def w_flow(x, P, flow_xy, om, valid, inlier, p):
    xn, Pn, (ax, ay) = _orig["update_flow"](x, P, flow_xy, om, valid, inlier, p)
    ok = bool(valid) and inlier > 0 and abs(flow_xy[0]) < p["FLOW_MAX"] and abs(flow_xy[1]) < p["FLOW_MAX"]
    tev.append(_t()); ev.append((2, [flow_xy[0], flow_xy[1], om[0], -om[1], -om[2], float(ok), 0], to_ned(xn), (int(ax), int(ay))))
    return xn, Pn, (ax, ay)


def w_yaw(x, P, p):
    xn, Pn, fired = _orig["update_yaw_pseudo"](x, P, p)
    tev.append(_t()); ev.append((3, [0] * 7, to_ned(xn), (int(fired), 0)))
    return xn, Pn, fired


def w_tag(x, P, z, sig_pos, sig_yaw, p):
    xn, Pn = _orig["update_tag"](x, P, z, sig_pos, sig_yaw, p)
    tev.append(_t()); ev.append((4, [z[1], z[0], wrap(math.pi / 2 - z[2]), sig_pos ** 2, sig_yaw ** 2, 0, 0], to_ned(xn), (1, 0)))
    return xn, Pn


def w_reanchor(x, p_fix_EN, yaw_fix):
    xn, Jr = _orig_reanchor(x, p_fix_EN, yaw_fix)
    # the replay then sets P <- diag(J P J^T), P[0,0] = P[1,1] = TAG_SIGMA_POS^2, P[8,8] = TAG_SIGMA_YAW^2
    tev.append(_t()); ev.append((5, [p_fix_EN[1], p_fix_EN[0], wrap(math.pi / 2 - yaw_fix), TAG_SIG_POS ** 2, TAG_SIG_YAW ** 2, 0, 0],
                                 to_ned(xn), (1, 0)))
    return xn, Jr


U.init_state, U.predict, U.predict_rts, U.update_range = w_init, w_predict, w_predict_rts, w_range
U.update_flow, U.update_yaw_pseudo, U.update_tag = w_flow, w_yaw, w_tag
MM.reanchor_jacobian = w_reanchor

# ---- redirect the trial directory to scratch (symlinks), so <trial>/room_ukf is never written ----
real_trial = os.path.expanduser(f"~/thesis_data/trials/{TRIAL}")
scratch = os.path.abspath(OUT + "_trial")
os.makedirs(scratch, exist_ok=True)
for f in ("bag", "imu_gaps.json"):
    if os.path.exists(f"{real_trial}/{f}") and not os.path.lexists(f"{scratch}/{f}"):
        os.symlink(f"{real_trial}/{f}", f"{scratch}/{f}")
_eu = os.path.expanduser


def eu(pth):
    r = _eu(pth)
    return scratch + r[len(real_trial):] if (r == real_trial or r.startswith(real_trial + "/")) else r


stored = f"{real_trial}/room_ukf/ukf_live.tum"
mt0 = {f: os.path.getmtime(os.path.join(real_trial, "room_ukf", f)) for f in os.listdir(f"{real_trial}/room_ukf")}
os.path.expanduser = eu
sys.argv = ["room_ukf_replay.py", TRIAL, "--no-rts"]
runpy.run_path(os.path.join(ROOT, "src", "estimators", "room_ukf_replay.py"), run_name="__main__")
os.path.expanduser = _eu
mt1 = {f: os.path.getmtime(os.path.join(real_trial, "room_ukf", f)) for f in os.listdir(f"{real_trial}/room_ukf")}
assert mt0 == mt1, "stored room_ukf/ changed!"
same = filecmp.cmp(stored, f"{scratch}/room_ukf/ukf_live.tum", shallow=False)
print(f"[export] wrapped ukf_live.tum byte-identical to the stored one: {same}; stored room_ukf/ untouched")

typ = np.array([e[0] for e in ev], np.int8)
inp = np.array([e[1] for e in ev], float)
xs = np.array([e[2] for e in ev], float)
fl = np.array([e[3] for e in ev], np.int8)
# Python's per-step process-noise diagonal, in the port's state order (NED/FRD: the diagonal is unchanged by the axis
# permutation within each block). For the DIAGNOSTIC harness option UKF_EQ_QDIAG (see UKF_Equiv.cpp): since D27 the
# offline UKF scales EKF3's per-step form by DT_REF/dt, the port uses EKF3's form at its own (12.5 ms) step.
qn = np.abs(np.diag(J @ np.diag(rec["qdiag"]) @ J.T))
qn.astype("<f8").tofile(OUT + ".qdiag")
np.savez_compressed(OUT + ".npz", x0=rec["x0"], P0=rec["P0"], qdiag_ned=qn, type=typ, inputs=inp, x_after=xs, flags=fl, time=np.array(tev),
                    live_tum_identical=same)
with open(OUT + ".bin", "wb") as f:
    f.write(b"UKFEV001")
    f.write(struct.pack("<15d", *rec["x0"])); f.write(struct.pack("<225d", *rec["P0"].ravel()))
    f.write(struct.pack("<Q", len(ev)))
    for t_, i_ in zip(typ, inp):
        f.write(struct.pack("<b7d", int(t_), *i_))
print(f"[export] {len(ev)} events: predict {int((typ == 0).sum())}, range {int((typ == 1).sum())}, flow {int((typ == 2).sum())}, "
      f"yaw-check {int((typ == 3).sum())}, tag {int((typ == 4).sum())}, re-anchor {int((typ == 5).sum())} -> {OUT}.npz / .bin")
