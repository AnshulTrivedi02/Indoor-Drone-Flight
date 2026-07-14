#!/usr/bin/env python3
"""
Bridge the custom optical flow measurement onto ArduPilot SITL via MAVLink
OPTICAL_FLOW, for EKF3 flow-velocity fusion (Stage A of the EKF baseline —
see CLAUDE.md, "Downward Optical Flow — EKF3 Fusion (Stage A)").

Subscribes to /optical_flow/measurement (custom OpticalFlow msg, from
flow_tracker.py) and /downward_lidar/range (sensor_msgs/Range), and injects
MAVLink OPTICAL_FLOW (message 100) — NOT OPTICAL_FLOW_RAD (message 106).
This ArduPilot build's GCS_MAVLINK::handle_message() has no case for
OPTICAL_FLOW_RAD at all (confirmed by reading GCS_Common.cpp directly), so
an injected OPTICAL_FLOW_RAD message would be silently dropped. FLOW_TYPE=5
(MAVLink) is served by AP_OpticalFlow_MAV, which decodes OPTICAL_FLOW and
reads its flow_rate_x/flow_rate_y extension fields (rad/s, instantaneous
rate) in preference to the deprecated flow_x/flow_y int16 fields. That
backend samples its own AHRS gyro internally for body-rate compensation —
it does not read gyro data from the message at all — so we send flow only.

flow_rate_x/y are MAVLink v2 extension fields, absent from pymavlink's
default v1 dialect (confirmed empirically: MAVLink_optical_flow_message's
fieldnames omits them, and optical_flow_send()'s signature has no
flow_rate_x/y parameter, unless MAVLINK20=1 is set before importing
pymavlink, which switches to the v20 dialect module). That must happen
before the `from pymavlink import mavutil` import below.

Axis/sign mapping: flow_x_rad/flow_y_rad (from /optical_flow/measurement)
are in the camera's optical/pixel frame (X=image-right, Y=image-down; see
flow_tracker.py). This is best-derived, not empirically confirmed - derived
from flow_tracker.py's own already-validated rotation-derotation formula
(flow_x_rot = -FOCAL*rollspeed, flow_y_rot = +FOCAL*pitchspeed) compared
against MAVLink OPTICAL_FLOW's field convention ("RH rotation about X
induces POSITIVE flow_rate_x"; "RH rotation about Y induces POSITIVE
flow_rate_y"): our flow_x_rot has the opposite sign to what a positive-roll
should give under the message's own convention, so flow_rate_x needs a sign
flip; flow_y_rot already matches, so flow_rate_y does not. MUST be verified
empirically per CLAUDE.md, "Downward Optical Flow — EKF3 Fusion (Stage A)"
via a known-direction (pure forward) flight and XKF5 FIX/FIY sign/magnitude
in the dataflash log, same as flow_tracker.py's own rotation-sign was only
finalised after hover testing - do not trust this derivation alone.

Runs on a dedicated MAVLink UDP port (14553), separate from fly_forward.py
(14550), attitude_bridge.py (14551) and lidar_bridge.py (14552).
sim_vehicle.py must be launched with an extra `--out 127.0.0.1:14553` for
this connection to receive traffic (see start_sim.sh / CLAUDE.md), and with
flow_ekf.parm appended to --defaults so FLOW_TYPE/EK3_SRC1_VELXY/EK3_FLOW_USE
are set correctly.

Usage:
    source /opt/ros/jazzy/setup.bash
    source ~/venv-ardupilot/bin/activate
    python3 flow_bridge.py --ros-args -p use_sim_time:=true
"""

import math
import os

# Must be set before importing pymavlink - selects the v20 dialect module,
# which is the only one exposing OPTICAL_FLOW's flow_rate_x/flow_rate_y
# extension fields (see module docstring above).
os.environ["MAVLINK20"] = "1"

from pymavlink import mavutil

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Range
from optical_flow_interfaces.msg import OpticalFlow

MAVLINK_PORT = 14553

# Ground-truth-free staleness guard: if the last LiDAR reading is older than
# this, ground_distance is reported as unknown (-1) rather than stale.
LIDAR_STALENESS_SEC = 0.5


class FlowBridge(Node):

    def __init__(self):
        super().__init__('flow_bridge')

        self.get_logger().info(f'Connecting to SITL on udp:127.0.0.1:{MAVLINK_PORT} ...')
        self.master = mavutil.mavlink_connection(f'udp:127.0.0.1:{MAVLINK_PORT}')
        self.master.wait_heartbeat()
        self.get_logger().info(
            f'Heartbeat received from system {self.master.target_system} '
            f'component {self.master.target_component}'
        )

        self._start_ns = self.get_clock().now().nanoseconds
        self._msg_count = 0

        self._last_range_m = None
        self._last_range_time = None

        self.create_subscription(Range, '/downward_lidar/range', self._on_range, 10)
        self.create_subscription(OpticalFlow, '/optical_flow/measurement', self._on_flow, 10)
        self.get_logger().info('Forwarding /optical_flow/measurement to EKF3 via OPTICAL_FLOW')

    def _on_range(self, msg: Range) -> None:
        self._last_range_m = msg.range
        self._last_range_time = self.get_clock().now()

    def _ground_distance_m(self) -> float:
        if self._last_range_m is None or self._last_range_time is None:
            return -1.0
        age_sec = (self.get_clock().now() - self._last_range_time).nanoseconds * 1e-9
        if age_sec > LIDAR_STALENESS_SEC:
            return -1.0
        return self._last_range_m

    def _on_flow(self, msg: OpticalFlow) -> None:
        if not msg.valid:
            return
        if not (math.isfinite(msg.flow_x_rad) and math.isfinite(msg.flow_y_rad)):
            return

        time_usec = (self.get_clock().now().nanoseconds - self._start_ns) // 1_000
        quality = min(max(round(msg.inlier_ratio * 255.0), 0), 255)

        # Best-derived axis/sign mapping - see module docstring. Verify via a
        # known-direction flight before trusting fused output.
        flow_rate_x = -msg.flow_x_rad
        flow_rate_y = msg.flow_y_rad

        self.master.mav.optical_flow_send(
            time_usec,
            0,          # sensor_id
            0,          # flow_x (deprecated, unused by AP_OpticalFlow_MAV)
            0,          # flow_y (deprecated, unused by AP_OpticalFlow_MAV)
            0.0,        # flow_comp_m_x (unused by AP_OpticalFlow_MAV)
            0.0,        # flow_comp_m_y (unused by AP_OpticalFlow_MAV)
            quality,
            self._ground_distance_m(),
            flow_rate_x,
            flow_rate_y,
        )

        self._msg_count += 1
        if self._msg_count == 1:
            self.get_logger().info(
                f'First OPTICAL_FLOW sent - flow_rate=({flow_rate_x:+.4f},{flow_rate_y:+.4f}) rad/s '
                f'quality={quality}'
            )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = FlowBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
