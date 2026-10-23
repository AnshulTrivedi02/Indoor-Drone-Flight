#!/usr/bin/env python3
"""E3 map-collapse diagnosis (DESCRIPTIVE, after scoring): every number quoted in the write-up, computed in one place from
the reconstruct.py JSONs, the run outputs and the bags (ground truth in tag 0's frame, as l_score.py). READ-ONLY.
Writes ~/thesis_data/tier1/stage2e/diag_collapse/summary.json (unrounded); check_prose_collapse.py rounds once.

Cost terms (all 0.5 * whitened residual squared, the replay's own noise: tag 0.05 m, 0.05 m, 5 deg; flow 0.25 rad/s):
  * tag cost: exact, from the reconstructed factors at (i) the run's final estimate (hindsight.tum + landmarks_final),
    (ii) the truth (ground-truth pose + true map for the REPORTED id). Arm (b) also with the Cauchy rho (k = 2.385).
  * flow cost: an APPROXIMATE proxy: |v_est - v_true| (horizontal, central difference over +-0.5 s of the hindsight and
    truth tracks) / (0.25 rad/s * h_cam), h_cam = truth z - 0.25 m; no rotational term, one term per keyframe. It is
    about 0 at the truth by construction. IMU and range costs are NOT evaluated.
Usage (venv-fgo): analyse.py"""
import json, os, sys
import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore
T1 = "/home/makerspace/thesis_data/tier1"; O = f"{T1}/stage2e/diag_collapse"; B = "lc_fgo_lc_t245_tags0-1-2-3-4-5-6-7"
SC = "/home/makerspace/thesis_ws/docs/thesis/tier1/scores"
K2 = "59.995-60.127-72.964-89.893-97.384-108.703-114.280-121.243-132.397-144.871-151.174-163.945-180.874-210.739-228.328-246.808-246.841"
ts = get_typestore(Stores.ROS2_JAZZY)
RUNS = {   # name: (trial, run dir, recon json, robust?, score json)
    "r1_1_s0": ("T_A_r1", f"{T1}/T_A_r1/{B}_mis0.01_s0", "recon_T_A_r1_0.01_s0", False, f"{SC}/E3a_T_A_r1_0.01_s0.json"),
    "r3_5_s0": ("T_A_r3", f"{T1}/T_A_r3/{B}_mis0.05_s0", "recon_T_A_r3_0.05_s0", False, f"{SC}/E3a_T_A_r3_0.05_s0.json"),
    "r1_1_s0_rob": ("T_A_r1", f"{T1}/T_A_r1/{B}_mis0.01_s0_robcauchy2.385", "recon_T_A_r1_0.01_s0_rob", True, f"{SC}/E3b_T_A_r1_0.01_s0.json"),
    "r2_5_s1_rob": ("T_A_r2", f"{T1}/T_A_r2/{B}_mis0.05_s1_robcauchy2.385", "recon_T_A_r2_0.05_s1_rob", True, f"{SC}/E3b_T_A_r2_0.05_s1.json"),
    "cf_ii": ("T_A_r1", f"{O}/T_A_r1/{B}_mis0.01_s0_cfkeep{K2}", "recon_cf_ii", False, f"{O}/score_cf_ii.json"),
}
G_cache = {}


def gt(trial):
    if trial not in G_cache:
        G = []
        with Reader(f"/home/makerspace/thesis_data/trials/{trial}/bag") as r:
            c = [x for x in r.connections if x.topic == "/ground_truth/pose"]
            for con, _, raw in r.messages(connections=c):
                m = ts.deserialize_cdr(raw, con.msgtype)
                G.append((m.header.stamp.sec + m.header.stamp.nanosec * 1e-9, m.pose.position.x + 3, m.pose.position.y + 3, m.pose.position.z))
        G_cache[trial] = np.array(G)
    return G_cache[trial]


rho = lambda w, k=2.385: 0.5 * k * k * np.log1p((w / k) ** 2)
spread = lambda P: float(np.sqrt(((P - P.mean(0)) ** 2).sum(1).mean()))
out = {}
for name, (trial, rdir, rj, rob, scj) in RUNS.items():
    if not os.path.exists(f"{O}/{rj}.json"):
        continue
    d = json.load(open(f"{O}/{rj}.json")); F = d["factors"]; m = np.array([f["mis"] for f in F])
    r = {"n_factors": len(F), "n_wrong": int(m.sum()), "first_sighting_mislabelled_tids": d["first_sighting_mislabelled_tids"]}
    for key in ("w_est", "w_truth"):
        W = np.linalg.norm(np.array([f[key] for f in F]), axis=1); c = 0.5 * W ** 2
        r[key] = {"tag_cost": float(c.sum()), "tag_cost_wrong": float(c[m].sum()), "wrong_share": float(c[m].sum() / c.sum()) if m.any() else 0.0,
                  "wrong_w_median": float(np.median(W[m])) if m.any() else None, "wrong_w_max": float(W[m].max()) if m.any() else None,
                  "correct_w_median": float(np.median(W[~m])), "correct_w_p95": float(np.percentile(W[~m], 95))}
        if rob:
            cr = rho(W); r[key].update({"cauchy_tag_cost": float(cr.sum()), "cauchy_tag_cost_wrong": float(cr[m].sum())})
        if m.any():
            top = np.sort(c[m])[::-1]; r[key]["top3_wrong_share_of_wrong"] = float(top[:3].sum() / top.sum())
    lt, tm = d["landmarks_final_by_tid"], d["true_map_tag0_frame"]
    r["spread_est_m"] = spread(np.array([lt[str(i)][:2] for i in range(8)])); r["spread_truth_m"] = spread(np.array([tm[str(i)][:2] for i in range(8)]))
    G = gt(trial); H = np.loadtxt(f"{rdir}/hindsight.tum", ndmin=2); t = H[:, 0]
    g = np.c_[np.interp(t, G[:, 0], G[:, 1]), np.interp(t, G[:, 0], G[:, 2])]
    r["path_hindsight_m"] = float(np.hypot(*np.diff(H[:, 1:3], axis=0).T).sum()); r["path_truth_m"] = float(np.hypot(*np.diff(g, axis=0).T).sum())
    n = 15; ve = (H[2 * n:, 1:3] - H[:-2 * n, 1:3]) / (t[2 * n:] - t[:-2 * n])[:, None]; vg = (g[2 * n:] - g[:-2 * n]) / (t[2 * n:] - t[:-2 * n])[:, None]
    hc = np.interp(t[n:-n], G[:, 0], G[:, 3]) - 0.25; w = np.linalg.norm(ve - vg, axis=1) / (0.25 * hc)
    r["flow_proxy_cost"] = float(0.5 * (w ** 2).sum()); r["flow_proxy_w_median"] = float(np.median(w))
    r["h_cam_median_m"] = float(np.median(hc)); r["flow_sigma_v_m_s"] = 0.25 * float(np.median(hc))
    if os.path.exists(scj):
        s = json.load(open(scj))["tracks"]; r["lc_live_rmse_m"] = s["lc live"]["rmse_m"]; r["lc_hindsight_rmse_m"] = s["lc hindsight"]["rmse_m"]
    # live time course: error just before / after each first correct sighting of a mislabel-created landmark, and first step
    L = np.loadtxt(f"{rdir}/live.tum", ndmin=2); tl = L[:, 0]
    el = np.hypot(L[:, 1] - np.interp(tl, G[:, 0], G[:, 1]), L[:, 2] - np.interp(tl, G[:, 0], G[:, 2]))
    ft = {tid: next(f["t"] for f in F if f["tid_true"] == tid and not f["mis"]) for tid in d["first_sighting_mislabelled_tids"]}
    r["first_correct_sighting_t"] = {str(k): v for k, v in ft.items()}
    r["err_before_first_correct"] = {str(k): float(el[(tl < v) & (tl >= v - 1)].max()) for k, v in ft.items()}
    r["err_after_first_correct"] = {str(k): float(el[(tl > v) & (tl <= v + 0.5)].max()) for k, v in ft.items()}
    i1 = int(np.argmax(el > 1.0)); r["first_live_err_over_1m_t"] = float(tl[i1])
    wt = [f["t"] for f in F if f["mis"]]; r["last_wrong_before_first_1m_t"] = max([x for x in wt if x <= tl[i1]], default=None)
    pre = [f for f in F if f["mis"] and f["t"] <= tl[i1]]
    r["last_wrong_before_first_1m"] = None if not pre else [pre[-1]["tid_true"], pre[-1]["tid"], pre[-1]["first"]]
    r["max_err_before_first_1m"] = float(el[:i1].max()) if i1 else None
    out[name] = r
# the earlier counterfactuals cf2_s1/cf2_s2 (T_A_r1 1%, seeds 1/2, both divergence triggers kept; 0 first-sighting mislabels)
for s, keep in ((1, "49.402-60.358"), (2, "54.253-55.870")):
    st = json.load(open(f"{T1}/diag_stage2e/T_A_r1/{B}_mis0.01_s{s}_cfkeep{keep}/stats.json")); P = np.array([v[:2] for v in st["landmarks_final"].values()])
    sc = json.load(open(f"{O}/score_cf2_s{s}.json"))["tracks"]
    out[f"cf2_s{s}"] = {"keyframe_failures": st["keyframe_failures"], "first_sighting_mislabelled": st["tier1"]["landmarks_first_sighting_mislabelled"],
                        "spread_est_m": spread(P), "lc_live_rmse_m": sc["lc live"]["rmse_m"], "lc_live_max_m": sc["lc live"]["max_m"],
                        "lc_hindsight_rmse_m": sc["lc hindsight"]["rmse_m"], "lc_live_lap1_m": sc["lc live"]["per_lap_rmse_m"][0],
                        "wall_s": st["wall_s"], "n_wrong_remaining": st["tier1"]["mislabel"]["n_mislabelled"] - len(st["tier1"]["mislabel_keep"]["kept_t_true_new"])}
for nm in ("cf_i", "cf_ii"):
    p = f"{O}/status/{nm}.json"
    if os.path.exists(p):
        out.setdefault(nm, {})["status"] = json.load(open(p))
json.dump(out, open(f"{O}/summary.json", "w"), indent=1)
print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk not in ("w_est", "w_truth", "status")} for k, v in out.items()}, indent=1))
