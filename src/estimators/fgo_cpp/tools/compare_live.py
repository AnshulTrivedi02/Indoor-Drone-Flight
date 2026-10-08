#!/usr/bin/env python3
"""Check a live-adapter replay (fgo_cpp_live_replay) against the export-driven C++ result (docs/fgo_cpp_port.md, band L).

Usage (~/venv-ardupilot: pymavlink + numpy): compare_live.py <tape.f64> <live_out_prefix> <ref_prefix> [--frame corridor|enu]
  1. every ODOMETRY frame in <live>.mav.bin is parsed by pymavlink (MAVLink 2, CRC checked); count = sent keyframes;
     each frame is re-encoded by pymavlink from its decoded fields (sysid 255, compid 197, same seq) and compared
     byte for byte with the adapter's frame (what fgo_node.py's odometry_send would put on the wire);
  2. time_usec of every frame equals an independent re-implementation of fgo_node._sitl_us (D25: 10 s settle, 10 s
     window, inliers within 20 ms of the median, lower envelope) over the time_ref messages that had arrived;
  3. states: (a) every keyframe row of the adapter vs the reference rows (count, |dp|, |dyaw|); (b) every decoded
     ODOMETRY state, converted back from NED to the navigation frame, vs the reference row of the same keyframe;
  4. validity: quality 100/0 against the adapter's valid flag."""
import os, sys
os.environ["MAVLINK20"] = "1"
import numpy as np
from pymavlink.dialects.v20 import ardupilotmega as mavlink

tape_p, live_p, ref_p = sys.argv[1:4]
frame = sys.argv[sys.argv.index("--frame") + 1] if "--frame" in sys.argv else "corridor"
tape = np.fromfile(tape_p).reshape(-1, 9)
L = np.fromfile(live_p + ".live.f64").reshape(-1, 6)          # t_k, valid, sent, t_us, step_ns, arrival index
K = np.fromfile(live_p + ".kf.f64").reshape(-1, 40)
Rf = np.fromfile(ref_p + ".kf.f64").reshape(-1, 40)
raw = open(live_p + ".mav.bin", "rb").read()

# 1. parse and re-encode
msgs = []
parser = mavlink.MAVLink(None)
for b in raw:
    m = parser.parse_char(bytes([b]))
    if m is not None:
        msgs.append(m)
print(f"[mavlink] parsed {len(msgs)} ODOMETRY frames (bad CRC / parse errors: {parser.total_receive_errors}); "
      f"sent keyframes {int(L[:, 2].sum())}")
enc = mavlink.MAVLink(None, srcSystem=255, srcComponent=197)
reb = bytearray()
for m in msgs:
    enc.seq = m.get_seq()
    reb += enc.odometry_encode(m.time_usec, m.frame_id, m.child_frame_id, m.x, m.y, m.z, m.q, m.vx, m.vy, m.vz,
                               m.rollspeed, m.pitchspeed, m.yawspeed, m.pose_covariance, m.velocity_covariance,
                               m.reset_counter, m.estimator_type, m.quality).pack(enc)
print(f"[mavlink] pymavlink re-encoding byte-identical to the adapter's frames: {bytes(reb) == raw}")

# 2. independent _sitl_us
sent = np.flatnonzero(L[:, 2] > 0)
tr = [(i, r[1], r[2]) for i, r in enumerate(tape) if r[0] == 7]
tr_idx = np.array([x[0] for x in tr]); tr_th = np.array([x[1] for x in tr]); tr_ts = np.array([x[2] for x in tr])
t0 = tr_th[0]
mism = 0
for j, kf in enumerate(sent):
    n_arr = int(L[kf, 5])                       # inputs consumed (tape rows of kinds 0-7) when this keyframe came out
    # map arrival count -> tape index (kind 8 rows do not count as arrivals)
    cnt = np.cumsum(tape[:, 0] != 8)
    last_row = int(np.searchsorted(cnt, n_arr))  # tape row index of the n_arr-th arrival
    k = np.searchsorted(tr_idx, last_row, side="right")   # time_refs that had arrived
    th_last = tr_th[k - 1]
    win = (tr_th[:k] >= th_last - 10.0)
    # the deque pops while front < th - 10 at each append: equivalent to keeping th >= th_last - 10
    o = (tr_th[:k] - tr_ts[:k])[win]
    med = np.median(o); mn = o[np.abs(o - med) <= 0.020].min()
    t_us = int(round((L[kf, 0] - mn) * 1e6))
    if th_last - t0 < 10.0 or t_us != int(msgs[j].time_usec):
        mism += 1
print(f"[clock] time_usec equal to the independent _sitl_us on {len(sent) - mism} of {len(sent)} frames")

# 3. states
yaw = lambda a: np.arctan2(a[:, 16], a[:, 13])
n = min(len(K), len(Rf))
print(f"[states] keyframes: adapter {len(K)}  reference {len(Rf)}  -> count {'IDENTICAL' if len(K) == len(Rf) else 'DIFFERENT'}")
dp = np.linalg.norm(K[:n, 10:13] - Rf[:n, 10:13], axis=1)
dy = np.degrees(np.abs((yaw(K[:n]) - yaw(Rf[:n]) + np.pi) % (2 * np.pi) - np.pi))
flags = {j: int((K[:n, j] != Rf[:n, j]).sum() - (np.isnan(K[:n, j]) & np.isnan(Rf[:n, j])).sum()) for j in (2, 3, 4, 5, 6, 32, 35)}
print(f"[states] decision mismatches by column {flags}")
print(f"[states] adapter rows vs reference: |dp| max {dp.max()*1e3:.3e} p99 {np.percentile(dp, 99)*1e3:.3e} mm; "
      f"|dyaw| max {dy.max():.3e} p99 {np.percentile(dy, 99):.3e} deg")
ok_rows = len(K) == len(Rf) and dp.max() <= 1e-3 and dy.max() <= 0.01
# decoded ODOMETRY -> navigation frame
P = np.array([[m.x, m.y, m.z] for m in msgs], float); Q = np.array([m.q for m in msgs], float)
if frame == "corridor":
    p_nav = np.column_stack([P[:, 0], -P[:, 1], -P[:, 2]])
else:
    p_nav = np.column_stack([P[:, 1], P[:, 0], -P[:, 2]])
w, x, y, z = Q.T
Rn = np.stack([np.stack([1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], -1),
               np.stack([2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], -1),
               np.stack([2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)], -1)], 1)
Cm = np.diag([1.0, -1, -1]) if frame == "corridor" else np.array([[0, 1.0, 0], [1, 0, 0], [0, 0, -1]])
Fb = np.diag([1.0, -1, -1])
Rnav = np.einsum("ij,njk,kl->nil", Cm.T, Rn, Fb)
yaw_nav = np.arctan2(Rnav[:, 1, 0], Rnav[:, 0, 0])
ref_s = Rf[sent]
dps = np.linalg.norm(p_nav - ref_s[:, 10:13], axis=1)
dys = np.degrees(np.abs((yaw_nav - yaw(ref_s) + np.pi) % (2 * np.pi) - np.pi))
print(f"[odometry] decoded states vs reference ({len(sent)} sent keyframes): |dp| max {dps.max()*1e3:.3e} "
      f"p99 {np.percentile(dps, 99)*1e3:.3e} mm; |dyaw| max {dys.max():.3e} p99 {np.percentile(dys, 99):.3e} deg")
ok_odo = dps.max() <= 1e-3 and dys.max() <= 0.01
# 4. validity
qual = np.array([m.quality for m in msgs]); val = L[sent, 1]
print(f"[valid] quality matches the valid flag on {int(((qual == 100) == (val > 0)).sum())} of {len(sent)} frames; "
      f"invalid keyframes {int((L[:, 1] == 0).sum())} of {len(L)} (first {L[L[:, 1] == 0][:1, 0]})")
print(f"BAND (same count, |dp|<=1 mm, |dyaw|<=0.01 deg; rows and decoded ODOMETRY): "
      f"{'PASS' if (ok_rows and ok_odo) else 'FAIL'}   time_usec all equal: {mism == 0}   "
      f"frames byte-identical to pymavlink: {bytes(reb) == raw}")
