#!/usr/bin/env python3
"""Task 1b: is the rollspeed-coupled lateral flow residual a SIGN error or a
TIMESTAMP offset between /attitude/angular_rates and the camera frames?
Cross-correlate rollspeed(t) vs measured flow_x_rad(t+lag) over a lag sweep; report
the lag of peak |correlation| and the correlation at lag 0. A sign/scale error peaks
at lag 0 (residual ~ rollspeed); a timestamp offset peaks at a non-zero lag (and the
residual would then track roll ACCELERATION). Run in venv-evo. Existing bag only."""
import sys, os, glob
import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore, get_types_from_msg

TRIAL = sys.argv[1] if len(sys.argv) > 1 else "dsn_tex_r1"
BAG = os.path.expanduser(f"~/thesis_data/trials/{TRIAL}/bag")
ts = get_typestore(Stores.ROS2_JAZZY)
mp = glob.glob(os.path.expanduser("~/thesis_ws/**/OpticalFlow.msg"), recursive=True)[0]
ts.register(get_types_from_msg(open(mp).read(), "optical_flow_interfaces/msg/OpticalFlow"))
stamp = lambda h: h.stamp.sec + h.stamp.nanosec*1e-9

att = []; flow = []
with Reader(BAG) as r:
    c = {x.topic: x for x in r.connections}
    for con, t, raw in r.messages(connections=[c[k] for k in
            ["/attitude/angular_rates", "/optical_flow/measurement"] if k in c]):
        m = ts.deserialize_cdr(raw, con.msgtype); tt = stamp(m.header)
        if con.topic == "/attitude/angular_rates":
            att.append((tt, m.vector.x))                 # rollspeed (FLU)
        else:
            if m.valid:
                flow.append((tt, m.flow_x_rad))
att = np.array(sorted(att)); flow = np.array(sorted(flow))
# common uniform grid over the cruise (avoid takeoff/land transients)
t0 = max(att[0, 0], flow[0, 0]) + 40; t1 = min(att[-1, 0], flow[-1, 0]) - 10
fs = 50.0; tg = np.arange(t0, t1, 1/fs)
rs = np.interp(tg, att[:, 0], att[:, 1])                  # rollspeed on grid
fx = np.interp(tg, flow[:, 0], flow[:, 1])                # measured flow_x on grid
rs -= rs.mean(); fx -= fx.mean()
# cross-correlation over lags: corr(rollspeed(t), flow_x(t+lag))
lags_s = np.arange(-0.30, 0.301, 1/fs)
cc = []
for L in lags_s:
    k = int(round(L*fs))
    if k >= 0:
        a, b = rs[:len(rs)-k], fx[k:]
    else:
        a, b = rs[-k:], fx[:len(fx)+k]
    cc.append(np.corrcoef(a, b)[0, 1])
cc = np.array(cc)
ipk = np.argmax(np.abs(cc))
c0 = cc[np.argmin(np.abs(lags_s))]
# also: correlation of residual proxy (-rollspeed - flow_x) with rollspeed vs roll accel
accel = np.gradient(rs, 1/fs)
resid = -rs - fx                                          # ~ lateral residual at cruise (transl ~0)
print(f"=== {TRIAL} derotation lag / sign analysis ===")
print(f"  corr(rollspeed, flow_x) at lag 0      = {c0:+.3f}")
print(f"  peak |corr| = {cc[ipk]:+.3f} at lag = {lags_s[ipk]*1000:+.1f} ms")
print(f"  corr(residual, rollspeed)={np.corrcoef(resid, rs)[0,1]:+.3f}   "
      f"corr(residual, roll ACCEL)={np.corrcoef(resid, accel)[0,1]:+.3f}")
print(f"  => lag~0 & +corr(rollspeed,flow_x) => flow_x = +k*rollspeed (SIGN of h_flow's"
      f" -rollspeed term is opposite). non-zero lag => timestamp offset.")
