#!/usr/bin/env python3
"""Assemble docs/thesis/world_images/: index.md (inventory, experiment mapping, per-shot camera record, onboard
coverage) and worlds_combined.pdf (one page per world: schematic, top-down render, angled render, onboard frames,
two-line caption). Inputs: renders/shots.json (render_world_docs.py), schematics/*.png (world_schematics.py),
onboard/frames.json (onboard_frames.py). Run: python3 sim/tools/world_docs_pack.py
"""
import json, math, os, re, subprocess, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
D = os.path.join(REPO, "docs", "thesis", "world_images")
sys.path.insert(0, os.path.dirname(__file__))
import world_schematics as WS

COMMIT = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()

# Thesis figure / table / appendix references per world: the one source for the PDF "reported in" line (W below) and
# the index.md section-1 "reported in" cells (IDX). Numbering = the 2026-10-16 revision of
# docs/thesis/figures_thesis/index.md (commit e202552): figures F2, F5, F6, F7; tables T1-T8 (docs/thesis/tables/);
# appendix A1-A3. The retired figures map F1 -> T1, F3 -> T2, F4 -> T3, F8 -> T5; F2's heading-error panel moved to
# T4 and F6's per-flight RMSE to T6. Assigned from each table's "Sources" line: T3 / T7 blank = the blank flights
# (UKF / FGO 11: dsn, p1c, fwdc, fwdplainc; EKF3 14: + ds_blank); T5 = s1_r* (room_wall_tag) and s1far / s2v2 / s3v2
# (room_wall_tag_far); T7 safety = H_safety_* (room_wall_tag_far); T8 = T rows (room_tags) and O rows (outdoor_indoor).
# "A3 ... F1" in the thesis index is the F1 robust-weighting EXPERIMENT, not a figure.
NO_THESIS = "no thesis figure or table"
TH = {
 "corridor_textured": "thesis T1 (standard-sensor row), T2 (no-heading columns)",
 "corridor_blank": "thesis T3, T7 (blank-floor validity), T1 blank row",
 "corridor_transition": NO_THESIS,
 "corridor_textured_fwdc": "thesis T1 (heading row, C0), T2, A3",
 "corridor_textured_fwdplainc": "thesis T1 (heading row), T2, A3",
 "corridor_transition_fwdc": NO_THESIS,
 "corridor_transition_fwdplainc": NO_THESIS,
 "corridor_blank_fwdc": "thesis T3 (11 blank flights), T7, T1 blank row",
 "corridor_blank_fwdplainc": "thesis T3, T7, T1 blank row",
 "corridor_textured_half_fwdc": "thesis F2, T4, T1 (closed-loop row), A1",
 "room_tags": "thesis F5 (T), F7 (L), T8 (T rows), T1 (T and L rows), A3",
 "room_wall_tag": "thesis T5 (EKF3 S1), A2",
 "room_wall_tag_far": "thesis T5, T7 (safety), A2, T1 H row",
 "outdoor_indoor": "thesis F6, T6, T7 (return jump), T8 (O rows), T1 O row",
}

# index.md section 1: the "reported in" cell of each row, keyed on the row's first cell (backticks removed).
# Rewritten by write_index(); every row must match.
IDX = {
 "corridor_textured": TH["corridor_textured"] + "; pack F03; numbers §1, §2, §6.1, §6.5, §7, §8, §14, §18",
 "corridor_blank": TH["corridor_blank"] + "; pack F06; numbers §6.2, §7",
 "corridor_transition": "numbers §1 (texture boundary y = 80 m by design, `sim/worlds/corridor_transition.sdf`: textured tile centred y = 70 m (l.175) and blank tile at y = 90 m (l.184), each 20 m), §6.2, §7, §11; " + NO_THESIS,
 "corridor_textured_fwdc": TH["corridor_textured_fwdc"]
    + "; pack F01, F02, F04, F05, F07, F15a; numbers §6.3–§6.6, §8, §9, §15, §15.1, §15.2",
 "corridor_textured_fwdplainc": TH["corridor_textured_fwdplainc"]
    + "; pack F04, F07; numbers §6.4, §6.6, §8, §9, §15.1, §15.2",
 "corridor_transition_fwdc / _fwdplainc": "numbers §6.2 (transition +60 s), §8, §9, §11 (ceiling group); " + NO_THESIS,
 "corridor_blank_fwdc / _fwdplainc": "thesis T3 (11 blank flights = dsn 3 + p1c 2 + fwdc 3 + fwdplainc 3), T7, "
    "T1 blank row (EKF3: 14 flights, + ds 3); numbers §6.2, §6.6, §8, §9",
 "corridor_textured_half_fwdc": "thesis **F2**, **T4**, T1 (closed-loop row), **A1**; pack F08, F15a; numbers §15",
 "corridor_tson_fwdc": "numbers §6.5 note row",
 "corridor_{textured,transition,blank}_fwd": "numbers §1/§2 Phase-2 rows, §11 no-ceiling group, superseded block; "
    "not analysed",
 "corridor_{textured,transition,blank}_fwdplain": "numbers §11 (`p1plain_trans`); METHODOLOGY only",
 "room_tags": "thesis **F5** (T), **F7** (L), T8 (T rows), T1 (T and L rows), A3; pack F09, F10, F12, F13; "
    "numbers §16.1, §16.3",
 "room_wall_tag": "thesis **T5** (EKF3 S1), A2; pack F14, F15b; numbers §17",
 "room_wall_tag_far": TH["room_wall_tag_far"] + "; pack F14, F15b; numbers §15 safety rows, §17, §17.1, §17.2",
 "room_wall_tag_far_occ": "METHODOLOGY only",
 "outdoor_indoor": "thesis **F6**, **T6**, T7 (return jump), T8 (O rows), T1 O row; pack F11; numbers §16.2, §18",
 "iris_textured": "numbers §2 IMU-rate rows and remaining flag 2; the Stage B/C ATE is VOID",
 "iris_runway": "the Stage C blank ATE is VOID; no current row",
}
IDX_NOTE = ('"thesis Fn / Tn / An" refers to the figures, tables and appendix pages listed in '
            '`docs/thesis/figures_thesis/index.md` (revision 2026-10-16; the tables are in `docs/thesis/tables/`). '
            'The former thesis figures F1, F3, F4 and F8 are now tables T1, T2, T3 and T5.')


def write_index():
    """Rewrite the section-1 "reported in" cells and the numbering note of index.md from IDX (idempotent)."""
    p = os.path.join(D, "index.md")
    L = open(p).read().split("\n")
    a = L.index("## 1. Inventory: every world and what used it")
    b = next(i for i in range(a + 1, len(L)) if L[i].startswith("## "))
    seen, note = set(), 0
    for i in range(a, b):
        if '"thesis Fn' in L[i]:
            L[i] = L[i][:L[i].index('"thesis Fn')] + IDX_NOTE; note += 1
        if L[i].startswith("| ") and not L[i].startswith("| world |"):
            c = L[i].split(" | ")
            k = c[0][2:].replace("`", "").strip()
            assert k in IDX, "index.md row not in IDX: %r" % k
            c[-1] = IDX[k] + " |"; L[i] = " | ".join(c); seen.add(k)
    assert note == 1 and seen == set(IDX), ("index.md rows / note not all matched", note, set(IDX) - seen)
    txt = "\n".join(L)
    # the only permitted F1/F3/F4/F8 tokens: the note's "former ... F1, F3, F4 and F8" sentence
    assert not re.search(r"\bF[1348]\b", txt.replace(IDX_NOTE, "")), "stale F1/F3/F4/F8 in index.md"
    open(p, "w").write(txt)


# world -> (status, experiments flown in it (trials/ counts), where reported, caption line 1, caption line 2).
# Mapping from trial metadata.yaml `world:` fields, batches/*.conf, tools/run_*.sh, closed_loop_run.sh and
# docs/thesis/{figures_thesis/index.md, final_results_pack_index.md, numbers.md} (checked 2026-10-16).
W = {
 "corridor_textured": ("CURRENT", "dsn_tex_r1-r10 (standard-sensor three-way baseline); ds_tex_r1-3 (compass on, reference); ~26 checks / shadow runs",
    TH["corridor_textured"] + "; pack F03; numbers §1, §2, §6.1, §6.5, §7, §8, §14, §18",
    "20 x 160 m corridor, checker floor, plain 5 m walls, no ceiling, downward sensors only: the dsn baseline.",
    "Cruise 0.5 m/s x 300 s north at 2 m from the spawn; no stored onboard images (dsn bags record no camera)."),
 "corridor_blank": ("CURRENT", "dsn_blank_r1-3; ds_blank_r1-3; corridor_blank_verify",
    TH["corridor_blank"] + "; pack F06; numbers §6.2, §7",
    "Same corridor with every floor tile blank (no albedo map): total loss of flow aiding.",
    "Cruise as the textured corridor; no stored onboard images."),
 "corridor_transition": ("CURRENT", "dsn_trans_r1-3; ds_trans_r1-3; corridor_trans_verify",
    "numbers §1 (texture boundary y = 80 m by design, `sim/worlds/corridor_transition.sdf`: textured tile centred y = 70 m (l.175) and blank tile at y = 90 m (l.184), each 20 m), §6.2, §7, §11 (no-ceiling group); " + TH["corridor_transition"],
    "Checker floor for y < 80 m, blank beyond: the mid-flight transition.",
    "Cruise as the textured corridor; no stored onboard images."),
 "corridor_textured_fwd": ("SUPERSEDED (camera sees sky)", "fwd_tex_r1-3, p1_fwd_tex, p1diag_fwd_*",
    "numbers §1/§2 Phase-2 and dropout rows, superseded block; not analysed",
    "Line-textured walls + textured end wall, iris_fwd forward camera, NO ceiling (sky visible).",
    "Superseded by corridor_textured_fwdc; frames not extracted."),
 "corridor_transition_fwd": ("SUPERSEDED (camera sees sky)", "fwd_trans_r1-3, p1_fwd_trans",
    "numbers §11 (no-ceiling group); not analysed",
    "Transition floor, line-textured walls, no ceiling.", "Superseded; frames not extracted."),
 "corridor_blank_fwd": ("SUPERSEDED (camera sees sky)", "fwd_blank_r1-3, p1_fwd_blank",
    "superseded block only", "Blank floor, line-textured walls, no ceiling.", "Superseded; frames not extracted."),
 "corridor_textured_fwdplain": ("SUPERSEDED (camera sees sky); no dataset", "p1plain_tex",
    "METHODOLOGY only", "Checker floor, plain walls and plain end wall, no ceiling.", "Superseded; frames not extracted."),
 "corridor_transition_fwdplain": ("SUPERSEDED (camera sees sky); no dataset", "p1plain_trans",
    "numbers §11 (p1plain_trans)", "Transition floor, plain walls, no ceiling.", "Superseded; frames not extracted."),
 "corridor_blank_fwdplain": ("SUPERSEDED (camera sees sky); no dataset", "p1plain_blank",
    "METHODOLOGY only", "Blank floor, plain walls, no ceiling.", "Superseded; frames not extracted."),
 "corridor_textured_fwdc": ("CURRENT (upper bound)", "fwdc_tex_r1-3, p1c_fwdc_tex, f4_fwdc_tex_r1-6, tsx_off_tex, full-speed closed loop cl_*_tex, gt_heading_*, rgs_*, lfs_check_tex",
    TH["corridor_textured_fwdc"] + "; pack F01, F02, F04, F05, F07, F15a; numbers §6.3-§6.6, §8, §9, §15, §15.1, §15.2",
    "Checker floor, line-textured walls, textured end wall at y = 165 m, plain ceiling at 5 m, forward camera.",
    "Onboard: forward frames at y = 40 m (VP valid) and y = 150 m (near the end wall: no measurement, by design)."),
 "corridor_textured_fwdplainc": ("CURRENT (featureless walls)", "fwdplainc_tex_r1-3, p1c_fwdplainc_tex, f4_fwdplainc_tex_r1-6",
    TH["corridor_textured_fwdplainc"] + "; pack F04, F07; numbers §6.4, §6.6, §8, §9, §15.1, §15.2",
    "Checker floor, plain walls and end wall, plain ceiling: the featureless-wall case.",
    "Onboard y = 40 m: the frozen VP passes support yet is ~5.6 deg off (GT yaw +0.03 deg): the documented plain-wall-over-checker failure."),
 "corridor_transition_fwdc": ("CURRENT", "fwdc_trans_r1-3, p1c_fwdc_trans",
    "numbers §6.2 (transition +60 s), §8, §9, §11 (ceiling group); " + TH["corridor_transition_fwdc"],
    "Transition floor (y = 80 m), line-textured walls, ceiling.", "Onboard: forward frame at the boundary, y = 80 m (VP valid)."),
 "corridor_transition_fwdplainc": ("CURRENT", "fwdplainc_trans_r1-3, p1c_fwdplainc_trans",
    "numbers §6.2, §8, §9, §11; " + TH["corridor_transition_fwdplainc"], "Transition floor, plain walls, ceiling.",
    "No onboard frames extracted (bags exist: trials/fwdplainc_trans_r*)."),
 "corridor_blank_fwdc": ("CURRENT", "fwdc_blank_r1-3, p1c_fwdc_blank",
    TH["corridor_blank_fwdc"] + "; numbers §6.2, §8, §9", "Blank floor, line-textured walls, ceiling.",
    "Onboard: forward frame at y = 40 m (VP valid; walls carry the heading although the floor carries no flow)."),
 "corridor_blank_fwdplainc": ("CURRENT", "fwdplainc_blank_r1-3, p1c_fwdplainc_blank",
    TH["corridor_blank_fwdplainc"] + "; numbers §6.2, §6.6 (yaw-only benefit), §8, §9", "Blank floor, plain walls, ceiling.",
    "Onboard: forward frame at y = 40 m (VP valid: plain walls over a blank floor validate)."),
 "corridor_textured_half_fwdc": ("CURRENT (all closed-loop results at half real-time, RTF 0.5)", "27 cl_*_half flights + FGO dev / shadow / ground-test runs and gt_heading_half* (44 trials)",
    TH["corridor_textured_half_fwdc"] + "; pack F08, F15a; numbers §15",
    "Geometrically identical to corridor_textured_fwdc; only <real_time_factor> 0.5 differs (FGO compute headroom).",
    "The simulator ran at half real time; the commanded flight speed was unchanged at 0.5 m/s (same route, 300 s at 2 m). Renders as the fwdc page; no frames extracted."),
 "corridor_tson_fwdc": ("RECORD ONLY (time-sync A/B)", "tsx_on_tex", "numbers §6.5 note row",
    "corridor_textured_fwdc with the drone model iris_fwd_ts (time-sync A/B); geometry identical.",
    "Renders identical to the fwdc page; no frames extracted."),
 "iris_textured": ("RECORD ONLY", "stage_b_verify, stage_c_textured, smoke_test, ekf3_diag_60s, imu_rate_verify, imu_verify2, nomag_test_long, sweep_v* (13)",
    "numbers §2 IMU-rate rows, remaining flag 2; Stage B/C ATE VOID; watcher SITL bench",
    "20 x 20 m checker mat, nothing beyond it (LiDAR no-return off the mat; Known Issue #6).",
    "Flown before vendoring (2026-07-29) from ~/ardupilot_gazebo/worlds; the render shows the vendored SDF."),
 "iris_runway": ("RECORD ONLY", "stage_c_blank", "Stage C blank ATE VOID; no current row",
    "Upstream runway world: 1500 x 100 m runway plane on a 10 km grass mesh.",
    "Flown before vendoring; no stored onboard images."),
 "outdoor_indoor": ("CURRENT (experiment O)", "O_r1, O_r2, O_r3b (reported); O_r3_IMUGAP excluded; o_check1",
    TH["outdoor_indoor"] + "; pack F11; numbers §16.2, §18",
    "Checker floor y = -20..80 m; 10 x 50 m building (y = 20..70) with a 3 m entrance and a non-shadowing roof.",
    "Route: 15 m GNSS-yaw alignment, 50 m out and back at 0.5 m/s; GNSS off past the gate N = 20 m; no stored onboard images."),
 "room_tags": ("CURRENT (experiments T and L)", "T_{A,B,C,D}_r1-3 (12 reported; L replays T_A_r1-3), tagchar_h15/20/25/30, tag_check*, room_check",
    TH["room_tags"] + "; pack F09, F10, F12, F13; numbers §16.1, §16.3",
    "10 x 10 m room, 3 m plain walls, checker floor, floor tags 0-7 at the corners / midpoints of the 6 m lap square.",
    "Onboard: the ONLY stored downward-camera frames (tagchar_h20 hover / cruise, tagchar_h30 cruise) - same checker texture."),
 "room_wall_tag": ("CURRENT results; no new flights (the flight script refuses it)", "H_s0a, H_s0b, H_s1_r1-3, H_gt_*, H_wtest_*",
    TH["room_wall_tag"] + "; pack F14, F15b; numbers §17",
    "room_tags + wall tag id 10 on the north wall (z 1.5 m), a parked occluder, iris_fwd spawned at the hold (0, 3.5).",
    "Routes: S0a grid sweep (world frame), S1 hold W(-1.5, 0) with E steps; forward images exist in H bags but none extracted."),
 "room_wall_tag_far": ("CURRENT (H re-flies, S2/S3, safety)", "H_s1far_r1/r2/r3b, H_s2(_v2)_r1-3, H_s3(_v2)_r1-3, H_gt_*_far, ~21 H_safety_*",
    TH["room_wall_tag_far"] + "; pack F14, F15b; numbers §15 safety rows, §17, §17.1, §17.2",
    "room_wall_tag with the spawn 3.9 m from the wall tag (0, 1.1), so the tag is seen before arming.",
    "Routes: anchor at W(-3.9, 0), hold W(-1.5, 0) (s1_far); safety2 hold W(-2.6, 0); no frames extracted."),
 "room_wall_tag_far_occ": ("RECORD ONLY (in-flight-anchor check)", "H_ifa_ekf3 (FAIL, room-box breach)",
    "METHODOLOGY only; no numbers row, no figure",
    "room_wall_tag_far with the occluder starting in front of the wall tag (no fix until uncovered airborne).",
    "Route: 1.5 m north in EKF3's own pre-anchor frame; no frames extracted."),
}
ONBOARD = {"room_tags": ["tagchar_h20__down_hover.png", "tagchar_h20__down_cruise.png", "tagchar_h30__down_cruise.png"],
           "corridor_textured_fwdc": ["fwdc_tex_r1__fwd_y040.png", "fwdc_tex_r1__fwd_y150.png"],
           "corridor_textured_fwdplainc": ["fwdplainc_tex_r1__fwd_y040.png", "fwdplainc_tex_r1__fwd_y150.png"],
           "corridor_transition_fwdc": ["fwdc_trans_r1__fwd_y080.png"],
           "corridor_blank_fwdc": ["fwdc_blank_r1__fwd_y040.png"],
           "corridor_blank_fwdplainc": ["fwdplainc_blank_r1__fwd_y040.png"]}
ORDER = ["corridor_textured", "corridor_blank", "corridor_transition",
         "corridor_textured_fwdc", "corridor_textured_fwdplainc", "corridor_transition_fwdc",
         "corridor_transition_fwdplainc", "corridor_blank_fwdc", "corridor_blank_fwdplainc",
         "corridor_textured_half_fwdc", "corridor_tson_fwdc",
         "corridor_textured_fwd", "corridor_transition_fwd", "corridor_blank_fwd",
         "corridor_textured_fwdplain", "corridor_transition_fwdplain", "corridor_blank_fwdplain",
         "room_tags", "room_wall_tag", "room_wall_tag_far", "room_wall_tag_far_occ", "outdoor_indoor",
         "iris_textured", "iris_runway"]


def parallax(world, s):
    """Worst-case horizontal displacement of the tallest object's top edge in a top view: h * r / altitude."""
    _, V, _ = WS.parse_world(world)
    h = max([v["zmax"] for v in V if WS.classify(v) in ("wall", "wall_lined", "ceiling")] or [0.0])
    r = math.hypot(*[x / 2 for x in s["ground_span_m"]])
    return h, r, h * r / s["eye"][2]


def main():
    shots = json.load(open(os.path.join(D, "renders", "shots.json")))
    frames = {f["file"]: f for f in json.load(open(os.path.join(D, "onboard", "frames.json")))["frames"]}
    assert set(ORDER) == set(W) == set(shots), "world lists disagree"
    # ------------------------------------------------------------------------------------------------ PDF
    with PdfPages(os.path.join(D, "worlds_combined.pdf")) as pdf:
        for w in ORDER:
            st, ex, used, c1, c2 = W[w]
            S = {s["name"]: s for s in shots[w]["shots"]}
            topn = "top_cutaway" if w == "outdoor_indoor" else "top_room" if w.startswith("room_") else "top"
            ob = ONBOARD.get(w, [])
            fig = plt.figure(figsize=(11.69, 8.27))
            fig.text(0.03, 0.965, w, fontsize=15, weight="bold")
            fig.text(0.03, 0.94, "status: %s   |   flown: %s" % (st, ex[:150]), fontsize=7.5, color="#4d4d4d")
            # Captions (rulings 2026-10-16): no pack-figure codes, claim numbers or commit hashes on the page; they stay in index.md.
            # Only the thesis references are printed; the record pointers (numbers.md sections, METHODOLOGY) stay in index.md.
            used_pdf = "; ".join(x.strip() for x in used.split(";") if x.strip().startswith(("thesis", "no thesis"))) or "no thesis figure or table"
            fig.text(0.03, 0.925, "reported in: %s" % used_pdf, fontsize=7.5, color="#4d4d4d")
            long_ = w.startswith("corridor") or w == "outdoor_indoor"
            if long_:
                boxes = {"sch": [0.03, 0.56, 0.94, 0.33], "top": [0.03, 0.44, 0.94, 0.11],
                         "ang": [0.03, 0.12, 0.30, 0.30], "ob": [0.35, 0.12, 0.62, 0.30]}
            else:
                boxes = {"sch": [0.03, 0.40, 0.50, 0.50], "top": [0.55, 0.40, 0.42, 0.50],
                         "ang": [0.03, 0.12, 0.30, 0.27], "ob": [0.35, 0.12, 0.62, 0.27]}
            def show(key, path, title):
                ax = fig.add_axes(boxes[key]); ax.imshow(Image.open(path)); ax.set_axis_off()
                ax.set_title(title, fontsize=7.5, loc="left", color="#4d4d4d")
            show("sch", os.path.join(D, "schematics", w + ".png"), "schematic from the SDF (schematics/%s.png)" % w)
            s = S[topn]
            show("top", os.path.join(D, "renders", s["file"]), "top-down render, %s; %s (renders/%s)"
                 % ("near-orthographic perspective", "ceiling/roof removed" if s["cutaway"] else "as built", s["file"]))
            show("ang", os.path.join(D, "renders", S["angled"]["file"]), "angled render (as built)")
            if ob:
                n = len(ob); x0, y0, wd, ht = boxes["ob"]
                for i, f in enumerate(ob):
                    ax = fig.add_axes([x0 + i * wd / n, y0, wd / n - 0.005, ht]); ax.imshow(Image.open(
                        os.path.join(D, "onboard", f))); ax.set_axis_off()
                    ax.set_title("onboard (bag): " + f, fontsize=6.5, loc="left", color="#4d4d4d")
            else:
                ax = fig.add_axes(boxes["ob"]); ax.set_axis_off()
                ax.text(0.02, 0.5, "No stored onboard frames extracted for this world.\n(see the world index, 'Onboard "
                        "coverage')", fontsize=10, color="#4d4d4d", va="center")
            fig.text(0.03, 0.065, c1, fontsize=9.5)
            fig.text(0.03, 0.04, c2, fontsize=9.5)
            pdf.savefig(fig); plt.close(fig)
    # ------------------------------------------------------------------------------------------------ shot table
    rows = ["| world | shot | what | eye (x, y, z) m | rpy (rad) | HFOV deg | px | projection | cutaway | top-view parallax |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for w in ORDER:
        for s in shots[w]["shots"]:
            par = ""
            if s["name"].startswith("top"):
                h, r, p = parallax(w, s)
                par = "%.2f m (h %.1f m at r %.0f m, alt %.0f m)" % (p, h, r, s["eye"][2])
            rows.append("| %s | `%s` | %s | %s | %s | %.2f | %dx%d | %s | %s | %s |" % (
                w, s["file"], s["what"], ", ".join("%.1f" % v for v in s["eye"]),
                ", ".join("%.3f" % v for v in s["rpy"]), s["hfov_deg"], s["width"], s["height"],
                "persp. (near-ortho)" if s["name"].startswith("top") else "perspective",
                "yes" if s["cutaway"] else "no", par))
    open(os.path.join(D, "shots_table.md"), "w").write("\n".join(rows) + "\n")
    for w in ORDER:
        assert not re.search(r"\bF[1348]\b", W[w][2]), (w, W[w][2])
    write_index()
    print("pdf pages", len(ORDER))


if __name__ == "__main__":
    main()
