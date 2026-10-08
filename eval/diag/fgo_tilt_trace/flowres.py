"""Flow residual against the shared model evaluated on GROUND TRUTH (velocity, attitude, height) + raw gyro, per 0.5 s bin."""
import sys, numpy as np
sys.path.insert(0, "/home/makerspace/thesis_ws/src/estimators")
from measurement_models import h_flow_pose
sys.path.insert(0, ".")
from tilt import q2rpy
Z = np.load(sys.argv[1]); a, b = float(sys.argv[2]), float(sys.argv[3])
gt, fl, imu = Z["gt"], Z["flow"], Z["imu"]; tg = gt[:, 0]
v = np.stack([np.gradient(gt[:, i], tg) for i in (1, 2, 3)], 1)
for lo in np.arange(a, b, 0.5):
    m = (fl[:, 0] >= lo) & (fl[:, 0] < lo + 0.5) & (fl[:, 3] > 0)
    res = []
    for t, fx, fy, val, inl, nf in fl[m]:
        j = np.searchsorted(tg, t); j = min(max(j, 1), len(tg) - 1)
        q = gt[j, 4:8]; x, y, z, w = q
        R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                      [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                      [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
        k = (imu[:, 0] > t - 1 / 30) & (imu[:, 0] <= t)
        om = imu[k, 4:7].mean(0) if k.any() else np.zeros(3)
        vw = np.array([np.interp(t, tg, v[:, i]) for i in range(3)])
        res.append(np.array([fx, fy]) - h_flow_pose(R, vw, np.interp(t, tg, gt[:, 3]), om))
    res = np.array(res)
    if len(res):
        print(f"{lo:5.1f} z {np.interp(lo+0.25, tg, gt[:, 3]):.2f} vz {np.interp(lo+0.25, tg, v[:, 2]):+.2f} n {len(res):2d} "
              f"res x {res[:,0].mean():+.3f}/{res[:,0].std():.3f}  y {res[:,1].mean():+.3f}/{res[:,1].std():.3f} rad/s")
