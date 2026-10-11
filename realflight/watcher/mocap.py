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

The packet, MocapSample, PoseSource, UdpPoseSource and pose_stamped_to_sample live in ONE shared module,
realflight/mcp1.py (also used by the rung-1 recorder, realflight/mocap); this module re-exports them unchanged.

Packet (little-endian, 93 bytes), struct '<4sIdI16sb7d':
  magic b'MCP1' | frame_no u32 | t_mocap f64 (s, mocap clock) | body_id u32 | body_name 16 bytes (NUL-padded ASCII)
  | tracked i8 (1 tracked, 0 NOT tracked, -1 unknown/not provided) | px py pz f64 | qw qx qy qz f64
"""

from realflight.mcp1 import (MAGIC, PACKET, MocapSample, PoseSource, UdpPoseSource, decode, encode,  # noqa: F401
                             pose_stamped_to_sample)

__all__ = ["MAGIC", "PACKET", "MocapSample", "PoseSource", "UdpPoseSource", "decode", "encode", "pose_stamped_to_sample"]
