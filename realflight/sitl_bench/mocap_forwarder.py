#!/usr/bin/env python3
"""SITL ONLY (bench 2c): a simulated mocap feed for the real-hardware watcher.

/ground_truth/pose (geometry_msgs/PoseStamped, Gazebo ENU, body FLU) -> MCP1 UDP packets (realflight/mcp1.py), the
packet the watcher's UdpPoseSource reads. Runs under the ROS 2 (system) python:
  source /opt/ros/jazzy/setup.bash; PYTHONPATH=<thesis_ws> python3 -m realflight.sitl_bench.mocap_forwarder \
      --dest 127.0.0.1:9870 [--dest 127.0.0.1:9880] --ctl-port 9879 --log OUT/forwarder.csv

Each destination has its own fault state, changed at run time by a JSON datagram to --ctl-port:
  {"dest": 0, "mode": "normal" | "stop" | "freeze" | "untracked" | "static",
   "tracked": 1 | -1,                 # flag sent with fresh/frozen poses (-1 = a source without a tracking flag)
   "body_name": "...", "body_id": n,  # wrong-body injection
   "latency_s": 0.15,                 # added transport delay
   "frame_reset": true}               # restart the frame counter at 0 (one shot)
Modes: stop = send nothing; freeze = repeat the last pose bit-identically (new frame numbers); untracked = tracked 0
with the last pose (as NatNet does); static = a fixed pose (a still object at (1, 1, 0), level) under the configured
name. t_mocap = this host's wall clock when the ground-truth pose was RECEIVED (the stand-in for the mocap exposure
stamp). Every packet sent is logged.
"""
import argparse
import collections
import json
import socket
import time

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node

from realflight.mcp1 import encode


class Dest:
    def __init__(self, addr):
        self.addr = addr
        self.mode = "normal"
        self.tracked = 1
        self.body_name, self.body_id = "thesis_quad", 1
        self.latency = 0.0
        self.frame = 0
        self.last = None             # (pos, quat) last real pose
        self.frozen = None
        self.q = collections.deque()  # (t_due, bytes, logrow)


class Forwarder(Node):
    def __init__(self, a):
        super().__init__("wbench_mocap_forwarder")
        self.dests = [Dest((h, int(p))) for h, p in (d.rsplit(":", 1) for d in a.dest)]
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ctl = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ctl.bind(("127.0.0.1", a.ctl_port)); self.ctl.setblocking(False)
        self.log = open(a.log, "a", buffering=1)
        if self.log.tell() == 0:
            self.log.write("t_send_wall,dest,frame,t_mocap,mode,tracked,body,x,y,z\n")
        self.create_subscription(PoseStamped, "/ground_truth/pose", self.on_pose, 50)
        self.create_timer(0.005, self.service)

    def on_pose(self, m):
        t = time.time()
        p, q = m.pose.position, m.pose.orientation
        pose = ((p.x, p.y, p.z), (q.w, q.x, q.y, q.z))
        for i, d in enumerate(self.dests):
            d.last = pose
            if d.mode == "stop":
                continue
            if d.mode == "freeze":
                if d.frozen is None:
                    d.frozen = pose
                pos, quat, trk = d.frozen[0], d.frozen[1], d.tracked
            elif d.mode == "untracked":
                pos, quat, trk = pose[0], pose[1], 0
            elif d.mode == "static":
                pos, quat, trk = (1.0, 1.0, 0.0), (1.0, 0.0, 0.0, 0.0), d.tracked
            else:
                pos, quat, trk = pose[0], pose[1], d.tracked
            d.frame += 1
            pkt = encode(d.frame, t, d.body_id, d.body_name, trk, pos, quat)
            row = (i, d.frame, t, d.mode, trk, f"{d.body_name}#{d.body_id}", pos)
            d.q.append((t + d.latency, pkt, row))
        self.service()

    def service(self):
        while True:
            try:
                c = json.loads(self.ctl.recv(4096).decode())
            except (BlockingIOError, InterruptedError):
                break
            except ValueError:
                continue
            d = self.dests[int(c.get("dest", 0))]
            if "mode" in c:
                d.mode = c["mode"]
                if d.mode != "freeze":
                    d.frozen = None
            for k, attr in (("tracked", "tracked"), ("body_name", "body_name"), ("body_id", "body_id"),
                            ("latency_s", "latency")):
                if k in c:
                    setattr(d, attr, c[k])
            if c.get("frame_reset"):
                d.frame = 0
            self.get_logger().info(f"control {c} -> dest {c.get('dest', 0)}: mode {d.mode} tracked {d.tracked} "
                                   f"body {d.body_name}#{d.body_id} latency {d.latency}")
            self.log.write(f"{time.time():.4f},CTL,{json.dumps(c).replace(',', ';')},,,,,,,\n")
        now = time.time()
        for d in self.dests:
            while d.q and d.q[0][0] <= now:
                _, pkt, row = d.q.popleft()
                try:
                    self.sock.sendto(pkt, d.addr)
                except OSError:
                    pass
                i, fr, t, mode, trk, body, pos = row
                self.log.write(f"{time.time():.4f},{i},{fr},{t:.4f},{mode},{trk},{body},"
                               f"{pos[0]:.4f},{pos[1]:.4f},{pos[2]:.4f}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", action="append", required=True)
    ap.add_argument("--ctl-port", type=int, default=9879)
    ap.add_argument("--log", required=True)
    a = ap.parse_args()
    rclpy.init()
    n = Forwarder(a)
    try:
        rclpy.spin(n)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
