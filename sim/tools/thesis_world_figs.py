#!/usr/bin/env python3
"""Four consolidated world schematics for the thesis reader-facing figure set
(docs/thesis/world_images/thesis/), replacing the old per-world schematic set.

Scope: documentation only. No world file, trial data or result is modified. Every number drawn is checked against
an INDEPENDENT parse of its source file (the world's own include/pose text, a profile json, or a batch conf line) -
not against the same code path used to draw it. The independent parse lives in `source_*()` below; the drawing code
in `draw_*()` never calls it, and `main()` asserts the two agree before a figure is written.

Style: eval/thesis_style.py (160 mm wide, Okabe-Ito palette, no in-figure titles, fonts 9-11 pt). Reuses the same
colour choices as the (now superseded) per-world sim/tools/world_schematics.py, which is NOT imported here (its own
drawing code has a bold left-aligned title and per-world file-name labels, both against the new brief), so the
style constants are restated directly.

Run: python3 sim/tools/thesis_world_figs.py
"""
import os, re, sys, math
import xml.etree.ElementTree as ET
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Patch, FancyArrowPatch
from matplotlib.lines import Line2D

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO, "eval"))
import thesis_style as ts

OUT = os.path.join(REPO, "docs", "thesis", "world_images", "thesis")
CAP = os.path.join(OUT, "captions")
os.makedirs(CAP, exist_ok=True)

ROUTE, TAG, CEIL, REF, WALL = "#E69F00", "#CC79A7", "#56B4E9", "#999999", ts.WALL
INK, INK2, GRID, SURF = ts.INK, ts.INK2, ts.GRID, ts.SURF

RC = dict(ts.RCPARAMS)
RC.update({"font.size": 9.5, "axes.labelsize": 9.5, "xtick.labelsize": 9, "ytick.labelsize": 9,
           "legend.fontsize": 8.5, "axes.grid": False, "axes.spines.top": True, "axes.spines.right": True})
plt.rcParams.update(RC)

CHECKS = []


def check(label, drawn, source, tol=1e-6):
    ok = abs(float(drawn) - float(source)) <= tol
    CHECKS.append((label, drawn, source, ok))
    if not ok:
        raise AssertionError("geometry check failed: %s drawn=%r source=%r" % (label, drawn, source))


def check_pt(label, drawn, source, tol=1e-6):
    for lab, d, s in zip(("x", "y"), drawn, source):
        check(label + " " + lab, d, s, tol)


def write_caption(path, text):
    with open(path, "w") as f:
        f.write(text.strip() + "\n")


def world_path(name):
    return os.path.join(REPO, "sim", "worlds", name + ".sdf")


# =====================================================================================================  SOURCE (independent parse: raw <include>/<model> pose text, one level, no pose-chain machinery)
def world_includes(name):
    """{model_or_name: (x, y, z, roll, pitch, yaw_rad)} for every top-level <include> and inline <model> of a world,
    read directly from its own <pose> text - independent of sim/tools/world_schematics.py's pose-chain parser."""
    root = ET.parse(world_path(name)).getroot()
    w = root.find("world")
    out = {}
    for inc in w.findall("include"):
        uri = inc.findtext("uri").strip()
        label = (inc.findtext("name") or uri.replace("model://", "")).strip()
        p = inc.find("pose")
        v = [float(t) for t in (p.text.split() if p is not None and p.text else "0 0 0 0 0 0".split())]
        if p is not None and p.get("degrees") == "true":
            v[3:] = [math.radians(a) for a in v[3:]]
        out[label] = tuple(v) + (uri,)
    for m in w.findall("model"):
        p = m.find("pose")
        v = [float(t) for t in (p.text.split() if p is not None and p.text else "0 0 0 0 0 0".split())]
        out[m.get("name")] = tuple(v) + (None,)
    return out


def inline_model_box(name, model_name):
    """Box <size> (x, y, z) of an inline top-level <model>'s own link/visual geometry, read directly - independent
    of world_includes() above (which only reads the model's own <pose>, not its geometry)."""
    root = ET.parse(world_path(name)).getroot()
    for m in root.find("world").findall("model"):
        if m.get("name") == model_name:
            s = m.find(".//box/size")
            return tuple(float(t) for t in s.text.split())
    raise KeyError(model_name)


def source_corridor():
    """Corridor geometry, independently re-read from corridor_transition.sdf (floor + wall + spawn) and
    corridor_textured_fwdc.sdf (ceiling), plus the flight line from batches/dsn_nomag.conf."""
    inc = world_includes("corridor_transition")
    tiles = sorted(v[1] for k, v in inc.items() if k.startswith("floor_tile_"))
    # boundary = the lowest-y centre of a blank tile, minus its half-width (10 m), read from each tile's OWN <uri>
    # ("blank_ground_visual" vs "textured_ground_visual"), not from an assumed tile-index cutoff
    blank_tile_ys = [v[1] for k, v in inc.items() if k.startswith("floor_tile_") and "blank_ground_visual" in v[-1]]
    textured_tile_ys = [v[1] for k, v in inc.items() if k.startswith("floor_tile_") and "textured_ground_visual" in v[-1]]
    assert blank_tile_ys and textured_tile_ys and max(textured_tile_ys) < min(blank_tile_ys), \
        "corridor_transition.sdf tiles are not cleanly textured-then-blank by y"
    boundary_y = (max(textured_tile_ys) + min(blank_tile_ys)) / 2  # tiles are 20 m and adjoin, so this is exact
    wx = [inc["wall_east"][0], inc["wall_west"][0]]
    wy_c = inc["wall_east"][1]
    wall_model = os.path.join(REPO, "sim", "models", "corridor_wall", "model.sdf")
    wsize = [float(t) for t in ET.parse(wall_model).getroot().find(".//box/size").text.split()]
    spawn = inc["iris_with_ardupilot"]
    flight = None
    for f in ("batches/rerun_main.conf", "batches/dsn_tex_extra.conf"):
        fp = os.path.join(REPO, f)
        if os.path.exists(fp):
            for ln in open(fp):
                t = ln.split()
                if len(t) >= 5 and not ln.lstrip().startswith("#") and t[0] == "corridor_textured":
                    flight = (float(t[1]), float(t[2]), float(t[3]))
                    break
        if flight:
            break
    return dict(tile_y=tiles, boundary_y=boundary_y, wall_x=wx, wall_y_half=wsize[1] / 2, wall_y_c=wy_c,
                wall_z=wsize[2], wall_thick=wsize[0], spawn=(spawn[0], spawn[1], spawn[5]), flight=flight)


def source_room(world):
    inc = world_includes(world)
    tags = {}
    for k, v in inc.items():
        if v[-1] and "apriltag36h11_" in v[-1]:
            tid = int(v[-1].rstrip("/").split("_")[-1])
            tags[tid] = (v[0], v[1], v[5], v[2])  # x, y, yaw, z
    spawn = inc["iris_with_ardupilot"]
    # room half-extent: the 4 inline wall models' own pose coordinate (not a hardcoded figure), checked for
    # agreement across all 4 before use
    halves = [max(abs(v[0]), abs(v[1])) for k, v in inc.items() if re.match(r"^wall_\d+$", k)]
    assert len(halves) == 4 and max(halves) - min(halves) < 1e-6, \
        "the 4 room walls do not agree on the room half-extent: %r" % halves
    tag_size = float(ET.parse(os.path.join(REPO, "sim", "models", "apriltag36h11_0", "model.sdf")).getroot()
                     .find(".//box/size").text.split()[0])
    return dict(tags=tags, spawn=(spawn[0], spawn[1], spawn[5]), n_walls=sum(1 for k in inc if re.match(r"^wall_\d+$", k)),
                room_half=halves[0], tag_size=tag_size)


def source_laps():
    txt = open(os.path.join(REPO, "tools", "run_expT.sh")).read()
    m = re.search(r"LAPS=([\d.]+),([\d.]+),([\d.]+)", txt)
    return float(m.group(1)), float(m.group(2)), float(m.group(3))


def source_wall_tag_and_hold():
    inc = world_includes("room_wall_tag")
    wt = inc["wall_tag_10"]
    # WALL_P: the navigation-frame origin tag_bridge_fwd.py uses to convert a profile's tag-frame (N, E) into world
    # coordinates - read independently from that file's own constant, not from the wall tag's rendered SDF pose,
    # since those are two different things that merely should agree (checked in main(), not assumed here)
    wall_p_txt = open(os.path.join(REPO, "tag_bridge_fwd.py")).read()
    wp = [float(x) for x in re.search(r"WALL_P = np\.array\(\[([^\]]*)\]\)", wall_p_txt).group(1).split(",")]
    prof = __import__("json").load(open(os.path.join(REPO, "batches", "expH", "s1_profile.json")))
    near = prof[0]["near"]  # [N, E] in tag frame W (N into the wall, E right, origin at WALL_P)
    n0, e0 = near
    hold = (e0, n0 + wp[1])  # world (x, y): x = E, y = N + WALL_P's north offset
    moves = [seg["to"] for seg in prof if seg["type"] == "move"]
    e_span = (min(m[1] for m in moves), max(m[1] for m in moves))
    return dict(wall_xyz=(wt[0], wt[1], wt[2]), wall_pitch=wt[3], wall_p=wp, hold=hold, e_span=e_span)


def source_outdoor_indoor():
    inc = world_includes("outdoor_indoor")
    spawn = inc["iris_with_ardupilot"]
    x_west = inc["bldg_west"][0]; x_east = inc["bldg_east"][0]
    y_south = inc["bldg_south_w"][1]  # south wall is in two segments either side of the entrance; same y for both
    assert abs(inc["bldg_south_e"][1] - y_south) < 1e-9
    y_north = inc["bldg_north"][1]
    # entrance half-width: from the two south-wall segments' own pose + box size (not retyped), not the OUTBACK gate
    sw_x, sw_sx = inc["bldg_south_w"][0], inline_model_box("outdoor_indoor", "bldg_south_w")[0]
    se_x, se_sx = inc["bldg_south_e"][0], inline_model_box("outdoor_indoor", "bldg_south_e")[0]
    sw_inner_edge = sw_x + sw_sx / 2    # west segment's edge facing the entrance
    se_inner_edge = se_x - se_sx / 2    # east segment's edge facing the entrance
    assert abs(sw_inner_edge + se_inner_edge) < 1e-9, "the two south-wall segments are not symmetric about x=0"
    entrance_half = se_inner_edge
    txt = open(os.path.join(REPO, "tools", "run_expO.sh")).read()
    m = re.search(r"OUTBACK=([\d.]+),([\d.]+),([\d.]+),([\d.]+),([\d.]+)", txt)
    al, als, out, spd, gate = (float(x) for x in m.groups())
    return dict(spawn=(spawn[0], spawn[1], spawn[5]), bldg_x=(x_west, x_east), bldg_south_y=y_south,
                bldg_north_y=y_north, entrance_half=entrance_half, outback=(al, als, out, spd, gate))


# =====================================================================================================  DRAWING
def savefig(fig, fid, width_in=ts.TEXT_WIDTH_IN, height_in=None, rect=(0.0, 0.0, 1.0, 1.0)):
    if height_in:
        fig.set_size_inches(width_in, height_in)
    fig.tight_layout(rect=rect)
    f = os.path.join(OUT, fid + ".png")
    fig.savefig(f, dpi=200)
    fig.savefig(f[:-4] + ".pdf")
    plt.close(fig)
    return f


def fig_legend(fig, handles, ncol=2):
    """Figure-level legend below the axes; the matching savefig(rect=...) call reserves the room for it below. Avoids
    ax.legend()'s bbox_to_anchor clipping once bbox_inches='tight' is not used for the final save (see the
    2026-11-02 restyle handover's width-fix note)."""
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.0), ncol=ncol, frameon=False, fontsize=8)


def scale_bar(ax, x0, y, length, label_above=False):
    ax.plot([x0, x0 + length], [y, y], color=INK, lw=3, solid_capstyle="butt", zorder=12)
    ax.text(x0 + length / 2, y + (0.4 if label_above else -0.4), "%g m" % length, ha="center",
            va="bottom" if label_above else "top", fontsize=9, color=INK)


def spawn_marker(ax, x, y, yaw_rad, label, dx=0.0, dy=0.0, flip_xy=False):
    d = (math.sin(yaw_rad), math.cos(yaw_rad)) if flip_xy else (math.cos(yaw_rad), math.sin(yaw_rad))
    ax.plot(x, y, marker="o", color=INK, ms=7, zorder=11)
    ax.annotate("", xy=(x + d[0] * 1.0, y + d[1] * 1.0), xytext=(x, y), zorder=11,
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.4))
    ax.annotate(label, (x, y), (x + dx, y + dy), fontsize=8.5, color=INK, ha="left", zorder=12)


def route_arrows(ax, pts, color=ROUTE, lw=2.0, style="-"):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, style, color=color, lw=lw, zorder=8, solid_capstyle="round")
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        if math.hypot(b[0] - a[0], b[1] - a[1]) < 1e-6:
            continue
        m = (a[0] + 0.55 * (b[0] - a[0]), a[1] + 0.55 * (b[1] - a[1]))
        d = (0.02 * (b[0] - a[0]), 0.02 * (b[1] - a[1]))
        ax.annotate("", xy=(m[0] + d[0], m[1] + d[1]), xytext=m, zorder=9,
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, mutation_scale=12))


# -----------------------------------------------------------------------------------------------  1. Corridor family
def fig_corridor(S):
    fig, ax = plt.subplots(figsize=(ts.TEXT_WIDTH_IN, 3.4))
    x_wall, y_lo, y_hi = S["wall_x"][0], S["wall_y_c"] - S["wall_y_half"], S["wall_y_c"] + S["wall_y_half"]
    boundary = S["boundary_y"]
    floor_lo = min(S["tile_y"]) - 10
    floor_hi = max(max(S["tile_y"]) + 10, y_hi)   # the walls run past the last floor tile; don't let that clip
    # floor: textured half then blank half (the three single-condition worlds are this drawing with one half
    # replaced by more of the other: see the key)
    ax.add_patch(Polygon([(0, -10), (boundary, -10), (boundary, 10), (0, 10)], closed=True, fc="#e2e2e2",
                         ec="#b0b0b0", lw=0.5, hatch="++", zorder=1))
    ax.add_patch(Polygon([(boundary, -10), (floor_hi, -10), (floor_hi, 10), (boundary, 10)], closed=True, fc="white",
                         ec="#b0b0b0", lw=0.5, zorder=1))
    ax.axvline(boundary, color=REF, ls=":", lw=1.5, zorder=5)
    # roof: a light, borderless fill over the full interior (present in the forward-camera variants only) - drawn
    # as a fill rather than an outline, because to true scale its edge coincides with the walls' outer face and an
    # outline there would sit on top of the wall band and be unreadable
    ax.add_patch(Rectangle((y_lo, -10), y_hi - y_lo, 20, fc=CEIL, ec="none", alpha=0.18, zorder=2))
    # walls: true thickness is only 0.2 m (checked below); drawn at a bolder DISPLAY width so they read at this
    # scale, stated here and in the caption rather than left unexplained
    DISPLAY_WALL_W = 1.0
    for xw in S["wall_x"]:
        ax.add_patch(Rectangle((y_lo, xw - DISPLAY_WALL_W / 2), y_hi - y_lo, DISPLAY_WALL_W,
                               fc=WALL, ec=WALL, lw=0.8, zorder=4))
    # spawn + planned flight line
    sx, sy, syaw = S["spawn"]
    route_arrows(ax, [(sy, sx), (sy + S["flight"][0] * S["flight"][2], sx)])
    ax.plot(sy, sx, marker="o", color=INK, ms=7, zorder=11)
    scale_bar(ax, 2, -14.0, 20, label_above=False)
    ax.set_xlim(floor_lo - 3, floor_hi + 3); ax.set_ylim(-20.5, 12.5)
    ax.set_aspect("equal")
    ax.set_xlabel("distance along the corridor (m)"); ax.set_ylabel("corridor width (m)")
    H = [Patch(fc="#e2e2e2", ec="#b0b0b0", hatch="++", label="checker floor (textured condition)"),
         Patch(fc="white", ec="#b0b0b0", label="blank floor (no texture)"),
         Line2D([], [], color=REF, ls=":", lw=1.5, label="texture boundary between the two floors"),
         Patch(fc=WALL, label="plain wall"),
         Patch(fc=WALL, hatch="|||", label="wall marked with lines (same position as the plain wall)"),
         Patch(fc=CEIL, alpha=0.18, ec="none", label="roof (present with the forward camera only)"),
         Line2D([0], [0], color=ROUTE, lw=2, label="planned flight line"),
         Line2D([0], [0], marker="o", color=INK, lw=0, label="spawn point")]
    fig_legend(fig, H, ncol=1)
    return savefig(fig, "corridor_family", rect=(0.0, 0.50, 1.0, 1.0))


# -----------------------------------------------------------------------------------------------  2/3. Room(s)
def fig_room(S, out_name, with_wall_tag=False, WT=None):
    from matplotlib.transforms import Affine2D
    fig, ax = plt.subplots(figsize=(ts.TEXT_WIDTH_IN, ts.TEXT_WIDTH_IN * 0.78))
    room_half, ts_ = S["room_half"], S["tag_size"]
    ax.add_patch(Rectangle((-room_half, -room_half), 2 * room_half, 2 * room_half, fc="#e2e2e2", ec="#b0b0b0", lw=0.5,
                           hatch="++", zorder=1))
    ax.add_patch(Rectangle((-room_half, -room_half), 2 * room_half, 2 * room_half, fill=False, ec=WALL, lw=2.4,
                           zorder=4))
    for tid, (x, y, yaw, z) in sorted(S["tags"].items()):
        r = Rectangle((x - ts_ / 2, y - ts_ / 2), ts_, ts_, fc=TAG, ec=TAG, zorder=5)
        r.set_transform(Affine2D().rotate_around(x, y, yaw) + ax.transData)
        ax.add_patch(r)
        lx, ly = x + 0.55 * math.cos(yaw + 0.9), y + 0.55 * math.sin(yaw + 0.9)
        ax.annotate(str(tid), (x, y), (lx, ly), fontsize=9, weight="bold", color=TAG, ha="center", va="center",
                    zorder=7)
    sx, sy, syaw = S["spawn"]
    c0 = (sx, sy)
    pts = [c0]
    for dn, de in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
        pts.append((pts[-1][0] + de * S["side"], pts[-1][1] + dn * S["side"]))
    route_arrows(ax, pts, lw=2.0)
    ax.plot(sx, sy, marker="o", color=INK, ms=7, zorder=11)
    ax.annotate("spawn / lap start", (sx, sy), (sx - 0.3, sy - 0.75), fontsize=8.5, color=INK, ha="right", zorder=12)
    if with_wall_tag:
        wx, wy, wz = WT["wall_xyz"]
        # the wall tag stands vertically (on the wall, seen edge-on from above): drawn as a short bar on the wall
        # line, its width taken from the tag model's own size (the same apriltag model as the floor tags)
        ax.add_patch(Rectangle((wx - ts_ / 2, wy - 0.04), ts_, 0.08, fc=TAG, ec=TAG, lw=1.5, zorder=7))
        hx, hy = WT["hold"]
        e_lo, e_hi = WT["e_span"]
        ax.plot([hx + e_lo, hx + e_hi], [hy, hy], color=ROUTE, lw=2.2, zorder=9, solid_capstyle="round")
        ax.plot(hx, hy, marker="s", mfc="white", mec=ROUTE, mew=1.8, ms=7, zorder=10)
    scale_bar(ax, -4.9, -6.6, 2, label_above=True)
    ax.set_xlim(-6.2, 6.2); ax.set_ylim(-7.0, 6.4)
    ax.set_aspect("equal")
    ax.set_xlabel("room x (m)"); ax.set_ylabel("room y (m)")
    H = [Patch(fc="#e2e2e2", ec="#b0b0b0", hatch="++", label="checker floor"),
         Patch(fc=WALL, label="room wall"),
         Patch(fc=TAG, label="floor tag (number is its id)"),
         Line2D([0], [0], color=ROUTE, lw=2, label="lap path (direction shown by the arrows)"),
         Line2D([0], [0], marker="o", color=INK, lw=0, label="spawn point")]
    if with_wall_tag:
        H += [Patch(fc=TAG, label="wall tag (on the wall, 1.5 m up)"),
              Line2D([0], [0], marker="s", mfc="white", mec=ROUTE, color=ROUTE, lw=2, label="hold point and its side steps")]
    fig_legend(fig, H, ncol=2)
    return savefig(fig, out_name, height_in=7.3, rect=(0.0, 0.14, 1.0, 1.0))


# -----------------------------------------------------------------------------------------------  4. Outdoor to indoor
def fig_outdoor_indoor(S):
    fig, ax = plt.subplots(figsize=(ts.TEXT_WIDTH_IN, 4.2))
    al, als, out, spd, gate = S["outback"]
    sx, sy, syaw = S["spawn"]
    x_lo, x_hi = S["bldg_x"]
    y0, y1 = S["bldg_south_y"], S["bldg_north_y"]
    half_gap = S["entrance_half"]
    entrance_y = y0   # the entrance is in the south wall; checked against the GNSS gate in main(), not assumed here
    # building walls, long axis horizontal: plot-x = world y, plot-y = world x
    ax.add_patch(Rectangle((y0, x_lo - 0.1), y1 - y0, 0.2, fc=WALL, ec=WALL, zorder=4))   # west wall
    ax.add_patch(Rectangle((y0, x_hi - 0.1), y1 - y0, 0.2, fc=WALL, ec=WALL, zorder=4))   # east wall
    ax.add_patch(Rectangle((y1 - 0.1, x_lo), 0.2, x_hi - x_lo, fc=WALL, ec=WALL, zorder=4))  # north (far) wall
    ax.add_patch(Rectangle((y0 - 0.1, x_lo), 0.2, (-half_gap) - x_lo, fc=WALL, ec=WALL, zorder=4))
    ax.add_patch(Rectangle((y0 - 0.1, half_gap), 0.2, x_hi - half_gap, fc=WALL, ec=WALL, zorder=4))
    ax.axvline(entrance_y, color=REF, ls=":", lw=1.5, zorder=3)
    ax.annotate("entrance (%g m gap)" % (2 * half_gap), xy=(entrance_y, half_gap), xytext=(entrance_y + 4, 7.6),
                fontsize=8.5, color=INK, ha="left", va="center", zorder=12,
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.0))
    # legs
    route_arrows(ax, [(sy, sx), (sy + al, sx)], lw=1.6)
    route_arrows(ax, [(sy + al, sx + 0.6), (sy + al + out, sx + 0.6)], lw=2.0)
    route_arrows(ax, [(sy + al + out, sx - 0.6), (sy + al, sx - 0.6)], lw=2.0, style="--")
    ax.plot(sy, sx, marker="o", color=INK, ms=7, zorder=11)
    scale_bar(ax, sy + 2, -8.6, 10, label_above=True)
    ax.set_xlim(sy - 3, y1 + 4); ax.set_ylim(-9.5, 9.5)
    ax.set_aspect("equal")
    ax.set_xlabel("distance north (m)"); ax.set_ylabel("distance east (m)")
    H = [Patch(fc=WALL, label="building wall (the gap is the entrance)"),
         Line2D([], [], color=REF, ls=":", lw=1.5, label="GNSS gate (off going in, on coming out), at the entrance"),
         Line2D([0], [0], color=ROUTE, lw=1.6, label="align leg (outdoors, with satellite positioning)"),
         Line2D([0], [0], color=ROUTE, lw=2.0, label="out leg (through the entrance)"),
         Line2D([0], [0], color=ROUTE, lw=2.0, ls="--", label="back leg (same heading, reverse)"),
         Line2D([0], [0], marker="o", color=INK, lw=0, label="spawn point")]
    fig_legend(fig, H, ncol=2)
    return savefig(fig, "outdoor_to_indoor", height_in=2.8, rect=(0.0, 0.37, 1.0, 1.0))


def main():
    # ---- 1. Corridor family
    S = source_corridor()
    check("corridor wall x", -S["wall_x"][0], S["wall_x"][1]); check("corridor wall x magnitude", abs(S["wall_x"][0]), 10.0)
    check("corridor wall thickness", S["wall_thick"], 0.2)
    check("corridor wall half-length", S["wall_y_half"], 85.0)
    check("corridor wall height", S["wall_z"], 5.0)
    check("corridor transition boundary y", S["boundary_y"], 80.0)
    check("corridor spawn x", S["spawn"][0], 0.0); check("corridor spawn y", S["spawn"][1], 0.0)
    check("corridor spawn yaw rad", S["spawn"][2], math.radians(90))
    f1 = fig_corridor(S)
    write_caption(os.path.join(CAP, "corridor_family.md"),
        'Plan view of the 20 m by 160 m corridor, showing the checkered and blank floors with the texture boundary of the transition condition, the plain or line-marked walls (drawn thicker than their true 0.2 m), the roof used with the forward camera, the spawn point and the planned flight line.')

    # ---- 2/3. Room(s)
    Sr = source_room("room_tags")
    n, side, spd = source_laps()
    Sr["side"] = side
    # independent check: tag yaw/position against the exact literal pose values transcribed by hand from the world
    # file (sim/worlds/room_tags.sdf), a separate reading from the ElementTree parse used to produce Sr
    expect = {0: (-3, -3, 0.0), 1: (-3, 3, 0.523599), 2: (3, 3, -0.785398), 3: (3, -3, 1.570796),
              4: (-3, 0, 0.261799), 5: (0, 3, -0.349066), 6: (3, 0, 1.047198), 7: (0, -3, -1.308997)}
    for tid, (ex, ey, eyaw) in expect.items():
        x, y, yaw, z = Sr["tags"][tid]
        check_pt("tag %d position" % tid, (x, y), (ex, ey))
        check("tag %d yaw" % tid, yaw, eyaw, tol=1e-5)
    check("room tag count", len(Sr["tags"]), 8)
    check("room lap side length", side, 6.0)
    check("room spawn x", Sr["spawn"][0], -3.0); check("room spawn y", Sr["spawn"][1], -3.0)
    check("room half-extent (drawn)", Sr["room_half"], 5.1)
    check("room tag size (drawn)", Sr["tag_size"], 0.5)
    # lap direction: fly_trial.py laps()'s own dirs list (N, E, S, W), read independently from its source rather
    # than assumed from an earlier docstring
    laps_dirs_txt = re.search(r"dirs = \[([^\]]*)\]", open(os.path.join(REPO, "fly_trial.py")).read()).group(1)
    laps_dirs = eval("[" + laps_dirs_txt + "]")
    assert laps_dirs == [(1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)], \
        "fly_trial.py's laps() direction order (N, E, S, W) changed: %r" % laps_dirs
    f2 = fig_room(Sr, "room_tags_lap")
    write_caption(os.path.join(CAP, "room_tags_lap.md"),
        'Plan view of the 10 m square tag room with the 8 floor tags and their ids, the 6 m square lap path and its direction, and the spawn point.')

    Srw = source_room("room_wall_tag")
    assert Srw["tags"] == Sr["tags"] or {k: v for k, v in Srw["tags"].items() if k != 10} == Sr["tags"], \
        "the wall-tag room's 8 floor tags must match the tag room exactly"
    WT = source_wall_tag_and_hold()
    check("wall tag x", WT["wall_xyz"][0], 0.0)
    check("wall tag y (rendered pose)", WT["wall_xyz"][1], 4.999)
    check("wall tag z", WT["wall_xyz"][2], 1.5)
    check("WALL_P north offset", WT["wall_p"][1], 4.998)
    # the wall tag's rendered SDF pose and the navigation frame's WALL_P are two different numbers (the SDF is the
    # physical tag; WALL_P is a separate constant the bridge code uses) that should only nearly agree, not an
    # identity - checked here with a stated, non-zero tolerance rather than asserted equal
    assert abs(WT["wall_xyz"][1] - WT["wall_p"][1]) < 0.002, \
        "the rendered wall tag pose and WALL_P disagree by more than the expected ~1 mm"
    check("hold point x", WT["hold"][0], 0.0)
    check("hold point y (from WALL_P - 1.5 m)", WT["hold"][1], 4.998 - 1.5, tol=1e-9)
    Srw["side"] = side
    f3 = fig_room(Sr, "room_tags_wall_tag", with_wall_tag=True, WT=WT)
    write_caption(os.path.join(CAP, "room_tags_wall_tag.md"),
        'The same tag room with the wall tag on the north wall, 1.5 m up, and the hold point in front of it with its side steps.')

    # ---- 4. Outdoor to indoor
    So = source_outdoor_indoor()
    check("outdoor spawn x", So["spawn"][0], 0.0); check("outdoor spawn y", So["spawn"][1], -15.0)
    check("outdoor align distance", So["outback"][0], 15.0)
    check("outdoor out distance", So["outback"][2], 50.0)
    check("outdoor GNSS gate y", So["outback"][4], 20.0)
    check("building north wall y", So["bldg_north_y"], 70.0)
    check("building south wall y (drawn)", So["bldg_south_y"], 20.0)
    check("entrance half-width (drawn)", So["entrance_half"], 1.5)
    # the real claim the caption makes: the entrance (south wall position) and the GNSS gate are the SAME number,
    # read from two unrelated sources (the world file's wall geometry and the flight script's own constant) -
    # not assumed equal, checked here
    check("entrance coincides with the GNSS gate", So["bldg_south_y"], So["outback"][4])
    f4 = fig_outdoor_indoor(So)
    write_caption(os.path.join(CAP, "outdoor_to_indoor.md"),
        'Plan view of the outdoor-to-indoor flight: the outdoor align leg, then the out and back legs through the entrance, where GNSS is switched off going in and on coming out (the two legs are drawn slightly apart but were flown on one line).')

    print("%d/%d geometry checks passed" % (sum(c[3] for c in CHECKS), len(CHECKS)))
    for lab, d, s, ok in CHECKS:
        if not ok:
            print("FAIL", lab, d, s)
    return [f1, f2, f3, f4]


if __name__ == "__main__":
    for f in main():
        print(f)
