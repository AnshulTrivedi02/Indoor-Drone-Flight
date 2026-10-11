"""Mocap input interface and the one concrete adapter: the MCP1 UDP pose packet.

INTERFACE (swappable adapters): a PoseSource has poll() -> list[MocapSample] (non-blocking: everything received since
the last call), fileno() for select(), and close(). Any adapter (a NatNet client, a Vicon DataStream client, a VRPN
client, a ROS 2 subscription, a file replayer) only has to produce MocapSample objects.

WHY THE MCP1 UDP PACKET for the concrete adapter (and not a ROS 2 PoseStamped topic or a vendor SDK directly):
  - The mocap system is not known yet. A vendor-neutral packet means the system-specific part is one small forwarder
    (NatNet SDK, Vicon DataStream SDK or a VRPN client -> MCP1), written once the system is known; the recorder, the
    tests and the export do not change.
  - It is the SAME packet the live safety watcher reads (realflight/watcher/mocap.py), so one forwarder
    feeds both, and the recorder logs exactly what the watcher saw.
  - PoseStamped drops fields the recording needs: the mocap frame number (duplicates, dropout counting), the tracking
    flag, and the body ID (only implicit in a topic name). Rung 1 also needs no ROS on the ground station.
  - It is testable offline with plain sockets.
  `pose_stamped_to_sample` converts a ROS 2 PoseStamped if a ROS driver is preferred later.

UNIFIED 2026-10-11: the packet, MocapSample, PoseSource, UdpPoseSource and pose_stamped_to_sample live in ONE shared
module, realflight/mcp1.py, which the watcher (realflight/watcher/mocap.py) also imports. The only recorder-specific
difference is UdpPoseSource's default SO_RCVBUF of 1 MiB (below).

Packet (little-endian, 93 bytes), struct '<4sIdI16sb7d':
  magic b'MCP1' | frame_no u32 | t_mocap f64 (s, mocap clock) | body_id u32 | body_name 16 bytes (NUL-padded ASCII)
  | tracked i8 (1 tracked, 0 NOT tracked, -1 unknown/not provided) | px py pz f64 (m, mocap frame)
  | qw qx qy qz f64 (scalar FIRST, mocap frame)
"""

from realflight import mcp1 as _mcp1
from realflight.mcp1 import MAGIC, PACKET, MocapSample, PoseSource, decode, encode, pose_stamped_to_sample  # noqa: F401

RECORDER_RCVBUF = 1 << 20


class UdpPoseSource(_mcp1.UdpPoseSource):
    """The shared adapter with the recorder's default receive buffer (1 MiB: absorb bursts while the disk writes)."""

    def __init__(self, host="0.0.0.0", port=0, clock=_mcp1.time.monotonic, rcvbuf=RECORDER_RCVBUF):
        super().__init__(host, port, clock, rcvbuf)
