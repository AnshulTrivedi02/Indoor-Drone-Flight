"""Figure for the plain-wall divergence trace (fwdplainc_tex_r1): (a) yaw error, first 3 s after the first heading;
(b) heading NIS and acceptance, FGO stored vs UKF stored; (c) yaw error over the flight, log-ish scale, four arms."""
import numpy as np, math, sys
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
SC = '/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/pw'
TD = '/home/makerspace/thesis_data/trials'; tr = 'fwdplainc_tex_r1'
OUT = sys.argv[1]
g = np.load(f'{TD}/{tr}/fwd_meas/gt_eval_only.npz')['g']
gy = lambda t: np.interp(t, g[:, 0], g[:, 3]) - math.pi / 2


def ye(p):
    a = np.loadtxt(p); x, y, z, w = a[:, 4], a[:, 5], a[:, 6], a[:, 7]
    yw = np.unwrap(np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))
    return a[:, 0], np.degrees(yw - gy(a[:, 0]))


arms = [('FGO, yaw0 σ 1e-3 rad (as run)', f'{TD}/{tr}/fgo_heading/fgo_traj.tum', 'C3', '-'),
        ('UKF, yaw0 σ 1° (as run)', f'{TD}/{tr}/ukf_heading/ukf_traj.tum', 'C0', '-'),
        ('FGO, yaw0 σ 1° (diagnostic)', f'{SC}/out/{tr}/fgo_heading_y0s1/fgo_traj.tum', 'C2', '--'),
        ('UKF, yaw0 σ 1e-3 rad (diagnostic)', f'{SC}/out/{tr}/ukf_heading_y0t/ukf_traj.tum', 'C1', '--')]
fig, ax = plt.subplots(3, 1, figsize=(9, 10))
fl = np.load(f'{TD}/{tr}/fgo_heading/timing_and_fwd.npz')['fwd_log']
nu = np.load(f'{TD}/{tr}/ukf_heading/timing_and_fwd.npz')['nis_psi']
t0 = fl[0, 0]
for lab, p, c, ls in arms:
    t, e = ye(p)
    w = (t >= t0 - 0.2) & (t <= t0 + 3)
    ax[0].plot(t[w] - t0, e[w], c, ls=ls, label=lab)
    ax[2].plot(t, e, c, ls=ls, label=lab)
ax[0].set_ylabel('yaw error (deg)'); ax[0].set_xlabel('s after the first valid heading (drone on the ground)')
ax[0].legend(fontsize=8); ax[0].grid(alpha=.3)
for (tt, n, ok), c, lab in ((fl[:, [0, 2, 3]].T, 'C3', 'FGO'), (nu[:, [0, 1, 2]].T, 'C0', 'UKF')):
    w = tt <= t0 + 3
    ax[1].semilogy(tt[w] - t0, n[w], '.', color=c, ms=4, label=f'{lab} heading NIS')
    a = w & (ok > 0)
    ax[1].semilogy(tt[a] - t0, n[a], 'o', mfc='none', color=c, ms=8, label=f'{lab} accepted')
ax[1].axhline(9, color='k', lw=.8); ax[1].set_ylabel('heading NIS (gate 9)'); ax[1].legend(fontsize=8); ax[1].grid(alpha=.3)
ax[1].set_xlabel('s after the first valid heading')
ax[2].set_ylabel('yaw error (deg, unwrapped)'); ax[2].set_xlabel('bag time (s)'); ax[2].set_yscale('symlog', linthresh=10)
ax[2].grid(alpha=.3)
fig.suptitle('fwdplainc_tex_r1, heading arm: the initial yaw prior decides yaw vs gyro-z bias')
fig.tight_layout(); fig.savefig(OUT, dpi=110)
print(OUT)
