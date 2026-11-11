import sys, os
sys.path.insert(0, os.path.expanduser("~/.cache/thesis_pyshim"))
from pymavlink import mavutil
trial = sys.argv[1]
D = os.path.expanduser(f"~/thesis_data/trials/{trial}")
mm = mavutil.mavlink_connection(f"{D}/ardupilot.bin")
n = 0
while True:
    m = mm.recv_match(type=["ERR", "MSG"])
    if m is None: break
    s = str(m)
    if "ail" in s.lower() or "FS_" in s or m.get_type() == "ERR":
        print(trial, m.get_type(), s[:200])
        n += 1
print(trial, "total flagged:", n)
