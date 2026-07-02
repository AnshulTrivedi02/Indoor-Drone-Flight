#!/usr/bin/env python3
"""
Bridge ArduPilot SITL body angular rates (MAVLink ATTITUDE) onto ROS2.

Opens a dedicated pymavlink UDP connection to SITL and republishes
rollspeed/pitchspeed/yawspeed as geometry_msgs/Vector3Stamped on
/attitude/angular_rates.

These are raw body-frame rates exactly as reported by MAVLink ATTITUDE,
i.e. FRD (X-forward, Y-right, Z-down) — NOT yet rotated into the Gazebo
FLU body frame or the downward camera's optical frame. That rotation is
done downstream in flow_tracker.py, which needs the camera-frame mapping
alongside the image stream. Keeping this node frame-agnostic means it
stays reusable if the camera mount ever changes.
    x = roll rate  (rollspeed,  rad/s)
    y = pitch rate (pitchspeed, rad/s)
    z = yaw rate   (yawspeed,   rad/s)

Runs on a dedicated MAVLink UDP port (14551) separate from fly_forward.py's
port (14550) — pymavlink's plain 'udp:' scheme binds and listens, so two
processes cannot share one port. sim_vehicle.py must be launched with an
extra `--out 127.0.0.1:14551` for this connection to receive traffic (see
start_sim.sh / CLAUDE.md).

The header.stamp uses the ROS clock (sim time, via /clock + use_sim_time)
rather than MAVLink's time_boot_ms, so it lines up with the image stream
timestamps used elsewhere in the pipeline. ArduPilot SITL runs lockstep
with Gazebo, so this stays closely aligned with when the attitude sample
was valid.

Usage:
    source /opt/ros/jazzy/setup.bash
    source ~/venv-ardupilot/bin/activate
    python3 attitude_bridge.py --ros-args -p use_sim_time:=true
"""

from pymavlink import mavutil

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Vector3Stamped

MAVLINK_PORT = 14551
ATTITUDE_STREAM_RATE_HZ = 50


class AttitudeBridge(Node):

    def __init__(self):
        super().__init__('attitude_bridge')

        self._pub = self.create_publisher(
            Vector3Stamped,
            '/attitude/angular_rates',
            10,
        )

        self.get_logger().info(f'Connecting to SITL on udp:127.0.0.1:{MAVLINK_PORT} ...')
        self.master = mavutil.mavlink_connection(f'udp:127.0.0.1:{MAVLINK_PORT}')
        self.master.wait_heartbeat()
        self.get_logger().info(
            f'Heartbeat received from system {self.master.target_system} '
            f'component {self.master.target_component}'
        )

        self._request_attitude_stream()

        # Poll for MAVLink messages faster than the requested ATTITUDE rate.
        self._timer = self.create_timer(1.0 / (ATTITUDE_STREAM_RATE_HZ * 2), self._poll)

        self._msg_count = 0
        self.get_logger().info('Publishing to /attitude/angular_rates')

    def _request_attitude_stream(self) -> None:
        """Ask the autopilot to send ATTITUDE at ATTITUDE_STREAM_RATE_HZ."""
        interval_us = int(1e6 / ATTITUDE_STREAM_RATE_HZ)
        self.master.mav.command_long_send(
            self.master.target_system,
            self.master.target_component,
            mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,
            0,
            mavutil.mavlink.MAVLINK_MSG_ID_ATTITUDE,
            interval_us,
            0, 0, 0, 0, 0,
        )

    def _poll(self) -> None:
        while True:
            msg = self.master.recv_match(type='ATTITUDE', blocking=False)
            if msg is None:
                break
            self._publish(msg)

    def _publish(self, msg) -> None:
        out = Vector3Stamped()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = 'base_link_frd'
        out.vector.x = msg.rollspeed
        out.vector.y = msg.pitchspeed
        out.vector.z = msg.yawspeed
        self._pub.publish(out)

        self._msg_count += 1
        if self._msg_count == 1:
            self.get_logger().info(
                f'First ATTITUDE received — rollspeed={msg.rollspeed:+.3f} '
                f'pitchspeed={msg.pitchspeed:+.3f} yawspeed={msg.yawspeed:+.3f} rad/s'
            )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = AttitudeBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
