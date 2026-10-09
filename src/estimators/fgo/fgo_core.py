"""FGO core — PURE (gtsam + numpy in, estimates out). No ROS, no bag, no sim-time
source inside. The replay harness and a future ROS2 node are thin wrappers that
only call init()/integrate_imu()/keyframe() and read latest(). Follows
FGO_DESIGN.md: IncrementalFixedLagSmoother, IMU-clock keyframes (§9.1),
CombinedImuFactor over every IMU sample (§5), shared h_flow/h_range factors,
weak zero-innovation yaw prior, variance-gated as EKF3 (§9.4).
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
    # ZERO (user ruling 2026-10-09, METHODOLOGY "FGO noise-model correction"; D18 MODEL CORRECTION): in GTSAM 4.2.1
    # CombinedImuFactor::integrateMeasurement (CombinedImuFactor.cpp:138-163) adds biasAccOmegaInt as extra IMU white
    # noise at EVERY sample, not as an initial bias covariance. EKF3's initial bias sigmas stay in the B(0) prior only.
    p.setBiasAccOmegaInit(np.zeros((6, 6)))
    return p


GYRO_B0 = 0.043633            # EKF3 initial gyro-bias 1σ (rad/s), FGO §5/§8
ACCEL_B0 = 0.2                # EKF3 initial accel-bias 1σ (m/s²)
# §9.4 yaw cap, VARIANCE-GATED (user ruling 2026-10-09, METHODOLOGY "MODEL AUDIT RESULT ... RULINGS" item 2: a
# correction of the implementation to its stated design). As EKF3's fuseEulerYaw(PREDICTED) and ukf_core.update_yaw_pseudo:
YAW_DT = 0.14                 # fire opportunity every 140 ms (MagFusion.cpp:263; ukf_core YAW_DT)
ATT_VAR_GATE = 0.04           # fire only if trace(predicted attitude cov) > 0.04 rad^2 (EKF3's quaternion trace > 0.01,
#                               MagFusion.cpp:274, mapped to the attitude tangent as in ukf_core ATT_VAR_GATE)


class FGO:
    def __init__(self, window=1.0, kf_dt=1.0/30.0, solver="batch", lm_maxiter=2, fwd_sigma=None, fwd_gate=9.0, fwd_robust=None,
                 log_cov=False):
        self.kf_dt = kf_dt
        self._window, self._lm_maxiter, self._solver = window, lm_maxiter, solver   # kept for reanchor() (experiment T)
        self.tag_noise = None      # experiment T: set by reanchor(); None = no tag factors (every other use)
        # Diagnostic (Phase 5b): run the gate-only filtering covariance recursion and log the
        # keyframe position/yaw covariance, in any arm. It never touches the smoother.
        self.log_cov = log_cov or fwd_sigma is not None
        self.cov_log = []          # (t, world pos cov xx, xy, yy, yaw var)
        # Phase 4 forward camera: None = baseline (no forward factors, no gate recursion).
        self.fwd_sigma, self.fwd_gate = fwd_sigma, fwd_gate
        self.fwd_log = []          # (t, kind, nis, accepted)
        self.cov_prev = None       # gate-only filtering covariance of (X, V, B) at the last keyframe
        # §9.4 yaw-cap gate (ruling 2026-10-09): the same gate-only recursion, run whenever the cap is active
        # (independent of log_cov, so cov_prev and reanchor() keep their old semantics); equal to cov_prev under log_cov.
        self.cov_gate = None
        self.t_yawchk = None
        self.yawgate_log = []      # (t, k, trace of the predicted attitude cov, fired) per check opportunity
        self.n_yaw_check = self.n_yaw_fire = 0
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
        if fwd_sigma is not None:
            self.heading_noise = gtsam.noiseModel.Isotropic.Sigma(1, fwd_sigma["psi"])
            if fwd_robust:                                  # F1 (offline): robust heading factor, gate removed by the caller
                kind, k = fwd_robust.split(":")
                est = (gtsam.noiseModel.mEstimator.Huber.Create(float(k)) if kind == "huber"
                       else gtsam.noiseModel.mEstimator.Cauchy.Create(float(k)))
                self.heading_noise = gtsam.noiseModel.Robust.Create(est, self.heading_noise)
            self.yawrate_noise = (gtsam.noiseModel.Isotropic.Sigma(1, fwd_sigma["omega"])
                                  if fwd_sigma.get("omega") is not None else None)
        self.k = 0
        self.prev_pose = self.prev_vel = self.prev_bias = None
        self.t_last = None
        self.yaw_ref = 0.0
        self.n_flow = self.n_range = self.n_imu = 0
        self.last = None            # (t, Pose3, vel)

    def init(self, accel_mean, first_range, t0, yaw0=0.0, yaw_sigma=None):
        ax, ay, az = accel_mean
        roll0 = np.arctan2(ay, az)
        pitch0 = np.arctan2(-ax, np.hypot(ay, az))
        pose0 = Pose3(Rot3.Ypr(yaw0, pitch0, roll0), np.array([0.0, 0.0, first_range + 0.12]))   # yaw0: F3 only
        vel0 = np.zeros(3)
        bias0 = gtsam.imuBias.ConstantBias(np.zeros(3), np.zeros(3))
        g = gtsam.NonlinearFactorGraph(); vals = gtsam.Values()
        # X(0) prior: [roll,pitch,yaw, x,y,z] tangent sigmas (§8); x,y,yaw gauge-fixed
        pose_sig = np.array([np.radians(2), np.radians(2), 1e-3, 1e-3, 1e-3, 0.5])
        if yaw_sigma is not None:                           # F3 only: a consistent prior sigma = the injected yaw offset
            pose_sig[2] = yaw_sigma
        g.add(PriorFactorPose3(X(0), pose0, gtsam.noiseModel.Diagonal.Sigmas(pose_sig)))
        g.add(gtsam.PriorFactorVector(V(0), vel0, gtsam.noiseModel.Isotropic.Sigma(3, 0.1)))
        bias_sig = np.array([ACCEL_B0]*3 + [GYRO_B0]*3)
        g.add(PriorFactorConstantBias(B(0), bias0, gtsam.noiseModel.Diagonal.Sigmas(bias_sig)))
        vals.insert(X(0), pose0); vals.insert(V(0), vel0); vals.insert(B(0), bias0)
        self.smoother.update(g, vals, _tsmap({X(0): t0, V(0): t0, B(0): t0}))
        if getattr(self, "batch_record", False):          # F2 (offline): keep every factor for one batch solve
            self.all_g = gtsam.NonlinearFactorGraph(); self.all_g.push_back(g)
            self.all_est = {X(0): pose0, V(0): np.array(vel0, float), B(0): bias0}; self.key_t = []
        if self.log_cov:
            self.cov_prev = np.diag(np.concatenate([pose_sig, [0.1] * 3, bias_sig]) ** 2)
        self.cov_gate = np.diag(np.concatenate([pose_sig, [0.1] * 3, bias_sig]) ** 2)
        self.t_yawchk = t0                                # as ukf_replay: the first check 140 ms after init
        self.prev_pose, self.prev_vel, self.prev_bias = pose0, vel0, bias0
        self.t_last = t0; self.yaw_ref = 0.0
        self.last = (t0, pose0, vel0)

    def integrate_imu(self, accel, gyro, dt):
        if 0 < dt < 0.2:
            self.pim.integrateMeasurement(np.asarray(accel, float), np.asarray(gyro, float), dt)
            self.n_imu += 1

    def keyframe(self, t, flow=None, omega=None, rng=None, fwd=None, tag=None, gnss=None):
        """Create keyframe k on the IMU clock. flow=(flow_xy, valid, inlier),
        omega = FLU rates for the flow factor, rng = range or None,
        fwd = (psi | None, omega_meas | None, gyro_z_avg) forward-camera measurements."""
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
        # VARIANCE-GATED (user ruling 2026-10-09, METHODOLOGY "MODEL AUDIT RESULT ... RULINGS" item 2; FGO_DESIGN §9.4):
        # at most one cap per 140 ms check, and only if the trace of THIS keyframe's predicted attitude covariance
        # (gate-only recursion: last keyframe's filtering cov + this IMU factor, before range/flow/forward) > 0.04 rad^2.
        i_yawcap = None
        cap_on = not getattr(self, "no_yawcap", False)   # F3b / after a tag re-anchor: off
        if cap_on and t - self.t_yawchk >= YAW_DT:
            self.t_yawchk = t
            tr = self._att_trace_pred(g, km1, k, Xk, Vk)
            fire = bool(tr > ATT_VAR_GATE)
            self.n_yaw_check += 1; self.n_yaw_fire += fire
            self.yawgate_log.append((t, k, tr, fire))
            if fire:
                i_yawcap = g.size()
                g.add(F.yaw_prior_factor(self.yaw_noise, X(k), Xk.rotation().yaw()))
        if rng is not None and 0.05 <= rng <= 40.0:
            g.add(F.range_factor(self.range_noise, X(k), rng)); self.n_range += 1
        if flow is not None:
            flow_xy, valid, inlier = flow
            if valid and inlier > 0.0 and abs(flow_xy[0]) < 4.2 and abs(flow_xy[1]) < 4.2:
                g.add(F.flow_factor(self.flow_noise, X(k), V(k), B(k), flow_xy, omega)); self.n_flow += 1
        if self.fwd_sigma is not None:
            self._forward_factors(g, vals, t, km1, k, Xk, fwd)
        if tag is not None and self.tag_noise is not None:      # experiment T: tag fix (no gate, pre-registered)
            g.add(F.tag_factor(self.tag_noise, X(k), tag)); self.n_tag = getattr(self, "n_tag", 0) + 1
        if gnss is not None and getattr(self, "gnss_noise", None) is not None:   # experiment O: GNSS fix (no gate)
            g.add(F.gnss_factor(self.gnss_noise, X(k), V(k), gnss)); self.n_gnss = getattr(self, "n_gnss", 0) + 1
        ts = {X(k): t, V(k): t, B(k): t}
        self.smoother.update(g, vals, _tsmap(ts))
        est = self.smoother.calculateEstimate()
        if getattr(self, "batch_record", False):          # F2 (offline): identical factors; latest estimate per key
            if getattr(self, "batch_drop_yawcap", False) and i_yawcap is not None:
                # experiment O hindsight (2026-10-08): the yaw cap anchors to the LIVE predicted yaw; in a whole-flight
                # batch its thousands of copies become information about the live estimate (circular), so the batch
                # record leaves it out. Default False: every earlier use (F2) unchanged.
                for i_ in range(g.size()):
                    if i_ != i_yawcap:
                        self.all_g.push_back(g.at(i_))
            else:
                self.all_g.push_back(g)
            for key in est.keys():                        # a dict: Values.update picks the fixed-size Vector3
                c = chr(gtsam.Symbol(key).chr())              # overload for velocities (stored dynamic) and throws
                self.all_est[key] = (est.atPose3(key) if c == "x" else
                                     (np.array(est.atVector(key), float) if c == "v" else est.atConstantBias(key)))
        if self.log_cov:
            self.cov_prev = self._posterior_cov(g, est, km1, k)
            self.cov_gate = self.cov_prev                     # the same recursion (the gate prior equals cov_prev)
            Rk = est.atPose3(X(k)).rotation().matrix()
            Pw = Rk @ self.cov_prev[3:6, 3:6] @ Rk.T          # body-frame translation tangent -> world
            Hy = F._jac_pose(lambda p_, v_, b_: np.array([p_.rotation().yaw()]), est.atPose3(X(k)), None, None, 1)
            self.cov_log.append((t, Pw[0, 0], Pw[0, 1], Pw[1, 1], float(Hy @ self.cov_prev[0:6, 0:6] @ Hy.T)))
        elif cap_on:
            self.cov_gate = self._posterior_cov(g, est, km1, k, prior=self.cov_gate)
        self.prev_pose = est.atPose3(X(k)); self.prev_vel = est.atVector(V(k)); self.prev_bias = est.atConstantBias(B(k))
        self.pim.resetIntegrationAndSetBias(self.prev_bias)
        self.k = k; self.t_last = t
        if getattr(self, "batch_record", False):
            self.key_t.append((k, t))                        # F2: the created keyframe's key and time
        self.last = (t, self.prev_pose, self.prev_vel)      # causal: newest keyframe only (§6)

    def latest(self):
        return self.last

    # ---------- experiment T: first-fix re-anchor ----------
    def reanchor(self, p_EN, yaw_fix, sig_pos, sig_yaw, vel_EN=None, sig_vel=None, keep_yawcap=False):
        """As EKF3's position reset + ExtNav yaw alignment, and identical to the UKF's (measurement_models.
        reanchor_jacobian): rigidly transform the newest keyframe state about the vertical so that (x, y, yaw) = the
        fix, rotate the horizontal velocity by the yaw change, and RESTART the smoother (same window, solver and LM
        cap) with a prior on that state: x, y, yaw sigmas = the fix noise; roll, pitch, z, velocity and bias sigmas =
        the diagonal of the gate-only filtering covariance (cov_prev; cross-covariances zeroed, as the UKF re-anchor).
        The new key sits at the newest keyframe's time; the IMU preintegration since then is kept. From here on the
        yaw cap is off (EKF3 with an ExtNav yaw source fuses its predicted yaw only before yaw alignment), and tag
        factors are added. A whole-flight batch record (batch_record) restarts here."""
        r, pch, y = self.prev_pose.rotation().rpy()
        d = F._wrap(yaw_fix - y); c, s_ = np.cos(d), np.sin(d); R3 = np.array([[c, -s_, 0], [s_, c, 0], [0, 0, 1.0]])
        pose = Pose3(Rot3.Ypr(yaw_fix, pch, r), np.array([p_EN[0], p_EN[1], self.prev_pose.translation()[2]]))
        vel = R3 @ np.asarray(self.prev_vel, float); bias = self.prev_bias
        C = self.cov_prev if self.cov_prev is not None else np.diag(
            np.concatenate([[np.radians(2)] * 2 + [1e-3] * 3 + [0.5], [0.1] * 3, [ACCEL_B0] * 3 + [GYRO_B0] * 3]) ** 2)
        pose_sig = np.array([np.sqrt(C[0, 0]), np.sqrt(C[1, 1]), sig_yaw, sig_pos, sig_pos, np.sqrt(C[5, 5])])
        vel_sig = np.sqrt(np.diag(R3 @ C[6:9, 6:9] @ R3.T)); bias_sig = np.sqrt(np.diag(C[9:15, 9:15]))
        if vel_EN is not None:                      # experiment O: velocity reset to the GNSS sample (as EKF3's alignment)
            vel = np.array([vel_EN[0], vel_EN[1], vel[2]]); vel_sig[0] = vel_sig[1] = sig_vel
        k = self.k + 1; t = self.t_last
        if self._solver == "batch":
            lm = gtsam.LevenbergMarquardtParams(); lm.setMaxIterations(self._lm_maxiter)
            self.smoother = gtsam_unstable.BatchFixedLagSmoother(self._window, lm)
        else:
            raise NotImplementedError("reanchor: batch solver only")
        g = gtsam.NonlinearFactorGraph(); vals = gtsam.Values()
        g.add(PriorFactorPose3(X(k), pose, gtsam.noiseModel.Diagonal.Sigmas(pose_sig)))
        g.add(gtsam.PriorFactorVector(V(k), vel, gtsam.noiseModel.Diagonal.Sigmas(vel_sig)))
        g.add(PriorFactorConstantBias(B(k), bias, gtsam.noiseModel.Diagonal.Sigmas(bias_sig)))
        vals.insert(X(k), pose); vals.insert(V(k), vel); vals.insert(B(k), bias)
        self.smoother.update(g, vals, _tsmap({X(k): t, V(k): t, B(k): t}))
        if getattr(self, "batch_record", False):
            self.all_g = gtsam.NonlinearFactorGraph(); self.all_g.push_back(g)
            self.all_est = {X(k): pose, V(k): vel, B(k): bias}; self.key_t = [(k, t)]
        if self.log_cov:
            self.cov_prev = np.diag(np.concatenate([pose_sig, vel_sig, bias_sig]) ** 2)
        self.cov_gate = np.diag(np.concatenate([pose_sig, vel_sig, bias_sig]) ** 2)   # yaw-cap gate (keep_yawcap)
        self.prev_pose, self.prev_vel = pose, vel
        self.k = k; self.no_yawcap = not keep_yawcap
        self.tag_noise = gtsam.noiseModel.Diagonal.Sigmas(np.array([sig_pos, sig_pos, sig_yaw]))
        self.last = (t, pose, vel)

    # ---------- Phase 4: chi-square gate via a gate-only filtering covariance ----------
    # The Python BatchFixedLagSmoother exposes no marginal covariance, so the predicted
    # covariance for the gate comes from a recursion alongside the smoother: the previous
    # keyframe's marginal of (X, V, B) as a Gaussian prior, plus this keyframe's factors
    # linearised at the current values, over the 30-dim (X,V,B)_{k-1} + (X,V,B)_k space.
    # It is used ONLY to gate; the smoother's solution is untouched.
    _DIMS = (6, 3, 6)

    def _info(self, factors, values, km1, k, prior=None):
        keys = [X(km1), V(km1), B(km1), X(k), V(k), B(k)]
        off, o = {}, 0
        for key, dm in zip(keys, self._DIMS * 2):
            off[key] = (o, dm); o += dm
        L = np.zeros((o, o))
        L[:15, :15] = np.linalg.inv(self.cov_prev if prior is None else prior)
        for i in range(factors.size()):
            jf = factors.at(i).linearize(values)
            A = jf.jacobian()[0]
            fk = list(jf.keys())
            idx = np.concatenate([np.arange(off[key][0], off[key][0] + off[key][1]) for key in fk])
            L[np.ix_(idx, idx)] += A.T @ A
        return L

    def _values(self, km1, k, pose_k, vel_k, bias_k, src=None):
        v = gtsam.Values()
        if src is None:
            v.insert(X(km1), self.prev_pose); v.insert(V(km1), self.prev_vel); v.insert(B(km1), self.prev_bias)
        else:
            v.insert(X(km1), src.atPose3(X(km1)) if src.exists(X(km1)) else self.prev_pose)
            v.insert(V(km1), src.atVector(V(km1)) if src.exists(V(km1)) else self.prev_vel)
            v.insert(B(km1), src.atConstantBias(B(km1)) if src.exists(B(km1)) else self.prev_bias)
        v.insert(X(k), pose_k); v.insert(V(k), vel_k); v.insert(B(k), bias_k)
        return v

    def _forward_factors(self, g, vals, t, km1, k, Xk, fwd):
        if fwd is None:
            return
        psi, om, gz = fwd
        Vk = vals.atVector(V(k))
        cov = np.linalg.inv(self._info(g, self._values(km1, k, Xk, Vk, self.prev_bias), km1, k))
        cXX, cBB = cov[15:21, 15:21], cov[24:30, 24:30]
        if psi is not None:
            f = F.heading_factor(self.heading_noise, X(k), psi)
            e = F._wrap(Xk.rotation().yaw() - psi)
            Hx = F._jac_pose(lambda p_, v_, b_: np.array([F._wrap(p_.rotation().yaw() - psi)]), Xk, None, None, 1)
            S = float(Hx @ cXX @ Hx.T) + self.fwd_sigma["psi"] ** 2
            nis = e * e / S
            ok = bool(np.isfinite(nis) and nis <= self.fwd_gate)
            if ok:
                g.add(f)
            self.fwd_log.append((t, 0, float(nis), ok, S))
        if om is not None:
            e = (gz - self.prev_bias.gyroscope()[2]) - om
            S = float(cBB[5, 5]) + self.fwd_sigma["omega"] ** 2
            nis = e * e / S
            ok = bool(np.isfinite(nis) and nis <= self.fwd_gate)
            if ok:
                g.add(F.yawrate_factor(self.yawrate_noise, B(k), om, gz))
            self.fwd_log.append((t, 1, float(nis), ok, S))

    def _posterior_cov(self, g, est, km1, k, prior=None):
        v = self._values(km1, k, est.atPose3(X(k)), est.atVector(V(k)), est.atConstantBias(B(k)), src=est)
        cov = np.linalg.inv(self._info(g, v, km1, k, prior))[15:30, 15:30]
        return 0.5 * (cov + cov.T)

    def _att_trace_pred(self, g, km1, k, Xk, Vk):
        """§9.4 gate quantity: trace of X(k)'s PREDICTED rotation-tangent covariance (rad^2), from the gate-only
        recursion: the previous keyframe's filtering covariance (cov_gate) + this keyframe's IMU factor (g holds
        only it when called), linearised at the IMU prediction. The trace is the same in the body and world frames.
        As EKF3 / the UKF, the check sees the predicted covariance, before that step's other fusions."""
        cov = np.linalg.inv(self._info(g, self._values(km1, k, Xk, Vk, self.prev_bias), km1, k, self.cov_gate))
        return float(cov[15, 15] + cov[16, 16] + cov[17, 17])   # left to right, as the C++
