from collections import deque

import cv2
import numpy as np

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from geometry_msgs.msg import Vector3Stamped
from cv_bridge import CvBridge

from optical_flow_interfaces.msg import OpticalFlow

# Camera focal length in pixels (confirmed via calibration, see CLAUDE.md).
FOCAL_LENGTH_PX = 554.0

# Angular-rate samples to retain for interpolation across a frame interval.
# At ~50 Hz attitude / ~30 Hz images this covers a few frames of history.
RATE_BUFFER_LEN = 100


class FlowTracker(Node):
    def __init__(self):
        super().__init__("flow_tracker")

        self.declare_parameter("min_valid_features", 20)
        self.declare_parameter("enable_derotation", True)

        self.bridge = CvBridge()
        self.prev_gray = None
        self.prev_pts = None
        self.prev_time = None

        # (timestamp_s, rollspeed, pitchspeed, yawspeed) — raw FRD body rates
        # from attitude_bridge.py, buffered for interpolation across the
        # LK-tracked frame interval (rates and images are on different
        # timelines, so "latest rate seen" is not accurate enough).
        self._rate_buffer = deque(maxlen=RATE_BUFFER_LEN)
        self._warned_no_attitude = False

        self.subscription = self.create_subscription(
            Image,
            "/downward_camera/image",
            self.image_callback,
            10,
        )

        self._attitude_sub = self.create_subscription(
            Vector3Stamped,
            "/attitude/angular_rates",
            self._attitude_callback,
            10,
        )

        self._pub = self.create_publisher(
            OpticalFlow,
            "/optical_flow/measurement",
            10,
        )

        self.feature_params = dict(
            maxCorners=200,
            qualityLevel=0.01,
            minDistance=7,
            blockSize=7,
        )

        self.lk_params = dict(
            winSize=(21, 21),
            maxLevel=3,
            criteria=(
                cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
                30,
                0.01,
            ),
        )

        self.get_logger().info("Optical flow tracker started.")
        self.get_logger().info("Subscribing to /downward_camera/image")
        self.get_logger().info("Subscribing to /attitude/angular_rates")
        self.get_logger().info("Publishing to /optical_flow/measurement")

    def _attitude_callback(self, msg: Vector3Stamped) -> None:
        t = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        self._rate_buffer.append((t, msg.vector.x, msg.vector.y, msg.vector.z))

    def _interp_rate_at(self, t: float):
        """Linearly interpolate buffered (rollspeed, pitchspeed, yawspeed) at time t."""
        if not self._rate_buffer:
            return None
        if t <= self._rate_buffer[0][0]:
            return self._rate_buffer[0][1:]
        if t >= self._rate_buffer[-1][0]:
            return self._rate_buffer[-1][1:]
        for (t0, *r0), (t1, *r1) in zip(self._rate_buffer, list(self._rate_buffer)[1:]):
            if t0 <= t <= t1:
                alpha = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
                return tuple(a + alpha * (b - a) for a, b in zip(r0, r1))
        return self._rate_buffer[-1][1:]

    def _mean_rate_over_interval(self, t0: float, t1: float):
        """Mean (rollspeed, pitchspeed, yawspeed) over [t0, t1].

        Uses buffered samples that fall inside the interval when available
        (attitude arrives faster than images), otherwise falls back to the
        interpolated endpoints. Returns zeros if no attitude data has been
        received yet — a safe no-op fallback that leaves flow undecorated.
        """
        samples = [s[1:] for s in self._rate_buffer if t0 <= s[0] <= t1]
        if samples:
            n = len(samples)
            return tuple(sum(c) / n for c in zip(*samples))

        r0 = self._interp_rate_at(t0)
        r1 = self._interp_rate_at(t1)
        if r0 is None or r1 is None:
            if not self._warned_no_attitude:
                self.get_logger().warn(
                    "No /attitude/angular_rates data received yet — "
                    "derotation is a no-op until attitude_bridge.py is running."
                )
                self._warned_no_attitude = True
            return (0.0, 0.0, 0.0)
        return tuple((a + b) / 2.0 for a, b in zip(r0, r1))

    def _publish_invalid(self, img_msg: Image) -> None:
        """Publish a zero/invalid measurement using the image header stamp."""
        msg = OpticalFlow()
        msg.header.stamp = img_msg.header.stamp
        msg.header.frame_id = "downward_camera"
        msg.valid = False
        self._pub.publish(msg)

    def image_callback(self, msg: Image):
        min_valid = self.get_parameter("min_valid_features").value

        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        current_time = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9

        if self.prev_gray is None:
            self.prev_gray = gray
            self.prev_time = current_time
            self.prev_pts = cv2.goodFeaturesToTrack(gray, mask=None, **self.feature_params)
            self._publish_invalid(msg)
            return

        if self.prev_pts is None or len(self.prev_pts) < 20:
            self.prev_pts = cv2.goodFeaturesToTrack(self.prev_gray, mask=None, **self.feature_params)
            self.prev_gray = gray
            self.prev_time = current_time
            self._publish_invalid(msg)
            return

        next_pts, status, error = cv2.calcOpticalFlowPyrLK(
            self.prev_gray,
            gray,
            self.prev_pts,
            None,
            **self.lk_params,
        )

        if next_pts is None or status is None:
            self.get_logger().warn("No optical flow points found.")
            self.prev_gray = gray
            self.prev_pts = cv2.goodFeaturesToTrack(gray, mask=None, **self.feature_params)
            self.prev_time = current_time
            self._publish_invalid(msg)
            return

        good_new = next_pts[status.flatten() == 1].reshape(-1, 2)
        good_old = self.prev_pts[status.flatten() == 1].reshape(-1, 2)

        tracked_count = len(good_new)
        pre_ransac_count = tracked_count

        if tracked_count > 0:
            displacement = good_new - good_old

            # RANSAC: reject geometrically inconsistent flow vectors
            if tracked_count >= 4:
                _, inlier_mask = cv2.estimateAffinePartial2D(
                    good_old, good_new,
                    method=cv2.RANSAC,
                    ransacReprojThreshold=2.0,
                )
                if inlier_mask is not None:
                    inliers = inlier_mask.flatten().astype(bool)
                    displacement = displacement[inliers]
                    tracked_count = int(np.sum(inliers))

            inlier_ratio = tracked_count / pre_ransac_count if pre_ransac_count > 0 else 0.0

            if tracked_count == 0:
                self.get_logger().warn("Tracked features = 0 after RANSAC")
                self.prev_gray = gray
                self.prev_time = current_time
                self.prev_pts = cv2.goodFeaturesToTrack(gray, mask=None, **self.feature_params)
                self._publish_invalid(msg)
                return

            mean_dx = float(np.median(displacement[:, 0]))
            mean_dy = float(np.median(displacement[:, 1]))

            interval_start = self.prev_time
            dt = current_time - interval_start if interval_start is not None else 0.0

            if dt > 0:
                flow_x_px_s = mean_dx / dt
                flow_y_px_s = mean_dy / dt
            else:
                flow_x_px_s = 0.0
                flow_y_px_s = 0.0

            # --- Gyro derotation -------------------------------------------------
            # Body rates (FRD, from MAVLink ATTITUDE via attitude_bridge.py) mapped
            # into the downward camera's optical frame (X=right, Y=down, Z=boresight):
            #   FRD body -> Gazebo FLU body:  (wx, -wy, -wz)   [imu_link's 180 deg
            #       roll SDF pose confirms this FRD<->FLU convention]
            #   FLU body -> camera mount:     Ry(90 deg) mount rotation (sensor
            #       <pose> in iris_with_standoffs/model.sdf) -> (wz, -wy, wx)
            #   mount (FLU-style) -> optical: X_opt=-Y_mount, Y_opt=-Z_mount,
            #       Z_opt=X_mount -> (wy, -wx, wz) = (pitchspeed, -rollspeed, yawspeed)
            # For small angles near the image centre, rotational pixel flow
            # reduces to (u_rot, v_rot) = (-f*wy_cam, f*wx_cam), which combines to:
            #     flow_x_rot = -FOCAL_LENGTH_PX * rollspeed
            #     flow_y_rot = +FOCAL_LENGTH_PX * pitchspeed
            # NOTE: the roll term's sign was flipped from the original derivation
            # (+f*rollspeed) after pure-rotation hover testing showed the
            # correction being added rather than subtracted from flow_x — the
            # derotated magnitude grew instead of collapsing toward zero. The
            # pitch term has the same derivation shape and may need the same
            # flip; not yet confirmed by an isolated pitch-only hover test.
            # Cross-checked against the validated forward-flight result (vx ->
            # flow_y only, never flow_x) — see CLAUDE.md. Yaw rate is dropped: a
            # pure boresight spin nets to ~zero in the median for a roughly
            # centred feature spread; the pure-yaw hover test is what verifies
            # that assumption actually holds for this scene.
            enable_derotation = self.get_parameter("enable_derotation").value
            rollspeed, pitchspeed, _yawspeed = self._mean_rate_over_interval(
                interval_start, current_time
            ) if interval_start is not None else (0.0, 0.0, 0.0)

            flow_x_rot = -FOCAL_LENGTH_PX * rollspeed
            flow_y_rot = FOCAL_LENGTH_PX * pitchspeed

            if enable_derotation:
                flow_x_derot = flow_x_px_s - flow_x_rot
                flow_y_derot = flow_y_px_s - flow_y_rot
            else:
                flow_x_derot = flow_x_px_s
                flow_y_derot = flow_y_px_s
            # -----------------------------------------------------------------------

            self.get_logger().info(
                f"features={tracked_count:3d}, "
                f"raw=({flow_x_px_s:+.3f},{flow_y_px_s:+.3f})px/s, "
                f"rot=({flow_x_rot:+.3f},{flow_y_rot:+.3f})px/s, "
                f"derot=({flow_x_derot:+.3f},{flow_y_derot:+.3f})px/s "
                f"[derotation={'on' if enable_derotation else 'off'}]"
            )

            # Stamp from the incoming image — mandatory for sim-time alignment.
            out = OpticalFlow()
            out.header.stamp = msg.header.stamp
            out.header.frame_id = "downward_camera"
            out.flow_x = flow_x_derot
            out.flow_y = flow_y_derot
            out.flow_x_raw = flow_x_px_s
            out.flow_y_raw = flow_y_px_s
            out.derotation_enabled = enable_derotation
            out.feature_count = tracked_count
            out.inlier_ratio = inlier_ratio
            out.valid = tracked_count >= min_valid
            # rad/s fields remain 0.0 until Task 3 (pixel-to-radian conversion).
            out.flow_x_rad = 0.0
            out.flow_y_rad = 0.0
            self._pub.publish(out)

        else:
            self.get_logger().warn("Tracked features = 0")
            self._publish_invalid(msg)

        self.prev_gray = gray
        self.prev_time = current_time

        if tracked_count < 20:
            self.prev_pts = cv2.goodFeaturesToTrack(gray, mask=None, **self.feature_params)
        else:
            self.prev_pts = good_new.reshape(-1, 1, 2)


def main(args=None):
    rclpy.init(args=args)
    node = FlowTracker()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
