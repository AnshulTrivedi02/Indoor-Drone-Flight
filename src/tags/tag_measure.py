"""AprilTag measurement module (experiments T and L; user ruling 2026-10-08). PURE (no ROS): detection and vehicle-pose
estimation from the DOWNWARD camera. Independent of the frozen heading program and its OpenCV 4.6 pin: it uses
pupil_apriltags in its own venv (~/venv-tags).

Frames (all verified against ground truth on the room check flight; see METHODOLOGY "Tag module"):
  * World: Gazebo/room ENU (x east, y north, z up).
  * Body: FLU at base_link (x forward, y left, z up).
  * Camera (OpenCV optical): x right, y down, z along the optical axis. The downward camera is at body (0, 0, -0.25)
    with SDF pose rpy (0, 1.5708, 0): Gazebo's camera x (optical axis) points DOWN, its y left, its z FORWARD. So in the
    body frame: optical z = -z_body, optical x = -y_body (image right = body right), optical y = -x_body (image down =
    body backward). R_BODY_CAM below has these as columns.
  * Tag (AprilTag convention): origin at the tag centre, x right, y down (as the tag image is printed), z into the tag.
    The tag model maps its image onto the top face of a thin box; TEXTURE_CONVENTION states how image axes land on the
    model's x/y (determined empirically on the check flight and then FROZEN).
pupil_apriltags returns pose_R, pose_t with p_cam = pose_R p_tag + pose_t (tag_size = the black square edge).
Vehicle pose: T_world_body = T_world_tag * T_tag_cam * T_cam_body.
"""
import json, math
import numpy as np

R_BODY_CAM = np.array([[0.0, -1.0, 0.0],     # columns: optical x, y, z expressed in the body frame
                       [-1.0, 0.0, 0.0],
                       [0.0, 0.0, -1.0]])
T_BODY_CAM_POS = np.array([0.0, 0.0, -0.25])
TAG_SIZE_M = 0.4                          # black square edge (0.8 x the 0.5 m model side)
# Tag frame -> model frame (columns = tag x, y, z in the model frame) for each candidate texture mapping on the box top
# face. The frozen choice is set after the check flight (see find_convention()).
CONVENTIONS = {
    "u+x_v-y": np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]], float),   # image right -> +x, image down -> -y
    "u-x_v+y": np.array([[-1, 0, 0], [0, 1, 0], [0, 0, -1]], float),
    "u+y_v+x": np.array([[0, 1, 0], [1, 0, 0], [0, 0, -1]], float),
    "u-y_v-x": np.array([[0, -1, 0], [-1, 0, 0], [0, 0, -1]], float),
    "u+x_v+y": np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]], float),      # mirrored candidates (z out of the floor)
    "u-x_v-y": np.array([[-1, 0, 0], [0, -1, 0], [0, 0, 1]], float),
}
TEXTURE_CONVENTION = "u-y_v-x"           # FROZEN 2026-10-08 from the room check flight: median pos err 0.013 m, |yaw| 0.02 deg
#                                           (every other candidate >= 0.38 m and 60-180 deg; METHODOLOGY "Tag module")


def rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


def load_map(path):
    m = json.load(open(path))
    return {t["id"]: {"p": np.array([t["x"], t["y"], t["z"]]), "yaw": math.radians(t["yaw_deg"])} for t in m["tags"]}


class TagDetector:
    def __init__(self, fx, fy, cx, cy, tag_size=TAG_SIZE_M, family="tag36h11", decimate=1.0, threads=1):
        from pupil_apriltags import Detector
        self.det = Detector(families=family, quad_decimate=decimate, nthreads=threads)
        self.cam = (fx, fy, cx, cy); self.tag_size = tag_size

    def detect(self, gray):
        """[(id, R_cam_tag 3x3, t_cam_tag (3,), corners (4,2), centre (2,), decision_margin, hamming)]"""
        out = []
        for d in self.det.detect(gray, estimate_tag_pose=True, camera_params=self.cam, tag_size=self.tag_size):
            out.append((int(d.tag_id), np.array(d.pose_R), np.array(d.pose_t).ravel(), np.array(d.corners),
                        np.array(d.center), float(d.decision_margin), int(d.hamming)))
        return out


def detect_pose_roi(det, gray, want_id, margin=40):
    """Experiment H (2026-10-08): detect WITHOUT pose on the full frame, then estimate the pose of `want_id` only, by
    running the same detector WITH pose on a crop around it (principal point shifted by the crop origin). Reason: from
    the far spawn a floor tag at a grazing angle is in view; pupil_apriltags' pose solver fails on it ("more than one
    new minima", an improper R) and afterwards the detector's results on IDENTICAL frames change (the wall tag is lost)
    and it can segfault, i.e. its state is corrupted. Returns detect()'s tuples for want_id only (pose in the full
    frame's camera); [] if absent."""
    fx, fy, cx, cy = det.cam
    out = []
    for d in det.det.detect(gray):
        if int(d.tag_id) != want_id:
            continue
        c = np.array(d.corners); x0 = max(int(c[:, 0].min()) - margin, 0); y0 = max(int(c[:, 1].min()) - margin, 0)
        x1 = min(int(c[:, 0].max()) + margin + 1, gray.shape[1]); y1 = min(int(c[:, 1].max()) + margin + 1, gray.shape[0])
        crop = np.ascontiguousarray(gray[y0:y1, x0:x1])
        for e in det.det.detect(crop, estimate_tag_pose=True, camera_params=(fx, fy, cx - x0, cy - y0), tag_size=det.tag_size):
            if int(e.tag_id) != want_id:
                continue
            off = np.array([x0, y0], float)
            out.append((want_id, np.array(e.pose_R), np.array(e.pose_t).ravel(), np.array(e.corners) + off,
                        np.array(e.center) + off, float(e.decision_margin), int(e.hamming)))
    return out


def vehicle_pose(tag_world, R_ct, t_ct, convention=None):
    """World pose of the body from one tag: (p_world_body (3,), R_world_body 3x3)."""
    M = CONVENTIONS[convention or TEXTURE_CONVENTION]
    R_wt = rz(tag_world["yaw"]) @ M; p_wt = tag_world["p"]
    R_tc = R_ct.T; p_tc = -R_ct.T @ t_ct                         # camera in the tag frame
    R_cb = R_BODY_CAM.T; p_cb = -R_BODY_CAM.T @ T_BODY_CAM_POS   # body in the camera frame
    R_wb = R_wt @ R_tc @ R_cb
    p_wb = p_wt + R_wt @ (p_tc + R_tc @ p_cb)
    return p_wb, R_wb


def yaw_of(R):
    return math.atan2(R[1, 0], R[0, 0])


def find_convention(samples, tag_map):
    """samples: [(id, R_ct, t_ct, p_true (3,), yaw_true)]. Returns {convention: (median pos err m, median |yaw err| deg)}."""
    res = {}
    for k in CONVENTIONS:
        pe, ye = [], []
        for i, R, t, p_true, yaw_true in samples:
            p, Rw = vehicle_pose(tag_map[i], R, t, k)
            pe.append(np.linalg.norm(p - p_true)); ye.append(abs((yaw_of(Rw) - yaw_true + math.pi) % (2 * math.pi) - math.pi))
        res[k] = (float(np.median(pe)), float(np.degrees(np.median(ye))))
    return res


# ---------------------------------------------------------------------------------------------------------------------
# Experiment H (wall tag, FORWARD camera; ruling 2026-10-08). Added; the floor-tag functions above are unchanged (T).
# Forward camera (iris_fwd_standoffs): level, along body +x, at body (0.15, 0, 0). Optical frame in body FLU:
# optical z = +x_body, optical x = -y_body (image right = body right), optical y = -z_body (image down = body down).
R_BODY_CAM_FWD = np.array([[0.0, 0.0, 1.0],     # columns: optical x, y, z expressed in the body frame
                           [-1.0, 0.0, 0.0],
                           [0.0, -1.0, 0.0]])
T_BODY_CAM_FWD_POS = np.array([0.15, 0.0, 0.0])


def rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], float)


# Candidate image->tag-model mappings for a VERTICAL tag (the floor CONVENTIONS composed with the mount rotation are
# tested by find_convention_full on the S0 check flight and then FROZEN, as TEXTURE_CONVENTION was for the floor).
def vehicle_pose_full(R_wt, p_wt, R_ct, t_ct, R_body_cam=R_BODY_CAM_FWD, t_body_cam=T_BODY_CAM_FWD_POS):
    """World pose of the body from one detection, for a tag of known world pose (R_wt: tag frame -> world, the tag
    frame in AprilTag convention: x right, y down, z into the tag) and any camera mount. Returns (p_wb, R_wb)."""
    R_tc = R_ct.T; p_tc = -R_ct.T @ t_ct
    R_cb = R_body_cam.T; p_cb = -R_body_cam.T @ t_body_cam
    R_wb = R_wt @ R_tc @ R_cb
    return p_wt + R_wt @ (p_tc + R_tc @ p_cb), R_wb


def wall_tag_R_wt(mount_rpy, convention):
    """Tag-frame -> world rotation for a model mounted with SDF rpy (roll, pitch, yaw) whose top face carries the
    texture under `convention` (a key of CONVENTIONS: the texture's axes on the model's top face)."""
    r, p, y = mount_rpy
    R_mount = rz(y) @ (np.array([[math.cos(p), 0, math.sin(p)], [0, 1, 0], [-math.sin(p), 0, math.cos(p)]])) @ rx(r)
    return R_mount @ CONVENTIONS[convention]


def find_convention_full(samples, mount_rpy, p_wt):
    """samples: [(R_ct, t_ct, p_true (3,), yaw_true)] for ONE tag. {convention: (median pos err m, median |yaw err| deg)}."""
    res = {}
    for k in CONVENTIONS:
        R_wt = wall_tag_R_wt(mount_rpy, k); pe, ye = [], []
        for R, t, p_true, yaw_true in samples:
            p, Rw = vehicle_pose_full(R_wt, p_wt, R, t)
            pe.append(np.linalg.norm(p - p_true)); ye.append(abs((yaw_of(Rw) - yaw_true + math.pi) % (2 * math.pi) - math.pi))
        res[k] = (float(np.median(pe)), float(np.degrees(np.median(ye))))
    return res
