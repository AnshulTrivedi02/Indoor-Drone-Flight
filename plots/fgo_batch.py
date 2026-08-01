#!/usr/bin/env python3
"""Run the FGO across the nine dsn_* bags at the primary window (0.25 s, batch,
under the 33 ms deployability budget) and assemble the per-condition table matching
the EKF3/UKF format. Run in venv-fgo. ~40 min."""
import os, re, subprocess, numpy as np

HOME = os.path.expanduser("~")
PY = f"{HOME}/venv-fgo/bin/python3"
EVO = f"{HOME}/venv-evo/bin/evo_ape"
REPLAY = f"{HOME}/thesis_ws/src/estimators/fgo/fgo_replay.py"
WINDOW = "0.25"
CONDS = {"tex": [f"dsn_tex_r{i}" for i in (1, 2, 3)],
         "blank": [f"dsn_blank_r{i}" for i in (1, 2, 3)],
         "trans": [f"dsn_trans_r{i}" for i in (1, 2, 3)]}


def evo_rmse(trial, aligned):
    d = f"{HOME}/thesis_data/trials/{trial}/fgo"
    cmd = [EVO, "tum", f"{d}/ground_truth.tum", f"{d}/fgo_traj.tum", "--t_max_diff", "0.05", "--no_warnings"]
    if aligned: cmd.append("-a")
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    m = re.search(r'rmse\s+([\d.]+)', out)
    return float(m.group(1)) if m else float('nan')


def run_one(trial):
    subprocess.run([PY, REPLAY, trial, WINDOW], capture_output=True, text=True)
    met = dict(l.strip().split("=") for l in open(f"{HOME}/thesis_data/trials/{trial}/fgo/metrics.txt"))
    return dict(flow=int(met["n_flow"]), along=float(met["along_pN"]), true=float(met["true_travel"]),
                cross=float(met["cross_track"]), yaw=float(met["yaw_drift"]), bgz=float(met["bgz_mean"]),
                ate_a=evo_rmse(trial, True), ate_u=evo_rmse(trial, False),
                tmed=float(met["step_median_ms"]), tp99=float(met["step_p99_ms"]))


rows = {}
for cond, trials in CONDS.items():
    for tr in trials:
        rows[tr] = run_one(tr); r = rows[tr]
        print(f"  {tr}: flow={r['flow']} along={r['along']:.1f} cross={r['cross']:.1f} "
              f"ATE_a={r['ate_a']:.2f} ATE_u={r['ate_u']:.1f} yaw={r['yaw']:.1f} t={r['tmed']:.0f}ms", flush=True)

print(f"\n{'trial':14}{'flow':>7}{'travel':>8}{'along':>8}{'cross':>8}{'ATE-a':>8}{'ATE-u':>8}{'yawdrift':>9}{'bgz':>8}{'t_med':>7}")
for cond, trials in CONDS.items():
    for tr in trials:
        r = rows[tr]
        print(f"{tr:14}{r['flow']:>7}{r['true']:>8.1f}{r['along']:>8.1f}{r['cross']:>8.1f}"
              f"{r['ate_a']:>8.2f}{r['ate_u']:>8.1f}{r['yaw']:>9.1f}{r['bgz']:>8.2f}{r['tmed']:>6.0f}ms")
    def ms(k): v = [rows[tr][k] for tr in trials]; return np.mean(v), max(v)-min(v)
    print(f"  mean/range {cond:5}{'':>16}{ms('along')[0]:>8.1f}{ms('cross')[0]:>8.1f}"
          f"{ms('ate_a')[0]:>8.2f}{ms('ate_u')[0]:>8.1f}{ms('yaw')[0]:>9.1f}{ms('bgz')[0]:>8.2f}")
    print(f"    (range){'':>18}{ms('along')[1]:>8.1f}{ms('cross')[1]:>8.1f}"
          f"{ms('ate_a')[1]:>8.2f}{ms('ate_u')[1]:>8.1f}{ms('yaw')[1]:>9.1f}{ms('bgz')[1]:>8.2f}")
print(f"\nprimary window {WINDOW}s (batch, deployable <33ms). n=1 per bag.")
