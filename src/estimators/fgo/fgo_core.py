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
    def __init__(self, window=1.0, kf_dt=1.0/30.0, solver="batch"):
        self.kf_dt = kf_dt
        # BatchFixedLagSmoother re-solves the window with LM each step (robust,
        # FGO_DESIGN §6 "--solver batch"); Incremental wraps iSAM2 (faster, but its
        # marginalisation + Python CustomFactors is fragile — cascades on error).
        self.smoother = (gtsam_unstable.BatchFixedLagSmoother(window) if solver == "batch"
                         else gtsam_unstable.IncrementalFixedLagSmoother(window))
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
        g.add(F.yaw_prior_factor(self.yaw_noise, X(k), self.yaw_ref))     # §9.4
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
