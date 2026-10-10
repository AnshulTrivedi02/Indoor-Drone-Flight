#!/usr/bin/env python3
"""R1 default-unchanged check, level (a): the geometry parametrisation leaves the SIM path BYTE-IDENTICAL.

Loads measurement_models / factors / fgo_core from a base commit (default 3a2c3a8, before R1) and from the working
tree, and compares, on random inputs with geom=None (the default every simulation caller uses):
  h_flow_pose, h_flow, h_range, h_flow_rot, the FGO flow- and range-factor errors (unwhitened) and Jacobians,
  FGO.init's pose, and a GroundProximityFlow sequence.
Equality is .tobytes() equality. Also checks make_geometry(SIM values) gives the same numbers (not required to be
bitwise: it is a different call path, used only by the events mode).
Usage (~/venv-fgo): python3 eval/bin2fgo_default_check.py [base_commit]"""
import importlib.util, os, subprocess, sys, tempfile
import numpy as np

BASE = sys.argv[1] if len(sys.argv) > 1 else "3a2c3a8"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EST = os.path.join(ROOT, "src", "estimators")


def load_tree(d):
    """Import measurement_models, factors, fgo_core from directory d (src/estimators layout) as fresh modules."""
    for k in ("measurement_models", "factors", "fgo_core"):
        sys.modules.pop(k, None)
    sys.path[:0] = [d, os.path.join(d, "fgo")]
    try:
        mm = importlib.import_module("measurement_models")
        F = importlib.import_module("factors")
        fc = importlib.import_module("fgo_core")
    finally:
        del sys.path[:2]
    for k in ("measurement_models", "factors", "fgo_core"):
        sys.modules.pop(k, None)
    return mm, F, fc


tmp = tempfile.mkdtemp(prefix="r1_base_")
os.makedirs(os.path.join(tmp, "fgo"))
for rel in ("measurement_models.py", "fgo/factors.py", "fgo/fgo_core.py"):
    src = subprocess.run(["git", "-C", ROOT, "show", f"{BASE}:src/estimators/{rel}"], capture_output=True, check=True).stdout
    open(os.path.join(tmp, rel), "wb").write(src)
old = load_tree(tmp)
new = load_tree(EST)
assert not hasattr(old[0], "make_geometry") and hasattr(new[0], "make_geometry"), "base/new modules not distinct"

import gtsam
from gtsam.symbol_shorthand import X, V, B

rng = np.random.default_rng(20261010)
fails = []; n = 0


def same(name, a, b):
    global n
    n += 1
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.shape != b.shape or a.tobytes() != b.tobytes():
        fails.append(name)


def rand_rot():
    r, p, y = rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4), rng.uniform(-np.pi, np.pi)
    return r, p, y


for i in range(2000):
    r, p, y = rand_rot()
    R_o = old[0].R_world_body(r, p, y); R_n = new[0].R_world_body(r, p, y)
    same("R_world_body", R_o, R_n)
    v = rng.normal(0, 1.0, 3); om = rng.normal(0, 0.5, 3); pU = rng.uniform(-0.2, 5.0)
    same("h_flow_pose", old[0].h_flow_pose(R_o, v, pU, om), new[0].h_flow_pose(R_n, v, pU, om))
    x = rng.normal(0, 1, 15); x[2] = pU
    same("h_flow", old[0].h_flow(x, om), new[0].h_flow(x, om))
    same("h_range", old[0].h_range(x), new[0].h_range(x))
    same("h_flow_rot", old[0].h_flow_rot(om), new[0].h_flow_rot(om))

# factor errors + Jacobians
noise2 = gtsam.noiseModel.Isotropic.Sigma(2, 0.25); noise1 = gtsam.noiseModel.Isotropic.Sigma(1, 0.5)
for i in range(300):
    r, p, y = rand_rot()
    pose = gtsam.Pose3(gtsam.Rot3.Ypr(y, p, r), rng.normal(0, 2, 3) + np.array([0, 0, 2.0]))
    vel = rng.normal(0, 1, 3)
    bias = gtsam.imuBias.ConstantBias(rng.normal(0, 0.05, 3), rng.normal(0, 0.01, 3))
    vals = gtsam.Values(); vals.insert(X(1), pose); vals.insert(V(1), vel); vals.insert(B(1), bias)
    fm = rng.normal(0, 0.5, 2); om = rng.normal(0, 0.3, 3); rm = rng.uniform(0.1, 5)
    for nm, fo, fn in (("flow_factor", old[1].flow_factor(noise2, X(1), V(1), B(1), fm, om),
                        new[1].flow_factor(noise2, X(1), V(1), B(1), fm, om)),
                       ("range_factor", old[1].range_factor(noise1, X(1), rm), new[1].range_factor(noise1, X(1), rm))):
        same(nm + ".unwhitened", fo.unwhitenedError(vals), fn.unwhitenedError(vals))
        lo, ln = fo.linearize(vals), fn.linearize(vals)
        same(nm + ".jacobian", lo.jacobian()[0], ln.jacobian()[0])
        same(nm + ".rhs", lo.jacobian()[1], ln.jacobian()[1])

# FGO.init pose and one keyframe with flow + range
for i in range(20):
    acc = np.array([rng.normal(0, 0.3), rng.normal(0, 0.3), 9.81]); r0 = rng.uniform(0.05, 0.3)
    outs = []
    for mod in (old, new):
        f = mod[2].FGO(window=0.25, kf_dt=1 / 30, lm_maxiter=2)
        f.init(acc, r0, 10.0)
        for k in range(12):
            f.integrate_imu(acc + rng.normal(0, 0.01, 3) * 0, np.zeros(3) + 0.001 * k, 1 / 400)
        f.keyframe(10.0 + 1 / 30, flow=(np.array([0.01, 0.2]), True, 0.9), omega=np.array([0.0, 0.01, 0.0]), rng=r0 + 0.01)
        t_, pose_, vel_ = f.latest()
        outs.append(np.concatenate([pose_.matrix().ravel(), np.asarray(vel_, float), [f.n_flow, f.n_range]]))
    same("FGO.init+keyframe", outs[0], outs[1])

# GroundProximityFlow
gs = []
for mod in (old, new):
    g = mod[0].GroundProximityFlow(5.0); seq = []
    for k in range(400):
        t = 4.0 + k * 0.025
        g.on_range(t, 0.08 + max(0, (t - 7.0)) * 0.3 if k % 7 else 41.0)
        g.on_gyro(t, np.array([0.0, 0.0, 0.02 * (k % 5)]), np.zeros(3))
        seq.append(np.concatenate([g.replace(np.array([0.1, 0.2]), np.array([0.01, -0.02, 0.0]), 0.01, 0.02),
                                   [float(g.takeoff), g.n_replaced]]))
    gs.append(np.array(seq))
same("GroundProximityFlow", gs[0], gs[1])

# make_geometry(SIM values) numerically equal to the constants (different call path; equality, not identity)
mm = new[0]
G = mm.make_geometry(flow_pos_frd=(0.0, 0.0, 0.25), range_pos_frd=(0.0, 0.0, 0.12))
for i in range(500):
    r, p, y = rand_rot(); R_ = mm.R_world_body(r, p, y)
    v = rng.normal(0, 1.0, 3); om = rng.normal(0, 0.5, 3); pU = rng.uniform(0.0, 5.0)
    if not np.allclose(mm.h_flow_pose(R_, v, pU, om), mm.h_flow_pose(R_, v, pU, om, G), rtol=0, atol=1e-15):
        fails.append("make_geometry(SIM) != constants")
        break

print(f"base {BASE}: {n} byte-identity comparisons, {len(set(fails))} failing kinds: {sorted(set(fails))}")
sys.exit(1 if fails else 0)
