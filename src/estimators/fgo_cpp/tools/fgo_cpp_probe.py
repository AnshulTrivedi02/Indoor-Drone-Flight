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
