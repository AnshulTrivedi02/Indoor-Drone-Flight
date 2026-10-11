"""SITL ONLY (bench 2c): every ARM/DISARM and arming-check message in a session's dataflash, on the wall clock."""
import glob
import os
import sys
from realflight.sitl_bench.analyse import boots, df_events

for D in sys.argv[1:]:
    cms = boots(D)
    print("##", os.path.basename(D), "first SYSTEM_TIME wall", cms[0].w[0])
    for b in sorted(glob.glob(os.path.join(D, "dataflash", "*.BIN"))):
        for w, f, src, s in df_events(b, cms[-1]):
            if "ARMED" in s or "Arm" in s or "PreArm" in s:
                print(f"{w:.3f} F={f:8.3f} {os.path.basename(b)} {s[:100]}")
