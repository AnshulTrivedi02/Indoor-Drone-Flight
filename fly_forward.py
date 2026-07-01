#!/usr/bin/env python3
"""Send a continuous forward velocity command to ArduPilot SITL via MAVLink.

Usage:
    python3 fly_forward.py [vx] [vy] [vz]

Defaults to vx=0.5 m/s forward. Ctrl+C to stop (sends zero velocity then lands).
Velocities are in the body-NED frame: vx=forward, vy=right, vz=down.
"""

import sys
import time
from pymavlink import mavutil

VX = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
VY = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
VZ = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0

# MAVProxy forwards to UDP 14550 by default
master = mavutil.mavlink_connection('udp:127.0.0.1:14550')
master.wait_heartbeat()
print(f"Connected — sending vx={VX} vy={VY} vz={VZ} m/s. Ctrl+C to stop.")

TYPE_MASK = 0b0000_1111_1100_0111  # use velocity only, ignore pos/accel/yaw

def send_velocity(vx, vy, vz):
    master.mav.set_position_target_local_ned_send(
        0,
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,
        TYPE_MASK,
        0, 0, 0,      # position (ignored)
        vx, vy, vz,   # velocity m/s
        0, 0, 0,      # acceleration (ignored)
        0, 0,         # yaw, yaw_rate (ignored)
    )

try:
    while True:
        send_velocity(VX, VY, VZ)
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nStopping — sending zero velocity.")
    for _ in range(10):
        send_velocity(0, 0, 0)
        time.sleep(0.05)
