import cv2
import numpy as np

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from cv_bridge import CvBridge


class FlowTracker(Node):
    def __init__(self):
        super().__init__("flow_tracker")

        self.bridge = CvBridge()
        self.prev_gray = None
        self.prev_pts = None
        self.prev_time = None

        self.subscription = self.create_subscription(
            Image,
            "/downward_camera/image",
            self.image_callback,
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

    def image_callback(self, msg: Image):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        current_time = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9

        if self.prev_gray is None:
            self.prev_gray = gray
            self.prev_time = current_time
            self.prev_pts = cv2.goodFeaturesToTrack(gray, mask=None, **self.feature_params)
            return

        if self.prev_pts is None or len(self.prev_pts) < 20:
            self.prev_pts = cv2.goodFeaturesToTrack(self.prev_gray, mask=None, **self.feature_params)
            self.prev_gray = gray
            self.prev_time = current_time
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
            return

        good_new = next_pts[status.flatten() == 1].reshape(-1, 2)
        good_old = self.prev_pts[status.flatten() == 1].reshape(-1, 2)

        tracked_count = len(good_new)

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

            if tracked_count == 0:
                self.get_logger().warn("Tracked features = 0 after RANSAC")
                self.prev_gray = gray
                self.prev_time = current_time
                self.prev_pts = cv2.goodFeaturesToTrack(gray, mask=None, **self.feature_params)
                return

            mean_dx = float(np.median(displacement[:, 0]))
            mean_dy = float(np.median(displacement[:, 1]))

            dt = current_time - self.prev_time if self.prev_time is not None else 0.0

            if dt > 0:
                flow_x_px_s = mean_dx / dt
                flow_y_px_s = mean_dy / dt
            else:
                flow_x_px_s = 0.0
                flow_y_px_s = 0.0

            self.get_logger().info(
                f"features={tracked_count:3d}, "
                f"mean_dx={mean_dx:+.3f}px, mean_dy={mean_dy:+.3f}px, "
                f"flow_x={flow_x_px_s:+.3f}px/s, flow_y={flow_y_px_s:+.3f}px/s"
            )
        else:
            self.get_logger().warn("Tracked features = 0")

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