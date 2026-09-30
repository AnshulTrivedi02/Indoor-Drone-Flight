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
    CORRECTED 2026-09-29 (METHODOLOGY "FINDING - lateral optical-flow sign"), from data
    with real lateral excitation (cl_ekf3_tex) and the roll tone at the forward axis's lag:
        flow_x = +v_left/h + omega_x      flow_y = +v_fwd/h - omega_y      (FLU rates)
    Previously flow_x = -v_left/h - omega_x (whole lateral row negated) and
    flow_y_rot = +omega_y (an FRD->FLU slip: flow_tracker's +pitchspeed is FRD).
    Forward translation (Stage A) was always right. Rotation MAGNITUDE (~1.4-1.5 x the
    filtered gyro on X) is an open item, not modelled.
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
# translational flow signs (Stage A: forward -> +flow_y). SIGN_X was -1.0 until
# 2026-09-29 (never tested laterally); +1.0 from the closed-loop lateral excursion.
SIGN_X = +1.0
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
    # NOTE (2026-09-29): the 2026-08-01 test above flipped ONLY the rotation term, leaving
    # the translation still negated, so the lateral row stayed inconsistent - which is
    # why it made the UKF worse. The whole row was wrong. Both terms are now corrected
    # together, and flow_y_rot's FLU sign is fixed (was +omega_y, i.e. -pitchspeed FRD).
    flow_x_rot, flow_y_rot = h_flow_rot(omega_body)
    return np.array([flow_x_trans + flow_x_rot, flow_y_trans + flow_y_rot])


def h_flow_rot(omega_body):
    """The rotational part of h_flow_pose (FLU body rates -> raw flow): +roll rate (was -omega_x);
    +pitchspeed FRD = -omega_y FLU (was +omega_y). Also the D15 zero-translation measurement."""
    return np.array([+omega_body[0], -omega_body[1]])


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


# ---------------------------------------------------------------------------------------------------------
# GROUND-PROXIMITY FLOW RULE (ruling D15, 2026-09-30) - EKF3's own rule, used unchanged, shared by the UKF
# and the FGO so every estimator handles flow near the floor identically (METHODOLOGY "Ruling D15").
#   take-off detected (AP_NavEKF3_VehicleStatus.cpp:466-481): false while disarmed; once armed and > 1 s after
#     arming, latches true at |gyro - bias| > 0.1 rad/s or range > range_at_arming + 0.1 m
#   replacement (AP_NavEKF3_OptFlowFusion.cpp:45-51): while NOT take-off detected AND range*cos(tilt) < 0.5 m,
#     the flow is replaced by a ZERO-TRANSLATION measurement: its predicted rotational part only
#     (h_flow_pose's rotation terms: flow_x = +w_x, flow_y = -w_y, FLU), i.e. EKF3's flowRadXYcomp = 0.
# ---------------------------------------------------------------------------------------------------------
GP_HEIGHT_M, GP_ARM_GUARD_S, GP_GYRO_RADPS, GP_RANGE_RISE_M = 0.5, 1.0, 0.1, 0.1


class GroundProximityFlow:
    def __init__(self, t_arm):
        """t_arm: arming time on the bag clock (imu_gaps.json arm_header_s); None -> never armed (no take-off)."""
        self.t_arm = t_arm
        self.takeoff = False
        self.rng_at_arm = None      # EKF3's rngAtStartOfFlight: the last range while on ground
        self.last_rng = None
        self.n_replaced = 0
        self.t_takeoff = None       # when take-off was detected (audit only)

    def armed(self, t):
        return self.t_arm is not None and t >= self.t_arm

    def on_range(self, t, rng):
        if not (0.05 <= rng <= 40.0):
            return
        self.last_rng = rng
        if not self.armed(t):
            self.rng_at_arm = rng
        elif (not self.takeoff and t - self.t_arm > GP_ARM_GUARD_S and self.rng_at_arm is not None
              and rng > self.rng_at_arm + GP_RANGE_RISE_M):
            self.takeoff = True; self.t_takeoff = t

    def on_gyro(self, t, gyro_rate, bias_rate):
        if not self.armed(t):
            self.takeoff = False
            return
        if not self.takeoff and t - self.t_arm > GP_ARM_GUARD_S:
            if np.linalg.norm(np.asarray(gyro_rate, float) - np.asarray(bias_rate, float)) > GP_GYRO_RADPS:
                self.takeoff = True; self.t_takeoff = t

    def replace(self, flow_xy, omega_flu, roll, pitch):
        """Return the flow to fuse: the measured flow, or the zero-translation measurement before take-off
        below 0.5 m (range * cos(tilt), as EKF3's rangefinder-based terrain height)."""
        if self.takeoff or self.last_rng is None:
            return flow_xy
        if self.last_rng * np.cos(roll) * np.cos(pitch) >= GP_HEIGHT_M:
            return flow_xy
        self.n_replaced += 1
        return h_flow_rot(omega_flu)          # EKF3's flowRadXYcomp = 0 (zero relVelSensor, lever arm included)


# ---------------------------------------------------------------------------------------------------------
# OFFLINE F-TEST VARIANTS (METHODOLOGY "PRE-REGISTRATION — offline tests F1, F2, F3"). Environment switches,
# ALL OFF by default (every pipeline result is unchanged); a variant writes to <est>_<arm>_<F_TAG>/.
#   F_TAG              output-directory tag (required with any F_* switch)
#   F_YAW0_DEG         F3: initial yaw offset (deg) and initial yaw sigma = the same value
#   F_HDG_FROM_CRUISE  F3: forward-camera headings withheld before the pinned cruise start
#   F_MASK "on/off"    F2: from cruise start, headings on `on` s, off `off` s, repeating (first interval on)
#   F_ROBUST "huber:k" | "cauchy:k"   F1 (FGO only): robust heading noise model, chi-square gate removed
#   F_YAW0_SIGMA_DEG   F3b: initial yaw sigma (deg), separate from the offset (default: sigma = the offset)
#   F_NO_YAWCAP 1      F3b: disable the zero-innovation yaw-bounding mechanisms (FGO yaw-cap prior, UKF pseudo-yaw)
#   F_BATCH 1          F2 (FGO only): also record every factor and solve ONE batch LM over the whole flight at the
#                      end (initialised from the live estimates), written to fgo_batch_traj.tum
# ---------------------------------------------------------------------------------------------------------
def f_variant():
    import os as _o
    v = {k: _o.environ.get(k) for k in ("F_TAG", "F_YAW0_DEG", "F_HDG_FROM_CRUISE", "F_MASK", "F_ROBUST", "F_BATCH",
                                         "F_YAW0_SIGMA_DEG", "F_NO_YAWCAP")}
    if any(v[k] for k in v if k != "F_TAG"):
        assert v["F_TAG"], "F_TAG is required with any F_* variant switch"
    return v


def f_filter_forward(ev, gt_t, gt_x, gt_y, v):
    """Apply F_HDG_FROM_CRUISE / F_MASK to the 'fwd' events of a time-sorted event list (bag clock)."""
    if not (v.get("F_HDG_FROM_CRUISE") or v.get("F_MASK")):
        return ev
    import sys as _s, os as _o
    _s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "..", "eval"))
    from cruise_window import cruise_bounds
    c0, c1 = cruise_bounds(np.asarray(gt_t), np.asarray(gt_x), np.asarray(gt_y))
    on = off = None
    if v.get("F_MASK"):
        on, off = (float(x) for x in v["F_MASK"].split("/"))
    out = []
    for e in ev:
        if e[1] != "fwd":
            out.append(e); continue
        t = e[0]
        if v.get("F_HDG_FROM_CRUISE") and t < c0:
            continue
        if on is not None and t >= c0 and ((t - c0) % (on + off)) >= on:
            continue
        out.append(e)
    return out
