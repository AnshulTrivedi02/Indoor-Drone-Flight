#!/usr/bin/env python3
"""Save one frame from each given ROS2 image topic to PNG (live render check).

The first frame seen on each topic is discarded (it can predate a teleport); the
next frame with a later stamp is saved.

Usage (system python, /opt/ros/jazzy sourced):
  python3 sim/tools/grab_frames.py OUT_DIR /forward_camera/image /downward_camera/image
"""
import os, sys
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from PIL import Image as PImage


def to_array(m):
    ch = {"mono8": 1, "rgb8": 3, "bgr8": 3}[m.encoding]
    a = np.frombuffer(bytes(m.data), np.uint8).reshape(m.height, m.step)[:, :m.width * ch]
    a = a.reshape(m.height, m.width, ch) if ch > 1 else a
    return a[..., ::-1] if m.encoding == "bgr8" else a


class Grab(Node):
    def __init__(self, out, topics):
        super().__init__("grab_frames")
        self.out, self.left, self.first = out, set(topics), {}
        for t in topics:
            self.create_subscription(Image, t, lambda m, t=t: self.cb(t, m), 1)

    def cb(self, topic, m):
        if topic not in self.left:
            return
        st = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
        if topic not in self.first:          # skip the first (possibly stale) frame; keep
            self.first[topic] = st           # the next one rendered after it
            return
        if st <= self.first[topic]:
            return
        name = topic.strip("/").replace("/", "_") + ".png"
        PImage.fromarray(to_array(m)).save(os.path.join(self.out, name))
        print(f"{topic}: {m.width}x{m.height} {m.encoding} stamp {m.header.stamp.sec}.{m.header.stamp.nanosec:09d} -> {name}")
        self.left.discard(topic)


if __name__ == "__main__":
    out, topics = sys.argv[1], sys.argv[2:]
    os.makedirs(out, exist_ok=True)
    rclpy.init()
    n = Grab(out, topics)
    while rclpy.ok() and n.left:
        rclpy.spin_once(n, timeout_sec=1.0)
    rclpy.shutdown()
