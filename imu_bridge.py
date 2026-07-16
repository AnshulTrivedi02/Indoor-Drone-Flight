#!/usr/bin/env python3
"""
Bridge ArduPilot SITL's accelerometer + gyro onto ROS2 as sensor_msgs/Imu.

This is the accelerometer input the UKF's (and later the FGO's) process
model needs and that no existing bridge provides — see CLAUDE.md, "Sensor
Fusion Architecture" / UKF design report: without sensed specific force,
roll and pitch are not observable at all (only gyro-integrable, open-loop),
which corrupts the flow measurement model's world->body velocity rotation
over exactly the long GNSS-denied flights this project's trial harness was
built to run.

Message choice: MAVLink HIGHRES_IMU (100, not RAW_IMU/SCALED_IMU). Read
directly from ArduPilot's own sender (GCS_Common.cpp,
GCS_MAVLINK::send_highres_imu) rather than assumed: it populates
xacc/yacc/zacc and xgyro/ygyro/zgyro straight from AP_InertialSensor's
calibrated get_accel()/get_gyro() as float32 SI units (m/s^2, rad/s) - no
scale factor and no int16 round-trip, unlike RAW_IMU (milli-g int16,
needs *GRAVITY_MSS/1000) or SCALED_IMU (same milli-g int16 encoding).
Confirmed compiled into this SITL build:
AP_MAVLINK_MSG_HIGHRES_IMU_ENABLED = (HAL_PROGRAM_SIZE_LIMIT_KB > 1024) &&
AP_INERTIALSENSOR_ENABLED (GCS_MAVLink/GCS_config.h) - trivially true for
SITL/Copter.

Specific force, not gravity-subtracted acceleration: AP_InertialSensor's
get_accel() is the calibrated raw accelerometer reading, exactly as any
strapdown IMU outputs it - gravity compensation only happens later, inside
an EKF's own state propagation. At level rest this reads ~+9.8 m/s^2
"upward" once rotated into ENU/FLU below (the classic "accelerometer reads
+1g sitting on a table" result) - verified empirically against a recorded
hover trial, not just asserted, see CLAUDE.md.

Rate: requested via MAV_CMD_SET_MESSAGE_INTERVAL at 50 Hz, matching
attitude_bridge.py's ATTITUDE rate (a UKF/FGO prediction step needs this
much faster than ArduPilot's own low telemetry defaults) - same
periodic-reassert pattern as attitude_bridge.py, since MAVProxy silently
re-issues its own low-rate stream request otherwise (see CLAUDE.md, Known
Issues).

Frame: HIGHRES_IMU's xacc/yacc/zacc and xgyro/ygyro/zgyro are FRD body
frame (X-forward, Y-right, Z-down), exactly like MAVLink ATTITUDE's
rollspeed/pitchspeed/yawspeed. Rotated into Gazebo/ROS FLU body
(X-forward, Y-left, Z-up) with (x, -y, -z) - the same
already-empirically-validated 180-degree-about-X FRD<->FLU convention
flow_tracker.py uses for gyro rates (confirmed against imu_link's 180 deg
roll SDF pose), reused verbatim here since it is a proper rotation and
applies identically to any body-frame vector, not just angular rate.

angular_velocity here is a second copy of body rates, deliberately
re-sourced from this same HIGHRES_IMU message (not /attitude/angular_rates,
which comes from a separately-polled MAVLink ATTITUDE message) so that
gyro and accel share the exact same underlying IMU sample and timestamp -
important for a UKF predict step and for GTSAM's preintegrated IMU factor,
which wants co-sampled accel/gyro pairs. flow_tracker.py's derotation is
unaffected and keeps using /attitude/angular_rates as before.

orientation is not provided (no attitude estimate is computed here) -
orientation_covariance[0] = -1 per REP-145. angular_velocity_covariance
and linear_acceleration_covariance are left at all-zero (valid data,
covariance unknown), also per REP-145.

Runs on a dedicated MAVLink UDP port (14555), separate from
fly_forward.py (14550), attitude_bridge.py (14551), lidar_bridge.py
(14552), flow_bridge.py (14553) and ekf_bridge.py (14554).
sim_vehicle.py / run_trial.sh must be launched with an extra
`--out 127.0.0.1:14555` for this connection to receive traffic.

Usage:
    source /opt/ros/jazzy/setup.bash
    source ~/venv-ardupilot/bin/activate
    python3 imu_bridge.py --ros-args -p use_sim_time:=true
"""

from pymavlink import mavutil

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Imu

MAVLINK_PORT = 14555
IMU_STREAM_RATE_HZ = 50


class ImuBridge(Node):

    def __init__(self):
        super().__init__('imu_bridge')

        self._pub = self.create_publisher(Imu, '/imu/data_raw', 10)

        self.get_logger().info(f'Connecting to SITL on udp:127.0.0.1:{MAVLINK_PORT} ...')
        self.master = mavutil.mavlink_connection(f'udp:127.0.0.1:{MAVLINK_PORT}')
        self.master.wait_heartbeat()
        self.get_logger().info(
            f'Heartbeat received from system {self.master.target_system} '
            f'component {self.master.target_component}'
        )

        self._request_imu_stream()

        # Poll for MAVLink messages faster than the requested HIGHRES_IMU rate.
        self._timer = self.create_timer(1.0 / (IMU_STREAM_RATE_HZ * 2), self._poll)

        # Same MAVProxy stream-rate-clobbering issue as attitude_bridge.py -
        # keep re-asserting ours so the effective rate doesn't decay.
        self._stream_request_timer = self.create_timer(2.0, self._request_imu_stream)

        self._msg_count = 0
        self.get_logger().info('Publishing to /imu/data_raw')

    def _request_imu_stream(self) -> None:
        """Ask the autopilot to send HIGHRES_IMU at IMU_STREAM_RATE_HZ."""
        interval_us = int(1e6 / IMU_STREAM_RATE_HZ)
        self.master.mav.command_long_send(
            self.master.target_system,
            self.master.target_component,
            mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,
            0,
            mavutil.mavlink.MAVLINK_MSG_ID_HIGHRES_IMU,
            interval_us,
            0, 0, 0, 0, 0,
        )

    def _poll(self) -> None:
        while True:
            msg = self.master.recv_match(type='HIGHRES_IMU', blocking=False)
            if msg is None:
                break
            self._publish(msg)

    def _publish(self, msg) -> None:
        out = Imu()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = 'base_link_flu'

        # No orientation estimate provided - REP-145.
        out.orientation_covariance[0] = -1.0

        # FRD -> FLU, same convention as flow_tracker.py's gyro handling.
        out.angular_velocity.x = float(msg.xgyro)
        out.angular_velocity.y = float(-msg.ygyro)
        out.angular_velocity.z = float(-msg.zgyro)

        out.linear_acceleration.x = float(msg.xacc)
        out.linear_acceleration.y = float(-msg.yacc)
        out.linear_acceleration.z = float(-msg.zacc)

        self._pub.publish(out)

        self._msg_count += 1
        if self._msg_count == 1:
            self.get_logger().info(
                f'First HIGHRES_IMU received - accel(FLU)='
                f'({out.linear_acceleration.x:+.3f},{out.linear_acceleration.y:+.3f},'
                f'{out.linear_acceleration.z:+.3f}) m/s^2  '
                f'gyro(FLU)=({out.angular_velocity.x:+.3f},{out.angular_velocity.y:+.3f},'
                f'{out.angular_velocity.z:+.3f}) rad/s'
            )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = ImuBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
