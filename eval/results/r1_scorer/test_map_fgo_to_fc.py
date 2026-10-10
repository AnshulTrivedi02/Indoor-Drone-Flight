"""Test-only: map the FGO TUM (Gazebo sim clock, the same clock as /ground_truth/pose) to the FC clock with the map
mocap_align fitted for GT-as-mocap (GT and the FGO share the sim clock)."""
import json, sys
import numpy as np
al = json.load(open(sys.argv[1]))["clock"]["map"]
o1, t1, r = al["o1_s"], al["t1_fc_s"], al["rate_ppm"] * 1e-6
a = np.loadtxt(sys.argv[2])
a[:, 0] = (a[:, 0] - o1 + r * t1) / (1 + r)
np.savetxt(sys.argv[3], a, fmt="%.6f")
print(len(a), a[0, 0], a[-1, 0])
