#!/usr/bin/env python3
"""Live AprilTag bridge (experiments T and L; user ruling 2026-10-08). ROS 2 node, run in ~/venv-tags with ROS sourced.

  /downward_camera/image -> src/tags/tag_measure.py (pupil_apriltags; frames frozen on the room check flight)
    * /tags/raw   (geometry_msgs/PoseStamped, one per detection, frame_id "tag_<id>"): camera-from-tag pose (R_ct, t_ct)
                  for EVERY detected tag, stamped at image capture. Used by L (tag positions unknown) and the tag report.
    * /tags/sent  (geometry_msgs/PoseWithCovarianceStamped, frame_id "tag_<id>"): the vehicle pose fix ACTUALLY SENT to
                  EKF3 (world ENU position + yaw), only for tags in this flight's condition subset (-p tag_ids). At most
                  ONE per image (the detection with the largest decision margin), so EKF3 (>= 20 ms between ExtNav
                  samples) and the UKF/FGO (replaying this topic) receive identical measurements.
    * MAVLink ODOMETRY to SITL SERIAL1 (udpclient 127.0.0.1:14557, as heading_bridge.py), the heading-bridge path:
      frame_id MAV_FRAME_LOCAL_FRD, child MAV_FRAME_BODY_FRD; time_usec = image capture time; x, y, z = the fix in
      NED (N = world y, E = world x, D = -world z: EKF3 treats LOCAL_FRD as its NED frame, no rotation applied, so the
      tag map is north-aligned through this mapping); q = yaw only (roll = pitch = 0; EKF3 extracts yaw only);
      velocity NaN (so useExtNavVel stays false); pose_covariance: cov[0] = sigma_pos^2, cov[6] = cov[11] = 0 so
      posErr = sqrt(cov0 + cov6 + cov11) = sigma_pos exactly; cov[15] = cov[18] = 0, cov[20] = sigma_yaw^2; quality 100.
      EKF3's effective noise: sigma_pos_eff = max(VISO_POS_M_NSE, sigma_pos); sigma_yaw_eff = max(VISO_YAW_M_NSE,
      angErr, 5 deg). These EFFECTIVE values are what the UKF and FGO must use (noise parity).
Parameters: tag_ids ("all" or "0,1,2,3"), sigma_pos_m, sigma_yaw_deg, map (tag map JSON), log_path (CSV), send (bool).
Run: python3 tag_bridge.py --ros-args -p use_sim_time:=true -p tag_ids:=0,1,2,3 -p sigma_pos_m:=0.05"""
import math, os, sys, time
os.environ.setdefault("MAVLINK20", "1")
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from scipy.spatial.transform import Rotation as Rot
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src", "tags"))
import tag_measure as T

MAVLINK_PORT = 14557
FX, CX, CY = 554.3827056884766, 320.0, 240.0      # downward camera (640x480, 60 deg HFOV); checked against camera_info
# Fix validity (measurement-intrinsic, image information only; tag characterisation 2026-10-08): a detection is eligible
# to be SENT only if the tag centre lies in the central third of the image (radius <= 1/3 of the half-diagonal, 133 px).
# There, at the 2.26 m cruise height, position p95 = 40 mm (sigma_pos 0.05 m); in the middle third it is 207 mm.
R_VALID = 1.0 / 3.0; HALF_DIAG = (CX ** 2 + CY ** 2) ** 0.5


class TagBridge(Node):
    def __init__(self):
        super().__init__("tag_bridge")
        self.declare_parameter("tag_ids", "all"); self.declare_parameter("sigma_pos_m", 0.05)
        self.declare_parameter("sigma_yaw_deg", 5.0); self.declare_parameter("send", True)
        self.declare_parameter("map", os.path.join(HERE, "sim", "worlds", "room_tags_map.json"))
        self.declare_parameter("log_path", "")
        ids = str(self.get_parameter("tag_ids").value)
        self.map = T.load_map(self.get_parameter("map").value)
        self.subset = set(self.map) if ids == "all" else {int(x) for x in ids.split(",") if x.strip() != ""}
        self.sig_p = float(self.get_parameter("sigma_pos_m").value); self.sig_y = math.radians(float(self.get_parameter("sigma_yaw_deg").value))
        self.det = T.TagDetector(FX, FX, CX, CY)
        q = QoSProfile(reliability=ReliabilityPolicy.RELIABLE, history=HistoryPolicy.KEEP_LAST, depth=5)
        self.create_subscription(Image, "/downward_camera/image", self._img, q)
        self.pub_raw = self.create_publisher(PoseStamped, "/tags/raw", 50)
        self.pub_sent = self.create_publisher(PoseWithCovarianceStamped, "/tags/sent", 50)
        lp = self.get_parameter("log_path").value
        self.log = open(lp, "w") if lp else None
        if self.log:
            self.log.write("t_capture,t_wall_done,id,in_subset,sent,margin,hamming,cx,cy,x_enu,y_enu,z_enu,yaw_enu,proc_ms,t_sim_sent\n")
        self.master = None
        if self.get_parameter("send").value:
            from pymavlink import mavutil
            self.mav = mavutil
            self.master = mavutil.mavlink_connection(f"udp:127.0.0.1:{MAVLINK_PORT}")
            self.get_logger().info("waiting for a heartbeat from SITL SERIAL1 ...")
            self.master.wait_heartbeat(timeout=60)
            self.get_logger().info(f"heartbeat from system {self.master.target_system}")
        self.get_logger().info(f"tag subset {sorted(self.subset)}; sigma_pos {self.sig_p} m; sigma_yaw {math.degrees(self.sig_y)} deg")

    def _img(self, m):
        t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9; t0 = time.perf_counter()
        img = np.frombuffer(m.data, np.uint8).reshape(m.height, m.step)
        img = img[:, :m.width * 3].reshape(m.height, m.width, 3)
        gray = (0.299 * img[:, :, 0] + 0.587 * img[:, :, 1] + 0.114 * img[:, :, 2]).astype(np.uint8)
        dets = self.det.detect(gray)
        best = None; fixes = []
        for (i, R, tt, cn, cc, dm, hm) in dets:
            r = PoseStamped(); r.header = m.header; r.header.frame_id = f"tag_{i}"
            r.pose.position.x, r.pose.position.y, r.pose.position.z = (float(v) for v in tt)
            qx, qy, qz, qw = Rot.from_matrix(R).as_quat()
            r.pose.orientation.x, r.pose.orientation.y, r.pose.orientation.z, r.pose.orientation.w = float(qx), float(qy), float(qz), float(qw)
            self.pub_raw.publish(r)
            if i in self.map:
                p, Rw = T.vehicle_pose(self.map[i], R, tt); fixes.append((i, dm, hm, cc, p, T.yaw_of(Rw)))
                central = ((cc[0] - CX) ** 2 + (cc[1] - CY) ** 2) ** 0.5 <= R_VALID * HALF_DIAG
                if i in self.subset and central and (best is None or dm > best[1]):
                    best = fixes[-1]
        proc = (time.perf_counter() - t0) * 1e3
        if best is not None:
            i, dm, hm, cc, p, yaw = best
            s = PoseWithCovarianceStamped(); s.header = m.header; s.header.frame_id = f"tag_{i}"
            s.pose.pose.position.x, s.pose.pose.position.y, s.pose.pose.position.z = (float(v) for v in p)
            s.pose.pose.orientation.z, s.pose.pose.orientation.w = math.sin(yaw / 2), math.cos(yaw / 2)
            c = [0.0] * 36; c[0] = c[7] = c[14] = self.sig_p ** 2; c[35] = self.sig_y ** 2; s.pose.covariance = c
            self.pub_sent.publish(s)
            if self.master is not None:
                yaw_ned = math.pi / 2 - yaw
                cov = [0.0] * 21; cov[0] = self.sig_p ** 2; cov[20] = self.sig_y ** 2
                nan = float("nan")
                self.master.mav.odometry_send(int(round(t * 1e6)), self.mav.mavlink.MAV_FRAME_LOCAL_FRD, self.mav.mavlink.MAV_FRAME_BODY_FRD,
                                              float(p[1]), float(p[0]), float(-p[2]),
                                              [math.cos(yaw_ned / 2), 0.0, 0.0, math.sin(yaw_ned / 2)],
                                              nan, nan, nan, nan, nan, nan, cov, [nan] * 21, 0, 0, 100)
        t_sent = self.get_clock().now().nanoseconds * 1e-9 if best is not None else float("nan")   # sim clock (use_sim_time)
        if self.log:
            tw = time.time()
            for (i, dm, hm, cc, p, yaw) in fixes:
                sent = best is not None and i == best[0]
                self.log.write(f"{t:.6f},{tw:.6f},{i},{int(i in self.subset)},{int(sent)},{dm:.2f},{hm},{cc[0]:.2f},{cc[1]:.2f},"
                               f"{p[0]:.5f},{p[1]:.5f},{p[2]:.5f},{yaw:.6f},{proc:.2f},{t_sent:.6f}\n")
            self.log.flush()


def main():
    rclpy.init(); n = TagBridge()
    try:
        rclpy.spin(n)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        if n.log: n.log.close()
        n.destroy_node()
        if rclpy.ok(): rclpy.shutdown()


if __name__ == "__main__":
    main()
