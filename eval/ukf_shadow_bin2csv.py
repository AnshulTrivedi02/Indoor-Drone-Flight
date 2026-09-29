#!/usr/bin/env python3
"""Part 4: convert the shadow UKF's own dataflash records (XUKF + XUKS, written live in SITL by
AP_NavUKF::log_state) into the same CSV layout the Replay tool writes (ukf_shadow.csv), so that
eval/ukf_shadow_replay_check.py reads a live SITL run and a Replay run identically.
Also reports whether the FMT records exist and how many rows parsed (a check that the dynamic
WriteStreaming messages decode from a SITL log, which the Replay log could not do).
Usage: python3 eval/ukf_shadow_bin2csv.py BIN OUT_CSV"""
import sys
from pymavlink import mavutil
b, out = sys.argv[1], sys.argv[2]
m = mavutil.mavlink_connection(b)
fmt, xf, xs = set(), {}, {}
while True:
    r = m.recv_match(type=["FMT", "XUKF", "XUKS"])
    if r is None:
        break
    t = r.get_type()
    if t == "FMT":
        if r.Name in ("XUKF", "XUKS"):
            fmt.add(r.Name)
    elif t == "XUKF":
        xf[r.TimeUS] = r
    else:
        xs[r.TimeUS] = r
common = sorted(set(xf) & set(xs))
print(f"FMT present: {sorted(fmt)}; XUKF rows {len(xf)}, XUKS rows {len(xs)}, paired {len(common)}")
with open(out, "w") as f:
    f.write("TimeUS,PN,PE,PD,VN,VE,VD,Roll,Pitch,Yaw,SVN,SVE,SS,Healthy,FlowAgeMs,FXa,FYa,Ra\n")
    for t in common:
        a, s = xf[t], xs[t]
        f.write(f"{t},{a.PN:.4f},{a.PE:.4f},{a.PD:.4f},{a.VN:.4f},{a.VE:.4f},{a.VD:.4f},{a.Roll:.3f},{a.Pitch:.3f},"
                f"{a.Yaw:.3f},{s.SVN:.5f},{s.SVE:.5f},{s.SS},{s.H},{s.FAge},{s.FXa},{s.FYa},{s.Ra}\n")
