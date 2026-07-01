#!/usr/bin/env python3
"""
Republish Gazebo ground-truth drone pose as geometry_msgs/PoseStamped.

Subscribes to the ros_gz_bridge TFMessage output from Gazebo's
/world/<world>/dynamic_pose/info and extracts the iris_with_ardupilot
model pose (which is relative to world for a top-level model), then
publishes it on /ground_truth/pose at the same rate.

Must be run AFTER the ros_gz_bridge is publishing dynamic_pose/info.
Timestamps in the output carry Gazebo sim time (passed through from the
bridge header) so they align with /clock when use_sim_time is active.

Usage:
    source /opt/ros/jazzy/setup.bash
    python3 ground_truth_pub.py [world_name] [model_name]

    world_name:  Gazebo world name (default: iris_textured)
    model_name:  Gazebo model name to track (default: iris_with_ardupilot)
"""

import sys
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
from tf2_msgs.msg import TFMessage
from geometry_msgs.msg import PoseStamped

WORLD = sys.argv[1] if len(sys.argv) > 1 else 'iris_textured'
MODEL = sys.argv[2] if len(sys.argv) > 2 else 'iris_with_ardupilot'
DYN_POSE_TOPIC = f'/world/{WORLD}/dynamic_pose/info'

# Match the QoS the bridge uses for dynamic_pose/info (best-effort, keep-last 1).
_SENSOR_QOS = QoSProfile(
    reliability=QoSReliabilityPolicy.BEST_EFFORT,
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=1,
)


class GroundTruthPublisher(Node):

    def __init__(self):
        super().__init__('ground_truth_pub')

        self._pub = self.create_publisher(PoseStamped, '/ground_truth/pose', 10)
        self._sub = self.create_subscription(
            TFMessage,
            DYN_POSE_TOPIC,
            self._cb,
            _SENSOR_QOS,
        )
        self._warned_missing = False
        self.get_logger().info(
            f'Subscribing to {DYN_POSE_TOPIC}, tracking model "{MODEL}" '
            f'→ /ground_truth/pose'
        )

    def _cb(self, msg: TFMessage) -> None:
        for tf in msg.transforms:
            if tf.child_frame_id == MODEL:
                ps = PoseStamped()
                ps.header = tf.header
                ps.header.frame_id = 'world'
                ps.pose.position.x = tf.transform.translation.x
                ps.pose.position.y = tf.transform.translation.y
                ps.pose.position.z = tf.transform.translation.z
                ps.pose.orientation = tf.transform.rotation
                self._pub.publish(ps)
                self._warned_missing = False
                return

        if not self._warned_missing:
            frames = [t.child_frame_id for t in msg.transforms]
            self.get_logger().warn(
                f'Model "{MODEL}" not found in TFMessage. '
                f'Available child_frame_ids: {frames}. '
                f'Run with: python3 ground_truth_pub.py {WORLD} <correct_model_name>'
            )
            self._warned_missing = True


def main() -> None:
    rclpy.init()
    node = GroundTruthPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
