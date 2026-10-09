#!/usr/bin/env python3
"""Numerics probe, Python side (~/venv-fgo): the same operations as src/probe.cpp, printed at %.17g.
Compare the two outputs line by line (fgo_cpp/tools/compare_probe.py) before any whole-flight comparison."""
import os, sys
import numpy as np
import gtsam
from gtsam.symbol_shorthand import X, V, B
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "fgo"))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
import factors as F
from fgo_core import make_pim_params


def pm(name, M):
    M = np.atleast_2d(np.asarray(M, float))
    print(name + "".join(f" {v:.17g}" for v in M.reshape(-1)))


R = gtsam.Rot3.Ypr(0.1, -0.2, 0.3)
pm("R", R.matrix())
print(f"yaw {R.yaw():.17g}")
pm("rpy", R.rpy())
P = gtsam.Pose3(R, np.array([1.0, 2.0, 3.0]))
d = np.array([1e-6, -2e-6, 3e-6, 4e-6, -5e-6, 6e-6])
pm("Pret+", P.retract(d).matrix())
pm("Pret-", P.retract(-d).matrix())
b0 = gtsam.imuBias.ConstantBias(np.array([0.01, -0.02, 0.03]), np.array([0.001, 0.002, -0.003]))
pim = gtsam.PreintegratedCombinedMeasurements(make_pim_params(), b0)
for i in range(200):
    a = np.array([0.1 * i / 200, -0.05, 9.81 + 0.001 * i])
    w = np.array([0.01, -0.02 * i / 200, 0.03])
    pim.integrateMeasurement(a, w, 0.003)
pm("deltaRij", pim.deltaRij().matrix())
pm("deltaPij", pim.deltaPij())
pm("deltaVij", pim.deltaVij())
pm("cov", pim.preintMeasCov())
ns = pim.predict(gtsam.NavState(P, np.array([0.4, 0.1, -0.05])), b0)
pm("predP", ns.pose().matrix())
pm("predV", ns.velocity())
vals = gtsam.Values()
vals.insert(X(1), P); vals.insert(V(1), np.array([0.05, 0.45, -0.01])); vals.insert(B(1), b0)
ff = F.flow_factor(gtsam.noiseModel.Isotropic.Sigma(2, 0.25), X(1), V(1), B(1), np.array([0.02, 0.17]),
                   np.array([0.011, -0.007, 0.002]))
pm("flowAb", ff.linearize(vals).augmentedJacobian())
rf = F.range_factor(gtsam.noiseModel.Isotropic.Sigma(1, 0.5), X(1), 2.7)
pm("rngAb", rf.linearize(vals).augmentedJacobian())
yf = F.yaw_prior_factor(gtsam.noiseModel.Isotropic.Sigma(1, 0.5), X(1), 0.0995)
pm("yawAb", yf.linearize(vals).augmentedJacobian())
print(f"wrap {F._wrap(-3.5):.17g} {F._wrap(3.5):.17g}")
# part 2 factors
pm("hdgAb", F.heading_factor(gtsam.noiseModel.Isotropic.Sigma(1, 0.0026), X(1), 0.0981).linearize(vals).augmentedJacobian())
pm("yrAb", F.yawrate_factor(gtsam.noiseModel.Isotropic.Sigma(1, 0.0028), B(1), 0.0021, 0.0013).linearize(vals).augmentedJacobian())
pm("tagAb", F.tag_factor(gtsam.noiseModel.Diagonal.Sigmas(np.array([0.05, 0.05, 0.0873])), X(1),
                         (1.02, 1.97, 0.11)).linearize(vals).augmentedJacobian())
pm("gnssAb", F.gnss_factor(gtsam.noiseModel.Diagonal.Sigmas(np.array([0.5, 0.5, 0.3, 0.3])), X(1), V(1),
                           (1.1, 2.2, 0.04, 0.5)).linearize(vals).augmentedJacobian())

# one FGO keyframe through the real smoother (see probe.cpp): 0 = IMU only, 1 = + range (the yaw-cap gate is not yet
# checked, < 140 ms after init), 2 = + flow; 3 = as 2 with a forced gate check (closed), 4 = as 3 with the gate prior's
# attitude variances inflated so that the gate opens and the cap factor is added (§9.4 gate, ruling 2026-10-09)
from fgo_core import FGO
for variant in range(5):
    f = FGO(window=0.25, kf_dt=1.0 / 30.0, lm_maxiter=2)
    f.init(np.array([-0.0009, 0.0009, 9.8107]), 0.075, 10.0)
    f.no_yawcap = variant == 0
    if variant >= 3:
        f.t_yawchk = 9.0
    if variant == 4:
        f.cov_gate = f.cov_gate.copy()
        for i in range(3):
            f.cov_gate[i, i] = 0.02
    for i in range(11):
        f.integrate_imu(np.array([0.1 * i / 200, -0.05, 9.81 + 0.001 * i]), np.array([0.01, -0.02 * i / 200, 0.03]), 0.003)
    f.keyframe(10.0 + 1.0 / 30.0, flow=((np.array([0.02, 0.17]), True, 0.9) if variant >= 2 else None),
               omega=np.array([0.011, -0.007, 0.002]), rng=(0.08 if variant >= 1 else None))
    M = f.prev_pose.matrix()
    vals = list(M[:3, :].reshape(-1)) + list(f.prev_vel) + list(f.prev_bias.vector())
    print(f"kf{variant}" + "".join(f" {v:.17g}" for v in vals))
    if variant >= 3:
        print(f"gate{variant}" + "".join(f" {float(v):.17g}" for v in f.yawgate_log[0]))
