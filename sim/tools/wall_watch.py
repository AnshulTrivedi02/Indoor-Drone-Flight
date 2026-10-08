#!/usr/bin/env python3
"""Ground-truth wall/crash watcher for closed-loop flights (METHODOLOGY "Closed loop").

ArduPilot's crash_check does not detect a wall scrape, and no EKF3 failsafe is meaningful
here, so contact is judged from Gazebo ground truth (/ground_truth/pose). Walls: 0.2 m thick,
centred at x = +-10 m, so the inner faces are at +-9.9 m; with the airframe's half-width,
contact is flagged at |x| >= 9.58 m. A crash is flagged when, after the vehicle has once been
above 1.5 m, it drops below 0.5 m before landing is expected (--land-after-y), or it tilts
more than 60 deg.

Stopping (rewritten 2026-09-29 after cl_ekf3_tex). The first version SIGTERMed run_trial.sh's
whole process group. That also killed the `tee` run_trial logs through, so run_trial died of
SIGPIPE (exit 141) inside its cleanup trap and left Gazebo, MAVProxy, the bridges and the bag
recorder running (each is setsid'd into its own group). The launcher then killed the watcher,
which is the rclpy ExternalShutdownException seen. Now, on a breach:
  1. SIGTERM fly_trial.py and run_trial.sh by PID only (bash defers its trap until the
     foreground fly_trial pipeline ends, so fly_trial must go too). tee survives and
     run_trial's own cleanup stops the recorder (bag flushed, metadata.yaml written) and the sim.
  2. If run_trial is still alive after STOP_GRACE_S, SIGTERM its process group.
  3. Once run_trial has exited, any leftover sim process is stopped: the bag recorder first
     (SIGTERM, which flushes it), then the rest (SIGTERM, then SIGKILL).
The watcher keeps logging ground truth throughout, ignores SIGINT/SIGTERM sent to itself, and
exits only when run_trial has exited and no sim process remains (breach or not). Every action
goes to STOP_LOG.txt. max |x| (and so min clearance) is tracked on every message, not the 2 Hz log.

Usage (system python, /opt/ros/jazzy sourced):
  python3 sim/tools/wall_watch.py OUT_DIR RUN_TRIAL_PID [--land-after-y 150]
"""
import argparse, math, os, signal, subprocess, time
import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from rclpy.signals import SignalHandlerOptions
from geometry_msgs.msg import PoseStamped

WALL_X = 9.58
STOP_GRACE_S = 90.0          # run_trial's cleanup waits up to 10 s for the recorder, then kills
LEFTOVER = ["ros2 bag record", "gz sim -v4 -s", "build/sitl/bin/arducopter", "mavproxy.py --daemon",
            "parameter_bridge", "flow_tracker", "ground_truth_pub.py", "attitude_bridge.py",
            "lidar_bridge.py", "flow_bridge.py", "ekf_bridge.py", "imu_bridge.py"]

ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("rt_pid", type=int)
ap.add_argument("--land-after-y", type=float, default=150.0)
ap.add_argument("--box", help="experiment H (room): 'xmin,xmax,ymin,ymax' of GT (world) allowed; outside = breach "
                "(gate G5: >= 0.5 m from every wall). Replaces the corridor wall rule and the corridor crash-height rule; "
                "the tilt rule stays")
ap.add_argument("--watch-process", help="pgrep -f pattern of a process the flight depends on (e.g. heading_bridge.py); "
                "if it dies while run_trial runs and the vehicle is airborne, the flight is stopped")
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)


def alive(pid):
    try:
        os.kill(pid, 0); return True
    except ProcessLookupError:
        return False


def pids(pattern):
    r = subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True)
    return [int(p) for p in r.stdout.split() if int(p) != os.getpid()]


class W(Node):
    def __init__(self):
        super().__init__("wall_watch")
        self.sub = self.create_subscription(PoseStamped, "/ground_truth/pose", self.cb, 50)
        self.timer = self.create_timer(1.0, self.tick)
        self.max_abs_x = 0.0; self.at = None; self.was_high = False; self.last_log = 0.0
        self.breached = False; self.t_stop = None; self.escalated = False; self.leftover_t = None
        self.finished = False
        self.z = 0.0; self.dep_seen = False; self.dep_dead = False
        self.track = open(os.path.join(a.out, "wall_watch_track.csv"), "w")
        self.track.write("t,x,y,z,tilt_deg\n")
        self.slog = open(os.path.join(a.out, "STOP_LOG.txt"), "a")

    def note(self, s):
        self.slog.write(f"{time.strftime('%H:%M:%S')} {s}\n"); self.slog.flush()
        self.get_logger().warn(s)

    def summary(self):
        with open(os.path.join(a.out, "wall_watch_summary.txt"), "w") as f:
            f.write(f"max_abs_x={self.max_abs_x:.4f}\nmin_clearance_to_{WALL_X}={WALL_X - self.max_abs_x:.4f}\n")
            if self.at:
                f.write(f"max_abs_x_at t={self.at[0]:.3f} x={self.at[1]:.3f} y={self.at[2]:.3f} z={self.at[3]:.3f}\n")

    def breach(self, why, m):
        if self.breached:
            return
        self.breached = True
        p = m.pose.position
        with open(os.path.join(a.out, "BREACH.txt"), "w") as f:
            f.write(f"{why}\nt={m.header.stamp.sec + m.header.stamp.nanosec * 1e-9:.3f} x={p.x:.3f} y={p.y:.3f} z={p.z:.3f}\n")
        self.note(f"BREACH: {why}; stopping the flight")
        for pid in pids("thesis_ws/fly_trial.py"):
            os.kill(pid, signal.SIGTERM); self.note(f"SIGTERM fly_trial.py pid {pid}")
        if alive(a.rt_pid):
            os.kill(a.rt_pid, signal.SIGTERM); self.note(f"SIGTERM run_trial.sh pid {a.rt_pid}")
        self.t_stop = time.monotonic()

    def cb(self, m):
        p, q = m.pose.position, m.pose.orientation
        t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
        bz = 1 - 2 * (q.x * q.x + q.y * q.y)                     # tilt = angle(body z, world z)
        tilt = math.degrees(math.acos(max(-1.0, min(1.0, bz))))
        if abs(p.x) > self.max_abs_x:
            self.max_abs_x = abs(p.x); self.at = (t, p.x, p.y, p.z)
        self.z = p.z; self._last_msg = m
        if p.z > 1.5:
            self.was_high = True
        if t - self.last_log >= 0.5:
            self.track.write(f"{t:.3f},{p.x:.4f},{p.y:.4f},{p.z:.4f},{tilt:.2f}\n"); self.track.flush()
            self.last_log = t; self.summary()
        if a.box:
            x0, x1, y0, y1 = (float(v) for v in a.box.split(","))
            if not (x0 <= p.x <= x1 and y0 <= p.y <= y1):
                self.breach(f"room box left: x {p.x:.3f} y {p.y:.3f} outside [{x0},{x1}] x [{y0},{y1}]", m)
            elif tilt > 60:
                self.breach(f"crash: tilt {tilt:.1f} deg > 60", m)
            return
        if abs(p.x) >= WALL_X:
            self.breach(f"wall contact: |x| = {abs(p.x):.3f} m >= {WALL_X}", m)
        elif tilt > 60:
            self.breach(f"crash: tilt {tilt:.1f} deg > 60", m)
        elif self.was_high and p.z < 0.5 and p.y < a.land_after_y:
            self.breach(f"crash: height {p.z:.2f} m < 0.5 m before the landing point", m)

    def heartbeat(self):
        """Fail-closed contract (ruling 2026-10-08): <out>/watch_heartbeat = '<wall time> box=<0|1> bridge=<0|1>', every
        tick. fly_trial (WATCH_HEARTBEAT) refuses to arm without a fresh heartbeat with both flags 1, and lands if it
        goes stale (> 3 s) or a flag drops in flight. box=1: the room-box rule is active; bridge=1: the watched process
        is running (1 when no process is watched)."""
        box = 1 if a.box else 0
        bridge = 1 if (not a.watch_process or bool(pids(a.watch_process))) else 0
        if self.breached:
            box = 0                      # a breach withdraws the confirmation: fly_trial lands
        tmp = os.path.join(a.out, "watch_heartbeat.tmp")
        with open(tmp, "w") as f:
            f.write(f"{time.time():.3f} box={box} bridge={bridge}\n")
        os.replace(tmp, os.path.join(a.out, "watch_heartbeat"))

    def tick(self):
        self.heartbeat()
        # Safeguard (closed-loop Part 1): a dependency (the heading node) dying mid-flight stops
        # the flight. The wall/crash checks above never depend on it.
        if a.watch_process and alive(a.rt_pid) and not self.breached:
            up = bool(pids(a.watch_process))
            if up:
                self.dep_seen = True
            elif self.dep_seen and not self.dep_dead:
                self.dep_dead = True
                self.note(f"watched process '{a.watch_process}' died (vehicle z = {self.z:.2f} m)")
                if self.z > 0.5 and getattr(self, "_last_msg", None) is not None:
                    self.breach(f"dependency died in flight: {a.watch_process}", self._last_msg)
        if alive(a.rt_pid):
            if self.breached and not self.escalated and time.monotonic() - self.t_stop > STOP_GRACE_S:
                self.escalated = True
                try:
                    os.killpg(os.getpgid(a.rt_pid), signal.SIGTERM)
                    self.note(f"run_trial still alive after {STOP_GRACE_S:.0f} s: SIGTERM its process group")
                except ProcessLookupError:
                    pass
            return
        left = {pat: pids(pat) for pat in LEFTOVER}
        left = {k: v for k, v in left.items() if v}
        if not left:
            self.summary(); self.note("run_trial exited and no sim process remains; watcher done")
            self.finished = True
            return
        if self.leftover_t is None:                                # first sighting: recorder first
            self.leftover_t = time.monotonic()
            self.note(f"run_trial exited with leftovers: {sorted(left)}")
            for pid in left.get("ros2 bag record", []):
                os.kill(pid, signal.SIGTERM); self.note(f"SIGTERM bag recorder pid {pid}")
            return
        dt = time.monotonic() - self.leftover_t
        if dt > 15 and not left.get("ros2 bag record") or dt > 30:
            sig = signal.SIGTERM if dt < 40 else signal.SIGKILL
            for pat, ps in left.items():
                for pid in ps:
                    try:
                        os.kill(pid, sig)
                    except ProcessLookupError:
                        pass
                self.note(f"{sig.name} {pat} {ps}")


def ignore(signum, _):
    n.note(f"watcher received signal {signum}: ignored until the flight is fully stopped")


rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
n = W()
signal.signal(signal.SIGINT, ignore); signal.signal(signal.SIGTERM, ignore)
try:
    while rclpy.ok() and not n.finished:
        rclpy.spin_once(n, timeout_sec=0.5)
except ExternalShutdownException:
    n.note("rclpy context shut down externally; flight stop state may be incomplete")
finally:
    n.summary()
    n.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()
