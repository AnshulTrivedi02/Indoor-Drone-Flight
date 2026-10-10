"""Mocap input interface (G1) and the one concrete adapter: a UDP pose packet.

WHAT THE REAL MOCAP SYSTEM MUST PROVIDE (the system is not yet known; supervisor input U7):
  - rate:      >= 50 Hz per rigid body (100-240 Hz typical). The stale limit is 0.5 s, so 50 Hz leaves 25 frames of
               margin; below ~20 Hz the 0.1 s breach-latency target of B4 cannot be met.
  - frame:     a fixed, right-handed world frame, z-up or y-up (--up-axis), metres, quaternion orientation. The box is
               defined in the converted z-up "watch frame" (frames.py). The rigid body's local axes must be FLU once
               converted, or corrected with --body-yaw-offset-deg (checked at B6).
  - identity:  a rigid-body name and/or numeric ID per pose, stable for the session (G3, B6).
  - tracking:  ideally a per-frame "tracked/valid" flag (NatNet's tracking-valid bit; Vicon's occluded flag). If the
               system only repeats the last pose when it loses the body (VRPN does this), set tracked = -1 and the
               watcher falls back to "bit-identical pose for >= 0.5 s = stale" (B5b; state which applies).
  - frame number and a mocap timestamp per frame (for duplicate rejection and the B7a latency measurement; the mocap PC
               and the ground station are synced by chrony/PTP).
  - latency:   mocap exposure -> watcher receipt median <= 50 ms, p99 <= 100 ms (B7a).

WHY A UDP PACKET (and not a ROS 2 PoseStamped subscription) for the concrete adapter:
  - VRPN/NatNet -> ROS 2 PoseStamped drops exactly the fields the safety checks need: the tracking flag, the body ID
    (only implicit in the topic name) and the mocap frame number.
  - The safety loop does not depend on the ROS 2 graph (DDS discovery, QoS, the same middleware the Pi pipeline
    uses), so a ROS fault cannot blind the watcher silently.
  - It is testable offline with plain sockets.
  The cost: a small forwarder from the vendor SDK (NatNet SDK, Vicon DataStream SDK, or a VRPN client) to this packet
  is needed once the system is known. Any forwarder fault stops the packets, which the stale check catches
  (fail-closed). If a ROS 2 driver is preferred, `pose_stamped_to_sample` below converts a PoseStamped (the
  adapter is swappable; any PoseSource works).

Packet (little-endian, 93 bytes), struct '<4sIdI16sb7d':
  magic b'MCP1' | frame_no u32 | t_mocap f64 (s, mocap clock) | body_id u32 | body_name 16 bytes (NUL-padded ASCII)
  | tracked i8 (1 tracked, 0 NOT tracked, -1 unknown/not provided) | px py pz f64 | qw qx qy qz f64
"""
import socket
import struct
import time
from dataclasses import dataclass
from typing import List, Optional

PACKET = struct.Struct("<4sIdI16sb7d")
MAGIC = b"MCP1"


@dataclass
class MocapSample:
    frame_no: int
    t_mocap: float          # mocap clock (s)
    t_rx: float             # receipt, watcher monotonic clock (s)
    body_id: int
    body_name: str
    tracked: int            # 1, 0, or -1 (unknown)
    pos: tuple              # mocap frame (m)
    quat: tuple             # (w, x, y, z), mocap frame
    t_rx_wall: float = 0.0  # receipt, wall clock (for the B7a latency log)


def encode(frame_no, t_mocap, body_id, body_name, tracked, pos, quat) -> bytes:
    return PACKET.pack(MAGIC, frame_no, t_mocap, body_id, body_name.encode()[:16], tracked, *pos, *quat)


def decode(data: bytes, t_rx: float, t_rx_wall: float = 0.0) -> Optional[MocapSample]:
    if len(data) != PACKET.size:
        return None
    f = PACKET.unpack(data)
    if f[0] != MAGIC:
        return None
    return MocapSample(frame_no=f[1], t_mocap=f[2], t_rx=t_rx, body_id=f[3],
                       body_name=f[4].rstrip(b"\0").decode(errors="replace"), tracked=f[5],
                       pos=tuple(f[6:9]), quat=tuple(f[9:13]), t_rx_wall=t_rx_wall)


class PoseSource:
    """Interface. poll() returns the samples received since the last call (non-blocking); fileno() for select()."""

    def poll(self) -> List[MocapSample]:
        raise NotImplementedError

    def fileno(self) -> int:
        raise NotImplementedError

    def close(self):
        pass


class UdpPoseSource(PoseSource):
    """Receives MCP1 packets on host:port. Malformed packets are counted and dropped."""

    def __init__(self, host="0.0.0.0", port=0, clock=time.monotonic):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((host, port))
        self.sock.setblocking(False)
        self.clock = clock
        self.bad = 0

    @property
    def port(self):
        return self.sock.getsockname()[1]

    def fileno(self):
        return self.sock.fileno()

    def poll(self):
        out = []
        while True:
            try:
                data = self.sock.recv(2048)
            except (BlockingIOError, InterruptedError):
                break
            s = decode(data, self.clock(), time.time())
            if s is None:
                self.bad += 1
            else:
                out.append(s)
        return out

    def close(self):
        self.sock.close()


def pose_stamped_to_sample(msg, body_name, frame_no, t_rx, t_rx_wall=0.0) -> MocapSample:
    """Swappable-adapter hook: a ROS 2 geometry_msgs/PoseStamped (duck-typed) -> MocapSample. PoseStamped has no
    tracking flag (tracked = -1, so the frozen-pose fallback applies) and no body ID (taken from the topic name the
    caller subscribed to)."""
    p, q = msg.pose.position, msg.pose.orientation
    st = msg.header.stamp
    return MocapSample(frame_no=frame_no, t_mocap=st.sec + st.nanosec * 1e-9, t_rx=t_rx, body_id=0,
                       body_name=body_name, tracked=-1, pos=(p.x, p.y, p.z), quat=(q.w, q.x, q.y, q.z),
                       t_rx_wall=t_rx_wall)
