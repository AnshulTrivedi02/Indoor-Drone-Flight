"""FGO core — PURE (gtsam + numpy in, estimates out). No ROS, no bag, no sim-time
source inside. The replay harness and a future ROS2 node are thin wrappers that
only call init()/integrate_imu()/keyframe() and read latest(). Follows
FGO_DESIGN.md: IncrementalFixedLagSmoother, IMU-clock keyframes (§9.1),
CombinedImuFactor over every IMU sample (§5), shared h_flow/h_range factors,
weak yaw-prior per keyframe (§9.4).
"""
import numpy as np
import gtsam
from gtsam import Pose3, Rot3, NavState, PreintegrationCombinedParams, \
    PreintegratedCombinedMeasurements, CombinedImuFactor
from gtsam import PriorFactorPose3, PriorFactorConstantBias
from gtsam.symbol_shorthand import X, V, B
import gtsam_unstable
import factors as F


def _tsmap(d):
    m = gtsam_unstable.FixedLagSmootherKeyTimestampMap()
    for k, t in d.items():
        m.insert((k, t))
    return m


def make_pim_params():
    p = PreintegrationCombinedParams.MakeSharedU(9.81)           # ENU Z-up, +9.81 at rest
    p.setAccelerometerCovariance(np.eye(3) * 1.53125e-3)         # NSE*sqrt(dt), FGO §5
    p.setGyroscopeCovariance(np.eye(3) * 2.8125e-6)
    p.setBiasAccCovariance(np.eye(3) * 5.0e-6)
    p.setBiasOmegaCovariance(np.eye(3) * 1.25e-8)
    p.setIntegrationCovariance(np.eye(3) * 1e-8)                 # conditioning floor (unmatched)
    p.setBiasAccOmegaInit(np.diag([0.2**2]*3 + [0.043633**2]*3))
    return p


GYRO_B0 = 0.043633            # EKF3 initial gyro-bias 1σ (rad/s), FGO §5/§8
ACCEL_B0 = 0.2                # EKF3 initial accel-bias 1σ (m/s²)


class FGO:
    def __init__(self, window=1.0, kf_dt=1.0/30.0, solver="batch", lm_maxiter=2):
        self.kf_dt = kf_dt
        # BatchFixedLagSmoother re-solves the window with LM each step and is ROBUST
        # (FGO_DESIGN §6). The incremental iSAM2 path is unusable here: its
        # marginalizeLeaves cascades ("variable not in VectorValues" at the lag boundary)
        # whenever a Python flow CustomFactor is in the graph (confirmed: works without
        # flow; ISAM2Params QR/no-cache, typed accessors, relin-disable all fail; a GTSAM
        # limitation, not our logic). We stay on batch and make it affordable by capping LM
        # iterations — each step is warm-started from the previous window solution, so it is
        # already near-converged (default full-LM was ~101 ms/step; 2 iters ~ 33 ms budget).
        if solver == "batch":
            lm = gtsam.LevenbergMarquardtParams()
            lm.setMaxIterations(lm_maxiter)
            self.smoother = gtsam_unstable.BatchFixedLagSmoother(window, lm)
        else:
            ip = gtsam.ISAM2Params(); ip.setFactorization("QR")
            ip.cacheLinearizedFactors = False; ip.findUnusedFactorSlots = True
            self.smoother = gtsam_unstable.IncrementalFixedLagSmoother(window, ip)
        self.pim = PreintegratedCombinedMeasurements(make_pim_params(),
                                                     gtsam.imuBias.ConstantBias(np.zeros(3), np.zeros(3)))
        self.flow_noise = gtsam.noiseModel.Isotropic.Sigma(2, 0.25)   # FLOW_M_NSE
        self.range_noise = gtsam.noiseModel.Isotropic.Sigma(1, 0.5)   # RNG_M_NSE
        self.yaw_noise = gtsam.noiseModel.Isotropic.Sigma(1, 0.5)     # EK3_YAW_M_NSE, §9.4
        self.k = 0
        self.prev_pose = self.prev_vel = self.prev_bias = None
        self.t_last = None
        self.yaw_ref = 0.0
        self.n_flow = self.n_range = self.n_imu = 0
        self.last = None            # (t, Pose3, vel)

    def init(self, accel_mean, first_range, t0):
        ax, ay, az = accel_mean
        roll0 = np.arctan2(ay, az)
        pitch0 = np.arctan2(-ax, np.hypot(ay, az))
        pose0 = Pose3(Rot3.Ypr(0.0, pitch0, roll0), np.array([0.0, 0.0, first_range + 0.12]))
        vel0 = np.zeros(3)
        bias0 = gtsam.imuBias.ConstantBias(np.zeros(3), np.zeros(3))
        g = gtsam.NonlinearFactorGraph(); vals = gtsam.Values()
        # X(0) prior: [roll,pitch,yaw, x,y,z] tangent sigmas (§8); x,y,yaw gauge-fixed
        pose_sig = np.array([np.radians(2), np.radians(2), 1e-3, 1e-3, 1e-3, 0.5])
        g.add(PriorFactorPose3(X(0), pose0, gtsam.noiseModel.Diagonal.Sigmas(pose_sig)))
        g.add(gtsam.PriorFactorVector(V(0), vel0, gtsam.noiseModel.Isotropic.Sigma(3, 0.1)))
        bias_sig = np.array([ACCEL_B0]*3 + [GYRO_B0]*3)
        g.add(PriorFactorConstantBias(B(0), bias0, gtsam.noiseModel.Diagonal.Sigmas(bias_sig)))
        vals.insert(X(0), pose0); vals.insert(V(0), vel0); vals.insert(B(0), bias0)
        self.smoother.update(g, vals, _tsmap({X(0): t0, V(0): t0, B(0): t0}))
        self.prev_pose, self.prev_vel, self.prev_bias = pose0, vel0, bias0
        self.t_last = t0; self.yaw_ref = 0.0
        self.last = (t0, pose0, vel0)

    def integrate_imu(self, accel, gyro, dt):
        if 0 < dt < 0.2:
            self.pim.integrateMeasurement(np.asarray(accel, float), np.asarray(gyro, float), dt)
            self.n_imu += 1

    def keyframe(self, t, flow=None, omega=None, rng=None):
        """Create keyframe k on the IMU clock. flow=(flow_xy, valid, inlier),
        omega = FLU rates for the flow factor, rng = range or None."""
        if self.pim.deltaTij() <= 0:
            return                                    # no IMU since last keyframe — skip (§8)
        km1, k = self.k, self.k + 1
        pred = self.pim.predict(NavState(self.prev_pose, self.prev_vel), self.prev_bias)
        Xk, Vk = pred.pose(), pred.velocity()
        g = gtsam.NonlinearFactorGraph(); vals = gtsam.Values()
        vals.insert(X(k), Xk); vals.insert(V(k), Vk); vals.insert(B(k), self.prev_bias)
        g.add(CombinedImuFactor(X(km1), V(km1), X(k), V(k), B(km1), B(k), self.pim))
        # §9.4 yaw cap: anchor to THIS keyframe's IMU-predicted yaw -> zero innovation
        # (matches EKF3 fuseEulerYaw(PREDICTED), MagFusion.cpp:1062-1064/:970), bounding
        # the yaw marginal without injecting absolute heading.
        g.add(F.yaw_prior_factor(self.yaw_noise, X(k), Xk.rotation().yaw()))
        if rng is not None and 0.05 <= rng <= 40.0:
            g.add(F.range_factor(self.range_noise, X(k), rng)); self.n_range += 1
        if flow is not None:
            flow_xy, valid, inlier = flow
            if valid and inlier > 0.0 and abs(flow_xy[0]) < 4.2 and abs(flow_xy[1]) < 4.2:
                g.add(F.flow_factor(self.flow_noise, X(k), V(k), B(k), flow_xy, omega)); self.n_flow += 1
        ts = {X(k): t, V(k): t, B(k): t}
        self.smoother.update(g, vals, _tsmap(ts))
        est = self.smoother.calculateEstimate()
        self.prev_pose = est.atPose3(X(k)); self.prev_vel = est.atVector(V(k)); self.prev_bias = est.atConstantBias(B(k))
        self.pim.resetIntegrationAndSetBias(self.prev_bias)
        self.k = k; self.t_last = t
        self.last = (t, self.prev_pose, self.prev_vel)      # causal: newest keyframe only (§6)

    def latest(self):
        return self.last
