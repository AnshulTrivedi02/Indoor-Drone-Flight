#!/usr/bin/env python3
"""METHODOLOGY-CHAPTER FIGURE AND TABLES, plus the compute and safety tables for the closing chapter (2026-10-17).

Drawing and tabulating only. Everything is built from existing code, parameter files and documents. No simulation is run and
no estimator result is recomputed. numbers.md (CONTENT-FROZEN) is not edited.

Outputs use NEW file names. eval/figs_thesis.py, its combined PDF and docs/thesis/figures_thesis/index.md are NOT touched.
The names are descriptive on purpose: M1-M3 are safety-mitigation codes, so they are not used as file ids.
  docs/thesis/figures_thesis/methods_architecture.{pdf,png}           proposed Figure 3.1
  docs/thesis/tables/methods_estimator_design.{md,tex,png}            proposed Table 3.1
  docs/thesis/tables/methods_noise_parity.{md,tex,png}                proposed Table 3.2
  docs/thesis/tables/methods_noise_exceptions.{md,tex,png}            proposed Table 3.3
  docs/thesis/tables/methods_experiment_matrix.{md,tex,png}           proposed Table 3.4
  docs/thesis/tables/realflight_compute.{md,tex,png}                  proposed Table 8.1
  docs/thesis/tables/realflight_safety_findings.{md,tex,png}          proposed Table 8.2
  docs/thesis/figures_thesis/index_methods.md                         captions, sources, cross-checks, numbering

Two kinds of check are made.
- SOURCE checks. Every cited file:line is verified: a verbatim needle must occur on that exact line. A miss fails the build.
- EXACT cross-checks. Derived values (the GTSAM noise conversion, the gate thresholds, the EKF3 prediction period, flight
  counts and flash differences) are computed HERE from their inputs. Each is compared, as a string, with the stored value read
  from the cited line. The rounding is the SAME rd() as eval/figs_thesis.py.

rd(), tex(), md() and tex_selfcheck() are loaded from eval/figs_thesis.py through the AST: the function definitions only. That
module has no __main__ guard, so importing it would run it and regenerate its outputs, which another agent is editing. No logic
is copied.

Usage: /home/makerspace/venv-evo/bin/python eval/figs_thesis_methods.py"""
import ast, math, os, re, subprocess, sys, textwrap
from decimal import Decimal
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUTF = os.path.join(ROOT, "docs", "thesis", "figures_thesis"); OUTT = os.path.join(ROOT, "docs", "thesis", "tables")
INDEX = os.path.join(OUTF, "index_methods.md")
SCRIPT = "eval/figs_thesis_methods.py"
git = lambda *a: subprocess.run(["git", *a], capture_output=True, text=True).stdout.strip()
COMMIT = git("-C", ROOT, "rev-parse", "--short", "HEAD")
AP_UKF = os.path.expanduser("~/ardupilot_ukf"); AP_PIN = os.path.expanduser("~/ardupilot")
AP_UKF_REV = "f30f6ffa2f, branch ukf-jitter-fix; files read with git show at this revision"
AP_PIN_REV = "7bac20cbcc; files read with git show at this revision"


# ------------------------------------------------------------------ shared helpers loaded from eval/figs_thesis.py (no copy)
def _load_from_figs_thesis(names):
    tree = ast.parse(open(os.path.join(HERE, "figs_thesis.py")).read())
    keep = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name in names) or
            (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in n.targets))]
    ns = {"re": re}
    exec(compile(ast.Module(body=keep, type_ignores=[]), "eval/figs_thesis.py", "exec"), ns)
    missing = [n for n in names if n not in ns]
    assert not missing, f"not found in figs_thesis.py: {missing}"
    return ns


_FT = _load_from_figs_thesis(["rd", "tex", "md", "tex_selfcheck", "TEX_ESC", "TEX_UNI"])
rd, _tex, md, tex_selfcheck = _FT["rd"], _FT["tex"], _FT["md"], _FT["tex_selfcheck"]
# Characters used here that figs_thesis.py's TEX_UNI does not map: an ADDITION applied before its tex(), which is unchanged.
TEX_EXTRA = {"ψ": r"$\psi$", "√": r"$\surd$", "²": r"$^2$", "⁻": r"$^-$", "¹": r"$^1$", "⁸": r"$^8$", "³": r"$^3$",
             "⁶": r"$^6$", "⁵": r"$^5$", "µ": r"$\mu$", "χ": r"$\chi$", "≠": r"$\neq$", "∞": r"$\infty$", "ω": r"$\omega$",
             "ν": r"$\nu$", "⊗": r"$\otimes$", "←": r"$\leftarrow$"}


def tex(s):
    return "".join(TEX_EXTRA[ch] if ch in TEX_EXTRA and ch not in _FT["TEX_UNI"] else _tex(ch) for ch in str(s))


# ------------------------------------------------------------------ style (the palette of eval/figs_thesis.py)
C = {"EKF3": "#0072B2", "UKF": "#009E73", "FGO": "#D55E00"}
INK, INK2, GRID = "#111111", "#4d4d4d", "#d9d9d9"
plt.rcParams.update({"font.size": 9, "pdf.fonttype": 42, "font.family": "DejaVu Sans"})
CHK = []; ITEMS = []


def check(label, computed, expected, src):
    """EXACT: the computed string must equal the expected string character for character (no tolerance)."""
    c, e = str(computed), str(expected)
    CHK.append((label, c, e, src, c == e))
    if c != e:
        print(f"   CHECK FAIL {label}: computed {c!r} expected {e!r}")


# ------------------------------------------------------------------ SOURCES: every citation is verified against its file
# alias -> (path, display name). S(alias, line, needle) is accepted only if `needle` occurs on that exact line.
ALIAS = {
    "M": ("METHODOLOGY.md", "M"), "N": ("docs/thesis/numbers.md", "N"), "V": ("docs/thesis/thesis_vocabulary.md", "V"),
    "CL": ("CLAUDE.md", "CLAUDE.md"), "FD": ("FGO_DESIGN.md", "FGO_DESIGN.md"), "PR": ("PROGRESS.md", "PROGRESS.md"),
    "DQ": ("docs/decisions_queue.md", "decisions_queue.md"),
    "UC": ("src/estimators/ukf_core.py", "UC"), "MM": ("src/estimators/measurement_models.py", "MM"),
    "FC": ("src/estimators/fgo/fgo_core.py", "FC"), "FN": ("src/estimators/fgo/fgo_node.py", "FN"),
    "FNC": ("src/estimators/fgo/fgo_node_core.py", "fgo_node_core.py"),
    "CN": ("src/estimators/fgo_cpp/src/fgo_cpp_node.cpp", "CN"), "CC": ("src/estimators/fgo_cpp/src/fgo_core.cpp", "CC"),
    "UR": ("src/estimators/ukf_replay.py", "ukf_replay.py"), "FR": ("src/estimators/fgo/fgo_replay.py", "fgo_replay.py"),
    "RT": ("run_trial.sh", "run_trial.sh"), "CLR": ("sim/tools/closed_loop_run.sh", "closed_loop_run.sh"),
    "WW": ("sim/tools/wall_watch.py", "wall_watch.py"), "FT": ("fly_trial.py", "fly_trial.py"),
    "HB": ("heading_bridge.py", "heading_bridge.py"), "HBC": ("src/forward_camera/heading_bridge_core.py", "heading_bridge_core.py"),
    "TB": ("tag_bridge.py", "tag_bridge.py"), "TBF": ("tag_bridge_fwd.py", "tag_bridge_fwd.py"),
    "IB": ("imu_bridge.py", "imu_bridge.py"), "FB": ("flow_bridge.py", "flow_bridge.py"),
    "LB": ("lidar_bridge.py", "lidar_bridge.py"), "AB": ("attitude_bridge.py", "attitude_bridge.py"),
    "GT": ("ground_truth_pub.py", "ground_truth_pub.py"),
    "FTR": ("src/optical_flow_node/optical_flow_node/flow_tracker.py", "flow_tracker.py"),
    "MW": ("realflight/watcher/mocap_watch.py", "mocap_watch.py"), "LV": ("realflight/watcher/liveness.py", "liveness.py"),
    "WFC": ("realflight/params/watcher_fc.parm", "watcher_fc.parm"), "MCP": ("realflight/mcp1.py", "mcp1.py"),
    "RFP": ("docs/real_flights_plan.md", "real_flights_plan.md"),
    "WB": ("docs/handovers/2026-10-10_mocap_watcher_build.md", "watcher-build handover"),
    "BFW": ("docs/handovers/2026-10-11_board_firmware_h743.md", "board-firmware handover"),
    "ARM": ("docs/handovers/2026-10-11_fgo_arm64.md", "arm64 handover"),
    "F8H": ("docs/handovers/2026-10-12_f8_investigation.md", "F8 handover"),
    "M2B": ("docs/handovers/2026-10-12_m2_full_bench.md", "M2 full-bench handover"),
    "M2R": ("docs/handovers/2026-10-12_m2r_rerun.md", "M2-R handover"),
    "BFP": ("docs/board_firmware_plan.md", "board_firmware_plan.md"),
    "CPPR": ("eval/results/fgo_cpp_arm64/RESULTS.md", "fgo_cpp_arm64/RESULTS.md"),
    "CLH": ("closedloop_heading.parm", "closedloop_heading.parm"),
    "CLHH": ("closedloop_heading_half.parm", "closedloop_heading_half.parm"),
    "CLP": ("closedloop.parm", "closedloop.parm"), "CLU": ("closedloop_ukf.parm", "closedloop_ukf.parm"),
    "CLF": ("closedloop_fgo.parm", "closedloop_fgo.parm"), "CRP": ("consolidated_rerun.parm", "consolidated_rerun.parm"),
    "CLUH": ("closedloop_ukf_heading.parm", "closedloop_ukf_heading.parm"),
    "HX": ("h_extnav.parm", "h_extnav.parm"), "HU": ("h_ukf_tag.parm", "h_ukf_tag.parm"),
    "TX": ("tags_extnav.parm", "tags_extnav.parm"), "OG": ("o_gnss.parm", "o_gnss.parm"),
    "US": ("ukf_shadow.parm", "ukf_shadow.parm"), "FS": ("fgo_shadow.parm", "fgo_shadow.parm"),
    "HS": ("tools/run_h_safety.sh", "run_h_safety.sh"), "THD": ("docs/tag_hold_design.md", "tag_hold_design.md"),
    "RM": ("batches/rerun_main.conf", "rerun_main.conf"), "CDC": ("batches/ceiling_datasets.conf", "ceiling_datasets.conf"),
    "F4C": ("batches/f4_robust.conf", "f4_robust.conf"), "HALF": ("sim/worlds/corridor_textured_half_fwdc.sdf", "corridor_textured_half_fwdc.sdf"),
    # ArduPilot trees, outside the repository. Branch and commit are recorded in the index.
    "UK": (os.path.join(AP_UKF, "libraries/AP_NavUKF/AP_NavUKF.cpp"), "AP_NavUKF.cpp"),
    "UKH": (os.path.join(AP_UKF, "libraries/AP_NavUKF/AP_NavUKF.h"), "AP_NavUKF.h"),
    "FGH": (os.path.join(AP_UKF, "libraries/AP_NavUKF/AP_NavFGO.h"), "AP_NavFGO.h"),
    "AH": (os.path.join(AP_UKF, "libraries/AP_AHRS/AP_AHRS.h"), "AP_AHRS.h"),
    "AC": (os.path.join(AP_UKF, "libraries/AP_AHRS/AP_AHRS.cpp"), "AP_AHRS.cpp"),
    "GC": (os.path.join(AP_UKF, "libraries/GCS_MAVLink/GCS_Common.cpp"), "GCS_Common.cpp"),
    "E3": (os.path.join(AP_PIN, "libraries/AP_NavEKF3/AP_NavEKF3.cpp"), "AP_NavEKF3.cpp"),
    "E3H": (os.path.join(AP_PIN, "libraries/AP_NavEKF3/AP_NavEKF3_core.h"), "AP_NavEKF3_core.h"),
    "E3Y": (os.path.join(AP_PIN, "libraries/AP_NavEKF3/AP_NavEKF3_MagFusion.cpp"), "AP_NavEKF3_MagFusion.cpp"),
    "E3M": (os.path.join(AP_PIN, "libraries/AP_NavEKF3/AP_NavEKF3_Measurements.cpp"), "AP_NavEKF3_Measurements.cpp"),
    "E3F": (os.path.join(AP_PIN, "libraries/AP_NavEKF3/AP_NavEKF3_OptFlowFusion.cpp"), "AP_NavEKF3_OptFlowFusion.cpp"),
    "E3P": (os.path.join(AP_PIN, "libraries/AP_NavEKF3/AP_NavEKF3_PosVelFusion.cpp"), "AP_NavEKF3_PosVelFusion.cpp"),
    "FGN": ("docs/thesis/diagnostics/numbers_fgo_gate_count.md", "numbers_fgo_gate_count.md"),
    "FGR": ("docs/thesis/diagnostics/fgo_gate_count_results.md", "fgo_gate_count_results.md"),
    "DL": ("docs/thesis/tier1/decisions_log.md", "decisions_log.md"),
}
_LINES = {}; SRC = []


AP_PINS = {AP_UKF: "f30f6ffa2f", AP_PIN: "7bac20cbcc"}   # the ArduPilot revisions the citations were verified at


def _lines(alias):
    """The file's lines. ArduPilot files are read at their pinned revision (git show rev:path), not from the working tree, so
    the source checks do not depend on which branch is checked out."""
    if alias not in _LINES:
        p = ALIAS[alias][0]
        for repo, rev in AP_PINS.items():
            if p.startswith(repo + "/"):
                txt = subprocess.run(["git", "-C", repo, "show", f"{rev}:{os.path.relpath(p, repo)}"], capture_output=True,
                                     text=True, check=True).stdout
                break
        else:
            txt = open(p if os.path.isabs(p) else os.path.join(ROOT, p), encoding="utf-8").read()
        _LINES[alias] = txt.split("\n")
    return _LINES[alias]


def S(alias, line, needle, end=None):
    """A verified citation: `needle` must occur verbatim on line `line` of the aliased file. Returns 'name:line[-end]'."""
    L_ = _lines(alias); ok = 1 <= line <= len(L_) and needle in L_[line - 1]
    SRC.append((alias, line, needle, ok))
    if not ok:
        hits = [i + 1 for i, t in enumerate(L_) if needle in t][:6]
        print(f"   SOURCE FAIL {alias}:{line} needle {needle!r}; found at {hits}")
    return f"{ALIAS[alias][1]}:{line}" + (f"-{end}" if end else "")


def cell(alias, line, k):
    """Cell k of the markdown table row on `line` (for the EXACT cross-checks: the expected value is read from the source line)."""
    return [c.strip() for c in _lines(alias)[line - 1].strip().strip("|").split("|")][k]


def grab(alias, line, pattern):
    """The first regex group of `pattern` on `line` (the expected string of a cross-check, read from the cited line)."""
    m = re.search(pattern, _lines(alias)[line - 1])
    return m.group(1) if m else f"<no match on {alias}:{line}>"


KEY_ABBR = ("Source abbreviations: M = METHODOLOGY.md; N = docs/thesis/numbers.md (content-frozen); V = docs/thesis/thesis_vocabulary.md; "
            "UC = src/estimators/ukf_core.py; MM = src/estimators/measurement_models.py; FC = src/estimators/fgo/fgo_core.py; "
            "FN = src/estimators/fgo/fgo_node.py; CN / CC = src/estimators/fgo_cpp/src/fgo_cpp_node.cpp / fgo_core.cpp; "
            f"AP_NavUKF.cpp, AP_NavFGO.h, AP_AHRS.* and GCS_Common.cpp are in the thesis ArduPilot fork ~/ardupilot_ukf ({AP_UKF_REV}); "
            f"AP_NavEKF3*.cpp/.h are in the pinned ArduPilot ~/ardupilot ({AP_PIN_REV}). Parameter files are at the repository root. "
            "Every file:line is verified by the generator against a verbatim needle (index_methods.md).")


# ======================================================================== shared table writer
def table_page(title, header, rows, widths, notes=(), fs=7.6):
    """A4-landscape page(s) of a wrapped text table on a white page; returns the figures."""
    figs = []; lh = fs * 1.36 / 72 / 8.27; tw = sum(widths)
    cpl = lambda w: max(6, int(w / tw * 0.94 * 11.69 * 72 / (fs * 0.62)) - 2)   # characters per line in a column (with a margin)

    def newpage(k):
        fig = plt.figure(figsize=(11.69, 8.27)); fig.patch.set_facecolor("white")
        fig.text(0.03, 0.968, title + (f" (continued, {k})" if k > 1 else ""), fontsize=11.5, weight="bold", va="top")
        x = 0.03; y = 0.928; nh = 1
        for h, w in zip(header, widths):
            hw = textwrap.wrap(h, cpl(w)); nh = max(nh, len(hw))
            fig.text(x, y, "\n".join(hw), fontsize=fs + 0.3, weight="bold", va="top"); x += w / tw * 0.94
        y2 = y - (1.36 * nh + 0.4) * lh
        fig.add_artist(Line2D([0.03, 0.97], [y2 + 0.2 * lh, y2 + 0.2 * lh], color=INK2, lw=0.8, transform=fig.transFigure))
        return fig, y2 - 0.3 * lh
    k = 1; fig, y = newpage(k)
    for row in rows:
        cells = [[ln for para in str(c).split("\n") for ln in (textwrap.wrap(para, cpl(w)) or [""])] for c, w in zip(row, widths)]
        n = max(len(c) for c in cells)
        if y - n * lh < 0.05:
            figs.append(fig); k += 1; fig, y = newpage(k)
        x = 0.03
        for ci, (c, w) in enumerate(zip(cells, widths)):
            fig.text(x, y, "\n".join(c), fontsize=fs, va="top", linespacing=1.25, weight="bold" if ci == 0 else "normal")
            x += w / tw * 0.94
        y -= (n * 1.03 + 0.55) * lh
        fig.add_artist(Line2D([0.03, 0.97], [y + 0.3 * lh, y + 0.3 * lh], color=GRID, lw=0.6, transform=fig.transFigure))
    for nt in notes:
        lines = textwrap.wrap(nt, 205)
        if y - len(lines) * lh < 0.025:
            figs.append(fig); k += 1; fig, y = newpage(k)
        fig.text(0.03, y, "\n".join(lines), fontsize=fs - 0.6, va="top", color=INK2, linespacing=1.2)
        y -= (len(lines) * 1.0 + 0.6) * lh
    figs.append(fig)
    return figs


def save_tab(num, name, title, caption, header, rows, widths, notes, chapter_note, fs=7.6):
    """One table, three outputs from the SAME row list: .md, .tex (booktabs) and rendered page(s) .png. Consumes CHK."""
    global CHK
    m_ = [f"# {num}. {title}", "", caption, "", "| " + " | ".join(md(h) for h in header) + " |", "|" + "---|" * len(header)]
    m_ += ["| " + " | ".join(md(c) for c in r) + " |" for r in rows]
    m_ += [""] + [f"*{md(n)}*\n" for n in notes] + [f"<!-- generated by {SCRIPT} (commit {COMMIT}); no number recomputed. Sources "
                                                     f"verified and cross-checks: docs/thesis/figures_thesis/index_methods.md, {num}. -->", ""]
    open(os.path.join(OUTT, name + ".md"), "w").write("\n".join(m_))
    tw = sum(widths); spec = "".join(f"p{{\\dimexpr {rd(w / tw * 0.999, 3)}\\linewidth-2\\tabcolsep\\relax}}" for w in widths)
    t_ = [f"% {num}: generated by {SCRIPT} (commit {COMMIT}). Sources and cross-checks: docs/thesis/figures_thesis/index_methods.md.",
          "% Needs \\usepackage{booktabs} (and longtable/landscape if typeset at full width). Not compiled here (no TeX installed);",
          "% checked for ASCII, balanced braces and the column count of every row.",
          r"\begin{table}[htbp]", r"\centering", r"\scriptsize", f"\\caption{{{tex(title)}. {tex(caption)}}}",
          f"\\label{{tab:{name}}}", f"\\begin{{tabular}}{{{spec}}}", r"\toprule",
          " & ".join(f"\\textbf{{{tex(h)}}}" for h in header) + r" \\", r"\midrule"]
    t_ += [" & ".join(tex(c) for c in r) + r" \\" for r in rows]
    t_ += [r"\bottomrule", r"\end{tabular}", r"\par\smallskip\raggedright"] + [f"\\textit{{Note.}} {tex(n)}\\par" for n in notes]
    t_ += [r"\end{table}", ""]
    txt = "\n".join(t_); tex_selfcheck(txt, len(header))
    open(os.path.join(OUTT, name + ".tex"), "w").write(txt)
    figs = table_page(f"{num}. {title}", header, rows, widths, notes=notes, fs=fs)
    pngs = []
    for k, f in enumerate(figs):
        base = os.path.join(OUTT, name + (f"_p{k + 1}" if len(figs) > 1 else ""))
        f.savefig(base + ".png", dpi=150, facecolor="white"); plt.close(f); pngs.append(os.path.basename(base) + ".png")
    ITEMS.append(dict(num=num, name=name, kind="table", title=title, caption=caption, files=[name + ".md", name + ".tex"] + pngs,
                      checks=CHK, chapter=chapter_note))
    print(f"wrote table {name} ({len(pngs)} page(s)); checks {sum(c[4] for c in CHK)}/{len(CHK)}")
    CHK = []


# ======================================================================== Figure 3.1: system architecture
def fig_architecture():
    srcs = []   # (what, citation) pairs for the index
    def cite(what, *c):
        srcs.append((what, "; ".join(c)))

    # ---- edges and boxes, each derived from a cited line
    cite("IMU: HIGHRES_IMU on SITL SERIAL2 (udpclient 14556, bypassing MAVProxy) -> imu_bridge -> /imu/data_raw, /imu/time_ref",
         S("RT", 300, "--serial2=udpclient:127.0.0.1:14556"), S("IB", 102, "MAVLINK_PORT = 14556"),
         S("IB", 123, "'/imu/data_raw'"), S("IB", 127, "'/imu/time_ref'"))
    cite("/imu/data_raw is for the UKF/FGO only; EKF3 (and the UKF port) use the FC's own IMU (DAL)",
         S("CL", 963, "ArduPilot EKF3 doesn't need `/imu/data_raw` itself"), S("UKH", 14, "Inputs (the same ones EKF3 uses)"))
    cite("Downward camera -> flow_tracker -> /optical_flow/measurement (uses /attitude/angular_rates)",
         S("FTR", 60, "/downward_camera/image"), S("FTR", 67, "/attitude/angular_rates"), S("FTR", 74, "/optical_flow/measurement"))
    cite("flow_bridge: OPTICAL_FLOW (msg 100) on MAVProxy 14553 -> EKF3; fanned out to the UKF port",
         S("FB", 80, "MAVLINK_PORT = 14553"), S("FB", 137, "optical_flow_send("), S("AC", 2798, "ukf.writeOptFlowMeas("))
    cite("lidar_bridge: DISTANCE_SENSOR on MAVProxy 14552 -> RNGFND1",
         S("LB", 46, "MAVLINK_PORT = 14552"), S("LB", 80, "distance_sensor_send("))
    cite("attitude_bridge: FC ATTITUDE on MAVProxy 14551 -> /attitude/angular_rates",
         S("AB", 44, "MAVLINK_PORT = 14551"), S("AB", 55, "'/attitude/angular_rates'"))
    cite("heading_bridge: forward camera -> vanishing-point heading -> ODOMETRY on SITL SERIAL1 (14557) -> ExtNav yaw; republishes "
         "/forward_camera/heading_sent", S("HB", 2, "Live forward-camera heading -> ArduPilot EKF3 ExternalNav yaw"),
         S("HB", 35, "MAVLINK_PORT = 14557"), S("HB", 72, "/forward_camera/heading_sent"),
         S("HBC", 27, "Message: ODOMETRY"))
    cite("ExtNav reaches EKF3 and (rulings D17 and H) the UKF port by the same call",
         S("AC", 2827, "EKF3.writeExtNavData("), S("AC", 2830, "ukf.writeExtNavData("))
    cite("Tag bridges: floor tags (tag_bridge, Experiments 2/3) and the wall tag (tag_bridge_fwd, Experiment 5) -> ODOMETRY on "
         "SERIAL1 14557 (ExtNav position + yaw); /tags/sent", S("TB", 11, "MAVLink ODOMETRY to SITL SERIAL1"),
         S("TBF", 2, "Live WALL-tag bridge for experiment H"), S("TBF", 12, "MAVLink ODOMETRY to SITL SERIAL1"),
         S("RT", 142, "TAG_BRIDGE and HEADING_BRIDGE share SERIAL1"))
    cite("Ground truth: Gazebo dynamic_pose -> ground_truth_pub -> /ground_truth/pose (evaluation and the SITL watcher only)",
         S("GT", 48, "'/ground_truth/pose'"), S("UR", 7, "Ground truth is used ONLY for evaluation"))
    cite("FGO node (Python or C++): subscriptions; ODOMETRY LOCAL_NED / ESTIMATOR_TYPE_NAIVE on SITL SERIAL3 (14558) -> AP_NavFGO",
         S("CN", 4, "Subscriptions (as fgo_node.py)"), S("RT", 166, "SERIAL3_ARG=(--serial3=udpclient:127.0.0.1:14558)"),
         S("RT", 448, "mavlink_out:=udp:127.0.0.1:14558"), S("GC", 4063, "MAV_FRAME_LOCAL_NED && f.estimator_type == MAV_ESTIMATOR_TYPE_NAIVE"),
         S("FGH", 2, "the thesis FGO (GTSAM fixed-lag smoother, run OUTSIDE ArduPilot"))
    cite("AHRS_EKF_TYPE selects the flying estimator: 12 = thesis UKF, 13 = thesis FGO; 3 = EKF3; 10 = simulator truth",
         S("AH", 499, "UKF = 12"), S("AH", 500, "FGO = 13"), S("CRP", 11, "AHRS_EKF_TYPE 10"), S("CLP", 4, "AHRS_EKF_TYPE 3"),
         S("CLU", 4, "AHRS_EKF_TYPE 12"), S("CLF", 4, "AHRS_EKF_TYPE 13"))
    cite("SHADOW: EKF3 flies and the UKF port / the FGO node + output predictor run in shadow (logged only)",
         S("CLR", 20, "UKF=shadow (ruling D17 V2): EKF3 flies"), S("CLR", 39, "FGO=shadow: EKF3 flies"),
         S("US", 2, "it never drives the vehicle"), S("AC", 528, "SHADOW unless AHRS_EKF_TYPE = 12"))
    cite("Camera heading to EKF3 via ExtNav only in closed loop (1C with heading: EK3_SRC1_YAW 6; UKF port AHRS_UKF_EXTYAW 1); "
         "the FGO node takes /forward_camera/heading_sent", S("CLH", 10, "EK3_SRC1_YAW 6"), S("CLUH", 1, "the UKF fuses the ExtNav"),
         S("RT", 449, "heading:="))
    cite("Offline 1B: EKF3 gets no heading (ruling 2026-09-29); the UKF/FGO arms read the frozen Phase 3 heading",
         S("M", 2884, "RULING — EKF3 in the offline forward-camera comparison"), S("M", 2888, "Only the UKF and FGO get forward-camera arms"),
         S("MM", 219, "def forward_events(trial, arm)"))
    cite("Experiment 5: EKF3 flies on the wall tag (ExtNav position + yaw); UKF-flying uses AHRS_UKF_EXTPOS/EXTYAW; FGO node takes /tags/sent",
         S("HX", 7, "EK3_SRC1_YAW 6"), S("HU", 7, "AHRS_UKF_EXTPOS 1"), S("CLR", 72, "TAG_BRIDGE_FWD=1"))
    cite("Offline replay reads the bag topics (ground truth for scoring only)", S("UR", 67, "/imu/data_raw"),
         S("FR", 101, "want = ["))
    cite("SITL safety watcher wall_watch.py: ground truth + process liveness -> heartbeat file -> fly_trial LAND / stop",
         S("WW", 5, "/ground_truth/pose"), S("WW", 53, "Box and tilt breaches always stop"), S("FT", 493, "safety watcher lost in flight"),
         S("CLR", 117, "wall_watch.py"), S("HS", 14, "WATCH_DEP_LOSS=land"))
    cite("Real-hardware watcher realflight/watcher: mocap (MCP1) + FC telemetry + beacons -> ONE LAND + HEARTBEAT gating FS_GCS; "
         "SITL bench only", S("MW", 3, "Runs on the GROUND STATION"), S("MW", 14, "sends ONE LAND"),
         S("LV", 4, "represented by a BEACON"), S("WFC", 14, "FS_GCS_ENABLE   5"), S("MCP", 1, "MCP1"))
    cite("Companion: in SITL every process ran on the desktop; Pi timing is an ESTIMATE; closed-loop real flights are future work",
         S("M", 13651, "Pi timing, ESTIMATED"), S("M", 12954, "closed-loop real flights are FUTURE WORK"))

    # ---- drawing (RESTYLE 2026-11-13: redrawn at the reader-facing text width, 160 mm, as two stacked panels -
    # (a) the sensors and the relays that carry their measurements, (b) the flight controller (where each estimator
    # runs), the companion FGO node, the safety watchers and the offline replay. Every box and edge from the
    # previous full-page version is kept; an edge that used to cross directly between two regions now crosses the
    # panel break through a small labelled stub at each end (e.g. "flow -> (b)" / "from (a): flow"). File, script
    # and ROS-topic names are replaced throughout with plain descriptions - see the restyle report for the full
    # old -> new table. The cite()/S() calls above are UNCHANGED: they verify the real source files for the index
    # and are independent of what the diagram itself draws.
    from thesis_style import TEXT_WIDTH_IN
    FIG_W_MM = TEXT_WIDTH_IN * 25.4                 # exactly 160 mm (RS-1 text width)
    PT_MM = 0.3528                                   # 1 pt in mm, for sizing boxes from font size
    FS_PANEL, FS_REGION, FS_TITLE, FS_BODY, FS_EDGE, FS_LEGEND = 11.0, 9.6, 9.0, 8.0, 8.0, 8.0
    FS_FLOOR = 8.0   # RS-1 floor, hard-coded (not derived from the declared sizes - that would be circular)
    GREY, DARK, PURPLE, RED = "#f2f2f2", "#333333", "#7B3294", "#C0392B"
    MARGIN, GAP, PAD = 4.0, 2.4, 1.8                 # mm

    def mm(fs):
        return fs * PT_MM

    # a region's frame must clear: its own header offset (mm(FS_REGION)*1.9, where the first box starts) plus the
    # full stacked column height passed in, plus a small bottom margin - "+5.0" alone (an earlier, under-measured
    # constant) let the last box in every region touch or cross the frame's own bottom edge.
    REGION_PAD = mm(FS_REGION) * 1.9 + 2.0

    def wrap_for(text, width_mm, fs, bold=False):
        # 0.60 for bold (box/region titles) vs 0.52 for regular weight - measured conservatively so a line that
        # passes this count never visually overflows its box at render time (checked against DejaVu Sans Bold).
        factor = 0.60 if bold else 0.52
        n = max(8, int((width_mm - 2 * PAD) / (factor * mm(fs))))
        out = []
        for para in str(text).split("\n"):
            out += textwrap.wrap(para, n) or [""]
        return out

    def box_lines(title, body, w, tfs=FS_TITLE, bfs=FS_BODY):
        return wrap_for(title, w, tfs, bold=True), (wrap_for(body, w, bfs) if body else [])

    def box_height(title, body, w, tfs=FS_TITLE, bfs=FS_BODY):
        tl, bl = box_lines(title, body, w, tfs, bfs)
        lh_t, lh_b = mm(tfs) * 1.22, mm(bfs) * 1.28
        return PAD + len(tl) * lh_t + (1.4 if bl else 0.0) + len(bl) * lh_b + PAD

    def draw_box(ax, x, y_top, w, title, body="", ec=DARK, fc="white", lw=1.1, ls="-", tfs=FS_TITLE, bfs=FS_BODY):
        tl, bl = box_lines(title, body, w, tfs, bfs)
        lh_t, lh_b = mm(tfs) * 1.22, mm(bfs) * 1.28
        h = box_height(title, body, w, tfs, bfs)
        ax.add_patch(FancyBboxPatch((x, y_top - h), w, h, boxstyle="round,pad=0,rounding_size=1.0", fc=fc, ec=ec, lw=lw, ls=ls))
        ty = y_top - PAD   # va="top": the text's own top edge goes here, matching box_height's PAD budget exactly
        for i, ln in enumerate(tl):
            ax.text(x + PAD, ty - i * lh_t, ln, fontsize=tfs, weight="bold", va="top", ha="left", color=INK)
        by = y_top - PAD - len(tl) * lh_t - (1.4 if bl else 0.0)
        for i, ln in enumerate(bl):
            ax.text(x + PAD, by - i * lh_b, ln, fontsize=bfs, va="top", ha="left", color=INK)
        return y_top - h

    def draw_column(ax, x, y_top, w, items, **kw):
        """items: (title, body, overrides-dict-or-None). Returns the column's final bottom y."""
        y = y_top
        for title, body, ov in items:
            o = dict(kw)
            if ov:
                o.update(ov)
            y = draw_box(ax, x, y, w, title, body, **o) - GAP
        return y + GAP

    def column_height(items, w, **kw):
        tfs = kw.get("tfs", FS_TITLE); bfs = kw.get("bfs", FS_BODY)
        hs = [box_height(t, b, w, tfs, bfs) for t, b, _ in items]
        return sum(hs) + GAP * max(0, len(hs) - 1)

    def region(ax, x, y_top, w, h, label, fc, ec="#888888", ls="-"):
        ax.add_patch(FancyBboxPatch((x, y_top - h), w, h, boxstyle="round,pad=0,rounding_size=1.6", fc=fc, ec=ec, lw=1.1, ls=ls))
        ax.text(x + 2.4, y_top - 2.6, label, fontsize=FS_REGION, weight="bold", va="top", color="#222222")

    def arrow(ax, p, q, color=DARK, ls="-", lw=1.0, text=None, tpos=0.5, toff=(0, 1.3), tha="center", conn="arc3", tc=None):
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=7.0, color=color, lw=lw, ls=ls,
                                      connectionstyle=conn, shrinkA=0, shrinkB=0))
        if text:
            tx = p[0] + (q[0] - p[0]) * tpos + toff[0]; ty = p[1] + (q[1] - p[1]) * tpos + toff[1]
            ax.text(tx, ty, text, fontsize=FS_EDGE, ha=tha, va="bottom", color=tc or color, linespacing=1.05)

    def elbow2(ax, x_src, y_src, lane_x, x_tgt, y_tgt, color=DARK, lw=1.0, ls="-", text=None, tc=None):
        """Like elbow(), but for connecting two DIFFERENT box edges (e.g. one box's right edge to another box's
        left edge, on opposite sides of the lane) rather than two points on the same edge. The label, if given, is
        placed on the final, horizontal, approach segment (clear of the vertical lane and of either diagonal),
        just above it - this is how "FGO state" and the two LAND edges are labelled without being crossed by their
        own line, the failure an earlier (purely diagonal) version of these three edges had."""
        ax.plot([x_src, lane_x], [y_src, y_src], color=color, lw=lw, ls=ls, solid_capstyle="butt")
        ax.plot([lane_x, lane_x], [y_src, y_tgt], color=color, lw=lw, ls=ls, solid_capstyle="butt")
        arrow(ax, (lane_x, y_tgt), (x_tgt, y_tgt), color=color, lw=lw, ls=ls, conn="arc3,rad=0")
        if text:
            ax.text(0.5 * (lane_x + x_tgt), y_tgt + 0.6, text, fontsize=FS_EDGE, ha="center", va="bottom",
                    color=tc or color, linespacing=0.95)

    def elbow(ax, box_x, y_src, lane_x, y_tgt, color=DARK, lw=1.0, ls="-"):
        """A 3-segment orthogonal connector: (box_x, y_src) -> (lane_x, y_src) -> (lane_x, y_tgt) -> (box_x, y_tgt),
        arrowhead at the end. Used for the internal relay-to-relay edges routed through a gutter lane, so the line
        actually touches both boxes at their own edge (box_x) instead of floating in the gutter between them at a
        fixed lane x the whole way - a defect an earlier draft of this figure had (confirmed from the code: both
        endpoints used the same x, which is never equal to a box's own edge)."""
        ax.plot([box_x, lane_x], [y_src, y_src], color=color, lw=lw, ls=ls, solid_capstyle="butt")
        ax.plot([lane_x, lane_x], [y_src, y_tgt], color=color, lw=lw, ls=ls, solid_capstyle="butt")
        arrow(ax, (lane_x, y_tgt), (box_x, y_tgt), color=color, lw=lw, ls=ls, conn="arc3,rad=0")

    def panel_label_lines(text):
        return wrap_for(text, FIG_W_MM - 2 * MARGIN + 2 * PAD, FS_PANEL, bold=True)   # wrap_for subtracts 2*PAD internally

    def panel_label_height(text):
        return len(panel_label_lines(text)) * mm(FS_PANEL) * 1.25 + mm(FS_PANEL) * 0.3

    def panel_label(ax, x, y_top, text):
        lines = panel_label_lines(text)
        lh = mm(FS_PANEL) * 1.25
        for i, ln in enumerate(lines):
            ax.text(x, y_top - i * lh, ln, fontsize=FS_PANEL, weight="bold", va="top", ha="left", color=INK)
        return y_top - len(lines) * lh - mm(FS_PANEL) * 0.3

    # =============================================================== panel (a): sensors and the measurement relays
    # The first 6 relays are row-aligned with the 6 sensors (same reading order), so their connecting arrows are
    # near-horizontal and cross no other box. The 3 relays with no direct sensor of their own (the rate relay, the
    # flow relay, and the external-navigation sender) sit below, fed by internal edges routed through the gutter
    # between the two columns, which is empty space.
    SENS_X, SENS_W = MARGIN, 72.0
    GUTTER = 12.0                                     # wide enough for 4 separated internal-routing lanes, see below
    STUB_W = 11.0                                     # right-hand lane for the cross-panel stub labels
    REL_X = SENS_X + SENS_W + GUTTER
    REL_W = FIG_W_MM - MARGIN - STUB_W - REL_X
    sensors = [
        ("IMU", "FC's own inertial sensor; read directly by EKF3 and the UKF. Relay below: same samples, on to "
         "the FGO node and the offline replay.", None),
        ("Downward camera", "30 Hz, rigid mount, facing down (height −0.25 m).", None),
        ("Downward LiDAR", "Single beam, 30 Hz, facing down (height −0.12 m).", None),
        ("Forward camera", "60°, 640×480, 30 Hz (forward-camera vehicle only).", None),
        ("AprilTags", "Floor tags (downward camera, Exp. 2/3); wall tag (forward camera, Exp. 5).", None),
        ("Ground truth / motion capture", "Simulator pose (simulation); motion-capture packets (real; watcher "
         "bench only).", None),
    ]
    relays = [
        ("IMU relay", "Accelerometer + gyroscope samples, for the UKF (offline) and FGO only - EKF3 and the UKF "
         "port read the IMU directly.", None),
        ("Optical-flow tracker", "Shi-Tomasi + Lucas-Kanade + RANSAC; estimates flow, removes rotation using the "
         "rate relay below.", None),
        ("Range relay", "Sends the downward range to the flight controller.", None),
        ("Heading relay", "Vanishing-point heading from the forward camera (C++ in closed loop).", {"ec": PURPLE}),
        ("Tag relays", "Position and heading from a detected floor or wall tag.", {"ec": PURPLE}),
        ("Ground-truth relay", "Simulator pose, for scoring and for the closed-loop safety watcher (read live, "
         "not from the recording).", None),
        ("Flow relay", "Sends the optical-flow tracker's measurement to the flight controller.", None),
        ("External-navigation sender", "Heading or a tag reading (never both): yaw only (heading), or position + "
         "yaw (tag), as one update for the flight controller.", {"ec": PURPLE}),
        ("Rate relay", "Body angular rates, fed back from the flight controller's own attitude estimate (panel b).", None),
    ]
    LABEL_A = "(a) Sensors and the relays that carry their measurements"
    LABEL_B = "(b) The flight controller: where each estimator runs, and what happens downstream"
    h_sens = column_height(sensors, SENS_W); h_rel = column_height(relays, REL_W)
    NOTE_H = box_height("Recorded", "Every relay's output above is written to the flight log, for the offline "
                         "replay and evaluation in panel (b).", REL_W + SENS_W + GUTTER)
    # mm(FS_REGION)*1.9: the gap between a region's own top edge and where its first box starts (sy_top below) -
    # previously missing from this budget, which (along with "+5.0" on the region frame itself, also fixed) let
    # the last box in each column sit flush with, or past, the region's bottom edge.
    H_A = panel_label_height(LABEL_A) + mm(FS_REGION) * 1.9 + max(h_sens, h_rel) + GAP + NOTE_H + 2 * MARGIN

    # =============================================================== panel (b): flight controller and downstream
    STUB_B = 18.0                                      # left-hand lane for the incoming cross-panel stub labels
    GUTTER_B = 28.0                                     # wide enough for 3 orthogonally-routed, labelled edges (see draw_panel_b)
    FC_X, FC_W = MARGIN + STUB_B, 96.0 - STUB_B - (GUTTER_B - 6.0)
    RC_X, RC_W = FC_X + FC_W + GUTTER_B, FIG_W_MM - MARGIN - (FC_X + FC_W + GUTTER_B)
    fc_items = [
        ("EKF3", "Fixed baseline. 24 states, quaternion; fuses flow, range, heading or tag when configured. "
         "FLYING at AHRS_EKF_TYPE 3; otherwise passive (own state still logged).", {"ec": C["EKF3"], "lw": 1.5}),
        ("UKF (flight-controller port)", "15 states, Euler; same inputs as EKF3. FLYING at AHRS_EKF_TYPE 12; "
         "otherwise shadow (logged only).", {"ec": C["UKF"], "lw": 1.5}),
        ("FGO interface", "Receives the FGO node's state; predicts forward on the IMU between updates. FLYING at "
         "AHRS_EKF_TYPE 13; otherwise shadow.", {"ec": C["FGO"], "lw": 1.5}),
        ("Estimator selector", "AHRS_EKF_TYPE picks who flies: 10 = simulator truth (Exp. 1A, 1B, 2, 3, 4: open "
         "loop); 3 = EKF3, 12 = UKF, 13 = FGO (Exp. 1C, 5, 5S: closed loop).", {"lw": 1.3}),
        ("Position controller and motors", "Mission and LAND from the flight script, or the FC's own failsafes. "
         "Vehicle: the Gazebo iris model.", None),
    ]
    rc_items = [
        ("FGO node", "GTSAM batch fixed-lag smoother, 0.25 s window, LM ≤ 2 iterations, 30 Hz keyframes. In: IMU, "
         "flow, range, rates (panel a), plus heading (1C) or tags (Exp. 5) when set. Out: state, to the flight "
         "controller. Runs separately - simulation: this desktop; real flights: a planned companion computer, "
         "timing estimated.", {"ec": C["FGO"], "lw": 1.4}),
        ("Closed-loop safety watcher", "Reads ground truth live (not the recording) and bridge/node liveness; "
         "writes a heartbeat the flight script won't arm without. LANDs on loss; box or tilt breach stops the "
         "run. Exp. 1C, 5, 5S.", {"ec": RED, "lw": 1.3}),
        ("Real-hardware safety watcher", "Mocap + FC telemetry + liveness beacons; one LAND command + a heartbeat "
         "gating the FC's own failsafe (Land, 3 s); also arming checks for heading and speed. Tested on the "
         "ground only so far.", {"ec": RED, "lw": 1.3, "ls": (0, (3, 2))}),
    ]
    off_w = (FIG_W_MM - 2 * MARGIN - 3 * GAP) / 4.0
    offline_items = [
        ("Recorded data", "The recordings above, plus the flight controller's own logged state from the same flight.", None),
        ("UKF replay", "The UKF run again on the recording (+ a smoother pass for the hindsight track).", {"ec": C["UKF"]}),
        ("FGO replay", "The FGO run again on the recording: live and whole-flight hindsight versions.", {"ec": C["FGO"]}),
        ("Evaluation", "Cruise-window ATE vs. the simulator pose (EKF3 from its own logged state); 1B heading: "
         "the frozen validation outputs.", None),
    ]
    h_fc = column_height(fc_items, FC_W); h_rc = column_height(rc_items, RC_W)
    h_off = max(box_height(t, b, off_w) for t, b, _ in offline_items)
    LEGEND_H = 44.0
    OFFLINE_TITLE_H = mm(FS_REGION) * 1.8   # the offline row's own title line, previously missing from the H_B budget
    H_B = panel_label_height(LABEL_B) + mm(FS_REGION) * 1.9 + max(h_fc, h_rc) + GAP + OFFLINE_TITLE_H + h_off + GAP + LEGEND_H + 2 * MARGIN

    PANEL_GAP = 8.0
    H = H_A + PANEL_GAP + H_B
    fig = plt.figure(figsize=(FIG_W_MM / 25.4, H / 25.4)); fig.patch.set_facecolor("white")
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, FIG_W_MM); ax.set_ylim(0, H); ax.axis("off")
    ax.patch.set_facecolor("white")

    def draw_panel_a(ax):
        # ---------------------------------------------------------------- panel (a)
        # No outer frame is drawn around the whole figure (the previous version's enclosing box left a blank band at
        # the top where an in-figure title used to sit - the "empty title box" - once the title was removed; this
        # version has no such enclosing frame at all, only the tight region frames below).
        y = panel_label(ax, MARGIN, H - 1.0, LABEL_A)
        top_a = y
        region(ax, SENS_X - 2.0, top_a, SENS_W + 4.0, h_sens + REGION_PAD, "Sensors", "#f7f7f7")
        region(ax, REL_X - 2.0, top_a, REL_W + 4.0, h_rel + REGION_PAD, "Measurement relays", "#f7f7f7")
        sy_top = top_a - mm(FS_REGION) * 1.9
        bottoms_s = []
        ys = sy_top
        for title, body, ov in sensors:
            o = dict(ov) if ov else {}
            ys2 = draw_box(ax, SENS_X, ys, SENS_W, title, body, **o)
            bottoms_s.append((title, ys, ys2)); ys = ys2 - GAP
        bottoms_r = []
        yr = sy_top
        for title, body, ov in relays:
            o = dict(ov) if ov else {}
            yr2 = draw_box(ax, REL_X, yr, REL_W, title, body, **o)
            bottoms_r.append((title, yr, yr2)); yr = yr2 - GAP
        pos_s = {t: (top, bot) for t, top, bot in bottoms_s}
        pos_r = {t: (top, bot) for t, top, bot in bottoms_r}

        def mid(d, k):
            top, bot = d[k]; return 0.5 * (top + bot)

        # sensor -> relay edges: the first 6 relays are row-aligned with the 6 sensors, so every one of these is a
        # short, near-horizontal line that crosses no other box.
        arrow(ax, (SENS_X + SENS_W, mid(pos_s, "IMU")), (REL_X, mid(pos_r, "IMU relay")))
        arrow(ax, (SENS_X + SENS_W, mid(pos_s, "Downward camera")), (REL_X, mid(pos_r, "Optical-flow tracker")))
        arrow(ax, (SENS_X + SENS_W, mid(pos_s, "Downward LiDAR")), (REL_X, mid(pos_r, "Range relay")))
        arrow(ax, (SENS_X + SENS_W, mid(pos_s, "Forward camera")), (REL_X, mid(pos_r, "Heading relay")), color=PURPLE)
        arrow(ax, (SENS_X + SENS_W, mid(pos_s, "AprilTags")), (REL_X, mid(pos_r, "Tag relays")), color=PURPLE)
        arrow(ax, (SENS_X + SENS_W, mid(pos_s, "Ground truth / motion capture")), (REL_X, mid(pos_r, "Ground-truth relay")))
        # relay -> relay edges for the 3 relays with no sensor of their own: routed through the empty gutter between
        # the two columns, on 4 separated vertical lanes so no two lines coincide. Each label is a short, UNROTATED
        # word placed in the gap just beside its own arrowhead (never along the line itself), so a label can never
        # reach into a neighbouring lane's line or another label - the failure mode an earlier draft had with rotated
        # labels spaced too closely together in a narrow gutter.
        g1, g2, g3, g4 = REL_X - 2.0, REL_X - 4.4, REL_X - 6.8, REL_X - 9.2
        y_tracker_out = mid(pos_r, "Optical-flow tracker") - 2.0   # flow leaves here
        y_tracker_in = mid(pos_r, "Optical-flow tracker") + 2.0    # rates arrives here (distinct point, same box)
        elbow(ax, REL_X, y_tracker_out, g1, mid(pos_r, "Flow relay"))
        elbow(ax, REL_X, pos_r["Heading relay"][1], g2, mid(pos_r, "External-navigation sender"), color=PURPLE)
        elbow(ax, REL_X, pos_r["Tag relays"][1], g3, mid(pos_r, "External-navigation sender") + 1.0, color=PURPLE)
        # the heading/tag lines are not separately labelled: purple colour plus the adjacent "Heading relay"/"Tag
        # relays" boxes they leave already identify them, and the gutter is too narrow for a horizontal label there
        # without reaching into the sensor or relay column's own frame (the failure an earlier, rotated-label draft had).
        elbow(ax, REL_X, mid(pos_r, "Rate relay"), g4, y_tracker_in)
        # "rates" labels the one internal edge whose purpose isn't already obvious from box adjacency (the rate
        # relay is far below the tracker it feeds, not next to it). Centred in the gutter's clear width, just
        # below the tracker. "flow" (tracker -> flow relay, g1) is NOT labelled here: at this y the Downward
        # LiDAR -> Range relay sensor edge (a different row's arrow) also crosses the gutter, and Flow relay's own
        # body text ("Sends the optical-flow tracker's measurement...") already names the connection.
        gutter_mid = 0.5 * ((SENS_X + SENS_W + 2.0) + (REL_X - 2.0))
        ax.text(gutter_mid, pos_r["Optical-flow tracker"][1] - 0.8, "rates", fontsize=FS_EDGE, ha="center", va="top", color=DARK)
        # cross-panel stubs, in a dedicated lane to the right of the relay column: outgoing (5), one incoming (attitude).
        stub_x0, stub_x1 = REL_X + REL_W + 0.8, FIG_W_MM - MARGIN
        ax.text(0.5 * (stub_x0 + stub_x1), pos_r["IMU relay"][0] + 1.5, "to (b)", fontsize=FS_EDGE, style="italic",
                ha="center", va="bottom", color=INK2)
        for key, label, colour in (("IMU relay", "IMU", DARK), ("Optical-flow tracker", "", DARK), ("Range relay", "range", DARK),
                                    ("Heading relay", "", PURPLE), ("Tag relays", "", PURPLE),
                                    ("Ground-truth relay", "ground\ntruth", DARK), ("Flow relay", "flow", DARK),
                                    ("External-navigation sender", "ExtNav", PURPLE)):
            if not label:
                continue
            yk = mid(pos_r, key)
            arrow(ax, (REL_X + REL_W, yk), (stub_x1, yk), color=colour, ls=":", lw=0.8)
            ax.text(stub_x0, yk + 0.7, label, fontsize=FS_EDGE, color=colour, ha="left", va="bottom", linespacing=0.95)
        # Rate relay carries BOTH directions: it receives the flight controller's own attitude (incoming) and its
        # republished rates are a direct input to the FGO node (outgoing) as well as feeding the tracker
        # internally above - the FGO node's own body text ("In: IMU, flow, range, rates") names this input, so the
        # stub is required for the connection table to balance, not just for symmetry with the other 5 relays.
        yk_in, yk_out = mid(pos_r, "Rate relay") - 5.5, mid(pos_r, "Rate relay") + 3.5
        arrow(ax, (stub_x1, yk_in), (REL_X + REL_W, yk_in), color=DARK, ls=":", lw=0.8)
        ax.text(stub_x0, yk_in + 0.7, "from (b):\nattitude", fontsize=FS_EDGE, color=DARK, ha="left", va="bottom", linespacing=0.95)
        arrow(ax, (REL_X + REL_W, yk_out), (stub_x1, yk_out), color=DARK, ls=":", lw=0.8)
        ax.text(stub_x0, yk_out + 0.7, "rates", fontsize=FS_EDGE, color=DARK, ha="left", va="bottom", linespacing=0.95)
        bottom_a_content = min(ys, yr)
        draw_box(ax, SENS_X, bottom_a_content - 1.5, REL_W + SENS_W + GUTTER, "Recorded",
                 "Every relay's output above is written to the flight log, for the offline replay and evaluation in panel (b).",
                 ec="#888888", fc="#f5f5f5")

    def draw_panel_b(ax):
        # ---------------------------------------------------------------- panel (b)
        y = panel_label(ax, MARGIN, H - H_A - PANEL_GAP - 1.0, LABEL_B)
        top_fc = y
        region(ax, FC_X - 2.0, top_fc, FC_W + 4.0, h_fc + REGION_PAD, "Flight controller", "#eaf2fb")
        region(ax, RC_X - 2.0, top_fc, RC_W + 4.0, h_rc + REGION_PAD, "Companion and safety", "#fdf0e6")
        fc_top = top_fc - mm(FS_REGION) * 1.9
        yf = fc_top
        pos_fc = {}
        for title, body, ov in fc_items:
            o = dict(ov) if ov else {}
            yf2 = draw_box(ax, FC_X, yf, FC_W, title, body, **o)
            pos_fc[title] = (yf, yf2); yf = yf2 - GAP
        yc = fc_top
        pos_rc = {}
        for title, body, ov in rc_items:
            o = dict(ov) if ov else {}
            yc2 = draw_box(ax, RC_X, yc, RC_W, title, body, **o)
            pos_rc[title] = (yc, yc2); yc = yc2 - GAP
        bottom_fc_block = min(yf, yc)

        def midb(d, k):
            top, bot = d[k]; return 0.5 * (top + bot)

        # incoming stubs from panel (a), in a dedicated lane to the left of the flight-controller box (width STUB_B).
        # Flow, range AND ExtNav all fan out to BOTH EKF3 and the UKF port (one combined label per box, matching the
        # original single "flow, range and ExtNav fan out to EKF3 and the UKF port" note). ExtNav does NOT go to the
        # estimator selector, which only reads the AHRS_EKF_TYPE setting, not sensor data - a routing bug in an
        # earlier draft of this figure, fixed.
        stub_b_x = MARGIN + 1.0
        y_ekf3_in = midb(pos_fc, "EKF3") + 3.0
        y_ekf3_out = midb(pos_fc, "EKF3") - 6.0
        y_ukf_in = midb(pos_fc, "UKF (flight-controller port)")
        arrow(ax, (stub_b_x, y_ekf3_in), (FC_X, y_ekf3_in), color=DARK, ls=":", lw=0.9)
        ax.text(MARGIN, y_ekf3_in + 0.6, "from (a):\nflow, range,\nExtNav", fontsize=FS_EDGE, ha="left", va="bottom",
                color=DARK, linespacing=0.95)
        arrow(ax, (stub_b_x, y_ukf_in), (FC_X, y_ukf_in), color=DARK, ls=":", lw=0.9)
        ax.text(MARGIN, y_ukf_in + 0.6, "from (a):\nflow, range,\nExtNav", fontsize=FS_EDGE, ha="left", va="bottom",
                color=DARK, linespacing=0.95)
        arrow(ax, (FC_X, y_ekf3_out), (stub_b_x, y_ekf3_out), color=DARK, ls=":", lw=0.9)
        ax.text(MARGIN, y_ekf3_out - 0.6, "attitude\n→ (a)", fontsize=FS_EDGE, ha="left", va="top", color=DARK, linespacing=0.95)
        # internal: estimators -> selector -> position controller
        for key in ("EKF3", "UKF (flight-controller port)", "FGO interface"):
            arrow(ax, (FC_X + FC_W - 1.5, pos_fc[key][1]), (FC_X + FC_W - 1.5, pos_fc[key][1] - GAP + 0.3), lw=1.6)
        arrow(ax, (FC_X + FC_W / 2, pos_fc["Estimator selector"][1]), (FC_X + FC_W / 2, pos_fc["Position controller and motors"][0]),
              lw=2.2)
        # FGO node <-> FGO interface, and the two safety-watcher edges: each label sits in the gutter between the two
        # columns (width GUTTER_B), anchored at the FC-side (target) end rather than the line's midpoint, so it never
        # reaches back into either box's own text.
        gx = FC_X + FC_W + 1.4
        # These 3 edges each cross the full GUTTER_B gutter between very different rows (FGO node near the top of
        # the companion column to FGO interface in the middle of the flight-controller column, etc.), so a label
        # placed anywhere directly on a straight diagonal sits in the line's own path - the failure an earlier
        # draft had ("FGO state" and "land" both crossed by their own arrow). Each is instead routed as an
        # orthogonal elbow2() (horizontal - vertical - horizontal), with its label on the final, purely horizontal,
        # approach segment, which no diagonal crosses. Three separate lane x's, ordered so none of the three
        # horizontal label segments overlaps another lane's vertical run.
        lane_fgo, lane_land1, lane_land2 = FC_X + FC_W + 10.0, FC_X + FC_W + 18.0, FC_X + FC_W + 24.0
        y_fgo = pos_fc["FGO interface"][0] + 2.5
        elbow2(ax, RC_X, midb(pos_rc, "FGO node"), lane_fgo, FC_X + FC_W, y_fgo, color=C["FGO"], lw=1.5,
               text="FGO\nstate")
        # the FGO node's own inputs: a stub arriving at its top, from the gutter (the only edge into the companion
        # panel other than the "FGO state" edge going the other way, above/below it)
        y_fgo_in = pos_rc["FGO node"][0] - 9.0
        arrow(ax, (gx, y_fgo_in), (RC_X, y_fgo_in), color=C["FGO"], ls=":", lw=0.9)
        ax.text(gx, y_fgo_in + 0.6, "from\n(a)", fontsize=FS_EDGE, ha="left", va="bottom", color=C["FGO"], linespacing=0.95)
        # ground truth's own stub: the closed-loop safety watcher is the one box in panel (b) that reads it live
        # (every other panel-b consumer of ground truth is the OFFLINE evaluation, via "Recorded data" below).
        # Pinned at least 12 mm below y_fgo (not just below this box's own top) - the two labels collided when each
        # was positioned independently of the other, a defect found by review.
        y_gt_in = min(pos_rc["Closed-loop safety watcher"][0] - 2.5, y_fgo - 12.0)
        arrow(ax, (gx, y_gt_in), (RC_X, y_gt_in), color=DARK, ls=":", lw=0.9)
        ax.text(gx, y_gt_in + 0.6, "from\n(a)", fontsize=FS_EDGE, ha="left", va="bottom", color=DARK, linespacing=0.95)
        y_land1 = pos_fc["Position controller and motors"][0] + 6.5
        elbow2(ax, RC_X, midb(pos_rc, "Closed-loop safety watcher"), lane_land1, FC_X + FC_W, y_land1, color=RED,
               lw=1.3, text="land (via\nthe flight\nscript)")
        y_land2 = pos_fc["Position controller and motors"][0] - 2.0
        elbow2(ax, RC_X, midb(pos_rc, "Real-hardware safety watcher"), lane_land2, FC_X + FC_W, y_land2, color=RED,
               lw=1.3, ls=(0, (3, 2)), text="land /\nheartbeat")

        # offline replay row - its own title sits in the OFFLINE_TITLE_H band reserved above the boxes, not jammed
        # into the same gap that separates it from the flight-controller/companion row above (that gap overlapped the
        # "Real-hardware safety watcher" box's own border in an earlier draft of this figure).
        title_top = bottom_fc_block - GAP
        off_top = title_top - OFFLINE_TITLE_H
        xo = MARGIN
        pos_off = {}
        for title, body, ov in offline_items:
            o = dict(ov) if ov else {}
            bot = draw_box(ax, xo, off_top, off_w, title, body, **o)
            pos_off[title] = (off_top, bot); xo += off_w + GAP
        # a left-to-right chain for the offline row, in reading order: recorded data -> UKF replay -> FGO replay -> evaluation
        xo = MARGIN
        for _ in range(3):
            x1 = xo + off_w; x2 = xo + off_w + GAP
            yband = 0.5 * (pos_off["Recorded data"][0] + pos_off["Recorded data"][1])
            arrow(ax, (x1, yband), (x2, yband), ls="--")
            xo += off_w + GAP
        bottom_off = min(b for _, b in pos_off.values())
        ax.text(MARGIN, title_top, "Offline replay and evaluation (workstation, after the flight)", fontsize=FS_REGION,
                weight="bold", va="top", color="#222222")

        # legend
        leg_y = bottom_off - 6.0
        leg = [Line2D([], [], color=DARK, lw=1.2, label="live data path (simulated flights)"),
               Line2D([], [], color=PURPLE, lw=1.6, label="camera heading or a tag via external navigation (closed-loop\n"
                      "heading runs, Exp. 5; passive EKF3 when a tag is present). Offline,\nonly the UKF and FGO get heading; EKF3 gets none."),
               Line2D([], [], color=DARK, lw=1.2, ls="--", label="offline replay on recorded data (passive estimators)"),
               Line2D([], [], color=RED, lw=1.3, label="safety action (land); dashed = real hardware (ground-tested only)"),
               Line2D([], [], color=DARK, lw=2.2, label="flying: the selected estimator drives the vehicle;\nothers are shadow (logged only)")]
        # bbox_transform=ax.transData (not the legend default, axes-fraction) - this must work identically whether
        # ax spans the whole combined figure (ylim (0, H)) or stands alone as just this panel (ylim (0, H_B)), so
        # it is anchored in the same absolute data coordinates draw_panel_b() uses everywhere else.
        leg_obj = ax.legend(handles=leg, loc="upper left", bbox_to_anchor=(MARGIN, leg_y), bbox_transform=ax.transData,
                            fontsize=FS_LEGEND, frameon=True, framealpha=1.0, edgecolor="#888888", handlelength=2.4,
                            borderpad=0.6, labelspacing=0.9)
        # Measure the legend's ACTUAL rendered extent (not a guessed constant) and fail loudly if LEGEND_H left too
        # little room - this is how the "legend runs off the bottom of the canvas" failure mode (found by review,
        # LEGEND_H=44 was too small) is now caught mechanically instead of by eye.
        fig_local = ax.get_figure(); fig_local.canvas.draw()
        bbox_data = leg_obj.get_window_extent(fig_local.canvas.get_renderer()).transformed(ax.transData.inverted())
        assert bbox_data.y0 >= -0.5, (f"legend bottom at y={bbox_data.y0:.2f} is below this panel's own y=0 - "
                                       f"LEGEND_H is too small by about {-bbox_data.y0:.1f} mm")

    def assert_no_text_overlap(fig_):
        """Mechanical check (plain assert, no check()): no two distinct Text labels overlap on the rendered page.
        Found real collisions by eye through several rounds of this figure's redesign (stub labels, gutter edge
        labels); this makes that failure mode a hard build error instead of something only caught by re-reading
        crops. Deliberately NOT extended to "does an arrow/box path cross a text" - the legend and box titles are
        expected to sit on/near their own box border, so that check would need a bigger exemption list than it's
        worth for this figure; text-vs-text overlap already catches everything found in review."""
        fig_.canvas.draw()
        renderer = fig_.canvas.get_renderer()
        boxes = []
        for t in fig_.findobj(matplotlib.text.Text):
            if not t.get_text().strip():
                continue
            bb = t.get_window_extent(renderer)
            if bb.width <= 0 or bb.height <= 0:
                continue
            boxes.append((t, bb))
        for i, (t1, b1) in enumerate(boxes):
            for t2, b2 in boxes[i + 1:]:
                if b1.overlaps(b2):
                    raise AssertionError(f"text overlap: {t1.get_text()!r} crosses {t2.get_text()!r}")

    draw_panel_a(ax)
    draw_panel_b(ax)
    # ---- font-size floor self-check (plain assert: must NOT use check(), which would leak into Table 3.1's count)
    sizes = [t.get_fontsize() for t in fig.findobj(matplotlib.text.Text) if t.get_text().strip()]
    assert sizes and min(sizes) >= FS_FLOOR - 1e-6, f"a text object is smaller than the declared floor {FS_FLOOR} pt: min {min(sizes) if sizes else None}"
    assert_no_text_overlap(fig)

    base = os.path.join(OUTF, "methods_architecture")
    fig.savefig(base + ".png", dpi=300, facecolor="white"); fig.savefig(base + ".pdf", facecolor="white"); plt.close(fig)
    print(f"methods_architecture: {FIG_W_MM:.1f} x {H:.1f} mm, smallest font {min(sizes):.1f} pt (floor {FS_FLOOR:.1f} pt)")

    # Split per-panel files (RESTYLE 2026-11-13, advisor-flagged): the combined file above is kept, unchanged, for
    # eval/figs_thesis.py's combine_extra_items() and build_thesis_assets.py, which both still reference
    # "methods_architecture.png"/".pdf" as a single file. But that combined file is 160 x 460 mm - taller than any
    # single printed page - and figs_thesis.py's own caption_page() scales a whole combined-PDF image down to fit
    # an A4-landscape page, which would shrink an image this tall far below 8 pt. These two new files are each
    # independently sized to ~H_A / ~H_B mm (both close to a single portrait page height) at the SAME 160 mm
    # native width, so each is legible on its own without depending on any downstream scaling. draw_panel_a()/
    # draw_panel_b() use only the absolute data coordinates already computed above (shared with the combined
    # figure), so reusing them on a new, independently-sized axes with a matching ylim window reproduces exactly
    # the same content at the correct physical scale - no coordinate math is duplicated or re-derived.
    # NOT yet wired into eval/figs_thesis.py or build_thesis_assets.py - that is a follow-up for whoever owns
    # those files (out of this generator's own scope), noted in the restyle report.
    fig_a = plt.figure(figsize=(FIG_W_MM / 25.4, H_A / 25.4)); fig_a.patch.set_facecolor("white")
    ax_a = fig_a.add_axes([0, 0, 1, 1]); ax_a.set_xlim(0, FIG_W_MM); ax_a.set_ylim(H - H_A, H); ax_a.axis("off")
    ax_a.patch.set_facecolor("white")
    draw_panel_a(ax_a)
    sizes_a = [t.get_fontsize() for t in fig_a.findobj(matplotlib.text.Text) if t.get_text().strip()]
    assert sizes_a and min(sizes_a) >= FS_FLOOR - 1e-6, f"panel (a): text below the floor: min {min(sizes_a) if sizes_a else None}"
    assert_no_text_overlap(fig_a)
    base_a = os.path.join(OUTF, "methods_architecture_a")
    fig_a.savefig(base_a + ".png", dpi=300, facecolor="white"); fig_a.savefig(base_a + ".pdf", facecolor="white"); plt.close(fig_a)
    print(f"methods_architecture_a: {FIG_W_MM:.1f} x {H_A:.1f} mm, smallest font {min(sizes_a):.1f} pt")

    fig_b = plt.figure(figsize=(FIG_W_MM / 25.4, H_B / 25.4)); fig_b.patch.set_facecolor("white")
    ax_b = fig_b.add_axes([0, 0, 1, 1]); ax_b.set_xlim(0, FIG_W_MM); ax_b.set_ylim(0, H_B); ax_b.axis("off")
    ax_b.patch.set_facecolor("white")
    draw_panel_b(ax_b)
    sizes_b = [t.get_fontsize() for t in fig_b.findobj(matplotlib.text.Text) if t.get_text().strip()]
    assert sizes_b and min(sizes_b) >= FS_FLOOR - 1e-6, f"panel (b): text below the floor: min {min(sizes_b) if sizes_b else None}"
    assert_no_text_overlap(fig_b)
    base_b = os.path.join(OUTF, "methods_architecture_b")
    fig_b.savefig(base_b + ".png", dpi=300, facecolor="white"); fig_b.savefig(base_b + ".pdf", facecolor="white"); plt.close(fig_b)
    print(f"methods_architecture_b: {FIG_W_MM:.1f} x {H_B:.1f} mm, smallest font {min(sizes_b):.1f} pt")
    # RESTYLE (2026-11-13, caption plain-language pass): the caption is now 4 plain sentences with no dates, D-numbers,
    # commit hashes, file names or line citations, and no new numbers (none at all, so the "only numbers already
    # present may appear" rule is trivially satisfied). Everything removed from the previous, longer caption -
    # experiment-id enumeration, AHRS_EKF_TYPE and AP_NavFGO, the companion/Pi detail, the two watchers' scope -
    # is preserved verbatim in docs/thesis/figures_thesis/caption_detail_c.md.
    # CAPTION (second shortening, 2026-11-14): 1-3 plain sentences; the open-loop/closed-loop experiment-structure
    # sentence and the "FGO runs as a separate process" sentence are dropped from the body (neither is needed to
    # read the diagram) and kept verbatim in caption_detail.md.
    plain_caption = ("Panel (a) shows the sensors and the relays that carry their measurements to the flight "
                      "controller and to the recorded data used offline. Panel (b) shows the flight controller, "
                      "where each of the three estimators runs, outlined in its own colour (EKF3 blue, UKF green, "
                      "FGO orange), alongside the safety watchers and the offline replay and evaluation.")
    ITEMS.append(dict(num="Figure 3.1", name="methods_architecture", kind="figure",
                      title="System architecture: sensors, bridges, the three estimators and where each one runs",
                      caption=plain_caption, files=["methods_architecture.png", "methods_architecture.pdf",
                      "methods_architecture_a.png", "methods_architecture_a.pdf", "methods_architecture_b.png",
                      "methods_architecture_b.pdf"], checks=[],
                      sources=srcs, chapter="Chapter 3 (method): the architecture the estimators, experiments and safety tables refer to"))
    from thesis_style import write_caption
    write_caption("methods_architecture", "Figure 3.1. System architecture: sensors, bridges, the three estimators and where each "
                  "one runs.\n\n" + ITEMS[-1]["caption"] + "\n\nVerdicts: Table A.4, none (descriptive).")
    print("wrote methods_architecture.png/.pdf")


# ======================================================================== Table 3.1: estimator design
def tab_design():
    # derived: EKF3 prediction period from 5 frames of the 400 Hz loop (CLAUDE "EKF3 Prediction dt")
    from decimal import Decimal as _D
    dt = 5 * (1.0 / 400.0); dt_s, dt_ms = rd(dt, 4), rd(float(_D(str(dt)).scaleb(3)), 1)     # s -> ms by an exact decimal shift (units pass)
    check("EKF3 prediction period = 5 frames × 1/400 s (s), printed in ms in Table 3.1", dt_s, grab("N", 183, r"\*\*([0-9.]+) s\*\*"), "N:183")
    check("UKF port predict period printed in Table 3.1 (ms) = EKF3's", dt_ms, grab("N", 186, r"port ([0-9.]+) ms"), "N:186")
    rows = [
        ["where it runs",
         f"ArduPilot's EKF3 at the pinned commit, on the flight controller (SITL). Flies at AHRS_EKF_TYPE 3 "
         f"[{S('N', 411, 'ArduPilot pinned commit')}; {S('CLP', 4, 'AHRS_EKF_TYPE 3')}]",
         f"Offline: Python ukf_core.py on the bags [{S('UC', 7, '15-state IMU-driven UKF')}]. Flight controller: the C++ port "
         f"AP_NavUKF, flies at AHRS_EKF_TYPE 12 [{S('UKH', 2, 'AP_NavUKF: 15-state unscented Kalman filter')}; {S('AH', 499, 'UKF = 12')}]",
         f"Offline: Python GTSAM (fgo_core.py). Flight: a node outside ArduPilot (Python or C++) whose state the in-firmware "
         f"AP_NavFGO output predictor propagates; flies at AHRS_EKF_TYPE 13 [{S('FGH', 2, 'run OUTSIDE ArduPilot')}; {S('AH', 500, 'FGO = 13')}]"],
        ["state vector",
         f"24 states [{S('E3H', 539, 'VectorN<ftype,24> Vector24')}]",
         f"15: position, velocity, roll/pitch/yaw, gyro bias and accelerometer bias, in EKF3's delta units "
         f"[{S('MM', 29, 'N = 15')}; {S('UC', 7, 'delta-form biases matching EKF3')}]",
         f"Per keyframe: pose X(k) (Pose3), velocity V(k) and IMU bias B(k) (rates) [{S('FD', 141, '`X(k)` | `gtsam.Pose3`')}; "
         f"{S('FD', 143, '`B(k)`')}]"],
        ["attitude",
         f"quaternion [{S('E3H', 575, 'QuaternionF quat;')}]",
         f"ZYX Euler angles [{S('UC', 7, 'ZYX Euler')}]",
         f"Rot3 inside Pose3 [{S('FC', 120, 'Pose3(Rot3.Ypr(')}]"],
        ["filter or smoother",
         "extended Kalman filter",
         "unscented Kalman filter (an RTS smoother over its predict nodes gives the hindsight track in Experiments 2 and 4 "
         f"[{S('M', 10146, 'unscented RTS smoother')}])",
         f"batch fixed-lag smoother, window 0.25 s, Levenberg–Marquardt capped at 2 iterations (warm-started), 30 Hz keyframes "
         f"[{S('FC', 90, 'BatchFixedLagSmoother(window, lm)')}; {S('M', 10129, 'The FGO uses window 0.25 s, batch fixed-lag, 2 LM iterations and 30 Hz keyframes')}; "
         f"{S('N', 451, 'LM iterations cap')}; {S('CN', 62, 'window_s')}]. Hindsight: the whole-flight batch"],
        ["prediction",
         f"every 5 IMU frames: {dt_ms} ms (derived from the source, not logged) [{S('N', 183, 'Frames per prediction')}; "
         f"{S('N', 184, 'derived, not logged')}]",
         f"port {dt_ms} ms (DAL frames); offline 15.00 ms, with the process noise scaled to EKF3's per-second densities "
         f"[{S('N', 186, 'UKF predict dt')}; {S('N', 187, 'identical per-second densities')}]",
         f"every 333 Hz IMU sample is preintegrated between keyframes [{S('CL', 719, 'Feed every 333 Hz sample')}]"],
        ["yaw cap (no yaw sensor)",
         f"zero-innovation synthetic yaw, checked every 140 ms, fused only when the quaternion variance trace exceeds 0.01; "
         f"R 0.5 rad [{S('E3Y', 263, 'lastSynthYawTime_ms > 140')}; {S('E3Y', 274, '> 0.01f')}; {S('N', 158, 'every 140 ms')}; {S('M', 9527, 'zero-innovation yaw pseudo-measurement')}]",
         f"the same mechanism, gated on the Euler attitude trace 0.04 rad² [{S('UC', 46, 'YAW_DT=0.14')}; {S('UC', 47, 'ATT_VAR_GATE=0.04')}; "
         f"{S('N', 160, 'UKF pseudo-yaw gate')}]",
         f"the same gate (0.04), σ 0.5 rad; gating ruled to match EKF3 and the UKF [{S('FC', 51, 'YAW_DT = 0.14')}; "
         f"{S('FC', 52, 'ATT_VAR_GATE = 0.04')}; {S('M', 12353, 'FGO yaw cap: GATED')}]"],
        ["flow and range fusion rate",
         f"flow 15.1 Hz, range 16 Hz (recorded as EKF3 design) [{S('M', 12338, 'EKF3 fuses flow at 15.1 Hz and range at 16 Hz')}; "
         f"{S('M', 12359, 'recorded as EKF3 design under D18')}]",
         f"both at 30 Hz, same per-sample σ [{S('M', 12338, 'Flow and range fusion rates')}]",
         "both at 30 Hz, same per-sample σ (same source)"],
        ["gating",
         f"flow NIS gate 9 (3σ), range height 25 (5σ, HGT_I_GATE with range as the height source), flow above 2.5 rad/s rejected (signed); flow quality is a binary accept "
         f"[{S('E3', 42, 'FLOW_I_GATE_DEFAULT')}; {S('E3F', 665, '_flowInnovGate')}; {S('E3P', 1022, '_hgtInnovGate')}; {S('E3', 312, 'FLOW_MAX')}; {S('FD', 416, 'binary accept')}]",
         f"the same values (FLOW_MAX tested two-sided, |flow| ≥ 2.5) [{S('UC', 44, 'FLOW_GATE=300, FLOW_MAX=2.5')}; "
         f"{S('UC', 45, 'RNG_GATE=500')}; {S('UK', 40, 'FLOW_GATE = 300')}]",
         f"NO flow or range NIS gate in either core; flow above 4.2 rad/s dropped; quality binary accept "
         f"[{S('FC', 184, 'abs(flow_xy[0]) < 4.2')}; {S('CC', 144, 'std::abs(flow->xy[0]) < 4.2')}; {S('M', 8659, 'no gate')}]. The design called for matched gates "
         f"[{S('FD', 446, 'matched NIS gate at factor-insertion time')}]; documented as a design deviation, not corrected (Table 3.3, exception 5)"],
        ["compute (details: Table 8.1)",
         "not measured (runs only inside ArduPilot)",
         f"offline predict 1.5–1.6 ms, forward update 0.25–0.49 ms median (DIAGNOSTIC, workstation) [{S('N', 450, 'UKF predict / forward update')}]",
         f"offline step 32.7–32.9 ms median on textured bags (DIAGNOSTIC, workstation) [{S('N', 445, 'FGO step, post-fix, baseline textured')}]"],
    ]
    check("UKF port TARGET_DT equals EKF3's EKF_TARGET_DT (s)", rd(int(grab("UK", 38, r"D\((\d+), 1000\)")) / 1000, 3),
          grab("E3H", 59, r"EKF_TARGET_DT\s+([0-9.]+)f"), "AP_NavUKF.cpp:38; AP_NavEKF3_core.h:59")
    check("flow NIS gate = (0.01 × EK3_FLOW_I_GATE)²", rd((0.01 * int(grab("E3", 42, r"FLOW_I_GATE_DEFAULT\s+(\d+)"))) ** 2, 0),
          grab("N", 147, r"NIS gate (\d+)"), "AP_NavEKF3.cpp:42; N:147")
    check("range NIS gate = (0.01 × EK3_RNG_I_GATE)²", rd((0.01 * int(grab("UC", 45, r"RNG_GATE=(\d+)"))) ** 2, 0),
          grab("N", 149, r"NIS gate (\d+)"), "UC:45; N:149")
    check("EKF3 range-height NIS gate = (0.01 × EK3_HGT_I_GATE)² (range as the height source)",
          rd((0.01 * int(grab("E3", 36, r"HGT_I_GATE_DEFAULT\s+(\d+)"))) ** 2, 0), grab("N", 149, r"NIS gate (\d+)"), "AP_NavEKF3.cpp:36; N:149")
    check("heading χ² gate of the UKF/FGO = (0.01 × 300)²", rd((0.01 * 300) ** 2, 1), grab("MM", 186, r"FWD_CHI2_GATE = ([0-9.]+)"), "MM:186")
    save_tab("Table 3.1", "methods_estimator_design", "Estimator design: EKF3, the UKF and the FGO",
             "Design of the three estimators as built (offline and in the flight software). Each cell gives its source in brackets.",
             ["", "EKF3 (fixed baseline)", "UKF", "FGO"], rows, [10, 30, 30, 30],
             [KEY_ABBR, "The FGO's missing flow/range NIS gate is a code-versus-design difference, ruled 2026-10-17 a documented design "
              "deviation (Table 3.3, exception 5); it was not corrected and nothing was re-run."], "Chapter 3 (method), estimators", fs=7.3)


# ======================================================================== Tables 3.2 and 3.3: noise parity and exceptions
def tab_fairness():
    # ---- derived: GTSAM continuous-time noise from EKF3's NSE values, σ_c = NSE·√dt, covariance = NSE²·dt, dt = 0.0125 s
    dt = 0.0125; sq = math.sqrt(dt)
    check("√dt at dt = 0.0125 s", rd(sq, 7), cell("N", 152, 1), "N:152")
    nse = {"ACC": 0.35, "GYRO": 0.015, "ABIAS": 0.02, "GBIAS": 0.001}
    # the NSE values themselves, read from EKF3's source defaults
    for k, pat in (("GYRO", r"GYRO_P_NSE_DEFAULT\s+([0-9.E+-]+)f"), ("ACC", r"ACC_P_NSE_DEFAULT\s+([0-9.E+-]+)f"),
                   ("GBIAS", r"GBIAS_P_NSE_DEFAULT\s+([0-9.E+-]+)f"), ("ABIAS", r"ABIAS_P_NSE_DEFAULT\s+([0-9.E+-]+)f")):
        ln = {"GYRO": 28, "ACC": 29, "GBIAS": 30, "ABIAS": 31}[k]
        check(f"EKF3 {k}_P_NSE default equals the value used here", rd(float(grab("E3", ln, pat)), 3), rd(nse[k], 3), f"AP_NavEKF3.cpp:{ln}")
    sup = {"⁻³": -3, "⁻⁶": -6, "⁻⁸": -8}; covs = []
    for name, k, ln, sd, mant_dp, exp, fc_ln in (("accelerometerCovariance", "ACC", 153, 8, 5, -3, 27), ("gyroscopeCovariance", "GYRO", 154, 9, 4, -6, 28),
                                                ("biasAccCovariance", "ABIAS", 155, 9, 1, -6, 29), ("biasOmegaCovariance", "GBIAS", 156, 10, 2, -8, 30)):
        sig = nse[k] * sq; cov = nse[k] ** 2 * dt
        supx = [s for s, v in sup.items() if v == exp][0]
        check(f"{name}: σ_c = NSE·√dt / covariance = NSE²·dt", f"{rd(sig, sd)} / {rd(cov / 10 ** exp, mant_dp)}×10{supx}", cell("N", ln, 1), f"N:{ln}")
        covs.append(f"{rd(cov / 10 ** exp, mant_dp)}e{exp}")
        check(f"{name} in fgo_core.py equals NSE²·dt (printed in Table 3.2)", covs[-1], grab("FC", fc_ln, r"\* ([0-9.]+e-\d)\)"), f"FC:{fc_ln}")
    check("EKF3 effective ExtNav yaw σ at the default VISO_YAW_M_NSE 0.2 rad (deg)", rd(math.degrees(0.2), 2),
          grab("M", 4756, r"\*\*Effective EKF3 yaw σ: ([0-9.]+)°"), "M:4756")
    check("VISO_YAW_M_NSE at which EKF3's 5° floor binds (rad)", rd(math.radians(5), 4), grab("M", 4757, r"`VISO_YAW_M_NSE` ≤ ([0-9.]+) rad"), "M:4757")

    rows = [
        ["flow (downward camera)", "0.25 rad/s", "0.25 rad/s", "0.25 rad/s", "offline and in flight (all builds)",
         f"EKF3 default {S('E3', 41, 'FLOW_M_NSE_DEFAULT      0.25f')}; {S('UC', 44, 'FLOW_M_NSE=0.25')}; "
         f"{S('UK', 40, 'FLOW_M_NSE = D(25, 100)')}; {S('FC', 97, 'Sigma(2, 0.25)')}; parity table {S('M', 9522, '| flow | 0.25 rad/s')}"],
        ["range (downward LiDAR)", "0.5 m", "0.5 m", "0.5 m", "offline and in flight",
         f"{S('E3', 293, 'RNG_M_NSE')}; {S('UC', 45, 'RNG_M_NSE=0.5')}; {S('UK', 41, 'RNG_M_NSE = D(5, 10)')}; {S('FC', 98, 'Sigma(1, 0.5)')}; "
         f"{S('M', 9523, '| range | 0.5 m')}"],
        ["forward heading, offline (Exp. 1B)", "none: EKF3 is the fixed no-yaw-source baseline",
         "0.148° (textured walls), 0.126° (plain walls)", "0.148° / 0.126° (the same)", "offline only",
         f"ruling {S('M', 2887, 'EKF3 is the fixed no-yaw-source baseline')}; {S('MM', 191, 'np.radians(0.148)')}; {S('MM', 192, 'np.radians(0.126)')}"],
        ["forward heading, closed loop (Exp. 1C)", "5°: ExtNav angle error floored at 5° inside EKF3 (VISO_YAW_M_NSE 0.05 rad)",
         "5° (ruled: what EKF3 applies after ArduPilot's floor)", "5°", "in flight",
         f"{S('E3M', 1118, 'MAX(angErr, radians(5.0f))')}; {S('CLH', 15, 'VISO_YAW_M_NSE 0.05')}; {S('M', 7555, 'The UKF applies the heading at **5°**')}; "
         f"{S('UK', 523, 'radians(5.0f)')}; {S('CN', 70, 'heading_sigma_deg')}; {S('M', 9526, 'heading σ (closed loop)')}"],
        ["tag position (Exp. 2, floor tags)", "0.05 m (VISO_POS_M_NSE)", "0.05 m", "0.05 m", "EKF3 live (passive); UKF/FGO offline",
         f"{S('TX', 8, 'VISO_POS_M_NSE')}; {S('MM', 356, 'TAG_SIGMA_POS = 0.05')}; {S('M', 10064, 'position σ = max(`VISO_POS_M_NSE`, posErr) = 0.05 m')}"],
        ["tag position (Exp. 5, wall tag)", "0.02 m (VISO_POS_M_NSE)", "0.02 m", "0.02 m (Python and C++ node, passed by the launcher)",
         "in flight (and the passive estimators)",
         f"{S('HX', 8, 'VISO_POS_M_NSE 0.02')}; {S('M', 10730, 'ROOM_TAG_SIGMA_POS=0.02')}; {S('RT', 423, 'tag_sigma_pos:=${TAG_SIGMA_POS:-0.02}')}; "
         f"{S('RT', 449, 'tag_sigma_pos_m:=${TAG_SIGMA_POS:-0.02}')}"],
        ["tag yaw (Exp. 2 and 5)", "5° (EKF3's floor)", "5°", "5°", "as above",
         f"{S('MM', 355, 'max(VISO_YAW_M_NSE 0.05 rad, angErr, 5 deg) = 5 deg')}; {S('HX', 9, 'VISO_YAW_M_NSE 0.05')}; {S('CN', 66, 'tag_sigma_yaw_deg')}"],
        ["GNSS (Exp. 4, outdoors only)", "0.5 m, 0.3 m/s (EKF3's effective noise)", "0.5 m, 0.3 m/s, the samples EKF3 received", "0.5 m, 0.3 m/s (the same)",
         "EKF3 live (passive); UKF/FGO offline", f"{S('M', 10336, 'σ 0.5 m, 0.3 m/s')}; {S('M', 10335, 'the samples EKF3 received')}"],
        ["yaw cap pseudo-measurement", "0.5 rad", "0.5 rad", "0.5 rad", "offline and in flight",
         f"{S('M', 9527, 'zero-innovation yaw pseudo-measurement')}; {S('UC', 46, 'YAW_M_NSE=max(0.5, 0.05)')}; {S('FC', 99, 'Sigma(1, 0.5)')}"],
        ["IMU process noise (gyro / accel / gyro-bias / accel-bias)",
         "GYRO_P_NSE 0.015 rad/s, ACC_P_NSE 0.35 m/s², GBIAS_P_NSE 0.001 rad/s², ABIAS_P_NSE 0.02 m/s³ (defaults), at its 12.5 ms step",
         "the same NSE values; offline per-step terms scaled by DT_REF/dt to the same per-second densities (ruled)",
         f"σ_c = NSE·√dt at dt {rd(float(Decimal(str(dt)).scaleb(3)), 1)} ms: covariances {', '.join(covs)} (same densities)",
         "offline and in flight",
         f"{S('E3', 28, 'GYRO_P_NSE_DEFAULT')}-31; {S('UC', 21, 'DT_REF = 0.0125')}; {S('M', 9567, 'D27 RULED')}; {S('FC', 27, '1.53125e-3')}-30; "
         f"{S('N', 151, 'GTSAM conversion rule')}; {S('CC', 39, 'setAccelerometerCovariance')}"],
        ["IMU input samples", "the FC's 1000 Hz delta angles and velocities", "offline: 333 Hz HIGHRES_IMU instantaneous samples "
         "(rectangular integration); port: the FC's DAL frames, as EKF3", "333 Hz HIGHRES_IMU samples (node and offline)",
         "interface limitation", f"{S('CL', 724, 'Standing caveat for all three estimators')}; {S('UKH', 14, 'Inputs (the same ones EKF3 uses)')}"],
        ["initial uncertainty", "yaw 0.1 rad (EKF3 design)", "yaw 1°, roll/pitch 5°", "yaw 1°, roll/pitch 5° (corrected priors); "
         "every flown FGO hold and corridor flight used the original 1e-3 rad / 2°", "offline: corrected; flight: see the FGO cell",
         f"{S('M', 12862, "EKF3's 0.1 rad is recorded as EKF3's design")}; {S('UC', 321, 'np.radians(5)**2, np.radians(5)**2, np.radians(1)**2')}; {S('FC', 44, 'YAW0_SIGMA = np.radians(1)')}; "
         f"{S('FC', 48, 'ROLLPITCH0_SIGMA = np.radians(5)')}; {S('N', 37, 'used the OLD priors')}"],
    ]
    save_tab("Table 3.2", "methods_noise_parity", "Noise parity: measurement and process noise per sensor and estimator",
             "The measurement noise each estimator applies, offline and in flight. Values come from the parameter files, the code "
             "constants and METHODOLOGY; the source column gives each. Where the estimators differ the difference is listed, with its "
             "ruling, in Table 3.3.",
             ["sensor / quantity", "EKF3", "UKF", "FGO", "context", "source"], rows, [14, 19, 17, 18, 11, 31],
             [KEY_ABBR, "The FGO's GTSAM conversion and the per-step terms are derived in the generator from EKF3's NSE defaults and "
              "EXACT-cross-checked against numbers.md and fgo_core.py (index_methods.md)."], "Chapter 3 (method), fairness", fs=7.0)

    # ---- Table 3.3: documented exceptions with their rulings
    # Row 5's gating-count addendum (D134/D137/D148): values read and EXACT-checked against the diagnostic's own
    # numbers file before the row text is built, so the printed sentence always carries the checked string.
    _gc_joint = re.search(r"\(([\d.]+%)\)", cell("FGN", 13, 6)).group(1)       # textured joint, chi2(2)=11.83
    _gc_one = re.search(r"\(([\d.]+%)\)", cell("FGN", 13, 7)).group(1)        # textured FLOW_MAX one-sided
    _gc_two = re.search(r"\(([\d.]+%)\)", cell("FGN", 13, 8)).group(1)        # textured FLOW_MAX two-sided
    _gc_chi2 = grab("FGN", 11, r"chi2\(2\)=([\d.]+)")
    ex = [
        ["1", "flow/range fusion rate", "EKF3 fuses flow at 15.1 Hz and range at 16 Hz; the UKF and FGO at 30 Hz with the same σ",
         "recorded as EKF3 design (design features are not copied); results state that the UKF and FGO fuse ~2× the information per second",
         f"{S('M', 12338, 'EKF3 fuses flow at 15.1 Hz')}; ruling {S('M', 12359, '15 Hz flow fusion is recorded as EKF3 design')}"],
        ["2", "forward heading offline (1B)", "only the UKF and FGO receive the camera heading; EKF3 none",
         "EKF3 is the fixed no-yaw-source baseline for the registered Phase 4 comparison (VISO_YAW_M_NSE floor; LOG_REPLAY=0). "
         "REOPENED (D131/D132): EKF3 + camera heading is now also evaluated offline via ArduPilot Replay, as a separate, descriptive arm; "
         "every value carries EKF3's own unconditional 5° angErr floor, and the matched 5° UKF/FGO arm is a separate run from the stored "
         "0.148°/0.126° heading-sigma arms. The existing Phase 4 (1B) results above are unchanged",
         f"ruling {S('M', 2884, 'RULING — EKF3 in the offline forward-camera comparison')}-2888; reopened {S('DL', 157, 'REOPENED')}, {S('DL', 158, 'REOPENED')}"],
        ["3", "closed-loop heading σ (1C)", "all three at 5°; the camera's own σ (0.148°) is not usable by EKF3",
         "5° is ArduPilot's floor (VISO_YAW_M_NSE 0.05); ruled that the UKF port applies the same 5°",
         f"{S('M', 4896, 'VISO_YAW_M_NSE = 0.05')}; ruling {S('M', 7553, 'Ruling D17')}"],
        ["4", "GTSAM integrationCovariance", "FGO only, 1e-8 (no EKF3 counterpart)",
         "documented asymmetry (a conditioning floor); no separate ruling found", f"{S('M', 9528, 'documented asymmetry')}; {S('FC', 31, 'setIntegrationCovariance')}"],
        ["5", "FGO flow/range gating (design deviation)", "EKF3 gates flow per axis at 3σ (FLOW_I_GATE 300) and range height at 5σ (HGT_I_GATE 500, range as the height source); the UKF gates both at 3σ / 5σ; NEITHER FGO core gates flow or range innovations (only a 4.2 rad/s flow clamp)",
         "DESIGN DEVIATION, documented, not corrected or re-run (results frozen); it leaves the FGO less defended, not more. The design called for matched gates. "
         f"A read-only gating-count diagnostic found that {_gc_joint} of textured flow factors would have been rejected by the joint test (chi2(2)={_gc_chi2} gate, against the stored, ungated FGO's own trajectory), and that the FLOW_MAX one-sided ({_gc_one}) and two-sided ({_gc_two}) counts are identical on the textured dsn_* bags; transition and blank are not read as a direct measure (both are in numbers.md's own diverging/† category, where an inflated predictive covariance confounds a low rejection count with a well-fit sensor)",
         f"EKF3 {S('E3F', 665, '_flowInnovGate')}, {S('E3P', 1022, '_hgtInnovGate')}; UKF {S('UC', 295, "p['FLOW_GATE']")}, {S('UC', 231, "p['RNG_GATE']")}; "
         f"FGO {S('FC', 184, '< 4.2')}, {S('CC', 144, 'std::abs(flow->xy[0]) < 4.2')}; design {S('FD', 446, 'matched NIS gate')}; ruling {S('M', 14302, 'FGO gating documented')}; "
         f"gating count (D134, D137, D148): {S('FGN', 11, 'chi2(2)=11.83') and S('FGN', 13, '0.01%') and ALIAS['FGN'][1] + ':11, 13'}"],
        ["6", "FLOW_MAX sidedness", "the UKF rejects |flow| ≥ 2.5 rad/s on either axis (two-sided); EKF3's fusion test is signed (flow < 2.5 rad/s per axis, one-sided)",
         "NO RULING FOUND; at 0.5 m/s and 2 m the flow is ~0.25 rad/s, far from the limit. Now counted, read-only (row 5): the one-sided and "
         "two-sided counts are identical in every run-set-1A/1B group, with no exception (0/0 in every set-1A group; 0/0 in every set-1B group "
         "except one, which reads 1/1 on a single extreme sample), so sidedness does not change the count on this data",
         f"{S('UC', 293, "abs(flow_xy[0]) >= p['FLOW_MAX']")}; {S('UK', 874, 'fabs(e.fr.x) < FLOW_MAX')}; EKF3 {S('E3F', 668, 'flowRadXY.x < frontend->_maxFlowRate')}; "
         f"gating count {S('FGR', 254, 'IDENTICAL in every single group, with no exception')}"],
        ["7", "ground-proximity flow rule", "EKF3's rule (flow zeroed and still fused below 0.5 m before take-off) applied to the UKF and FGO",
         "a sensor-validity rule, shared (not tuning)", f"ruling {S('M', 7038, 'Ruling D15')}; {S('M', 7060, 'This is a sensor-model')}"],
        ["8", "EKF3's pre-arm yaw-bias learning", "EKF3 learns gyro-z bias on the ground; not given to the UKF or FGO",
         "principle: sensor-validity rules are shared, design features are not copied; a caveat on the no-heading closed loop only",
         f"{S('M', 7785, 'D18: no. PRINCIPLE')}-7792; {S('PR', 47, 'D18 principle recorded')}"],
        ["9", "EKF3 range median-of-3, tilt cut, floor", "EKF3 only", "EKF3 design, not copied", f"{S('M', 8871, 'Under D18 they are not copied')}"],
        ["10", "UKF offline predict period and process noise", "offline UKF steps 15.00 ms; its process noise is scaled to EKF3's per-second densities",
         "ruled: same per-second densities as the FGO and the UKF port", f"{S('M', 9567, 'D27 RULED')}; {S('N', 186, 'UKF predict dt')}"],
        ["11", "FGO initial uncertainty", "corrected to yaw 1°, roll/pitch 5° (the UKF's); the ORIGINAL flown FGO corridor and hold results "
         "used 1e-3 rad / 2° (now superseded: original priors); a re-fly on the corrected priors is the current FGO corridor (H1.8) and "
         "hold row; EKF3 keeps 0.1 rad",
         "a model correction (the initial-uncertainty correction); EKF3's 0.1 rad is its design",
         f"ruling {S('M', 12857, 'FGO initial yaw sigma, a MODEL CORRECTION under D18')}-12862; {S('N', 36, 'Flown FGO results')}; "
         f"re-fly {S('DL', 153, 'corrected priors')}"],
        ["12", "FGO biasAccOmegaInt", "was diag(0.2², 0.043633²): extra IMU white noise (gyro ~26×, accel ~5× looser); set to 0",
         "a model correction (a sensor-noise error)", f"ruling {S('M', 12046, 'setBiasAccOmegaInit')}; {S('M', 12052, 'gyro ~26×, accelerometer ~5× looser')}; "
         f"{S('FC', 35, 'setBiasAccOmegaInit(np.zeros((6, 6)))')}"],
        ["13", "UKF Cholesky jitter", "both builds added 1e-12·I to P before every Cholesky; now jitter is added only if the factorisation fails "
         "(ladder 0, 1e-12, 1e-9, 1e-6)", "a model correction",
         f"{S('M', 12329, 'Both builds add 1e-12·I to P before the Cholesky')}; ruling {S('M', 12343, 'UKF jitter: a MODEL CORRECTION under D18')}; "
         f"{S('UC', 57, 'CHOL_JITTER_LADDER = (0.0, 1e-12, 1e-9, 1e-6)')}"],
        ["14", "UKF flow derotation", "the UKF derotates flow with the bias-corrected rate", "a model correction, not a copied design feature",
         f"ruling {S('M', 11366, 'bias-corrected rate is ADOPTED as a MODEL CORRECTION')}"],
        ["15", "lateral optical-flow sign", "the lateral flow sign was wrong in EKF3's input and in the UKF/FGO model; fixed for all",
         "a finding, fixed in every estimator before the consolidated re-run",
         f"{S('M', 4069, 'lateral optical-flow sign is wrong')}; {S('M', 4155, 'Lateral flow sign — rulings, fix and verification')}; {S('N', 213, 'sign fix')}"],
        ["16", "flow validity", "every estimator accepts flow on the same binary validity flag (feature count), no R-scaling",
         "ruled: flow validity uses the feature count only", f"{S('M', 8936, 'flow validity uses the feature count only')}; {S('FD', 424, 'No continuous R-scaling')}"],
        ["17", "IMU gap rule", "replays of the UKF and FGO start after / exclude IMU gaps; EKF3 (live) is still scored",
         "ruling (2026-09-24), extended", f"{S('M', 1985, 'RULE — IMU gaps and the replay estimators')}; {S('M', 2487, 'IMU timing rule EXTENDED')}"],
        ["18", "tag-fix gating (Exp. 2–5)", "EKF3 gates tag fixes (position 5σ, yaw 3σ, bypassed after a 10 s timeout); the UKF and FGO do not gate them",
         "pre-registered; validity is the shared tag rule (a sensor-validity rule)",
         f"{S('M', 10066, 'Gates: position 5σ, yaw 3σ')}; {S('M', 10134, 'No gate')}; {S('M', 11613, 'applied IDENTICALLY to EKF3, the UKF and the FGO')}"],
        ["19", "GNSS on return (Exp. 4)", "the UKF and FGO fuse the GNSS samples EKF3 received, ungated, and on return simply resume "
         "(no reset or variance inflation); EKF3 behaves by its own design", "EKF3 design, not copied; no gate, as in Exp. 2",
         f"{S('M', 10336, '**No gate**')}; {S('M', 10337, 'No reset or variance inflation on return')}"],
        ["20", "FGO: no yaw reset at the first heading", "the FGO fuses the first heading with no reset", "design feature, not copied",
         f"{S('M', 8043, 'not copied, per D18')}"],
        ["21", "robust heading weighting", "Cauchy kernel, k = 2.385, in the robust FGO only (H1.4, H1.7)", "calibrated on the calibration bags, as pre-registered",
         f"{S('M', 8281, 'Cauchy, k = 2.385 chosen')}"],
        ["22", "drift band per estimator (H5.5)", "the UKF's band is 2× the others'", "pre-registered", f"{S('M', 10691, 'UKF:** ≤ 2× those')}"],
        ["23", "EKF3 tag-fix delay (Exp. 2)", "EKF3 fuses ExternalNav tag fixes with VISO_DELAY_MS 15 ms, up to 12 ms short of the measured "
         "minimum latency (17.5–26.6 ms), for both position and yaw; the UKF and FGO replay /tags/sent at the capture stamp and are not affected",
         "ruled deviation from the latency rule, kept with no re-fly; bounded at ≤ 6 mm per fix at 0.5 m/s, ≤ 22 mm at the measured "
         "1.80 m/s corner maximum, ≤ 0.06° in yaw",
         f"ruling (user, 2026-10-08) {S('M', 10509, 'RULING (user, 2026-10-08): T `VISO_DELAY_MS` stays 15 ms, no re-fly')}; "
         f"{S('M', 10512, 'VISP receipt − capture was **17.5–26.6 ms**, so 15 ms is up to **12 ms short**')}; "
         f"{S('M', 10514, 'the ExternalNav delay applies to **both** position and yaw fusion')}; "
         f"{S('M', 10528, 'The UKF and FGO replay `/tags/sent` at the capture stamp and are not affected at all')}; "
         f"{S('N', 542, 'the per-fix bound is ≤ 6 mm nominal, ≤ 22 mm at the measured 1.80 m/s')}; {S('N', 543, '≤ 0.06° in yaw')}"],
    ]
    # Row 23's numbers, EXACT against the cited lines (methodology and the frozen numbers file).
    check("Table 3.3 row 23: measured minimum latency (ms)", "17.5–26.6", grab("M", 10512, r"\*\*([\d.]+–[\d.]+) ms\*\*"), "M:10512")
    check("Table 3.3 row 23: shortfall (ms)", "12", grab("M", 10512, r"up to \*\*(\d+) ms short"), "M:10512")
    check("Table 3.3 row 23: nominal bound (mm)", "6", grab("N", 542, r"≤ (\d+) mm nominal"), "N:542")
    check("Table 3.3 row 23: corner bound (mm)", "22", grab("N", 542, r"≤ (\d+) mm at the measured"), "N:542")
    check("Table 3.3 row 23: corner speed (m/s)", "1.80", grab("N", 542, r"measured ([\d.]+) m/s"), "N:542")
    check("Table 3.3 row 23: yaw bound (deg)", "0.06", grab("N", 543, r"≤ ([\d.]+)° in yaw"), "N:543")
    check("Table 3.3 row 23: nominal speed (m/s)", "0.5", grab("M", 10517, r"12 ms × ([\d.]+) m/s"), "M:10517")
    # Row 5's gating-count addendum, EXACT against the diagnostic's own numbers file (D134/D137/D148).
    check("Table 3.3 row 5: gating count, textured joint flow-rejection rate (chi2(2)=11.83)", "0.01%", _gc_joint, "FGN:13")
    check("Table 3.3 row 5: gating count, textured FLOW_MAX one-sided rate", "0.00%", _gc_one, "FGN:13")
    check("Table 3.3 row 5: gating count, textured FLOW_MAX two-sided rate", "0.00%", _gc_two, "FGN:13")
    check("Table 3.3 row 5: gating count, FLOW_MAX one-sided == two-sided (textured)", _gc_one, _gc_two, "FGN:13")
    check("Table 3.3 row 5: gating count, joint chi2(2) threshold", "11.83", _gc_chi2, "FGN:11")
    save_tab("Table 3.3", "methods_noise_exceptions", "Documented exceptions to noise and treatment parity, with their rulings",
             "Every documented place where the noise or the treatment differs between estimators, with the ruling that covers it. "
             "Two code differences (5, 6) have no ruling in the record and are reported, not resolved.",
             ["#", "item", "difference", "ruling / status", "source"], ex, [3, 15, 33, 25, 30],
             [KEY_ABBR, "Ruling numbers (D-numbers) appear only in the source column, beside their METHODOLOGY lines; the cells describe "
              "each ruling in words (vocabulary §8.2)."], "Chapter 3 (method), fairness", fs=7.0)


# ======================================================================== Table 3.4: experiment matrix
def tab_matrix():
    n1a = 3 * 3; n1b_bags = 2 * 3 * 3; n1b_rep = (9 * 3 + 9 * 2) * 2; n_f4 = 6 * 2; n_t = 4 * 3
    check("1B validation bags: 2 wall conditions × 3 floors × 3 repeats", str(n1b_bags), grab("M", 2706, r"the (\d+) dataset bags"), "M:2706")
    check("1B offline fusion replays: (9 textured-wall bags × 3 arms + 9 plain-wall bags × 2 arms) × 2 estimators",
          str(n1b_rep), grab("M", 2970, r"giving (\d+) replay runs"), "M:2970")
    check("1B robust-weighting replication: 6 flights × 2 worlds", str(n_f4), grab("M", 9706, r"\((\d+) flights\)"), "M:9706")
    check("Exp. 2: 4 tag conditions × 3 repeats", str(n_t), grab("M", 10123, r": (\d+) flights"), "M:10123")
    rows = [
        ["1A standard-sensor comparison", "corridor, textured / blank / transition floor", "IMU, downward flow, LiDAR; no yaw source",
         "EKF3 live but passive (truth flying); UKF, FGO replayed offline", "open",
         f"{n1a} flights (3 floors × 3 repeats) + 7 confirmatory textured repeats; unit: flight", "cruise ATE (textured); behaviour after flow loss (blank, transition)",
         "H1.1", f"{S('V', 41, '**1A**')}; {S('M', 865, '3 corridor worlds × 3 repeats')}; {S('M', 5640, '7 new repeats')}; {S('M', 2874, 'flown on simulator truth')}; {S('V', 148, 'H1.1')}"],
        ["1B camera-heading studies: measurement validation", "corridor with ceiling; textured or plain walls × 3 floors",
         "forward camera (heading, yaw rate)", "none (measurement only)", "open",
         f"6 calibration flights + {n1b_bags} dataset bags; unit: flight", "heading accuracy per bag; dataset-quality bands", "H1.2",
         f"{S('M', 2692, 'the six `p1c_*` check flights only')}; {S('M', 2706, 'the 18 dataset bags')}; {S('V', 149, 'H1.2')}"],
        ["1B: offline fusion", f"the same {n1b_bags} bags", "IMU, flow, LiDAR + forward heading (and yaw rate on textured walls)",
         "UKF and FGO offline, each with and without the heading; EKF3 the no-heading reference", "open",
         f"0 new flights; {n1b_rep} replays (bag × arm × estimator)", "cruise ATE; heading-error decomposition of sideways drift", "H1.3, C1.a",
         f"{S('M', 2958, 'EKF3 is the fixed no-yaw-source baseline')}; {S('M', 2970, '90 replay runs')}; {S('V', 150, 'H1.3')}; {S('V', 152, 'C1.a')}"],
        ["1B: offline tests (robust weighting, hindsight, large initial error)", "the textured- and plain-wall textured-floor bags",
         "as 1B offline fusion", "UKF and FGO offline (H1.5 adds the FGO whole-flight batch); EKF3 excluded", "open",
         "0 new flights; 6 bags (H1.4), 3 bags (H1.5, H1.6–H1.6c, × initial-error values)", "lockouts and yaw-error maximum; off-interval yaw RMS; convergence time",
         "H1.4, X1.b, H1.5, H1.6, H1.6b, H1.6c", f"{S('M', 7880, 'existing recordings only')}; {S('M', 7922, '≥ 4 of 6')}; {S('M', 7956, 'only the UKF and FGO are compared')}; {S('V', 153, 'H1.4')}-158"],
        ["1B: robust-weighting replication", "corridor with ceiling, textured floor; plain and textured walls", "as 1B offline fusion",
         "UKF hard-gated, FGO hard-gated, FGO robust (offline); truth flying", "open", f"{n_f4} new flights (6 × 2 worlds); unit: flight",
         "yaw-error maximum (primary); wrong headings accepted; cross-track", "H1.7a–c",
         f"{S('M', 9706, 'n = 6 per world (12 flights)')}; {S('F4C', 1, 'truth flies')}; {S('V', 159, 'H1.7a')}-161"],
        ["1C closed-loop corridor flights", "corridor with ceiling, textured floor, textured walls; full and half real-time (RTF 0.5)",
         "IMU, flow, LiDAR; + live camera heading (with heading)", "each estimator flies in turn (EKF3, UKF port, FGO node); FGO at half real-time only",
         "closed", "per estimator and build: 1 flight without heading + 3 with heading; unit: flight",
         "without heading: wall-contact time in the contact window; with heading: the five closed-loop criteria (+ estimator validity)", "H1.8, H1.9",
         f"{S('V', 41, '**1C**')}; {S('N', 464, 'n = 1 per no-heading cell')}; {S('M', 7795, 'All FGO closed-loop flights fly at half')}; {S('V', 162, 'H1.8')}; {S('V', 163, 'H1.9')}"],
        ["2 known tags", "room with floor tags (10 × 10 m)", "IMU, flow, LiDAR + floor AprilTags (known positions)",
         "EKF3 live, passive (truth flying); UKF, FGO offline; hindsight: FGO batch, smoothed UKF", "open",
         f"{n_t} flights (4 tag conditions × 3 repeats); unit: flight (5 laps each)", "horizontal RMSE over the laps; hindsight gain per gap", "H2.1–H2.4",
         f"{S('M', 10107, '10 × 10 m room')}; {S('M', 10123, '12 flights')}; {S('M', 10114, 'EKF3 receives it live')}; {S('V', 170, 'H2.1')}-173"],
        ["3 loop closure", "room with floor tags (Exp. 2's condition-A flights)", "IMU, flow, LiDAR + tags at unknown positions",
         "keyframe FGO only, replayed offline on Exp. 2 flights, with and without loop closure", "open",
         "0 new flights; 3 flights × 2 modes; validation on one corridor flight", "per-lap horizontal RMSE (live and hindsight)", "V3, H3.1–H3.4",
         f"{S('M', 10493, 'L uses T_A_r1, T_A_r2 and T_A_r3')}; {S('M', 10456, '**FGO capability**')}; {S('V', 179, 'V3')}-183"],
        ["4 outdoor–indoor", "outdoor–indoor world (GNSS outside only)", "IMU, flow, LiDAR; GNSS outdoors only",
         "EKF3 live, passive (truth flying); UKF, FGO offline with the same GNSS samples; hindsight tracks", "open",
         "3 flights (one re-flown unchanged); unit: flight", "indoor horizontal RMSE; jump on GNSS return", "H4.1–H4.3",
         f"{S('M', 10301, 'open loop on simulator truth')}; {S('M', 10310, 'Three repeats.')}; {S('OG', 2, 'AHRS_EKF_TYPE 10')}; {S('V', 189, 'H4.1')}-191"],
        ["5 tag hold", "room with a wall tag (near and far spawn)", "IMU, flow, LiDAR + wall AprilTag (forward camera)",
         "EKF3 flies (UKF, FGO passive); then the UKF port flies; then the FGO node flies", "closed",
         "3 flights per hold set; primary sets: EKF3-flying (far spawn), UKF-flying (final build), FGO-flying (final build); also an EKF3-flying "
         "near-spawn set and earlier/ablation-build sets (×3 each), and 1 characterisation + 1 check flight; unit: flight",
         "hold error (mean, max); drift during tag loss; re-lock; jump; smoothness", "H5.1–H5.7",
         f"{S('M', 10661, 'EKF3 flies')}; {S('THD', 141, 'Repeats: 3 per stage and estimator')}; {S('N', 635, '×3 each')}; {S('N', 649, 'are PRIMARY')};{S('V', 197, 'H5.1')}-204"],
        ["5S safety tests", "room with a wall tag (far spawn), 2 m-clearance hold", "as Exp. 5; failure injected (forced-invalid, node-kill)",
         "the UKF port or the FGO node flies; EKF3 one reference run (no criteria)", "closed",
         "4 tests (UKF / FGO × forced-invalid / node-kill), final run of each; unit: test run", "attitude criterion, position-lost declaration, safe landing, single landing",
         "none (criteria only)", f"{S('M', 11286, 'Option (i) safety tests')}; {S('N', 490, 'Safety tests (H config, 2 m-clearance hold)')}; {S('V', 58, 'They therefore carry criteria (S-A1–S-A4)')}"],
    ]
    save_tab("Table 3.4", "methods_experiment_matrix", "Experiment matrix",
             "Every experiment in the thesis numbering, with its worlds, sensors, estimators and their roles, loop, number of flights "
             "(with the unit), primary metric and hypothesis labels. Real-flight readiness is not an experiment and has no row "
             "(vocabulary §1, decision 3).",
             ["experiment", "world(s)", "sensors", "estimators and roles", "loop", "n (unit)", "primary metric", "hypotheses", "source"],
             rows, [13, 12, 12, 16, 5, 15, 14, 8, 22],
             [KEY_ABBR, "'Truth flying' = AHRS_EKF_TYPE 10: the simulator's state flies the vehicle, so the path does not depend on "
              "any estimator; EKF3 then runs live but passively (vocabulary term 39). Not given an H label: the robust closed-loop set "
              "(×3, half real-time (RTF 0.5), descriptive) and the static yaw sweep. Half real-time (RTF 0.5): the simulator ran at half real time; the commanded flight speed was unchanged at 0.5 m/s. H5.2–H5.4 have only "
              "tag_hold_design.md as their source (no METHODOLOGY pre-registration line)."], "Chapter 3 (method), experiments", fs=6.6)


# ======================================================================== Table 8.1: compute and deployability
def tab_compute():
    m_free = [int(x.replace(",", "")) for x in re.findall(r"([\d,]+) B", _lines("M")[13567 - 1])[:2]]
    p_free = [int(x.replace(",", "")) for x in re.findall(r"([\d,]+) B", _lines("M")[13568 - 1])[:2]]
    fl_m = "+" + rd((m_free[0] - m_free[1]) / 1000, 1) + " kB"; fl_p = "+" + rd((p_free[0] - p_free[1]) / 1000, 1) + " kB"
    kf, kf_half = rd(1000 / 30, 1), rd(1000 / 30 / 0.5, 1)
    check("MatekH743 flash added = free without − free with (kB, 1000 B)", fl_m, cell("M", 13567, 3), "M:13567")
    check("Pixhawk6X flash added (kB)", fl_p, cell("M", 13568, 3), "M:13568")
    check("wall time per keyframe at RTF 0.5 = (1/30 s)/0.5 (ms)", kf_half, grab("M", 7779, r"\(([0-9.]+) ms wall per keyframe"), "M:7779")
    check("keyframe period 1/30 s (ms)", kf, grab("M", 7772, r"against the ([0-9.]+) ms keyframe period"), "M:7772")
    rows = [
        ["offline step time (DIAGNOSTIC, workstation Python)",
         "not measured: EKF3 runs only inside ArduPilot",
         f"predict 1.5–1.6 ms median (p95 ≤ 2.1 ms); forward update 0.25–0.49 ms [{S('N', 450, 'UKF predict / forward update')}; "
         f"{S('M', 3329, 'p95 ≤ 2.1 ms')}]",
         f"32.7–32.9 ms median / 37–38 ms p95 (textured; 6 jobs in parallel); transition 17–18; blank 4.5 ms; against a 33 ms budget "
         f"[{S('N', 445, 'FGO step, post-fix, baseline textured')}; {S('N', 448, 'transition baseline')}; {S('N', 449, 'blank baseline')}; {S('N', 209, 'FGO deployability budget')}]"],
        ["C++ FGO node on the workstation (DIAGNOSTIC)", "—", "—",
         f"replay median / p99: 0.53 / 0.92 ms (standard-sensor bag), 0.91 / 1.68 ms (with heading) [{S('CPPR', 66, '0.53 / 0.92 ms')}; {S('CPPR', 67, '0.91 / 1.68 ms')}]"],
        ["flight-controller flash (MEASURED, board build, two H743 boards)",
         "not measured separately (part of stock firmware)",
         f"UKF port 13.7 kB (from symbol sizes)",
         f"FGO interface 4.6 kB (from symbol sizes). UKF + FGO + 5.8 kB shared plumbing: {fl_m} (MatekH743), {fl_p} (Pixhawk6X) "
         f"[{S('M', 13567, '| MatekH743 |')}; {S('M', 13568, '| Pixhawk6X |')}; {S('M', 13570, 'UKF 13.7 kB flash')}; {S('BFW', 58, '5.8 kB of shared plumbing')}]"],
        ["flight-controller static RAM (MEASURED)", "not measured separately", "~25 kB", f"~14.8 kB; together +40.3 kB; no heap [{S('M', 13570, 'FGO 4.6 kB / ~14.8 kB')}]"],
        ["flight-controller CPU", "not measured", f"ESTIMATED 2–6 % at 80 Hz (a bench PM log would give the real figure) [{S('M', 13571, 'CPU ESTIMATED 2–6%')}]",
         f"not estimated (only: the output predictor replays up to ~100 buffered IMU steps per state at ~10 Hz, an estimate) "
         f"[{S('BFP', 161, 'replays up to about 100 buffered IMU steps per state')}]"],
        ["companion computer (Pi), C++ FGO node", "—", "—",
         f"ESTIMATED p99 ~3.4 ms (Pi 5), ~8.7 ms (Pi 4) against the 33 ms keyframe; worst spike ~25 ms (Pi 5), ~58–67 ms (Pi 4); a Pi 5 is "
         f"recommended. qemu timing relative only; memory 43–52 MB qemu peak (upper bound) [{S('M', 13651, 'Pi timing, ESTIMATED')}-13653; "
         f"{S('M', 13674, 'A Pi 5 is RECOMMENDED')}; {S('M', 13655, '43–52 MB qemu peak')}]"],
        ["closed-loop real-time factor (Exp. 1C)", f"flew at full real time and at half real-time [{S('N', 470, 'EKF3 full / half')}]",
         f"flew at full real time (old UKF) and at half real-time (final port) [{S('N', 471, 'UKF full (old UKF, jitter) / half')}]",
         f"half real-time (RTF 0.5): at full speed the Python node's step (42–49 ms median) exceeded the {kf} ms keyframe period around "
         f"lift-off; at half real-time (RTF 0.5) it has {kf_half} ms of wall time per keyframe. The flights show its behaviour given sufficient compute, "
         f"not real-time feasibility "
         f"[{S('M', 7771, 'the FGO step is 42–49 ms')}; {S('M', 7795, 'All FGO closed-loop flights fly at half')}; {S('M', 7803, 'given sufficient compute')}; "
         f"{S('HALF', 44, '<real_time_factor>0.5</real_time_factor>')}]"],
    ]
    save_tab("Table 8.1", "realflight_compute", "Compute and deployability per estimator",
             "Offline step time, flight-controller cost and companion-computer timing, each labelled as its source labels it: "
             "MEASURED (board build), ESTIMATED, or DIAGNOSTIC (workstation timing, which says nothing directly about onboard feasibility).",
             ["quantity", "EKF3", "UKF", "FGO"], rows, [16, 18, 26, 40],
             [KEY_ABBR, "Half real-time (RTF 0.5): the simulator ran at half real time; the commanded flight speed was unchanged at 0.5 m/s. "
              "Nothing was flashed to a board; the flash and RAM figures are from the compiled images. The real-flight "
              "readiness notes (docs/real_flight_readiness.md) carry older Pi and CPU figures; METHODOLOGY's are used here."],
             "Chapter 8 (towards real flights); the offline row may also sit in Chapter 3", fs=7.3)


# ======================================================================== Table 8.2: safety findings
def tab_safety():
    rows = [
        ["Land detector does not trip (code F2)", "on flow-only EKF3 the land detector sometimes did not trip; once the vehicle tipped over ~9 s after touchdown",
         "SITL watcher bench; cause traced to the pre-arm velocity runaway (F8)", "the pilot disarms after any automatic LAND (card); M3 tightens it to 2 s",
         "procedural; not tested as a mitigation", f"{S('M', 13609, 'tipped over')}; {S('F8H', 21, 'It follows from F8')}; {S('M', 14014, 'the pilot disarms within 2 s')}"],
        ["LAND retry could override the pilot (F6)", "the watcher re-sent LAND every 0.3 s until acknowledged, which could override a pilot in ALT_HOLD",
         "SITL bench: 7/12 commands needed a second send", "LAND re-sent only while the FC still shows its pre-LAND mode; stops on ACK, any pilot mode or 5 sends",
         "BUILT; TESTED IN SITL (bench re-run: one LAND each, PASS)", f"{S('M', 13607, 'LAND retry (every 0.3 s')}; {S('M', 13820, 'LAND is re-sent only while')}; {S('M', 13876, 'each sent exactly ONE LAND')}"],
        ["Arming allowed with a large yaw error (F7)", "arming was allowed with a 22° yaw error", "SITL bench (a harness carry); the link to the fly-away is inferred",
         "watcher arming check: the FC yaw must agree with the mocap heading within 5° for ≥ 1 s; plus a card step",
         "BUILT; TESTED IN SITL (all PASS); one full-bench case failed as worded (M2 reacting to a teleport); hardware test pending",
         f"{S('M', 13886, 'arming is allowed with a 22')}; ruling {S('M', 13893, 'F7:')}; {S('M', 13936, 'SITL-bench PASSED')}; {S('M', 13938, 'must agree with the mocap heading')}; {S('M', 14102, 'F7-a:')}"],
        ["EKF3 velocity runaway on the ground (F8)", "stock EKF3 logic: the velocity runs away before arming; 5/46 arms, all re-arms after a landing in the same boot",
         "stored SITL bench logs (bounded investigation); trigger and size partly SITL", "M1–M3 (rows below)",
         "risk LOW on the first arm of a boot, MODERATE on a re-arm", f"{S('M', 13909, 'CONFIRMED, stock EKF3 logic')}; {S('M', 13919, '5/46 arms')}; {S('M', 13927, 'LOW on the first arm')}"],
        ["No EKF origin: the stock EKF failsafe never runs (B8a)", "without an origin EKF3 reports (0, 0) after aiding loss and the stock EKF failsafe returns at once",
         "SITL bench B8a (harness fault); repeated with the origin set: LAND 1.94 s after the last flow, 1.67 m", "EKF origin set and VERIFIED on every real flight (card + parameters)",
         "procedure TESTED IN SITL; on hardware a card step", f"{S('M', 13834, 'B8a verdict')}; {S('M', 13841, 'Without an origin, the stock EKF failsafe never runs')}; "
         f"{S('M', 13874, 'LAND (EKF_FAILSAFE) 1.94 s')}; ruling {S('M', 13892, 'EKF origin')}"],
        ["FC refusal gap after the watcher withdraws", "the FC refuses arming only ~3.3–3.6 s after the watcher withdraws (FS_GCS_TIMEOUT); a manual re-arm inside it is stopped only by M1 and the card",
         "SITL bench (observed in a void attempt)", "flight card: no re-arm within 10 s of any disarm", "procedural; not re-tested",
         f"{S('M', 14116, 'the FC refuses only ~3.3 s')}; {S('M', 14161, 'SAFETY OBSERVATION (void attempt 4)')}; {S('M', 14162, 'The FC-side gap is ~3.3–3.6 s')}; {S('M', 14134, 'NO RE-ARM WITHIN 10 s')}"],
        ["Flight script would command LAND over a pilot takeover (H10)", "fly_trial.py would command LAND after a pilot takeover; the bench passed only because its driver had a guard",
         "SITL guard check: criteria 1–3 PASS, criterion 4 failed as worded (harness artefact); mock tests", "the guard merged into fly_trial.py",
         "BUILT; TESTED IN SITL (accepted on criteria 1–3 plus the mock tests)", f"{S('M', 13593, 'B10b passed ONLY because')}; {S('M', 13987, 'H10 guard MERGED')}; ruling {S('M', 13997, 'The guard is ACCEPTED')}"],
        ["M1: power-cycle before a re-arm", "mitigation for F8", "applied in the SITL harness", "power-cycle the FC before any re-arm after a landing, then re-verify the EKF origin",
         "procedural (cards)", f"ruling {S('M', 14010, 'M1 (procedural)')}; {S('M', 14153, 'after M1, the origin is re-verified')}"],
        ["M2: watcher velocity check", "mitigation for F8", "SITL: the watcher withdrew at the first |v| ≥ 0.2 m/s sample; all counted FC probes refused (re-registered test PASSES AS WORDED)",
         "the watcher refuses arming unless EKF3's velocity stays < 0.2 m/s for 5 s while mocap shows the vehicle still; also a card step",
         "BUILT; TESTED IN SITL; hardware (props off) untested", f"{S('M', 14011, 'M2 (detection)')}; {S('M', 14155, 'M2-R PASSES AS WORDED')}; {S('M', 14158, 'withdrew at the first')}"],
        ["M3: land in ALT_HOLD; disarm within 2 s", "mitigation for F8 and F2", "the simulated pilot uses 2 s", "land in ALT_HOLD where safe; disarm within 2 s of any LAND touchdown",
         "procedural (cards)", f"ruling {S('M', 14014, 'M3 (procedural)')}; {S('M2B', 79, 'M3 in the harness')}"],
        ["Stock firmware arms without a watcher (watcher gap G6)", "stock ArduCopter refuses to arm only after the watcher was seen and then lost; never started → the FC ARMS",
         "SITL: arms by stick, by MAVLink and by force-arm; ARMING_RUDDER 0 blocks only the stick; the draft Lua script blocks stick and MAVLink",
         "(i) arm only via the flight script, ARMING_RUDDER 0; (ii) Lua arming authorisation",
         "Lua TESTED IN SITL only; on the board: hardware only; the G6 ruling is still open",
         f"{S('M', 13133, 'stock ArduCopter refuses to arm only AFTER')}; {S('M', 13601, 'Stock-firmware arming, CONFIRMED in SITL')}; {S('M', 13750, 'B5/B8a/G6 rulings')}"],
        ["Watcher gaps G1–G11 (11 gaps of the simulation watcher for real hardware)",
         "no mocap input; no stale-pose check; no rigid-body identity; breach stops the simulation; no FC-side layer; FC arms without a watcher; local-only liveness; "
         "'stop' has no hardware meaning; local heartbeat file; no height limit; heartbeat masking",
         "73 offline tests; SITL watcher bench (stock SITL) exercising each gap", "realflight/watcher closes all 11 (mocap input, stale-pose LAND 0.4–0.7 s, ID check, one LAND, "
         "own-ID heartbeat + GCS failsafe, beacons, height limit)",
         "11/11 BUILT and offline-tested; FC-side halves of G5, G6, G11 proven only on the bench; hardware-only: B4d, B6 hand procedure, B7a latency, B7c, "
         "B8b/c, B10c receiver failsafe, Lua on the board, Pi beacons, audible alert",
         f"{S('RFP', 442, '| G1 |')}-452; {S('M', 13122, 'Real-hardware mocap watcher BUILT (G1–G11)')}; {S('WB', 52, 'The FC-side')}; {S('M', 13615, 'B4d, the B6 hand procedure')}"],
    ]
    gaps = sum(1 for i in range(442, 453) if re.match(r"\| G\d+ \|", _lines("RFP")[i - 1]))
    check("number of watcher gaps listed in real_flights_plan.md (G1–G11)", gaps, int(grab("M", 13122, r"\(G1–G(\d+)\)")), "real_flights_plan.md:442-452; M:13122")
    save_tab("Table 8.2", "realflight_safety_findings", "Safety findings from the SITL safety bench, with mitigations and status",
             "Findings for the real-flight path: each with its evidence (the SITL watcher bench on stock SITL, or a source trace), its "
             "mitigation and its status (built, tested in SITL, or hardware only). These are not the 5S safety tests (Table 7.2).",
             ["finding (code)", "what", "evidence", "mitigation", "status", "source"], rows, [15, 22, 18, 20, 14, 20],
             [KEY_ABBR, "The codes F2, F6, F7, F8, B8a, H10 and M1–M3 have no thesis names in the vocabulary; the descriptive names "
              "here are proposals (a user ruling is needed). F2/F6/F7 also collide with figure ids, and the watcher's G1–G11 with "
              "another G family (glossary_flags.md)."], "Chapter 8 (towards real flights)", fs=7.0)


# ======================================================================== index
def write_index():
    nsrc = len(SRC); nok = sum(s[3] for s in SRC)
    allc = [c for it in ITEMS for c in it["checks"]]
    L_ = [f"# Methodology figure and tables: index (2026-10-17)", "",
          f"Built by `{SCRIPT}` at commit `{COMMIT}` (run with `/home/makerspace/venv-evo/bin/python`). Drawing and tabulating only: "
          "no simulation, no estimator result recomputed, numbers.md not edited. **Not yet in the combined PDF**: integration with "
          "`eval/figs_thesis.py` and `index.md` comes later. ArduPilot trees cited: thesis fork `~/ardupilot_ukf` "
          f"({AP_UKF_REV}); pinned `~/ardupilot` ({AP_PIN_REV}).", "",
          f"**Source checks: {nok}/{nsrc} citations verified** (the needle occurs verbatim on the cited line). "
          f"**Cross-checks: {sum(c[4] for c in allc)}/{len(allc)} EXACT** (computed string = stored string, `rd()` of "
          "`eval/figs_thesis.py`, loaded by AST).", "",
          "**Proposed numbering** (vocabulary §6: by chapter; Chapter 3 = method, Chapter 8 = towards real flights). File names are "
          "descriptive and new; `M1`–`M3` are deliberately not used as ids because they are the F8 mitigation codes.", "",
          "| proposed no. | files | title | checks | proposed place |", "|---|---|---|---|---|"]
    for it in ITEMS:
        L_.append(f"| {it['num']} | " + ", ".join(f"`{f}`" for f in it["files"]) + f" | {it['title']} | "
                  f"{sum(c[4] for c in it['checks'])}/{len(it['checks'])} | {it['chapter']} |")
    L_ += ["", "## Captions, sources and cross-checks", ""]
    for it in ITEMS:
        L_ += [f"### {it['num']}: {it['title']}", "", f"- **Caption:** {it['caption']}"]
        if it.get("sources"):
            L_ += ["- **Edges and boxes, with their sources** (every edge is derived from these lines):", ""]
            L_ += ["| what the diagram shows | source (file:line) |", "|---|---|"] + [f"| {md(w)} | {md(s)} |" for w, s in it["sources"]] + [""]
        else:
            L_ += [f"- **Sources:** in the table's source column (`docs/thesis/tables/{it['name']}.md`)."]
        if it["checks"]:
            L_ += ["", "| check | computed | expected | source | match |", "|---|---|---|---|---|"]
            L_ += [f"| {md(c[0])} | `{c[1]}` | `{c[2]}` | {md(c[3])} | {'yes' if c[4] else '**NO**'} |" for c in it["checks"]]
        L_ += [""]
    L_ += ["## Source verification (every citation)", "", "| file | line | needle | ok |", "|---|---|---|---|"]
    seen = set()
    for a, ln, nd, ok in SRC:
        if (a, ln, nd) in seen:
            continue
        seen.add((a, ln, nd))
        p = ALIAS[a][0].replace(os.path.expanduser("~"), "~")
        L_.append(f"| `{p}` | {ln} | `{nd.replace('|', '¦')}` | {'yes' if ok else '**NO**'} |")
    L_ += ["", "## Not buildable from existing sources (reported, not filled)", "",
           "- EKF3 offline step time: none exists (EKF3 runs only inside ArduPilot).",
           "- EKF3 flight-controller CPU, flash and RAM: not measured (part of stock firmware).",
           "- The FGO interface's flight-controller CPU: not estimated.",
           "- A ruling for the FGO's missing flow/range NIS gate and for the two-sided FLOW_MAX of the UKF (Table 3.3, rows 5–6).",
           "- The G6 ruling (stock-firmware arming without a watcher): open (M:13750).",
           "- Thesis names for the safety codes F2, F6, F7, F8, B8a, H10 and M1–M3: none in the vocabulary; Table 8.2 uses "
           "descriptive proposals.", ""]
    open(INDEX, "w").write("\n".join(L_))
    print(f"wrote {INDEX}: sources {nok}/{nsrc}, checks {sum(c[4] for c in allc)}/{len(allc)}")
    return nok == nsrc and all(c[4] for c in allc)


if __name__ == "__main__":
    os.makedirs(OUTF, exist_ok=True); os.makedirs(OUTT, exist_ok=True)
    fig_architecture()
    tab_design()
    tab_fairness()
    tab_matrix()
    tab_compute()
    tab_safety()
    ok = write_index()
    sys.exit(0 if ok else 1)
