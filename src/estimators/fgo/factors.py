"""Custom GTSAM factors for the FGO — flow, range, and the weak yaw-prior.

PURE: no ROS, no bag, no sim-time. Each factor imports the SAME `h_flow_pose` /
`h_range` the UKF uses (fairness made structural, FGO_DESIGN §2). Jacobians are
numerical central differences on the manifold (FGO_DESIGN §2 "Jacobians"), so the
Jacobian is by construction the derivative of the shared model — no second copy.
"""
import numpy as np
import gtsam
from gtsam import CustomFactor
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from measurement_models import h_flow_pose, CAM_OFFSET, RANGE_LEVER, H_MIN, h_heading, h_yawrate

EPS = 1e-6


def _wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


# ---------- flow factor: 2-DOF on X(k), V(k), B(k) ----------
def flow_factor(noise, key_x, key_v, key_b, flow_meas, omega_meas):
    """Predicted raw angular flow - measured, in the camera-optical frame.
    omega is bias-corrected inside (FGO §2: omega = omega_meas - B(k).gyro), so
    the flow residual can inform gyro bias through the rotational term."""
    flow_meas = np.asarray(flow_meas, float)

    def err(pose, vel, bias):
        R = pose.rotation().matrix()
        p_U = pose.translation()[2]
        omega = omega_meas - bias.gyroscope()
        return h_flow_pose(R, vel, p_U, omega) - flow_meas

    def efun(this, values, H):
        pose = values.atPose3(key_x); vel = values.atVector(key_v); bias = values.atConstantBias(key_b)
        e = err(pose, vel, bias)
        if H is not None:
            H[0] = _jac_pose(err, pose, vel, bias, 2)
            H[1] = _jac_vec(err, pose, vel, bias, 2)
            H[2] = _jac_bias(err, pose, vel, bias, 2)
        return e
    return CustomFactor(noise, [key_x, key_v, key_b], efun)


# ---------- range factor: 1-DOF on X(k) ----------
def range_factor(noise, key_x, range_meas):
    """Flat-floor rangefinder height = base_link height - lever (FGO §3)."""
    def err(pose, vel, bias):
        return np.array([pose.translation()[2] - RANGE_LEVER - range_meas])

    def efun(this, values, H):
        pose = values.atPose3(key_x)
        e = err(pose, None, None)
        if H is not None:
            H[0] = _jac_pose(err, pose, None, None, 1)
        return e
    return CustomFactor(noise, [key_x], efun)


# ---------- weak yaw cap: 1-DOF zero-innovation anchor on yaw(X(k)) (FGO §9.4) ----------
def yaw_prior_factor(noise, key_x, yaw_ref):
    """Weak (0.5 rad) yaw cap on the yaw DOF only — bounds the yaw marginal so it
    does not free-drift, matching EKF3's fuseEulerYaw(PREDICTED). EKF3 sets the yaw
    innovation to EXACTLY ZERO for the PREDICTED method
    (AP_NavEKF3_MagFusion.cpp:1062-1064: `case PREDICTED: innovYaw = 0.0f`) against
    `yawAngPredicted` = the current *propagated* state yaw (:970), so it caps
    variance WITHOUT injecting absolute heading. To match, the caller passes
    yaw_ref = the keyframe's IMU-PREDICTED yaw (from pim.predict), NOT a fixed
    gauge value — so the error is ~0 at the linearisation point (zero innovation)
    and this factor bounds the yaw marginal rather than anchoring it absolutely.
    (An absolute anchor to a fixed yaw would be stronger than EKF3/UKF and inject
    heading — see METHODOLOGY.) Wrapped, 1-DOF, R = EK3_YAW_M_NSE 0.5 rad."""
    def err(pose, vel, bias):
        return np.array([_wrap(pose.rotation().yaw() - yaw_ref)])

    def efun(this, values, H):
        pose = values.atPose3(key_x)
        e = err(pose, None, None)
        if H is not None:
            H[0] = _jac_pose(err, pose, None, None, 1)
        return e
    return CustomFactor(noise, [key_x], efun)


# ---------- forward camera (Phase 4): heading on X(k), yaw rate on B(k) ----------
def heading_factor(noise, key_x, psi_meas):
    """Forward-camera heading relative to the corridor axis: wrap(h_heading(yaw) - psi),
    the SAME shared model the UKF uses (measurement_models.h_heading)."""
    def err(pose, vel, bias):
        return np.array([_wrap(h_heading(pose.rotation().yaw()) - psi_meas)])

    def efun(this, values, H):
        pose = values.atPose3(key_x)
        e = err(pose, None, None)
        if H is not None:
            H[0] = _jac_pose(err, pose, None, None, 1)
        return e
    return CustomFactor(noise, [key_x], efun)


def yawrate_factor(noise, key_b, omega_meas, gyro_z_avg):
    """Forward-camera yaw rate: h_yawrate(gyro_z_avg, b_gz) - omega, on the bias key
    (GTSAM bias is rate form, FLU). SAME shared model as the UKF."""
    def err(pose, vel, bias):
        return np.array([h_yawrate(gyro_z_avg, bias.gyroscope()[2]) - omega_meas])

    def efun(this, values, H):
        bias = values.atConstantBias(key_b)
        e = err(None, None, bias)
        if H is not None:
            H[0] = _jac_bias(err, None, None, bias, 1)
        return e
    return CustomFactor(noise, [key_b], efun)


# ---------- numerical Jacobians on the manifold (central differences) ----------
def _jac_pose(err, pose, vel, bias, m):
    H = np.zeros((m, 6))
    for j in range(6):
        d = np.zeros(6); d[j] = EPS
        H[:, j] = (err(pose.retract(d), vel, bias) - err(pose.retract(-d), vel, bias)) / (2 * EPS)
    return H


def _jac_vec(err, pose, vel, bias, m):
    H = np.zeros((m, 3))
    for j in range(3):
        d = np.zeros(3); d[j] = EPS
        H[:, j] = (err(pose, vel + d, bias) - err(pose, vel - d, bias)) / (2 * EPS)
    return H


def _jac_bias(err, pose, vel, bias, m):
    H = np.zeros((m, 6))
    ba, bg = bias.accelerometer(), bias.gyroscope()
    for j in range(6):
        d = np.zeros(6); d[j] = EPS
        bp = gtsam.imuBias.ConstantBias(ba + d[:3], bg + d[3:])
        bm = gtsam.imuBias.ConstantBias(ba - d[:3], bg - d[3:])
        H[:, j] = (err(pose, vel, bp) - err(pose, vel, bm)) / (2 * EPS)
    return H
