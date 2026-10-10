"""Real-hardware mocap safety watcher (closes gaps G1-G11 of docs/real_flights_plan.md section 7.2.0).

Modules:
  mocap.py     - mocap input interface (MocapSample, PoseSource) and the UDP pose-packet adapter (G1, G3 stream level)
  frames.py    - mocap frame conversion (z-up / y-up) and Euler angles in the FC's FRD convention
  liveness.py  - networked process liveness: beacon sender and monitor (G7)
  core.py      - the decision logic, clock-injected and I/O-free (G2, G3, G4 latch, G8, G10, stall)
  fc_link.py   - MAVLink link to the flight controller: heartbeat, LAND, param check (G4, G5, G6, G11)
  mocap_watch.py - the executable watcher (wires the above together; G9 heartbeat file)

This is a NEW module. sim/tools/wall_watch.py (the SITL watcher) is deliberately not imported or modified; the pieces
copied from it are marked "copied from wall_watch.py".
"""
