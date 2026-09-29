"""Core of the live forward-camera heading bridge (closed-loop Part 1, user ruling 2026-09-29).

PURE: no ROS, no MAVLink I/O. Shared by the ROS 2 node (`heading_bridge.py`) and the offline
bag test (`eval/heading_bridge_offline.py`), so the offline test exercises the code that flies.

Measurement: the FROZEN Phase 3 heading pipeline, unchanged — `fwd_measure.heading(img,
seed=k, inlier_deg=<frozen>)`, valid iff a heading exists and support >= S_MIN (frozen), the
same validity Phase 4 used. `k` is the index of the frame in the image stream (every frame
counts, processed or not), which is exactly Phase 3's per-frame RANSAC seed, so a node started
at a bag's first frame reproduces Phase 3's outputs frame for frame. Live, `k` counts from node
start: same method and parameters, different RANSAC seeds.

Every Nth frame (`every_n`): only frames with k % every_n == 0 are processed; the per-frame
method is unchanged, so each processed frame's measurement is identical to Phase 3's.

FRAME DEFINITION (recorded in METHODOLOGY). Phase 3's psi is the heading relative to the
corridor axis in the ENU/FLU sense (psi = GT ENU yaw - 90 deg, positive = nose left).
ArduPilot's yaw is NED (positive = nose right), so the measured quantity maps as
    yaw_AP = OFFSET - radians(psi)          (wrapped to [-pi, pi))
OFFSET is set ONCE, from EKF3's own yaw (MAVLink ATTITUDE.yaw) on the ground before take-off:
the circular mean of (yaw_EKF3 + radians(psi)) over the first N_OFFSET valid headings. It is
never updated and never uses ground truth. (It must be set before arming because ArduPilot's
VisualOdom arming check needs messages within 300 ms, AP_VisualOdom_Backend.cpp:33-37.)
With OFFSET chosen this way the first message equals EKF3's own yaw, so EKF3's ExtNav yaw
alignment on the first sample (alignYawAngle, AP_NavEKF3_MagFusion.cpp:370-372) is a no-op.

Message: ODOMETRY (revised 2026-09-29: the ArduPilot dev docs' preferred message; was
VISION_POSITION_ESTIMATE). GCS_Common.cpp:4055-4087: frame_id must be MAV_FRAME_LOCAL_FRD and
child_frame_id MAV_FRAME_BODY_FRD; heading goes in q (roll = pitch = 0, yaw = yaw_AP); the
velocity it always forwards is NaN here, so writeExtNavVelData returns early
(AP_NavEKF3_Measurements.cpp:1130) and nothing but yaw can reach EKF3 (VELXY is flow anyway).
QUALITY carries the per-frame confidence and VISO_QUAL_MIN is the gate
(AP_VisualOdom_MAV.cpp:47-51): quality = floor(50 * support / S_MIN) capped at 100, and -1 when
there is no vanishing point; VISO_QUAL_MIN = 50 therefore accepts exactly the frozen Phase 3
validity (support >= S_MIN). Every processed frame is sent once the offset is locked.
  time_usec = frame capture time (image header stamp, sim clock, us). ArduPilot's jitter
           correction maps it to its own clock (GCS_Common.cpp:4106,7373-7387), assuming the
           fastest message had zero lag; VISO_DELAY_MS must therefore be the MINIMUM
           capture->receipt latency.
  x,y,z  = 0, 0, 0 PLACEHOLDER (a NaN position drops the whole sample,
           AP_NavEKF3_Measurements.cpp:1076-1078). Stated error 100 m (the clamp maximum,
           AP_VisualOdom_MAV.cpp:42). Not fused: EK3_SRC1_POSXY stays None, and ResetPosition
           uses ExtNav only in AID_ABSOLUTE (AP_NavEKF3_PosVelFusion.cpp:124-162), which flow
           aiding never reaches.
  roll, pitch = 0 (only yaw is extracted, 321 order); yaw = yaw_AP.
  pose_covariance: position diagonal 100^2/3 each (posErr = 100 m); roll/pitch 0; yaw
           sigma_psi^2. ArduPilot COMBINES elements 15, 18, 20 as angErr = sqrt(c15 + c18 + c20)
           (GCS_Common.cpp:4077), so roll/pitch are set to 0 and angErr = sigma_psi exactly.
           It is then clamped to [VISO_YAW_M_NSE, 1.5] rad (AP_VisualOdom_MAV.cpp:43), floored
           at 5 deg by EKF3 (AP_NavEKF3_Measurements.cpp:1118), and fused with
           R_YAW = max(err, 0.05)^2 (AP_NavEKF3_MagFusion.cpp:879). Effective sigma: 11.46 deg
           at the default VISO_YAW_M_NSE 0.2 rad; 5.0 deg if VISO_YAW_M_NSE <= 0.0873 rad.
"""
import math, os, sys, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fwd_measure as F

POS_PLACEHOLDER = (0.0, 0.0, 0.0)
POS_ERR_M = 100.0
N_OFFSET = 30


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def covariance(sigma_psi_rad):
    """21-element upper-triangular 6x6 pose covariance (x y z roll pitch yaw)."""
    c = [0.0] * 21
    for i in (0, 6, 11):            # x, y, z variances
        c[i] = POS_ERR_M ** 2 / 3.0
    c[15], c[18], c[20] = 0.0, 0.0, sigma_psi_rad ** 2   # roll, pitch, yaw variances
    return c


class HeadingCore:
    def __init__(self, inlier_deg, s_min, sigma_psi_deg, every_n=1):
        self.inlier_deg, self.s_min, self.every_n = float(inlier_deg), float(s_min), int(every_n)
        self.sigma = math.radians(sigma_psi_deg)
        self.cov = covariance(self.sigma)
        self.offset = None
        self._off_s, self._off_c = [], []

    def selected(self, k):
        return k % self.every_n == 0

    def measure(self, k, img):
        """Frozen Phase 3 heading on frame k. Returns (psi_deg or None, support, valid, proc_s)."""
        t0 = time.perf_counter()
        h = F.heading(img, seed=k, inlier_deg=self.inlier_deg)
        dt = time.perf_counter() - t0
        psi, sup = h["psi_deg"], (h["support"] if h["psi_deg"] is not None else 0.0)
        valid = psi is not None and sup >= self.s_min
        return psi, sup, valid, dt

    def feed_offset(self, yaw_ekf_rad, psi_deg):
        """Offset estimation (ground, pre-arm): returns True once locked."""
        if self.offset is not None:
            return True
        a = yaw_ekf_rad + math.radians(psi_deg)
        self._off_s.append(math.sin(a)); self._off_c.append(math.cos(a))
        if len(self._off_s) >= N_OFFSET:
            self.offset = math.atan2(sum(self._off_s), sum(self._off_c))
            return True
        return False

    def quality(self, psi_deg, support):
        """ODOMETRY quality: -1 without a vanishing point, else floor(50*support/S_MIN) <= 100
        (VISO_QUAL_MIN = 50 <=> support >= S_MIN, the frozen validity)."""
        if psi_deg is None:
            return -1
        return int(min(100, math.floor(50.0 * support / self.s_min)))

    def q_yaw(self, yaw):
        """[w, x, y, z] for roll = pitch = 0."""
        return [math.cos(yaw / 2), 0.0, 0.0, math.sin(yaw / 2)]

    def yaw_ap(self, psi_deg):
        return wrap(self.offset - math.radians(psi_deg))
