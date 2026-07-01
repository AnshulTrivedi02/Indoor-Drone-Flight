#!/usr/bin/env python3
"""
Republish Gazebo ground-truth drone pose as geometry_msgs/PoseStamped.

Subscribes to /world/<world>/dynamic_pose/info bridged as PoseArray
(geometry_msgs/msg/PoseArray ← gz.msgs.Pose_V).

The PoseArray contains all dynamic entity poses in Gazebo-defined order.
poses[0] is always iris_with_ardupilot (the top-level model) whose pose
is relative to the world frame — all other entries are relative to their
parent entities and are not useful as ground truth.

The PoseArray header carries the Gazebo sim timestamp from the Pose_V
outer header, so /ground_truth/pose timestamps track sim time.

Usage:
    source /opt/ros/jazzy/setup.bash
    python3 ground_truth_pub.py [world_name]

    world_name:  Gazebo world name (default: iris_textured)
"""

import sys
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
from geometry_msgs.msg import PoseArray, PoseStamped

WORLD = sys.argv[1] if len(sys.argv) > 1 else 'iris_textured'
DYN_POSE_TOPIC = f'/world/{WORLD}/dynamic_pose/info'

# Match the QoS the bridge uses (best-effort, keep-last 1).
_SENSOR_QOS = QoSProfile(
    reliability=QoSReliabilityPolicy.BEST_EFFORT,
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=1,
)

# Minimum publish count before giving up and warning about empty messages.
_WARN_AFTER = 5


class GroundTruthPublisher(Node):

    def __init__(self):
        super().__init__('ground_truth_pub')

        self._pub = self.create_publisher(PoseStamped, '/ground_truth/pose', 10)
        self._sub = self.create_subscription(
            PoseArray,
            DYN_POSE_TOPIC,
            self._cb,
            _SENSOR_QOS,
        )
        self._msg_count = 0
        self.get_logger().info(
            f'Subscribing to {DYN_POSE_TOPIC} (PoseArray) → /ground_truth/pose'
        )
        self.get_logger().info(
            'poses[0] assumed to be iris_with_ardupilot (top-level model, world frame)'
        )

    def _cb(self, msg: PoseArray) -> None:
        self._msg_count += 1

        if not msg.poses:
            if self._msg_count >= _WARN_AFTER:
                self.get_logger().warn('Received PoseArray with no poses — bridge may not be active yet')
            return

        ps = PoseStamped()
        # Use the PoseArray's outer header: it carries the Gazebo Pose_V sim timestamp.
        ps.header = msg.header
        ps.header.frame_id = 'world'
        ps.pose = msg.poses[0]
        self._pub.publish(ps)

        if self._msg_count == 1:
            stamp = msg.header.stamp
            self.get_logger().info(
                f'First pose published — stamp sec={stamp.sec} '
                f'(0 = wall-clock fallback needed; >0 = sim time OK)'
            )


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
