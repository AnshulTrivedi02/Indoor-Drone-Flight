"""Shared measurement models for the UKF (and later the FGO).

PURE functions — plain numpy arrays in, numpy arrays out. No ROS, no bag, no
sim-time. State is a 15-vector in a fixed layout (see STATE_* below); world
frame ENU, body frame FLU, attitude as ZYX Euler.

Frames/signs pinned from source, not guessed:
  - h_range: EKF3 flat-terrain rangefinder height, base_link referenced
    (h = p_U - RANGE_LEVER, RANGE_LEVER=0.12 m), CLAUDE.md UKF Design + FGO §3.
  - h_cam = p_U - 0.25 (camera below base_link); == lidar_range - 0.13, FGO §0.
  - h_flow: RAW angular flow (translational + rotational) in the camera-optical
    axes, matching what flow_tracker.py publishes and estimators consume
    (flow_tracker.py:275-276: flow_x_rot=-rollspeed, flow_y_rot=+pitchspeed).
    Translational sign from validated Stage A: forward v_body.x -> +flow_y.
    SIGN_X (lateral -> flow_x) is the empirical pin-point (design note).
"""
import numpy as np

# --- 15-state layout ---
P_SLICE = slice(0, 3)      # p_E, p_N, p_U   (ENU, m)
V_SLICE = slice(3, 6)      # v_E, v_N, v_U   (ENU, m/s)
A_SLICE = slice(6, 9)      # roll, pitch, yaw (rad, ZYX; world<-body FLU)
BG_SLICE = slice(9, 12)    # gyro bias  (rad, delta-angle per predict step)
BA_SLICE = slice(12, 15)   # accel bias (m/s, delta-velocity per predict step)
N = 15

# --- geometry (metres) ---
RANGE_LEVER = 0.12                                   # LiDAR below base_link
CAM_OFFSET = 0.25                                    # camera below base_link
FLOW_LEVER_ARM_BODY = np.array([0.0, 0.0, -CAM_OFFSET])  # FLU
H_MIN = 0.10
# translational flow signs (Stage A: forward -> +flow_y; SIGN_X is the pin)
SIGN_X = -1.0
SIGN_Y = +1.0


def R_world_body(roll, pitch, yaw):
    """ZYX (yaw*pitch*roll) rotation, ENU world <- FLU body."""
    cr, sr = np.cos(roll), np.sin(roll)
    cp, sp = np.cos(pitch), np.sin(pitch)
    cy, sy = np.cos(yaw), np.sin(yaw)
    return np.array([
        [cy*cp, cy*sp*sr - sy*cr, cy*sp*cr + sy*sr],
        [sy*cp, sy*sp*sr + cy*cr, sy*sp*cr - cy*sr],
        [-sp,   cp*sr,            cp*cr]])


def h_range(x):
    """Predicted LiDAR range = base_link height - lever arm (flat floor)."""
    return np.array([x[2] - RANGE_LEVER])


def h_flow_pose(R_wb, v_world, p_U, omega_body):
    """Predicted RAW angular flow (rad/s), 2-vector (flow_x, flow_y) — the single
    shared geometric model, in the pose form the FGO factor needs.

    R_wb: 3x3 world<-body (FLU) rotation.  v_world: ENU velocity (3,).
    p_U: base_link height (m).  omega_body: FLU body rates the flow derotates
    against. The caller decides bias handling: the UKF passes the RAW measured
    rate (its gyro bias is applied in predict); the FGO passes the bias-CORRECTED
    rate omega_meas - B(k).gyroscope() (FGO §2, difference #5/#8) so flow can
    inform gyro bias through this term. The geometry below is identical either way.
    """
    v_body = R_wb.T @ v_world                          # world velocity into FLU
    v_s = v_body + np.cross(omega_body, FLOW_LEVER_ARM_BODY)
    h_cam = max(p_U - CAM_OFFSET, H_MIN)
    flow_x_trans = SIGN_X * (v_s[1] / h_cam)          # lateral  -> flow_x
    flow_y_trans = SIGN_Y * (v_s[0] / h_cam)          # forward  -> flow_y (Stage A)
    flow_x_rot = -omega_body[0]                        # -rollspeed
    flow_y_rot = +omega_body[1]                        # +pitchspeed
    return np.array([flow_x_trans + flow_x_rot, flow_y_trans + flow_y_rot])


def h_flow(x, omega_body):
    """UKF entry point: predicted RAW angular flow from the 15-state vector.
    Thin wrapper over the shared h_flow_pose so there is ONE geometric model."""
    return h_flow_pose(R_world_body(x[6], x[7], x[8]), x[V_SLICE], x[2], omega_body)
