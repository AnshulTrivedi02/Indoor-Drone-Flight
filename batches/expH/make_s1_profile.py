#!/usr/bin/env python3
"""Experiment H S1 profile (METHODOLOGY pre-registration), in the tag frame W (LOCAL_NED with EKF3 flying on the wall tag).
Usage: python3 batches/expH/make_s1_profile.py AMPLITUDE_M OUT.json"""
import json, sys
A = float(sys.argv[1]); H = [-1.5, 0.0]
S = [{"type": "wait_fix", "near": H, "tol": 0.5, "timeout": 60},
     {"type": "move", "to": H, "speed": 0.2}, {"type": "hold", "s": 60}]
for _ in range(3):                                  # 3 lateral cycles: centre -> +A -> centre -> -A -> centre, 5 s pauses
    for e in (A, 0.0, -A, 0.0):
        S += [{"type": "move", "to": [H[0], e], "speed": 0.2}, {"type": "hold", "s": 5}]
S += [{"type": "hold", "s": 30}]
for loss, after in ((5, 20), (15, 20), (30, 30)):   # losses while hovering
    S += [{"type": "occluder", "on": True}, {"type": "hold", "s": loss}, {"type": "occluder", "on": False}, {"type": "hold", "s": after}]
# loss during a lateral move: covered for the whole centre -> +A -> centre move (A/0.2 s each way, 2 s pause)
S += [{"type": "occluder", "on": True}, {"type": "move", "to": [H[0], A], "speed": 0.2}, {"type": "hold", "s": 2},
      {"type": "move", "to": H, "speed": 0.2}, {"type": "occluder", "on": False}, {"type": "hold", "s": 20}]
json.dump(S, open(sys.argv[2], "w"), indent=1)
tot = sum(s.get("s", 0) for s in S) + sum(abs(A) / 0.2 for s in S if s["type"] == "move" and s["to"][1] != 0) * 1 + 12 * 2.5 * A / 0.5
print(f"{len(S)} segments; amplitude {A} m")
