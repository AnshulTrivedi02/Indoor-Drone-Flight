#!/usr/bin/env python3
"""Live forward-camera heading -> ArduPilot EKF3 ExternalNav yaw (closed-loop Part 1).

Subscribes /forward_camera/image, runs the FROZEN Phase 3 heading pipeline on every Nth frame
(src/forward_camera/heading_bridge_core.py: frame definition, placeholder position, sigma,
timestamps), and sends ODOMETRY (LOCAL_FRD / BODY_FRD, quality-gated by VISO_QUAL_MIN) on its own SITL serial port (SERIAL1,
udpclient 127.0.0.1:14557, MAVProxy bypassed like imu_bridge.py). Reads EKF3's own yaw from
MAVLink ATTITUDE on the same link, only to set the fixed frame offset once on the ground.
Never reads ground truth. "No measurement" frames send nothing.

Parameters (ROS): every_n (int, 1), sigma_psi_deg (float, pre-registered per dataset),
log_path (CSV, one row per processed frame).
ArduPilot side (closedloop_heading.parm): VISO_TYPE 1, EK3_SRC1_YAW 6, VISO_QUAL_MIN 50,
VISO_DELAY_MS measured.

Run: source /opt/ros/jazzy/setup.bash; ~/venv-ardupilot python via PYTHONPATH as the other
bridges; python3 heading_bridge.py --ros-args -p use_sim_time:=true -p sigma_psi_deg:=0.148
"""
import os
os.environ["MAVLINK20"] = "1"       # ODOMETRY quality/estimator_type are v2 extensions
import json, math, sys, threading, time
import numpy as np
import cv2
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image
from geometry_msgs.msg import Vector3Stamped
from pymavlink import mavutil

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src", "forward_camera"))
from heading_bridge_core import HeadingCore, POS_PLACEHOLDER

MAVLINK_PORT = 14557
cv2.setNumThreads(1)


class HeadingBridge(Node):
    def __init__(self):
        super().__init__("heading_bridge")
        fz = json.load(open(os.path.join(HERE, "eval", "results", "fwd_calibration.json")))["frozen"]
        self.declare_parameter("every_n", 1)
        self.declare_parameter("sigma_psi_deg", 0.148)
        self.declare_parameter("log_path", "")
        self.declare_parameter("impl", "python")      # "cpp": C++ port; not for flights until ruled
        n = int(self.get_parameter("every_n").value)
        sig = float(self.get_parameter("sigma_psi_deg").value)
        self.core = HeadingCore(fz["inlier_deg"], fz["s_min"], sig, n, impl=str(self.get_parameter("impl").value))
        lp = self.get_parameter("log_path").value
        self.log = open(lp, "w") if lp else None
        if self.log:
            self.log.write("k,t_capture,t_sim_recv,t_sim_sent,proc_ms,psi_deg,support,valid,quality,sent,yaw_ap_rad,yaw_ekf_rad,offset_rad,armed\n")
        self.get_logger().info(f"frozen {fz}; every_n={n}; sigma_psi={sig} deg; SERIAL1 udp:{MAVLINK_PORT}")

        self.master = mavutil.mavlink_connection(f"udp:127.0.0.1:{MAVLINK_PORT}")
        self.master.wait_heartbeat()
        self.get_logger().info(f"heartbeat from system {self.master.target_system}")
        self.yaw_ekf, self.armed = None, False
        self._request_attitude(); self.create_timer(2.0, self._request_attitude)
        self.create_timer(0.005, self._poll)

        self.k = -1
        self._slot, self._lock, self._evt = None, threading.Lock(), threading.Event()
        self.dropped = 0
        threading.Thread(target=self._worker, daemon=True).start()
        qos = QoSProfile(reliability=ReliabilityPolicy.RELIABLE, history=HistoryPolicy.KEEP_LAST, depth=5)
        self.create_subscription(Image, "/forward_camera/image", self._on_image, qos)
        # D19 (FGO heading input, the same message as ArduPilot's): every ODOMETRY sent is also published here,
        # stamped at capture: x = yaw_ap (rad, the sent NED yaw), y = quality, z = angErr (rad, what
        # AP_VisualOdom computes from the covariance: sqrt(cov15+cov18+cov20) = sigma_psi with roll = pitch = 0)
        self.pub_sent = self.create_publisher(Vector3Stamped, "/forward_camera/heading_sent", 20)
        self._ang_err = math.radians(sig)

    def _request_attitude(self):
        self.master.mav.command_long_send(self.master.target_system, self.master.target_component,
                                          mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, 0,
                                          mavutil.mavlink.MAVLINK_MSG_ID_ATTITUDE, 20000, 0, 0, 0, 0, 0)

    def _poll(self):
        while True:
            m = self.master.recv_match(type=["ATTITUDE", "HEARTBEAT"], blocking=False)
            if m is None:
                return
            if m.get_type() == "ATTITUDE":
                self.yaw_ekf = m.yaw
            elif m.get_srcSystem() == self.master.target_system and m.get_srcComponent() == 1:
                self.armed = bool(m.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)

    def _sim_now(self):
        return self.get_clock().now().nanoseconds * 1e-9

    def _on_image(self, msg):
        self.k += 1
        if not self.core.selected(self.k):
            return
        img = np.frombuffer(msg.data, np.uint8).reshape(msg.height, msg.step)[:, :msg.width].copy()
        t = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        with self._lock:
            if self._slot is not None:
                self.dropped += 1          # worker still busy with an earlier selected frame
            self._slot = (self.k, img, t, self._sim_now())
        self._evt.set()

    def _worker(self):
        while rclpy.ok():
            self._evt.wait(); self._evt.clear()
            with self._lock:
                job, self._slot = self._slot, None
            if job is None:
                continue
            k, img, t, t_recv = job
            psi, sup, valid, dt = self.core.measure(k, img)
            sent, yaw_ap = False, float("nan")
            qual = self.core.quality(psi, sup)
            if valid and self.core.offset is None and self.yaw_ekf is not None and not self.armed:
                if self.core.feed_offset(self.yaw_ekf, psi):
                    self.get_logger().info(f"frame offset locked: {math.degrees(self.core.offset):+.3f} deg (EKF3 yaw, on ground)")
            if self.core.offset is not None:
                # every processed frame is sent; VISO_QUAL_MIN (50) rejects quality < 50 (and -1)
                yaw_ap = self.core.yaw_ap(psi) if psi is not None else 0.0
                x, y, z = POS_PLACEHOLDER
                nan = float("nan")
                self.master.mav.odometry_send(int(round(t * 1e6)), mavutil.mavlink.MAV_FRAME_LOCAL_FRD,
                                              mavutil.mavlink.MAV_FRAME_BODY_FRD, x, y, z, self.core.q_yaw(yaw_ap),
                                              nan, nan, nan, nan, nan, nan, self.core.cov, [nan] + [0.0] * 20,
                                              0, mavutil.mavlink.MAV_ESTIMATOR_TYPE_VISION, qual)
                sent = True
                hm = Vector3Stamped(); hm.header.frame_id = "ned"
                hm.header.stamp.sec = int(t); hm.header.stamp.nanosec = int(round((t - int(t)) * 1e9)) % 1000000000
                hm.vector.x, hm.vector.y, hm.vector.z = float(yaw_ap), float(qual), float(self._ang_err)
                self.pub_sent.publish(hm)
            if self.log:
                self.log.write(f"{k},{t:.6f},{t_recv:.6f},{self._sim_now():.6f},{1e3*dt:.2f},{'' if psi is None else f'{psi:.5f}'},"
                               f"{sup:.1f},{int(valid)},{qual},{int(sent)},{yaw_ap:.6f},{'' if self.yaw_ekf is None else f'{self.yaw_ekf:.6f}'},"
                               f"{'' if self.core.offset is None else f'{self.core.offset:.6f}'},{int(self.armed)}\n")
                self.log.flush()


def main():
    rclpy.init()
    n = HeadingBridge()
    try:
        rclpy.spin(n)
    except KeyboardInterrupt:
        pass
    finally:
        n.get_logger().info(f"frames {n.k + 1}, dropped selected frames {n.dropped}")
        if n.log:
            n.log.close()


if __name__ == "__main__":
    main()
