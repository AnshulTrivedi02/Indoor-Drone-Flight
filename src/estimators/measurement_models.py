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
    # NOTE (2026-08-01): a proposed sign flip of flow_x_rot (-> +rollspeed) was tested and
    # REVERTED — it failed its confirmation (UKF ATE -a 11.7 -> 16.3, yaw drift 12.4 -> 19.3,
    # gyro-z overshoot 245% -> 336%). The GT-residual rollspeed coupling did drop, but the
    # estimator got worse and the UKF innovation flipped (+0.71 -> -0.69) rather than
    # zeroing. The EKF3-vs-UKF innovation comparison that motivated it was flawed (EKF3's
    # FIX is post-derotation, the UKF's nu is full-model — not comparable). See METHODOLOGY.
    flow_x_rot = -omega_body[0]                        # -rollspeed (unchanged; see note)
    flow_y_rot = +omega_body[1]                        # +pitchspeed
    return np.array([flow_x_trans + flow_x_rot, flow_y_trans + flow_y_rot])


def h_flow(x, omega_body):
    """UKF entry point: predicted RAW angular flow from the 15-state vector.
    Thin wrapper over the shared h_flow_pose so there is ONE geometric model."""
    return h_flow_pose(R_world_body(x[6], x[7], x[8]), x[V_SLICE], x[2], omega_body)


class FlowFrameGyroAverager:
    """Interval-averaged gyro for flow derotation — the omega passed to h_flow.

    The raw optical flow's rotational content is the body rate INTEGRATED over the
    camera frame then divided by dt (flow_tracker.py:223-227, flow rate = mean_dx/dt,
    dt = current_frame - prev_frame), i.e. the gyro AVERAGED over (prev_frame,
    current_frame]. Feeding h_flow the instantaneous rate leaves a roll-rate-coupled
    residual EKF3 does not carry; EKF3 cancels it with the same interval-average
    (OF bodyRate = gyro_sum/gyro_sum_count, AP_OpticalFlow_MAV.cpp:38-42,76; fused as
    flowRadXYcomp, AP_NavEKF3_Measurements.cpp:206,227). This averager reproduces that
    on the prediction side. The flow message stamp IS the capture time
    (flow_tracker.py:296), so the window has no offset. Applied 2026-08-01 — the
    geometrically-correct, EKF3-faithful derotation; see METHODOLOGY FINDING 4 (it
    also raises gate acceptance and, under unobservable yaw, the flow->yaw leak).

    SHARED by the UKF and FGO so both derotate with the identical rate (fairness).
    Feed it the co-sampled /imu/data_raw gyro (333 Hz); call average() at each flow.
    """
    def __init__(self, t_init):
        self._buf = []            # (t, gx, gy, gz) since the last flow frame
        self._t_prev = t_init

    def push(self, t, gyro):
        self._buf.append((t, gyro[0], gyro[1], gyro[2]))

    def average(self, t_flow, fallback):
        """Mean gyro over (prev_flow, t_flow]; `fallback` (latest omega) if empty."""
        win = [g for g in self._buf if g[0] > self._t_prev]
        if win:
            om = np.array([np.mean([g[1] for g in win]),
                           np.mean([g[2] for g in win]),
                           np.mean([g[3] for g in win])])
        else:
            om = np.asarray(fallback, float)
        self._t_prev = t_flow
        self._buf = [g for g in self._buf if g[0] > t_flow]     # drop consumed window
        return om


def sitl_gyro_drift(t_sec):
    """Instantaneous TRUE gyro-z bias magnitude (deg/min) from SITL's drift model
    (AP_InertialSensor_SITL.cpp:390-402): a triangle wave, period = 2*SIM_DRIFT_TIME
    = 10 min, ramping 0 -> ~15 -> 0 at slope radians(SIM_DRIFT_SPEED=0.05)/min =
    3.00 deg/min per minute. NOT the constant 9.8 the old code assumed — that was a
    cruise-window MEAN of this ramp. Validated against recorded /imu/data_raw gyro-z
    (matches within ~0.2 deg/min across the flight). t_sec = bag/sim stamp (seconds
    since boot, phase-aligned to the drift cycle). Vectorised; returns |bias| deg/min
    (the sign is +FRD / -FLU; use magnitudes to compare across estimator conventions)."""
    m = np.fmod(np.asarray(t_sec, float)/60.0, 10.0)
    d = np.where(m < 5.0, m, 10.0 - m) * np.radians(0.05)   # rad/s
    return np.degrees(d)*60.0                               # deg/min, magnitude


# ---------------------------------------------------------------------------
# Forward camera (Phase 4, METHODOLOGY "Phase 4 — offline forward-camera fusion").
# SHARED by the UKF and the FGO: the same models, noise, gate and inputs.
# ---------------------------------------------------------------------------
import json as _json
import os as _os

FWD_CHI2_GATE = 9.0      # nu^2 / S <= 9 (3 sigma; EKF3 flow gate 300 -> (0.01*300)^2)
# Noise from the static-sweep residuals (pre-registered): sigma_psi = robust sigma of
# (psi - commanded offset) over all valid sweep frames per dataset; sigma_omega = the
# flight-calibration value scaled by the same sweep/flight inflation (the sweep has no
# yaw-rate measurement). Yaw rate is not used on plain walls (failed Phase 3).
FWD_SIGMA = {"fwdc": {"psi": np.radians(0.148), "omega": np.radians(0.162)},
             "fwdplainc": {"psi": np.radians(0.126), "omega": None}}
FWD_ARMS = ("baseline", "heading", "heading_yawrate")


def wrap_angle(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def h_heading(yaw):
    """Heading relative to the corridor axis. The navigation frame's yaw reference is
    the corridor axis (both estimators initialise yaw = 0 facing along it; the
    ExternalNav convention, where the external heading source defines the reference)."""
    return yaw


def h_yawrate(gyro_z_avg, bg_z_rate):
    """Body yaw rate seen by the forward camera over the frame interval: the
    interval-averaged co-sampled gyro-z minus the gyro-z bias (rad/s, FLU). Roll/pitch
    coupling is neglected (cruise tilt ~0.02 deg)."""
    return gyro_z_avg - bg_z_rate


def fwd_dataset(trial):
    tok = trial.split("_")
    return "fwdplainc" if "fwdplainc" in tok else ("fwdc" if "fwdc" in tok else None)


def forward_events(trial, arm):
    """Forward-camera measurement events for an arm, from the frozen Phase 3 outputs.

    Returns [(t, "fwd", (psi_rad | None, omega_rad | None))]. Validity is
    measurement-intrinsic only (Phase 3 frozen S_MIN / N_MIN): no ground truth,
    position or world knowledge. "baseline" returns []."""
    if arm in (None, "baseline"):
        return []
    ds = fwd_dataset(trial)
    if ds is None:
        raise ValueError(f"{trial}: not a forward-camera dataset bag")
    use_w = arm == "heading_yawrate"
    if use_w and FWD_SIGMA[ds]["omega"] is None:
        raise ValueError(f"{trial}: yaw-rate arm not defined for {ds} (failed Phase 3 validation)")
    here = _os.path.dirname(_os.path.abspath(__file__))
    cal = _json.load(open(_os.path.join(here, "..", "..", "eval", "results", "fwd_calibration.json")))["frozen"]
    d = np.load(_os.path.expanduser(f"~/thesis_data/trials/{trial}/fwd_meas/meas_frozen.npz"))
    assert float(d["inlier_grid"][0]) == cal["inlier_deg"] and int(d["box_grid"][0]) == cal["box_half_px"]
    t, psi, sup = d["t"], d["psi"][:, 0], d["support"][:, 0]
    om, ntr = d["omega"][:, 0, 0], d["n_trk"][:, 0, 0]
    out = []
    for k in range(len(t)):
        p = float(np.radians(psi[k])) if (np.isfinite(psi[k]) and sup[k] >= cal["s_min"]) else None
        w = float(np.radians(om[k])) if (use_w and np.isfinite(om[k]) and ntr[k] >= cal["n_min"]) else None
        if p is not None or w is not None:
            out.append((float(t[k]), "fwd", (p, w)))
    return out
