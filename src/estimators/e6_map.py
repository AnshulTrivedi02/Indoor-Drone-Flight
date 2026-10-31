#!/usr/bin/env python3
"""E6 (tier-1 extension experiment "map once, fly again", pre-registered in docs/thesis/tier1/e6_preregistration.md):
a SUPPLIED tag map for the Experiment 2 (repo "T") replays room_ukf_replay.py / room_fgo_replay.py (flag --tag-map).

Nothing here runs unless --tag-map is given to one of those replays; without it their code path is unchanged (gates
G0-UKF and G-E4, byte identity, e6_preregistration.md §7).

What the flag does (e6_preregistration.md §2):
  * the replays read /tags/sent: the fixes the tag bridge SENT in the flight, each the vehicle (x, y, yaw) in the world
    frame computed with the TRUE (surveyed) pose of the tag named in frame_id "tag_<id>" (tag_bridge.py:87-99);
  * the bridge's choice of WHICH detection to send (subset, central third, largest decision margin) never depends on the
    map values, so a bridge holding the supplied map would have sent the same detections, re-expressed with the
    supplied tag pose. For a tag flat on the floor (z, roll, pitch known: the flat-floor assumption of Experiment 3)
    that re-expression is exact in the plane:
        p' = t'_j + Rz(th'_j - th_j) (p - t_j),      yaw' = yaw + (th'_j - th_j)
    with (t_j, th_j) the true and (t'_j, th'_j) the supplied position and yaw of tag j;
  * the supplied map is treated EXACTLY as the surveyed map: fixed, known landmarks; the tag noise is unchanged
    (TAG_SIGMA_POS 0.05 m, TAG_SIGMA_YAW 5 deg) and no map uncertainty is added.
Map file: the room_tags_map.json layout ({"tags": [{"id", "x", "y", "z", "yaw_deg", ...}]}), world (Gazebo ENU) frame;
an optional "yaw_rad" per tag is used in preference to yaw_deg (no degree round trip). Every id of the true map must be
present.

Self-test (venv-tags or venv-evo; reads one bag, writes nothing):
  python3 src/estimators/e6_map.py --selftest T_A_r1
checks (1) the true map reproduces /tags/sent from the matching /tags/raw detection (same stamp, id) through
tag_measure.vehicle_pose, and (2) the planar re-expression equals vehicle_pose recomputed from /tags/raw with a
perturbed map, to round-off."""
import hashlib, json, math, os, re, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TRUE_MAP = os.path.join(HERE, "..", "..", "sim", "worlds", "room_tags_map.json")
TIER1_DATA_ROOT = os.path.expanduser("~/thesis_data/tier1")
TRIALS_ROOT = os.path.expanduser("~/thesis_data/trials")
NAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")


def refuse(msg):
    sys.exit(f"[e6] REFUSED: {msg}")


def _under(path, root):
    path, root = os.path.realpath(path), os.path.realpath(root)
    return path == root or path.startswith(root + os.sep)


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def load_map(path):
    """{id: (x, y, yaw_rad)} from a room_tags_map.json-layout file."""
    m = json.load(open(path))
    return {int(t["id"]): (float(t["x"]), float(t["y"]),
                           float(t["yaw_rad"]) if "yaw_rad" in t else math.radians(float(t["yaw_deg"]))) for t in m["tags"]}


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def remap_fix(fix, true_tag, map_tag):
    """(x, y, yaw) world fix computed with true_tag (x, y, yaw) -> the same detection re-expressed with map_tag."""
    x, y, yaw = fix
    tx, ty, th = true_tag; mx, my, mh = map_tag
    d = mh - th; c, s = math.cos(d), math.sin(d); dx, dy = x - tx, y - ty
    return (mx + c * dx - s * dy, my + s * dx + c * dy, wrap(yaw + d))


def sent_ids(bagdir):
    """[(stamp, id)] of /tags/sent in bag order."""
    from rosbags.rosbag2 import Reader
    from rosbags.typesys import Stores, get_typestore
    ts = get_typestore(Stores.ROS2_JAZZY); out = []
    with Reader(bagdir) as r:
        conns = [c for c in r.connections if c.topic == "/tags/sent"]
        for con, _, raw in r.messages(connections=conns):
            m = ts.deserialize_cdr(raw, con.msgtype)
            out.append((m.header.stamp.sec + m.header.stamp.nanosec * 1e-9, int(m.header.frame_id.split("_")[1])))
    return out


def parse_args(argv):
    """(map_path, name) from --tag-map FILE --tag-map-name NAME, or (None, None) when neither is given."""
    def val(f):
        if f not in argv:
            return None
        i = argv.index(f)
        if i + 1 >= len(argv):
            refuse(f"{f} needs a value")
        return argv[i + 1]
    mp, nm = val("--tag-map"), val("--tag-map-name")
    if mp is None and nm is None:
        return None, None
    if mp is None or nm is None:
        refuse("--tag-map and --tag-map-name go together")
    if not NAME_RE.match(nm):
        refuse(f"--tag-map-name {nm!r}: letters, digits, _ . - only")
    if not os.path.isfile(mp):
        refuse(f"--tag-map {mp!r} not found")
    return os.path.abspath(mp), nm


def check_out(out):
    """A supplied-map run writes only under ~/thesis_data/tier1, never under ~/thesis_data/trials, never over a
    non-empty directory."""
    if not _under(out, TIER1_DATA_ROOT):
        refuse(f"output {out!r} is not under {TIER1_DATA_ROOT}")
    if _under(out, TRIALS_ROOT):
        refuse(f"output {out!r} resolves under {TRIALS_ROOT}")
    if os.path.lexists(out) and (not os.path.isdir(out) or os.listdir(out)):
        refuse(f"output {out!r} exists and is not empty (no overwrite)")


def apply(ev, bagdir, map_path, true_map_path=TRUE_MAP):
    """Re-express every ("tag", (x, y, yaw)) event of ev (built in bag order from /tags/sent by the replay) with the
    supplied map. Returns (new ev, provenance dict). Refuses on any mismatch between the replay's tag events and the
    bag's /tags/sent (count, order, stamps)."""
    true_map, sup = load_map(true_map_path), load_map(map_path)
    if set(sup) != set(true_map):
        refuse(f"supplied map ids {sorted(sup)} != true map ids {sorted(true_map)}")
    ids = sent_ids(bagdir)
    tags = [i for i, e in enumerate(ev) if e[1] == "tag"]
    if len(tags) != len(ids):
        refuse(f"{len(tags)} tag events but {len(ids)} /tags/sent messages")
    out = list(ev); per = {}
    for k, (i, (ts_, tid)) in enumerate(zip(tags, ids)):
        t, _, fix = ev[i]
        if t != ts_:
            refuse(f"tag event {k}: stamp {t!r} != /tags/sent stamp {ts_!r}")
        new = remap_fix(fix, true_map[tid], sup[tid])
        out[i] = (t, "tag", new)
        p = per.setdefault(str(tid), {"n": 0, "max_shift_m": 0.0})
        p["n"] += 1; p["max_shift_m"] = max(p["max_shift_m"], math.hypot(new[0] - fix[0], new[1] - fix[1]))
    dmap = {str(j): {"dx_m": sup[j][0] - true_map[j][0], "dy_m": sup[j][1] - true_map[j][1],
                     "dyaw_deg": math.degrees(wrap(sup[j][2] - true_map[j][2]))} for j in sorted(true_map)}
    return out, {"tag_map": map_path, "tag_map_sha256": sha256(map_path), "true_map": os.path.abspath(true_map_path),
                 "true_map_sha256": sha256(true_map_path), "n_fixes_remapped": len(tags), "per_tag": per,
                 "map_minus_true": dmap,
                 "rule": "p' = t'_j + Rz(th'_j - th_j)(p - t_j), yaw' = yaw + th'_j - th_j; tag noise unchanged"}


def selftest(trial):
    """Read-only check on one stored flight (see the module docstring)."""
    sys.path.insert(0, os.path.join(HERE, "..", "tags")); import tag_measure as TM
    from rosbags.rosbag2 import Reader
    from rosbags.typesys import Stores, get_typestore
    ts = get_typestore(Stores.ROS2_JAZZY)
    tm = TM.load_map(TRUE_MAP); true_map = load_map(TRUE_MAP)
    rng = np.random.default_rng(0)
    pert = {j: (x + rng.uniform(-0.2, 0.2), y + rng.uniform(-0.2, 0.2), wrap(h + math.radians(rng.uniform(-5, 5))))
            for j, (x, y, h) in true_map.items()}
    raw, sent = {}, []
    with Reader(os.path.join(TRIALS_ROOT, trial, "bag")) as r:
        conns = [c for c in r.connections if c.topic in ("/tags/raw", "/tags/sent")]
        for con, _, b in r.messages(connections=conns):
            m = ts.deserialize_cdr(b, con.msgtype); t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
            tid = int(m.header.frame_id.split("_")[1])
            if con.topic == "/tags/raw":
                q = m.pose.orientation; w, x, y, z = q.w, q.x, q.y, q.z
                R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                              [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                              [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])
                raw[(t, tid)] = (R, np.array([m.pose.position.x, m.pose.position.y, m.pose.position.z]))
            else:
                q = m.pose.pose.orientation
                sent.append((t, tid, (m.pose.pose.position.x, m.pose.pose.position.y, 2 * math.atan2(q.z, q.w))))
    e_true, e_pert = [], []
    for t, tid, fix in sent:
        R, tt = raw[(t, tid)]
        p, Rw = TM.vehicle_pose(tm[tid], R, tt)
        e_true.append(max(abs(p[0] - fix[0]), abs(p[1] - fix[1]), abs(wrap(TM.yaw_of(Rw) - fix[2]))))
        mt = {"p": np.array([pert[tid][0], pert[tid][1], tm[tid]["p"][2]]), "yaw": pert[tid][2]}
        p2, R2 = TM.vehicle_pose(mt, R, tt)
        f2 = remap_fix(fix, true_map[tid], pert[tid])
        e_pert.append(max(abs(p2[0] - f2[0]), abs(p2[1] - f2[1]), abs(wrap(TM.yaw_of(R2) - f2[2]))))
    res = {"trial": trial, "n_sent": len(sent), "true_map_vs_sent_max_abs": float(max(e_true)),
           "perturbed_remap_vs_vehicle_pose_max_abs": float(max(e_pert)),
           "note": "max over fixes of max(|dx| m, |dy| m, |dyaw| rad); the true-map term includes the /tags/raw "
                   "quaternion round trip"}
    print(json.dumps(res, indent=1))
    ok = res["true_map_vs_sent_max_abs"] < 1e-6 and res["perturbed_remap_vs_vehicle_pose_max_abs"] < 1e-6
    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--selftest":
        sys.exit(selftest(sys.argv[2]))
    sys.exit(__doc__)
