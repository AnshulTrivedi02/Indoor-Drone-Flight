"""Forward-camera measurements (Phase 3): heading from the corridor vanishing point, and
yaw rate from horizontal forward-image flow. Pure image processing: no ground truth and
no other sensor enters here. METHODOLOGY "Phase 3 — forward-camera measurements".

Conventions. Camera optical frame: u right, v down; K from /forward_camera/camera_info
(fx = fy = 554.38, cx = 320, cy = 240, no distortion). The camera is rigid and level,
looking along body +x. psi = heading of the body relative to the corridor axis, in the
ENU sense (positive = nose rotated anticlockwise seen from above, i.e. to the left).
Rotating the nose left moves the corridor's vanishing point RIGHT in the image, so
    psi = atan((u_vp - cx) / fx)
and the matching yaw rate is omega = d(psi)/dt = (du / fx) / dt for the horizontal image
motion du of distant scene points (small-angle). Roll and pitch are not compensated:
cruise pitch is ~0.02 deg and roll is similarly small, and with the VP near the image
centre their effect on u_vp is second order (stated as a limitation).
"""
import math
import numpy as np
import cv2

FX, CX, CY = 554.3827056884766, 320.0, 240.0

# Fixed method constants (standard values, NOT tuned): LSD defaults; segments shorter
# than MIN_LEN_PX, or within ANGLE_EXCL_DEG of horizontal or vertical, are discarded
# (horizontals are the cross-corridor lines; verticals are wall bars and door-like
# edges, and neither points at the vanishing point); RANSAC inlier = the segment's
# direction is within INLIER_DEG of the direction from its midpoint to the VP.
MIN_LEN_PX = 15.0
ANGLE_EXCL_DEG = 5.0
INLIER_DEG = 1.5
RANSAC_ITERS = 300
# VP hypotheses must lie inside the image (W x H). A forward camera looking along the
# corridor sees the corridor VP in frame for any heading within the half-FOV (+-30 deg);
# beyond that there is no heading measurement anyway. This rejects the checkerboard
# floor's diagonal families, whose VPs sit near +-45 deg, outside the frame.
IMG_W, IMG_H = 640, 480
# ...and within HORIZON_BAND_DEG of the image's centre row. The camera is mounted level
# and cruise pitch is ~0.02 deg (std 0.17 deg), so the corridor VP sits on the horizon
# row to within a few pixels; beyond +-5 deg of pitch the measurement is simply
# unavailable. This rejects checkerboard aliasing families converging ~11 deg below the
# horizon, which otherwise outscore the four wall/floor/ceiling junctions of the
# plain-wall worlds. Both image constraints were added after they failed on CALIBRATION
# frames (METHODOLOGY, Phase 3); they are geometric priors, not fitted thresholds.
HORIZON_BAND_DEG = 5.0
_V_BAND = FX * math.tan(math.radians(HORIZON_BAND_DEG))

_lsd = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD)


def segments(img):
    """LSD segments as (N, 4) x1 y1 x2 y2, filtered by length and orientation."""
    out = _lsd.detect(img)[0]
    if out is None:
        return np.zeros((0, 4))
    s = out.reshape(-1, 4).astype(np.float64)
    d = s[:, 2:] - s[:, :2]
    length = np.hypot(d[:, 0], d[:, 1])
    ang = np.degrees(np.arctan2(np.abs(d[:, 1]), np.abs(d[:, 0])))       # 0 = horizontal
    keep = (length >= MIN_LEN_PX) & (ang > ANGLE_EXCL_DEG) & (ang < 90 - ANGLE_EXCL_DEG)
    return s[keep]


def _residual_deg(s, p):
    """Angle between each segment and the line from its midpoint to point p (deg)."""
    mid = 0.5 * (s[:, :2] + s[:, 2:])
    d = s[:, 2:] - s[:, :2]
    q = p[None, :] - mid
    cross = np.abs(d[:, 0] * q[:, 1] - d[:, 1] * q[:, 0])
    dot = np.abs(d[:, 0] * q[:, 0] + d[:, 1] * q[:, 1])
    return np.degrees(np.arctan2(cross, dot))


def _intersect(a, b):
    la = np.cross([a[0], a[1], 1.0], [a[2], a[3], 1.0])
    lb = np.cross([b[0], b[1], 1.0], [b[2], b[3], 1.0])
    p = np.cross(la, lb)
    if abs(p[2]) < 1e-9:
        return None
    return p[:2] / p[2]


def _balanced(s, L, inl, p):
    """Two-sided support: 2 x min(inlier length left of the VP, right of it). The
    corridor VP is supported from both sides (left and right walls and junctions); the
    checkerboard floor's spurious families are one-sided. Third prior added on
    CALIBRATION frames (METHODOLOGY, Phase 3)."""
    mid_u = 0.5 * (s[:, 0] + s[:, 2])
    return 2.0 * min(L[inl & (mid_u < p[0])].sum(), L[inl & (mid_u > p[0])].sum())


def vanishing_point(s, seed=0, inlier_deg=INLIER_DEG):
    """RANSAC VP over segments (length-weighted sampling, balanced two-sided scoring),
    then least-squares refinement on the inliers. Returns dict or None."""
    n = len(s)
    if n < 2:
        return None
    L = np.hypot(s[:, 2] - s[:, 0], s[:, 3] - s[:, 1])
    rng = np.random.default_rng(seed)
    pr = L / L.sum()
    best, best_score = None, 0.0
    for _ in range(RANSAC_ITERS):
        i, j = rng.choice(n, 2, replace=False, p=pr)
        p = _intersect(s[i], s[j])
        if p is None or not np.all(np.isfinite(p)) or not (0 <= p[0] < IMG_W and abs(p[1] - CY) <= _V_BAND):
            continue
        inl = _residual_deg(s, p) <= inlier_deg
        sc = _balanced(s, L, inl, p)
        if sc > best_score:
            best, best_score = inl, sc
    if best is None or best.sum() < 2 or best_score <= 0:
        return None
    # refine: least squares on the inlier lines (normal form n.x = c), length-weighted
    si, w = s[best], L[best]
    d = si[:, 2:] - si[:, :2]
    nrm = np.stack([-d[:, 1], d[:, 0]], 1) / np.hypot(d[:, 0], d[:, 1])[:, None]
    c = (nrm * si[:, :2]).sum(1)
    A = nrm * w[:, None] ** 0.5
    b = c * w ** 0.5
    p, *_ = np.linalg.lstsq(A, b, rcond=None)
    inl = _residual_deg(s, p) <= inlier_deg
    mid_u = 0.5 * (s[inl, 0] + s[inl, 2])
    return {"u": float(p[0]), "v": float(p[1]), "n_inl": int(inl.sum()),
            "len_inl": float(L[inl].sum()), "support": float(_balanced(s, L, inl, p)),
            "n_left": int((mid_u < p[0]).sum()), "n_right": int((mid_u > p[0]).sum())}


def heading(img, seed=0, inlier_deg=INLIER_DEG, segs=None):
    """Per-frame heading. Returns psi_deg (None if no VP) and the support statistics.
    A heading is VALID when support >= the calibrated S_MIN (balanced two-sided inlier
    length, px); otherwise the output is "no measurement" (this is also what happens at
    the end wall, where the junctions shorten and vanish)."""
    vp = vanishing_point(segments(img) if segs is None else segs, seed, inlier_deg)
    if vp is None:
        return {"psi_deg": None, "u": None, "v": None, "n_inl": 0, "len_inl": 0.0,
                "support": 0.0, "n_left": 0, "n_right": 0}
    vp["psi_deg"] = math.degrees(math.atan((vp["u"] - CX) / FX))
    return vp


def yaw_rate(prev, img, vp_u, vp_v, dt, half_box):
    """Yaw rate (deg/s) from the median horizontal LK flow of Shi-Tomasi corners inside a
    box of half-size half_box px around the previous frame's vanishing point.

    PARALLAX LIMITATION: forward translation adds radial flow away from the focus of
    expansion (~ the VP when flying along the corridor), with horizontal component
    (u - u_foe) * V / Z. Restricting to a box around the VP keeps |u - u_foe| small and
    Z large, and the median over a roughly symmetric box cancels the remainder to first
    order. It does not remove it: residual parallax is a bias that depends on the
    feature layout."""
    h, w = img.shape
    mask = np.zeros_like(prev)
    u0, u1 = int(max(0, vp_u - half_box)), int(min(w, vp_u + half_box))
    v0, v1 = int(max(0, vp_v - half_box)), int(min(h, vp_v + half_box))
    if u1 - u0 < 4 or v1 - v0 < 4:
        return {"omega_dps": None, "n_trk": 0}
    mask[v0:v1, u0:u1] = 255
    p0 = cv2.goodFeaturesToTrack(prev, maxCorners=100, qualityLevel=0.01, minDistance=5, mask=mask)
    if p0 is None:
        return {"omega_dps": None, "n_trk": 0}
    p1, st, _ = cv2.calcOpticalFlowPyrLK(prev, img, p0, None, winSize=(21, 21), maxLevel=3)
    ok = st.ravel() == 1
    if ok.sum() == 0:
        return {"omega_dps": None, "n_trk": 0}
    du = (p1[ok, 0, 0] - p0[ok, 0, 0])
    return {"omega_dps": float(math.degrees(np.median(du) / FX / dt)), "n_trk": int(ok.sum())}
