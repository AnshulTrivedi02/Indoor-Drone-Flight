import numpy as np, sys, math
TD = '/home/makerspace/thesis_data/trials/'


def tumyaw(p):
    a = np.loadtxt(p); x, y, z, w = a[:, 4], a[:, 5], a[:, 6], a[:, 7]
    return a[:, 0], np.unwrap(np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))


R2 = np.radians(0.126) ** 2
sub = sys.argv[1] if sys.argv[1].startswith('fgo') else 'fgo_heading'
trs = sys.argv[2:] if sys.argv[1].startswith('fgo') else sys.argv[1:]
for tr in trs:
    g = np.load(TD + tr + '/fwd_meas/gt_eval_only.npz')['g']
    gy = lambda t: np.interp(t, g[:, 0], g[:, 3]) - math.pi / 2
    z = np.load(TD + tr + f'/{sub}/timing_and_fwd.npz'); fl = z['fwd_log']; S = z['fwd_S']
    tf, yf = tumyaw(TD + tr + f'/{sub}/fgo_traj.tum')
    zu = np.load(TD + tr + '/ukf_heading/timing_and_fwd.npz'); nu = zu['nis_psi']; Su = zu['S_psi']
    tu, yu = tumyaw(TD + tr + '/ukf_heading/ukf_traj.tum')
    m = np.load(TD + tr + '/fwd_meas/meas_frozen.npz')
    print('=====', tr, sub, 'gt t0', g[0, 0], 'meas t range', m['t'][0], m['t'][-1])
    acc = fl[:, 3] > 0
    print('FGO fused times:', np.round(fl[acc, 0], 2))
    print('UKF fused n', int((nu[:, 2] > 0).sum()), 'first fused', nu[nu[:, 2] > 0, 0][:8])
    ps = m['psi'][:, 0]
    for T0 in [10, 12, 15, 20, 25, 30, 40, 60, 100, 150, 200, 250, 300]:
        i = np.searchsorted(fl[:, 0], T0); j = np.searchsorted(tf, T0); ju = np.searchsorted(tu, T0); iu = np.searchsorted(nu[:, 0], T0)
        if i >= len(fl) or j >= len(tf):
            continue
        ef = math.degrees(yf[j] - gy(tf[j])); eu = math.degrees(yu[ju] - gy(tu[ju]))
        k = np.searchsorted(m['t'], T0); mk = [kk for kk in range(k, min(k + 60, len(ps))) if np.isfinite(ps[kk])]
        merr = np.median([ps[kk] - math.degrees(gy(m['t'][kk])) for kk in mk]) if mk else float('nan')
        win = (fl[:, 0] >= T0 - 5) & (fl[:, 0] < T0)
        winu = (nu[:, 0] >= T0 - 5) & (nu[:, 0] < T0)
        sdf = math.degrees(math.sqrt(max(S[min(i, len(S) - 1)] - R2, 0)))
        sdu = math.degrees(math.sqrt(max(Su[min(iu, len(Su) - 1)] - R2, 0)))
        print(f't={T0:4d} FGO yawerr {ef:+9.3f} sd {sdf:7.3f} medNIS5s {np.median(fl[win,2]) if win.any() else np.nan:10.1f} acc {int(fl[win,3].sum())}/{win.sum()}'
              f' | UKF yawerr {eu:+8.3f} sd {sdu:6.3f} medNIS {np.median(nu[winu,1]) if winu.any() else np.nan:8.1f} acc {int(nu[winu,2].sum())}/{winu.sum()} | meas-GT med {merr:+.3f}')
