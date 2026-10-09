"""Per-keyframe gyro-z bias and yaw around the first heading acceptances, from the equivalence dumps
(base = unmodified FGO; y0s1 = initial yaw sigma 1 deg), plus the yaw-cap gate log over the same span."""
import numpy as np, json, math, sys
SC = '/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/pw'
TD = '/home/makerspace/thesis_data/trials'
g = np.load(f'{TD}/fwdplainc_tex_r1/fwd_meas/gt_eval_only.npz')['g']
out = {}
for tag in ('base',):
    kf = np.fromfile(f'{SC}/dump/{tag}_tex_r1.kf.f64').reshape(-1, 40)
    yg = np.fromfile(f'{SC}/dump/{tag}_tex_r1.yawgate.f64').reshape(-1, 4)
    t = kf[:, 0]; R = kf[:, 13:22].reshape(-1, 3, 3); yaw = np.unwrap(np.arctan2(R[:, 1, 0], R[:, 0, 0]))
    bgz = np.degrees(kf[:, 30])            # rad/s -> deg/s
    nis, ok = kf[:, 31], kf[:, 32]
    gy = np.interp(t, g[:, 0], g[:, 3]) - math.pi / 2
    e = np.degrees(yaw - gy)
    print(f'===== {tag}: keyframes {len(t)}; yaw-cap checks {len(yg)}, fired {int(yg[:,3].sum())}')
    sel = np.where(t < t[0] + 1.2)[0]
    for i in sel:
        print(f'  t={t[i]:7.3f} bgz {bgz[i]:+8.3f} deg/s  yaw err {e[i]:+7.3f} deg  heading nis {nis[i]:9.2f} ok {ok[i]:.0f}')
    for T0 in (12, 20, 28, 60, 200):
        i = np.searchsorted(t, T0)
        print(f'  t={T0:4d}: bgz {bgz[i]:+8.3f} deg/s ({60*bgz[i]:+7.1f} dpm)  yaw err {e[i]:+9.2f} deg')
    pre = yg[yg[:, 0] < 28.0]
    print(f'  yaw-cap gate before take-off (t<28 s): checks {len(pre)}, fired {int(pre[:,3].sum())}, trace max {pre[:,2].max():.3g} (gate 0.04)')
    out[tag] = dict(t=t[sel].tolist(), bgz_dps=bgz[sel].tolist(), yaw_err_deg=e[sel].tolist(), nis=nis[sel].tolist(), ok=ok[sel].tolist(),
                    bgz_dps_at={str(T0): float(bgz[np.searchsorted(t, T0)]) for T0 in (12, 20, 28, 60, 200)},
                    cap_pre_takeoff=dict(checks=int(len(pre)), fired=int(pre[:, 3].sum()), trace_max=float(pre[:, 2].max())),
                    cap_total=dict(checks=int(len(yg)), fired=int(yg[:, 3].sum())))
json.dump(out, open(f'{SC}/a5.json', 'w'), indent=1)
