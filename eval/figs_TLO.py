#!/usr/bin/env python3
"""Supervisor figures for experiments T, O and L (2026-10-08). Same style and palette as
eval/figs_supervisor_2026_10_01.py (EKF3 blue, FGO orange, UKF aqua; hindsight tracks dashed in their estimator's hue;
every series direct-labelled or in a legend). No new experiments: numbers from the committed result files
(eval/results/expT, expO, expL), curves from the recorded trial data named per figure.
Output: plots/supervisor_2026-10-08/fig11..fig15_*.png, figures.pdf, INDEX.md.
Usage (venv-evo + the pymavlink shim): PYTHONPATH=$HOME/.cache/thesis_pyshim ~/venv-evo/bin/python eval/figs_TLO.py"""
import json, os, re, subprocess, textwrap
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator
from matplotlib.backends.backend_pdf import PdfPages
from pymavlink import mavutil
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "eval", "results"); TD = os.path.expanduser("~/thesis_data/trials")
OUT = os.path.join(ROOT, "plots", "supervisor_2026-10-08"); os.makedirs(OUT, exist_ok=True)
COMMIT = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
C = {"EKF3": "#2a78d6", "FGO": "#eb6834", "UKF": "#1baf7a"}
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb"
plt.rcParams.update({"font.size": 14, "axes.titlesize": 16, "axes.labelsize": 14, "xtick.labelsize": 12, "ytick.labelsize": 12,
                     "legend.fontsize": 12, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
                     "text.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF, "lines.linewidth": 2,
                     "axes.spines.top": False, "axes.spines.right": False})
FIGS = []
TRK = {"EKF3 live": (C["EKF3"], "-"), "UKF live": (C["UKF"], "-"), "FGO live": (C["FGO"], "-"),
       "RTS-UKF (hindsight)": (C["UKF"], "--"), "FGO hindsight (whole-flight batch)": (C["FGO"], "--")}
SHORT = {"EKF3 live": "EKF3 live", "UKF live": "UKF live", "FGO live": "FGO live", "RTS-UKF (hindsight)": "RTS-UKF (hindsight)",
         "FGO hindsight (whole-flight batch)": "FGO batch (hindsight)"}


def plain_log(ax, ticks):
    ax.yaxis.set_major_locator(FixedLocator(ticks)); ax.yaxis.set_minor_locator(NullLocator())
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))


def badge(fig, kind):
    col = {"CONFIRMATORY": "#1c5cab", "DESCRIPTIVE": INK2, "DIAGNOSTIC": "#8a5a00"}[kind.split()[0]]
    fig.text(0.995, 0.995, kind, ha="right", va="top", fontsize=11, color=col, weight="bold")


def save(fig, name, title, caption, kind, sources):
    badge(fig, kind); p = os.path.join(OUT, name); fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
    FIGS.append((p, title, caption, kind, sources)); print("wrote", p)


J = lambda p: json.load(open(os.path.join(RES, p)))

# ---------------------------------------------------------------- fig11: T hindsight gain vs gap length
fig, axs = plt.subplots(1, 2, figsize=(14, 5.6), sharey=True)
agg = J("expT/t_aggregate.json")
for ax, live, hind, key, col, lab in ((axs[0], "FGO live", "FGO hindsight (whole-flight batch)", "H-T1 (FGO live -> whole-flight batch)", C["FGO"], "FGO: live − whole-flight batch"),
                                       (axs[1], "UKF live", "RTS-UKF (hindsight)", "P-T2 (UKF live -> RTS)", C["UKF"], "UKF: live − RTS-smoothed")):
    for cnd in "ABCD":
        Lg, Dg = [], []
        for r in (1, 2, 3):
            for g in J(f"expT/T_{cnd}_r{r}.json")["gaps"]:
                if live in g and hind in g:
                    Lg.append(g["length_s"]); Dg.append(1e3 * (g[live]["mean"] - g[hind]["mean"]))
        ax.scatter(Lg, Dg, s=22, color=col, alpha=0.35, edgecolor="none")
        med = 1e3 * agg[key]["median_gain_m"][cnd]
        ax.plot([np.median(Lg)], [med], "D", color=col, ms=11, mec=SURF, mew=2)
        ax.annotate(cnd, (np.median(Lg), med), textcoords="offset points", xytext=(8, 6), fontsize=13, weight="bold", color=INK)
    ax.axhline(0, color=INK2, lw=1)
    v = agg[key]
    ax.set_title(f"{lab}\nρ = {v['spearman_rho']:+.2f}, p = {v['p']:.0e}; {'PASS' if v['PASS'] else 'FAIL'}", fontsize=14)
    ax.set_xlabel("gap between tag fixes (s)")
axs[0].set_ylabel("hindsight gain per gap (mm)\n(live mean error − hindsight mean error)")
save(fig, "fig11_T_hindsight_gain_vs_gap.png", "T: hindsight gain grows with the gap for the FGO, not for the single-pass RTS-UKF",
     "Per gap between consecutive tag fixes (12 flights, 213 gaps; dots), the mean live horizontal error minus the mean hindsight error over "
     "that gap; diamonds = condition medians (A all 8 tags, B corners, C 2 diagonal, D 1 tag; median gaps 4.3/10.1/22.0/46.3 s). Left: the "
     "FGO's whole-flight batch against its own fixed-lag live estimate — the pre-registered primary H-T1, strictly increasing, PASS. Right: "
     "the RTS-smoothed UKF against the live UKF (P-T2, FAIL): helpful with dense fixes, harmful on long gaps (a single-pass smoother; see METHODOLOGY). "
     "Same information for every estimator (the fixes EKF3 received).",
     "CONFIRMATORY (pre-registered H-T1, P-T2)", "eval/results/expT/T_*.json (gaps), t_aggregate.json")

# ---------------------------------------------------------------- fig12: T RMSE per condition
fig, ax = plt.subplots(figsize=(13, 5.8))
names = list(TRK); off = np.linspace(-0.3, 0.3, len(names))
for i, n in enumerate(names):
    col, ls = TRK[n]
    for ci, cnd in enumerate("ABCD"):
        v = [1e3 * J(f"expT/T_{cnd}_r{r}.json")["tracks"][n]["horiz_err_m"]["rmse"] for r in (1, 2, 3)]
        mk = "o" if ls == "-" else "s"
        ax.scatter([ci + off[i]] * 3, v, color=col if ls == "-" else SURF, edgecolor=col, linewidth=2, s=50, marker=mk, zorder=3,
                   label=SHORT[n] if ci == 0 else None)
ax.set_xticks(range(4)); ax.set_xticklabels(["A: all 8\n(gap 4.3 s)", "B: corners\n(10.1 s)", "C: 2 diagonal\n(22.0 s)", "D: 1 tag\n(46.3 s)"])
ax.set_ylabel("horizontal RMSE over the laps (mm)"); ax.set_yscale("log"); plain_log(ax, [10, 20, 50, 100, 200])
ax.legend(ncol=5, loc="upper left", fontsize=11, frameon=False, bbox_to_anchor=(0, 1.12))
save(fig, "fig12_T_rmse_by_condition.png", "T: horizontal error by tag density, live and hindsight",
     "Horizontal RMSE in the world frame (no alignment) over the 5-lap window, 3 repeats per condition (each marker one flight; repeats agree "
     "within 8 mm). Filled circles = live estimates, open squares = hindsight. The FGO live is lowest of the live tracks with frequent fixes "
     "(A–C), EKF3 with the sparsest (D); live ratios 1.8–2.3× (P-T3 FAIL). The whole-flight FGO stays at 11–34 mm in every condition; the "
     "RTS-UKF does not (P-T4 FAIL). Log scale.",
     "CONFIRMATORY (pre-registered P-T3, P-T4)", "eval/results/expT/T_*.json (tracks.*.horiz_err_m.rmse)")

# ---------------------------------------------------------------- fig13: O error over the flight + indoor RMSE
ts = get_typestore(Stores.ROS2_JAZZY)
tr = "O_r1"; D = f"{TD}/{tr}"
o = J(f"expO/{tr}.json"); toff, ton = o["markers_bag_s"]["GNSS OFF"], o["markers_bag_s"]["GNSS ON"]
G = np.loadtxt(f"{D}/room_ukf/ground_truth.tum")
TR = []
with Reader(f"{D}/bag") as rd:
    cs = [c for c in rd.connections if c.topic == "/imu/time_ref"]
    for con, _, raw in rd.messages(connections=cs):
        m = ts.deserialize_cdr(raw, con.msgtype)
        TR.append((m.time_ref.sec + m.time_ref.nanosec * 1e-9, m.header.stamp.sec + m.header.stamp.nanosec * 1e-9))
TR = np.array(TR); sitl, d = TR[:, 0], TR[:, 1] - TR[:, 0]; env = []
for lo in np.arange(sitl.min(), sitl.max(), 5.0):
    w = (sitl >= lo) & (sitl < lo + 5)
    if w.sum() > 50:
        i = np.argmin(d[w]); env.append((sitl[w][i], d[w][i]))
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
ax = axs[0]; ax.axvspan(0, ton - toff, color=GRID, zorder=0); ax.text((ton - toff) / 2, 0.02, f"indoors: GNSS off ({ton - toff:.0f} s)", ha="center",
                                                                     transform=ax.get_xaxis_transform(), color=INK2, fontsize=12)
for n, T in tracks.items():
    col, ls = TRK[n]; w = (T[:, 0] > toff - 40) & (T[:, 0] < ton + 30)
    e = np.hypot(T[w, 1] - np.interp(T[w, 0], G[:, 0], G[:, 1]), T[w, 2] - np.interp(T[w, 0], G[:, 0], G[:, 2]))
    ax.plot(T[w, 0] - toff, e, color=col, ls=ls, label=SHORT[n])
ax.set_xlabel("time from GNSS OFF (s)"); ax.set_ylabel("horizontal error (m)"); ax.set_xlim(-40, ton - toff + 30)
ax.legend(loc="upper left", fontsize=11, frameon=False)
ax.annotate("EKF3 reset jump\n4.1 m", (ton - toff + 4.5, 3.4), fontsize=11, color=C["EKF3"])
ax = axs[1]
for i, n in enumerate(TRK):
    col, ls = TRK[n]
    v = [J(f"expO/{t}.json")["tracks"][n]["indoor_rmse_m"] for t in ("O_r1", "O_r2", "O_r3b")]
    ax.scatter([i] * 3, v, color=col if ls == "-" else SURF, edgecolor=col, linewidth=2, s=60, marker="o" if ls == "-" else "s", zorder=3)
ax.set_xticks(range(len(TRK))); ax.set_xticklabels([SHORT[n].replace(" (", "\n(") for n in TRK], rotation=0, fontsize=10)
ax.set_ylabel("indoor horizontal RMSE (m)"); ax.set_ylim(0, None)
save(fig, "fig13_O_indoor_hindsight.png", "O: indoor error with GNSS outside only; hindsight reconstruction and EKF3's return jump",
     "Left: horizontal error against time for one flight (O_r1), outdoor → indoor (grey, GNSS off) → outdoor, world frame, no alignment. "
     "The live tracks drift indoors (mostly lateral, from yaw drift) and EKF3 jumps 4.1 m when it resets to GNSS on return; the "
     "whole-flight FGO reconstructs the indoor segment to 0.33 m. Right: indoor RMSE for all 3 flights (one marker each; open = hindsight). "
     "H-O1 PASS 3/3 (FGO batch below both filters' live tracks); H-O2 and P-O3 FAIL. The RTS-UKF here is single-pass; its cap-free variant is "
     "worse (0.97 m, METHODOLOGY). Same GNSS samples for all estimators.",
     "CONFIRMATORY (pre-registered H-O1, H-O2, P-O3)",
     "eval/results/expO/O_*.json; curves: O_r1 room_ukf/, room_fgo/ TUMs, dataflash XKF1 about EKF3's origin (gnss.npz)")

# ---------------------------------------------------------------- fig14: L lap-by-lap
fig, ax = plt.subplots(figsize=(12, 5.8))
CL, CN = C["FGO"], INK2
for mode, col, lab in (("lc", CL, "with loop closure"), ("nolc", CN, "without loop closure")):
    for kind, ls, mk in (("live", "-", "o"), ("hindsight", "--", "s")):
        for r in (1, 2, 3):
            v = J(f"expL/T_A_r{r}_t245.json")["tracks"][f"{mode} {kind}"]["per_lap_rmse_m"]
            ax.plot(range(1, 6), np.array(v) * 1e3, color=col, ls=ls, marker=mk, ms=6, alpha=0.85,
                    label=f"{lab}, {kind}" if r == 1 else None, mfc=col if ls == "-" else SURF)
ax.set_xlabel("lap"); ax.set_ylabel("horizontal RMSE per lap (mm)"); ax.set_xticks(range(1, 6)); ax.set_yscale("log")
plain_log(ax, [20, 30, 50, 100, 200, 300, 500])
ax.legend(loc="lower left", ncol=2, fontsize=11, frameon=False, bbox_to_anchor=(0, 1.01))
save(fig, "fig14_L_lap_by_lap.png", "L: tag re-identification bounds the drift lap by lap",
     "Keyframe FGO with tags at UNKNOWN positions, T_A_r1–r3 (3 lines per style), RMSE per 6 m lap in the first tag's frame. With loop "
     "closure (tags re-identified by id) the live error falls after lap 1 and stays 0.02–0.04 m (H-L1 PASS: lap 5 ≤ 1.5 × lap 1); without it "
     "(a new landmark per pass) it grows 4.5–5.5× over five laps (P-L4 PASS), and hindsight does not reliably help. An FGO capability, not an "
     "FGO-vs-filter result: the filters have no loop-closure equivalent without a different design. Log scale.",
     "CONFIRMATORY (pre-registered H-L1, P-L4)", "eval/results/expL/T_A_r*_t245.json (per_lap_rmse_m)")

# ---------------------------------------------------------------- fig15: L computational cost
S = os.environ.get("L_LOGDIR", os.path.join(RES, "expL", "logs"))   # replay progress logs (committed)
fig, ax = plt.subplots(figsize=(12, 5.4))
for mode, col, lab in (("lc", CL, "with loop closure (8 landmarks)"), ("nolc", CN, "without loop closure (~41 landmarks)")):
    for r in (1, 2, 3):
        p = os.path.join(S, f"L3_T_A_r{r}_{mode}.log")
        L_ = [tuple(map(float, x)) for x in re.findall(r"keyframe (\d+) t ([\d.]+) landmarks (\d+) wall (\d+)", open(p).read())]
        xs, ys, pk, pw = [], [], 0, 0
        for k, t, lm, w in L_:
            xs.append((pk + k) / 2); ys.append(1e3 * (w - pw) / (k - pk)); pk, pw = k, w
        ax.plot(xs, ys, color=col, marker="o", label=lab if r == 1 else None, alpha=0.85)
ax.set_xlabel("keyframe (30 Hz; ~33 s of flight per 1000)"); ax.set_ylabel("mean solve time per update (ms)"); ax.set_yscale("log")
plain_log(ax, [10, 20, 50, 100, 200, 500, 1000])
ax.legend(loc="lower left", ncol=2, fontsize=11, frameon=False, bbox_to_anchor=(0, 1.01))
save(fig, "fig15_L_compute_cost.png", "L: per-update solve time over the flight (diagnostic)",
     "Mean iSAM2 update time per 1000-keyframe block, keyframe FGO with retained history (30 Hz keyframes, the thesis cadence), "
     "3 flights per mode. With loop closure the cost stays at tens of ms; without it each pass adds a landmark and the cost climbs to "
     "0.1–1.4 s per update in 1000-keyframe means (per-update p99 1.3–2.2 s). Workstation Python with numerical-Jacobian factors, six replays in parallel: diagnostic only. "
     "A real drone would need a much lower keyframe rate, bounded landmarks and compiled factors.",
     "DIAGNOSTIC (not a pre-registered metric)", "lc_fgo_replay progress logs (per 1000 keyframes), lc_fgo_*_t245/stats.json")

pdf = os.path.join(OUT, "figures.pdf")
with PdfPages(pdf) as P:
    for png, title, cap, kind, src in FIGS:
        img = plt.imread(png)
        fig = plt.figure(figsize=(11.69, 8.27))
        ax = fig.add_axes([0.03, 0.26, 0.94, 0.70]); ax.imshow(img); ax.axis("off")
        fig.text(0.03, 0.235, "\n".join(textwrap.wrap(f"{title}  —  {kind}", 120)), fontsize=11.5, weight="bold", va="top")
        fig.text(0.03, 0.175, "\n".join(textwrap.wrap(cap, 165)), fontsize=9.5, va="top")
        fig.text(0.03, 0.045, "\n".join(textwrap.wrap(f"Source: {src}. Commit {COMMIT}.", 180)), fontsize=8.5, va="top", color=INK2)
        P.savefig(fig); plt.close(fig)
with open(os.path.join(OUT, "INDEX.md"), "w") as f:
    f.write(f"# Supervisor figures, 2026-10-08: experiments T, O, L (continues the 2026-10-01 set, fig1–fig10)\n\nGenerated by "
            f"`eval/figs_TLO.py` at commit `{COMMIT}`. Combined PDF: `figures.pdf`. No new experiments; numbers from committed result "
            "files, curves from the recorded trial data named per figure.\n\n")
    for png, title, cap, kind, src in FIGS:
        f.write(f"## {os.path.basename(png)}: {title}\n\n- **Status:** {kind}\n- **Caption:** {cap}\n- **Data source:** {src}\n- **Commit:** `{COMMIT}`\n\n")
print("wrote", pdf)
