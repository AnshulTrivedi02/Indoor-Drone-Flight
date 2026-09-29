#!/usr/bin/env python3
"""ROS 2 node: the online FGO (ruling D7). A THIN shell around fgo_node_core.FgoNodeCore, the class
the offline equivalence tests drive (eval/fgo_node_equiv.py). Subscribes to the same topics
fgo_replay.py reads; every message is pushed into the core in ARRIVAL order with its header stamp.
Publishes, at each keyframe, /fgo/pose (geometry_msgs/PoseStamped, ENU/FLU, stamped at the keyframe
time) and /fgo/valid (std_msgs/Bool; false after a post-take-off IMU gap, the IMU-gap rule's causal
form). Not used in any flight until FGO steps 2-3 are done and ruled on (METHODOLOGY, D7).
Run: python3 fgo_node.py --ros-args -p use_sim_time:=true [-p horizon_s:=0.10]   (~/venv-fgo + ROS)"""
import glob, math, multiprocessing as mp, os, sys, threading, time
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


def _st(h):
    return h.stamp.sec + h.stamp.nanosec * 1e-9


def _quat(r, p, y):
    cr, sr, cp, sp, cy, sy = math.cos(r / 2), math.sin(r / 2), math.cos(p / 2), math.sin(p / 2), math.cos(y / 2), math.sin(y / 2)
    return (sr * cp * cy - cr * sp * sy, cr * sp * cy + sr * cp * sy, cr * cp * sy - sr * sp * cy, cr * cp * cy + sr * sp * sy)


def _core_proc(inq, outq, kw, stats_path):
    """The FGO core process: pushes every message in arrival order; returns each new keyframe."""
    core = FgoNodeCore(**kw); n_out = 0
    while True:
        item = inq.get()
        if item is None:
            break
        t, kind, payload, tw_epoch = item
        core.push(t, kind, payload, t_wall=time.perf_counter() - (time.time() - tw_epoch))
        while n_out < len(core.traj):
            outq.put((core.traj[n_out], core.valid)); n_out += 1
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
        self._n_pub = 0
        q = QoSProfile(reliability=ReliabilityPolicy.RELIABLE, history=HistoryPolicy.KEEP_LAST, depth=200)
        self.create_subscription(Imu, "/imu/data_raw", self._imu, q)
        self.create_subscription(TimeReference, "/imu/time_ref", self._tref, q)
        self.create_subscription(OpticalFlow, "/optical_flow/measurement", self._flow, q)
        self.create_subscription(Range, "/downward_lidar/range", self._rng, q)
        self.create_subscription(Vector3Stamped, "/attitude/angular_rates", self._att, q)
        self.pub = self.create_publisher(PoseStamped, "/fgo/pose", 10)
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
                                      horizon_s=float(self.get_parameter("horizon_s").value), dejitter="causal", gap="causal"),
                                 self.get_parameter("stats_path").value), daemon=True)
        self._proc.start()
        self._stop = False
        self._pub_thread = threading.Thread(target=self._publisher, daemon=True)
        self._pub_thread.start()

    def _push(self, t, kind, payload):
        self._to_core.put((t, kind, payload, time.time()))     # wall arrival time (lag includes queueing)

    def _publisher(self):
        while not self._stop:
            try:
                row, valid = self._from_core.get(timeout=0.2)
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

    def stop_worker(self):
        self._to_core.put(None)                 # the core drains its queue, writes stats, exits
        self._proc.join(timeout=600)
        self._stop = True

    def _imu(self, m):
        self._push(_st(m.header), "imu", (np.array([m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z]),
                                          np.array([m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z])))

    def _tref(self, m):
        self._push(_st(m.header), "tref", m.time_ref.sec + m.time_ref.nanosec * 1e-9)

    def _flow(self, m):
        self._push(_st(m.header), "flow", (np.array([m.flow_x_rad, m.flow_y_rad]), bool(m.valid), float(m.inlier_ratio)))

    def _rng(self, m):
        self._push(_st(m.header), "rng", float(m.range))

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
