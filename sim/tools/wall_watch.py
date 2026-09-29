#!/usr/bin/env python3
"""Ground-truth wall/crash watcher for closed-loop flights (METHODOLOGY "Closed loop").

ArduPilot's crash_check does not detect a wall scrape, and no EKF3 failsafe is meaningful
here, so contact is judged from Gazebo ground truth (/ground_truth/pose). Walls: 0.2 m thick,
centred at x = +-10 m, so the inner faces are at +-9.9 m; with the airframe's half-width,
contact is flagged at |x| >= 9.58 m. A crash is flagged when, after the vehicle has once been
above 1.5 m, it drops below 0.5 m before landing is expected (the caller passes --land-after-y),
or it tilts more than 60 deg. On a breach it writes BREACH.txt and SIGTERMs the given process
group (run_trial.sh), which stops the flight and flushes the bag. It logs min wall clearance,
max |x| and the GT track at 2 Hz.

Usage (system python, /opt/ros/jazzy sourced):
  python3 sim/tools/wall_watch.py OUT_DIR PGID [--land-after-y 150]
"""
import math, os, signal, sys, time, argparse
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped

WALL_X = 9.58

ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("pgid", type=int)
ap.add_argument("--land-after-y", type=float, default=150.0); a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)


class W(Node):
    def __init__(self):
        super().__init__("wall_watch")
        self.sub = self.create_subscription(PoseStamped, "/ground_truth/pose", self.cb, 50)
        self.max_abs_x = 0.0; self.was_high = False; self.done = False; self.last_log = 0.0
        self.track = open(os.path.join(a.out, "wall_watch_track.csv"), "w")
        self.track.write("t,x,y,z,tilt_deg\n")

    def breach(self, why, m):
        if self.done:
            return
        self.done = True
        p = m.pose.position
        with open(os.path.join(a.out, "BREACH.txt"), "w") as f:
            f.write(f"{why}\nt={m.header.stamp.sec + m.header.stamp.nanosec * 1e-9:.3f} x={p.x:.3f} y={p.y:.3f} z={p.z:.3f}\n")
        self.get_logger().error(f"BREACH: {why}; stopping the flight")
        try:
            os.killpg(a.pgid, signal.SIGTERM)
        except ProcessLookupError:
            pass

    def cb(self, m):
        p, q = m.pose.position, m.pose.orientation
        t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
        # tilt = angle between body z and world z
        bz = 1 - 2 * (q.x * q.x + q.y * q.y)
        tilt = math.degrees(math.acos(max(-1.0, min(1.0, bz))))
        self.max_abs_x = max(self.max_abs_x, abs(p.x))
        if p.z > 1.5:
            self.was_high = True
        if t - self.last_log >= 0.5:
            self.track.write(f"{t:.3f},{p.x:.4f},{p.y:.4f},{p.z:.4f},{tilt:.2f}\n"); self.track.flush(); self.last_log = t
            with open(os.path.join(a.out, "wall_watch_summary.txt"), "w") as f:
                f.write(f"max_abs_x={self.max_abs_x:.4f}\nmin_clearance_to_{WALL_X}={WALL_X - self.max_abs_x:.4f}\n")
        if abs(p.x) >= WALL_X:
            self.breach(f"wall contact: |x| = {abs(p.x):.3f} m >= {WALL_X}", m)
        elif tilt > 60:
            self.breach(f"crash: tilt {tilt:.1f} deg > 60", m)
        elif self.was_high and p.z < 0.5 and p.y < a.land_after_y:
            self.breach(f"crash: height {p.z:.2f} m < 0.5 m before the landing point", m)


rclpy.init(); n = W()
try:
    rclpy.spin(n)
except KeyboardInterrupt:
    pass
