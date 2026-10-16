#!/usr/bin/env python3
"""Documentation renders of every simulation world (docs/thesis/world_images/renders/).

For each world in sim/worlds/ this script writes a COPY of the world SDF to a scratch directory, adds TEMPORARY static
camera models (one per shot), runs the copy server-only (`gz sim -s -r`, the way run_trial.sh runs the flights), waits
for every camera to deliver its 4th frame (sim t = 2 s; earlier frames can predate scene loading), keeps it, and tears
the server down. Frames are taken from each camera's gz-transport topic by an in-process subscriber (a camera with
no subscriber is not rendered by the Sensors system). The world's own sun, scene and models are untouched, so the lighting is the flights' lighting.
sim/worlds/* is never modified.

"cutaway" shots are rendered from a second copy with the visual-only ceiling / roof models removed (corridor_ceiling,
bldg_roof), so the floor is visible from above; every cutaway is labelled as such in the index.

Projection: gz-sensors 8.2.2 does not read SDF <projection_type> (libgz-sensors8-camera references no
sdf::Camera::ProjectionType symbol; see the index), so the top-down views are HIGH-ALTITUDE, NARROW-FOV PERSPECTIVE
views, not orthographic. Their residual parallax is given per shot in the index.

Run (system python; the caller holds FLIGHT_LOCK; nothing else may be simulating):
  python3 sim/tools/render_world_docs.py --out docs/thesis/world_images/renders --scratch <dir> [world ...]
Writes renders/<world>__<shot>.jpg and renders/shots.json (pose, FOV, resolution, projection of every shot).
"""
import argparse, glob, json, math, os, re, shutil, signal, subprocess, sys, threading, time
import numpy as np
from PIL import Image as PImage

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORLDS = os.path.join(REPO, "sim", "worlds")
CUT_MODELS = ("corridor_ceiling", "bldg_roof")      # visual-only covers removed in cutaway copies


def look_at(eye, target):
    dx, dy, dz = (t - e for t, e in zip(target, eye))
    return 0.0, math.atan2(-dz, math.hypot(dx, dy)), math.atan2(dy, dx)


def shot(name, what, eye, target=None, hfov_deg=60.0, w=1600, h=900, rpy=None, cutaway=False, far=4000.0):
    r = rpy if rpy is not None else look_at(eye, target)
    return dict(name=name, what=what, eye=list(eye), target=list(target) if target else None, rpy=list(r),
                hfov_deg=hfov_deg, width=w, height=h, cutaway=cutaway, near=0.05, far=far, projection="perspective")


def top(name, what, cx, cy, span_img_w, w, h, yaw, alt, cutaway=False):
    """Straight-down view centred on (cx, cy) covering span_img_w metres across the image width.
    yaw = pi/2: image right = +x, up = +y. yaw = pi: image right = +y, up = -x (long corridors run left to right)."""
    alt = min(alt, span_img_w / 2 / math.tan(0.06))        # SDF requires horizontal_fov >= 0.1 rad; keep >= 0.12
    hfov = 2 * math.degrees(math.atan(span_img_w / 2 / alt))
    s = shot(name, what, (cx, cy, alt), None, hfov, w, h, rpy=(0.0, math.pi / 2, yaw), cutaway=cutaway, far=alt + 50)
    s["projection"] = "perspective, high-altitude narrow-FOV (near-orthographic)"
    s["ground_span_m"] = [span_img_w, span_img_w * h / w]
    return s


def corridor_shots(world):
    ceil = world.endswith("c") and ("_fwdc" in world or "_fwdplainc" in world)
    fwd = "_fwd" in world
    lined = fwd and "plain" not in world
    alt = 600.0
    S = []
    S.append(top("top", "whole world from above" + (" (ceiling removed: cutaway)" if ceil else ""),
                 0, 72.5, 190, 3200, 400, math.pi, alt, cutaway=ceil))
    if ceil:
        S.append(top("top_roof", "whole world from above, as built (the ceiling slab covers the corridor)",
                     0, 72.5, 190, 3200, 400, math.pi, alt))
    S.append(shot("angled", "three-quarter overview from the south-west, above the spawn end",
                  (-30, -32, 24), (0, 45, 0), 60, 1600, 900))
    if ceil:
        S.append(shot("angled_cutaway", "three-quarter overview with the ceiling removed (cutaway)",
                      (-30, -32, 24), (0, 45, 0), 60, 1600, 900, cutaway=True))
    S.append(shot("interior", "inside the corridor at flight height (2 m) looking down the flight direction (+y)",
                  (0, 2, 2.0), (0, 60, 2.0), 80, 1600, 900))
    if "transition" in world:
        S.append(shot("boundary", "the textured/blank floor boundary at y = 80 m",
                      (-7, 70, 4.5), (0, 82, 0), 70, 1600, 900))
    if fwd:
        S.append(shot("wall", "close-up of the east wall surface (" + ("line-textured" if lined else "plain") + ")",
                      (3, 40, 2.0), (10, 46, 2.3), 70, 1600, 900))
        S.append(shot("endwall", "approaching the end wall at y = 165 m (" + ("textured" if lined else "plain") + ")",
                      (0, 140, 2.0), (0, 165, 2.0), 60, 1600, 900))
    if ceil:
        S.append(shot("ceiling", "looking up at the ceiling slab (underside z = 5.0 m) from 1 m",
                      (-8, 30, 1.0), (2, 45, 5.0), 80, 1600, 900))
    S.append(shot("spawn", "the drone at the spawn (0, 0, 0.195), facing +y",
                  (-1.6, -2.4, 1.4), (0, 0, 0.25), 60, 1600, 900))
    return S


def room_shots(world):
    alt = 150.0
    S = [top("top", "whole world from above (the 20 x 20 m floor tile; room walls at |x|, |y| = 5.1 m)",
             0, 0, 21, 1600, 1600, math.pi / 2, alt),
         top("top_room", "the 10 x 10 m room from above (tags readable)", 0, 0, 11, 1600, 1600, math.pi / 2, alt),
         shot("angled", "three-quarter overview from the south-west", (-8.5, -10.5, 11), (0, 0.5, 0), 60, 1600, 900),
         shot("tags", "inside the room from above the south wall (5 m), all eight floor tags",
              (0, -4.9, 5.0), (0, 0.6, 0), 85, 1600, 900),
         shot("tag2", "close-up of floor tag 2 at (3, 3), yaw -45 deg (0.5 m tile, 0.4 m black square)",
              (2.2, 1.6, 1.6), (3, 3, 0), 50, 1600, 900)]
    if world.startswith("room_wall_tag"):
        spawn_y = 3.5 if world == "room_wall_tag" else 1.1
        S.append(shot("walltag", "wall tag id 10 on the north wall (0, 5.0, 1.5) seen from beside the spawn"
                      + (" (occluder in front of it)" if world.endswith("_occ") else ""),
                      (0.9, spawn_y - 0.6, 1.7), (0, 5.0, 1.5), 60, 1600, 900))
        S.append(shot("spawn", "the forward-camera drone at the spawn (0, %.1f), facing the wall tag" % spawn_y,
                      (-1.6, spawn_y - 2.4, 1.4), (0, spawn_y, 0.25), 60, 1600, 900))
    else:
        S.append(shot("spawn", "the drone at the spawn (-3, -3) over tag 0", (-4.6, -5.4, 1.4), (-3, -3, 0.25),
                      60, 1600, 900))
    return S


def outdoor_shots(world):
    alt = 500.0
    return [top("top", "whole world from above, as built (roof on)", 0, 30, 104, 2400, 500, math.pi, alt),
            top("top_cutaway", "whole world from above with the building roof removed (cutaway)",
                0, 30, 104, 2400, 500, math.pi, alt, cutaway=True),
            shot("angled", "three-quarter overview from the south-west", (-26, -32, 18), (0, 30, 0), 60, 1600, 900),
            shot("entrance", "the 3 m entrance in the south wall (y = 20 m) seen from outside at flight height",
                 (0, 9, 2.0), (0, 20, 1.5), 70, 1600, 900),
            shot("indoor", "inside the building at flight height looking north (+y)", (0, 22, 2.0), (0, 60, 1.5),
                 80, 1600, 900),
            shot("spawn", "the drone at the spawn (0, -15), facing +y", (-1.6, -17.4, 1.4), (0, -15, 0.25),
                 60, 1600, 900)]


def iris_shots(world):
    S = [top("top", "the area around the spawn from above (60 m across)", 0, 0, 60, 1600, 1600, math.pi / 2, 300.0),
         shot("angled", "three-quarter overview from the south-west", (-15, -18, 10), (0, 2, 0), 65, 1600, 900),
         shot("spawn", "the drone at the spawn (0, 0, 0.195), facing +y", (-1.6, -2.4, 1.4), (0, 0, 0.25),
              60, 1600, 900)]
    if world == "iris_runway":
        S.insert(1, top("top_wide", "the runway from above (1600 m across)", -29, 545, 1600, 2400, 600,
                        math.pi / 2, 3000.0))
        S[1]["rpy"] = [0.0, math.pi / 2, math.pi]   # long axis (y) left to right
        S[1]["what"] = "the whole runway from above (1600 m along y, left to right)"
    return S


def shots_for(world):
    if world.startswith("corridor_"):
        return corridor_shots(world)
    if world.startswith("room_"):
        return room_shots(world)
    if world == "outdoor_indoor":
        return outdoor_shots(world)
    if world.startswith("iris_"):
        return iris_shots(world)
    raise SystemExit("no shot list for " + world)


def camera_model(s, save_dir):
    x, y, z = s["eye"]; r, p, yw = s["rpy"]
    return f"""
    <model name="doccam_{s['name']}">
      <static>true</static>
      <pose>{x:.4f} {y:.4f} {z:.4f} {r:.6f} {p:.6f} {yw:.6f}</pose>
      <link name="link">
        <sensor name="doccam_{s['name']}" type="camera">
          <always_on>1</always_on>
          <update_rate>2</update_rate>
          <topic>/doccam/{s['name']}</topic>
          <camera>
            <horizontal_fov>{math.radians(s['hfov_deg']):.6f}</horizontal_fov>
            <image><width>{s['width']}</width><height>{s['height']}</height><format>R8G8B8</format></image>
            <clip><near>{s['near']}</near><far>{s['far']}</far></clip>
          </camera>
        </sensor>
      </link>
    </model>
"""


def strip_cutaway(sdf):
    """Remove <include> blocks and <model> blocks of the visual-only ceiling / roof."""
    for m in CUT_MODELS:
        sdf, n1 = re.subn(r"<include>(?:(?!</include>).)*?model://%s<(?:(?!</include>).)*?</include>" % m, "", sdf,
                          flags=re.S)
        sdf, n2 = re.subn(r'<model name="%s">.*?</model>' % m, "", sdf, flags=re.S)
    return sdf


def run_copy(world, shots, scratch, tag, timeout_s=240, frames_needed=4):
    src = open(os.path.join(WORLDS, world + ".sdf")).read()
    if tag == "cut":
        src2 = strip_cutaway(src)
        assert src2 != src, "cutaway removed nothing for " + world
        src = src2
    wdir = os.path.join(scratch, world + "_" + tag)
    shutil.rmtree(wdir, ignore_errors=True); os.makedirs(wdir)
    cams = ""
    for s in shots:
        cams += camera_model(s, None)
    i = src.rindex("</world>")
    copy = os.path.join(wdir, world + ".sdf")
    open(copy, "w").write(src[:i] + "\n    <!-- TEMPORARY documentation cameras (render_world_docs.py) -->" + cams
                          + "\n  " + src[i:])
    env = dict(os.environ)
    env["GZ_SIM_RESOURCE_PATH"] = ":".join([os.path.join(REPO, "sim", "models"),
                                            os.path.expanduser("~/ardupilot_gazebo/models"),
                                            os.path.expanduser("~/ardupilot_gazebo/worlds")])
    env["GZ_SIM_SYSTEM_PLUGIN_PATH"] = os.path.expanduser("~/ardupilot_gazebo/build")
    env["GZ_PARTITION"] = "doccam_%d" % os.getpid()   # isolate gz-transport from anything else on the host
    os.environ["GZ_PARTITION"] = env["GZ_PARTITION"]           # the subscriber must share the partition
    from gz.transport13 import Node
    from gz.msgs10.image_pb2 import Image
    lock = threading.Lock(); count = {s["name"]: 0 for s in shots}; last = {}

    def cb_for(name):
        def cb(msg):
            with lock:
                count[name] += 1
                if count[name] >= frames_needed and name not in last:   # skip the first frames (scene still loading)
                    a = np.frombuffer(msg.data, np.uint8).reshape(msg.height, msg.step)[:, :msg.width * 3]
                    last[name] = a.reshape(msg.height, msg.width, 3).copy()
        return cb
    node = Node()
    for s in shots:
        assert node.subscribe(Image, "/doccam/" + s["name"], cb_for(s["name"]))
    log = open(os.path.join(wdir, "gz.log"), "w")
    p = subprocess.Popen(["gz", "sim", "-v2", "-s", "-r", copy], stdout=log,
                         stderr=subprocess.STDOUT, env=env, start_new_session=True)
    t0 = time.time(); ok = False
    try:
        while time.time() - t0 < timeout_s:
            if p.poll() is not None:
                print(f"  {world}/{tag}: gz exited early (code {p.returncode})"); break
            with lock:
                if len(last) == len(shots):
                    ok = True; break
            time.sleep(1)
    finally:
        for s in shots:
            node.unsubscribe("/doccam/" + s["name"])
        try:
            os.killpg(p.pid, signal.SIGTERM); p.wait(timeout=20)
        except Exception:
            try: os.killpg(p.pid, signal.SIGKILL)
            except Exception: pass
            p.wait()
    res = {}
    for s in shots:
        if s["name"] in last:
            f = os.path.join(wdir, s["name"] + ".png"); PImage.fromarray(last[s["name"]]).save(f); res[s["name"]] = f
        else:
            res[s["name"]] = None
    print(f"  {world}/{tag}: {'ok' if ok else 'INCOMPLETE'} in {time.time() - t0:.0f} s")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--scratch", required=True)
    ap.add_argument("worlds", nargs="*")
    a = ap.parse_args()
    worlds = a.worlds or sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(WORLDS, "*.sdf")))
    os.makedirs(a.out, exist_ok=True)
    meta_path = os.path.join(a.out, "shots.json")
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    for w in worlds:
        S = shots_for(w)
        meta[w] = {"shots": [], "failed": []}
        for tag in ("asbuilt", "cut"):
            sub = [s for s in S if s["cutaway"] == (tag == "cut")]
            if not sub:
                continue
            res = run_copy(w, sub, a.scratch, tag)
            for s in sub:
                f = res[s["name"]]
                if f is None:
                    meta[w]["failed"].append(s["name"]); continue
                dst = os.path.join(a.out, f"{w}__{s['name']}.jpg")       # JPEG q92 keeps the docs set small
                PImage.open(f).convert("RGB").save(dst, quality=92)
                meta[w]["shots"].append(dict(s, file=os.path.basename(dst)))
        json.dump(meta, open(meta_path, "w"), indent=1)
    print("done")


if __name__ == "__main__":
    main()
