#!/usr/bin/env python3
"""UKF port validation STEP 2, part 1: export the offline UKF's exact event stream and states.

Runs the UNMODIFIED src/estimators/ukf_replay.py (runpy) with recording wrappers around its
ukf_core calls (init_state, predict, update_range, update_flow, update_yaw_pseudo). Each call's
INPUTS and the Python state AFTER it are recorded in call order, so the C++ port can be driven
through the identical sequence (METHODOLOGY "Step 1. Agreement criterion, PRE-REGISTERED"):
the same dejittered IMU steps (accumulated da, dv, actual dt), the same flow values with the
same frame-averaged gyro, the same range samples and the same yaw-pseudo cadence.
The replay's outputs are REDIRECTED to a scratch directory (os.path.expanduser wrapper), so the
comparison outputs in <trial>/ukf/ are never touched.

Everything is converted to the port's frames (ENU/FLU -> NED/FRD), and the conversion is
checked numerically against both sides' rotation conventions before anything is written:
  pos/vel (N, E, D) = (y, x, -z); roll_n = roll_e; pitch_n = -pitch_e; yaw_n = pi/2 - yaw_e;
  gyro/accel bias FRD = (x, -y, -z); IMU da/dv FRD = (x, -y, -z); flow gyro (p, q) = (wx, -wy);
  flow rates unchanged (the port takes ArduPilot raw flow = +flow_{x,y}_rad after the sign fix).
Output: an .npz (x0, P0 in NED; per-event type/inputs/Python state after, in NED) and a binary
event file for the C++ harness (libraries/AP_NavUKF/examples/UKF_Equiv).
Usage (~/venv-evo): python3 eval/ukf_event_export.py TRIAL OUT_PREFIX"""
import math, os, runpy, struct, sys
import numpy as np

TRIAL, OUT = sys.argv[1], sys.argv[2]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "estimators"))
import ukf_core as U
from measurement_models import R_world_body

# ---- frame conversion ENU/FLU -> NED/FRD ----
T = np.array([[0, 1, 0], [1, 0, 0], [0, 0, -1.0]])      # ENU vector -> NED vector
F = np.diag([1.0, -1.0, -1.0])                           # FRD vector -> FLU vector (and back)
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


def R_ned_frd(r, p, yw):     # AP_Math Matrix3::from_euler (321), NED <- FRD
    cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(p), math.sin(p), math.cos(yw), math.sin(yw)
    return np.array([[cp * cy, sr * sp * cy - cr * sy, cr * sp * cy + sr * sy],
                     [cp * sy, sr * sp * sy + cr * cy, cr * sp * sy - sr * cy],
                     [-sp, sr * cp, cr * cp]])


rng = np.random.default_rng(0)
for _ in range(1000):                                   # conversion self-check
    e = rng.uniform([-0.5, -0.5, -math.pi], [0.5, 0.5, math.pi])
    xe = np.zeros(15); xe[6:9] = e
    xn = to_ned(xe)
    A = T @ R_world_body(*e) @ F
    assert np.allclose(A, R_ned_frd(*xn[6:9]), atol=1e-12), "Euler conversion check failed"
print("[export] ENU/FLU -> NED/FRD conversion verified on 1000 random attitudes")

# ---- recording wrappers ----
rec = {"x0": None, "P0": None}
ev = []          # (type, inputs(list of float), x_after_NED(15), flags(2))
_orig = {k: getattr(U, k) for k in ("init_state", "predict", "update_range", "update_flow", "update_yaw_pseudo")}


def w_init(*a, **k):
    x, P = _orig["init_state"](*a, **k)
    rec["x0"], rec["P0"] = to_ned(x), J @ P @ J.T
    return x, P


PERTURB_ULP = os.environ.get("PERTURB_ULP") == "1"     # DIAGNOSTIC only: 1-ulp input perturbation (round-off sensitivity)


def w_predict(x, P, da, dv, p, dt=None):
    if PERTURB_ULP:
        dv = np.nextafter(dv, np.inf)
    xn, Pn = _orig["predict"](x, P, da, dv, p, dt=dt)
    d = p["dt"] if dt is None else dt
    ev.append((0, [da[0], -da[1], -da[2], dv[0], -dv[1], -dv[2], d], to_ned(xn), (0, 0)))
    return xn, Pn


def w_range(x, P, z, p):
    xn, Pn, acc = _orig["update_range"](x, P, z, p)
    ev.append((1, [z, 0, 0, 0, 0, 0, 0], to_ned(xn), (int(acc), 0)))
    return xn, Pn, acc


ROUND_FLOW32 = os.environ.get("ROUND_FLOW32") == "1"   # DIAGNOSTIC only: the port stores flow rate/gyro as float


def w_flow(x, P, flow_xy, om, valid, inlier, p):
    if ROUND_FLOW32:
        flow_xy = np.asarray(flow_xy, np.float32).astype(float); om = np.asarray(om, np.float32).astype(float)
    xn, Pn, (ax, ay) = _orig["update_flow"](x, P, flow_xy, om, valid, inlier, p)
    ok = bool(valid) and inlier > 0 and abs(flow_xy[0]) < p["FLOW_MAX"] and abs(flow_xy[1]) < p["FLOW_MAX"]
    ev.append((2, [flow_xy[0], flow_xy[1], om[0], -om[1], -om[2], float(ok), 0], to_ned(xn), (int(ax), int(ay))))
    return xn, Pn, (ax, ay)


def w_yaw(x, P, p):
    xn, Pn, fired = _orig["update_yaw_pseudo"](x, P, p)
    ev.append((3, [0] * 7, to_ned(xn), (int(fired), 0)))
    return xn, Pn, fired


U.init_state, U.predict, U.update_range, U.update_flow, U.update_yaw_pseudo = w_init, w_predict, w_range, w_flow, w_yaw

# ---- redirect the replay's outputs away from <trial>/ukf ----
real_trial = os.path.expanduser(f"~/thesis_data/trials/{TRIAL}")
scratch = os.path.abspath(OUT + "_replay_out")
_eu = os.path.expanduser


def eu(pth):
    r = _eu(pth)
    return scratch + r[len(real_trial):] if r.startswith(real_trial + "/ukf") else r


os.path.expanduser = eu
sys.argv = ["ukf_replay.py", TRIAL]
runpy.run_path(os.path.join(ROOT, "src", "estimators", "ukf_replay.py"), run_name="__main__")
os.path.expanduser = _eu

typ = np.array([e[0] for e in ev], np.int8)
inp = np.array([e[1] for e in ev], float)
xs = np.array([e[2] for e in ev], float)
fl = np.array([e[3] for e in ev], np.int8)
np.savez_compressed(OUT + ".npz", x0=rec["x0"], P0=rec["P0"], type=typ, inputs=inp, x_after=xs, flags=fl)
with open(OUT + ".bin", "wb") as f:                      # C++ harness input
    f.write(b"UKFEV001")
    f.write(struct.pack("<15d", *rec["x0"])); f.write(struct.pack("<225d", *rec["P0"].ravel()))
    f.write(struct.pack("<Q", len(ev)))
    for t_, i_ in zip(typ, inp):
        f.write(struct.pack("<b7d", int(t_), *i_))
print(f"[export] {len(ev)} events: predict {int((typ == 0).sum())}, range {int((typ == 1).sum())}, "
      f"flow {int((typ == 2).sum())}, yaw-check {int((typ == 3).sum())} -> {OUT}.npz / .bin")
