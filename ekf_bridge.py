#!/usr/bin/env python3
"""
Bridge ArduPilot EKF3's state estimate onto ROS2 as /ekf/pose
(geometry_msgs/PoseStamped), for Stage B evaluation against
/ground_truth/pose — see CLAUDE.md, "EKF State Estimate — Stage B (evo
evaluation)".

Reads MAVLink LOCAL_POSITION_NED (position, NED) and ATTITUDE_QUATERNION
(orientation, FRD-body-relative-to-NED-world) and republishes as a single
PoseStamped in ENU/FLU (Gazebo/ROS convention, matching /ground_truth/pose),
applying the NED<->ENU and FRD<->FLU transforms documented in CLAUDE.md:

  Position (NED -> ENU, purely definitional axis relabelling):
    enu.x = ned.y ; enu.y = ned.x ; enu.z = -ned.z

  Orientation (FRD-body/NED-world -> FLU-body/ENU-world), composed from two
  fixed quaternions (Hamilton product, q_enu_flu = q_ned2enu (x) q_attitude
  (x) q_frd2flu):
    q_ned2enu = (w=0, x=sqrt(2)/2, y=sqrt(2)/2, z=0)  - 180 deg about the NED
      axis (1,1,0)/sqrt(2); verified by explicit rotation-matrix conversion,
      not assumed.
    q_frd2flu = (w=0, x=1, y=0, z=0)  - 180 deg about body X (forward);
      exactly matches flow_tracker.py's own already-empirically-validated
      FRD<->FLU relationship ((wx, -wy, -wz) for angular rates - the same
      transform applied to a static orientation instead of a rate).

Runs on a dedicated MAVLink UDP port (14554), separate from fly_forward.py
(14550), attitude_bridge.py (14551), lidar_bridge.py (14552) and
flow_bridge.py (14553). sim_vehicle.py must be launched with an extra
`--out 127.0.0.1:14554` for this connection to receive traffic (see
start_sim.sh / CLAUDE.md).

Usage:
    source /opt/ros/jazzy/setup.bash
    source ~/venv-ardupilot/bin/activate
    python3 ekf_bridge.py --ros-args -p use_sim_time:=true
"""

import math

from pymavlink import mavutil

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped

MAVLINK_PORT = 14554
STREAM_RATE_HZ = 30

# Fixed frame-transform quaternions (w, x, y, z) - see module docstring.
Q_NED2ENU = (0.0, math.sqrt(2) / 2, math.sqrt(2) / 2, 0.0)
Q_FRD2FLU = (0.0, 1.0, 0.0, 0.0)


def quat_mul(a, b):
    """Hamilton product a (x) b, both (w, x, y, z)."""
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    )


class EkfBridge(Node):

    def __init__(self):
        super().__init__('ekf_bridge')

        self._pub = self.create_publisher(PoseStamped, '/ekf/pose', 10)

        self.get_logger().info(f'Connecting to SITL on udp:127.0.0.1:{MAVLINK_PORT} ...')
        self.master = mavutil.mavlink_connection(f'udp:127.0.0.1:{MAVLINK_PORT}')
        self.master.wait_heartbeat()
        self.get_logger().info(
            f'Heartbeat received from system {self.master.target_system} '
            f'component {self.master.target_component}'
        )

        self._request_streams()
        self._stream_request_timer = self.create_timer(2.0, self._request_streams)

        # Poll for MAVLink messages faster than the requested stream rate.
        self._timer = self.create_timer(1.0 / (STREAM_RATE_HZ * 2), self._poll)

        self._last_quat_enu_flu = (1.0, 0.0, 0.0, 0.0)  # identity until first ATTITUDE_QUATERNION
        self._msg_count = 0
        self.get_logger().info('Publishing to /ekf/pose')

    def _request_streams(self) -> None:
        interval_us = int(1e6 / STREAM_RATE_HZ)
        for msg_id in (
            mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED,
            mavutil.mavlink.MAVLINK_MSG_ID_ATTITUDE_QUATERNION,
        ):
            self.master.mav.command_long_send(
                self.master.target_system,
                self.master.target_component,
                mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,
                0,
                msg_id,
                interval_us,
                0, 0, 0, 0, 0,
            )

    def _poll(self) -> None:
        while True:
            msg = self.master.recv_match(
                type=['LOCAL_POSITION_NED', 'ATTITUDE_QUATERNION'], blocking=False)
            if msg is None:
                break
            if msg.get_type() == 'ATTITUDE_QUATERNION':
                self._on_attitude(msg)
            else:
                self._on_position(msg)

    def _on_attitude(self, msg) -> None:
        q_att = (msg.q1, msg.q2, msg.q3, msg.q4)  # (w, x, y, z), FRD body rel. NED world
        self._last_quat_enu_flu = quat_mul(quat_mul(Q_NED2ENU, q_att), Q_FRD2FLU)

    def _on_position(self, msg) -> None:
        out = PoseStamped()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = 'map'

        out.pose.position.x = float(msg.y)   # East
        out.pose.position.y = float(msg.x)   # North
        out.pose.position.z = float(-msg.z)  # Up

        w, x, y, z = self._last_quat_enu_flu
        out.pose.orientation.w = w
        out.pose.orientation.x = x
        out.pose.orientation.y = y
        out.pose.orientation.z = z

        self._pub.publish(out)

        self._msg_count += 1
        if self._msg_count == 1:
            self.get_logger().info(
                f'First /ekf/pose sent - position=({out.pose.position.x:+.3f},'
                f'{out.pose.position.y:+.3f},{out.pose.position.z:+.3f}) m'
            )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = EkfBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
