#!/usr/bin/env python3
"""E3 map-collapse diagnosis (descriptive): figures. Reads the run outputs (live.tum, hindsight.tum), ground truth from the
bag (tag 0's frame, as l_score.py) and the reconstruct.py JSONs. Writes docs/thesis/tier1/figs/e3_collapse_*.png.
Usage (venv-evo): figs.py [extra 'label=run_dir=recon_json_name' for counterfactual time courses]"""
import json, sys, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore
FGO, TRUTH = "#D55E00", "#999999"
T1 = "/home/makerspace/thesis_data/tier1"; O = f"{T1}/stage2e/diag_collapse"; FIG = "/home/makerspace/thesis_ws/docs/thesis/tier1/figs"
B = "lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7"
ts = get_typestore(Stores.ROS2_JAZZY)


def gt(trial):
    G = []
    with Reader(f"/home/makerspace/thesis_data/trials/{trial}/bag") as r:
        c = [x for x in r.connections if x.topic == "/ground_truth/pose"]
        for con, _, raw in r.messages(connections=c):
            m = ts.deserialize_cdr(raw, con.msgtype)
            G.append((m.header.stamp.sec + m.header.stamp.nanosec * 1e-9, m.pose.position.x + 3.0, m.pose.position.y + 3.0))
    return np.array(G)


def err(run, G, kind="live"):
    H = np.loadtxt(f"{run}/{kind}.tum", ndmin=2); t = H[:, 0]
    return t, np.hypot(H[:, 1] - np.interp(t, G[:, 0], G[:, 1]), H[:, 2] - np.interp(t, G[:, 0], G[:, 2])), H


def events(recon):
    F = recon["factors"]; first_mis = [f["t"] for f in F if f["mis"] and f["first"]]
    other = [f["t"] for f in F if f["mis"] and not f["first"]]
    mis_tids = recon["first_sighting_mislabelled_tids"]
    first_true = [next(f["t"] for f in F if f["tid_true"] == tid and not f["mis"]) for tid in mis_tids]
    return first_mis, other, first_true


def timecourse(ax, run, recon, G, title):
    t, e, _ = err(run, G)
    fm, ot, ft = events(recon)
    for x in ot: ax.axvline(x, color="#555555", lw=0.6, ls=":", zorder=1)
    for x in fm: ax.axvline(x, color="#000000", lw=1.2, ls="--", zorder=2)
    for x in ft: ax.axvline(x, color="#0072B2", lw=1.4, ls="-", zorder=2)
    ax.plot(t, e, color=FGO, lw=1.2, zorder=3)
    ax.set_title(title, fontsize=10, loc="left"); ax.set_ylabel("live horizontal error (m)")
    ef = e[np.isfinite(e)]; top = float(ef.max()) * 1.05
    if top > 10.0:                                  # a diverged run: axis clipped at 10 m (linear axis, stated in the title)
        top = 10.0; title += " [axis clipped at 10 m]"; ax.set_title(title, fontsize=10, loc="left")
    ax.set_ylim(0, top); ax.grid(axis="y", color="#e5e5e5", lw=0.6)
    for s in ("top", "right"): ax.spines[s].set_visible(False)


runs = [("T_A_r1", "0.01", 0, "T_A_r1, 1%, seed 0 (arm (a))"), ("T_A_r3", "0.05", 0, "T_A_r3, 5%, seed 0 (arm (a))")]
Gs = {}
fig, axs = plt.subplots(2, 1, figsize=(10, 6.5), sharex=True)
for ax, (tr, p, s, title) in zip(axs, runs):
    Gs.setdefault(tr, gt(tr)); rc = json.load(open(f"{O}/recon_{tr}_{p}_s{s}.json"))
    timecourse(ax, f"{T1}/{tr}/{B}_mis{p}_s{s}", rc, Gs[tr], title)
axs[-1].set_xlabel("time (s, bag clock)")
h = [plt.Line2D([], [], color=FGO, lw=1.2), plt.Line2D([], [], color="#000000", ls="--", lw=1.2),
     plt.Line2D([], [], color="#555555", ls=":", lw=0.8), plt.Line2D([], [], color="#0072B2", lw=1.4)]
fig.legend(h, ["FGO live error against truth", "wrong id on a FIRST sighting (creates the landmark)", "other wrong id (existing landmark)",
               "first CORRECT sighting of a mislabel-created landmark"], loc="upper center", ncol=2, fontsize=8, frameon=False)
fig.tight_layout(rect=(0, 0, 1, 0.92)); fig.savefig(f"{FIG}/e3_collapse_timecourse.png", dpi=150); plt.close(fig)

# counterfactual time courses (T_A_r1 1% s0: original, cf (i), cf (ii)) if present
cf = [a.split("=", 2) for a in sys.argv[1:]]   # label=run_dir=recon_json_name (events only are read from the recon json)
if cf:
    G = Gs["T_A_r1"]; fig, axs = plt.subplots(len(cf) + 1, 1, figsize=(10, 2.6 * (len(cf) + 1)), sharex=True)
    items = [("original T_A_r1 1% s0", f"{T1}/T_A_r1/{B}_mis0.01_s0", f"{O}/recon_T_A_r1_0.01_s0.json")] + \
            [(lab, d, f"{O}/{rj}.json") for lab, d, rj in cf]
    for ax, (lab, d, rj) in zip(axs, items):
        timecourse(ax, d, json.load(open(rj)), G, lab)
    axs[-1].set_xlabel("time (s, bag clock)")
    fig.legend(h, ["FGO live error against truth", "wrong id on a FIRST sighting", "other wrong id", "first CORRECT sighting of a mislabel-created landmark"],
               loc="upper center", ncol=2, fontsize=8, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.93)); fig.savefig(f"{FIG}/e3_collapse_counterfactuals.png", dpi=150); plt.close(fig)

# final map + hindsight track against truth
maps = [("T_A_r1", f"{T1}/T_A_r1/{B}_mis0.01_s0", "recon_T_A_r1_0.01_s0", "T_A_r1 1% s0, arm (a)"),
        ("T_A_r3", f"{T1}/T_A_r3/{B}_mis0.05_s0", "recon_T_A_r3_0.05_s0", "T_A_r3 5% s0, arm (a)"),
        ("T_A_r2", f"{T1}/T_A_r2/{B}_mis0.05_s1_robcauchy2.385", "recon_T_A_r2_0.05_s1_rob", "T_A_r2 5% s1, arm (b) robust")]
fig, axs = plt.subplots(1, 3, figsize=(12, 4.4))
for ax, (tr, d, rj, title) in zip(axs, maps):
    Gs.setdefault(tr, gt(tr)); G = Gs[tr]; rc = json.load(open(f"{O}/{rj}.json")); _, _, H = err(d, G, "hindsight")
    w = (G[:, 0] >= H[0, 0]) & (G[:, 0] <= H[-1, 0])
    ax.plot(G[w, 1], G[w, 2], color=TRUTH, lw=0.8); ax.plot(H[:, 1], H[:, 2], color=FGO, lw=0.6, alpha=0.8)
    for tid, v in rc["true_map_tag0_frame"].items():
        ax.plot(v[0], v[1], "s", color=TRUTH, ms=8); ax.annotate(tid, (v[0], v[1]), xytext=(6, 4), textcoords="offset points", fontsize=8, color="#555555")
    for tid, v in rc["landmarks_final_by_tid"].items():
        ax.plot(v[0], v[1], "o", color=FGO, ms=6, mec="white", mew=1)
    ax.set_aspect("equal"); ax.set_xlim(-1.5, 7.5); ax.set_ylim(-1.5, 7.5); ax.set_title(title, fontsize=10, loc="left")
    ax.set_xlabel("x in tag 0's frame (m)"); ax.grid(color="#eeeeee", lw=0.5)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
axs[0].set_ylabel("y in tag 0's frame (m)")
h2 = [plt.Line2D([], [], color=TRUTH, lw=0.8), plt.Line2D([], [], color=FGO, lw=0.8), plt.Line2D([], [], marker="s", ls="", color=TRUTH),
      plt.Line2D([], [], marker="o", ls="", color=FGO)]
fig.legend(h2, ["truth track", "FGO hindsight track", "true tag positions (id)", "FGO final landmarks"], loc="upper center", ncol=4, fontsize=8, frameon=False)
fig.tight_layout(rect=(0, 0.02, 1, 0.92)); fig.savefig(f"{FIG}/e3_collapse_maps.png", dpi=150); plt.close(fig)
print("figures written")
