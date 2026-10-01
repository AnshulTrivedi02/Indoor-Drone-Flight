#!/usr/bin/env python3
"""Supervisor-meeting figures (2026-10-01). No new experiments: every number comes from committed result files
(eval/results/*.json, docs/thesis/numbers.md) or, for curves, from the recorded flight data (bags / dataflash logs)
named per figure. Style: the dataviz skill's reference palette (validated: EKF3 slot 1 blue, FGO slot 2 orange,
UKF slot 3 aqua, all-pairs PASS; aqua < 3:1 contrast -> every series is also direct-labelled).
Output: plots/supervisor_2026-10-01/figN_*.png, figures.pdf (one figure + caption per page), INDEX.md.
Usage (venv-evo + pymavlink shim): python3 eval/figs_supervisor_2026_10_01.py"""
import json, math, os, subprocess, sys, glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from pymavlink import mavutil
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
from cruise_window import cruise_bounds
RES = os.path.join(ROOT, "eval", "results"); TD = os.path.expanduser("~/thesis_data/trials")
OUT = os.path.join(ROOT, "plots", "supervisor_2026-10-01"); os.makedirs(OUT, exist_ok=True)
COMMIT = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
C = {"EKF3": "#2a78d6", "FGO": "#eb6834", "UKF": "#1baf7a"}
INK, INK2, GRID, SURF, WALL = "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb", "#8c8b86"
plt.rcParams.update({"font.size": 14, "axes.titlesize": 16, "axes.labelsize": 14, "xtick.labelsize": 12, "ytick.labelsize": 12,
                     "legend.fontsize": 12, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
                     "text.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF, "lines.linewidth": 2,
                     "axes.spines.top": False, "axes.spines.right": False})
L = lambda f: json.load(open(os.path.join(RES, f)))
FIGS = []   # (png, title, caption, kind, sources)


def badge(fig, kind):
    col = {"CONFIRMATORY": "#1c5cab", "DESCRIPTIVE": INK2, "EXPLORATORY": "#8a5a00"}[kind.split()[0]]
    fig.text(0.995, 0.995, kind, ha="right", va="top", fontsize=11, color=col, weight="bold")


def save(fig, name, title, caption, kind, sources):
    badge(fig, kind); p = os.path.join(OUT, name); fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
    FIGS.append((p, title, caption, kind, sources)); print("wrote", p)


ts = get_typestore(Stores.ROS2_JAZZY)
def gt_of(trial):
    g = []
    with Reader(f"{TD}/{trial}/bag") as r:
        cs = [c for c in r.connections if c.topic == "/ground_truth/pose"]
        for con, tn, raw in r.messages(connections=cs):
            m = ts.deserialize_cdr(raw, con.msgtype)
            g.append((m.header.stamp.sec + m.header.stamp.nanosec * 1e-9, m.pose.position.x, m.pose.position.y))
    return np.array(sorted(g))


def log_yaw(trial, est):
    m = mavutil.mavlink_connection(f"{TD}/{trial}/ardupilot.bin"); E, S = [], []
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
    c0, c1 = cruise_bounds(S[:, 0], Ee, N)
    un = lambda d: np.degrees(np.unwrap(np.radians(d)))
    w = E[:, 0] >= c0
    e = (un(E[w, 1]) - np.interp(E[w, 0], S[:, 0], un(S[:, 3])) + 180) % 360 - 180
    return E[w, 0] - c0, e


def cl_meta(tr):
    """(cruise start s, contact {x, y, t_rel} or None) from either closed-loop JSON schema (the scorer's, or the
    hand-written cl_ukf_a_tex.json: cruise_start_s, contact.E_m/N_m/cruise_plus_s)."""
    js = L(f"closed_loop_{tr}.json")
    c0 = js["cruise_s"][0] if "cruise_s" in js else js["cruise_start_s"]
    ct = js.get("contact")
    if ct and "t_rel_cruise_s" not in ct:
        ct = {"x": ct["E_m"], "y": ct["N_m"], "t_rel_cruise_s": ct["cruise_plus_s"]}
    return c0, ct


CL = {"EKF3_off": ["cl_a_tex"], "EKF3_on": ["cl_bcpp_tex_r1", "cl_bcpp_tex_r2", "cl_bcpp_tex_r3"],
      "UKF_off": ["cl_ukf_a_tex"], "UKF_on": ["cl_ukf_b_tex_r1", "cl_ukf_b_tex_r2", "cl_ukf_b_tex_r3"]}
WIN = {"EKF3": (155, 215), "UKF": (146, 218)}

# ------------------------------------------------------------------------------------------------ Figure 1
fig, axs = plt.subplots(2, 2, figsize=(16, 8.6), sharex=True, sharey=True)
for i, est in enumerate(("EKF3", "UKF")):
    for j, mode in enumerate(("off", "on")):
        ax = axs[i, j]
        for yw in (10, -10):
            ax.axhspan(yw - 0.1 if yw > 0 else yw - 0.1, yw + 0.1, color=WALL)
        ax.axhline(9.58, color=WALL, lw=0.8, ls=":"); ax.axhline(-9.58, color=WALL, lw=0.8, ls=":")
        for k, tr in enumerate(CL[f"{est}_{mode}"]):
            g = gt_of(tr); c0, ct = cl_meta(tr)
            w = g[:, 0] >= 20
            ax.plot(g[w, 2], g[w, 1], color=C[est], lw=2 if mode == "off" else 1.6, alpha=1 if k == 0 else 0.75)
            if mode == "off":
                ax.plot(ct["y"], ct["x"], marker="X", ms=13, color=INK, mec=SURF, mew=1.5, zorder=5)
                y0 = float(np.interp(c0, g[:, 0], g[:, 2]))
                a, b = WIN[est]
                ax.axvspan(y0 + 0.5 * a, y0 + 0.5 * b, ymin=0.0, ymax=0.08, color=C[est], alpha=0.25, lw=0)
                ax.annotate(f"wall contact at cruise +{ct['t_rel_cruise_s']:.1f} s\n(predicted window +{a}…+{b} s, shaded)",
                            (ct["y"], ct["x"]), xytext=(4, 3.2), fontsize=12, color=INK,
                            arrowprops=dict(arrowstyle="-", color=INK2, lw=1))
        if mode == "on":
            mx = max(L(f"closed_loop_{tr}.json")["B"]["B2"]["max_abs_x_cruise_m"] for tr in CL[f"{est}_on"])
            ax.text(80, 6.2, f"3 flights, max |cross-track| {mx:.2f} m (band 6.0 m)", ha="center", fontsize=12, color=INK)
        ax.set_title(f"{est}, {'no camera heading' if mode == 'off' else 'with camera heading'}", loc="left")
        ax.text(2, 8.2, "east wall", fontsize=11, color=INK2); ax.text(2, -8.9, "west wall", fontsize=11, color=INK2)
        ax.set_ylim(-10.6, 10.6); ax.set_xlim(0, 160)
        if i == 1: ax.set_xlabel("distance along corridor, true North y (m)")
        if j == 0: ax.set_ylabel("lateral position, true East x (m)")
fig.suptitle("Closed loop: the estimator flies the vehicle. True paths in the textured corridor (full speed)", x=0.01, ha="left", fontsize=17)
fig.tight_layout(rect=(0, 0, 1, 0.95))
save(fig, "fig1_closed_loop_paths.png", "Closed-loop true paths: EKF3 and UKF, with and without the camera heading",
     "Ground-truth paths (top-down) when EKF3 or the UKF is the vehicle's estimator, 0.5 m/s, textured corridor "
     "(walls at x = ±10 m; dotted line = the 9.58 m wall-contact threshold). Without heading both drift west into the wall "
     "(X = contact; shaded strip = the pre-registered contact window, mapped to distance at 0.5 m/s); with the camera heading "
     "all 6 flights stay within 0.34 m of the centreline. n = 1 per no-heading set, 3 per heading set. The FGO closed loop was flown at half "
     "speed only (fig10, fig9). "
     "Same information within each estimator (heading on vs off); EKF3 and UKF differ by design.",
     "CONFIRMATORY (pre-registered criteria)",
     "paths: trial bags cl_a_tex, cl_bcpp_tex_r1-3, cl_ukf_a_tex, cl_ukf_b_tex_r1-3 (/ground_truth/pose); contact times, cruise "
     "start and B2: eval/results/closed_loop_<trial>.json; windows: METHODOLOGY pre-registrations (set (a); D16 check)")

# ------------------------------------------------------------------------------------------------ Figure 2
fig, axs = plt.subplots(2, 2, figsize=(16, 8.6), sharex=True)
for i, est in enumerate(("EKF3", "UKF")):
    for j, mode in enumerate(("off", "on")):
        ax = axs[i, j]
        for k, tr in enumerate(CL[f"{est}_{mode}"]):
            t, e = log_yaw(tr, est)
            ax.plot(t, e, color=C[est], lw=1.4 if mode == "on" else 2, alpha=1 if k == 0 else 0.7)
        if mode == "on":
            ax.set_ylim(-1.0, 1.0); ax.axhspan(-1.0, -1.0, color=GRID)
            p95 = [L(f"closed_loop_{tr}.json")["B"]["B3"]["p95_deg"] for tr in CL[f"{est}_on"]]
            ax.text(5, 0.78, f"|error| p95 {min(p95):.2f}–{max(p95):.2f}° (band 1.0°)", fontsize=12)
        else:
            ax.text(5, 0.9 * ax.get_ylim()[1], "drifts without an absolute heading", fontsize=12)
        ax.set_title(f"{est}, {'no camera heading (1 flight)' if mode == 'off' else 'with camera heading (3 flights)'}", loc="left")
        if i == 1: ax.set_xlabel("time since cruise start (s)")
        if j == 0: ax.set_ylabel("heading error, estimate − truth (°)")
fig.suptitle("Closed loop: heading error drifts without the camera heading and stays bounded with it (note the different y-scales)", x=0.01, ha="left", fontsize=16)
fig.tight_layout(rect=(0, 0, 1, 0.95))
save(fig, "fig2_closed_loop_heading_error.png", "Closed-loop heading error with and without the camera heading",
     "Heading error of the flying estimator (EKF3: XKF1; UKF: its current-time output XUKO) against simulator truth, from cruise start, "
     "full-speed closed-loop flights. Left: no heading, drift until wall contact. Right: with the camera heading, bounded well inside the "
     "pre-registered B3 band. Y-scales differ between columns (stated). Same-information comparison within each row.",
     "CONFIRMATORY (pre-registered B3 bands)", "curves: dataflash logs of the trials in Figure 1; p95 values: eval/results/closed_loop_<trial>.json (B3)")

# ------------------------------------------------------------------------------------------------ Figure 3
ev = {**L("rerun_dsn_evo.json")["trials"], **L("dsn_extra_evo.json")["trials"]}
pt = L("dsn_paired_test.json")
fig, (ax, bx) = plt.subplots(1, 2, figsize=(16, 6.6), gridspec_kw={"width_ratios": [1.6, 1]})
for k, est in enumerate(("EKF3", "FGO", "UKF")):
    v = [(i, ev[f"dsn_tex_r{i}"]["est"][est]["ate_a_cruise"]["+0.00"]) for i in range(1, 11) if est in ev[f"dsn_tex_r{i}"]["est"]]
    x = np.array([p[0] for p in v]) + (k - 1) * 0.22
    ax.scatter(x, [p[1] for p in v], s=70, color=C[est], edgecolor=SURF, linewidth=1.5, zorder=3, label=f"{est} (n={len(v)})")
    ax.text(10.55, np.median([p[1] for p in v]), f"{est} median {np.median([p[1] for p in v]):.2f} m", color=INK, fontsize=12, va="center")
ax.set_xticks(range(1, 11)); ax.set_xlim(0.5, 13.6); ax.set_ylim(0, 7)
ax.set_xlabel("flight (dsn_tex r1 … r10)"); ax.set_ylabel("position error, evo -a cruise (m)")
ax.set_title("Per-flight accuracy, textured floor, no heading (after all corrections incl. D15)", loc="left", fontsize=14)
ax.legend(loc="upper left", frameon=False)
d = np.array(pt["d_m"]); fl = pt["usable_for_FGO"]
bx.axhline(0, color=INK2, lw=1)
bx.scatter(range(len(d)), d, s=80, color=C["EKF3"], edgecolor=SURF, linewidth=1.5, zorder=3)
lo, hi = pt["t95_ci_m"]; md = pt["mean_d_m"]
bx.errorbar([len(d) + 0.6], [md], yerr=[[md - lo], [hi - md]], fmt="D", ms=10, color=INK, capsize=8, lw=2)
bx.text(len(d) + 0.9, md, f"mean {md:.2f} m\n95% CI [{lo:.2f}, {hi:.2f}]", va="center", fontsize=12)
bx.set_xticks(list(range(len(d))) + [len(d) + 0.6]); bx.set_xticklabels([f.replace("dsn_tex_", "") for f in fl] + ["mean"])
bx.set_xlim(-0.6, len(d) + 3.2); bx.set_ylabel("EKF3 − FGO (m)")
bx.set_title(f"Confirmatory test: {pt['verdict'].split('(')[0].strip()} ({pt['n_neg']}/{len(d)} negative)", loc="left", fontsize=14)
fig.suptitle("Offline accuracy on the textured floor without heading: EKF3 lowest; confirmed EKF3 < FGO", x=0.01, ha="left", fontsize=16)
fig.tight_layout(rect=(0, 0, 1, 0.93))
save(fig, "fig3_offline_textured_no_heading.png", "Offline accuracy, textured floor, no heading; confirmatory EKF3 − FGO test",
     "Left: evo -a (cruise) per flight for the three estimators on the same 10 open-loop flights (same information; r10 is unusable for UKF/FGO under the "
     "IMU-gap rule). Right: the pre-registered paired test on the 6 usable new flights r4–r9 (d = EKF3 − FGO; t-interval df 5). "
     "Values after the consolidated corrections, D15 and D27 (offline UKF process noise aligned). UKF median 5.34 m (all 9 stable).",
     "CONFIRMATORY (right panel); DESCRIPTIVE (left)", "eval/results/rerun_dsn_evo.json, dsn_extra_evo.json (evo -a cruise '+0.00'); dsn_paired_test.json")

# ------------------------------------------------------------------------------------------------ Figure 4
fig, ax = plt.subplots(figsize=(15, 6.6)); EK4, U4, F4 = [], [], []
bags = [("fwdc", r) for r in (1, 2, 3)] + [("fwdplainc", r) for r in (1, 2, 3)]
for i, (ds, r) in enumerate(bags):
    e = L(f"phase4_{ds}_evo.json")["trials"][f"{ds}_tex_r{r}"]["est"]
    u, f, k = (e["UKF_heading"]["ate_a_cruise"]["+0.00"], e["FGO_heading"]["ate_a_cruise"]["+0.00"], e["EKF3"]["ate_a_cruise"]["+0.00"])
    EK4.append(k); U4.append(u); F4.append(f)
    ax.plot([i, i], [f, u], color=GRID, lw=3, zorder=1)
    ax.scatter([i], [u], s=110, color=C["UKF"], edgecolor=SURF, linewidth=1.5, zorder=3, label="UKF + camera heading" if i == 0 else None)
    ax.scatter([i], [f], s=110, color=C["FGO"], edgecolor=SURF, linewidth=1.5, zorder=3, label="FGO + camera heading" if i == 0 else None)
    ax.scatter([i + 0.25], [k], s=60, marker="s", facecolor="none", edgecolor=WALL, linewidth=1.5, zorder=2,
               label="EKF3 without heading (reference only; NOT same information)" if i == 0 else None)
    ax.text(i + 0.08, u, f"{u:.2f}", fontsize=11, va="center"); ax.text(i + 0.08, f, f"{f:.2f}", fontsize=11, va="center")
ax.set_yscale("log"); ax.set_ylim(0.05, 8)
ax.set_xticks(range(6)); ax.set_xticklabels([f"{ds}_tex_r{r}\n({'line-textured walls' if ds == 'fwdc' else 'plain walls'})" for ds, r in bags], fontsize=11)
ax.set_ylabel("position error, evo -a cruise (m, log scale)")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=3, frameon=False)
fig.suptitle("With the camera heading: FGO lower position error than UKF on 6/6 bags (same information)", x=0.01, ha="left", fontsize=16)
fig.tight_layout(rect=(0, 0, 1, 0.93))
save(fig, "fig4_offline_with_heading_C0.png", "Offline with camera heading: FGO vs UKF (C0, post-D15)",
     "Heading arms of the offline UKF and FGO on the same 6 textured-floor bags with the same camera headings (σ 0.148°/0.126°, 3σ gate): "
     f"FGO lower on {sum(a < b for a, b in zip(F4, U4))}/6 ({min(F4):.2f}–{max(F4):.2f} m vs {min(U4):.2f}–{max(U4):.2f} m). Grey squares: EKF3 WITHOUT heading ({min(EK4):.2f}–{max(EK4):.2f} m), shown only as a reference; "
     "it is not a same-information comparison. Not shown: the UKF has LOWER yaw error on 5 of 6 bags (C0).",
     "DESCRIPTIVE (C0 report; prediction recorded)", "eval/results/phase4_fwdc_evo.json, phase4_fwdplainc_evo.json (UKF_heading, FGO_heading, EKF3; evo -a cruise)")

# ------------------------------------------------------------------------------------------------ Figure 5
dec = L("phase5_analysis.json")["decomposition"]
fig, ax = plt.subplots(figsize=(15, 6.6)); HH = {}
rows = [("EKF3", "EKF3", "no heading"), ("UKF", "UKF_baseline", "no heading"), ("UKF", "UKF_heading", "with heading"),
        ("FGO", "FGO_baseline", "no heading"), ("FGO", "FGO_heading", "with heading")]
for i, (est, arm, lab) in enumerate(rows):
    h = [abs(dec[f"fwdc_tex_r{r}"][arm]["xtrack_head_m"]) for r in (1, 2, 3)]
    s = [abs(dec[f"fwdc_tex_r{r}"][arm]["xtrack_resid_m"]) for r in (1, 2, 3)]
    ax.scatter(h, [i + 0.12] * 3, s=90, color=C[est], edgecolor=SURF, linewidth=1.5, zorder=3, label="heading-driven" if i == 0 else None)
    ax.scatter(s, [i - 0.12] * 3, s=90, marker="s", facecolor=SURF, edgecolor=C[est], linewidth=2, zorder=3, label="residual (not heading)" if i == 0 else None)
    HH[arm] = (h, s)
    ax.text(max(h + s) * 1.3, i, f"heading-driven {np.mean(h):.2f} m | residual {np.mean(s):.2f} m", va="center", fontsize=12)
ax.set_yticks(range(len(rows))); ax.set_yticklabels([f"{e}, {l}" for e, _, l in rows])
ax.set_xscale("log"); ax.set_xlim(0.01, 3000); ax.invert_yaxis()
ax.set_xlabel("cross-track error at end of cruise (m, log scale)")
ax.legend(loc="lower right", frameon=False)
fig.suptitle("Where the cross-track error comes from: heading-driven vs residual, before and after the camera heading", x=0.01, ha="left", fontsize=16)
fig.tight_layout(rect=(0, 0, 1, 0.93))
save(fig, "fig5_drift_decomposition.png", "Heading-driven vs residual cross-track, with and without the camera heading",
     "Lateral-error decomposition (Phase 5) on fwdc_tex r1–r3 (n = 3 per row, dots): the part of the end-of-cruise cross-track explained by the "
     f"estimator's heading error vs the residual. Without heading, heading error drives {min(min(HH[a][0]) for a in ('EKF3','UKF_baseline','FGO_baseline')):.1f}–{max(max(HH[a][0]) for a in ('EKF3','UKF_baseline','FGO_baseline')):.1f} m of cross-track; with the camera heading "
     f"the heading-driven part falls to ≤{max(max(HH[a][0]) for a in ('UKF_heading','FGO_heading')):.2f} m, leaving the UKF with a {np.mean(HH['UKF_heading'][1]):.2f} m mean residual (a sideways drift not explained by heading) and the FGO {np.mean(HH['FGO_heading'][1]):.2f} m. "
     "EKF3 has no offline heading arm (closed loop only). Same information within each estimator.",
     "DESCRIPTIVE (Phase 5 analysis)", "eval/results/phase5_analysis.json (decomposition: xtrack_head_m, xtrack_resid_m)")

# ------------------------------------------------------------------------------------------------ Figure 6
bb = L("blank_behaviour.json")
fig, ax = plt.subplots(figsize=(14, 6.8))
T = ["+10s", "+30s", "+60s", "+120s"]; tx = [10, 30, 60, 120]
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
    med = np.nanmedian(np.array(curves), axis=0)
    ax.plot(tx, med, color=C[est], lw=3, marker="o", ms=8, label=f"{est} median (n={len(curves)})")
    ax.text(124, med[-1], f"{est}: {med[-1]:.0f} m at +120 s", va="center", fontsize=12)
ax.set_yscale("log"); ax.set_xlim(0, 150); ax.set_ylim(1, 1e5)
ax.axhspan(1, 1e5, xmin=0, xmax=120 / 150, color="#f0efec", zorder=0)
ax.text(3, 2.2e4, "EKF3: position flagged INVALID from take-off to landing on every blank flight\n"
        "(output held at the origin; not scored) — no error curve by design", fontsize=12, color=INK)
ax.set_xlabel("time since flow loss (s)"); ax.set_ylabel("position error magnitude (m, log scale)")
ax.legend(loc="lower right", frameon=False)
fig.suptitle("Total loss of flow aiding (blank floor): UKF and FGO dead-reckon and diverge; EKF3 declares itself invalid", x=0.01, ha="left", fontsize=16)
fig.tight_layout(rect=(0, 0, 1, 0.93))
save(fig, "fig6_blank_flow_loss.png", "Loss of flow aiding on the blank floor",
     "Position error magnitude after flow is lost (blank floor) for the UKF and FGO baselines (thin: each of 11 flights: dsn, p1c, fwdc, fwdplainc "
     "blank; thick: median). EKF3 has no curve: its position is flagged invalid for the whole flight and it outputs the origin, so it is not scored "
     "(evaluation rule). Behaviour under total loss, not accuracy; the estimators respond by design differently.",
     "DESCRIPTIVE", "eval/results/blank_behaviour.json (along_m, cross_m at +10/+30/+60/+120 s; EKF3 validity)")

# ------------------------------------------------------------------------------------------------ Figure 7 (table)
rows = [
    ("dsn textured, EKF3 evo -a mean (r1–r3)", "4.66 m", "4.00 m", "4.00 m (unchanged)"),
    ("dsn textured, FGO evo -a mean (r1–r3)", "4.65 m", "4.52 m", "4.64 m"),
    ("dsn textured, UKF evo -a (r1–r3)", "16.98 / 9.96 / 20.71 m", "17.45 / 2.28 / 4.30 m", "4.23 / 2.14 / 5.38 m"),
    ("dsn textured, UKF r1–r9 median", "—", "17.5 m (≤4.3 m on 3/9)", "5.34 m (all 9 stable)"),
    ("Heading share of EKF3 lateral drift (dsn_tex_r3)", "68.9 %", "90.6 %", "—"),
    ("EKF3 lateral flow innovation |FIX| (airborne mean)", "~300–450", "7", "—"),
    ("Confirmatory EKF3 − FGO (r4–r9), 95% CI", "—", "−0.69 [−1.20, −0.19] m", "−0.69 [−1.16, −0.21] m"),
]
fixes = [("(i) flow sign", "lateral optical-flow axis had the wrong sign in the EKF3 bridge and the UKF/FGO flow model"),
         ("(ii) FLOW_POS_Z", "camera lever arm (0.25 m below the IMU) was not given to EKF3"),
         ("(iii) UKF time step", "UKF integrated with 12.5 ms while each step spanned 15 ms (~15% position under-scale)"),
         ("(iv) time sync", "SITL ran without time sync (which also injected AHRS_EKF_TYPE=10 silently); now on, set explicitly"),
         ("(v) roll gains", "a roll limit cycle in the vehicle's attitude loop contaminated flow; gains fixed"),
         ("D15 ground-proximity rule", "UKF/FGO fused flow on the ground; EKF3's rule (flow = no motion below 0.5 m before take-off) now shared")]
fig = plt.figure(figsize=(16, 7.6)); ax = fig.add_axes([0.01, 0.47, 0.98, 0.44]); ax.axis("off")
tab = ax.table(cellText=[list(r) for r in rows], colLabels=["headline number", "before corrections", "after 5 corrections (re-flown)", "after D15 (UKF: + D27)"],
               loc="upper left", cellLoc="left", colLoc="left", colWidths=[0.40, 0.19, 0.22, 0.19])
tab.auto_set_font_size(False); tab.set_fontsize(12.5); tab.scale(1, 2.1)
for (r_, c_), cell in tab.get_celld().items():
    cell.set_edgecolor(GRID); cell.set_facecolor(SURF if r_ else "#f0efec")
    if r_ == 0: cell.set_text_props(weight="bold")
ax2 = fig.add_axes([0.01, 0.02, 0.98, 0.43]); ax2.axis("off")
ax2.text(0, 1, "What each correction fixed (one line each; (i)–(v) applied together in one re-flown batch, so their effects are not separable):",
         fontsize=13, weight="bold", va="top")
for k, (a, b) in enumerate(fixes):
    ax2.text(0, 0.84 - 0.14 * k, f"{a}:", fontsize=12.5, weight="bold", va="top"); ax2.text(0.20, 0.84 - 0.14 * k, b, fontsize=12.5, va="top")
fig.suptitle("The corrections: headline numbers before and after", x=0.01, ha="left", fontsize=17)
save(fig, "fig7_corrections_table.png", "Corrections: headline numbers old vs new",
     "Headline numbers before the consolidated corrections, after the five corrections (re-flown datasets), and after D15. Old values are the "
     "superseded rows recorded verbatim in numbers.md; '—' = not computed at that stage. The five corrections were applied together (one "
     "re-fly), so their individual effects are not separated. The UKF values in the last column also include D27 (the offline UKF's IMU process "
     "noise aligned to the FGO/port per-second densities, 2026-10-01).",
     "DESCRIPTIVE", "docs/thesis/numbers.md (Former sections 6–9; §6.1, §6.3; Superseded by D15); eval/results/dsn_paired_test.json")

# ------------------------------------------------------------------------------------------------ Figure 8
f1 = L("f1_test.json")
bagsF = ["fwdplainc_tex_r1", "fwdplainc_tex_r2", "fwdplainc_tex_r3", "fwdc_tex_r1", "fwdc_tex_r2", "fwdc_tex_r3"]
arms = [("UKF_hard", "UKF, hard 3σ gate", C["UKF"], None), ("FGO_hard", "FGO, hard 3σ gate", C["FGO"], "//"), ("FGO_robust", "FGO, robust (Cauchy)", C["FGO"], None)]
mets = [("correct rejected (%)", lambda m: 100 * m["correct_rejected"] / max(m["correct"], 1)),
        ("wrong accepted (%)", lambda m: 100 * m["wrong_accepted"] / max(m["wrong"], 1) if m["wrong"] else np.nan),
        ("worst-case yaw error (°)", lambda m: m["yaw_max_deg"]), ("max cross-track (m)", lambda m: m["xtrack_max_m"])]
fig, axs = plt.subplots(2, 2, figsize=(16, 9))
for ax, (lab, fn) in zip(axs.flat, mets):
    for k, (arm, nm, col, hatch) in enumerate(arms):
        v = [fn(f1[b][arm]) for b in bagsF]
        ax.bar(np.arange(6) + (k - 1) * 0.26, v, width=0.24, color=col if hatch is None else SURF, edgecolor=col, hatch=hatch, lw=1.5, label=nm)
    ax.set_xticks(range(6)); ax.set_xticklabels(["plain r1", "plain r2", "plain r3", "textured\nend wall r1", "textured\nend wall r2", "textured\nend wall r3"], fontsize=11)
    ax.set_ylabel(lab); ax.set_title(lab, loc="left", fontsize=14)
axs[0, 0].legend(loc="upper right", frameon=False, fontsize=11)
fig.suptitle("Robust weighting trade-off (F1): fewer correct headings rejected, lower cross-track — larger worst-case yaw than the UKF", x=0.01, ha="left", fontsize=16)
fig.tight_layout(rect=(0, 0, 1, 0.94))
save(fig, "fig8_f1_robust_tradeoff.png", "F1: robust heading weighting trade-off",
     "Same camera headings (σ 0.148°/0.126°) on plain-wall bags (whole cruise) and the textured end-wall region (y > 140 m). Pre-registered F1 "
     "decision FAILED as worded (the UKF had the lower worst-case yaw on all 6 bags). Descriptively: the robust FGO rejects far fewer correct headings "
     "than the UKF on plain walls (16–18% vs 85–94% on r1/r2; 28% on r3), accepts fewer wrong ones, and has lower cross-track on all 3; the hard-gated FGO bar isolates "
     "the effect of the weighting from the estimator. 'Rejected' for the robust arm = weight < 0.5 (still contributes). "
     "Small n on the textured end wall: only 3 / 5 / 2 wrong headings (r1/r2/r3), so its 'wrong accepted' 33% is 1 of 3.",
     "EXPLORATORY (descriptive part; the pre-registered decision failed)", "eval/results/f1_test.json")


# ------------------------------------------------------------------------------------------------ Figure 9 (closed-loop summary, D28)
def setb(trs):
    B = [L(f"closed_loop_{t}.json")["B"] for t in trs]
    rng = lambda f: f"{min(f(b) for b in B):.2f}–{max(f(b) for b in B):.2f}"
    return (f"{sum(b['pass'] for b in B)}/3", rng(lambda b: b["B2"]["max_abs_x_cruise_m"]) + " m",
            rng(lambda b: b["B3"]["p95_deg"]) + "° / " + rng(lambda b: b["B3"]["max_deg"]) + "°")
def seta(tr, win):
    c0, ct = cl_meta(tr); t_ = ct["t_rel_cruise_s"]
    return f"west +{t_:.1f} s  {'PASS' if win[0] <= t_ <= win[1] else 'MISS'}  [+{win[0]}, +{win[1]}]"
rows9 = [
    ("EKF3, full speed", seta("cl_a_tex", (155, 215)), *setb([f"cl_bcpp_tex_r{i}" for i in (1, 2, 3)])),
    ("EKF3, half speed", seta("cl_a_tex_half", (155, 215)), *setb([f"cl_bcpp_tex_r{i}_half" for i in (1, 2, 3)])),
    ("UKF, full speed", seta("cl_ukf_a_tex", (146, 218)), *setb([f"cl_ukf_b_tex_r{i}" for i in (1, 2, 3)])),
    ("UKF, half speed", seta("cl_ukf_a_tex_half", (146, 218)), *setb([f"cl_ukf_b_tex_r{i}_half" for i in (1, 2, 3)])),
    ("FGO hard-gated, half speed", seta("cl_fgo_a_tex_half", (145, 196)), *setb([f"cl_fgo_b_tex_r{i}_half" for i in (1, 2, 3)])),
    ("FGO robust heading, half speed", "not flown", *setb([f"cl_fgo_b_robust_tex_r{i}_half" for i in (1, 2, 3)])),
]
fig = plt.figure(figsize=(16, 6.4)); ax = fig.add_axes([0.01, 0.20, 0.98, 0.68]); ax.axis("off")
tab = ax.table(cellText=[list(r) for r in rows9], colLabels=["flying estimator", "no heading: wall contact (window)", "with heading: B1–B5 pass",
               "max cross-track (B2)", "yaw error p95 / max (B3)"], loc="upper left", cellLoc="left", colLoc="left",
               colWidths=[0.22, 0.31, 0.15, 0.13, 0.19])
tab.auto_set_font_size(False); tab.set_fontsize(12.5); tab.scale(1, 2.2)
for (r_, c_), cell in tab.get_celld().items():
    cell.set_edgecolor(GRID); cell.set_facecolor(SURF if r_ else "#f0efec")
    if r_ == 0: cell.set_text_props(weight="bold")
fig.text(0.01, 0.12, "UKF half r3 fails B4 (D22: flow validity lags the feature count). Both FGO with-heading sets are 3/3 after the D28 scorer fix "
         "(first scored 2/3: a landing speed sample stretched the B5 window into the stop).", fontsize=12, color=INK2)
fig.text(0.01, 0.07, "No cross-speed comparison is claimed (D21); n = 1 per no-heading cell, so closed-loop run-to-run variability is unmeasured.",
         fontsize=12, color=INK2)
fig.suptitle("Closed loop, all three estimators: summary (restated after D28)", x=0.01, ha="left", fontsize=17)
save(fig, "fig9_closed_loop_summary.png", "Closed-loop summary: all three estimators flying the vehicle",
     "Pre-registered closed-loop results. No heading: west-wall contact time in cruise against the pre-registered window (EKF3's half-speed "
     "flight missed it: D21). With the camera heading: flights passing B1–B5 (+S2 for UKF/FGO), and the B2/B3 ranges over the 3 flights. "
     "The FGO was flown at half speed only. Every FGO closed-loop result is stated with the D23 climb-top transient (LiDAR short returns) and the "
     "D26 findings (larger per-heading weight, ~5x fast heading jitter coupling into vehicle yaw; descriptive).",
     "CONFIRMATORY (pre-registered criteria)",
     "eval/results/closed_loop_<trial>.json (scorer after D28); windows: METHODOLOGY pre-registrations; numbers.md §15")

# ------------------------------------------------------------------------------------------------ Figure 10 (half-speed paths, all three)
HALF = [("EKF3", "cl_a_tex_half", [f"cl_bcpp_tex_r{i}_half" for i in (1, 2, 3)], (155, 215), "-"),
        ("UKF", "cl_ukf_a_tex_half", [f"cl_ukf_b_tex_r{i}_half" for i in (1, 2, 3)], (146, 218), "-"),
        ("FGO", "cl_fgo_a_tex_half", [f"cl_fgo_b_tex_r{i}_half" for i in (1, 2, 3)], (145, 196), "-"),
        ("FGO robust", None, [f"cl_fgo_b_robust_tex_r{i}_half" for i in (1, 2, 3)], None, "--")]
fig, axs = plt.subplots(4, 2, figsize=(16, 13), sharex=True, sharey=True)
for i, (nm, off, ons, win, ls) in enumerate(HALF):
    col = C["FGO"] if nm.startswith("FGO") else C[nm]
    for j in (0, 1):
        ax = axs[i, j]
        for yw in (10, -10):
            ax.axhspan(yw - 0.1, yw + 0.1, color=WALL)
        ax.axhline(9.58, color=WALL, lw=0.8, ls=":"); ax.axhline(-9.58, color=WALL, lw=0.8, ls=":")
        if j == 0:
            if off is None:
                ax.text(80, 0, "not flown (the robust variant was flown with heading only)", ha="center", fontsize=12, color=INK2)
            else:
                g = gt_of(off); c0, ct = cl_meta(off); w = g[:, 0] >= 20
                ax.plot(g[w, 2], g[w, 1], color=col, lw=2, ls=ls)
                ax.plot(ct["y"], ct["x"], marker="X", ms=13, color=INK, mec=SURF, mew=1.5, zorder=5)
                y0 = float(np.interp(c0, g[:, 0], g[:, 2])); a, b = win
                ax.axvspan(y0 + 0.5 * a, y0 + 0.5 * b, ymin=0.0, ymax=0.08, color=col, alpha=0.25, lw=0)
                ax.annotate(f"contact at cruise +{ct['t_rel_cruise_s']:.1f} s (window +{a}…+{b} s)", (ct["y"], ct["x"]),
                            xytext=(4, 3.2), fontsize=12, color=INK, arrowprops=dict(arrowstyle="-", color=INK2, lw=1))
        else:
            for k, tr in enumerate(ons):
                g = gt_of(tr); w = g[:, 0] >= 20
                ax.plot(g[w, 2], g[w, 1], color=col, lw=1.6, ls=ls, alpha=1 if k == 0 else 0.75)
            mx = max(L(f"closed_loop_{tr}.json")["B"]["B2"]["max_abs_x_cruise_m"] for tr in ons)
            ax.text(80, 6.2, f"3 flights, max |cross-track| {mx:.2f} m (band 6.0 m)", ha="center", fontsize=12, color=INK)
        ax.set_title(f"{nm}, {'no camera heading' if j == 0 else 'with camera heading'}", loc="left", fontsize=14)
        ax.set_ylim(-10.6, 10.6); ax.set_xlim(0, 160)
        if i == 3: ax.set_xlabel("distance along corridor, true North y (m)")
        if j == 0: ax.set_ylabel("true East x (m)")
fig.suptitle("Closed loop at half speed: true paths when each estimator flies the vehicle", x=0.01, ha="left", fontsize=17)
fig.tight_layout(rect=(0, 0, 1, 0.96))
save(fig, "fig10_closed_loop_paths_half.png", "Closed-loop true paths at half speed: EKF3, UKF, FGO (hard-gated and robust heading)",
     "Ground-truth paths (top-down), 0.5 m/s, half-speed textured corridor (walls at x = ±10 m; dotted = the 9.58 m contact threshold). "
     "Without heading every estimator drifts west into the wall (X = contact; shaded = the pre-registered window, mapped to distance at 0.5 m/s); "
     "EKF3 reached it later than its window (D21). With the camera heading all 12 flights stay near the centreline; the FGO rows show its "
     "larger heading jitter only as small path wiggles at this scale. Solid = hard-gated heading, dashed = robust heading weighting (plan step 2(b)).",
     "CONFIRMATORY (pre-registered criteria)",
     "trial bags cl_*_half (/ground_truth/pose); contact times and B2: eval/results/closed_loop_<trial>.json; windows: METHODOLOGY pre-registrations")

# ------------------------------------------------------------------------------------------------ PDF + index
pdf = os.path.join(OUT, "figures.pdf")
with PdfPages(pdf) as P:
    for png, title, cap, kind, src in FIGS:
        img = plt.imread(png); h, w = img.shape[:2]
        fig = plt.figure(figsize=(11.69, 8.27))
        ax = fig.add_axes([0.03, 0.26, 0.94, 0.70]); ax.imshow(img); ax.axis("off")
        import textwrap
        fig.text(0.03, 0.235, "\n".join(textwrap.wrap(f"{title}  —  {kind}", 120)), fontsize=11.5, weight="bold", va="top")
        fig.text(0.03, 0.175, "\n".join(textwrap.wrap(cap, 165)), fontsize=9.5, va="top")
        fig.text(0.03, 0.045, "\n".join(textwrap.wrap(f"Source: {src}. Commit {COMMIT}.", 180)), fontsize=8.5, va="top", color=INK2)
        P.savefig(fig); plt.close(fig)
with open(os.path.join(OUT, "INDEX.md"), "w") as f:
    f.write(f"# Supervisor meeting figures, 2026-10-01 (updated 2026-10-02: D27, D28, fig9–fig10)\n\nGenerated by `eval/figs_supervisor_2026_10_01.py` at commit `{COMMIT}`. "
            "Combined PDF: `figures.pdf` (one figure + caption per page). No new experiments; numbers from committed result files, "
            "curves from the recorded trial data named per figure.\n\n")
    for png, title, cap, kind, src in FIGS:
        f.write(f"## {os.path.basename(png)}: {title}\n\n- **Status:** {kind}\n- **Caption:** {cap}\n- **Data source:** {src}\n- **Commit:** `{COMMIT}`\n\n")
print("wrote", pdf)
