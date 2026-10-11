#!/usr/bin/env python3
"""Export a raw mocap recording (recorder.py) to the CSV eval/mocap_align.py reads:
  t_s, x, y, z, qx, qy, qz, qw     (metres; world z UP; scalar-LAST quaternion)

This is the ONE place where the raw log's conventions are converted:
  - quaternion order: raw (w, x, y, z) -> (x, y, z, w);
  - up axis: --up-axis z (identity) or y (Rx(+90 deg): (x, y, z) -> (x, -z, y); the body orientation becomes
    A R A^T, the same convention as realflight/watcher/frames.py). Confirm the axis on the bench (hand-roll and
    hand-pitch the vehicle) before trusting it.
Segments (recorder restarts, 2026-10-11): a raw log with more than one `segment` for the body is REFUSED when its
t_mocap, in recording order, is not strictly increasing across the whole log (a mocap clock reset: sorting by t_mocap
would interleave the segments), unless --segment N names one. It is allowed when t_mocap is continuous (a forwarder
restart while the mocap clock kept running) or with --time rx (the receive clock is monotonic). Logs from before the
segment column count as one segment.
Rows dropped (counted in the summary):
  - other bodies (when the log holds several, --body-id or --body-name is required);
  - tracked == 0 (the system said NOT tracked);
  - tracked == -1 only: FROZEN poses, i.e. a run of bit-identical poses lasting >= --frozen-s (VRPN repeats the last
    pose when it loses the body); the first sample of the run is kept, the repeats are dropped;
  - non-increasing times (after sorting by the chosen clock).
The time column is t_mocap (default; the mocap's own frame clock, least jitter) or t_rx (--time rx, the receive clock).
Both are written to the summary JSON next to the output.

Usage: python3 -m realflight.mocap.export RAW.csv OUT.csv [--up-axis z|y] [--body-id N | --body-name S] [--time mocap|rx]
                                         [--segment N]
"""
import argparse, csv, json, math, os, sys

import numpy as np

_A_QUAT = {"z": (1.0, 0.0, 0.0, 0.0), "y": (math.cos(math.pi / 4), math.sin(math.pi / 4), 0.0, 0.0)}   # (w,x,y,z)
_A_MAT = {"z": np.eye(3), "y": np.array([[1.0, 0.0, 0.0], [0.0, 0.0, -1.0], [0.0, 1.0, 0.0]])}


def qmul(a, b):
    """Hamilton product, (w, x, y, z), vectorised over rows."""
    aw, ax, ay, az = a.T; bw, bx, by, bz = b.T
    return np.c_[aw * bw - ax * bx - ay * by - az * bz, aw * bx + ax * bw + ay * bz - az * by,
                 aw * by - ax * bz + ay * bw + az * bx, aw * bz + ax * by - ay * bx + az * bw]


def convert_up(p, q_wxyz, up):
    """p (N,3), q (N,4) w-first in the mocap frame -> z-up: p' = A p, R' = A R A^T (q' = qA q qA^-1)."""
    A = _A_MAT[up]; qa = np.tile(_A_QUAT[up], (len(q_wxyz), 1)); qa_inv = qa * np.array([1, -1, -1, -1])
    q = qmul(qmul(qa, q_wxyz), qa_inv)
    q /= np.linalg.norm(q, axis=1)[:, None]
    return (A @ p.T).T, q


def load_raw(path):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit(f"{path}: no rows")
    num = lambda k, t=float: np.array([t(r[k]) for r in rows])
    return {"frame_no": num("frame_no", int), "t_mocap": num("t_mocap"), "t_rx": num("t_rx_mono"),
            "body_id": num("body_id", int), "body_name": np.array([r["body_name"] for r in rows]),
            "tracked": num("tracked", int), "p": np.c_[num("px"), num("py"), num("pz")],
            "segment": np.array([int(r.get("segment") or 0) for r in rows]),
            "q": np.c_[num("qw"), num("qx"), num("qy"), num("qz")]}


def frozen_mask(t, p, q, tracked, frozen_s):
    """True for the REPEATS inside a run of bit-identical poses lasting >= frozen_s, among tracked == -1 rows."""
    drop = np.zeros(len(t), bool); i = 0; n = len(t)
    while i < n:
        j = i + 1
        while j < n and np.array_equal(p[j], p[i]) and np.array_equal(q[j], q[i]):
            j += 1
        if j - i > 1 and t[j - 1] - t[i] >= frozen_s:
            drop[i + 1:j] = tracked[i + 1:j] == -1
        i = j
    return drop


def export(raw, out_path, up="z", body_id=None, body_name=None, time_col="mocap", frozen_s=0.5, segment=None):
    keys = sorted(set(zip(raw["body_id"].tolist(), raw["body_name"].tolist())))
    if body_id is None and body_name is None:
        if len(keys) > 1:
            sys.exit(f"several bodies in the log {keys}: give --body-id or --body-name")
        sel = np.ones(len(raw["t_mocap"]), bool)
    else:
        sel = np.ones(len(raw["t_mocap"]), bool)
        if body_id is not None:
            sel &= raw["body_id"] == body_id
        if body_name is not None:
            sel &= raw["body_name"] == body_name
    r = {k: v[sel] for k, v in raw.items()}
    segs = sorted(set(r["segment"].tolist()))
    if segment is not None:
        if segment not in segs:
            sys.exit(f"segment {segment} not in the log (segments {segs})")
        r = {k: v[r["segment"] == segment] for k, v in r.items()}
    elif len(segs) > 1 and time_col == "mocap" and not np.all(np.diff(r["t_mocap"]) > 0):
        sys.exit(f"the log has {len(segs)} segments (recorder restarts, see the .meta.json `restarts`) and its mocap "
                 f"clock is not continuous across them: sorting by t_mocap would interleave them. Name one with "
                 f"--segment N (segments {segs}), or use --time rx.")
    t = r["t_mocap"] if time_col == "mocap" else r["t_rx"]
    o = np.argsort(t, kind="stable"); r = {k: v[o] for k, v in r.items()}; t = t[o]
    n0 = len(t)
    untracked = r["tracked"] == 0
    frozen = frozen_mask(t, r["p"], r["q"], r["tracked"], frozen_s)
    keep = ~untracked & ~frozen
    t, p, q = t[keep], r["p"][keep], r["q"][keep]
    inc = np.r_[True, np.diff(t) > 0]
    t, p, q = t[inc], p[inc], q[inc]
    p2, q2 = convert_up(p, q, up)
    with open(out_path, "w") as f:
        f.write("# t_s, x, y, z, qx, qy, qz, qw  (metres, z up, scalar-last; from realflight.mocap.export)\n")
        for ti, pi, qi in zip(t, p2, q2):
            f.write(f"{ti:.9f},{pi[0]:.6f},{pi[1]:.6f},{pi[2]:.6f},{qi[1]:.9f},{qi[2]:.9f},{qi[3]:.9f},{qi[0]:.9f}\n")
    summ = {"raw_rows_for_body": int(n0), "dropped_not_tracked": int(untracked.sum()),
            "dropped_frozen": int(frozen.sum()), "dropped_non_increasing_time": int((~inc).sum()),
            "written": int(len(t)), "time_column": time_col, "up_axis": up, "frozen_s": frozen_s,
            "bodies_in_log": [list(k) for k in keys], "segments_in_log": segs, "segment_exported": segment,
            "out": os.path.abspath(out_path)}
    with open(out_path + ".export.json", "w") as f:
        json.dump(summ, f, indent=1)
    return summ


def main(argv=None):
    ap = argparse.ArgumentParser(description="raw mocap CSV -> mocap_align CSV")
    ap.add_argument("raw"); ap.add_argument("out"); ap.add_argument("--up-axis", choices=["z", "y"], required=True)
    ap.add_argument("--body-id", type=int); ap.add_argument("--body-name")
    ap.add_argument("--time", choices=["mocap", "rx"], default="mocap"); ap.add_argument("--frozen-s", type=float, default=0.5)
    ap.add_argument("--segment", type=int, help="export only this recorder segment (required for a multi-segment log "
                    "whose mocap clock is not continuous)")
    a = ap.parse_args(argv)
    s = export(load_raw(a.raw), a.out, a.up_axis, a.body_id, a.body_name, a.time, a.frozen_s, a.segment)
    print(json.dumps(s, indent=1))


if __name__ == "__main__":
    main()
