#!/usr/bin/env python3
"""D22 climb-plateau diagnostic figure + analogue summary statistics (venv-evo: numpy, matplotlib).

Inputs (produced by the scripts in this folder; kept in the session scratchpad, not committed):
  rep_<analogue>.npz   replay_tracker.py output on a bag WITH /downward_camera/image
  <analogue>.npz       extract.py output (published flow, GT) for the same bag
  decay.json           decay_test.py output for the two D22 flights (published flow + GT only)
Usage: make_figure.py SCRATCH_DIR OUT_DIR
"""
import sys, json, os, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

S, OUT = sys.argv[1], sys.argv[2]
F = 554.0


def analogue(rep, pub):
    r = np.load(os.path.join(S, rep)); d = np.load(os.path.join(S, pub))
    R, C = r['rows'], list(r['cols']); g = lambda n: R[:, C.index(n)]
    gt = d['gt'][np.argsort(d['gt'][:, 0])]; tg, z = gt[:, 0], gt[:, 3]
    t = g('t'); zq = np.interp(t, tg, z)
    zd = (np.interp(t + .05, tg, z) - np.interp(t - .05, tg, z)) / .1
    tl = tg[np.argmax(z > 0.30)]
    sel = (t > tl) & (t < tl + 2.5) & (g('valid') == 1) & (zq > 0.5) & (zq < 2.0) & np.isfinite(g('s'))
    dt = g('dt')
    out = dict(t=t[sel] - tl, z=zq[sel], fx=g('fx')[sel], fpp=(g('tpp_x') / dt / F)[sel],
               exp=((g('s') - 1) * g('offx_med') / dt / F)[sel], k_fit=(-(g('s') - 1) / dt)[sel],
               k_gt=(zd / (zq - 0.25))[sel], offx=g('offx_med')[sel], offy=g('offy_med')[sel], inl=g('inl')[sel])
    out['res'] = out['fx'] - out['fpp'] - out['exp']
    return out


def stats(name, a):
    rr = lambda v: float(np.sqrt(np.mean(v ** 2)))
    s = (f"{name}: n={len(a['fx'])} valid climb frames (z 0.5-2.0 m), inlier {a['inl'].min():.2f}-{a['inl'].max():.2f}; "
         f"peak flow_x {a['fx'].max():+.3f} rad/s; median-x offset at plateau start {a['offx'][0]:+.1f} px "
         f"(y {a['offy'][0]:+.1f} px); RMS flow_x {rr(a['fx']):.3f}; RMS flow@PP {rr(a['fpp']):.4f}; "
         f"RMS(flow_x - flow@PP - (s-1)*offx/dt/F) {rr(a['res']):.4f}; "
         f"fitted -(s-1)/dt over GT zdot/h_cam: median {np.median(a['k_fit'] / a['k_gt']):.3f} "
         f"(range {np.min(a['k_fit'] / a['k_gt']):.3f}-{np.max(a['k_fit'] / a['k_gt']):.3f})")
    print(s); return s


A1 = analogue('rep_h20.npz', 'tagh20.npz')
A2 = analogue('rep_check.npz', 'tagcheck.npz')
lines = [stats('tagchar_h20', A1), stats('tag_check2img', A2)]
D = json.load(open(os.path.join(S, 'decay.json')))
for r in D:
    lines.append(f"{r['name']} c_rot={r['c_rot']} window={r['window']} n={r['n']} u0={r['u_start']:+.1f}px "
                 f"RMS(obs-pred)={r['rms_pred']:.3f} RMS(obs-null)={r['rms_null']:.3f}")
open(os.path.join(OUT, 'summary.txt'), 'w').write('\n'.join(lines) + '\n')

fig, ax = plt.subplots(1, 3, figsize=(15, 4.6), constrained_layout=True)
a = ax[0]
a.plot(A1['z'], A1['fx'], 'o', ms=4, color='#1f77b4', label='published flow_x (median displacement)')
a.plot(A1['z'], A1['exp'], '-', color='#d62728', label='expansion term (s-1)·u_med/dt/F')
a.plot(A1['z'], A1['fpp'], 's', ms=3, color='#2ca02c', label='fitted similarity: translation at principal point')
a.axhline(0, color='k', lw=.5)
a.set(xlabel='GT z (m)', ylabel='flow_x (rad/s)',
      title='Analogue tagchar_h20 (images; replay exact)\nmedian offset −49 px → +0.23 rad/s, all inliers')
a.legend(fontsize=7.5)
a = ax[1]
a.plot(A1['z'], A1['k_gt'], '-', color='k', label='GT ż / h_cam')
a.plot(A1['z'], A1['k_fit'], 'o', ms=3, color='#9467bd', label='fitted −(s−1)/dt (RANSAC similarity)')
a.set(xlabel='GT z (m)', ylabel='1/s', title='Fitted scale rate = expected expansion rate\n(basis for checks (b) and (c))')
a.legend(fontsize=8)
a = ax[2]
cols = {'cl_ukf_b_tex_r3_half': '#1f77b4', 'cl_fgo_b_tex_r3_half_v3': '#ff7f0e'}
for r in D:
    if r['c_rot'] != 1.0 or not r['window'].startswith('full'):
        continue
    c = cols[r['name']]; short = 'UKF' if 'ukf' in r['name'] else 'FGO'
    a.plot(r['z'], r['obs'], 'o', ms=4, color=c, label=f'{short}: published flow_x')
    a.plot(r['z'], r['pred'], '-', color=c, label=f'{short}: 1-param expansion model (u0 {r["u_start"]:+.0f} px)')
    a.plot(r['z'], r['null'], ':', color=c, label=f'{short}: roll + lateral only (no expansion)')
a.axhline(0, color='k', lw=.5)
a.set(xlabel='GT z (m)', ylabel='flow_x (rad/s)',
      title='D22 flights (NO images): plateau vs prediction\nu0 from 1st frame; c_rot 1.0, c_lat 1.004 (METHODOLOGY)')
a.legend(fontsize=7)
fig.savefig(os.path.join(OUT, 'd22_plateau_expansion.png'), dpi=130)
print('wrote', OUT)
