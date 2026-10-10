#!/usr/bin/env python3
"""Pi-side liveness sidecars (G7): send beacons to the watcher for a process that is not (yet) beacon-instrumented.

  proc   python3 -m realflight.watcher.sidecars proc --name flow_bridge --pattern flow_bridge.py --to HOST:PORT
         Beacons only while exactly-matching process(es) exist and none is in state T (stopped/traced), t (tracing
         stop), Z (zombie) or X (dead). Catches death and SIGSTOP. It cannot see a hang inside a running process;
         use the topic sidecar (or in-process beacons) for that.
  topic  python3 -m realflight.watcher.sidecars topic --name flow_tracker --topic /optical_flow/measurement
             --type optical_flow_interfaces/msg/OpticalFlow --to HOST:PORT
         Needs rclpy (source ROS 2). progress = number of messages seen on the process's OUTPUT topic, so a hung
         process stops the counter and the watcher's progress check fires.

Both beacon at 5 Hz. If the sidecar itself dies, the beacon stops: fail-closed.
"""
import argparse
import os
import time

from realflight.watcher.liveness import LivenessBeacon

BAD_STATES = set("TtZXx")


def proc_state(pid):
    """Single-letter state from /proc/<pid>/stat, or None if gone."""
    try:
        with open(f"/proc/{pid}/stat") as f:
            s = f.read()
    except OSError:
        return None
    return s[s.rindex(")") + 2]


def find_pids(pattern):
    """Like `pgrep -f pattern` (substring of the full command line), excluding this process. Local to the Pi."""
    me = os.getpid()
    out = []
    for d in os.listdir("/proc"):
        if not d.isdigit() or int(d) == me:
            continue
        try:
            with open(f"/proc/{d}/cmdline", "rb") as f:
                cmd = f.read().replace(b"\0", b" ").decode(errors="replace")
        except OSError:
            continue
        if pattern in cmd and "realflight.watcher.sidecars" not in cmd:
            out.append(int(d))
    return out


class ProcSidecar:
    def __init__(self, name, addr, pattern=None, pid=None):
        self.beacon = LivenessBeacon(name, addr)
        self.pattern, self.pid = pattern, pid

    def healthy(self):
        pids = [self.pid] if self.pid else find_pids(self.pattern)
        if not pids:
            return False, "no process"
        states = {p: proc_state(p) for p in pids}
        bad = {p: s for p, s in states.items() if s is None or s in BAD_STATES}
        return (not bad), (f"bad state {bad}" if bad else "ok")

    def step(self):
        ok, _ = self.healthy()
        if ok:
            self.beacon.beat(None)
        return ok


class TopicRateCore:
    """rclpy-free core of the topic sidecar: count messages, beacon with the count as progress."""

    def __init__(self, name, addr):
        self.beacon = LivenessBeacon(name, addr)
        self.count = 0

    def on_msg(self, _msg=None):
        self.count += 1

    def step(self):
        self.beacon.beat(self.count)


def _parse_addr(s):
    h, p = s.rsplit(":", 1)
    return h, int(p)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="kind", required=True)
    p1 = sub.add_parser("proc"); p1.add_argument("--name", required=True); p1.add_argument("--to", required=True)
    g = p1.add_mutually_exclusive_group(required=True); g.add_argument("--pattern"); g.add_argument("--pid", type=int)
    p2 = sub.add_parser("topic"); p2.add_argument("--name", required=True); p2.add_argument("--to", required=True)
    p2.add_argument("--topic", required=True); p2.add_argument("--type", required=True)
    for p in (p1, p2):
        p.add_argument("--period", type=float, default=0.2)
    a = ap.parse_args(argv)
    addr = _parse_addr(a.to)
    if a.kind == "proc":
        sc = ProcSidecar(a.name, addr, pattern=a.pattern, pid=a.pid)
        while True:
            sc.step(); time.sleep(a.period)
    import importlib
    import rclpy
    from rclpy.node import Node
    pkg, _, typ = a.type.split("/")
    msg_t = getattr(importlib.import_module(f"{pkg}.msg"), typ)
    core = TopicRateCore(a.name, addr)
    rclpy.init()
    node = Node(f"liveness_{a.name}")
    node.create_subscription(msg_t, a.topic, core.on_msg, 50)
    node.create_timer(a.period, core.step)
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node(); rclpy.shutdown()


if __name__ == "__main__":
    main()
