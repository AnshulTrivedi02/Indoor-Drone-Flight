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

Rate: requested via MAV_CMD_SET_MESSAGE_INTERVAL at a 3 ms interval - the
fastest ArduPilot permits at SCHED_LOOP_RATE=400 (see IMU_STREAM_INTERVAL_MS
below for the source-level reason). This was raised from an earlier 50 Hz,
which aliased: ~0.25 m/s^2 RMS of accel-z energy sits above the 25 Hz Nyquist
a 50 Hz stream implies (see CLAUDE.md, "IMU Aliasing"). Same
periodic-reassert pattern as attitude_bridge.py is retained as cheap
insurance, though the MAVProxy stream-clobbering it originally guarded
against no longer applies on this dedicated link.

Intended consumption: do NOT decimate this stream. The UKF accumulates
samples by elapsed time to >=12.5 ms and predicts on the accumulated total,
mirroring EKF3's own readIMUData()/CovariancePrediction() behaviour, so that
EKF3's *_NSE process-noise values transfer unchanged. GTSAM's preintegrated
IMU factor likewise consumes every sample between keyframes. Summing a*dt
over these instantaneous samples is rectangular integration and is NOT
identical to the true delta-angle/delta-velocity EKF3 gets from the INS
driver - an approximation, documented in CLAUDE.md.

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

Runs on port 14556, fed by a DEDICATED SITL serial output
(`arducopter --serial2=udpclient:127.0.0.1:14556`) rather than a MAVProxy
`--out` port. This is a deliberate departure from the pattern every other
bridge follows - fly_forward.py (14550), attitude_bridge.py (14551),
lidar_bridge.py (14552), flow_bridge.py (14553) and ekf_bridge.py (14554)
all take MAVProxy `--out` ports. Rationale and the note that it diverges
from the architecture brief are recorded in CLAUDE.md, "IMU Bridge -
dedicated SITL output (MAVProxy bypass)". run_trial.sh no longer passes
`--out 127.0.0.1:14555`.

Usage:
    source /opt/ros/jazzy/setup.bash
    source ~/venv-ardupilot/bin/activate
    python3 imu_bridge.py --ros-args -p use_sim_time:=true
"""

from pymavlink import mavutil

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Imu

# Dedicated SITL SERIAL2 UDP output (arducopter --serial2=udpclient:127.0.0.1:14556),
# NOT a MAVProxy --out port. This DEPARTS from the "every bridge owns a MAVLink UDP
# port via MAVProxy --out" pattern every other bridge follows - see CLAUDE.md,
# "IMU Bridge - dedicated SITL output (MAVProxy bypass)". The reason is headroom:
# at the rate below, MAVProxy would be relaying this stream to six outputs in
# single-threaded Python on top of everything else.
MAVLINK_PORT = 14556

# 3 ms is the FLOOR imposed by ArduPilot, not a preference. GCS_Common.cpp's
# cap_message_interval() enforces "no greater than 0.8 * SCHED_LOOP_RATE"; at
# SCHED_LOOP_RATE=400 the floor is 2500/800 = 3.125 ms, and set_message_interval()
# truncates microseconds to integer ms, so a 2 ms request is rejected outright
# ("Requested rate for message ID N too fast. Increase SCHED_LOOP_RATE").
# Raising SCHED_LOOP_RATE is NOT an option - it changes EKF3's own frame rate and
# INS sampling, i.e. the baseline being compared against.
#
# The rate is raised from the original 50 Hz because 50 Hz aliases: measured
# ~0.25 m/s^2 RMS of accel-z energy above the 25 Hz Nyquist (inferred from VIBE,
# which is computed on the 1000 Hz sensor stream). See CLAUDE.md, "IMU Aliasing".
IMU_STREAM_INTERVAL_MS = 3


class ImuBridge(Node):

    def __init__(self):
        super().__init__('imu_bridge')

        self._pub = self.create_publisher(Imu, '/imu/data_raw', 10)

        self.get_logger().info(f'Connecting to SITL on udpin:127.0.0.1:{MAVLINK_PORT} (dedicated SERIAL2, MAVProxy bypassed) ...')
        self.master = mavutil.mavlink_connection(f'udp:127.0.0.1:{MAVLINK_PORT}')
        self.master.wait_heartbeat()
        self.get_logger().info(
            f'Heartbeat received from system {self.master.target_system} '
            f'component {self.master.target_component}'
        )

        self._request_imu_stream()

        # Poll well above the stream rate; _poll() drains the socket in a loop, so
        # this only bounds added latency, not throughput. 1 kHz against a nominal
        # ~333 Hz stream.
        self._timer = self.create_timer(0.001, self._poll)

        # Same MAVProxy stream-rate-clobbering issue as attitude_bridge.py -
        # keep re-asserting ours so the effective rate doesn't decay.
        self._stream_request_timer = self.create_timer(2.0, self._request_imu_stream)

        self._msg_count = 0
        self.get_logger().info('Publishing to /imu/data_raw')

    def _request_imu_stream(self) -> None:
        """Ask the autopilot to send HIGHRES_IMU every IMU_STREAM_INTERVAL_MS."""
        interval_us = IMU_STREAM_INTERVAL_MS * 1000
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
