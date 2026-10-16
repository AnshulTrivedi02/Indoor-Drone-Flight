#!/usr/bin/env python3
"""Top-down schematics of every simulation world, generated FROM THE SDF (docs/thesis/world_images/schematics/).

Geometry: every <include> and inline <model> of sim/worlds/<world>.sdf is resolved (sim/models first, then
~/ardupilot_gazebo/models, as GZ_SIM_RESOURCE_PATH orders them), and each <visual> (box, plane, or a COLLADA mesh's
bounding box) is placed in 3-D with the full pose chain world <- include/model <- link <- visual (roll, pitch, yaw;
`degrees="true"` honoured), then projected onto the floor. No dimension is typed in here: walls, floor tiles, the
ceiling / roof, tags (their ids from the model name), the occluder and the spawn all come from the files.

Routes come from the mission/profile files, not from flown data:
  corridor cruise       the world's line in batches/*.conf (velocity x duration along +y from the spawn; fly_trial.py
                        cruises velocity-only on LOCAL_NED north = world +y); corridor_textured_half_fwdc from
                        sim/tools/closed_loop_run.sh (--velocity / --duration)
  T / L laps            LAPS=<n>,<side>,<speed> in tools/run_expT.sh (fly_trial.laps(): N -> E -> S -> W from the spawn)
  tagchar               batches/tagchar.conf (velocity x duration north from the spawn)
  O                     OUTBACK=<align_m>,<align_speed>,<out_m>,<speed>,<gate_n> in tools/run_expO.sh
  H                     batches/expH/*.json; tag-frame W (N_W = world y - WALL_P_y, E_W = world x, WALL_P from
                        tag_bridge_fwd.py), except s0a/s0b which are flown in the world frame (fly_trial.py)
LOCAL_NED north = world +y, east = world +x (origin at world (0, 0)).

Drawing offsets (NOT geometry): the O out / back legs are drawn 0.6 m either side of x = 0 and the tagchar line 0.25 m
west of the lap line so the overlapping legs stay visible; all were flown at the spawn's x.

Colours (Okabe-Ito; the estimator colours #0072B2 / #009E73 / #D55E00 are NOT used, they mean EKF3 / UKF / FGO in the
thesis figures): planned route #E69F00 (orange); AprilTags #CC79A7 (reddish purple); ceiling / roof outline #56B4E9
(sky blue, dashed); references (GNSS gate, transition boundary, room box) #999999 (grey, the thesis's reference grey);
walls #5e5e5e (the thesis figures' wall grey); spawn #111111.

Run: python3 sim/tools/world_schematics.py --out docs/thesis/world_images/schematics [world ...]
"""
import argparse, glob, json, math, os, re, xml.etree.ElementTree as ET
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
from matplotlib.collections import PatchCollection

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODEL_PATHS = [os.path.join(REPO, "sim", "models"), os.path.expanduser("~/ardupilot_gazebo/models")]
ROUTE, TAG, CEIL, REF, WALL, INK, INK2 = "#E69F00", "#CC79A7", "#56B4E9", "#999999", "#5e5e5e", "#111111", "#4d4d4d"
plt.rcParams.update({"font.size": 9.5, "axes.titlesize": 11, "axes.labelsize": 9.5, "axes.edgecolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "text.color": INK, "axes.labelcolor": INK,
                     "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42,
                     "savefig.facecolor": "white", "figure.facecolor": "white"})


# ---------------------------------------------------------------------------------------------------- SDF geometry
def pose_of(el):
    """4x4 transform of an element's <pose> child (identity if absent)."""
    p = el.find("pose") if el is not None else None
    if p is None or not (p.text or "").strip():
        return np.eye(4)
    v = [float(t) for t in p.text.split()]
    v += [0.0] * (6 - len(v))
    if p.get("degrees") == "true":
        v[3:] = [math.radians(a) for a in v[3:]]
    r, pi, y = v[3:]
    cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(pi), math.sin(pi), math.cos(y), math.sin(y)
    R = np.array([[cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
                  [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
                  [-sp, cp * sr, cp * cr]])
    T = np.eye(4); T[:3, :3] = R; T[:3, 3] = v[:3]
    return T


def model_dir(uri):
    name = uri.replace("model://", "").strip("/")
    for base in MODEL_PATHS:
        d = os.path.join(base, name)
        if os.path.exists(os.path.join(d, "model.sdf")):
            return d
    raise FileNotFoundError(uri)


def dae_bbox(path):
    """Axis-aligned bbox (2 x 3) of a COLLADA mesh: positions x the node <matrix> (the airfield plane)."""
    txt = open(path).read()
    pos = np.array(re.search(r'<float_array id="[^"]*positions-array"[^>]*>([^<]*)', txt).group(1).split(), float)
    pos = pos.reshape(-1, 3)
    m = re.search(r'<node id="[^"]*"[^>]*>\s*<matrix[^>]*>([^<]*)</matrix>', txt)
    M = np.array(m.group(1).split(), float).reshape(4, 4) if m else np.eye(4)
    P = (M @ np.c_[pos, np.ones(len(pos))].T).T[:, :3]
    return np.array([P.min(0), P.max(0)])


def visuals_of_model(model_el, T_model, mdir, model_name, out):
    for link in model_el.findall("link"):
        T_link = T_model @ pose_of(link)
        for vis in link.findall("visual"):
            T = T_link @ pose_of(vis)
            g = vis.find("geometry")
            mat = vis.find("material")
            albedo = mat.findtext(".//albedo_map") if mat is not None else None
            diff = mat.findtext("diffuse") if mat is not None else None
            if g.find("box") is not None:
                sx, sy, sz = (float(t) for t in g.find("box/size").text.split())
                c = np.array([[a, b, cc] for a in (-sx / 2, sx / 2) for b in (-sy / 2, sy / 2) for cc in (-sz / 2, sz / 2)])
                kind = "box"
            elif g.find("plane") is not None:
                sx, sy = (float(t) for t in g.find("plane/size").text.split())
                c = np.array([[a, b, 0.0] for a in (-sx / 2, sx / 2) for b in (-sy / 2, sy / 2)])
                kind = "plane"
            elif g.find("mesh") is not None and mdir is not None:
                uri = g.find("mesh/uri").text
                f = os.path.join(model_dir("model://" + uri.replace("model://", "").split("/")[0]),
                                 *uri.replace("model://", "").split("/")[1:])
                if not f.endswith(".dae"):
                    continue
                bb = dae_bbox(f)
                c = np.array([[a, b, cc] for a in bb[:, 0] for b in bb[:, 1] for cc in bb[:, 2]])
                kind = "mesh"
            else:
                continue
            W = (T @ np.c_[c, np.ones(len(c))].T).T[:, :3]
            out.append(dict(model=model_name, link=link.get("name"), visual=vis.get("name"), kind=kind, pts=W,
                            zmin=W[:, 2].min(), zmax=W[:, 2].max(), albedo=albedo, diffuse=diff,
                            uri_dir=os.path.basename(mdir) if mdir else None))


def parse_world(world):
    root = ET.parse(os.path.join(REPO, "sim", "worlds", world + ".sdf")).getroot()
    w = root.find("world")
    vis, spawn = [], None
    for inc in w.findall("include"):
        uri = inc.findtext("uri").strip(); mdir = model_dir(uri); T = pose_of(inc)
        name = inc.findtext("name") or os.path.basename(mdir)
        if os.path.basename(mdir).startswith("iris"):
            spawn = dict(xy=T[:2, 3], yaw=math.atan2(T[1, 0], T[0, 0]), model=os.path.basename(mdir), name=name)
            continue
        m = ET.parse(os.path.join(mdir, "model.sdf")).getroot().find("model")
        visuals_of_model(m, T @ pose_of(m), mdir, name, vis)
    for m in w.findall("model"):
        visuals_of_model(m, pose_of(m), None, m.get("name"), vis)
    return w.get("name"), vis, spawn


def classify(v):
    name, d = v["model"], (v["uri_dir"] or "")
    if v["model"] == "axes":
        return None                                           # upstream axis-line visuals (1 cm boxes), not drawn
    if d.startswith("apriltag36h11_"):
        return "tag_wall" if v["zmax"] - v["zmin"] > 0.1 else "tag_floor"
    if name == "occluder":
        return "occluder"
    if v["kind"] in ("plane", "mesh"):
        a = (v["albedo"] or "")
        if "checker" in a: return "floor_checker"
        if "runway" in a: return "runway"
        if "Grass" in a: return "grass"
        return "floor_blank"
    if v["kind"] == "box":
        if v["zmin"] > 2.5:
            return "ceiling"
        if v["zmax"] - v["zmin"] > 1.0:
            return "wall_lined" if (v["albedo"] or "") else "wall"
    return None


def checker_square_m(v):
    """Checker square size from the texture itself: tile width / number of squares across the albedo image."""
    from PIL import Image
    f = os.path.join(model_dir("model://" + v["uri_dir"]), v["albedo"]) if not v["albedo"].startswith("model://") \
        else os.path.join(model_dir("model://" + v["albedo"][8:].split("/")[0]), *v["albedo"][8:].split("/")[1:])
    a = np.array(Image.open(f).convert("L"))[a_row(f)]
    n = len(np.nonzero(np.diff(a.astype(int)))[0]) + 1
    return (v["pts"][:, 0].max() - v["pts"][:, 0].min()) / n


def a_row(f):
    return 5


def hull2(P):
    P = sorted(set(map(tuple, np.round(P[:, :2], 6))))
    if len(P) < 3:
        return np.array(P)
    def cross(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in P:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(P):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return np.array(lo[:-1] + up[:-1])


# ------------------------------------------------------------------------------------------------------- routes
def conf_cruise(world):
    """(velocity, altitude, duration, source) for a corridor world: its first line in batches/*.conf, or closed_loop_run.sh."""
    for f in sorted(glob.glob(os.path.join(REPO, "batches", "*.conf"))):
        for ln in open(f):
            t = ln.split()
            if len(t) >= 5 and not ln.lstrip().startswith("#") and t[0] == world:
                return float(t[1]), float(t[2]), float(t[3]), os.path.relpath(f, REPO) + " (" + t[4] + ")"
    s = open(os.path.join(REPO, "sim", "tools", "closed_loop_run.sh")).read()
    m = re.search(r'--velocity (\S+) --altitude "\$\{ALT:-([\d.]+)\}" --duration (\d+)', s)
    return float(m.group(1)), float(m.group(2)), float(m.group(3)), "sim/tools/closed_loop_run.sh"


def env_param(script, key):
    m = re.search(key + r"=([\d.,]+)", open(os.path.join(REPO, script)).read())
    return [float(x) for x in m.group(1).split(",")]


def wall_p():
    m = re.search(r"WALL_P = np.array\(\[([^\]]*)\]\)", open(os.path.join(REPO, "tag_bridge_fwd.py")).read())
    return [float(x) for x in m.group(1).split(",")]


def h_profile_path(prof, frame_w):
    """Waypoints (world x, y) of an H profile: the wait_fix point, then every move."""
    pts = []
    wp = wall_p()
    for seg in json.load(open(os.path.join(REPO, "batches", "expH", prof))):
        p = seg.get("near") if seg["type"] == "wait_fix" else seg.get("to") if seg["type"] == "move" else None
        if p is None:
            continue
        n, e = p
        pts.append((e, n + wp[1]) if frame_w else (e, n))
    return np.array(pts)


# ------------------------------------------------------------------------------------------------------- drawing
def draw(world, out_dir):
    wname, V, spawn = parse_world(world)
    long_y = world.startswith("corridor_") or world == "outdoor_indoor"
    # map world (x, y) -> plot (u, v): long worlds plot y to the right, x downward (as the renders)
    tr = (lambda P: np.c_[P[:, 1], P[:, 0]]) if long_y else (lambda P: np.asarray(P)[:, :2])
    if long_y:
        fig, ax = plt.subplots(figsize=(15, 3.6 if world.startswith("corridor") else 4.6))
    else:
        fig, ax = plt.subplots(figsize=(8.2, 8.2))
    layers = {"floor_checker": [], "floor_blank": [], "runway": [], "grass": [], "wall": [], "wall_lined": [],
              "ceiling": [], "tag_floor": [], "tag_wall": [], "occluder": []}
    for v in V:
        k = classify(v)
        if k:
            layers[k].append(v)
    hl = []
    for v in layers["grass"]:
        ax.add_patch(Polygon(tr(hull2(v["pts"])), closed=True, fc="#eef3e6", ec="none", zorder=0))
    for v in layers["runway"]:
        ax.add_patch(Polygon(tr(hull2(v["pts"])), closed=True, fc="#bdbdbd", ec=INK2, lw=0.6, zorder=1))
    for v in layers["floor_checker"]:
        ax.add_patch(Polygon(tr(hull2(v["pts"])), closed=True, fc="#e2e2e2", ec="#b0b0b0", lw=0.5, hatch="++",
                             zorder=1))
    for v in layers["floor_blank"]:
        ax.add_patch(Polygon(tr(hull2(v["pts"])), closed=True, fc="white", ec="#b0b0b0", lw=0.5, zorder=1))
    for v in layers["wall"] + layers["wall_lined"]:
        lined = v in layers["wall_lined"]
        ax.add_patch(Polygon(tr(hull2(v["pts"])), closed=True, fc=WALL, ec=WALL, lw=1.6,
                             hatch="|||" if lined else None, zorder=4))
    for v in layers["ceiling"]:
        ax.add_patch(Polygon(tr(hull2(v["pts"])), closed=True, fill=False, ec=CEIL, lw=1.4, ls="--", zorder=6))
    for v in layers["tag_floor"]:
        ax.add_patch(Polygon(tr(hull2(v["pts"])), closed=True, fc=TAG, ec=TAG, zorder=5))
        c = tr(v["pts"][:, :2].mean(0, keepdims=True))[0]
        ax.text(c[0] + 0.3, c[1] + 0.3, v["uri_dir"].split("_")[-1], color=TAG, fontsize=9, weight="bold", zorder=7)
    for v in layers["tag_wall"]:
        ax.add_patch(Polygon(tr(hull2(v["pts"])), closed=True, fc=TAG, ec=TAG, lw=2.5, zorder=7))
        c = tr(v["pts"][:, :2].mean(0, keepdims=True))[0]
        ax.text(c[0], c[1] + 0.45, "wall tag %s (z %.1f m)" % (v["uri_dir"].split("_")[-1], v["pts"][:, 2].mean()),
                color=TAG, fontsize=9, weight="bold", ha="center", va="bottom", zorder=7)
    for v in layers["occluder"]:
        P = tr(hull2(v["pts"])); c = P.mean(0); zc = v["pts"][:, 2].mean()
        ax.add_patch(Polygon(P, closed=True, fc=REF, ec=REF, lw=2, zorder=7))
        ax.text(c[0] + 1.0, c[1] - 0.5, "occluder (z %.1f m: %s)" % (zc, "in front of the tag at start" if zc > 0
                else "parked below the floor"), color=INK2, fontsize=8, ha="left", zorder=7)

    notes = []
    # ---- routes from mission/profile files
    def route(P, style="-", lab=None, lw=2.0, arrows=True):
        Q = tr(np.asarray(P))
        ax.plot(Q[:, 0], Q[:, 1], style, color=ROUTE, lw=lw, zorder=8, label=lab, solid_capstyle="round")
        if arrows:
            for i in range(len(Q) - 1):
                a, b = Q[i], Q[i + 1]
                if np.hypot(*(b - a)) > 1e-6:
                    m = a + 0.55 * (b - a)
                    ax.annotate("", xy=m + 0.01 * (b - a), xytext=m, zorder=9,
                                arrowprops=dict(arrowstyle="-|>", color=ROUTE, lw=lw, mutation_scale=13))
    sx, sy = spawn["xy"]
    if world.startswith("corridor_"):
        vel, alt, dur, src = conf_cruise(world)
        route([(sx, sy), (sx, sy + vel * dur)], lab="planned cruise: %.1f m/s x %.0f s = %.0f m at %.1f m"
              % (vel, dur, vel * dur, alt))
        if "transition" in world:
            ys = [v["pts"][:, 1] for v in layers["floor_blank"]]
            yb = min(y.min() for y in ys)
            ax.axvline(yb, color=REF, ls=":", lw=1.5, zorder=5)
            ax.text(yb + 0.8, -11.5, "textured | blank boundary y = %.0f m" % yb, color=INK2, fontsize=8.5)
    elif world == "room_tags":
        n, side, spd = env_param("tools/run_expT.sh", "LAPS")
        c = [(sx, sy)]
        for dn, de in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            c.append((c[-1][0] + de * side, c[-1][1] + dn * side))
        alt = float(re.search(r'echo "room_tags\s+\S+\s+(\S+)', open(os.path.join(REPO, "tools", "run_expT.sh")).read()).group(1))
        route(c, lab="Experiments 2 and 3: laps: %d x %.0f m square N-E-S-W at %.1f m/s, %.1f m"
              % (n, side, spd, alt))
        t = open(os.path.join(REPO, "batches", "tagchar.conf")).read().split("\n")
        t = [l.split() for l in t if l.strip() and not l.startswith("#")]
        route([(sx - 0.25, sy), (sx - 0.25, sy + float(t[0][1]) * float(t[0][3]))], style="--", lw=1.4, arrows=False,
              lab="tag check flights: %.1f m/s north for %.0f s at %s m"
              % (float(t[0][1]), float(t[0][3]), "/".join(r[2] for r in t)))
    elif world == "outdoor_indoor":
        al, als, out, spd, gate = env_param("tools/run_expO.sh", "OUTBACK")
        route([(sx, sy), (sx, sy + al)], lab="Experiment 4: align: %.0f m at %.1f m/s (GNSS on)" % (al, als))
        route([(sx + 0.6, sy + al), (sx + 0.6, sy + al + out)], lab="Experiment 4: out: %.0f m at %.1f m/s" % (out, spd))
        route([(sx - 0.6, sy + al + out), (sx - 0.6, sy + al)], style="--", lab="Experiment 4: back: reverse, same heading")
        ax.axvline(gate, color=REF, ls=":", lw=1.5, zorder=5)
        ax.text(gate + 0.6, 9.3, "GNSS gate N = %.0f m (off going in, on coming out)" % gate, color=INK2, fontsize=8.5)
    elif world.startswith("room_wall_tag"):
        wp = wall_p()
        m = re.search(r"--box=([-\d.]+),([-\d.]+),([-\d.]+),([-\d.]+)",
                      open(os.path.join(REPO, "sim", "tools", "closed_loop_run.sh")).read())
        x0b, x1b, y0b, y1b = (float(t) for t in m.groups())
        ax.add_patch(Rectangle((x0b, y0b), x1b - x0b, y1b - y0b, fill=False, ec=REF, ls=":", lw=1.2, zorder=5))
        ax.text(x0b + 0.1, y0b + 0.15, "Experiment 5 safety-watcher room box", color=INK2, fontsize=8)
        if world == "room_wall_tag":
            P = h_profile_path("s0a_sweep.json", False)
            route(P, lw=1.0, arrows=False, lab="Experiment 5 characterisation: grid sweep (world frame)")
            P = h_profile_path("s1_profile.json", True)
            route(P, style="-", lw=2.0, arrows=False, lab="Experiment 5 EKF3-flying hold set: hold W(%.1f, %.1f), E steps of %.1f m"
                  % (P[1][1] - wall_p()[1], P[1][0], np.abs(P[:, 0]).max()))
        elif world == "room_wall_tag_far":
            P = h_profile_path("s1_far_profile.json", True); wp = wall_p()
            route(P[:2], lab="Experiment 5 hold sets, far spawn (EKF3-, UKF- and FGO-flying): anchor at W(%.1f, %.1f), "
                  "move to the hold W(%.1f, %.1f)" % (P[0][1] - wp[1], P[0][0], P[1][1] - wp[1], P[1][0]))
            route(h_profile_path("s1_far_profile.json", True)[1:], lw=1.2, arrows=False,
                  lab="  then E steps of %.1f m at the hold" % np.abs(P[:, 0]).max())
            P = h_profile_path("safety2_fgo_profile.json", True)
            ax.plot(*tr(P[-1:]).T, "D", color=ROUTE, ms=7, mfc="white", mew=1.8, zorder=10,
                    label="5S safety tests (FGO): hold W(%.1f, %.1f)" % (P[-1][1] - wall_p()[1], P[-1][0]))
        else:
            P = h_profile_path("ifanchor_profile.json", False)
            ax.annotate("", xy=(sx, sy + P[0][1]), xytext=(sx, sy), zorder=9,
                        arrowprops=dict(arrowstyle="-|>", color=ROUTE, lw=2, mutation_scale=13))
            ax.plot([], [], color=ROUTE, lw=2, label="Experiment 5 in-flight-anchor check: move %.1f m north in EKF3's own pre-anchor frame, "
                    "drawn from the spawn" % P[0][1])
        notes.append("tag frame W: N_W = world y - %.3f, E_W = world x" % wp[1])
    elif world.startswith("iris_"):
        notes.append("no mission file: the early pipeline-check and speed-sweep flights flew a few metres north (record only)")

    # ---- spawn
    S = tr(np.array([[sx, sy]]))[0]
    yaw = spawn["yaw"]; d = np.array([math.cos(yaw), math.sin(yaw)])
    dd = np.array([d[1], d[0]]) if long_y else d
    ax.plot(*S, marker="o", color=INK, ms=7, zorder=11, label="spawn %s (%.1f, %.1f), yaw %.0f deg"
            % (spawn["model"], sx, sy, math.degrees(yaw)))

    # ---- frame, scale bar, legend handles for the floor / walls
    allp = np.vstack([tr(v["pts"][:, :2]) for v in V if classify(v) in
                      ("floor_checker", "floor_blank", "wall", "wall_lined", "ceiling", "runway")])
    if world == "iris_runway":
        allp = np.array([[-80.0, -80.0], [80.0, 80.0]])      # the 1.5 km runway: show the spawn area only
    if world.startswith("room_"):                              # zoom on the room (walls); the floor tile is 20 m
        allp = np.vstack([tr(v["pts"][:, :2]) for v in layers["wall"]]); allp = np.r_[allp - 0.6, allp + 0.6]
    lo, hi = allp.min(0), allp.max(0); pad = 0.04 * (hi - lo).max()
    ax.set_xlim(lo[0] - pad, hi[0] + pad); ax.set_ylim(lo[1] - pad, hi[1] + pad)
    ax.set_aspect("equal")
    if long_y:
        ax.invert_yaxis()
        ax.set_xlabel("world y (m)  [flight direction +y = ArduPilot north]"); ax.set_ylabel("world x (m)")
    else:
        ax.set_xlabel("world x (m)  [east]"); ax.set_ylabel("world y (m)  [north]")
    span = (hi - lo)[0]
    ax.annotate("", xy=S + dd * 0.05 * span, xytext=S, zorder=11, arrowprops=dict(arrowstyle="->", color=INK, lw=1.3))
    L = [1, 2, 5, 10, 20, 50, 100][int(np.searchsorted([1, 2, 5, 10, 20, 50, 100], span / 6))]
    x0 = lo[0] + 0.02 * span; yb = ax.get_ylim()[0] + (0.06 if not long_y else -0.06) * abs(np.diff(ax.get_ylim()))[0]
    ax.plot([x0, x0 + L], [yb, yb], color=INK, lw=3, zorder=12, solid_capstyle="butt")
    ax.text(x0 + L + 0.01 * span, yb, "%g m" % L, ha="left", va="center", fontsize=9, zorder=12)
    ax.grid(False)
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    H = []
    if layers["floor_checker"]: H.append(Patch(fc="#e2e2e2", ec="#b0b0b0", hatch="++",
                                         label="checker floor (%.4g m squares)" % checker_square_m(layers["floor_checker"][0])))
    if layers["floor_blank"]: H.append(Patch(fc="white", ec="#b0b0b0", label="blank floor (no albedo map)"))
    if layers["runway"]: H.append(Patch(fc="#bdbdbd", ec=INK2, label="runway plane (runway.png)"))
    if layers["wall"]: H.append(Patch(fc=WALL, label="plain wall"))
    if layers["wall_lined"]: H.append(Patch(fc=WALL, hatch="|||", label="textured wall (line / end-wall texture)"))
    if layers["ceiling"]: H.append(Line2D([], [], color=CEIL, ls="--", lw=1.4, label="ceiling / roof slab (visual only)"))
    if layers["tag_floor"]: H.append(Patch(fc=TAG, label="floor AprilTag (id)"))
    hs, ls = ax.get_legend_handles_labels()
    ax.legend(H + hs, [h.get_label() for h in H] + ls, loc="upper left", bbox_to_anchor=(1.01, 1.0) if not long_y
              else (0.0, -0.22), ncol=1 if not long_y else 2, fontsize=8, frameon=False)
    ax.set_title("%s: top-down schematic from the SDF" % world, loc="left", weight="bold", pad=18 if notes else 6)
    if notes:
        ax.text(0.0, 1.01, "; ".join(notes), transform=ax.transAxes, fontsize=7.5, color=INK2, va="bottom")
    os.makedirs(out_dir, exist_ok=True)
    f = os.path.join(out_dir, world + ".png")
    fig.savefig(f, dpi=170, bbox_inches="tight"); fig.savefig(f[:-4] + ".pdf", bbox_inches="tight"); plt.close(fig)
    return f, {k: len(v) for k, v in layers.items()}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("worlds", nargs="*")
    a = ap.parse_args()
    ws = a.worlds or sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(REPO, "sim", "worlds", "*.sdf")))
    for w in ws:
        f, n = draw(w, a.out)
        print(w, {k: v for k, v in n.items() if v})


if __name__ == "__main__":
    main()
