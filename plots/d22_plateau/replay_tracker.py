#!/usr/bin/python3
"""Offline replay of flow_tracker.py's per-frame algorithm on recorded /downward_camera/image frames,
with extra diagnostics (feature centroid, fitted similarity, translation at the principal point).
System python3 (cv2 4.6.0, the same build the ROS node uses). Reads the rosbag2 sqlite directly."""
import sqlite3, struct, sys
import numpy as np, cv2

FOCAL = 554.0  # flow_tracker.FOCAL_LENGTH_PX
FEAT = dict(maxCorners=200, qualityLevel=0.01, minDistance=7, blockSize=7)
LK = dict(winSize=(21, 21), maxLevel=3, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01))
MIN_VALID = 20


class R:
    def __init__(s, b): s.b, s.o = b, 4
    def al(s, n): s.o += (-(s.o - 4)) % n
    def u32(s): s.al(4); v = struct.unpack_from('<I', s.b, s.o)[0]; s.o += 4; return v
    def i32(s): s.al(4); v = struct.unpack_from('<i', s.b, s.o)[0]; s.o += 4; return v
    def u8(s): v = s.b[s.o]; s.o += 1; return v
    def f64(s): s.al(8); v = struct.unpack_from('<d', s.b, s.o)[0]; s.o += 8; return v
    def st(s): n = s.u32(); v = s.b[s.o:s.o + n - 1].decode(); s.o += n; return v


def parse_image(b):
    r = R(b); sec = r.i32(); ns = r.u32(); r.st()
    h = r.u32(); w = r.u32(); enc = r.st(); r.u8(); step = r.u32(); n = r.u32()
    data = np.frombuffer(b, np.uint8, n, r.o)
    return sec + ns * 1e-9, h, w, enc, step, data


def parse_K(b):
    r = R(b); r.i32(); r.u32(); r.st(); r.u32(); r.u32(); r.st()
    nd = r.u32(); [r.f64() for _ in range(nd)]
    return [r.f64() for _ in range(9)]


def to_gray(h, w, enc, step, data):
    if enc in ('rgb8', 'bgr8'):
        img = data.reshape(h, step)[:, :w * 3].reshape(h, w, 3)
        bgr = img[:, :, ::-1].copy() if enc == 'rgb8' else img  # cv_bridge: rgb8 -> bgr8 is a channel swap
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    if enc == 'mono8':  # cv_bridge mono8 -> bgr8 then BGR2GRAY
        g = data.reshape(h, step)[:, :w]
        return cv2.cvtColor(cv2.cvtColor(g, cv2.COLOR_GRAY2BGR), cv2.COLOR_BGR2GRAY)
    raise ValueError(enc)


def main(db, out):
    c = sqlite3.connect(db)
    tid = {n: i for i, n in c.execute('select id,name from topics')}
    K = (parse_K(c.execute('select data from messages where topic_id=? limit 1', (tid['/downward_camera/camera_info'],)).fetchone()[0])
         if '/downward_camera/camera_info' in tid else [554.3827, 0, 320.0, 0, 554.3827, 240.0, 0, 0, 1])  # same camera model
    cx, cy = K[2], K[5]
    print('K fx fy cx cy', K[0], K[4], cx, cy)
    cv2.setRNGSeed(42)
    prev_gray = prev_pts = prev_time = None
    rows = []
    NAN = float('nan')
    for (b,) in c.execute('select data from messages where topic_id=? order by timestamp', (tid['/downward_camera/image'],)):
        t, h, w, enc, step, data = parse_image(b)
        gray = to_gray(h, w, enc, step, data)
        row = [t, 0, 0., 0., 0, 0., 0] + [NAN] * 14  # t, published, fx, fy, count, inl, valid, diag...
        if prev_gray is None:
            prev_gray, prev_time = gray, t
            prev_pts = cv2.goodFeaturesToTrack(gray, mask=None, **FEAT)
            rows.append(row); continue
        if prev_pts is None or len(prev_pts) < 20:
            prev_pts = cv2.goodFeaturesToTrack(prev_gray, mask=None, **FEAT)
            prev_gray, prev_time = gray, t
            row[1] = 2  # re-detect frame (invalid published)
            rows.append(row); continue
        nxt, status, _ = cv2.calcOpticalFlowPyrLK(prev_gray, gray, prev_pts, None, **LK)
        if nxt is None or status is None:
            prev_gray, prev_time = gray, t
            prev_pts = cv2.goodFeaturesToTrack(gray, mask=None, **FEAT)
            rows.append(row); continue
        good_new = nxt[status.flatten() == 1].reshape(-1, 2)
        good_old = prev_pts[status.flatten() == 1].reshape(-1, 2)
        tracked = len(good_new); pre = tracked
        M = None; inl_old = good_old
        if tracked > 0:
            disp = good_new - good_old
            if tracked >= 4:
                M, mask = cv2.estimateAffinePartial2D(good_old, good_new, method=cv2.RANSAC, ransacReprojThreshold=2.0)
                if mask is not None:
                    inl = mask.flatten().astype(bool)
                    disp = disp[inl]; inl_old = good_old[inl]; tracked = int(inl.sum())
            ratio = tracked / pre if pre > 0 else 0.0
            if tracked == 0:
                prev_gray, prev_time = gray, t
                prev_pts = cv2.goodFeaturesToTrack(gray, mask=None, **FEAT)
                rows.append(row); continue
            dt = t - prev_time
            mdx, mdy = float(np.median(disp[:, 0])), float(np.median(disp[:, 1]))
            fx = mdx / dt / FOCAL if dt > 0 else 0.
            fy = mdy / dt / FOCAL if dt > 0 else 0.
            row[1:7] = [1, fx, fy, tracked, ratio, int(tracked >= MIN_VALID)]
            # diagnostics
            mx, my = float(np.median(inl_old[:, 0])), float(np.median(inl_old[:, 1]))
            ax, ay = float(np.mean(inl_old[:, 0])), float(np.mean(inl_old[:, 1]))
            if M is not None:
                a, bb = M[0, 0], M[1, 0]
                s = float(np.hypot(a, bb)); th = float(np.arctan2(bb, a))
                tpp = M @ np.array([cx, cy, 1.0]) - np.array([cx, cy])
                fit_disp = (inl_old @ M[:, :2].T + M[:, 2]) - inl_old
                fmx = float(np.median(fit_disp[:, 0]))
            else:
                s = th = fmx = NAN; tpp = [NAN, NAN]
            row[7:] = [mx - cx, my - cy, ax - cx, ay - cy, mdx, mdy, s, th, M[0, 2] if M is not None else NAN,
                       M[1, 2] if M is not None else NAN, tpp[0], tpp[1], fmx, dt]
        rows.append(row)
        prev_gray, prev_time = gray, t
        if tracked < 20:
            prev_pts = cv2.goodFeaturesToTrack(gray, mask=None, **FEAT)
        else:
            prev_pts = good_new.reshape(-1, 1, 2)
    cols = ('t pub fx fy cnt inl valid offx_med offy_med offx_mean offy_mean mdx mdy s theta tx ty tpp_x tpp_y '
            'fitmed_dx dt').split()
    np.savez(out, rows=np.array(rows), cols=np.array(cols), K=np.array(K))
    print(len(rows), 'frames ->', out)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
