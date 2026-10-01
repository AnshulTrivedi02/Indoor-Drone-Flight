#!/usr/bin/env python3
"""ROS 2 node: the online FGO (ruling D7). A THIN shell around fgo_node_core.FgoNodeCore, the class
the offline equivalence tests drive (eval/fgo_node_equiv.py). Subscribes to the same topics
fgo_replay.py reads; every message is pushed into the core in ARRIVAL order with its header stamp.
Publishes, at each keyframe, /fgo/pose (geometry_msgs/PoseStamped, ENU/FLU, stamped at the keyframe
time) and /fgo/valid (std_msgs/Bool; false after a post-take-off IMU gap, the IMU-gap rule's causal
form). Not used in any flight until FGO steps 2-3 are done and ruled on (METHODOLOGY, D7).
Run: python3 fgo_node.py --ros-args -p use_sim_time:=true [-p horizon_s:=0.10]   (~/venv-fgo + ROS)"""
import glob, math, multiprocessing as mp, os, sys, threading, time
from collections import deque
os.environ.setdefault("MAVLINK20", "1")     # ODOMETRY quality/estimator_type are v2 extensions (D19 backend)
import numpy as np
import rclpy
import rclpy.executors
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from geometry_msgs.msg import PoseStamped, Vector3Stamped
from sensor_msgs.msg import Imu, Range, TimeReference
from std_msgs.msg import Bool
from optical_flow_interfaces.msg import OpticalFlow
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fgo_node_core import FgoNodeCore


CLOCK_SETTLE_S = 10.0     # D25: no state is sent until the SITL clock map's 10 s window is full
CLOCK_OUTLIER_S = 0.020   # D25: offsets further than this from the window median are not used (the true offset
#                           drifts ~0.2 ms/s, SITL's clock running ~0.02% slow; delivery jitter is a few ms)


def _st(h):
    return h.stamp.sec + h.stamp.nanosec * 1e-9


def _quat(r, p, y):
    cr, sr, cp, sp, cy, sy = math.cos(r / 2), math.sin(r / 2), math.cos(p / 2), math.sin(p / 2), math.cos(y / 2), math.sin(y / 2)
    return (sr * cp * cy - cr * sp * sy, cr * sp * cy + sr * cp * sy, cr * cp * sy - sr * sp * cy, cr * cp * cy + sr * sp * sy)


def _core_proc(inq, outq, kw, stats_path):
    """The FGO core process: pushes every message in arrival order; returns each new keyframe."""
    import signal
    signal.signal(signal.SIGINT, signal.SIG_IGN)   # run_trial stops the node's process group with SIGINT: the core
    #                                                 must not die mid-step; it drains on the None sentinel and saves
    core = FgoNodeCore(**kw); n_out = 0
    while True:
        item = inq.get()
        if item is None:
            break
        t, kind, payload, tw_epoch = item
        core.push(t, kind, payload, t_wall=time.perf_counter() - (time.time() - tw_epoch))
        while n_out < len(core.traj):
            outq.put((core.traj[n_out], core.valid, core.states[n_out])); n_out += 1
    core.flush()
    if stats_path:
        np.savez(stats_path, step_ns=np.array(core.step_ns, np.int64), lag=np.array(core.lag).reshape(-1, 2),
                 traj=np.array(core.traj), valid=core.valid, reinits=core.reinits,
                 valid_log=np.array(core.valid_log, float).reshape(-1, 2),
                 gaps_seen=np.array(core.gaps_seen, float).reshape(-1, 3),
                 n_pushed=np.array([(k, v) for k, v in core.n_pushed.items()], dtype=object),
                 n_imu_integrated=(core.fgo.n_imu if core.fgo is not None else 0))


class FgoNode(Node):
    def __init__(self):
        super().__init__("fgo_node")
        self.declare_parameter("horizon_s", 0.10)
        self.declare_parameter("window_s", 0.25)
        self.declare_parameter("lm_iters", 2)
        self.declare_parameter("stats_path", "")          # on shutdown: per-keyframe step time and queue lag (npz)
        # D19 backend (route a): send each keyframe state to ArduPilot (AHRS_EKF_TYPE 13) over its own MAVLink
        # route, SITL SERIAL3 -> udpclient 127.0.0.1:14558. Empty = not sent (shadow/offline use).
        self.declare_parameter("mavlink_out", "")
        # D19 FGO heading input (ruling D17's principle: the same heading at the same trust as EKF3/UKF): the
        # heading bridge's sent ODOMETRY, re-published on /forward_camera/heading_sent, gated exactly as
        # AP_VisualOdom + EKF3: quality >= VISO_QUAL_MIN 50; angErr clamped to [VISO_YAW_M_NSE 0.05, 1.5] rad;
        # sigma = max(angErr, 5 deg); >= 20 ms apart (extNavIntervalMin_ms); chi-square gate 9 (3 sigma).
        # Fused at its capture stamp (the FGO's factor-graph design; EKF3/UKF use TS - VISO_DELAY_MS).
        self.declare_parameter("heading", False)
        self._toff = deque()                                 # (t_header, t_header - t_sitl) over the last 10 s
        self._tref_t0 = None; self._toff_early = []          # D25: settle reference and start-up diagnostics
        self._n_unsettled = self._n_outl_max = self._n_maps_with_outliers = 0
        self._mav = None
        self._n_pub = 0
        q = QoSProfile(reliability=ReliabilityPolicy.RELIABLE, history=HistoryPolicy.KEEP_LAST, depth=200)
        self.create_subscription(Imu, "/imu/data_raw", self._imu, q)
        self.create_subscription(TimeReference, "/imu/time_ref", self._tref, q)
        self.create_subscription(OpticalFlow, "/optical_flow/measurement", self._flow, q)
        self.create_subscription(Range, "/downward_lidar/range", self._rng, q)
        self.create_subscription(Vector3Stamped, "/attitude/angular_rates", self._att, q)
        self.pub = self.create_publisher(PoseStamped, "/fgo/pose", 10)
        self._hdg_last = None
        if self.get_parameter("heading").value:
            self.create_subscription(Vector3Stamped, "/forward_camera/heading_sent", self._hdg, q)
        self.pub_valid = self.create_publisher(Bool, "/fgo/valid", 10)
        # The FGO core runs in a SEPARATE PROCESS; callbacks only forward messages over a pipe.
        # History (fgo_shadow_sitl_tex2/3, 2026-09-30): running the step inside the callbacks blocked
        # the executor (~28 ms per keyframe under load) and lost ~1.4% of IMU/time_ref messages (false
        # IMU gaps, a false invalid flag); a worker THREAD fixed the loss but the GIL, shared with 333 Hz
        # Python callbacks, slowed the step to ~48 ms and the node fell behind (lag grew ~0.43 s/s).
        ctx = mp.get_context("spawn")
        self._to_core, self._from_core = ctx.Queue(), ctx.Queue()
        self._proc = ctx.Process(target=_core_proc, args=(self._to_core, self._from_core,
                                 dict(window=float(self.get_parameter("window_s").value), lm_iters=int(self.get_parameter("lm_iters").value),
                                      fwd_sigma=({"psi": math.radians(5.0), "omega": None} if self.get_parameter("heading").value else None),
                                      fwd_gate=9.0,
                                      horizon_s=float(self.get_parameter("horizon_s").value), dejitter="causal", gap="causal"),
                                 self.get_parameter("stats_path").value), daemon=True)
        self._proc.start()
        self._stop = False
        out = self.get_parameter("mavlink_out").value
        if out:
            from pymavlink import mavutil
            self._mav = mavutil.mavlink_connection(out, source_component=197)
        self._pub_thread = threading.Thread(target=self._publisher, daemon=True)
        self._pub_thread.start()

    def _sitl_us(self, t):
        """Bag/sim header time -> SITL (DAL) clock, us: the lower envelope of header - /imu/time_ref over the
        last 10 s (the least-delayed sample), as eval/input_timing's clock map but causal.
        D25 (ruled 2026-10-01): NO output until the map has settled (the window holds CLOCK_SETTLE_S of samples),
        and the envelope is taken over INLIERS only (|offset - window median| <= CLOCK_OUTLIER_S). A single too-low
        start-up offset used to be held by the plain minimum for the whole 10 s window and stamped states up to
        ~42 ms in the future (fgo_groundtest_half_b: ArduPilot's uint32 age wrapped -> invalid -> pre-arm refused).
        With no outliers the value is identical to the plain minimum. The deque is snapshotted with list() (one C
        call under the GIL) because the executor thread appends while this publisher thread reads."""
        snap = list(self._toff)
        if not snap or self._tref_t0 is None or snap[-1][0] - self._tref_t0 < CLOCK_SETTLE_S:
            self._n_unsettled += 1
            return None
        o = np.fromiter((x for _, x in snap), float, len(snap))
        inl = np.abs(o - np.median(o)) <= CLOCK_OUTLIER_S
        n_out = int(len(o) - inl.sum())
        self._n_outl_max = max(self._n_outl_max, n_out)
        self._n_maps_with_outliers += n_out > 0
        return int(round((t - o[inl].min()) * 1e6))

    def _send_state(self, st, valid):
        t_k, p, v, R, bg, ba = st
        t_us = self._sitl_us(t_k)
        if self._mav is None or t_us is None:
            return
        # pymavlink "udp:" listens; it can only reply to an address it has received from (SITL SERIAL3's
        # udpclient heartbeats). Drain what has arrived so the destination is known (found: the first smoke
        # test sent nothing because the node never read).
        while self._mav.recv_msg() is not None:
            pass
        if getattr(self._mav, "udp_server", False) and not self._mav.clients:     # pymavlink 2.4.49: senders go to .clients
            self._n_unsent = getattr(self, "_n_unsent", 0) + 1
            return
        # The FGO's navigation frame is the CORRIDOR frame (measurement_models.h_heading: yaw 0 along the corridor
        # at spawn): x = forward along the corridor = North, y = left = West, z = up. -> NED: (x, -y, -z).
        # (Found in the second smoke test: an ENU mapping put yaw 90 deg off and swapped N/E.)
        C = np.array([[1.0, 0, 0], [0, -1, 0], [0, 0, -1]])    # corridor (x fwd/N, y W, z U) -> NED
        Fb = np.diag([1.0, -1, -1])                           # FLU <-> FRD
        pn, vn, Rn = C @ p, C @ v, C @ R @ Fb
        # rotation matrix -> quaternion (w, x, y, z)
        tr = np.trace(Rn)
        if tr > 0:
            S = math.sqrt(tr + 1.0) * 2; qw = 0.25 * S; qx = (Rn[2, 1] - Rn[1, 2]) / S; qy = (Rn[0, 2] - Rn[2, 0]) / S; qz = (Rn[1, 0] - Rn[0, 1]) / S
        elif Rn[0, 0] > Rn[1, 1] and Rn[0, 0] > Rn[2, 2]:
            S = math.sqrt(1.0 + Rn[0, 0] - Rn[1, 1] - Rn[2, 2]) * 2; qw = (Rn[2, 1] - Rn[1, 2]) / S; qx = 0.25 * S; qy = (Rn[0, 1] + Rn[1, 0]) / S; qz = (Rn[0, 2] + Rn[2, 0]) / S
        elif Rn[1, 1] > Rn[2, 2]:
            S = math.sqrt(1.0 + Rn[1, 1] - Rn[0, 0] - Rn[2, 2]) * 2; qw = (Rn[0, 2] - Rn[2, 0]) / S; qx = (Rn[0, 1] + Rn[1, 0]) / S; qy = 0.25 * S; qz = (Rn[1, 2] + Rn[2, 1]) / S
        else:
            S = math.sqrt(1.0 + Rn[2, 2] - Rn[0, 0] - Rn[1, 1]) * 2; qw = (Rn[1, 0] - Rn[0, 1]) / S; qx = (Rn[0, 2] + Rn[2, 0]) / S; qy = (Rn[1, 2] + Rn[2, 1]) / S; qz = 0.25 * S
        bgf, baf = Fb @ bg, Fb @ ba
        cov = [float("nan")] * 21; cov[0], cov[1], cov[2] = float(baf[0]), float(baf[1]), float(baf[2])
        from pymavlink import mavutil
        self._mav.mav.odometry_send(t_us, mavutil.mavlink.MAV_FRAME_LOCAL_NED, mavutil.mavlink.MAV_FRAME_BODY_FRD,
                                    float(pn[0]), float(pn[1]), float(pn[2]), [float(qw), float(qx), float(qy), float(qz)],
                                    float(vn[0]), float(vn[1]), float(vn[2]), float(bgf[0]), float(bgf[1]), float(bgf[2]),
                                    cov, [float("nan")] * 21, 0, mavutil.mavlink.MAV_ESTIMATOR_TYPE_NAIVE, 100 if valid else 0)

    def _push(self, t, kind, payload):
        self._to_core.put((t, kind, payload, time.time()))     # wall arrival time (lag includes queueing)

    def _publisher(self):
        while not self._stop:
            try:
                row, valid, st = self._from_core.get(timeout=0.2)
            except Exception:
                continue
            t_k, x, y, z, r, p, yw, _ = row
            m = PoseStamped(); m.header.frame_id = "map"
            m.header.stamp.sec = int(t_k); m.header.stamp.nanosec = int(round((t_k - int(t_k)) * 1e9)) % 1000000000
            m.pose.position.x, m.pose.position.y, m.pose.position.z = float(x), float(y), float(z)
            qx, qy, qz, qw = _quat(r, p, yw)
            m.pose.orientation.x, m.pose.orientation.y, m.pose.orientation.z, m.pose.orientation.w = qx, qy, qz, qw
            self.pub.publish(m)
            self.pub_valid.publish(Bool(data=bool(valid)))
            self._send_state(st, valid)

    def stop_worker(self):
        sp = self.get_parameter("stats_path").value
        if sp:                                  # D25 clock-map diagnostics, next to the core's stats
            np.savez(sp.replace(".npz", "") + "_clockmap.npz", early=np.array(self._toff_early).reshape(-1, 2),
                     tref_t0=np.nan if self._tref_t0 is None else self._tref_t0, n_unsettled=self._n_unsettled,
                     n_outliers_max=self._n_outl_max, n_maps_with_outliers=self._n_maps_with_outliers,
                     settle_s=CLOCK_SETTLE_S, outlier_s=CLOCK_OUTLIER_S)
        self._to_core.put(None)                 # the core drains its queue, writes stats, exits
        self._proc.join(timeout=600)
        self._stop = True

    def _imu(self, m):
        self._push(_st(m.header), "imu", (np.array([m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z]),
                                          np.array([m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z])))

    def _tref(self, m):
        th, ts = _st(m.header), m.time_ref.sec + m.time_ref.nanosec * 1e-9
        self._push(th, "tref", ts)
        if self._tref_t0 is None:
            self._tref_t0 = th
        if th - self._tref_t0 < 20.0:                     # D25 diagnostics: the first 20 s of raw offsets
            self._toff_early.append((th, th - ts))
        self._toff.append((th, th - ts))
        while self._toff and self._toff[0][0] < th - 10.0:
            self._toff.popleft()

    def _flow(self, m):
        self._push(_st(m.header), "flow", (np.array([m.flow_x_rad, m.flow_y_rad]), bool(m.valid), float(m.inlier_ratio)))

    def _rng(self, m):
        self._push(_st(m.header), "rng", float(m.range))

    def _hdg(self, m):
        t, yaw_ap, qual, ang = _st(m.header), m.vector.x, m.vector.y, m.vector.z
        if qual < 50:                                                  # VISO_QUAL_MIN (AP_VisualOdom_MAV.cpp:47-51)
            return
        if self._hdg_last is not None and t - self._hdg_last < 0.020:  # extNavIntervalMin_ms = 20
            return
        self._hdg_last = t
        # sigma: clamp [0.05, 1.5] then the 5 deg floor = 5 deg; set as the core's fixed heading noise (fwd_sigma)
        self._push(t, "fwd", (-yaw_ap, None))                           # FGO corridor yaw (CCW) = -NED yaw

    def _att(self, m):
        self._push(_st(m.header), "att", np.array([m.vector.x, m.vector.y, m.vector.z]))


def main():
    rclpy.init()
    n = FgoNode()
    try:
        rclpy.spin(n)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        n.stop_worker()
        n.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
