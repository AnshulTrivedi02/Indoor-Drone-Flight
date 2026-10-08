"""Equivalence export for the C++ FGO port (docs/fgo_cpp_port.md). Used ONLY when FGO_DUMP_EVENTS is set in
fgo_replay.py / room_fgo_replay.py; it reads estimator state but never changes it.

Files written for a prefix P:
  P.init.json   init inputs and configuration (floats via json: exact round trip)
  P.raw.f64     the RAW event stream in bag order (header stamps, before the gap rule / dejitter / sort), plus the
                forward-camera / GNSS measurement events exactly as the replay appends them; input to the C++ front end
  P.events.f64  the PROCESSED event stream the replay loop consumes (after gap rule, dejitter, stable sort), with
                each flow's interval-averaged omega and each forward frame's interval-averaged gyro-z
  P.kf.f64      per keyframe (KF_COLS columns, below)
  P.batch.f64   whole-flight batch solution, if any: (k, t, p xyz, R row-major 9)
Event rows (EV_COLS = 9): kind, t, then payload
  0 imu  acc xyz, gyro xyz          1 att  rate xyz                 2 rng  range
  3 flow fx, fy, valid, inlier, omega xyz (processed stream only; NaN in raw)
  4 fwd  psi|NaN, omega|NaN, gyro-z avg (NaN in raw)                5 tag  x, y, yaw
  6 gnss E, N, vE, vN
"""
import json
import numpy as np

EV_COLS = 9
KF_COLS = 40
KIND = {"imu": 0, "att": 1, "rng": 2, "flow": 3, "fwd": 4, "tag": 5, "gnss": 6}
NAN = float("nan")


def _num(v):
    return NAN if v is None else float(v)


def event_rows(ev, flow_om=None, fwd_gz=None):
    flow_om = flow_om or {}; fwd_gz = fwd_gz or {}
    rows = np.full((len(ev), EV_COLS), NAN)
    for i, (tt, kind, d) in enumerate(ev):
        r = rows[i]; r[0] = KIND[kind]; r[1] = tt
        if kind == "imu":
            r[2:5] = d[0]; r[5:8] = d[1]
        elif kind == "att":
            r[2:5] = d
        elif kind == "rng":
            r[2] = d
        elif kind == "flow":
            r[2:6] = [d[0][0], d[0][1], float(d[1]), d[2]]
            if i in flow_om:
                r[6:9] = flow_om[i]
        elif kind == "fwd":
            r[2] = _num(d[0]); r[3] = _num(d[1])
            if i in fwd_gz:
                r[4] = fwd_gz[i]
        elif kind == "tag":
            r[2:5] = d
        elif kind == "gnss":
            r[2:6] = d
    return rows


def kf_row(t_kf, t_lat, k_before, k_after, d_replaced, d_flow, d_range, flow_used, rng, pose, vel, bias,
           fwd_entries=(), d_tag=0, d_gnss=0, anchored=1, failed=0, n_fail=0):
    """fwd_entries: the fwd_log entries appended during this keyframe ((t, kind, nis, ok, S), kind 0 heading, 1 yaw rate)."""
    psi = [NAN, NAN]; om = [NAN, NAN]
    for e in fwd_entries:
        (psi if e[1] == 0 else om)[:] = [e[2], float(e[3])]
    fu = flow_used if flow_used is not None else (NAN, NAN)
    row = [t_kf, t_lat, k_before, k_after, d_replaced, d_flow, d_range, fu[0], fu[1], _num(rng)]
    row += list(pose.translation()) + list(pose.rotation().matrix().reshape(-1)) + list(np.asarray(vel, float))
    row += list(bias.accelerometer()) + list(bias.gyroscope())
    row += psi + om + [d_tag, d_gnss, anchored, failed, n_fail]
    assert len(row) == KF_COLS
    return row


def write(prefix, info, raw_ev, ev, flow_om, fwd_gz, kf_rows, batch_rows=None):
    raw = event_rows(raw_ev); proc = event_rows(ev, flow_om, fwd_gz)
    raw.tofile(prefix + ".raw.f64"); proc.tofile(prefix + ".events.f64")
    np.asarray(kf_rows, np.float64).reshape(-1, KF_COLS).tofile(prefix + ".kf.f64")
    if batch_rows is not None:
        np.asarray(batch_rows, np.float64).reshape(-1, 14).tofile(prefix + ".batch.f64")
    info = dict(info, event_cols=EV_COLS, kf_cols=KF_COLS, n_raw=len(raw), n_events=len(proc), n_kf=len(kf_rows),
                n_batch=(None if batch_rows is None else len(batch_rows)))
    json.dump(info, open(prefix + ".init.json", "w"), indent=1)
