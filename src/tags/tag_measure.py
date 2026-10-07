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
