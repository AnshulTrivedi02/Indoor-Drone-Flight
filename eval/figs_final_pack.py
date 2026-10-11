#!/usr/bin/env python3
"""FINAL RESULTS PACK (2026-10-11; METHODOLOGY ruling 2026-10-11, item 0). Analysis only: no replays, no new runs.

Regenerates the final figure set from the RESTATED results (eval/results/ at the FGO-only re-run, 819caab, and the
re-flown closed-loop / H results), adds the tag-experiment figure (H) and the closed-loop summary, renders the
before/after claims table and the corrections summary, and assembles ONE PDF plus an index.

Every figure carries CHECKS: values computed here from the result files, compared with the value typed from
docs/thesis/numbers.md (or METHODOLOGY where numbers.md has no row). A failed check marks the figure FLAGGED.

Inputs (read only): eval/results/**, docs/thesis/headline_claims_before_after.md,
docs/thesis/final_results_pack_corrections.md, and recorded flight data under ~/thesis_data/trials
(dataflash SIM/XKF1/XUKO for closed-loop paths and heading error; O_r1 bag /imu/time_ref and room TUMs;
T_A_r*/lc_fgo_*_t245/stats.json). Closed-loop paths use the dataflash SIM record (simulator truth, ~10 Hz) instead of
the zstd-packed bags; cross-checked against the scored B2 (bag /ground_truth/pose) to <= 4 mm.

Outputs: plots/final_results_pack/F*.png, docs/thesis/final_results_pack.pdf, docs/thesis/final_results_pack_index.md.
The historical supervisor sets (plots/supervisor_2026-10-0{1,8}/) are NOT touched.
Usage: ~/venv-evo/bin/python eval/figs_final_pack.py   (pymavlink via ~/.cache/thesis_pyshim, inserted below)"""
import json, math, os, re, subprocess, sys, textwrap
sys.path.insert(0, os.path.expanduser("~/.cache/thesis_pyshim"))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator
from matplotlib.backends.backend_pdf import PdfPages
from pymavlink import mavutil
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
from cruise_window import cruise_bounds
RES = os.path.join(ROOT, "eval", "results"); TD = os.path.expanduser("~/thesis_data/trials")
OUT = os.path.join(ROOT, "plots", "final_results_pack"); os.makedirs(OUT, exist_ok=True)
PDF = os.path.join(ROOT, "docs", "thesis", "final_results_pack.pdf")
INDEX = os.path.join(ROOT, "docs", "thesis", "final_results_pack_index.md")
SCRIPT = "eval/figs_final_pack.py"
COMMIT = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()

# Palette: the validated reference palette of the 2026-10-01 set (EKF3 slot 1 blue, FGO slot 2 orange, UKF slot 3 aqua;
# all-pairs CVD PASS). Aqua is < 3:1 contrast, so every series also has its own marker shape and a legend/direct label.
C = {"EKF3": "#2a78d6", "FGO": "#eb6834", "UKF": "#1baf7a"}
MK = {"EKF3": "o", "FGO": "s", "UKF": "^"}
INK, INK2, GRID, SURF, WALL = "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb", "#8c8b86"
plt.rcParams.update({"font.size": 13, "axes.titlesize": 14, "axes.labelsize": 13, "xtick.labelsize": 11, "ytick.labelsize": 11,
                     "legend.fontsize": 11, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
                     "text.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF, "lines.linewidth": 2,
                     "axes.spines.top": False, "axes.spines.right": False})
L = lambda f: json.load(open(os.path.join(RES, f)))
ITEMS = []        # dicts: id, png, title, kind, caption, inputs, rows, checks, status, replaces, note
CHK = []          # checks of the figure being built


def f2(v, n=2):
    return f"{v:.{n}f}"


def rng(vals, n=2, unit=""):
    return f"{min(vals):.{n}f}–{max(vals):.{n}f}{unit}"


NUM = re.compile(r"[-+−]?\d+(?:\.\d+)?(?:e[-+]?\d+)?")
ROUNDING = []     # checks that match only to one unit in the last printed digit (rounding-boundary transcriptions)


def check(label, computed, expected, src, exact=False):
    """Exact string match, or a numeric match within one unit of the expected value's last printed digit (recorded as
    a rounding-boundary note, not a mismatch: numbers.md values are transcribed, sometimes rounded differently)."""
    c, e = str(computed), str(expected)
    ok = c == e
    if not ok and not exact:
        a = NUM.findall(c.replace("−", "-")); b = NUM.findall(e.replace("−", "-"))
        if a and len(a) == len(b) and NUM.sub("#", c.replace("−", "-")) == NUM.sub("#", e.replace("−", "-")):
            unit = lambda s: 10 ** -len(s.split(".")[1]) if "." in s and "e" not in s else 1
            if all(abs(float(x) - float(y)) <= unit(y) * 1.0001 for x, y in zip(a, b)):
                ok = True; ROUNDING.append((label, c, e, src))
    CHK.append((label, c, e, src, ok))


def save(fig, fid, name, title, kind, caption, inputs, rows, replaces="", note=""):
    global CHK
    col = {"CONFIRMATORY": "#1c5cab", "DESCRIPTIVE": INK2, "EXPLORATORY": "#8a5a00", "DIAGNOSTIC": "#8a5a00", "SUMMARY": INK2}[kind.split()[0]]
    fig.text(0.995, 0.995, kind, ha="right", va="top", fontsize=10, color=col, weight="bold")
    p = os.path.join(OUT, name); fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
    ok = all(c[4] for c in CHK)
    ITEMS.append(dict(id=fid, png=p, title=title, kind=kind, caption=caption, inputs=inputs, rows=rows, checks=CHK,
                      status=("CURRENT" if CHK else "CURRENT (JSON only, unchecked)") if ok else "FLAGGED (check mismatch)", replaces=replaces, note=note))
    print(f"wrote {p}  checks {sum(c[4] for c in CHK)}/{len(CHK)}")
    for c in CHK:
        if not c[4]:
            print("   CHECK FAIL:", c)
    CHK = []


# ------------------------------------------------------------------ flight-data helpers (dataflash only)
_sim = {}
def sim_path(tr):
    """Simulator-truth path from dataflash SIM: (t s, x East m, y North m, yaw deg), origin at the first sample (spawn)."""
    if tr in _sim:
        return _sim[tr]
    m = mavutil.mavlink_connection(f"{TD}/{tr}/ardupilot.bin"); S = []
    while True:
        r = m.recv_match(type=["SIM"])
        if r is None:
            break
        S.append((r.TimeUS / 1e6, r.Lat, r.Lng, r.Yaw))
    S = np.array(S); lat, lng = S[:, 1], S[:, 2]
    if abs(lat).max() > 1000:
        lat, lng = lat / 1e7, lng / 1e7
    N = np.radians(lat - lat[0]) * 6378137; E = np.radians(lng - lng[0]) * 6378137 * math.cos(math.radians(lat.mean()))
    _sim[tr] = np.column_stack([S[:, 0], E, N, S[:, 3]]); return _sim[tr]


def log_yaw(tr, est):
    m = mavutil.mavlink_connection(f"{TD}/{tr}/ardupilot.bin"); E, S = [], []
    while True:
        r = m.recv_match(type=["SIM", "XKF1", "XUKO"])
        if r is None:
            break
        t = r.get_type()
        if t == "SIM": S.append((r.TimeUS / 1e6, r.Lat, r.Lng, r.Yaw))
        elif t == "XKF1" and est == "EKF3" and r.C == 0: E.append((r.TimeUS / 1e6, r.Yaw))
        elif t == "XUKO" and est == "UKF": E.append((r.TimeUS / 1e6, r.Yaw))
    S, E = np.array(S), np.array(E); lat, lng = S[:, 1], S[:, 2]
    if abs(lat).max() > 1000:
        lat, lng = lat / 1e7, lng / 1e7
    N = np.radians(lat - lat[0]) * 6378137; Ee = np.radians(lng - lng[0]) * 6378137 * math.cos(math.radians(lat.mean()))
    c0, _ = cruise_bounds(S[:, 0], Ee, N)
    un = lambda d: np.degrees(np.unwrap(np.radians(d)))
    w = E[:, 0] >= c0
    e = (un(E[w, 1]) - np.interp(E[w, 0], S[:, 0], un(S[:, 3])) + 180) % 360 - 180
    return E[w, 0] - c0, e


def cl_meta(tr):
    js = L(f"closed_loop_{tr}.json")
    c0 = js["cruise_s"][0] if "cruise_s" in js else js["cruise_start_s"]
    ct = js.get("contact")
    if ct and "t_rel_cruise_s" not in ct:
        ct = {"x": ct["E_m"], "y": ct["N_m"], "t_rel_cruise_s": ct["cruise_plus_s"]}
    return c0, ct


def draw_corridor(ax):
    for yw in (10, -10):
        ax.axhspan(yw - 0.1, yw + 0.1, color=WALL)
    ax.axhline(9.58, color=WALL, lw=0.8, ls=":"); ax.axhline(-9.58, color=WALL, lw=0.8, ls=":")
    ax.set_ylim(-10.6, 10.6); ax.set_xlim(0, 160)


def path_panel_off(ax, tr, est, win, ls="-"):
    g = sim_path(tr); c0, ct = cl_meta(tr); w = g[:, 0] >= 20
    ax.plot(g[w, 2], g[w, 1], color=C[est], lw=2, ls=ls)
    ax.plot(ct["y"], ct["x"], marker="X", ms=12, color=INK, mec=SURF, mew=1.5, zorder=5)
    y0 = float(np.interp(c0, g[:, 0], g[:, 2])); a, b = win
    ax.axvspan(y0 + 0.5 * a, y0 + 0.5 * b, ymin=0.0, ymax=0.08, color=C[est], alpha=0.25, lw=0)
    t = ct["t_rel_cruise_s"]
    ax.annotate(f"contact at cruise +{t:.1f} s ({'PASS' if a <= t <= b else 'MISS'}, window +{a}…+{b} s)", (ct["y"], ct["x"]),
                xytext=(4, 3.2), fontsize=11, color=INK, arrowprops=dict(arrowstyle="-", color=INK2, lw=1))
    return t


def path_panel_on(ax, trs, est, ls="-"):
    mx = []
    for k, tr in enumerate(trs):
        g = sim_path(tr); w = g[:, 0] >= 20
        ax.plot(g[w, 2], g[w, 1], color=C[est], lw=1.5, ls=ls, alpha=1 if k == 0 else 0.75)
        js = L(f"closed_loop_{tr}.json"); c0, c1 = js["cruise_s"]
        wc = (g[:, 0] >= c0) & (g[:, 0] <= c1)
        mx.append((js["B"]["B2"]["max_abs_x_cruise_m"], float(abs(g[wc, 1]).max())))
    ax.text(80, 6.2, f"{len(trs)} flights, max |cross-track| in cruise {max(a for a, _ in mx):.2f} m (band 6.0 m)", ha="center", fontsize=11)
    return mx


# =============================================================================================== F01 full-speed paths
CLF = {"EKF3_off": "cl_a_tex", "EKF3_on": [f"cl_bcpp_tex_r{i}" for i in (1, 2, 3)],
       "UKF_off": "cl_ukf_a_tex", "UKF_on": [f"cl_ukf_b_tex_r{i}" for i in (1, 2, 3)]}
WIN = {"EKF3": (155, 215), "UKF": (146, 218), "FGO": (145, 196)}
fig, axs = plt.subplots(2, 2, figsize=(16, 8.4), sharex=True, sharey=True)
mxall = []
for i, est in enumerate(("EKF3", "UKF")):
    draw_corridor(axs[i, 0]); draw_corridor(axs[i, 1])
    t = path_panel_off(axs[i, 0], CLF[f"{est}_off"], est, WIN[est])
    check(f"{est} full no-heading contact (s)", f"+{t:.1f}", {"EKF3": "+186.2", "UKF": "+163.0"}[est], "numbers.md §15 rows 1–2")
    mx = path_panel_on(axs[i, 1], CLF[f"{est}_on"], est); mxall += mx
    for j, m in enumerate(("no camera heading (n = 1)", "with camera heading (n = 3)")):
        axs[i, j].set_title(f"{est} flying, {m}", loc="left")
    axs[i, 0].set_ylabel("true East x (m)")
axs[1, 0].set_xlabel("distance along corridor, true North y (m)"); axs[1, 1].set_xlabel("distance along corridor, true North y (m)")
dmax = max(abs(a - b) for a, b in mxall)
check("SIM path vs scored B2 (bag GT), max |Δ| over 6 flights <= 0.010 m", "ok" if dmax <= 0.010 else f"{dmax:.3f}", "ok", "path-source cross-check")
check("EKF3 full C++ heading B2 range (m)", rng([a for a, _ in mxall[:3]]), "0.23–0.34", "numbers.md §15 B2 row")
check("UKF full heading B2 range (m)", rng([a for a, _ in mxall[3:]]), "0.16–0.29", "numbers.md §15 B2 row")
fig.suptitle("Closed loop at full speed: true paths when EKF3 or the UKF flies the vehicle (textured corridor)", x=0.01, ha="left", fontsize=15)
fig.tight_layout(rect=(0, 0, 1, 0.95))
save(fig, "F01", "F01_closed_loop_paths_full.png", "Closed-loop true paths at full speed: EKF3 and UKF, with and without the camera heading",
     "CONFIRMATORY (pre-registered closed-loop criteria)",
     "Simulator-truth paths (top-down) when EKF3 or the UKF is the vehicle's estimator: 0.5 m/s, textured corridor `corridor_textured_fwdc`. "
     "Walls are at x = ±10 m; the dotted line is the 9.58 m contact threshold. Without heading, both drift west into the wall: X marks the "
     "contact, and the shaded strip is the pre-registered contact window, mapped to distance at 0.5 m/s. With the camera heading, all six "
     "flights stay within 0.34 m of the centreline. n = 1 per no-heading flight and n = 3 per heading set; closed-loop run-to-run "
     "variability is unmeasured. The full-speed UKF here is the port BEFORE the jitter correction (flown 2026-10-01); it was not re-flown at "
     "full speed. The FGO flew at half speed only (F08). Same information within each estimator (heading on against off).",
     "paths: dataflash SIM of cl_a_tex, cl_bcpp_tex_r1–r3, cl_ukf_a_tex, cl_ukf_b_tex_r1–r3; contact times and B2: "
     "eval/results/closed_loop_<trial>.json", "§15: no-heading contact EKF3/UKF full; with-heading flights passing; B2 max cross-track",
     replaces="plots/supervisor_2026-10-01/fig1_closed_loop_paths.png (same flights; bag GT replaced by dataflash SIM)")

# =============================================================================================== F02 full-speed heading error
fig, axs = plt.subplots(2, 2, figsize=(16, 8.4), sharex=True)
for i, est in enumerate(("EKF3", "UKF")):
    for j, mode in enumerate(("off", "on")):
        ax = axs[i, j]; trs = [CLF[f"{est}_off"]] if mode == "off" else CLF[f"{est}_on"]
        for k, tr in enumerate(trs):
            t, e = log_yaw(tr, est); ax.plot(t, e, color=C[est], lw=1.3 if mode == "on" else 2, alpha=1 if k == 0 else 0.7)
        if mode == "on":
            ax.set_ylim(-1.0, 1.0)
            p95 = [L(f"closed_loop_{tr}.json")["B"]["B3"]["p95_deg"] for tr in trs]
            mxd = [L(f"closed_loop_{tr}.json")["B"]["B3"]["max_deg"] for tr in trs]
            ax.text(5, 0.8, f"|error| p95 {rng(p95)}°, max {rng(mxd)}° (bands 1.0° / 2.0°)", fontsize=11)
            check(f"{est} full B3 p95 / max (deg)", f"{rng(p95)}/{rng(mxd)}",
                  {"EKF3": "0.28–0.31/0.40–0.42", "UKF": "0.17–0.21/0.26–0.31"}[est], "numbers.md §15 B3 row")
        else:
            ax.text(5, 0.9 * ax.get_ylim()[1], "drifts without an absolute heading (until wall contact)", fontsize=11)
        ax.set_title(f"{est} flying, {'no camera heading (1 flight)' if mode == 'off' else 'with camera heading (3 flights)'}", loc="left")
        if i == 1: ax.set_xlabel("time since cruise start (s)")
        if j == 0: ax.set_ylabel("heading error, estimate − truth (°)")
fig.suptitle("Closed loop at full speed: heading error drifts without the camera heading, bounded with it (y-scales differ by column)",
             x=0.01, ha="left", fontsize=15)
fig.tight_layout(rect=(0, 0, 1, 0.95))
save(fig, "F02", "F02_closed_loop_heading_error_full.png", "Closed-loop heading error at full speed, with and without the camera heading",
     "CONFIRMATORY (pre-registered B3 bands)",
     "Heading error of the flying estimator against simulator truth (EKF3: XKF1; UKF: its current-time output XUKO), from cruise start, on the "
     "full-speed closed-loop flights of F01. Left: no heading, drift until wall contact. Right: with the camera heading, bounded well inside "
     "the pre-registered B3 bands (p95 ≤ 1.0°, max ≤ 2.0°). The y-scales differ between the columns. Same flights as F01 (UKF = the "
     "pre-jitter-correction port).",
     "curves: dataflash XKF1 / XUKO / SIM of the F01 trials; p95 and max: eval/results/closed_loop_<trial>.json (B3)",
     "§15: B3 yaw-error p95 / max (EKF3 full C++, UKF full)",
     replaces="plots/supervisor_2026-10-01/fig2_closed_loop_heading_error.png (same flights, same method)")

# =============================================================================================== F03 offline textured
ev = {**L("rerun_dsn_evo.json")["trials"], **L("dsn_extra_evo.json")["trials"]}
pt = L("dsn_paired_test.json")
fig, (ax, bx) = plt.subplots(1, 2, figsize=(16, 6.4), gridspec_kw={"width_ratios": [1.6, 1]})
med = {}
for k, est in enumerate(("EKF3", "FGO", "UKF")):
    v = [(i, ev[f"dsn_tex_r{i}"]["est"][est]["ate_a_cruise"]["+0.00"]) for i in range(1, 11)
         if est in ev[f"dsn_tex_r{i}"]["est"] and ev[f"dsn_tex_r{i}"]["est"][est]["ate_a_cruise"].get("+0.00") is not None]
    if est != "EKF3":
        v = [p for p in v if p[0] <= 9]
    x = np.array([p[0] for p in v]) + (k - 1) * 0.22
    ax.scatter(x, [p[1] for p in v], s=70, marker=MK[est], color=C[est], edgecolor=SURF, linewidth=1.5, zorder=3, label=f"{est} (n = {len(v)})")
    m9 = float(np.median([p[1] for p in v if p[0] <= 9])); med[est] = m9
    ax.text(10.6, m9, f"{est} median r1–r9 {m9:.2f} m", color=INK, fontsize=11, va="center")
    m3 = np.mean([p[1] for p in v if p[0] <= 3])
    check(f"{est} dsn_tex mean r1–r3 (m)", f2(m3), {"EKF3": "4.00", "FGO": "3.44", "UKF": "3.59"}[est], "numbers.md §6.1 / claims 1a")
    check(f"{est} dsn_tex median r1–r9 (m)", f2(m9), {"EKF3": "4.10", "FGO": "4.46", "UKF": "5.13"}[est], "numbers.md §6.1 standing row")
ax.set_xticks(range(1, 11)); ax.set_xlim(0.5, 14.2); ax.set_ylim(0, 7)
ax.set_xlabel("flight (dsn_tex r1 … r10; r10 unusable for UKF/FGO, IMU-gap rule)"); ax.set_ylabel("position error, evo -a (cruise) (m)")
ax.set_title("Per-flight accuracy, textured floor, no heading (descriptive)", loc="left", fontsize=13)
ax.legend(loc="upper left", frameon=False)
d = np.array(pt["d_m"]); fl = pt["usable_for_FGO"]
bx.axhline(0, color=INK2, lw=1)
bx.scatter(range(len(d)), d, s=80, marker=MK["EKF3"], color=C["EKF3"], edgecolor=SURF, linewidth=1.5, zorder=3)
lo, hi = pt["t95_ci_m"]; md = pt["mean_d_m"]
bx.errorbar([len(d) + 0.6], [md], yerr=[[md - lo], [hi - md]], fmt="D", ms=9, color=INK, capsize=8, lw=2)
bx.text(len(d) + 0.95, md, f"mean {md:+.3f} m\n95% CI [{lo:+.3f}, {hi:+.3f}]", va="center", fontsize=11)
bx.set_xticks(list(range(len(d))) + [len(d) + 0.6]); bx.set_xticklabels([f.replace("dsn_tex_", "") for f in fl] + ["mean"])
bx.set_xlim(-0.6, len(d) + 3.6); bx.set_ylabel("d = EKF3 − FGO, evo -a (cruise) (m)")
bx.set_title(f"Confirmatory test (r4–r10): {pt['verdict']}\nd < 0 on {pt['n_neg']} of {len(d)} usable (5/7 with r10 counted against)", loc="left", fontsize=13)
check("confirmatory verdict", pt["verdict"], "no ordering claimed", "numbers.md §6.1 confirmatory row")
check("confirmatory mean d, CI (m)", f"{md:.3f} [{lo:.3f}, {hi:.3f}]", "-0.021 [-0.989, 0.947]", "numbers.md §6.1 confirmatory row")
check("confirmatory d per flight r4–r9", " ".join(f"{x:+.3f}" for x in d), "-0.359 -0.489 +1.845 -0.498 -0.460 -0.164", "numbers.md §6.1")
fig.suptitle("Offline, textured floor, no heading: no ordering between EKF3 and the FGO is claimed (claim 2 WITHDRAWN)", x=0.01, ha="left", fontsize=15)
fig.tight_layout(rect=(0, 0, 1, 0.93))
save(fig, "F03", "F03_offline_textured_no_heading.png", "Offline accuracy, textured floor, no heading; the confirmatory EKF3 − FGO test",
     "CONFIRMATORY (right panel); DESCRIPTIVE (left)",
     "Left: evo -a (cruise) per flight for the three estimators on the same open-loop dsn_tex flights (same information). Descriptive "
     f"only: mean of r1–r3 FGO 3.44 < UKF 3.59 < EKF3 4.00 m (n = 3, driven by the bimodal r2; restatement "
     f"ruling 5); median of r1–r9 UKF {med['UKF']:.2f} > FGO {med['FGO']:.2f} > EKF3 {med['EKF3']:.2f} m. Right: the pre-registered "
     "paired test on the new flights r4–r10 (d = EKF3 − FGO; r10 is unusable for the FGO and counts against both directions). With the "
     "corrected FGO the verdict is \"no ordering claimed\": the former \"EKF3 beats the FGO\" (6/7, CI [−1.16, −0.21]) used the "
     "mis-specified FGO noise model and is WITHDRAWN (ruling 2, 2026-10-10). It is driven by r6 (FGO 1.27 against EKF3 3.11 m). "
     "UKF/FGO after all corrections, including the FGO-only re-run.",
     "eval/results/rerun_dsn_evo.json, dsn_extra_evo.json (ate_a_cruise '+0.00'); dsn_paired_test.json",
     "§6.1 (r1–r3 values, means, medians, confirmatory test, standing row); claims 1a, 1b, 2",
     replaces="plots/supervisor_2026-10-01/fig3_offline_textured_no_heading.png (FLAGGED: title says 'confirmed EKF3 < FGO', UKF median 5.34)")

# =============================================================================================== F04 C0
fig, ax = plt.subplots(figsize=(15, 6.4)); EK4, U4, F4 = [], [], []
bags = [("fwdc", r) for r in (1, 2, 3)] + [("fwdplainc", r) for r in (1, 2, 3)]
armsj = {ds: L(f"phase4_{ds}_arms.json") for ds in ("fwdc", "fwdplainc")}
mism = 0
for i, (ds, r) in enumerate(bags):
    e = L(f"phase4_{ds}_evo.json")["trials"][f"{ds}_tex_r{r}"]["est"]
    u, f, k = (e["UKF_heading"]["ate_a_cruise"]["+0.00"], e["FGO_heading"]["ate_a_cruise"]["+0.00"], e["EKF3"]["ate_a_cruise"]["+0.00"])
    a = armsj[ds][f"{ds}_tex_r{r}"]
    for arm, val in (("UKF_heading", u), ("FGO_heading", f)):
        try:
            if abs(a[arm]["evo"]["ate_a_cruise"]["+0.00"] - val) > 1e-6: mism += 1
        except (KeyError, TypeError):
            pass
    EK4.append(k); U4.append(u); F4.append(f)
    ax.plot([i, i], [f, u], color=GRID, lw=3, zorder=1)
    ax.scatter([i], [u], s=110, marker=MK["UKF"], color=C["UKF"], edgecolor=SURF, linewidth=1.5, zorder=3, label="UKF + camera heading" if i == 0 else None)
    ax.scatter([i], [f], s=110, marker=MK["FGO"], color=C["FGO"], edgecolor=SURF, linewidth=1.5, zorder=3, label="FGO + camera heading" if i == 0 else None)
    ax.scatter([i + 0.25], [k], s=60, marker="o", facecolor="none", edgecolor=WALL, linewidth=1.5, zorder=2,
               label="EKF3 without heading (reference only; NOT same information)" if i == 0 else None)
    ax.text(i + 0.08, u, f"{u:.2f}", fontsize=10, va="center"); ax.text(i + 0.08, f, f"{f:.2f}", fontsize=10, va="center")
ax.axvspan(2.5, 5.5, color="#f0efec", zorder=0)
ax.text(4, 6.0, "plain walls over the CHECKERBOARD floor: the heading FAILED Phase 3 validation here;\n"
        "no heading benefit is claimed (CONDITIONAL on the initial yaw σ; restatement ruling 4)", ha="center", fontsize=10.5, color=INK)
ax.set_yscale("log"); ax.set_ylim(0.04, 9)
ax.set_xticks(range(6)); ax.set_xticklabels([f"{ds}_tex_r{r}\n({'line-textured walls' if ds == 'fwdc' else 'plain walls'})" for ds, r in bags], fontsize=10)
ax.set_ylabel("position error, evo -a (cruise) (m, log scale)")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=3, frameon=False)
check("evo vs arms json agreement (mismatches)", mism, 0, "phase4_*_evo.json vs phase4_*_arms.json")
check("fwdc UKF +heading r1–r3 (m)", " / ".join(f2(x) for x in U4[:3]), "0.13 / 0.13 / 0.14", "numbers.md §6.6")
check("fwdc FGO +heading r1–r3 (m)", " / ".join(f2(x) for x in F4[:3]), "0.06 / 0.06 / 0.06", "numbers.md §6.6")
check("fwdplainc UKF +heading r1–r3 (m)", " / ".join(f2(x) for x in U4[3:]), "0.19 / 0.15 / 0.25", "numbers.md §6.6")
check("fwdplainc FGO +heading r1–r3 (m)", " / ".join(f2(x) for x in F4[3:]), "0.15 / 0.09 / 0.22", "numbers.md §6.6")
check("C0: FGO lower than UKF", f"{sum(a < b for a, b in zip(F4, U4))}/6", "6/6", "numbers.md §6.6 C0 row; claim 7")
check("EKF3 no-heading fwdc / fwdplainc r1–r3 (m)", " / ".join(f2(x) for x in EK4), "4.09 / 3.60 / 4.08 / 4.08 / 4.06 / 4.08", "numbers.md §6.4")
fig.suptitle("Offline with the camera heading: the FGO is lower than the UKF on all 6 textured-floor bags (C0; same information)", x=0.01, ha="left", fontsize=15)
fig.tight_layout(rect=(0, 0, 1, 0.93))
save(fig, "F04", "F04_offline_with_heading_C0.png", "Offline with the camera heading: FGO against UKF (C0)",
     "DESCRIPTIVE (C0 report)",
     f"Heading arms of the offline UKF and FGO on the same six textured-floor bags with the same camera headings (σ 0.148° / 0.126°, 3σ gate), "
     f"evo -a (cruise). FGO lower on {sum(a < b for a, b in zip(F4, U4))}/6: line-textured walls 0.06 against 0.13–0.14 m; plain walls "
     "0.09–0.22 against 0.15–0.25 m (margin 0.03–0.06 m). C0 compares the two estimators; it is not a heading-benefit claim. On the "
     "plain-wall bags (checkerboard floor, shaded) the heading failed Phase 3 validation, so NO heading benefit is claimed there: at a 0.1 rad "
     "initial yaw σ r3 rises to 5.70 m for both estimators (numbers.md §18). With heading the yaw error is UKF ≈ FGO on both wall types "
     "(fwdc 0.07–0.08°; fwdplainc 3.08–3.39° against 3.07–3.41°): the former \"UKF about 2× lower yaw error\" no longer holds (claim 6). "
     "Both estimators are equally over-confident on plain walls (NEES UKF 13.41, FGO 13.95). Open grey circles: EKF3 WITHOUT heading "
     "(3.60–4.09 m), shown only as a reference; not a same-information comparison.",
     "eval/results/phase4_fwdc_evo.json, phase4_fwdplainc_evo.json (UKF_heading, FGO_heading, EKF3); cross-checked against phase4_*_arms.json",
     "§6.4 (EKF3 fwdc/fwdplainc); §6.6 (heading arms, C0, yaw RMS, conditional plain-wall benefit, NEES); claims 5, 6, 7, 9",
     replaces="plots/supervisor_2026-10-01/fig4_offline_with_heading_C0.png (FLAGGED: values 0.08–0.61 / 0.61–0.94 m; 'UKF lower yaw error 5/6')")

# =============================================================================================== F05 decomposition
dec = L("phase5_analysis.json")["decomposition"]
fig, ax = plt.subplots(figsize=(15, 6.2)); HH = {}
rows5 = [("EKF3", "EKF3", "no heading"), ("UKF", "UKF_baseline", "no heading"), ("UKF", "UKF_heading", "with heading"),
         ("FGO", "FGO_baseline", "no heading"), ("FGO", "FGO_heading", "with heading")]
for i, (est, arm, lab) in enumerate(rows5):
    h = [abs(dec[f"fwdc_tex_r{r}"][arm]["xtrack_head_m"]) for r in (1, 2, 3)]
    s = [abs(dec[f"fwdc_tex_r{r}"][arm]["xtrack_resid_m"]) for r in (1, 2, 3)]
    ax.scatter(h, [i + 0.12] * 3, s=85, marker=MK[est], color=C[est], edgecolor=SURF, linewidth=1.5, zorder=3, label="heading-driven (filled)" if i == 0 else None)
    ax.scatter(s, [i - 0.12] * 3, s=85, marker=MK[est], facecolor=SURF, edgecolor=C[est], linewidth=2, zorder=3, label="residual, not heading (open)" if i == 0 else None)
    HH[arm] = (h, s)
    ax.text(max(h + s) * 1.3, i, f"heading-driven {np.mean(h):.2f} m | residual {np.mean(s):.2f} m", va="center", fontsize=11)
ax.set_yticks(range(len(rows5))); ax.set_yticklabels([f"{e}, {l}" for e, _, l in rows5])
ax.set_xscale("log"); ax.set_xlim(0.005, 3000); ax.invert_yaxis()
ax.set_xlabel("|cross-track error| at end of cruise (m, log scale)"); ax.legend(loc="lower right", frameon=False)
fig.suptitle("Where the cross-track error comes from: heading-driven against residual (fwdc_tex r1–r3)", x=0.01, ha="left", fontsize=15)
fig.tight_layout(rect=(0, 0, 1, 0.93))
nh = [x for a in ("EKF3", "UKF_baseline", "FGO_baseline") for x in HH[a][0]]
save(fig, "F05", "F05_drift_decomposition.png", "Heading-driven against residual cross-track, with and without the camera heading",
     "DESCRIPTIVE (Phase 5 analysis)",
     f"Lateral-error decomposition (Phase 5) on fwdc_tex r1–r3 (n = 3 per row): the part of the end-of-cruise cross-track explained by the "
     f"estimator's own heading error (filled) against the residual (open). Without heading, the heading error drives {min(nh):.1f}–{max(nh):.1f} m "
     f"of cross-track. With the camera heading the heading-driven part falls to ≤ {max(max(HH[a][0]) for a in ('UKF_heading', 'FGO_heading')):.2f} m, "
     f"leaving mean residuals of UKF {np.mean(HH['UKF_heading'][1]):.2f} m and FGO {np.mean(HH['FGO_heading'][1]):.2f} m. EKF3 has no offline "
     "heading arm (closed loop only). Values from the final re-runs; numbers.md has no Phase 5 decomposition row (§6.3 lists the related "
     "residual-partition rows as NOT RESTATED), so this figure is checked against its JSON only.",
     "eval/results/phase5_analysis.json (decomposition: xtrack_head_m, xtrack_resid_m)",
     "none (METHODOLOGY Phase 5 only; numbers.md §6.3 'not recomputed' note)",
     replaces="plots/supervisor_2026-10-01/fig5_drift_decomposition.png (FLAGGED: caption values pre-final re-run, e.g. UKF residual 1.78 m)",
     note="No numbers.md row: CURRENT against its JSON only.")

# =============================================================================================== F06 blank
bb = L("blank_behaviour.json")
fig, ax = plt.subplots(figsize=(14, 6.4))
T = ["+10s", "+30s", "+60s", "+120s"]; tx = [10, 30, 60, 120]; R6 = {}
for est, keys in (("UKF", ("ukf", "ukf_baseline")), ("FGO", ("fgo", "fgo_baseline"))):
    curves = []
    for trn, v in bb.items():
        if "blank" not in trn or trn.startswith("ds_"):
            continue
        a = next((v[k] for k in keys if k in v), None)
        if a is None:
            continue
        y = [math.hypot(a[t]["along_m"], a[t]["cross_m"]) if a.get(t) else np.nan for t in T]
        curves.append(y); ax.plot(tx, y, color=C[est], lw=1, alpha=0.35)
    cu = np.array(curves); R6[est] = cu
    mdn = np.nanmedian(cu, axis=0)
    ax.plot(tx, mdn, color=C[est], lw=3, marker=MK[est], ms=8, label=f"{est} baseline, median (n = {len(curves)})")
    ax.text(124, mdn[-1], f"{est}: ~{mdn[-1]:.0f} m at +120 s †", va="center", fontsize=11)
check("UKF +10/+30/+60 s ranges (m)", f"{rng(R6['UKF'][:, 0], 1)} / {rng(R6['UKF'][:, 1], 1)} / {rng(R6['UKF'][:, 2], 0)}",
      "6.4–8.2 / 27.3–36.5 / 60–108", "numbers.md §6.2")
check("FGO +10/+30/+60 s ranges (m)", f"{rng(R6['FGO'][:, 0], 1)} / {rng(R6['FGO'][:, 1], 1)} / {rng(R6['FGO'][:, 2], 0)}",
      "6.4–8.2 / 28.0–37.0 / 154–204", "numbers.md §6.2")
check("n flights", f"{len(R6['UKF'])}/{len(R6['FGO'])}", "11/11", "numbers.md §6.2")
ax.set_yscale("log"); ax.set_xlim(0, 150); ax.set_ylim(1, 1e5)
ax.text(3, 2.2e4, "EKF3: position flagged INVALID from take-off to landing on every blank flight\n"
        "(output held at the origin; not scored): no error curve, by design", fontsize=11, color=INK)
ax.set_xlabel("time since flow loss (s)"); ax.set_ylabel("position error magnitude (m, log scale)")
ax.legend(loc="lower right", frameon=False)
fig.suptitle("Total loss of flow aiding (blank floor): the UKF and FGO dead-reckon and diverge; EKF3 declares itself invalid", x=0.01, ha="left", fontsize=15)
fig.tight_layout(rect=(0, 0, 1, 0.93))
save(fig, "F06", "F06_blank_flow_loss.png", "Loss of flow aiding on the blank floor",
     "DESCRIPTIVE",
     "Position error magnitude after flow is lost on the blank floor, UKF and FGO baselines (thin lines: each of the 11 flights, dsn, p1c, fwdc "
     "and fwdplainc blank; thick: median). UKF 6.4–8.2 / 27.3–36.5 / 60–108 m and FGO 6.4–8.2 / 28.0–37.0 / 154–204 m at +10 / +30 / +60 s. "
     "EKF3 has no curve: its position is flagged invalid for the whole flight and it outputs the origin, which is not scored. Behaviour under "
     "total loss, not accuracy. † From +60 s the curves are runaway magnitudes (end of cruise UKF 29–40 km, FGO 22–41 km): evidence of divergence with its "
     "order of magnitude, not precise values (not bit-reproducible across BLAS builds; numbers.md †). The heading does not bound position "
     "without flow either (claim 10).",
     "eval/results/blank_behaviour.json (along_m, cross_m at +10/+30/+60/+120 s; EKF3 validity)",
     "§6.2 (+10/+30/+60 s rows, end-of-cruise †, EKF3 invalid); claim 10",
     replaces="plots/supervisor_2026-10-01/fig6_blank_flow_loss.png (curves pre-final re-run)")

# =============================================================================================== F07 F1
f1 = L("f1_test.json")
bagsF = ["fwdplainc_tex_r1", "fwdplainc_tex_r2", "fwdplainc_tex_r3", "fwdc_tex_r1", "fwdc_tex_r2", "fwdc_tex_r3"]
arms = [("UKF_hard", "UKF, hard 3σ gate", C["UKF"], None), ("FGO_hard", "FGO, hard 3σ gate", C["FGO"], "//"), ("FGO_robust", "FGO, robust (Cauchy)", C["FGO"], None)]
mets = [("correct headings rejected (%)", lambda m: 100 * m["correct_rejected"] / max(m["correct"], 1)),
        ("wrong headings accepted (%)", lambda m: 100 * m["wrong_accepted"] / max(m["wrong"], 1) if m["wrong"] else np.nan),
        ("worst-case yaw error (°)", lambda m: m["yaw_max_deg"]), ("max cross-track (m)", lambda m: m["xtrack_max_m"])]
fig, axs = plt.subplots(2, 2, figsize=(16, 8.8))
for ax, (lab, fn) in zip(axs.flat, mets):
    for k, (arm, nm, col, hatch) in enumerate(arms):
        v = [fn(f1[b][arm]) for b in bagsF]
        ax.bar(np.arange(6) + (k - 1) * 0.26, v, width=0.24, color=col if hatch is None else SURF, edgecolor=col, hatch=hatch, lw=1.5, label=nm)
    ax.set_xticks(range(6)); ax.set_xticklabels(["plain r1", "plain r2", "plain r3", "textured\nend wall r1", "textured\nend wall r2", "textured\nend wall r3"], fontsize=10)
    ax.set_ylabel(lab); ax.set_title(lab, loc="left", fontsize=13)
axs[0, 0].legend(loc="upper right", frameon=False, fontsize=10)
dec1 = f1["decision"]; lk = dec1["lockout_total"]
check("F1 robust lower yaw max on", f"{dec1['robust_lower_yaw_max_on']}/6", "6/6", "numbers.md §15.2 F1 row")
check("F1 lockouts FGO_robust = UKF_hard", json.dumps(lk, sort_keys=True), json.dumps({"FGO_robust": 3, "UKF_hard": 3}, sort_keys=True), "numbers.md §15.2 F1 row")
check("F1 verdict robust_FGO_better", dec1["robust_FGO_better"], False, "numbers.md §15.2: NOT met (lockout tie)")
check("FGO_hard plain-wall yaw max (deg)", rng([f1[b]["FGO_hard"]["yaw_max_deg"] for b in bagsF[:3]]), "4.59–5.03", "numbers.md §15.2 F1 row")
fig.suptitle("F1 (robust heading weighting): NOT met (lockout tie); robust FGO lower worst-case yaw on 6/6", x=0.01, ha="left", fontsize=15)
fig.tight_layout(rect=(0, 0, 1, 0.94))
save(fig, "F07", "F07_f1_robust_tradeoff.png", "F1: robust heading weighting trade-off",
     "EXPLORATORY (descriptive bars; pre-registered decision NOT met)",
     "Same camera headings (σ 0.148° / 0.126°) on the plain-wall bags (whole cruise) and the textured end-wall region (y > 140 m). The "
     "pre-registered F1 decision is NOT met (lockout tie; ruling 8): the robust FGO has the lower worst-case yaw on 6/6 bags, but its lockouts "
     "equal the UKF's (3 = 3). The hard-gated FGO no longer diverges on plain walls (yaw max 4.59–5.03°, = UKF to 0.01°; was ~180°). Its F1 "
     "lockouts rose 14 → 33 but are not part of the rule. 'Rejected' for the robust arm = weight < 0.5 (it still contributes). The textured "
     "end-wall 'wrong accepted' rates rest on very few wrong headings.",
     "eval/results/f1_test.json", "§15.2 F1 row; claim 27",
     replaces="plots/supervisor_2026-10-01/fig8_f1_robust_tradeoff.png (FLAGGED: caption 'UKF lower worst-case yaw on all 6')")

# =============================================================================================== F08 half-speed paths incl. re-flights
HALF = [("EKF3", "EKF3", "cl_a_tex_half", [f"cl_bcpp_tex_r{i}_half" for i in (1, 2, 3)], "-"),
        ("UKF original (pre-jitter fix)", "UKF", "cl_ukf_a_tex_half", [f"cl_ukf_b_tex_r{i}_half" for i in (1, 2, 3)], "-"),
        ("UKF v2 (jitter-corrected)", "UKF", "cl_ukf_a_tex_half_v2", [f"cl_ukf_b_tex_r{i}_half_v2" for i in (1, 2, 3)], "-"),
        ("FGO original (old noise model)", "FGO", "cl_fgo_a_tex_half", [f"cl_fgo_b_tex_r{i}_half" for i in (1, 2, 3)], "-"),
        ("FGO v3 (final; OLD priors)", "FGO", "cl_fgo_a_tex_half_v3", [f"cl_fgo_b_tex_r{i}_half_v3" for i in (1, 2, 3)], "-"),
        ("FGO robust (original)", "FGO", None, [f"cl_fgo_b_robust_tex_r{i}_half" for i in (1, 2, 3)], "--")]
fig, axs = plt.subplots(len(HALF), 2, figsize=(16, 3.0 * len(HALF) + 1), sharex=True, sharey=True)
CT8 = {}; B28 = {}
for i, (nm, est, off, ons, ls) in enumerate(HALF):
    draw_corridor(axs[i, 0]); draw_corridor(axs[i, 1])
    if off is None:
        axs[i, 0].text(80, 0, "not flown (robust variant flown with heading only)", ha="center", fontsize=11, color=INK2)
    else:
        CT8[nm] = path_panel_off(axs[i, 0], off, est, WIN[est], ls)
    mx = path_panel_on(axs[i, 1], ons, est, ls); B28[nm] = [a for a, _ in mx]
    axs[i, 0].set_title(f"{nm}, no camera heading", loc="left", fontsize=12)
    axs[i, 1].set_title(f"{nm}, with camera heading", loc="left", fontsize=12)
    axs[i, 0].set_ylabel("true East x (m)")
axs[-1, 0].set_xlabel("distance along corridor, true North y (m)"); axs[-1, 1].set_xlabel("distance along corridor, true North y (m)")
check("contacts EKF3 / UKF / UKF v2 / FGO / FGO v3 (s)", " / ".join(f"+{CT8[n]:.1f}" for n in [h[0] for h in HALF[:5]]),
      "+242.1 / +198.0 / +165.9 / +165.8 / +169.9", "numbers.md §15 (EKF3, UKF, UKF v2, FGO, FGO v3)")
check("UKF v2 heading B2 (m)", " / ".join(f"{x:.3f}" for x in B28["UKF v2 (jitter-corrected)"]), "0.231 / 0.253 / 0.219", "numbers.md §15 re-flown B1/B2/B4 row")
check("FGO v3 heading B2 (m)", " / ".join(f"{x:.3f}" for x in B28["FGO v3 (final; OLD priors)"]), "0.118 / 0.033 / 0.392", "numbers.md §15 re-flown B1/B2/B4 row")
check("EKF3 half / UKF orig / FGO hard / FGO robust B2 range (m)",
      " ; ".join(rng(B28[n]) for n in ("EKF3", "UKF original (pre-jitter fix)", "FGO original (old noise model)", "FGO robust (original)")),
      "0.24–0.33 ; 0.13–0.53 ; 0.06–0.25 ; 0.05–0.14", "numbers.md §15 B2 row")
fig.suptitle("Closed loop at half speed: true paths when each estimator flies, original sets and the corrected re-flights", x=0.01, ha="left", fontsize=15)
fig.tight_layout(rect=(0, 0, 1, 0.97))
save(fig, "F08", "F08_closed_loop_paths_half.png", "Closed-loop true paths at half speed: EKF3, UKF (original and v2), FGO (original, v3, robust)",
     "CONFIRMATORY (pre-registered closed-loop criteria)",
     "Simulator-truth paths, half-speed textured corridor `corridor_textured_half_fwdc` (cruise 0.5 m/s; walls at x = ±10 m; dotted = 9.58 m "
     "contact threshold). Without heading every estimator drifts west into the wall (X = contact; shaded = the pre-registered window). EKF3 "
     "reached it after its window (+242.1 s, MISS; D21; no cross-speed comparison is claimed). With the camera heading, every flight shown "
     "stays near the centreline. The re-flights: UKF v2 (jitter-corrected port) contact +165.9 s, heading set 3/3 (the original r3 failed "
     "B4, D22); FGO v3 (noise fix + gated yaw cap) contact +169.9 s, heading set 3/3 (r3 B4 0.246 m/s, the closest call; D22 recurrence). "
     "The FGO v2 (noise fix only) ablation is in F15. ALL flown FGO results used the OLD FGO priors (initial yaw σ 1e-3 rad, roll/pitch 2°); "
     "they were not re-flown before the freeze. n = 1 per no-heading flight. Dashed = robust heading weighting (plan step 2(b)).",
     "paths: dataflash SIM of the trials named in each panel title (cl_*_half, *_v2, *_v3); contact and B2: eval/results/closed_loop_<trial>.json",
     "§15 rows (contact EKF3/UKF/UKF v2/FGO/FGO v2/FGO v3 half; B2; re-flown B1/B2/B4 and B3 rows); claim 14",
     replaces="plots/supervisor_2026-10-01/fig10_closed_loop_paths_half.png (FLAGGED: lacks the UKF v2 and FGO v3 re-flights)",
     note="numbers.md §15 rows for the UKF v2 and FGO v2/v3 re-flights added 2026-10-11 (pack flag 2).")

# =============================================================================================== T, O, L
TRK = {"EKF3 live": (C["EKF3"], "-", "EKF3"), "UKF live": (C["UKF"], "-", "UKF"), "FGO live": (C["FGO"], "-", "FGO"),
       "RTS-UKF (hindsight)": (C["UKF"], "--", "UKF"), "FGO hindsight (whole-flight batch)": (C["FGO"], "--", "FGO")}
SHORT = {"EKF3 live": "EKF3 live", "UKF live": "UKF live", "FGO live": "FGO live", "RTS-UKF (hindsight)": "RTS-UKF (hindsight)",
         "FGO hindsight (whole-flight batch)": "FGO batch (hindsight)"}


def plain_log(ax, ticks):
    ax.yaxis.set_major_locator(FixedLocator(ticks)); ax.yaxis.set_minor_locator(NullLocator())
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))


# F09 T gain
fig, axs = plt.subplots(1, 2, figsize=(14, 5.6), sharey=True)
agg = L("expT/t_aggregate.json")
for ax, live, hind, key, est, lab in ((axs[0], "FGO live", "FGO hindsight (whole-flight batch)", "H-T1 (FGO live -> whole-flight batch)", "FGO", "FGO: live − whole-flight batch"),
                                      (axs[1], "UKF live", "RTS-UKF (hindsight)", "P-T2 (UKF live -> RTS)", "UKF", "UKF: live − RTS-smoothed")):
    for cnd in "ABCD":
        Lg, Dg = [], []
        for r in (1, 2, 3):
            for g in L(f"expT/T_{cnd}_r{r}.json")["gaps"]:
                if live in g and hind in g:
                    Lg.append(g["length_s"]); Dg.append(1e3 * (g[live]["mean"] - g[hind]["mean"]))
        ax.scatter(Lg, Dg, s=20, marker=MK[est], color=C[est], alpha=0.35, edgecolor="none")
        m_ = 1e3 * agg[key]["median_gain_m"][cnd]
        ax.plot([np.median(Lg)], [m_], "D", color=C[est], ms=11, mec=SURF, mew=2)
        ax.annotate(cnd, (np.median(Lg), m_), textcoords="offset points", xytext=(8, 6), fontsize=12, weight="bold", color=INK)
    ax.axhline(0, color=INK2, lw=1); v = agg[key]
    ax.set_title(f"{lab}\nρ = {v['spearman_rho']:+.2f}, p = {v['p']:.0e}; {'PASS' if v['PASS'] else 'FAIL'}", fontsize=13)
    ax.set_xlabel("gap between tag fixes (s)")
axs[0].set_ylabel("hindsight gain per gap (mm)\n(live mean error − hindsight mean error)")
h1 = agg["H-T1 (FGO live -> whole-flight batch)"]; p2 = agg["P-T2 (UKF live -> RTS)"]
check("H-T1 median gain A–D (m)", " / ".join(f"{h1['median_gain_m'][c]:.3f}" for c in "ABCD"), "0.010 / 0.011 / 0.023 / 0.052", "numbers.md §16.1")
check("H-T1 rho, p, PASS", f"{h1['spearman_rho']:+.2f} {h1['p']:.0e} {h1['PASS']}", "+0.30 6e-06 True", "numbers.md §16.1")
check("P-T2 gain A–D (m), PASS", " / ".join(f"{p2['median_gain_m'][c]:+.3f}" for c in "ABCD") + f" {p2['PASS']}",
      "+0.020 / +0.032 / +0.037 / +0.029 False", "numbers.md §16.1")
fig.tight_layout()
save(fig, "F09", "F09_T_hindsight_gain_vs_gap.png", "T: the hindsight gain grows with the gap for the FGO, not for the single-pass RTS-UKF",
     "CONFIRMATORY (pre-registered H-T1, P-T2)",
     "Per gap between consecutive tag fixes (12 flights, 213 gaps; dots), the mean live horizontal error minus the mean hindsight error over the "
     "gap; diamonds = condition medians (A all 8 tags, B corners, C 2 diagonal, D 1 tag; median gaps 4.3 / 10.1 / 22.0 / 46.3 s). Left: the "
     "FGO whole-flight batch against its own fixed-lag live estimate, the pre-registered primary H-T1: medians 0.010 / 0.011 / 0.023 / "
     "0.052 m, strictly increasing, ρ = +0.30, PASS. Right: the RTS-smoothed UKF against the live UKF (P-T2, FAIL): +0.020 / +0.032 / +0.037 / "
     "+0.029 m, all positive now but not increasing. Same tag fixes for every estimator. Restated after the FGO-only re-run.",
     "eval/results/expT/T_*.json (gaps), t_aggregate.json", "§16.1 (H-T1, P-T2); claim 17",
     replaces="plots/supervisor_2026-10-08/fig11_T_hindsight_gain_vs_gap.png (pre-final re-run values)")

# F10 T RMSE
fig, ax = plt.subplots(figsize=(13, 5.8)); names = list(TRK); off = np.linspace(-0.3, 0.3, len(names)); TT = {}
for i, n in enumerate(names):
    col, ls, est = TRK[n]
    for ci, cnd in enumerate("ABCD"):
        v = [1e3 * L(f"expT/T_{cnd}_r{r}.json")["tracks"][n]["horiz_err_m"]["rmse"] for r in (1, 2, 3)]
        TT[(n, cnd)] = v
        ax.scatter([ci + off[i]] * 3, v, color=col if ls == "-" else SURF, edgecolor=col, linewidth=2, s=50, marker=MK[est], zorder=3,
                   label=SHORT[n] + (" (open)" if ls == "--" else "") if ci == 0 else None)
ax.set_xticks(range(4)); ax.set_xticklabels(["A: all 8\n(gap 4.3 s)", "B: corners\n(10.1 s)", "C: 2 diagonal\n(22.0 s)", "D: 1 tag\n(46.3 s)"])
ax.set_ylabel("horizontal RMSE over the laps (mm, log scale)"); ax.set_yscale("log"); plain_log(ax, [10, 20, 50, 100, 200])
ax.legend(ncol=5, loc="upper left", fontsize=10, frameon=False, bbox_to_anchor=(0, 1.12))
ag = agg["conditions"]
exp10 = {"A": "0.039 0.037 0.020 0.014 0.011", "B": "0.055 0.061 0.026 0.031 0.015", "C": "0.074 0.076 0.053 0.039 0.019", "D": "0.096 0.131 0.083 0.109 0.028"}
for cnd in "ABCD":
    mr = ag[cnd]["mean_rmse_m"]
    check(f"T {cnd}: EKF3 / UKF / FGO live / RTS-UKF / FGO batch (m)",
          " ".join(f"{mr[k]:.3f}" for k in ("EKF3 live", "UKF live", "FGO live", "RTS-UKF (hindsight)", "FGO hindsight (whole-flight batch)")),
          exp10[cnd], "numbers.md §16.1 table")
fig.tight_layout()
save(fig, "F10", "F10_T_rmse_by_condition.png", "T: horizontal error by tag density, live and hindsight",
     "CONFIRMATORY (pre-registered P-T3, P-T4)",
     "Horizontal RMSE in the world frame (no alignment) over the 5-lap window; 3 repeats per condition (each marker one flight). Filled = "
     "live, open = hindsight; marker shape = estimator. The FGO live track is lowest of the live tracks in every condition (in D, 0.083 "
     "against EKF3 0.096 m, descriptive only, n = 3; ruling 7). Live max/min ratios 1.97 / 2.36 / 1.42 / 1.58 (P-T3 FAIL). The FGO batch "
     "stays at 11–28 mm; batch FGO against RTS-UKF ratios 1.31 / 2.14 / 2.07 / 3.89 (P-T4 FAIL). Log scale.",
     "eval/results/expT/T_*.json (tracks.*.horiz_err_m.rmse); t_aggregate.json (means)", "§16.1 table, P-T3, P-T4, condition D bullet; claims 17, 18",
     replaces="plots/supervisor_2026-10-08/fig12_T_rmse_by_condition.png (FLAGGED: caption 'EKF3 lowest live with the sparsest (D)', '11–34 mm')")

# F11 O
ts = get_typestore(Stores.ROS2_JAZZY)
tr = "O_r1"; D = f"{TD}/{tr}"
o = L(f"expO/{tr}.json"); toff, ton = o["markers_bag_s"]["GNSS OFF"], o["markers_bag_s"]["GNSS ON"]
G = np.loadtxt(f"{D}/room_ukf/ground_truth.tum")
TR = []
with Reader(f"{D}/bag") as rd:
    cs = [c for c in rd.connections if c.topic == "/imu/time_ref"]
    for con, _, raw in rd.messages(connections=cs):
        m = ts.deserialize_cdr(raw, con.msgtype)
        TR.append((m.time_ref.sec + m.time_ref.nanosec * 1e-9, m.header.stamp.sec + m.header.stamp.nanosec * 1e-9))
TR = np.array(TR); sitl, dd = TR[:, 0], TR[:, 1] - TR[:, 0]; env = []
for lo in np.arange(sitl.min(), sitl.max(), 5.0):
    w = (sitl >= lo) & (sitl < lo + 5)
    if w.sum() > 50:
        i = np.argmin(dd[w]); env.append((sitl[w][i], dd[w][i]))
env = np.array(env); kk, c0 = np.polyfit(env[:, 0], env[:, 1], 1)
oE, oN = np.load(f"{D}/gnss.npz")["ekf3_origin_EN"]
mv = mavutil.mavlink_connection(f"{D}/ardupilot.bin"); k1 = []
while True:
    r = mv.recv_match(type=["XKF1"])
    if r is None: break
    if r.C == 0:
        t = r.TimeUS / 1e6; k1.append((t + kk * t + c0, r.PE + oE, r.PN + oN))
tracks = {"EKF3 live": np.array(k1)}
for n, p in (("UKF live", "room_ukf/ukf_live.tum"), ("RTS-UKF (hindsight)", "room_ukf/ukf_rts.tum"), ("FGO live", "room_fgo/fgo_live.tum"),
             ("FGO hindsight (whole-flight batch)", "room_fgo/fgo_batch.tum")):
    tracks[n] = np.loadtxt(f"{D}/{p}")[:, :3]
fig, axs = plt.subplots(1, 2, figsize=(15, 5.8), gridspec_kw={"width_ratios": [2.2, 1]})
ax = axs[0]; ax.axvspan(0, ton - toff, color=GRID, zorder=0)
ax.text((ton - toff) / 2, 0.93, f"indoors: GNSS off ({ton - toff:.0f} s)", ha="center", transform=ax.get_xaxis_transform(), color=INK2, fontsize=11)
rm_ind = {}
for n, Tk in tracks.items():
    col, ls, est = TRK[n]; w = (Tk[:, 0] > toff - 40) & (Tk[:, 0] < ton + 30)
    e = np.hypot(Tk[w, 1] - np.interp(Tk[w, 0], G[:, 0], G[:, 1]), Tk[w, 2] - np.interp(Tk[w, 0], G[:, 0], G[:, 2]))
    ax.plot(Tk[w, 0] - toff, e, color=col, ls=ls, label=SHORT[n])
    wi = (Tk[:, 0] >= toff) & (Tk[:, 0] <= ton)
    ei = np.hypot(Tk[wi, 1] - np.interp(Tk[wi, 0], G[:, 0], G[:, 1]), Tk[wi, 2] - np.interp(Tk[wi, 0], G[:, 0], G[:, 2]))
    rm_ind[n] = float(np.sqrt(np.mean(ei ** 2)))
ax.set_xlabel("time from GNSS OFF (s)"); ax.set_ylabel("horizontal error (m)"); ax.set_xlim(-40, ton - toff + 30)
ax.legend(loc="upper left", fontsize=10, frameon=False)
jump = o["tracks"]["EKF3 live"]["max_step_after_return_m"]
ax.annotate(f"EKF3 reset jump\n{jump:.1f} m", (ton - toff + 4.5, 3.4), fontsize=10, color=INK)
ax = axs[1]; OI = {}
for i, n in enumerate(TRK):
    col, ls, est = TRK[n]
    v = [L(f"expO/{t}.json")["tracks"][n]["indoor_rmse_m"] for t in ("O_r1", "O_r2", "O_r3b")]; OI[n] = v
    ax.scatter([i] * 3, v, color=col if ls == "-" else SURF, edgecolor=col, linewidth=2, s=60, marker=MK[est], zorder=3)
ax.set_xticks(range(len(TRK))); ax.set_xticklabels([SHORT[n].replace(" (", "\n(") for n in TRK], fontsize=9)
ax.set_ylabel("indoor horizontal RMSE (m)"); ax.set_ylim(0, None)
exO = {"EKF3 live": "1.42–1.43", "UKF live": "0.77–0.84", "FGO live": "0.83–0.89", "RTS-UKF (hindsight)": "0.58–0.60", "FGO hindsight (whole-flight batch)": "0.59–0.59"}
for n in TRK:
    check(f"O indoor RMSE {SHORT[n]} (m)", rng(OI[n]), exO[n], "numbers.md §16.2 table")
cf = [L(f"expO/{t}.json")["tracks"]["RTS-UKF (hindsight, cap-free forward pass)"]["indoor_rmse_m"] for t in ("O_r1", "O_r2", "O_r3b")]
check("O cap-free RTS-UKF (m)", rng(cf), "0.60–0.62", "numbers.md §16.2")
jumps = [L(f"expO/{t}.json")["tracks"]["EKF3 live"]["max_step_after_return_m"] for t in ("O_r1", "O_r2", "O_r3b")]
check("O EKF3 reset jump (m)", rng(jumps), "4.10–4.10", "numbers.md §16.2 ('4.10 m, every flight')")
dO = max(abs(rm_ind[n] - o["tracks"][n]["indoor_rmse_m"]) for n in TRK)
check("O_r1 curve indoor RMSE recomputed vs json, max |Δ| <= 0.05 m", "ok" if dO <= 0.05 else f"{dO:.3f}", "ok", "curve source vs scorer")
fig.tight_layout()
save(fig, "F11", "F11_O_indoor_hindsight.png", "O: indoor error with GNSS outside only; hindsight reconstruction and EKF3's return jump",
     "CONFIRMATORY (pre-registered H-O1, H-O2, P-O3)",
     "Left: horizontal error against time for O_r1, outdoor → indoor (grey, GNSS off, 123 s) → outdoor; world frame, no alignment. The live "
     "tracks drift indoors and EKF3 jumps 4.10 m when it resets to GNSS on return. Right: indoor RMSE for all 3 flights (filled = live, open = "
     "hindsight). H-O1 PASS 3/3 (the FGO batch is below both filters' live tracks). H-O2 FAIL (live ratio 1.72–1.84×). P-O3 PASS (batch FGO "
     "against RTS-UKF 1.01–1.02, cap-free 1.02–1.05; flip accepted, ruling 5). The FGO batch is now 0.59 m (was 0.33 m): the former \"FGO batch "
     "~2× better than the RTS-UKF\" was largely an artefact of the mis-specified FGO noise model and is WITHDRAWN. Partial attribution "
     "(ruled): ~93% noise fix, ~7% yaw cap, +0.03 m interaction. Same GNSS samples for every estimator.",
     "eval/results/expO/O_*.json; curves: O_r1 room_ukf/, room_fgo/ TUMs (FGO-only re-run outputs), dataflash XKF1 about EKF3's origin (gnss.npz), "
     "bag /imu/time_ref (clock map)", "§16.2 table and bullets (H-O1, H-O2, P-O3, WITHDRAWN, partial attribution); §18; claims 19–22",
     replaces="plots/supervisor_2026-10-08/fig13_O_indoor_hindsight.png (FLAGGED: '0.33 m', 'P-O3 FAIL', 'cap-free 0.97 m')")

# F12 L laps
fig, ax = plt.subplots(figsize=(12, 5.8)); LL = {}
for mode, col, lab, mk in (("lc", C["FGO"], "with loop closure", "s"), ("nolc", INK2, "without loop closure", "D")):
    for kind, ls in (("live", "-"), ("hindsight", "--")):
        for r in (1, 2, 3):
            tk = L(f"expL/T_A_r{r}_t245.json")["tracks"][f"{mode} {kind}"]
            v = tk["per_lap_rmse_m"]; LL.setdefault((mode, kind), []).append(tk)
            ax.plot(range(1, 6), np.array(v) * 1e3, color=col, ls=ls, marker=mk, ms=6, alpha=0.85,
                    label=f"{lab}, {kind}" if r == 1 else None, mfc=col if ls == "-" else SURF)
ax.set_xlabel("lap (6 m square)"); ax.set_ylabel("horizontal RMSE per lap (mm, log scale)"); ax.set_xticks(range(1, 6)); ax.set_yscale("log")
plain_log(ax, [20, 30, 50, 100, 200, 300, 500])
ax.legend(loc="lower left", ncol=2, fontsize=10, frameon=False, bbox_to_anchor=(0, 1.01))
check("L lc live overall (m)", rng([t["rmse_m"] for t in LL[("lc", "live")]], 3), "0.049–0.076", "numbers.md §16.3")
check("L lc hindsight overall (m)", rng([t["rmse_m"] for t in LL[("lc", "hindsight")]], 3), "0.017–0.027", "numbers.md §16.3")
check("L nolc live overall (m)", rng([t["rmse_m"] for t in LL[("nolc", "live")]], 3), "0.262–0.361", "numbers.md §16.3")
check("L nolc hindsight overall (m)", rng([t["rmse_m"] for t in LL[("nolc", "hindsight")]], 3), "0.221–0.266", "numbers.md §16.3")
check("L lap5/lap1 lc live; nolc live", rng([t["per_lap_rmse_m"][4] / t["per_lap_rmse_m"][0] for t in LL[("lc", "live")]]) + "; " +
      rng([t["per_lap_rmse_m"][4] / t["per_lap_rmse_m"][0] for t in LL[("nolc", "live")]], 1), "0.16–0.43; 2.9–4.5", "numbers.md §16.3")
fig.tight_layout()
save(fig, "F12", "F12_L_lap_by_lap.png", "L: tag re-identification bounds the drift lap by lap",
     "CONFIRMATORY (pre-registered H-L1, H-L2, H-L3, P-L4)",
     "Keyframe FGO with tags at UNKNOWN positions, T_A_r1–r3 (3 lines per style), RMSE per 6 m lap in the first tag's frame. With loop closure "
     "the live error falls after lap 1 (lap 5 ÷ lap 1 0.16–0.43; overall 0.049–0.076 m live, 0.017–0.027 m hindsight). Without it the live "
     "error grows 2.9–4.5× over five laps (overall 0.262–0.361 m). H-L1, H-L2, H-L3 and P-L4 PASS 3/3; the magnitudes moved in the FGO-only "
     "re-run (initial-uncertainty correction; not attributed individually), the result did not. An FGO capability, not an FGO-against-filter "
     "result. V-L is not re-scorable on the corrected FGO (ruling 6, 2026-10-09). Log scale.",
     "eval/results/expL/T_A_r*_t245.json (per_lap_rmse_m, rmse_m)", "§16.3 table and bullets; claims 23, 24",
     replaces="plots/supervisor_2026-10-08/fig14_L_lap_by_lap.png (FLAGGED: caption '4.5–5.5×', '0.02–0.04 m')")

# F13 L compute cost (stats.json of the current outputs)
fig, axs = plt.subplots(1, 3, figsize=(15, 5.2)); ST = {}
for j, (key, lab, sc) in enumerate((("step_median_ms", "median solve time per update (ms)", 1), ("step_p99_ms", "p99 solve time per update (ms)", 1),
                                     ("wall_s", "wall time per replay (s)", 1))):
    ax = axs[j]
    for k, (mode, col, nm) in enumerate((("lc", C["FGO"], "with LC"), ("nolc", INK2, "no LC"))):
        v = [json.load(open(f"{TD}/T_A_r{r}/lc_fgo_{mode}_t245/stats.json"))[key] for r in (1, 2, 3)]; ST[(mode, key)] = v
        ax.bar(np.arange(3) + (k - 0.5) * 0.38, v, width=0.36, color=col, label=nm)
    ax.set_xticks(range(3)); ax.set_xticklabels(["T_A_r1", "T_A_r2", "T_A_r3"]); ax.set_ylabel(lab); ax.set_yscale("log")
    ax.set_title(lab, loc="left", fontsize=12)
axs[0].legend(frameon=False)
check("L LC median (ms)", rng(ST[("lc", "step_median_ms")], 0), "35–41", "numbers.md §16.3 (FGO-only re-run; restated 2026-10-11)", exact=True)
check("L no-LC median (ms)", rng(ST[("nolc", "step_median_ms")], 0), "50–61", "numbers.md §16.3 (FGO-only re-run; restated 2026-10-11)", exact=True)
check("L no-LC wall (s)", rng(ST[("nolc", "wall_s")], 0), "7276–9583", "numbers.md §16.3 (FGO-only re-run; restated 2026-10-11)", exact=True)
fig.suptitle("L: computational cost per replay, keyframe FGO (diagnostic; workstation Python)", x=0.01, ha="left", fontsize=14)
fig.tight_layout(rect=(0, 0, 1, 0.92))
lc_m, nl_m, nl_w = ST[("lc", "step_median_ms")], ST[("nolc", "step_median_ms")], ST[("nolc", "wall_s")]
save(fig, "F13", "F13_L_compute_cost.png", "L: per-update solve time and wall time (diagnostic)",
     "DIAGNOSTIC (not a pre-registered metric)",
     f"Per-replay cost of the keyframe FGO (30 Hz keyframes, retained history), T_A_r1–r3, from the CURRENT outputs (FGO-only re-run, "
     f"2026-10-10): median solve time LC {rng(lc_m, 1)} ms, no-LC {rng(nl_m, 1)} ms; no-LC p99 {rng(ST[('nolc', 'step_p99_ms')], 0)} ms; no-LC "
     f"wall time {rng(nl_w, 0)} s (numbers.md §16.3, restated 2026-10-11; the first final re-run's LC 36–41, no-LC 47–54 ms, wall "
     "9,868–11,175 s are superseded). Diagnostic only; results unaffected. Workstation Python with six parallel jobs: says nothing about "
     "onboard feasibility. Replaces the per-1000-keyframe curve, whose logs pre-date the final re-runs.",
     "~/thesis_data/trials/T_A_r{1,2,3}/lc_fgo_{lc,nolc}_t245/stats.json (mtime 2026-10-10 19:00–21:35)",
     "§16.3 'Computational cost' bullets (DIAGNOSTIC)",
     replaces="plots/supervisor_2026-10-08/fig15_L_compute_cost.png (NOT REGENERATED: its progress logs eval/results/expL/logs/ pre-date the final re-runs)",
     note="numbers.md §16.3 restated 2026-10-11 (pack flag 1); the earlier mismatch was numbers.md staleness, not a plotting error.")

# =============================================================================================== F14 H tag experiment
HJ = lambda t: L(f"expH/{t}.json")
S1 = ["s1_r1", "s1_r2", "s1_r3"]; S1F = ["s1far_r1", "s1far_r2", "s1far_r3b"]
S2V = ["s2v2_r1", "s2v2_r2", "s2v2_r3"]; S2O = ["s2_r1", "s2_r2", "s2_r3"]
S3V = ["s3v2_r1", "s3v2_r2", "s3v2_r3"]; S3O = ["s3_r1", "s3_r2", "s3_r3"]
LOSS = ["5 s hover", "15 s hover", "30 s hover", "~7 s during a move"]


def drifts(trs, key, metric="eff"):
    out = [[], [], [], []]
    for t in trs:
        for i, lo in enumerate(HJ(t)["losses"]):
            v = lo[key]
            out[i].append(1e3 * (v["effective"]["drift_m"] if metric == "eff" else v["drift_end_m"]))
    return out


GROUPS = [  # (estimator, mode, data, style)
    ("EKF3", "flying", drifts(S1 + S1F, "EKF3"), "filled"),
    ("EKF3", "shadow", drifts(S2V + S3V, "EKF3"), "open"),
    ("UKF", "shadow", drifts(S1 + S1F, "UKF"), "open"),
    ("UKF", "flying", drifts(S2V, "UKF_port"), "filled"),
    ("UKF", "flying (old port, jitter)", drifts(S2O, "UKF_port"), "faint"),
    ("FGO", "shadow", drifts(S1 + S1F, "FGO"), "open"),
    ("FGO", "flying", drifts(S3V, "FGO_flying"), "filled"),
    ("FGO", "flying (noise fix only)", drifts(S3O, "FGO_flying"), "faint")]
fig = plt.figure(figsize=(17, 9.6))
gs = fig.add_gridspec(2, 4, height_ratios=[1, 1.15], hspace=0.42, wspace=0.28)
for li in range(4):
    ax = fig.add_subplot(gs[1, li])
    xs = []
    for gi, (est, mode, dat, sty) in enumerate(GROUPS):
        x = {"EKF3": 0, "UKF": 1, "FGO": 2}[est] + {"flying": -0.18, "shadow": 0.18}.get(mode, -0.36 if "old" in mode or "noise" in mode else 0)
        if "old" in mode or "noise" in mode:
            x = {"EKF3": 0, "UKF": 1, "FGO": 2}[est] - 0.36
        y = dat[li]
        kw = dict(marker=MK[est], s=46, zorder=3)
        if sty == "filled": ax.scatter([x] * len(y), y, color=C[est], edgecolor=SURF, linewidth=1, **kw)
        elif sty == "open": ax.scatter([x] * len(y), y, facecolor=SURF, edgecolor=C[est], linewidth=1.8, **kw)
        else: ax.scatter([x] * len(y), y, color=C[est], alpha=0.28, edgecolor="none", **kw)
    ax.set_xticks([0, 1, 2]); ax.set_xticklabels(["EKF3", "UKF", "FGO"]); ax.set_xlim(-0.6, 2.5); ax.set_ylim(0, 45)
    ax.set_title(f"tag lost: {LOSS[li]}", loc="left", fontsize=12)
    if li == 0: ax.set_ylabel("drift at re-acquisition (mm)")
# legend-only proxies
ax0 = fig.add_subplot(gs[0, 2:]); ax0.axis("off")
from matplotlib.lines import Line2D
prox = [Line2D([], [], ls="", marker="o", color=INK2, ms=8, label="filled: estimator FLYING the vehicle (closed loop)"),
        Line2D([], [], ls="", marker="o", mfc=SURF, mec=INK2, mew=1.8, ms=8, label="open: SHADOW (offline replay / passive on the same flight)"),
        Line2D([], [], ls="", marker="o", color=INK2, alpha=0.3, ms=8, label="faint (left of each group): earlier build, ablation"),
        Line2D([], [], ls="", marker=MK["EKF3"], color=C["EKF3"], ms=9, label="EKF3"),
        Line2D([], [], ls="", marker=MK["UKF"], color=C["UKF"], ms=9, label="UKF"),
        Line2D([], [], ls="", marker=MK["FGO"], color=C["FGO"], ms=9, label="FGO")]
ax0.legend(handles=prox, loc="center left", frameon=False, fontsize=11)
# hold panel (vehicle; flying only)
axh = fig.add_subplot(gs[0, :2]); HOLD = {}
for k, (lab, est, trs, sty) in enumerate((("EKF3 (S1 + S1 far)", "EKF3", S1 + S1F, "filled"), ("UKF port v2 (S2v2)", "UKF", S2V, "filled"),
                                           ("UKF port, old (S2)", "UKF", S2O, "faint"), ("FGO final (S3v2)", "FGO", S3V, "filled"),
                                           ("FGO noise fix only (S3)", "FGO", S3O, "faint"))):
    mm = [1e3 * w["mean_m"] for t in trs for w in HJ(t)["hold_windows_vehicle"]]; HOLD[lab] = mm
    kw = dict(marker=MK[est], s=46, zorder=3)
    if sty == "filled": axh.scatter([k] * len(mm), mm, color=C[est], edgecolor=SURF, **kw)
    else: axh.scatter([k] * len(mm), mm, color=C[est], alpha=0.28, edgecolor="none", **kw)
axh.set_xticks(range(5)); axh.set_xticklabels(["EKF3\n(S1, S1 far)", "UKF\n(S2v2)", "UKF old\n(S2)", "FGO\n(S3v2)", "FGO noise-only\n(S3)"], fontsize=10)
axh.set_ylabel("hold error, window mean (mm)"); axh.set_ylim(0, 12)
axh.set_title("vehicle hold error against the hold point, flying estimator (2 windows per flight)", loc="left", fontsize=12)
# checks against numbers.md §17 (S1 effective drift) and METHODOLOGY (S2v2 / S3v2 end-of-loss drift, hold)
for est, key, exp in (("EKF3", "EKF3", ["13–27", "6–25", "3–11", "7–31"]), ("UKF", "UKF", ["11–19", "5–22", "4–9", "8–19"]),
                      ("FGO", "FGO", ["9–18", "4–20", "1–8", "0.5–8"])):
    dd_ = drifts(S1, key)
    got = [rng(x, 0) if not (est == "FGO" and i == 3) else f"{min(x):.1f}–{max(x):.0f}" for i, x in enumerate(dd_)]
    check(f"S1 {est} {'flying' if est == 'EKF3' else 'shadow'} drift 5/15/30/move (mm, effective)", " | ".join(got), " | ".join(exp), "numbers.md §17 table")
s1h = [1e3 * w["mean_m"] for t in S1 for w in HJ(t)["hold_windows_vehicle"]]; s1x = [1e3 * w["max_m"] for t in S1 for w in HJ(t)["hold_windows_vehicle"]]
check("S1 hold mean / max (mm)", f"{np.mean(s1h):.0f} / {rng(s1x, 0)}", "8 / 16–25", "numbers.md §17 S1 table")
for nm, trs, key, exp in (("S2v2", S2V, "UKF_port", "5/7/8 | 19/7/26 | 6/10/10 | 26/4/5"), ("S3v2", S3V, "FGO_flying", "13/20/17 | 7/25/27 | 22/15/9 | 17/11/18")):
    de = drifts(trs, key, "end")
    check(f"{nm} flying end-of-loss drift r1/r2/r3 (mm)", " | ".join("/".join(f"{x:.0f}" for x in row) for row in de), exp, "METHODOLOGY S2/S3 RE-FLY sections")
check("S2v2 hold mean / max (mm)", f"{rng(HOLD['UKF port v2 (S2v2)'], 1)} / {rng([1e3 * w['max_m'] for t in S2V for w in HJ(t)['hold_windows_vehicle']], 0)}",
      "6.1–7.4 / 17–21", "METHODOLOGY S2 RE-FLY")
check("S3v2 hold mean / max (mm)", f"{rng(HOLD['FGO final (S3v2)'], 1)} / {rng([1e3 * w['max_m'] for t in S3V for w in HJ(t)['hold_windows_vehicle']], 0)}",
      "8.1–9.0 / 18–28", "METHODOLOGY S3 RE-FLY")
lock = [lo[k]["lockout"] for t in S1 + S1F + S2V + S3V for lo in HJ(t)["losses"] for k in lo if isinstance(lo[k], dict) and "lockout" in lo[k]]
check("lockouts in any loss", sum(bool(x) for x in lock), 0, "numbers.md §17 (P-H7 PASS); METHODOLOGY S2v2/S3v2")
_hc = [v for k, v in L("expH/h_comparative_2026-10-11.json")["sets"].items() if k.startswith("re-flown")][0]
check("H comparative on S2v2/S3v2 (H-H2; P-H3; H-H4 15 s; H-H4 5 s)",
      "; ".join(_hc["criteria"][k].split()[0] for k in ("H-H2", "P-H3", "H-H4 (15 s)", "H-H4 (5 s)")),
      "FAIL; FAIL; FAIL; FAIL", "numbers.md §17.2 (computed 2026-10-11, PENDING ruling)")
check("S2v2 / S3v2 run-mean hold error (mm)",
      " / ".join(rng([r["hold_mean_mm"] for r in _hc[e]], 1) for e in ("UKF", "FGO")), "6.4–7.1 / 8.3–8.6", "numbers.md §17.2 table")
fig.suptitle("Experiment H (marker-relative hold, wall tag): hold error and drift per tag-loss duration, shadow and flying", x=0.01, ha="left", fontsize=15)
save(fig, "F14", "F14_H_tag_loss_drift.png", "H: hold error and tag-loss drift per loss duration, EKF3 / UKF / FGO, shadow and flying",
     "DESCRIPTIVE (per-flight values; pre-registered bands all PASS)",
     "Bottom: drift at re-acquisition after each tag loss (5, 15, 30 s in the hover; ~7 s during a move), per flight, in mm, EFFECTIVE metric "
     "(from the last fix to the first returning fix; numbers.md §17's metric). Filled = the estimator flying the vehicle: EKF3 in S1 (near "
     "spawn, r1–r3) and the S1 far-spawn re-fly (r1, r2, r3b); the UKF port in S2v2 (jitter-corrected); the C++ FGO in S3v2 (noise fix + "
     "gated yaw cap; OLD priors). Open = shadow: the UKF and FGO replayed offline on the S1 flights (final re-runs), and EKF3 running passively "
     "on the S2v2/S3v2 flights. Faint = earlier builds (S2 old UKF port with jitter; S3 FGO noise fix only), shown as ablations. Every value is "
     "inside its pre-registered band (UKF ≤ 100 / 200 / 400 / 300 mm, FGO ≤ 50 / 100 / 200 / 150 mm); no lockout (P-H7 PASS). The shadows "
     "now drift at EKF3's scale: \"there is no gap between the shadow and the flying estimators\" (ruling 6; claim 26). Top: vehicle hold "
     "error (window means). The comparative criteria H-H2 / P-H3 / H-H4 were adjudicated on S2/S3 (old builds, all FAIL); computed on "
     "S2v2/S3v2 on 2026-10-11 (numbers.md §17.2) they give the SAME verdicts (all FAIL), PENDING a user ruling. Each estimator flew its own flights: pairing is by run index, not "
     "trajectory. METHODOLOGY quotes S2v2/S3v2 with the end-of-loss metric; the two differ by ≤ 5 mm (index cross-check).",
     "eval/results/expH/s1_r{1,2,3}.json, s1far_r{1,2,3b}.json, s2v2_r*.json, s2_r*.json, s3v2_r*.json, s3_r*.json "
     "(losses[*].<est>.effective.drift_m, drift_end_m; hold_windows_vehicle)",
     "§17 (S1 table; tag-loss drift table; P-H5, P-H7; ruling 6 note); §17.1 (S2/S2v2/S3/S3v2); §17.2 (comparative criteria, PENDING); claims 25, 26",
     note="NEW figure. The S1-far shadows have no numbers.md rows (METHODOLOGY only).")

# =============================================================================================== F15 closed-loop summary (two pages)
def setb(trs):
    B = [L(f"closed_loop_{t}.json")["B"] for t in trs]
    r_ = lambda f: f"{min(f(b) for b in B):.2f}–{max(f(b) for b in B):.2f}"
    js = [L(f"closed_loop_{t}.json") for t in trs]
    s2 = all(j.get("S2", {}).get("pass", True) for j in js)
    fails = [f"r{i + 1} {k}" for i, b in enumerate(B) for k in ("B1", "B2", "B3", "B4", "B5") if not b[k]["pass"]]
    return (f"{sum(b['pass'] and j.get('S2', {}).get('pass', True) for b, j in zip(B, js))}/3" + (f" ({', '.join(fails)} FAIL)" if fails else ""),
            r_(lambda b: b["B2"]["max_abs_x_cruise_m"]) + " m", r_(lambda b: b["B3"]["p95_deg"]) + "° / " + r_(lambda b: b["B3"]["max_deg"]) + "°",
            r_(lambda b: b["B4"]["max_abs_lat_speed_mps"]) + " m/s")


def seta(tr, win):
    if tr is None:
        return "not flown"
    c0, ct = cl_meta(tr); t_ = ct["t_rel_cruise_s"]
    return f"west +{t_:.1f} s, {'PASS' if win[0] <= t_ <= win[1] else 'MISS'} [+{win[0]}, +{win[1]}]"


rowsA = [
    ("EKF3, full", "EKF3 + ExtNav yaw", seta("cl_a_tex", WIN["EKF3"]), *setb([f"cl_bcpp_tex_r{i}" for i in (1, 2, 3)])),
    ("EKF3, full (Python bridge)", "as above", "—", *setb([f"cl_b_tex_r{i}" for i in (1, 2, 3)])),
    ("EKF3, half", "as above", seta("cl_a_tex_half", WIN["EKF3"]) + " (D21)", *setb([f"cl_bcpp_tex_r{i}_half" for i in (1, 2, 3)])),
    ("UKF, full", "port, pre-jitter fix", seta("cl_ukf_a_tex", WIN["UKF"]), *setb([f"cl_ukf_b_tex_r{i}" for i in (1, 2, 3)])),
    ("UKF, half", "port, pre-jitter fix", seta("cl_ukf_a_tex_half", WIN["UKF"]), *setb([f"cl_ukf_b_tex_r{i}_half" for i in (1, 2, 3)])),
    ("UKF v2, half", "port, jitter-corrected", seta("cl_ukf_a_tex_half_v2", WIN["UKF"]), *setb([f"cl_ukf_b_tex_r{i}_half_v2" for i in (1, 2, 3)])),
    ("FGO, half (hard gate)", "old noise model", seta("cl_fgo_a_tex_half", WIN["FGO"]), *setb([f"cl_fgo_b_tex_r{i}_half" for i in (1, 2, 3)])),
    ("FGO, half (robust)", "old noise model", "not flown", *setb([f"cl_fgo_b_robust_tex_r{i}_half" for i in (1, 2, 3)])),
    ("FGO v2, half", "noise fix only (ablation)", seta("cl_fgo_a_tex_half_v2", WIN["FGO"]), *setb([f"cl_fgo_b_tex_r{i}_half_v2" for i in (1, 2, 3)])),
    ("FGO v3, half", "final: noise fix + gated cap", seta("cl_fgo_a_tex_half_v3", WIN["FGO"]), *setb([f"cl_fgo_b_tex_r{i}_half_v3" for i in (1, 2, 3)])),
]
check("EKF3 half contact MISS", rowsA[2][2].split(",")[1].strip().split()[0], "MISS", "numbers.md §15 (D21)")
check("UKF half orig heading pass", rowsA[4][3].split()[0], "2/3", "numbers.md §15 (r3 B4)")
check("UKF v2 / FGO v3 heading pass", f"{rowsA[5][3]} / {rowsA[9][3]}", "3/3 / 3/3", "numbers.md §15 (re-flown sets)")
check("FGO v2 heading pass (ablation)", rowsA[8][3], "3/3", "numbers.md §15 (re-flown sets)")
check("FGO hard / robust heading pass (D28)", f"{rowsA[6][3]} / {rowsA[7][3]}", "3/3 / 3/3", "numbers.md §15 (D28)")
check("EKF3 full C++ / half heading pass", f"{rowsA[0][3]} / {rowsA[2][3]}", "3/3 / 3/3", "numbers.md §15")


def table_fig(rows, cols, widths, title, notes, fs=10.5, scale=2.0, h=7.6):
    fig = plt.figure(figsize=(17, h)); ax = fig.add_axes([0.01, 0.20, 0.98, 0.70]); ax.axis("off")
    tab = ax.table(cellText=[list(r) for r in rows], colLabels=cols, loc="upper left", cellLoc="left", colLoc="left", colWidths=widths)
    tab.auto_set_font_size(False); tab.set_fontsize(fs); tab.scale(1, scale)
    for (r_, c_), cell in tab.get_celld().items():
        cell.set_edgecolor(GRID); cell.set_facecolor(SURF if r_ else "#f0efec")
        if r_ == 0:
            cell.set_text_props(weight="bold"); cell.set_height(cell.get_height() * 1.6)
    for k, n in enumerate(notes):
        fig.text(0.01, 0.15 - 0.032 * k, n, fontsize=10.5, color=INK2)
    fig.suptitle(title, x=0.01, ha="left", fontsize=15)
    return fig


fig = table_fig(rowsA, ["flying estimator, speed", "build", "no heading: wall contact (window)", "with heading: B1–B5 + S2 pass",
                        "B2 max\ncross-track", "B3 yaw error\np95 / max", "B4 max\nlateral speed"],
                [0.13, 0.15, 0.21, 0.15, 0.10, 0.15, 0.11],
                "Closed-loop summary (1/2): the textured corridor, all three estimators flying the vehicle",
                ["Windows: EKF3 [+155, +215] s, UKF [+146, +218] s, FGO [+145, +196] s (pre-registered). n = 1 per no-heading cell; closed-loop run-to-run variability is unmeasured. "
                 "No cross-speed comparison is claimed (D21).",
                 "ALL flown FGO results used the OLD FGO priors (initial yaw σ 1e-3 rad, roll/pitch 2°); no re-fly before the freeze. B4 failures (UKF half r3 0.296 m/s) and the FGO v3 r3 "
                 "near-miss (0.246) are D22,",
                 "a shared sensor-pipeline limitation (flow validity on feature count only). numbers.md §15 carries the original sets and the v2/v3 re-flights "
                 "(rows added 2026-10-11)."], fs=10, scale=2.1, h=8.0)
save(fig, "F15a", "F15a_closed_loop_summary_corridor.png", "Closed-loop summary (1/2): corridor sets, every flown build",
     "SUMMARY (pre-registered criteria)",
     "What flew in the textured corridor and how it scored, computed from the closed-loop score files. Original sets and the corrected "
     "re-flights are both shown (labelled by build). The UKF v2 set passes 3/3 where the original failed r3 on B4; the FGO v2 (noise fix only) "
     "and v3 (final) sets pass 3/3, with the heading excursions of the original (B3 max 1.28–1.88°) gone and a small steady offset (B3 mean "
     "0.19–0.24°). The per-heading weight comparison is CHANGED: FGO ≈ 1.3–1.4 % on the v3 flights, UKF side OPEN, no ratio stated (claim 15).",
     "eval/results/closed_loop_<trial>.json for cl_a_tex, cl_b_tex_r*, cl_bcpp_tex_r*(_half), cl_a_tex_half, cl_ukf_a_tex(_half)(_v2), "
     "cl_ukf_b_tex_r*(_half)(_v2), cl_fgo_a_tex_half(_v2)(_v3), cl_fgo_b_tex_r*_half(_v2)(_v3), cl_fgo_b_robust_tex_r*_half",
     "§15 rows (contacts, B1–B5 counts, B2, B3, re-flown sets); claim 14",
     replaces="plots/supervisor_2026-10-01/fig9_closed_loop_summary.png (FLAGGED: lacks the re-flights; caption '~5x per-heading weight' superseded)")


def hsum(trs, key):
    hm = [1e3 * w["mean_m"] for t in trs for w in HJ(t)["hold_windows_vehicle"]]
    dr = [1e3 * lo[key]["effective"]["drift_m"] for t in trs for lo in HJ(t)["losses"]]
    rl = [lo[key]["effective"]["relock_after_first_fix_s"] for t in trs for lo in HJ(t)["losses"]]
    lk = sum(lo[key]["lockout"] for t in trs for lo in HJ(t)["losses"])
    return f"{min(hm):.1f}–{max(hm):.1f} mm", f"{min(dr):.0f}–{max(dr):.0f} mm", f"{min(rl):+.3f}…{max(rl):+.3f} s", f"{lk}"


rowsH = [("S1, EKF3 flying (near spawn)", "unmodified EKF3", *hsum(S1, "EKF3")),
         ("S1 far re-fly, EKF3 flying", "unmodified EKF3", *hsum(S1F, "EKF3")),
         ("S2, UKF port flying", "port, pre-jitter fix", *hsum(S2O, "UKF_port")),
         ("S2v2, UKF port flying", "port, jitter-corrected", *hsum(S2V, "UKF_port")),
         ("S3, C++ FGO flying", "noise fix only (ablation)", *hsum(S3O, "FGO_flying")),
         ("S3v2, C++ FGO flying", "final; OLD priors", *hsum(S3V, "FGO_flying"))]


def sflag(f):
    j = HJ(f); out = []
    for k in ("S-A1", "S-A2", "S-A3", "S-A4_single_landing"):
        if k in j and isinstance(j[k], dict) and "PASS" in j[k]:
            out.append(f"{k[:4]} {'PASS' if j[k]['PASS'] else 'FAIL'}")
    return ", ".join(out) if out else "see METHODOLOGY"


rowsS = [("UKF (a) TFAIL", "safety_ukf_a_v2 (jitter-corrected)", sflag("safety_ukf_a_v2"), "ukf_a: S-A2, S-A3 FAIL → ukf_a_rerun ALL PASS"),
         ("UKF (b) KILL", "safety_ukf_b_v2 (jitter-corrected)", sflag("safety_ukf_b_v2"), "S-A2 as worded: 5.75 s vs 5.5 s (relay drain); ukf_b PASS"),
         ("FGO (a)", "safety_fgo_a_v3 (final; OLD priors)", sflag("safety_fgo_a_v3"), "fgo_a PASS; fgo_a_v2 PASS"),
         ("FGO (b) KILL", "safety_fgo_b_v3 (final; OLD priors)", sflag("safety_fgo_b_v3"), "fgo_b S-A3 FAIL → fgo_b2, fgo_b_v2 PASS"),
         ("EKF3 reference", "safety_ekf3_ref", "drift 1.40 m (prediction ≤ 0.5 m WRONG); no breach", "—")]
check("UKF (b) v2 S-A2 fails as worded", HJ("safety_ukf_b_v2")["S-A2"]["PASS"], False, "METHODOLOGY 'UKF safety (b) RE-TEST'")
check("UKF (b) v2 S-A2 delay (s)", f"{HJ('safety_ukf_b_v2')['S-A2']['text_delay_s']:.2f}", "5.75", "METHODOLOGY")
check("FGO a_v3 / b_v3 / UKF a_v2 all S-A pass", all(HJ(f)[k]["PASS"] for f in ("safety_fgo_a_v3", "safety_fgo_b_v3", "safety_ukf_a_v2")
                                                   for k in ("S-A1", "S-A2", "S-A3", "S-A4_single_landing") if k in HJ(f)), True, "METHODOLOGY RESULT sections")
check("S2v2 / S3v2 lockouts", f"{rowsH[3][5]} / {rowsH[5][5]}", "0 / 0", "METHODOLOGY")
fig = plt.figure(figsize=(17, 9.0))
for (rows, cols, widths, y0, hh, ttl) in (
        (rowsH, ["H flight set", "build", "hold error (window means)", "tag-loss drift (effective, all losses)", "re-lock after first fix", "lockouts"],
         [0.20, 0.17, 0.15, 0.20, 0.17, 0.07], 0.50, 0.40, "Experiment H, wall-tag hold (3 flights per set)"),
        (rowsS, ["safety test", "final run (2 m-clearance hold)", "final result", "history"], [0.12, 0.24, 0.30, 0.32], 0.08, 0.34,
         "Safety tests (failure injected in the hold; the FC must declare position lost and land)")):
    ax = fig.add_axes([0.01, y0, 0.98, hh]); ax.axis("off"); ax.set_title(ttl, loc="left", fontsize=13)
    tab = ax.table(cellText=[list(r) for r in rows], colLabels=cols, loc="upper left", cellLoc="left", colLoc="left", colWidths=widths)
    tab.auto_set_font_size(False); tab.set_fontsize(10); tab.scale(1, 1.9)
    for (r_, c_), cell in tab.get_celld().items():
        cell.set_edgecolor(GRID); cell.set_facecolor(SURF if r_ else "#f0efec")
        if r_ == 0: cell.set_text_props(weight="bold")
fig.text(0.01, 0.05, "H verdicts: H-H1 PASS on every set; P-H5 and P-H7 PASS; P-H6 FAILS as worded (occluder render lag); H-H2, P-H3 and H-H4 FAIL as adjudicated on "
         "S2/S3 (old builds); computed on S2v2/S3v2 (numbers.md §17.2): same verdicts, PENDING a user ruling.", fontsize=10.5, color=INK2)
fig.text(0.01, 0.02, "All drift bands PASS for every set; the jump criterion as worded fails in most losses (drift below the hold's own step noise). Flown FGO = OLD priors.",
         fontsize=10.5, color=INK2)
fig.suptitle("Closed-loop summary (2/2): marker-relative hold (H) and the safety tests", x=0.01, ha="left", fontsize=15)
save(fig, "F15b", "F15b_closed_loop_summary_H_safety.png", "Closed-loop summary (2/2): H hold sets and the safety tests",
     "SUMMARY (pre-registered criteria)",
     "Verdicts: H-H1 PASS on every set; P-H5 and P-H7 PASS; P-H6 FAILS as worded; H-H2, P-H3 and H-H4 FAIL as adjudicated on S2/S3 (old "
     "builds); computed on S2v2/S3v2 on 2026-10-11 they give the same verdicts (numbers.md §17.2, PENDING a user ruling). H: per flight set, the vehicle hold error, the effective tag-loss drift over all four losses, the re-lock time after the first returning "
     "fix (negative for the UKF: event-time stamping) and lockouts, computed from the H score files. Safety: the final run of each test and "
     "its history. UKF (b) fails S-A2 as worded (the FC declared position lost 5.75 s after the kill against a 5.5 s bound; 0.71 s of "
     "relay drain after the SIGKILL; the watcher had already commanded the landing). The EKF3 reference drifted 1.40 m against a "
     "prediction of ≤ 0.5 m (the prediction was wrong; no breach). The FGO safety re-tests flew the final FGO with the OLD priors.",
     "eval/results/expH/s1*_r*.json, s2*_r*.json, s3*_r*.json; expH/safety_*.json", "§17 (S1), §17.1 (S2/S3 sets), §17.2 (comparative criteria, PENDING); §15 safety rows; claim 25",
     note="numbers.md rows added 2026-10-11 (pack flags 2, 3).")


# =============================================================================================== tables T1, T2 (markdown -> text pages)
def md_table(path, start_pat=None):
    rows = []; txt = open(path).read()
    for ln in txt.splitlines():
        if ln.startswith("|") and not re.match(r"^\|[-\s|]+\|$", ln):
            rows.append([c.strip() for c in re.split(r"(?<!\\)\|", ln.strip()[1:-1])])
    return rows, txt


def clean(s):
    return re.sub(r"\*\*|`", "", s).replace("\\|", "|")


def text_pages(P, title, header, rows, widths, notes=(), fs=8.2, src=""):
    """Paginated table: each column wrapped to its width (characters); rows advance until the page fills."""
    lh = fs * 1.32 / 72 / 8.27   # line height in figure fraction (A4 landscape, 8.27 in high)
    def newpage(k):
        fig = plt.figure(figsize=(11.69, 8.27))
        fig.text(0.03, 0.965, f"{title}" + (f" (continued, page {k})" if k > 1 else ""), fontsize=13, weight="bold", va="top")
        x = 0.03; y = 0.925
        for h, w in zip(header, widths):
            fig.text(x, y, h, fontsize=fs + 0.5, weight="bold", va="top"); x += w / sum(widths) * 0.94
        return fig, y - 2.0 * lh
    k = 1; fig, y = newpage(k)
    for row in rows:
        cells = [textwrap.wrap(clean(c), max(8, int(w * 0.86))) or [""] for c, w in zip(row, widths)]
        n = max(len(c) for c in cells)
        if y - n * lh < 0.07:
            if src: fig.text(0.03, 0.03, src, fontsize=7.5, color=INK2)
            P.savefig(fig); plt.close(fig); k += 1; fig, y = newpage(k)
        fig.add_artist(Line2D([0.03, 0.97], [y + 0.4 * lh, y + 0.4 * lh], color=GRID, lw=0.6, transform=fig.transFigure))
        x = 0.03
        for c, w in zip(cells, widths):
            fig.text(x, y, "\n".join(c), fontsize=fs, va="top", linespacing=1.25); x += w / sum(widths) * 0.94
        y -= (n + 0.6) * lh
    for nt in notes:
        lines = textwrap.wrap(clean(nt), 175)
        if y - len(lines) * lh < 0.07:
            if src: fig.text(0.03, 0.03, src, fontsize=7.5, color=INK2)
            P.savefig(fig); plt.close(fig); k += 1; fig, y = newpage(k)
        fig.text(0.03, y, "\n".join(lines), fontsize=fs, va="top", color=INK2); y -= (len(lines) + 0.8) * lh
    if src: fig.text(0.03, 0.03, src, fontsize=7.5, color=INK2)
    P.savefig(fig); plt.close(fig)
    return k


claims_path = os.path.join(ROOT, "docs", "thesis", "headline_claims_before_after.md")
corr_path = os.path.join(ROOT, "docs", "thesis", "final_results_pack_corrections.md")
crow, ctxt = md_table(claims_path)
claims_hdr, claims_rows = crow[0], crow[1:]
counts = {s: sum(r[2] == s for r in claims_rows) for s in ("HOLDS", "CHANGED", "WITHDRAWN")}
CHK = []
check("claims table row count", len(claims_rows), 36, "headline_claims_before_after.md 'Counts' line")
check("claims HOLDS / CHANGED / WITHDRAWN", f"{counts['HOLDS']} / {counts['CHANGED']} / {counts['WITHDRAWN']}", "17 / 16 / 3", "headline_claims 'Counts' line")
T1_CHECKS = CHK
xrow, xtxt = md_table(corr_path)
corr_hdr, corr_rows = xrow[0], xrow[1:]
CHK = []
check("corrections listed", len(corr_rows), 18, "final_results_pack_corrections.md")
T2_CHECKS = CHK; CHK = []

# =============================================================================================== PDF
def caption_page(P, it):
    img = plt.imread(it["png"]); h, w = img.shape[:2]
    fig = plt.figure(figsize=(11.69, 8.27))
    top = 0.955; avail = 0.62; aw = 0.94; ah = aw * (h / w) * 11.69 / 8.27
    if ah > avail: aw *= avail / ah; ah = avail
    ax = fig.add_axes([0.5 - aw / 2, top - ah, aw, ah]); ax.imshow(img); ax.axis("off")
    y = top - ah - 0.015
    status = it["status"]
    t = "\n".join(textwrap.wrap(f"{it['id']}. {it['title']}  —  {it['kind']}  —  status: {status}", 125))
    fig.text(0.03, y, t, fontsize=10.5, weight="bold", va="top"); y -= 0.022 * (t.count("\n") + 1) + 0.006
    cap = "\n".join(textwrap.wrap(clean(it["caption"]), 175)); fig.text(0.03, y, cap, fontsize=8.6, va="top"); y -= 0.0185 * (cap.count("\n") + 1) + 0.008
    nchk = len(it["checks"]); okc = sum(c[4] for c in it["checks"])
    src = "\n".join(textwrap.wrap(f"Source: script {SCRIPT} (commit {COMMIT}); inputs: {it['inputs']}. Supports numbers.md: {it['rows']}. "
                                  f"Checks against numbers.md/METHODOLOGY: {okc}/{nchk} match" + (" (see index for the mismatch)" if okc < nchk else "") + ".", 190))
    fig.text(0.03, max(y, 0.02 + 0.0165 * (src.count("\n") + 1)), src, fontsize=7.4, va="top", color=INK2)
    P.savefig(fig); plt.close(fig)


with PdfPages(PDF) as P:
    fig = plt.figure(figsize=(11.69, 8.27))
    fig.text(0.06, 0.86, "Final results pack", fontsize=26, weight="bold")
    fig.text(0.06, 0.80, "Indoor UAV state estimation: EKF3, UKF and FGO under degraded sensing (simulation results, FROZEN 2026-10-11)", fontsize=13)
    intro = ("Regenerated from the restated results: the final consolidated re-run (425e824) and the FGO-only re-run (819caab), plus the re-flown "
             "closed-loop and H flights. Every figure page carries its caption, its status, its source (script and input files), the numbers.md "
             "rows it supports, and how many of its plotted values were checked against numbers.md / METHODOLOGY. Conventions: evo = evo -a (cruise), "
             "metres; † = a runaway magnitude from a diverging estimate (order of magnitude only, not bit-reproducible across BLAS builds); "
             "textured means at n = 3 are descriptive only. Flown FGO results used the OLD FGO priors (initial yaw σ 1e-3 rad, roll/pitch 2°). "
             f"Built by {SCRIPT} at commit {COMMIT}. Index: docs/thesis/final_results_pack_index.md.")
    fig.text(0.06, 0.74, "\n".join(textwrap.wrap(intro, 140)), fontsize=10.5, va="top")
    y = 0.52; fig.text(0.06, y, "Contents", fontsize=13, weight="bold"); y -= 0.03
    for it in ITEMS:
        fig.text(0.07, y, f"{it['id']}  {it['title']}  [{it['status']}]", fontsize=9.5); y -= 0.021
    fig.text(0.07, y, "T1  Headline claims: before against after the final re-runs (36 rows)", fontsize=9.5); y -= 0.021
    fig.text(0.07, y, "T2  Corrections summary: what was wrong, how it was found, its effect (18 rows)", fontsize=9.5)
    P.savefig(fig); plt.close(fig)
    for it in ITEMS:
        caption_page(P, it)
    text_pages(P, "T1. Headline claims, before against after the final re-runs", ["#", "claim before", "status", "evidence now"],
               [[r[0], r[1], r[2], r[3]] for r in claims_rows], [5, 60, 15, 105],
               notes=[ln for ln in ctxt.split("\n\n") if ln.startswith("**Counts") or ln.startswith("**0.1 rad")],
               src="Source: docs/thesis/headline_claims_before_after.md (rendered verbatim, markdown emphasis removed); values: docs/thesis/numbers.md.")
    text_pages(P, "T2. Corrections summary", ["#", "correction", "scope", "what was wrong", "how found", "effect on headline numbers", "attribution"],
               [r for r in corr_rows], [3, 22, 9, 40, 27, 50, 38],
               notes=[p for p in xtxt.split("\n\n") if p.startswith("**Attribution rule") or p.startswith("**What the partial")], fs=7.2,
               src="Source: docs/thesis/final_results_pack_corrections.md (values quoted from METHODOLOGY.md, numbers.md, eval/results/*; nothing recomputed).")
print("wrote", PDF)

# =============================================================================================== index
HIST = [
    ("plots/supervisor_2026-10-01/fig1_closed_loop_paths.png", "F01", "CURRENT values (same flights); superseded in the pack by F01"),
    ("plots/supervisor_2026-10-01/fig2_closed_loop_heading_error.png", "F02", "CURRENT values (same flights); superseded in the pack by F02"),
    ("plots/supervisor_2026-10-01/fig3_offline_textured_no_heading.png", "F03", "FLAGGED-superseded: 'confirmed EKF3 < FGO' (WITHDRAWN), UKF median 5.34, pre-final values"),
    ("plots/supervisor_2026-10-01/fig4_offline_with_heading_C0.png", "F04", "FLAGGED-superseded: pre-final heading-arm values; 'UKF lower yaw error 5/6'"),
    ("plots/supervisor_2026-10-01/fig5_drift_decomposition.png", "F05", "FLAGGED-superseded: pre-final decomposition"),
    ("plots/supervisor_2026-10-01/fig6_blank_flow_loss.png", "F06", "FLAGGED-superseded: pre-final runaway curves"),
    ("plots/supervisor_2026-10-01/fig7_corrections_table.png", "T2", "FLAGGED-superseded: stops at D15/D27; 'confirmatory −0.69 [−1.16, −0.21]' WITHDRAWN"),
    ("plots/supervisor_2026-10-01/fig8_f1_robust_tradeoff.png", "F07", "FLAGGED-superseded: 'UKF lower worst-case yaw on all 6'"),
    ("plots/supervisor_2026-10-01/fig9_closed_loop_summary.png", "F15a", "FLAGGED-superseded: lacks the v2/v3 re-flights; '~5x per-heading weight' (claim 15 CHANGED)"),
    ("plots/supervisor_2026-10-01/fig10_closed_loop_paths_half.png", "F08", "FLAGGED-superseded: lacks the UKF v2 / FGO v3 re-flights"),
    ("plots/supervisor_2026-10-08/fig11_T_hindsight_gain_vs_gap.png", "F09", "FLAGGED-superseded: pre-final FGO values"),
    ("plots/supervisor_2026-10-08/fig12_T_rmse_by_condition.png", "F10", "FLAGGED-superseded: 'EKF3 lowest live in D' (claim 18 CHANGED), '11–34 mm'"),
    ("plots/supervisor_2026-10-08/fig13_O_indoor_hindsight.png", "F11", "FLAGGED-superseded: FGO batch '0.33 m', 'P-O3 FAIL', 'cap-free 0.97 m'"),
    ("plots/supervisor_2026-10-08/fig14_L_lap_by_lap.png", "F12", "FLAGGED-superseded: '4.5–5.5×', pre-final L values"),
    ("plots/supervisor_2026-10-08/fig15_L_compute_cost.png", "F13", "NOT REGENERATED: per-1000-keyframe logs (eval/results/expL/logs/, 2026-10-08) pre-date the final re-runs; replaced by the per-replay summary F13"),
    ("plots/supervisor_2026-10-0{1,8}/figures.pdf", "this PDF", "FLAGGED-superseded as a set (historical record of the supervisor meetings; kept unchanged)"),
    ("plots/*.png (top level: ate_by_condition, nomag_*, textured_*, ekf3_diag_*, ukf_diag_*, alongtrack_vs_travel, pn_vs_truey, "
     "ekf3_diag_4_flowresid_tilt; last committed 2026-08-01), plots/lateral_diag/ (2026-09-23), plots/phase5/ (2026-09-29)", "—",
     "NOT REGENERATED, FLAGGED-superseded: pre-correction diagnostics (before the consolidated re-fly / final re-runs); their estimator values must "
     "not be quoted. plots/inlier_ratio_transition.png and the plots/fwd_camera/ frame grids are sensor-level/render records, unaffected"),
    ("plots/plainwall_trace/, plots/d22_plateau/ (2026-10-10)", "—",
     "NOT REGENERATED, not superseded: recent single-purpose diagnostics (the D18 plain-wall trace cited in numbers.md §6.6/§18; the D22 plateau "
     "diagnostic). Kept as is"),
]
with open(INDEX, "w") as f:
    f.write("# Final results pack: index (2026-10-11)\n\n")
    f.write(f"PDF: `docs/thesis/final_results_pack.pdf`. Figures: `plots/final_results_pack/`. Built by `{SCRIPT}` at commit `{COMMIT}` "
            "(run with `~/venv-evo/bin/python`; analysis only, no replays). Tables: T1 from `docs/thesis/headline_claims_before_after.md`, "
            "T2 from `docs/thesis/final_results_pack_corrections.md`.\n\n")
    f.write("**Status key:** CURRENT = regenerated from the restated results and every check matches numbers.md / METHODOLOGY; "
            "FLAGGED = shows superseded values or a check mismatches (reason given); NOT REGENERATED = kept as is, reason given.\n\n")
    f.write("## Pack contents\n\n| id | figure / table | status | source (script; inputs) | numbers.md rows supported | checks |\n|---|---|---|---|---|---|\n")
    for it in ITEMS:
        okc = sum(c[4] for c in it["checks"])
        f.write(f"| {it['id']} | `{os.path.relpath(it['png'], ROOT)}`: {it['title']} | {it['status']} | `{SCRIPT}`; {it['inputs']} | {it['rows']} | "
                f"{okc}/{len(it['checks'])} |\n")
    f.write(f"| T1 | Headline claims before/after (36 rows) | CURRENT | rendered by `{SCRIPT}` from `docs/thesis/headline_claims_before_after.md` | "
            f"all rows cited in its evidence column | {sum(c[4] for c in T1_CHECKS)}/{len(T1_CHECKS)} |\n")
    f.write(f"| T2 | Corrections summary (18 rows) | CURRENT | `docs/thesis/final_results_pack_corrections.md` (quotes METHODOLOGY, numbers.md, eval/results) | "
            f"§6.1, §6.5, §6.6, §15, §16.2, §17, §18 | {sum(c[4] for c in T2_CHECKS)}/{len(T2_CHECKS)} |\n\n")
    f.write("## FLAGGED items\n\n")
    fl = [it for it in ITEMS if it["status"] != "CURRENT"]
    for it in fl:
        bad = [c for c in it["checks"] if not c[4]]
        f.write(f"- **{it['id']}** ({it['status']}): " + "; ".join(f"{c[0]}: computed `{c[1]}`, expected `{c[2]}` ({c[3]})" for c in bad) +
                (f". {it['note']}" if it["note"] else "") + "\n")
    f.write("- **RESOLVED 2026-10-11 (pack flags 1–2):** numbers.md §16.3 cost bullets restated from the FGO-only re-run outputs; numbers.md §15 "
            "now carries the UKF v2 contact (+165.9 s) and the UKF v2 / FGO v2 (ablation) / FGO v3 heading sets (all 3/3), plus the safety-test rows "
            "(handover `docs/handovers/2026-10-11_pack_flags_fixed.md`).\n")
    f.write("- **Experiment H comparative criteria (H-H2, P-H3, H-H4): COMPUTED on S2v2/S3v2 on 2026-10-11, PENDING a user ruling** "
            "(numbers.md §17.2; `eval/h_comparative.py`, a reduction of the stored h_score outputs). Same verdicts as the adjudicated S2/S3 set (all "
            "FAIL); wording changes only (the FGO hold is now highest, not tied with EKF3; EKF3's 15 s jump strictly smallest). S2/S2v2/S3/S3v2 rows: "
            "numbers.md §17.1. The S1-far shadows still have no numbers.md rows.\n")
    if ROUNDING:
        f.write("- **Rounding-boundary transcriptions in numbers.md (not superseded values; ≤ one unit in the last printed digit):** " +
                "; ".join(f"{r[0]}: file `{r[1]}`, numbers.md `{r[2]}`" for r in ROUNDING) + ". Accepted as matches; listed with both readings in numbers.md 'Flags: remaining' item 8 (values unchanged).\n")
    f.write("- **Historical supervisor figures** (below) carry superseded values or captions; they are kept unchanged as meeting records.\n\n")
    f.write("## Checks per figure (computed from the result files against the value typed from the cited source)\n\n")
    for it in ITEMS + [dict(id="T1", checks=T1_CHECKS, title="claims table"), dict(id="T2", checks=T2_CHECKS, title="corrections table")]:
        f.write(f"### {it['id']}: {it['title']}\n\n| check | computed | expected | source | match |\n|---|---|---|---|---|\n")
        for c in it["checks"]:
            rnd = any(r[0] == c[0] and r[1] == c[1] for r in ROUNDING)
            f.write(f"| {c[0]} | `{c[1]}` | `{c[2]}` | {c[3]} | {('yes (last-digit rounding)' if rnd else 'yes') if c[4] else '**NO**'} |\n")
        f.write("\n")
    f.write("## Historical figures (not in the pack)\n\n| file | replaced by | status |\n|---|---|---|\n")
    for a, b, c in HIST:
        f.write(f"| `{a}` | {b} | {c} |\n")
    f.write("\n## Captions\n\n")
    for it in ITEMS:
        f.write(f"### {it['id']}: {it['title']}\n\n- **Kind:** {it['kind']}\n- **Caption:** {it['caption']}\n- **Inputs:** {it['inputs']}\n"
                f"- **Replaces:** {it['replaces'] or '— (new)'}\n\n")
print("wrote", INDEX)
