import os, sys, time
from pymavlink import mavutil
T = os.path.expanduser("~/thesis_data/trials")
for d in sys.argv[1:]:
    p = os.path.join(T, d, "ardupilot.bin")
    m = mavutil.mavlink_connection(p)
    v = {}
    while True:
        r = m.recv_match(type="PARM")
        if r is None:
            break
        if r.Name in ("AHRS_EKF_TYPE", "AHRS_UKF_ENABLE"):
            v[r.Name] = r.Value
        if len(v) == 2:
            break
    print(d, time.strftime("%F %H:%M", time.localtime(os.path.getmtime(p))), v)
