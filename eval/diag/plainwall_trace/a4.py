"""Evaluate the diagnostic replays (scratch) against the stored Phase-4 arms, with the same evo -a (cruise)
call as eval/three_way_eval.py (its own functions, imported), the stored pinned window, and phase4_eval's yaw-error
definition. Run with ~/venv-ardupilot/bin/python. Writes a4.json."""
import sys, os, json, math, tempfile
import numpy as np
W = '/home/makerspace/thesis_ws/.claude/worktrees/agent-a375613081292d466'
sys.path.insert(0, W + '/eval')
import three_way_eval as T
SC = '/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/pw'
TD = '/home/makerspace/thesis_data/trials'
ARMS = {ds: json.load(open(f'{W}/eval/results/phase4_{ds}_arms.json')) for ds in ('fwdc', 'fwdplainc')}


def tumyaw(a):
    x, y, z, w = a[:, 4], a[:, 5], a[:, 6], a[:, 7]
    return np.unwrap(np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))


def ev(trial, d, est_f, tmp):
    ds = 'fwdplainc' if 'fwdplainc' in trial else 'fwdc'
    t0, t1 = ARMS[ds][trial]['window_s']
    ref, est = np.loadtxt(f'{d}/ground_truth.tum'), np.loadtxt(f'{d}/{est_f}')
    rc, ec = f'{tmp}/r.tum', f'{tmp}/e.tum'
    T.write_tum(rc, T.crop(ref, t0, t1)); T.write_tum(ec, T.crop(est, t0, t1))
    ate = T.evo_ape_a(rc, ec)
    g = np.load(f'{TD}/{trial}/fwd_meas/gt_eval_only.npz')['g']
    w = (est[:, 0] >= t0) & (est[:, 0] <= t1)
    err = np.degrees(tumyaw(est)[w] - (np.interp(est[w, 0], g[:, 0], g[:, 3]) - math.pi / 2))
    if np.abs(err).max() < 170:
        err = (err + 180) % 360 - 180
    m = {k: float(v) for k, v in (l.strip().split('=') for l in open(f'{d}/metrics.txt') if '=' in l)}
    fs = json.load(open(f'{d}/fwd_stats.json'))['counts']
    return dict(evo_a_cruise=ate, yaw_rms=float(np.sqrt(np.mean(err ** 2))), yaw_max=float(np.abs(err).max()),
                bgz_mean_dpm=m.get('bgz_mean'), true_bias_dpm=m.get('true_bias_mean'),
                psi_fused=fs['psi_fused'], psi_valid=fs['psi_valid'])


rows = [  # label, trial, directory, traj file
    ('FGO stored (Phase 4)', 'fwdplainc_tex_r1', f'{TD}/fwdplainc_tex_r1/fgo_heading', 'fgo_traj.tum'),
    ('FGO base (scratch re-run)', 'fwdplainc_tex_r1', f'{SC}/out/fwdplainc_tex_r1/fgo_heading', 'fgo_traj.tum'),
    ('UKF stored (Phase 4)', 'fwdplainc_tex_r1', f'{TD}/fwdplainc_tex_r1/ukf_heading', 'ukf_traj.tum'),
    ('UKF base (scratch re-run)', 'fwdplainc_tex_r1', f'{SC}/out/fwdplainc_tex_r1/ukf_heading', 'ukf_traj.tum'),
]
for tr in ('fwdplainc_tex_r1', 'fwdplainc_trans_r1'):
    rows.append(('UKF stored (Phase 4)', tr, f'{TD}/{tr}/ukf_heading', 'ukf_traj.tum'))
    rows.append(('UKF y0 sigma 1e-3 rad (FGO value)', tr, f'{SC}/out/{tr}/ukf_heading_y0t', 'ukf_traj.tum'))
for tr in ('fwdplainc_tex_r1', 'fwdplainc_tex_r2', 'fwdplainc_tex_r3', 'fwdplainc_trans_r1', 'fwdplainc_trans_r2',
           'fwdplainc_trans_r3', 'fwdplainc_blank_r1', 'fwdc_tex_r1'):
    rows.append(('FGO stored (Phase 4)', tr, f'{TD}/{tr}/fgo_heading', 'fgo_traj.tum'))
    rows.append(('FGO y0 sigma 1 deg (UKF value)', tr, f'{SC}/out/{tr}/fgo_heading_y0s1', 'fgo_traj.tum'))
    rows.append(('UKF stored (Phase 4)', tr, f'{TD}/{tr}/ukf_heading', 'ukf_traj.tum'))
out = []
seen = set()
with tempfile.TemporaryDirectory() as tmp:
    for lab, tr, d, f in rows:
        if (lab, tr) in seen or not os.path.exists(f'{d}/{f}'):
            continue
        seen.add((lab, tr))
        r = ev(tr, d, f, tmp); r.update(label=lab, trial=tr); out.append(r)
        print(f"{tr:20} {lab:36} evo {r['evo_a_cruise']:8.2f} m  yaw rms {r['yaw_rms']:8.2f} max {r['yaw_max']:8.2f} deg  "
              f"bgz {r['bgz_mean_dpm']:+8.1f} (true {r['true_bias_dpm']:.1f}) dpm  psi {r['psi_fused']}/{r['psi_valid']}")
json.dump(out, open(f'{SC}/a4.json', 'w'), indent=1)
