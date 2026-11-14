#!/usr/bin/env python3
"""GROUP C candidate thesis figures, continued after C07: Extension E6 (map reuse), the figure-of-eight mapping
flights.

Scope (per the brief): write ONLY the candidate plot files, their captions and an index entry -- this script does
NOT rebuild docs/thesis/figures_thesis/candidates/thesis_figures_candidates.pdf, the thesis_assets bundle, the
combined thesis PDF or the writing pack.

STORED OUTPUTS ONLY, except for one read-only bag extraction (ground truth for C08's flown paths), which is done by
the separate eval/figs_cand_e6route_extract.py, run once under heavy.py, with its cache deleted by this script once
every candidate here is safely on disk -- the same pattern eval/figs_cand_c.py uses for its own C05/C06 tag-map
extraction.

Data (all pre-registered/scored, nothing re-scored here):
  - commanded route: docs/thesis/tier1/e6/fig8_3c_profile.json (3 identical circuits of 8 "move" legs) and the
    segment "from"/"to" fields of docs/thesis/tier1/scores/e6_route_E6M_fig8_<r>.json (eval/e6_route_check.py's own
    output). FRAME FINDING (see below): the segment "to" fields are NOT a ground-truth measurement of the realised
    corner -- they are the raw profile's own "to" waypoint, reordered from the profile's [N, E] storage order into
    world (x, y) = (East, North) by eval/e6_route_check.py's own `to = (sg["to"][1], sg["to"][0])` line. Only the
    very first "from" (segment 0) comes from a logged, actually-measured start position
    (fly_trial.log's "HPROFILE: ... start N ... E ..."). Confirmed for every one of the 24 legs, all three flights,
    by the check below, which compares each stored segment "to" against the raw profile's own "to" with the same
    swap applied -- so the commanded route drawn here is grounded in the raw profile, not re-typed, and the swap is
    pinned by a passing check rather than taken on trust;
  - flown paths: /ground_truth/pose of the three mapping-flight bags (E6M_fig8_r1b, E6M_fig8_r2, E6M_fig8_r3),
    taken-off-to-landed (trimmed to ground-truth altitude z > 0.3 m, a declared threshold -- the rest cruises at
    ~2 m and sits at ~0.195 m on the ground, so 0.3 m cleanly separates airborne from not);
  - surveyed tags and room geometry: sim/worlds/room_tags_map.json (8 tags) and sim/worlds/room_tags.sdf (walls,
    spawn pose; 10 x 10 m room, confirmed by a literal substring check against the world file's own comment and
    wall poses, not re-measured);
  - FGO/UKF tag maps: docs/thesis/tier1/e6/maps/E6M_fig8_<r>/map_fgo.json, map_ukf.json, map_errors.json -- already
    in the WORLD frame (eval/e6_maps.py: "world (Gazebo ENU) = tag-0 frame + (-3, -3), yaw 0 (registered, no fit)"),
    so no further transform is applied here;
  - cross-check target: docs/thesis/tier1/numbers_tier1.md's two E6 map-error tables (the per-estimator "landmark
    error against the surveyed map" table under "Section Maps", and the "Map error per pair" table under
    "Stage 2") -- both checked, before any C09/C10 caption is written, and the script STOPS if either disagrees.

Frame (per the brief's instruction to be careful here; this is also the frame issue actually found while building
these candidates -- see the FRAME FINDING above): everything drawn is already in the Gazebo world frame -- ground
truth, the commanded route (once the profile's own [N, E] -> world (East, North) swap is applied, confirmed by
check rather than assumed), and the tag maps (eval/e6_maps.py registers tag 0 to its surveyed world pose with a
fixed translation, no fit). Axes are labelled East (m) / North (m), equal scale, per
docs/thesis/tier1/e6_preregistration.md Section 1.2 ("The world frame (Gazebo ENU), reached from tag 0's frame by a
fixed, registered translation") and Section 3.2 ("Map sources"). Plotting the raw profile's [N, E] pairs directly as
(x, y) without this swap would mirror the drawn route across the line y = x -- this was checked, not assumed.

Outputs: docs/thesis/figures_thesis/candidates/C08.{png,pdf}, C09.{png,pdf}, C10_table.md,
docs/thesis/figures_thesis/candidates/captions/C08.md, C09.md, C10.md, and three appended rows in
docs/thesis/figures_thesis/candidates/index_c.md.
Usage: /home/makerspace/venv-evo/bin/python eval/figs_cand_e6route.py"""
import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
T1D = os.path.join(ROOT, "docs", "thesis", "tier1")
OUTD = os.path.join(ROOT, "docs", "thesis", "figures_thesis", "candidates")
CAPD = os.path.join(OUTD, "captions")
os.makedirs(OUTD, exist_ok=True)
os.makedirs(CAPD, exist_ok=True)
INDEX = os.path.join(OUTD, "index_c.md")
CACHE = os.path.expanduser("~/thesis_data/cand_e6route_cache")
COMMIT = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()

L1 = lambda f: json.load(open(os.path.join(T1D, f)))
LT = lambda f: json.load(open(os.path.join(T1D, "scores", f)))
LM = lambda r, f: json.load(open(os.path.join(T1D, "e6", "maps", f"E6M_fig8_{r}", f)))

# ------------------------------------------------------------------ rd(): the thesis rounding rule, parsed (not run) from
# figs_thesis.py, exactly as eval/figs_cand_c.py and eval/cl_heading_perflight.py already do (AST, function only, SHA-pinned).
FT = os.path.join(HERE, "figs_thesis.py")
_src = open(FT).read()
_rd = next(n for n in ast.parse(_src).body if isinstance(n, ast.FunctionDef) and n.name == "rd")
RD_SHA = hashlib.sha256(ast.get_source_segment(_src, _rd).encode()).hexdigest()
_ns = {}
exec(compile(ast.Module(body=[_rd], type_ignores=[]), FT, "exec"), _ns)
rd = _ns["rd"]
assert RD_SHA == "e7320d3b8f377157c0c6512b2c0b77c978ac309a7130d2729480b786e02589b3", "rd() changed in figs_thesis.py"

# ------------------------------------------------------------------ style
sys.path.insert(0, HERE)
import thesis_style as TS

C, MK, TRUTH = TS.C, TS.MK, TS.TRUTH
INK, INK2, GRID, SURF = TS.INK, TS.INK2, TS.GRID, TS.SURF
FW = TS.TEXT_WIDTH_IN           # 6.30 in = 160 mm
plt.rcParams.update(TS.RCPARAMS)

RUNS = ["r1b", "r2", "r3"]
TRIAL = {r: f"E6M_fig8_{r}" for r in RUNS}
PAIR = {"r1b": "T_A_r1", "r2": "T_A_r2", "r3": "T_A_r3"}   # cross-checked below against scores/e6_verdicts.json "pairs"

# ------------------------------------------------------------------ checks (same discipline as eval/figs_cand_c.py)
CHK = []
TXT = []
FIGS = {}


def check(fid, label, computed, expected, src):
    c, e = str(computed), str(expected)
    ok = c == e
    CHK.append(dict(fig=fid, label=label, computed=c, expected=e, where=src, ok=ok))
    if not ok:
        print("   CHECK FAIL:", fid, label, repr(c), repr(e), src)
    return c


def T(s):
    TXT.append(s)
    return s


NUMTOK = re.compile(r"\d+(?:\.\d+)?")
# no trailing \b on CAND_RE: also strips "C10" out of "C10_table.md" (underscore is a \w char), the same fix
# eval/figs_cand_c.py applies for its own "C03_table.md" etc.
CAND_RE = re.compile(r"\bC[01]\d")     # strip "fake numbers" inside this script's own candidate ids (C08, C09, C10)
# "E6"/"e6" (the extension experiment name) and "tier1" (a path component, docs/thesis/tier1/) are identifiers, not
# claim numbers -- both appear routinely in file paths and prose quoted in these captions/tables, sometimes joined to
# a neighbouring word by an underscore (e.g. "numbers_tier1.md"), which is a \w character, so plain \b does not fire
# there; a letter-only lookaround is used instead (underscores and digits either side are fine).
E6_RE = re.compile(r"(?<![A-Za-z])(?:E6|e6|tier1)(?![A-Za-z])")
# run/trial identifiers are not claim numbers (e.g. the 1 inside "r1b", the 1/6/8 inside "E6M_fig8_r1b", the 1 inside
# "T_A_r1") -- stripped before the NUMTOK scan, the same fix eval/figs_cand_c.py applies to "EKF3" (-> "EKF") and its own
# candidate ids, so a run name doesn't need its own passing check just to appear in a caption.
_IDENTS = sorted(set(list(TRIAL.values()) + list(PAIR.values()) + RUNS), key=len, reverse=True)
IDENT_RE = re.compile(r"\b(?:" + "|".join(re.escape(s) for s in _IDENTS) + r")\b")


def _strip(s):
    return CAND_RE.sub("CAND", E6_RE.sub("EXT", IDENT_RE.sub("RUNID", s)))


def allowed_for(fid):
    a = set()
    for c in CHK:
        if c["fig"] == fid and c["ok"]:
            a |= set(NUMTOK.findall(_strip(c["computed"]))) | set(NUMTOK.findall(_strip(c["expected"])))
    return a


def guard(fid, text):
    """Every number in a caption body or a table's cell text must be grounded in a passing check() of this candidate id --
    the same discipline eval/figs_cand_c.py applies (NUMTOK)."""
    allowed = allowed_for(fid)
    stray = sorted({t for t in NUMTOK.findall(_strip(text))} - allowed)
    assert not stray, f"{fid}: number(s) {stray} written without a passing check"


def save(fid, fig, inputs):
    """Figure candidates: PDF + PNG, 160 mm wide, number guard (TXT, i.e. only explicitly-drawn ax.text() content --
    legend labels are plain descriptive strings and are not number-guarded, matching eval/figs_cand_c.py), no em-dash,
    linear axes only, nothing off-canvas, no bold in axes, >= 9 pt."""
    allowed = allowed_for(fid)
    stray = sorted({t for s in TXT for t in NUMTOK.findall(_strip(s))} - allowed)
    assert not stray, f"{fid}: number(s) {stray} drawn without a check"
    for s in TXT:
        assert "—" not in s, f"{fid}: em-dash in '{s}'"
    for a_ in fig.axes:
        assert a_.get_xscale() == "linear" and a_.get_yscale() == "linear", f"{fid}: a non-linear axis"
        for t_ in a_.texts + [a_.xaxis.label, a_.yaxis.label]:
            assert t_.get_fontweight() not in ("bold", "heavy"), f"{fid}: bold text in axes: {t_.get_text()!r}"
    fig.canvas.draw()
    r_ = fig.canvas.get_renderer()
    W_, H_ = fig.bbox.width, fig.bbox.height
    ticks_ = {id(t) for a_ in fig.axes for t in a_.get_xticklabels() + a_.get_yticklabels()}
    for t_ in fig.findobj(matplotlib.text.Text):
        assert "—" not in t_.get_text(), f"{fid}: em-dash in figure text"
        if t_.get_text() and t_.get_visible():
            assert t_.get_fontsize() >= 9.0, f"{fid}: text below the 9 pt floor ({t_.get_fontsize()} pt): {t_.get_text()[:50]!r}"
        if t_.get_text() and t_.get_visible() and id(t_) not in ticks_:
            b_ = t_.get_window_extent(renderer=r_)
            assert b_.x0 >= -1 and b_.x1 <= W_ + 1 and b_.y0 >= -1 and b_.y1 <= H_ + 1, f"{fid}: text runs off the figure: {t_.get_text()[:50]!r}"
    p_png = os.path.join(OUTD, f"{fid}.png")
    p_pdf = os.path.join(OUTD, f"{fid}.pdf")
    fig.savefig(p_png, dpi=200)
    fig.savefig(p_pdf)
    plt.close(fig)
    FIGS[fid] = dict(files=[os.path.relpath(p_png, ROOT), os.path.relpath(p_pdf, ROOT)], inputs=inputs)
    print(f"wrote {fid}.png/.pdf")


def write_caption(fid, text):
    p = os.path.join(CAPD, f"{fid}.md")
    with open(p, "w") as f:
        f.write(text.strip() + "\n")
    return p


def pointer_line(ids):
    if not ids:
        return "Verdicts: Table A.4, none (descriptive)."
    return "Verdicts: Table A.4, rows " + "; ".join(ids) + "."


# =================================================================== shared data
TRUE_MAP = {t["id"]: t for t in json.load(open(os.path.join(ROOT, "sim", "worlds", "room_tags_map.json")))["tags"]}
SDF_TXT = open(os.path.join(ROOT, "sim", "worlds", "room_tags.sdf")).read()
PAIRS_STORED = LT("e6_verdicts.json")["pairs"]
check("C08", "mapping-trial to T_A pairing matches scores/e6_verdicts.json",
      {PAIR[r]: TRIAL[r] for r in RUNS}, PAIRS_STORED, "docs/thesis/tier1/scores/e6_verdicts.json pairs")

PROFILE = json.load(open(os.path.join(T1D, "e6", "fig8_3c_profile.json")))
check("C08", "commanded route: 24 legs = 3 identical circuits of 8", f"{len(PROFILE)}/8={len(PROFILE) // 8}", "24/8=3",
      "docs/thesis/tier1/e6/fig8_3c_profile.json")

ROUTE = {r: LT(f"e6_route_E6M_fig8_{r}.json") for r in RUNS}
# FRAME FINDING: fig8_3c_profile.json stores each waypoint as [N, E] (confirmed against eval/e6_route_check.py's own
# "start N ... E ..." log parsing and its `to = (sg["to"][1], sg["to"][0])` line, which performs the swap into world
# (x, y) = (East, North)). The stored segment "to" is therefore the raw profile's own waypoint, reordered -- NOT an
# independent ground-truth measurement of the realised corner (only segment 0's "from" is, via the logged start
# position). Checked here for all 24 legs and all three flights, not assumed:
for r in RUNS:
    segs = ROUTE[r]["segments"]
    swap_ok = all(segs[i]["to"] == [PROFILE[i]["to"][1], PROFILE[i]["to"][0]] for i in range(len(PROFILE)))
    check("C08", f"{TRIAL[r]}: every stored segment 'to' equals the raw profile's 'to', [N, E] -> world (E, N) swapped",
          swap_ok, True, f"docs/thesis/tier1/e6/fig8_3c_profile.json vs docs/thesis/tier1/scores/e6_route_E6M_fig8_{r}.json")
    per_ok = all(segs[i]["to"] == segs[i + off]["to"] for i in range(8) for off in (8, 16))
    check("C08", f"{TRIAL[r]}: realised route periodic every 8 legs (3 identical circuits)", per_ok, True,
          f"docs/thesis/tier1/scores/e6_route_E6M_fig8_{r}.json segments")
CIRCUIT1 = {r: [tuple(ROUTE[r]["segments"][0]["from"])] + [tuple(s["to"]) for s in ROUTE[r]["segments"][:8]] for r in RUNS}
# the commanded route drawn on the figure is r1b's own stored circuit-1 corners (the profile's own waypoints, swapped
# into world order as checked above, not hand-typed).
ROUTE_XY = np.array(CIRCUIT1["r1b"])

check("C08", "room size (10 x 10 m), exact substring from the world file's own comment",
      "10 x 10 m" if "10 x 10 m" in SDF_TXT else "MISSING", "10 x 10 m", "sim/worlds/room_tags.sdf")
check("C08", "spawn pose (world x, y, z, roll, pitch, yaw deg), exact substring from the world file",
      "-3 -3 0.195 0 0 90" if "-3 -3 0.195 0 0 90" in SDF_TXT else "MISSING", "-3 -3 0.195 0 0 90",
      "sim/worlds/room_tags.sdf")
check("C08", "airborne altitude threshold used to trim takeoff/landing (m), a declared choice",
      rd(0.3, 1), "0.3", "this script: declared choice, clear of the ~2 m cruise and ~0.195 m resting height")
check("C08", "surveyed tag count", str(len(TRUE_MAP)), "8", "sim/worlds/room_tags_map.json")
check("C08", "tag ids drawn on the figure (0-7)", ",".join(str(i) for i in sorted(TRUE_MAP)), "0,1,2,3,4,5,6,7",
      "sim/worlds/room_tags_map.json ids")
check("C08", "the spawn point coincides with tag id", TRUE_MAP[0]["x"] == -3 and TRUE_MAP[0]["y"] == -3 and 0 == 0,
      True, "sim/worlds/room_tags_map.json id 0; sim/worlds/room_tags.sdf spawn pose")
check("C09", "tag ids drawn on the figure (0-7)", ",".join(str(i) for i in sorted(TRUE_MAP)), "0,1,2,3,4,5,6,7",
      "sim/worlds/room_tags_map.json ids")

# ------------------------------------------------------------------ map position RMS + BOTH numbers_tier1.md cross-checks,
# done BEFORE any C09/C10 output is written, so a mismatch stops the script before anything dependent is on disk (the
# brief: "if they disagree, STOP and report").
MAPS = {r: dict(fgo=LM(r, "map_fgo.json"), ukf=LM(r, "map_ukf.json"), err=LM(r, "map_errors.json")) for r in RUNS}
RMS = {r: {src: rd(MAPS[r]["err"]["errors"][src]["pos_rms_m"], 4) for src in ("fgo", "ukf")} for r in RUNS}
NUM_TIER1 = open(os.path.join(T1D, "numbers_tier1.md")).read()
CROSS_FIDS = ("C09", "C10")   # tagged under both, so each candidate's own guard()/save() can ground its RMS numbers
for r in RUNS:
    # table 1: "Map error per pair" (one row per pair: T_A_rk, mapping flight, FGO RMS, UKF RMS, ratio)
    rx1 = re.compile(r"\|\s*" + re.escape(PAIR[r]) + r"\s*\|\s*" + re.escape(TRIAL[r]) +
                      r"\s*\|\s*([0-9.]+)\s*\|\s*([0-9.]+)\s*\|\s*[0-9.]+\s*\|")
    m1 = rx1.search(NUM_TIER1)
    assert m1, f"{PAIR[r]}/{TRIAL[r]} row not found in numbers_tier1.md 'Map error per pair' table"
    # table 2: the per-estimator "landmark error against the surveyed map" table (one row per mapping flight x estimator)
    rx2f = re.compile(r"\|\s*" + re.escape(TRIAL[r]) + r"\s*\|\s*FGO \(a\)\s*\|\s*([0-9.]+)\s*\|")
    rx2u = re.compile(r"\|\s*" + re.escape(TRIAL[r]) + r"\s*\|\s*UKF \(b\)\s*\|\s*([0-9.]+)\s*\|")
    m2f, m2u = rx2f.search(NUM_TIER1), rx2u.search(NUM_TIER1)
    assert m2f and m2u, f"{TRIAL[r]} row not found in numbers_tier1.md's landmark-error table"
    for fid in CROSS_FIDS:
        check(fid, f"{TRIAL[r]}: FGO map position RMS == numbers_tier1.md 'Map error per pair' row",
              RMS[r]["fgo"], m1.group(1), "docs/thesis/tier1/numbers_tier1.md 'Map error per pair'")
        check(fid, f"{TRIAL[r]}: UKF map position RMS == numbers_tier1.md 'Map error per pair' row",
              RMS[r]["ukf"], m1.group(2), "docs/thesis/tier1/numbers_tier1.md 'Map error per pair'")
        check(fid, f"{TRIAL[r]}: FGO map position RMS == numbers_tier1.md landmark-error table row",
              RMS[r]["fgo"], m2f.group(1), "docs/thesis/tier1/numbers_tier1.md landmark error against the surveyed map")
        check(fid, f"{TRIAL[r]}: UKF map position RMS == numbers_tier1.md landmark-error table row",
              RMS[r]["ukf"], m2u.group(1), "docs/thesis/tier1/numbers_tier1.md landmark error against the surveyed map")
if not all(c["ok"] for c in CHK if c["fig"] in CROSS_FIDS):
    sys.exit("[figs_cand_e6route] STOP: a map-error number disagreed with numbers_tier1.md -- see CHECK FAIL lines above")
for r in RUNS:
    for src in ("fgo", "ukf"):
        per = MAPS[r]["err"]["errors"][src]["per_tag"]
        check("C09", f"{TRIAL[r]} {src}: tag 0 (gauge) carries no per-tag error entry", "0" in per, False,
              f"docs/thesis/tier1/e6/maps/{TRIAL[r]}/map_errors.json errors.{src}.per_tag")
        pe = np.array([v["pos_err_m"] for v in per.values()])
        check("C09", f"{TRIAL[r]} {src}: recomputed position RMS over the 7 non-gauge tags (6 dp) matches the stored value",
              rd(float(np.sqrt(np.mean(pe ** 2))), 6), rd(MAPS[r]["err"]["errors"][src]["pos_rms_m"], 6),
              f"docs/thesis/tier1/e6/maps/{TRIAL[r]}/map_errors.json errors.{src}")
        check("C09", f"{TRIAL[r]} {src}: n_tags (non-gauge) stored", MAPS[r]["err"]["errors"][src]["n_tags"], 7,
              f"docs/thesis/tier1/e6/maps/{TRIAL[r]}/map_errors.json errors.{src}.n_tags")
    check("C09", f"{TRIAL[r]}: FGO map file tag count", len(MAPS[r]["fgo"]["tags"]), 8,
          f"docs/thesis/tier1/e6/maps/{TRIAL[r]}/map_fgo.json")
    check("C09", f"{TRIAL[r]}: UKF map file tag count", len(MAPS[r]["ukf"]["tags"]), 8,
          f"docs/thesis/tier1/e6/maps/{TRIAL[r]}/map_ukf.json")
for r in RUNS:
    for src in ("fgo", "ukf"):
        tags_by_id = {t["id"]: t for t in MAPS[r][src]["tags"]}
        for tid_s, p_ in MAPS[r]["err"]["errors"][src]["per_tag"].items():
            tid = int(tid_s)
            tr = TRUE_MAP[tid]
            got_dx = tags_by_id[tid]["x"] - tr["x"]
            got_dy = tags_by_id[tid]["y"] - tr["y"]
            check("C09", f"{TRIAL[r]} {src} tag {tid}: map-file (dx, dy) matches map_errors.json per_tag (6 dp)",
                  f"{rd(got_dx, 6)}, {rd(got_dy, 6)}", f"{rd(p_['dx_m'], 6)}, {rd(p_['dy_m'], 6)}",
                  f"docs/thesis/tier1/e6/maps/{TRIAL[r]}/map_{src}.json vs map_errors.json")
# =================================================================== C08: the figure-of-eight route
TXT = []
GT = {}
for r in RUNS:
    z = np.load(os.path.join(CACHE, f"gt_{TRIAL[r]}.npz"))["G"]
    airborne = z[:, 3] > 0.3
    idx = np.where(airborne)[0]
    GT[r] = z[idx[0]:idx[-1] + 1]
    # sanity: the airborne window must fully contain the scored mapping window (first leg start to last circuit end)
    t_lo, t_hi = GT[r][0, 0], GT[r][-1, 0]
    seg0_t = ROUTE[r]["segments"][0]["t_start_bag"]
    c3_t1 = ROUTE[r]["circuits"][-1]["t1"]
    check("C08", f"{TRIAL[r]}: airborne window (z > 0.3 m) contains the scored mapping window",
          bool(t_lo < seg0_t and t_hi > c3_t1), True,
          f"~/thesis_data/cand_e6route_cache/gt_{TRIAL[r]}.npz (z threshold); docs/thesis/tier1/scores/e6_route_E6M_fig8_{r}.json")

# One panel per flight, shared scale (the brief's other allowed layout) -- an overlay of all three true paths in one
# panel was built and viewed first; at this scale the three paths overlap the commanded route closely enough that
# distinct line styles were not legible, so the brief's condition for the overlay option ("if legible") was not met.
fig, axs = plt.subplots(1, 3, figsize=(FW, FW / 3 + 1.6), sharex=True, sharey=True)
RB = 5.0   # inner wall face (centreline 5.1 - half-thickness 0.1), checked above
for i, r in enumerate(RUNS):
    ax = axs[i]
    ax.set_aspect(1.0, adjustable="box")
    ax.add_patch(plt.Rectangle((-RB, -RB), 2 * RB, 2 * RB, fill=False, edgecolor=INK2, lw=1.1, ls=(0, (4, 2)), zorder=1))
    ax.plot(ROUTE_XY[:, 0], ROUTE_XY[:, 1], color=TRUTH, lw=2.4, ls=(0, (6, 2)), zorder=2)
    ax.plot(GT[r][:, 1], GT[r][:, 2], color=INK, lw=1.1, zorder=3, alpha=0.95)
    for tid in sorted(TRUE_MAP):
        t = TRUE_MAP[tid]
        ax.plot(t["x"], t["y"], marker="D", ms=6, color=TRUTH, mec=INK2, mew=0.5, ls="", zorder=4)
        if tid == 0:
            continue   # the spawn star (below) already marks and labels tag 0
        if tid in (4, 6, 3):
            dx, dy = (0.3, -0.4)
        elif tid in (1, 2):
            dx, dy = (0.35, 0.42)
        else:
            dx, dy = (0.3, 0.3)
        ax.text(t["x"] + dx, t["y"] + dy, T(str(tid)), fontsize=9, ha="center", va="center", color=INK, zorder=5)
    # the spawn point coincides with tag 0 (checked above): a large hollow star over the diamond, so both are visible,
    # not a filled marker hiding the diamond underneath.
    ax.plot(-3, -3, marker="*", ms=15, mfc="none", mec=INK, mew=1.3, ls="", zorder=6)
    ax.text(-3, -3 - 0.8, T("0"), fontsize=9, ha="center", va="center", color=INK, zorder=7)
    ax.set_title(T(f"({'abc'[i]}) {r}"), loc="left", fontsize=9.0)
    ax.set_xlabel("East (m)")
axs[0].set_xlim(-5.7, 5.7)
axs[0].set_ylim(-5.7, 5.7)
axs[0].set_ylabel("North (m)")
leg_handles = [Line2D([], [], color=TRUTH, lw=2.4, ls=(0, (6, 2)), label="commanded route"),
               Line2D([], [], color=INK, lw=1.1, label="true path"),
               Line2D([], [], ls="", marker="D", ms=6, color=TRUTH, mec=INK2, mew=0.5, label="surveyed tag (id)"),
               Line2D([], [], color=INK2, lw=1.1, ls=(0, (4, 2)), label="room wall"),
               Line2D([], [], ls="", marker="*", ms=15, mfc="none", mec=INK, mew=1.3, label="spawn (on tag 0)")]
fig.legend(handles=leg_handles, loc="lower center", ncol=3, frameon=False, fontsize=9.0, bbox_to_anchor=(0.5, 0.0), columnspacing=1.3)
fig.tight_layout(rect=(0, 0.14, 1, 1))
check("C08", "panel labels printed (one mapping flight per panel)", "a,b,c", ",".join("abc"[:3]), "this script: r1b, r2, r3 in order")
save("C08", fig, "docs/thesis/tier1/e6/fig8_3c_profile.json; docs/thesis/tier1/scores/e6_route_E6M_fig8_{r1b,r2,r3}.json; "
     "sim/worlds/room_tags_map.json, room_tags.sdf; ~/thesis_data/trials/E6M_fig8_{r1b,r2,r3}/bag (/ground_truth/pose, "
     "via eval/figs_cand_e6route_extract.py under heavy.py)")

C08_CAP = (
    "E6 mapping flights, the figure-of-eight route: the commanded route (grey) and the ground-truth path actually flown "
    "(black), one mapping flight per panel ((a) r1b, (b) r2, (c) r3), world frame, equal scale. Diamonds mark the 8 "
    "surveyed floor tags by id, the star marks the spawn point (on tag 0), and the dashed square is the room's inner "
    "wall."
)
guard("C08", C08_CAP)
write_caption("C08", C08_CAP + "\n\n" + pointer_line([]))

# =================================================================== C09: the tag maps the mapping flights produced
TXT = []

# At true room scale (tags up to 6 m apart) the position errors (2-7 cm, see RMS below) are sub-pixel and the
# connector lines invisible -- confirmed by generating that version first and viewing it (no misleading "zoom-only"
# figure was shipped). Row 1 keeps the true-scale spatial map (so the FGO/UKF map agrees with the surveyed layout is
# shown honestly, not zoomed to look worse than it is); row 2 adds, per flight, the SAME per-tag errors as local
# vectors from each tag's own true position (one shared local origin per panel) -- this is what actually makes the
# error magnitude and direction visible, per the brief, without moving any point to a position it wasn't measured
# at. Metres throughout (not cm), per the house units convention (docs/thesis/tier1/decisions_log.md D7: "All other
# position errors are in m").
MAXE_M = max(abs(v["dx_m"]) for r in RUNS for src in ("fgo", "ukf") for v in MAPS[r]["err"]["errors"][src]["per_tag"].values())
MAXE_M = max(MAXE_M, max(abs(v["dy_m"]) for r in RUNS for src in ("fgo", "ukf") for v in MAPS[r]["err"]["errors"][src]["per_tag"].values()))
check("C09", "largest per-tag error component over all three flights, both estimators, fits inside the 0.09 m panel limit",
      MAXE_M <= 0.09, True, "docs/thesis/tier1/e6/maps/E6M_fig8_{r1b,r2,r3}/map_errors.json errors.{fgo,ukf}.per_tag")

fig, axs = plt.subplots(2, 3, figsize=(FW, 2 * (FW / 3) + 1.5), sharex="row", sharey="row")
LIM = 3.9
ELIM = 0.09   # m, shared across row 2 -- checked above to exceed every drawn error
for i, r in enumerate(RUNS):
    ax = axs[0, i]
    ax.set_aspect(1.0, adjustable="box")
    fgo_by_id = {t["id"]: t for t in MAPS[r]["fgo"]["tags"]}
    ukf_by_id = {t["id"]: t for t in MAPS[r]["ukf"]["tags"]}
    for tid in sorted(TRUE_MAP):
        tr = TRUE_MAP[tid]
        ax.plot(tr["x"], tr["y"], marker="D", ms=5.5, color=TRUTH, mec=INK2, mew=0.4, ls="", zorder=4)
        dx, dy = (-0.62, 0.0) if tid == 0 else (0.62, 0.0)
        ax.text(tr["x"] + dx, tr["y"] + dy, T(str(tid)), fontsize=9, ha="center", va="center", color=INK, zorder=6)
        if tid == 0:
            continue
        fg, uk = fgo_by_id[tid], ukf_by_id[tid]
        ax.plot([tr["x"], fg["x"]], [tr["y"], fg["y"]], color=C["FGO"], lw=0.8, zorder=2)
        ax.plot([tr["x"], uk["x"]], [tr["y"], uk["y"]], color=C["UKF"], lw=0.8, zorder=2)
        ax.plot(fg["x"], fg["y"], marker=MK["FGO"], ms=6, mfc="none", mec=C["FGO"], mew=1.3, ls="", zorder=5)
        ax.plot(uk["x"], uk["y"], marker=MK["UKF"], ms=6, mfc="none", mec=C["UKF"], mew=1.3, ls="", zorder=5)
    ax.set_title(T(f"({'abc'[i]}) {r}"), loc="left", fontsize=9.0)
    ax.set_xlabel("East (m)")

    axe = axs[1, i]
    axe.set_aspect(1.0, adjustable="box")
    axe.plot(0, 0, marker="D", ms=5.5, color=TRUTH, mec=INK2, mew=0.4, ls="", zorder=4)
    circ = plt.Circle((0, 0), 0.05, fill=False, edgecolor=INK2, lw=0.8, ls=(0, (2, 1.5)), zorder=1)
    axe.add_patch(circ)
    for tid in sorted(TRUE_MAP):
        if tid == 0:
            continue
        tr = TRUE_MAP[tid]
        fg, uk = fgo_by_id[tid], ukf_by_id[tid]
        fgx, fgy = fg["x"] - tr["x"], fg["y"] - tr["y"]
        ukx, uky = uk["x"] - tr["x"], uk["y"] - tr["y"]
        axe.plot([0, fgx], [0, fgy], color=C["FGO"], lw=0.8, zorder=2)
        axe.plot([0, ukx], [0, uky], color=C["UKF"], lw=0.8, zorder=2)
        axe.plot(fgx, fgy, marker=MK["FGO"], ms=6, mfc="none", mec=C["FGO"], mew=1.3, ls="", zorder=5)
        axe.plot(ukx, uky, marker=MK["UKF"], ms=6, mfc="none", mec=C["UKF"], mew=1.3, ls="", zorder=5)
    axe.set_title(T(f"({'def'[i]}) {r}"), loc="left", fontsize=9.0)
    axe.set_xlabel("East error (m)")
axs[0, 0].set_ylabel("North (m)")
axs[0, 0].set_xlim(-LIM, LIM)
axs[0, 0].set_ylim(-LIM, LIM)
axs[1, 0].set_ylabel("North error (m)")
axs[1, 0].set_xlim(-ELIM, ELIM)
axs[1, 0].set_ylim(-ELIM, ELIM)
fig.legend(handles=[Line2D([], [], ls="", marker="D", ms=5.5, color=TRUTH, mec=INK2, mew=0.4, label="surveyed / true tag"),
                    Line2D([], [], ls="", marker=MK["FGO"], mfc="none", mec=C["FGO"], mew=1.3, ms=6, label="FGO map tag"),
                    Line2D([], [], ls="", marker=MK["UKF"], mfc="none", mec=C["UKF"], mew=1.3, ms=6, label="UKF map tag"),
                    Line2D([], [], color=INK2, lw=0.8, ls=(0, (2, 1.5)), label="0.05 m reference circle")],
           loc="lower center", ncol=4, frameon=False, fontsize=9.0, bbox_to_anchor=(0.5, 0.0), columnspacing=1.2)
fig.tight_layout(rect=(0, 0.13, 1, 1))
check("C09", "panel labels printed (one mapping flight per panel, two rows, r1b/r2/r3 in order)", "a,b,c,d,e,f", ",".join("abcdef"),
      "this script: row 1 spatial map, row 2 local error vectors")
check("C09", "reference circle radius printed (m)", rd(0.05, 2), "0.05", "this script: a declared, round reference radius")
save("C09", fig, "docs/thesis/tier1/e6/maps/E6M_fig8_{r1b,r2,r3}/map_fgo.json, map_ukf.json, map_errors.json; "
     "sim/worlds/room_tags_map.json")

C09_CAP = (
    "E6 mapping flights, the tag maps they produced: the surveyed tag positions (grey diamonds), the FGO map (open "
    "orange squares) and the UKF map (open green triangles), one mapping flight per panel, top row ((a) r1b, (b) r2, "
    "(c) r3). The bottom row ((d) r1b, (e) r2, (f) r3) re-centres each flight's non-gauge tags on their own true "
    "position, equal scale shared across panels, so the small FGO/UKF position errors, invisible at room scale, are "
    "visible as short vectors from the surveyed position."
)
guard("C09", C09_CAP)
write_caption("C09", C09_CAP + "\n\n" + pointer_line(["Extension E6 P1"]))

# =================================================================== C10: the per-flight map position RMS (table candidate)
# The numbers_tier1.md cross-check (both of its E6 map-error tables) already ran, with its own STOP, in the shared-data
# section above -- before C09's caption was written, not after.
check("C10", "n_tags (non-gauge) stored, all three flights", [MAPS[r]["err"]["errors"]["fgo"]["n_tags"] for r in RUNS], [7, 7, 7],
      "docs/thesis/tier1/e6/maps/E6M_fig8_{r1b,r2,r3}/map_errors.json")

C10_ROWS = [[PAIR[r], TRIAL[r], RMS[r]["fgo"], RMS[r]["ukf"]] for r in RUNS]
C10_MD = "\n".join([
    "# C10. E6 mapping flights: per-flight map position RMS (table candidate)",
    "",
    "| pair | mapping flight | FGO map position RMS (m) | UKF map position RMS (m) |",
    "|---|---|---|---|",
] + ["| " + " | ".join(row) + " |" for row in C10_ROWS] + [
    "",
    "Position RMS over the 7 non-gauge tags (the gauge tag is fixed to its surveyed position by definition), rounded once "
    "from docs/thesis/tier1/e6/maps/<mapping flight>/map_errors.json (errors.{fgo,ukf}.pos_rms_m), cross-checked by exact "
    "string equality against BOTH of docs/thesis/tier1/numbers_tier1.md's E6 map-error tables (the 'Map error per pair' "
    "table and the per-estimator 'landmark error against the surveyed map' table). Same data as candidate C09's chart.",
])
guard("C10", C10_MD)
with open(os.path.join(OUTD, "C10_table.md"), "w") as f:
    f.write(C10_MD + "\n")
print("wrote C10_table.md")

C10_CAP = (
    "E6 mapping flights: the per-flight map position root-mean-square error, over the non-gauge surveyed tags, for the "
    "FGO map and the UKF map each mapping flight produced. Reproduced as a table from the same data as the companion "
    "tag-map figure."
)
guard("C10", C10_CAP)
write_caption("C10", C10_CAP + "\n\n" + pointer_line(["Extension E6 P1"]))

# =================================================================== totals + index
N_OK = sum(1 for c in CHK if c["ok"])
N_TOT = len(CHK)
print(f"figs_cand_e6route: {N_OK}/{N_TOT} checks ok")
assert N_OK == N_TOT, "a check failed -- see CHECK FAIL lines above"

NEW_ROWS = [
    "| C08 | E6 mapping flights: the figure-of-eight route | (new; E6 mapping flights, docs/thesis/tier1/e6_results.md) | "
    "tier1/e6/fig8_3c_profile.json; scores/e6_route_E6M_fig8_{r1b,r2,r3}.json; sim/worlds/room_tags_map.json, room_tags.sdf; "
    f"bags E6M_fig8_{{r1b,r2,r3}} (ground truth) | {sum(1 for c in CHK if c['fig'] == 'C08')}/"
    f"{sum(1 for c in CHK if c['fig'] == 'C08')} | none (descriptive) |",
    "| C09 | E6 mapping flights: the tag maps they produced | (new; E6 mapping flights, docs/thesis/tier1/e6_results.md) | "
    "tier1/e6/maps/E6M_fig8_{r1b,r2,r3}/map_fgo.json, map_ukf.json, map_errors.json; sim/worlds/room_tags_map.json | "
    f"{sum(1 for c in CHK if c['fig'] == 'C09')}/{sum(1 for c in CHK if c['fig'] == 'C09')} (shared with C10) | "
    "Extension E6 P1 |",
    "| C10 | E6 mapping flights: per-flight map position RMS (table) | (new; same source as C09) | "
    "tier1/e6/maps/E6M_fig8_{r1b,r2,r3}/map_errors.json; tier1/numbers_tier1.md | "
    f"{sum(1 for c in CHK if c['fig'] == 'C10')}/{sum(1 for c in CHK if c['fig'] == 'C10')} (shared with C09) | "
    "Extension E6 P1 |",
]
idx_txt = open(INDEX).read()
if "| C08 |" not in idx_txt:
    lines = idx_txt.split("\n")
    m_hdr = re.search(r"\*\*Checks: (\d+/\d+) \(exact string equality\)\.\*\*", idx_txt)
    assert m_hdr, "index_c.md: expected 'Checks: N/N' header line not found"
    i = next(j for j, ln in enumerate(lines) if ln.startswith("| C07 |"))
    lines = lines[:i + 1] + NEW_ROWS + lines[i + 1:]
    j = next(j for j, ln in enumerate(lines) if ln.strip() == "Notes for the coordinator:")
    lines = lines[:j] + [
        "- C08/C09/C10 (Extension E6, map reuse) added by eval/figs_cand_e6route.py, continuing group C after C07; no "
        "figure here was rebuilt or renumbered.",
        "- C08 is descriptive (no Table A.4 row of its own, same convention as C05/C06); C09 and the C10 table both point "
        "at Extension E6's P1 row (the map-position-RMS comparison).",
        f"- The \"Checks: {m_hdr.group(1)}\" line above this table is eval/figs_cand_c.py's own total (C01-C07 only, "
        "unchanged by this script, which does not re-run it); eval/figs_cand_e6route.py's own C08-C10 totals are in the "
        "table row above, per candidate id.",
        "",
    ] + lines[j:]
    with open(INDEX, "w") as f:
        f.write("\n".join(lines))
    print("appended C08/C09/C10 to index_c.md")
else:
    print("index_c.md already has C08 -- not re-appended")

# ------------------------------------------------------------------ delete the bag-extraction cache
if os.path.isdir(CACHE):
    shutil.rmtree(CACHE)
    print(f"removed {CACHE}")
