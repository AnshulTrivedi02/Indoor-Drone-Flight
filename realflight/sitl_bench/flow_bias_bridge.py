#!/usr/bin/env python3
"""SITL ONLY (wbench5_m2r, the re-registered M2-R; handover docs/handovers/2026-10-12_m2r_rerun.md §1): flow_bridge.py
with a controllable, logged velocity-equivalent BIAS on ONE flow axis, for the stimulus "corrupt flow on the final
descent" (the stored persistent runaway, wbench4_hoverB_173841 BIN 49, had accepted wild near-floor flow).

In "pass" mode (the default, and the state at start) every message is exactly what flow_bridge.py sends: this class
subclasses flow_bridge.FlowBridge and calls its _on_flow unchanged. In "bias" mode the flow_rate_y sent to the FC is
  flow_rate_y + b,   b = v_b(t) / r,   v_b(t) = v * min(1, (t - t0) / ramp_s),   r = rng - 0.13 m
(r: the camera's height above the floor from the LiDAR range; the camera is 0.13 m below the LiDAR, 0.25 vs 0.12 m
below base_link). So EKF3, which predicts flow as v_body / r, is shown a body velocity v_b too large on one axis,
whatever the height. flow_rate_x is never biased (the other axis stays accepted: the F8 persistence mechanism, F8
handover §2.4). When |b| would exceed `max_rad` (default 2.0 rad/s, under FLOW_MAX 2.5) or r <= 0.05 or the range is
stale, the bias is CUT: the mode latches back to "pass" (real flow resumes; no artificial dropout).

Control: JSON datagrams to UDP 127.0.0.1:<ctl-port>: {"mode": "pass"} or
{"mode": "bias", "v": 1.0, "ramp_s": 1.0, "max_rad": 2.0}. Every OPTICAL_FLOW sent is logged to --log (CSV):
t_wall, mode, rng, r, raw_x, raw_y, bias_y, sent_x, sent_y, quality; mode changes are logged as "#" lines.
"""
import argparse
import json
import socket
import sys
import time

CAM_BELOW_LIDAR_M = 0.13


def bias_rad(v, ramp_s, t0, now, rng, max_rad):
    """The velocity-equivalent bias in rad/s, or None (= cut: revert to pass) if it cannot be applied."""
    if rng is None or rng <= 0:
        return None
    r = rng - CAM_BELOW_LIDAR_M
    if r <= 0.05:
        return None
    vb = v * (1.0 if ramp_s <= 0 else min(1.0, max(0.0, (now - t0) / ramp_s)))
    b = vb / r
    if abs(b) > max_rad:
        return None
    return b


class _Wrap:
    """Captures the arguments of optical_flow_send so that the bias can be applied to the very message the parent
    builds (the parent's code path, fields and order are untouched)."""

    def __init__(self, real, owner):
        self.real, self.owner = real, owner

    def optical_flow_send(self, time_usec, sensor_id, fx, fy, cmx, cmy, quality, gd, rate_x, rate_y):
        o = self.owner
        o.poll_ctl()
        now = time.time()
        b = 0.0
        if o.mode == "bias":
            bb = bias_rad(o.v, o.ramp_s, o.t0, now, gd, o.max_rad)
            if bb is None:
                o.set_mode("pass", why=f"cut (rng {gd:.3f}, v {o.v}, max {o.max_rad} rad/s)")
            else:
                b = bb
        sy = rate_y + b
        o.csv.write(f"{now:.4f},{o.mode},{gd:.3f},{gd - CAM_BELOW_LIDAR_M:.3f},{rate_x:.5f},{rate_y:.5f},{b:.5f},"
                    f"{rate_x:.5f},{sy:.5f},{quality}\n")
        return self.real.optical_flow_send(time_usec, sensor_id, fx, fy, cmx, cmy, quality, gd, rate_x, sy)

    def __getattr__(self, k):
        return getattr(self.real, k)


def make_node(ctl_port, log):
    """Import the ROS side only here (the bias maths above is unit-tested without ROS)."""
    import flow_bridge as fb
    return type("BiasBridge", (_BiasMixin, fb.FlowBridge), {})(ctl_port, log)


class _BiasMixin:
    def __init__(self, ctl_port, log):
        super().__init__()
        self.mode, self.v, self.ramp_s, self.max_rad, self.t0 = "pass", 0.0, 1.0, 2.0, 0.0
        self.csv = open(log, "a", buffering=1)
        self.csv.write("t_wall,mode,rng,r,raw_x,raw_y,bias_y,sent_x,sent_y,quality\n")
        self.ctl = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ctl.bind(("127.0.0.1", ctl_port))
        self.ctl.setblocking(False)
        self.master.mav = _Wrap(self.master.mav, self)
        self.create_timer(0.05, self.poll_ctl)

    def set_mode(self, mode, why=""):
        self.mode = mode
        self.csv.write(f"# {time.time():.4f} mode {mode} v={self.v} ramp_s={self.ramp_s} max_rad={self.max_rad} "
                       f"{why}\n")

    def poll_ctl(self):
        while True:
            try:
                d, _ = self.ctl.recvfrom(4096)
            except (BlockingIOError, OSError):
                return
            try:
                c = json.loads(d.decode())
            except ValueError:
                continue
            if c.get("mode") == "bias":
                self.v = float(c.get("v", 1.0)); self.ramp_s = float(c.get("ramp_s", 1.0))
                self.max_rad = float(c.get("max_rad", 2.0)); self.t0 = time.time()
                self.set_mode("bias", why="command")
            else:
                self.set_mode("pass", why="command")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ctl-port", type=int, required=True)
    ap.add_argument("--log", required=True)
    a, rest = ap.parse_known_args()
    import rclpy
    rclpy.init(args=[sys.argv[0]] + rest)
    node = make_node(a.ctl_port, a.log)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
