#!/usr/bin/env python3
"""
Bridge the Gazebo downward LiDAR onto ArduPilot SITL via MAVLink DISTANCE_SENSOR.

Subscribes to /downward_lidar/range (sensor_msgs/Range, published by the
gpu_lidar sensor in iris_with_standoffs/model.sdf — see CLAUDE.md, Sensor
Status) and forwards each reading to ArduPilot as RNGFND1, using the
Gazebo-geometry-derived range rather than ArduPilot's built-in SIM_SONAR
analog rangefinder simulation, consistent with this project's
render-driven-sensing philosophy.

Runs on a dedicated MAVLink UDP port (14552), separate from fly_forward.py's
port (14550) and attitude_bridge.py's port (14551) — pymavlink's plain 'udp:'
scheme binds and listens, so no two processes can share one port.
sim_vehicle.py must be launched with an extra `--out 127.0.0.1:14552` for
this connection to receive traffic (see start_sim.sh / CLAUDE.md), and with
lidar_rangefinder.parm appended to --defaults so RNGFND1_TYPE is MAVLink (10)
rather than gazebo-iris.parm's default Analog/SIM_SONAR (1).

sensor_msgs/Range reports range in metres; MAVLink DISTANCE_SENSOR wants
centimetres — converted here. Orientation is MAV_SENSOR_ROTATION_PITCH_270
(=25), matching RNGFND1_ORIENT in lidar_rangefinder.parm, for a
downward-facing sensor.

Readings are forwarded as soon as they arrive (no buffering/throttling) so
wall-clock latency stays minimal; the DISTANCE_SENSOR time_boot_ms field
isn't used by ArduPilot's own freshness check (it stamps arrival with its
own AP_HAL::millis() on receipt), so it's populated from this node's ROS
clock purely for traceability, not because ArduPilot depends on it.

Usage:
    source /opt/ros/jazzy/setup.bash
    source ~/venv-ardupilot/bin/activate
    python3 lidar_bridge.py --ros-args -p use_sim_time:=true
"""

import math

from pymavlink import mavutil

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Range

MAVLINK_PORT = 14552
DISTANCE_SENSOR_ORIENTATION = 25  # MAV_SENSOR_ROTATION_PITCH_270 / RNGFND1_ORIENT


class LidarBridge(Node):

    def __init__(self):
        super().__init__('lidar_bridge')

        self.get_logger().info(f'Connecting to SITL on udp:127.0.0.1:{MAVLINK_PORT} ...')
        self.master = mavutil.mavlink_connection(f'udp:127.0.0.1:{MAVLINK_PORT}')
        self.master.wait_heartbeat()
        self.get_logger().info(
            f'Heartbeat received from system {self.master.target_system} '
            f'component {self.master.target_component}'
        )

        self._start_ns = self.get_clock().now().nanoseconds
        self._msg_count = 0

        self.create_subscription(Range, '/downward_lidar/range', self._on_range, 10)
        self.get_logger().info('Forwarding /downward_lidar/range to RNGFND1 via DISTANCE_SENSOR')

    def _on_range(self, msg: Range) -> None:
        if not math.isfinite(msg.range) or not (msg.min_range <= msg.range <= msg.max_range):
            # Mirrors how a real driver would drop an invalid/no-return reading
            # rather than feed the EKF a bogus distance.
            return

        time_boot_ms = (self.get_clock().now().nanoseconds - self._start_ns) // 1_000_000
        current_distance_cm = min(max(round(msg.range * 100.0), 0), 65535)
        min_distance_cm = min(max(round(msg.min_range * 100.0), 0), 65535)
        max_distance_cm = min(max(round(msg.max_range * 100.0), 0), 65535)

        self.master.mav.distance_sensor_send(
            time_boot_ms,
            min_distance_cm,
            max_distance_cm,
            current_distance_cm,
            mavutil.mavlink.MAV_DISTANCE_SENSOR_LASER,
            0,  # id: first (and only) rangefinder instance -> RNGFND1
            DISTANCE_SENSOR_ORIENTATION,
            255,  # covariance: UINT8_MAX = unknown
        )

        self._msg_count += 1
        if self._msg_count == 1:
            self.get_logger().info(f'First DISTANCE_SENSOR sent — range={msg.range:.3f} m')


def main(args=None) -> None:
    rclpy.init(args=args)
    node = LidarBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
