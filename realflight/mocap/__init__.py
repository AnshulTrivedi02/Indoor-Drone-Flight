"""Mocap RECORDER for the rung-1 real flights (plan item R7): logs the mocap stream to a file for offline scoring.

Modules:
  source.py    - the input interface (MocapSample, PoseSource) and the one concrete adapter: the MCP1 UDP pose packet.
  recorder.py  - the executable recorder: raw CSV + JSON metadata sidecar (counts, duplicates, malformed, dropouts).
  export.py    - raw CSV -> the mocap_align CSV (`t_s, x, y, z, qx, qy, qz, qw`, metres, z UP, scalar-last quaternion).

The packet, MocapSample and PoseSource are defined ONCE, in realflight/mcp1.py, shared with the live safety watcher
(realflight/watcher/mocap.py). source.py re-exports them (unified 2026-10-11).

WHAT THE REAL MOCAP SYSTEM MUST PROVIDE (the system is unknown until the supervisor names it; plan input S5):
  - a forwarder from the vendor SDK (OptiTrack NatNet, Vicon DataStream, or a VRPN client) to the MCP1 UDP packet below,
    run on the mocap PC or the ground station. One small program, written once the system is known.
  - destinations: the recorder and the watcher both bind a UDP port, and two processes cannot share one unicast port,
    so the forwarder sends every packet to BOTH ports (or to a multicast group both join).
  - rate >= 100 Hz per rigid body (120-240 Hz typical). The time sync (eval/mocap_align.py) differentiates orientation,
    so a higher rate helps; >= 50 Hz is the watcher's floor.
  - per frame: the mocap frame number (duplicate rejection, dropout counting) and the MOCAP-CLOCK timestamp of the frame
    (exposure time if the SDK gives it). The recorder also logs its own receive time (monotonic and wall clock).
  - a rigid-body ID and/or name, stable for the session; the vehicle is one rigid body.
  - a tracked/valid flag per frame if the system has one (NatNet: tracking-valid bit; Vicon: occluded flag). VRPN repeats
    the last pose instead: send tracked = -1, and the export drops frozen (bit-identical) poses.
  - world frame: right-handed, metres, z UP or y UP (export --up-axis; OptiTrack Motive defaults to y up, Vicon to z up).
    The yaw/origin of the mocap frame do not matter: mocap_align fits them (4-DoF).
  - the mocap clock need not be synchronised to anything: mocap_align fits offset AND rate against the FC's 400 Hz RISI
    gyro. It should be MONOTONIC and continuous for the whole recording; sync wiggles at both ends of each log. A
    restart (frame counter or mocap clock reset) no longer loses data: the recorder starts a new `segment` and logs it,
    but a segment without both sync wiggles cannot be time-aligned, so a restart mid-flight may still cost that flight.
  - orientation noise: well under ~0.1 deg per frame (ordinary for marker sets of 4+ markers); worse noise blurs |w|.
"""
