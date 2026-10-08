"""Does setBiasAccOmegaInit enter the preintegrated covariance in this gtsam build? (diagnostic)"""
import sys, numpy as np, gtsam
sys.path.insert(0, "/home/makerspace/thesis_ws/src/estimators/fgo"); sys.path.insert(0, "/home/makerspace/thesis_ws/src/estimators")
import fgo_core
print("gtsam", gtsam.__version__ if hasattr(gtsam, "__version__") else "?")
for lab, binit in [("thesis (binit 0.2/0.0436)", True), ("binit = 0", False)]:
    p = fgo_core.make_pim_params()
    if not binit:
        p.setBiasAccOmegaInit(np.zeros((6, 6)))
    pim = gtsam.PreintegratedCombinedMeasurements(p, gtsam.imuBias.ConstantBias())
    for _ in range(11):
        pim.integrateMeasurement(np.array([0, 0, 9.81]), np.zeros(3), 0.003)
    C = pim.preintMeasCov()
    d = np.sqrt(np.diag(C))
    print(lab, "dt", pim.deltaTij(), "sd rot (deg)", np.degrees(d[0:3]).round(5), "pos", d[3:6].round(7), "vel", d[6:9].round(6),
          "ba", d[9:12].round(6), "bg", d[12:15].round(7))
    print("   rot-bg cross", C[0, 12], " vel-ba cross", C[6, 9])
