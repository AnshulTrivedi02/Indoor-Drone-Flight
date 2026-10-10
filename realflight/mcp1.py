"""The ONE shared mocap input module: the MCP1 UDP pose packet, MocapSample, the PoseSource interface, UdpPoseSource and
the ROS 2 PoseStamped hook. Used by BOTH the live safety watcher (realflight/watcher/mocap.py re-exports it) and the
rung-1 recorder (realflight/mocap/source.py re-exports it). Unified 2026-10-11; before that the two packages carried
identical, independent copies.

INTERFACE (swappable adapters): a PoseSource has poll() -> list[MocapSample] (non-blocking: everything received since
the last call), fileno() for select(), close(), and `bad` (malformed inputs dropped so far). Any adapter (a NatNet
client, a Vicon DataStream client, a VRPN client, a ROS 2 subscription, a file replayer) only has to produce
MocapSample objects.

WHY A UDP PACKET (and not a ROS 2 PoseStamped subscription or a vendor SDK directly):
  - The mocap system is not known yet. A vendor-neutral packet means the system-specific part is one small forwarder
    (NatNet SDK, Vicon DataStream SDK or a VRPN client -> MCP1), written once the system is known.
  - One forwarder feeds both the watcher and the recorder, so the recorder logs exactly what the watcher saw.
  - PoseStamped drops the fields both need: the mocap frame number (duplicate rejection, dropout counting), the tracking
    flag, and the body ID (only implicit in a topic name).
  - The safety loop does not depend on the ROS 2 graph, so a ROS fault cannot blind the watcher silently.
  - It is testable offline with plain sockets.
  `pose_stamped_to_sample` converts a ROS 2 PoseStamped if a ROS driver is preferred later.

Packet (little-endian, 93 bytes), struct '<4sIdI16sb7d':
  magic b'MCP1' | frame_no u32 | t_mocap f64 (s, mocap clock) | body_id u32 | body_name 16 bytes (NUL-padded ASCII)
  | tracked i8 (1 tracked, 0 NOT tracked, -1 unknown/not provided) | px py pz f64 (m, mocap frame)
  | qw qx qy qz f64 (scalar FIRST, mocap frame)
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
    t_rx: float             # receipt, this host's monotonic clock (s)
    body_id: int
    body_name: str
    tracked: int            # 1, 0, or -1 (unknown)
    pos: tuple              # mocap frame (m)
    quat: tuple             # (w, x, y, z), mocap frame
    t_rx_wall: float = 0.0  # receipt, wall clock (s since epoch; the watcher's B7a latency log)


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

    bad = 0                 # malformed inputs dropped so far (adapters that can see them count them)

    def poll(self) -> List[MocapSample]:
        raise NotImplementedError

    def fileno(self) -> int:
        raise NotImplementedError

    def close(self):
        pass


class UdpPoseSource(PoseSource):
    """Receives MCP1 packets on host:port (port 0 = any free port, see .port). Malformed packets are counted, dropped.
    rcvbuf: SO_RCVBUF in bytes, or None to keep the OS default (the watcher's setting; the recorder asks for 1 MiB to
    absorb bursts while the disk writes)."""

    def __init__(self, host="0.0.0.0", port=0, clock=time.monotonic, rcvbuf=None):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if rcvbuf is not None:
            try:
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, rcvbuf)
            except OSError:
                pass
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
    tracking flag (tracked = -1, so the watcher's frozen-pose fallback and the export's frozen-pose rule apply) and no
    body ID (taken from the topic name the caller subscribed to)."""
    p, q = msg.pose.position, msg.pose.orientation
    st = msg.header.stamp
    return MocapSample(frame_no=frame_no, t_mocap=st.sec + st.nanosec * 1e-9, t_rx=t_rx, body_id=0,
                       body_name=body_name, tracked=-1, pos=(p.x, p.y, p.z), quat=(q.w, q.x, q.y, q.z),
                       t_rx_wall=t_rx_wall)
