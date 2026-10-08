#!/usr/bin/env python3
"""Apply the binit0 change (user ruling 2026-10-09) to an estimators tree given as argv[1]."""
import os, sys
root = sys.argv[1]
p = os.path.join(root, "fgo", "fgo_core.py")
s = open(p).read()
old = "    p.setBiasAccOmegaInit(np.diag([0.2**2]*3 + [0.043633**2]*3))\n"
new = ("    # ZERO (user ruling 2026-10-09, METHODOLOGY \"FGO noise-model correction\"; D18 MODEL CORRECTION): in GTSAM 4.2.1\n"
       "    # CombinedImuFactor::integrateMeasurement (CombinedImuFactor.cpp:138-163) adds biasAccOmegaInt as extra IMU white\n"
       "    # noise at EVERY sample, not as an initial bias covariance. EKF3's initial bias sigmas stay in the B(0) prior only.\n"
       "    p.setBiasAccOmegaInit(np.zeros((6, 6)))\n")
assert s.count(old) == 1
open(p, "w").write(s.replace(old, new))
p = os.path.join(root, "fgo_cpp", "src", "fgo_core.cpp")
s = open(p).read()
old = ("  gtsam::Vector6 d;\n"
       "  d << 0.2 * 0.2, 0.2 * 0.2, 0.2 * 0.2, 0.043633 * 0.043633, 0.043633 * 0.043633, 0.043633 * 0.043633;\n"
       "  p->setBiasAccOmegaInit(d.asDiagonal().toDenseMatrix());\n")
new = ("  // ZERO (user ruling 2026-10-09, METHODOLOGY \"FGO noise-model correction\"; D18 MODEL CORRECTION): in GTSAM 4.2.1\n"
       "  // CombinedImuFactor::integrateMeasurement (CombinedImuFactor.cpp:138-163) adds biasAccOmegaInt as extra IMU white\n"
       "  // noise at EVERY sample, not as an initial bias covariance. EKF3's initial bias sigmas stay in the B(0) prior only.\n"
       "  p->setBiasAccOmegaInit(gtsam::Matrix6::Zero());\n")
assert s.count(old) == 1
open(p, "w").write(s.replace(old, new))
print("patched", root)
