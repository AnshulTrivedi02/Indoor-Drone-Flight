#!/usr/bin/env python3
"""Live WALL-tag bridge for experiment H (marker-relative position holding; ruling 2026-10-08). ROS 2 node, run in
~/venv-tags with ROS sourced. The floor-tag bridge of T (tag_bridge.py) is unchanged; this is its forward-camera
counterpart.

  /forward_camera/image (mono L8, 640x480, 60 deg) -> src/tags/tag_measure.py (pupil_apriltags)
    * /tags/raw   (PoseStamped, frame_id "tag_<id>"): camera-from-tag pose of EVERY detection, stamped at capture.
    * /tags/sent  (PoseWithCovarianceStamped, frame_id "tag_<id>"): the vehicle fix actually SENT, in the tag frame W
                  written as ENU (x = E_W = world x - tag x, y = N_W = world y - tag y, z = world z) + yaw (ENU), only
                  for the wall tag and only if the detection passes the validity rule (r_valid_px, from S0).
    * /forward_camera/image_audit: every `audit_every`-th forward image, unchanged (2 Hz at 15), for auditing.
    * MAVLink ODOMETRY to SITL SERIAL1 (udpclient 127.0.0.1:14557, as tag_bridge.py), when send is true:
      LOCAL_FRD / BODY_FRD, time_usec = capture time, x, y, z = (N_W, E_W, -world z) [EKF3 treats LOCAL_FRD as its NED
      frame: W is then EKF3's navigation frame], q = yaw only (yaw_ned = pi/2 - yaw_enu), velocity NaN,
      cov[0] = sigma_pos^2, cov[20] = sigma_yaw^2, quality 100. EKF3's effective noise = max(VISO_*_M_NSE, sent) with
      the 5 deg yaw floor; the UKF/FGO use the same effective values.
Wall tag (sim/worlds/room_wall_tag.sdf): id 10, centre (0, 4.998, 1.5) (front face), mounted with SDF rpy (pi/2, 0, 0).
Parameters: send (bool), r_valid_px (float; detections whose centre is farther from the image centre are not sent),
convention (texture convention key, frozen in S0), sigma_pos_m, sigma_yaw_deg, audit_every, log_path."""
import math, os, sys, time
os.environ.setdefault("MAVLINK20", "1")
import numpy as np
import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import ParameterDescriptor
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from scipy.spatial.transform import Rotation as Rot
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src", "tags"))
import tag_measure as T

MAVLINK_PORT = 14557
FX, CX, CY = 554.3827056884766, 320.0, 240.0          # forward camera: same intrinsics as the downward camera
WALL_ID = 10
WALL_P = np.array([0.0, 4.998, 1.5])
WALL_RPY = (math.pi / 2, 0.0, 0.0)


class TagBridgeFwd(Node):
    def __init__(self):
        super().__init__("tag_bridge_fwd")
        # dynamic typing for the numeric parameters: "-p r_valid_px:=400" arrives as an INTEGER (H_s0b attempt 1);
        # every value is cast explicitly below
        dyn = ParameterDescriptor(dynamic_typing=True)
        for n, v in (("send", False), ("r_valid_px", 0.0), ("sigma_pos_m", 0.05), ("sigma_yaw_deg", 5.0), ("audit_every", 15), ("log_path", ""),
                     ("status_path", ""), ("range_min_m", 0.9), ("range_max_m", 2.8)):
            self.declare_parameter(n, v, dyn if n in ("r_valid_px", "sigma_pos_m", "sigma_yaw_deg", "audit_every", "range_min_m", "range_max_m") else ParameterDescriptor())
        self.declare_parameter("convention", "", ParameterDescriptor(dynamic_typing=True))
        conv = str(self.get_parameter("convention").value)
        self.R_wt = T.wall_tag_R_wt(WALL_RPY, conv) if conv else None
        self.r_valid = float(self.get_parameter("r_valid_px").value)
        self.sig_p = float(self.get_parameter("sigma_pos_m").value); self.sig_y = math.radians(float(self.get_parameter("sigma_yaw_deg").value))
        self.audit_every = int(self.get_parameter("audit_every").value); self.n_img = 0
        self.det = T.TagDetector(FX, FX, CX, CY)
        q = QoSProfile(reliability=ReliabilityPolicy.RELIABLE, history=HistoryPolicy.KEEP_LAST, depth=5)
        self.create_subscription(Image, "/forward_camera/image", self._img, q)
        self.pub_raw = self.create_publisher(PoseStamped, "/tags/raw", 50)
        self.pub_sent = self.create_publisher(PoseWithCovarianceStamped, "/tags/sent", 50)
        self.pub_audit = self.create_publisher(Image, "/forward_camera/image_audit", 5)
        lp = self.get_parameter("log_path").value
        self.log = open(lp, "w") if lp else None
        if self.log:
            self.log.write("t_capture,t_wall_done,id,valid,sent,margin,hamming,cx,cy,range_m,x_enuW,y_enuW,z,yaw_enu,proc_ms,t_sim_sent\n")
        self.master = None
        # status file (H ruling 2026-10-08 item 4): the SITL address the fixes go to (the most recently heard SERIAL1
        # source) and the sent count, rewritten atomically on each send; fly_trial checks it against SITL's live port
        self.status_path = self.get_parameter("status_path").value; self.n_sent = 0
        # D18 sensor-validity rule (user ruling 2026-10-08, after the UKF tilt-bias trace): IN FLIGHT a fix is valid only
        # within the characterised S0a camera-to-tag range [range_min_m, range_max_m]; ON THE GROUND WHILE DISARMED it
        # stays valid at any range (the pre-arm anchor; measured separately, F1). Armed state = SITL's HEARTBEAT on this
        # link. One rule for every estimator: EKF3 and the UKF port get only these fixes over MAVLink, the FGO node and
        # the offline replays only these on /tags/sent.
        self.rng_lo = float(self.get_parameter("range_min_m").value); self.rng_hi = float(self.get_parameter("range_max_m").value)
        self.armed = False
        if self.get_parameter("send").value:
            if self.R_wt is None or self.r_valid <= 0:
                raise SystemExit("send=true needs the frozen convention and r_valid_px from S0")
            from pymavlink import mavutil
            self.mav = mavutil
            self.master = mavutil.mavlink_connection(f"udp:127.0.0.1:{MAVLINK_PORT}")
            self.get_logger().info("waiting for a heartbeat from SITL SERIAL1 ...")
            self.master.wait_heartbeat(timeout=60)
            self.get_logger().info(f"heartbeat from system {self.master.target_system}")
        self.get_logger().info(f"wall tag {WALL_ID}; send {self.master is not None}; r_valid {self.r_valid} px; convention '{conv}'; "
                               f"in-flight range band [{self.rng_lo}, {self.rng_hi}] m")

    def _img(self, m):
        t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9; t0 = time.perf_counter()
        self.n_img += 1
        if self.audit_every > 0 and self.n_img % self.audit_every == 0:
            self.pub_audit.publish(m)
        if self.master is not None:                  # drain: armed state, and the reply port follows a SITL reboot
            while True:
                mm = self.master.recv_msg()
                if mm is None:
                    break
                if mm.get_type() == "HEARTBEAT" and mm.get_srcComponent() == 1:
                    self.armed = bool(mm.base_mode & self.mav.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
        gray = np.frombuffer(m.data, np.uint8).reshape(m.height, m.step)[:, :m.width]
        # wall tag only, pose on a crop around it (tag_measure.detect_pose_roi; 2026-10-08: from the far spawn a floor tag
        # at a grazing angle broke pupil_apriltags' pose solver and crashed this node; /tags/raw is now the wall tag only)
        dets = T.detect_pose_roi(self.det, np.ascontiguousarray(gray), WALL_ID)
        rows = []; best = None
        for (i, R, tt, cn, cc, dm, hm) in dets:
            if not (np.linalg.det(R) > 0.5):            # an improper pose is never used (belt and braces)
                self.get_logger().warn(f"tag {i}: improper pose rotation (det {np.linalg.det(R):.3f}), frame skipped")
                continue
            r = PoseStamped(); r.header = m.header; r.header.frame_id = f"tag_{i}"
            r.pose.position.x, r.pose.position.y, r.pose.position.z = (float(v) for v in tt)
            qx, qy, qz, qw = Rot.from_matrix(R).as_quat()
            r.pose.orientation.x, r.pose.orientation.y, r.pose.orientation.z, r.pose.orientation.w = float(qx), float(qy), float(qz), float(qw)
            self.pub_raw.publish(r)
            if i != WALL_ID:
                continue
            rng = float(np.linalg.norm(tt))
            valid = self.r_valid > 0 and math.hypot(cc[0] - CX, cc[1] - CY) <= self.r_valid
            if self.master is not None and self.armed and not (self.rng_lo <= rng <= self.rng_hi):
                valid = False                            # D18 range rule: in flight, outside the characterised band
            pw = yaw = None
            if self.R_wt is not None:
                p, Rw = T.vehicle_pose_full(self.R_wt, WALL_P, R, tt); pw = (p[0] - WALL_P[0], p[1] - WALL_P[1], p[2]); yaw = T.yaw_of(Rw)
            rows.append([i, valid, dm, hm, cc, rng, pw, yaw])
            if valid and pw is not None and (best is None or dm > best[2]):
                best = rows[-1]
        proc = (time.perf_counter() - t0) * 1e3; t_sent = float("nan")
        if best is not None:
            _, _, dm, hm, cc, rng, pw, yaw = best
            s = PoseWithCovarianceStamped(); s.header = m.header; s.header.frame_id = f"tag_{WALL_ID}"
            s.pose.pose.position.x, s.pose.pose.position.y, s.pose.pose.position.z = (float(v) for v in pw)
            s.pose.pose.orientation.z, s.pose.pose.orientation.w = math.sin(yaw / 2), math.cos(yaw / 2)
            c = [0.0] * 36; c[0] = c[7] = c[14] = self.sig_p ** 2; c[35] = self.sig_y ** 2; s.pose.covariance = c
            self.pub_sent.publish(s)
            if self.master is not None:
                # drain SITL's messages so pymavlink's UDP client set learns a SITL reboot's new SERIAL1 source port
                # (re-exec); without this every fix after a reboot went to the dead port (H_gt_ukf)
                while self.master.recv_msg() is not None:
                    pass
                yaw_ned = math.pi / 2 - yaw; nan = float("nan")
                cov = [0.0] * 21; cov[0] = self.sig_p ** 2; cov[20] = self.sig_y ** 2
                self.master.mav.odometry_send(int(round(t * 1e6)), self.mav.mavlink.MAV_FRAME_LOCAL_FRD, self.mav.mavlink.MAV_FRAME_BODY_FRD,
                                              float(pw[1]), float(pw[0]), float(-pw[2]),
                                              [math.cos(yaw_ned / 2), 0.0, 0.0, math.sin(yaw_ned / 2)],
                                              nan, nan, nan, nan, nan, nan, cov, [nan] * 21, 0, 0, 100)
                t_sent = self.get_clock().now().nanoseconds * 1e-9
                self.n_sent += 1
                if self.status_path:
                    cl = getattr(self.master, "clients_last_alive", {})
                    dest = max(cl, key=cl.get) if cl else getattr(self.master, "last_address", None)
                    tmp = self.status_path + ".tmp"
                    with open(tmp, "w") as f:
                        f.write(f"{time.time():.3f} {dest[1] if dest else 0} {self.n_sent}\n")
                    os.replace(tmp, self.status_path)
        if self.log:
            tw = time.time()
            for i, valid, dm, hm, cc, rng, pw, yaw in rows:
                sent = best is not None and rows.index(best) == rows.index([i, valid, dm, hm, cc, rng, pw, yaw])
                px = ",".join("nan" for _ in range(3)) if pw is None else f"{pw[0]:.5f},{pw[1]:.5f},{pw[2]:.5f}"
                self.log.write(f"{t:.6f},{tw:.6f},{i},{int(valid)},{int(sent)},{dm:.2f},{hm},{cc[0]:.2f},{cc[1]:.2f},{rng:.4f},{px},"
                               f"{'nan' if yaw is None else f'{yaw:.6f}'},{proc:.2f},{t_sent:.6f}\n")
            self.log.flush()


def main():
    rclpy.init(); n = TagBridgeFwd()
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
