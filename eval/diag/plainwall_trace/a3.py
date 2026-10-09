"""Stored Phase-4 outputs: (1) the late FGO acceptances are wrap-through passes (yaw error mod 360 ~ 0);
(2) lockout statistics: first rejection streak, longest streak, accepted fraction by phase."""
import numpy as np, math, json, sys
TD = '/home/makerspace/thesis_data/trials/'


def tumyaw(p):
    a = np.loadtxt(p); x, y, z, w = a[:, 4], a[:, 5], a[:, 6], a[:, 7]
    return a[:, 0], np.unwrap(np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))


res = {}
for tr in sys.argv[1:]:
    g = np.load(TD + tr + '/fwd_meas/gt_eval_only.npz')['g']
    gy = lambda t: np.interp(t, g[:, 0], g[:, 3]) - math.pi / 2
    z = np.load(TD + tr + '/fgo_heading/timing_and_fwd.npz'); fl = z['fwd_log']
    tf, yf = tumyaw(TD + tr + '/fgo_heading/fgo_traj.tum')
    acc = fl[fl[:, 3] > 0, 0]
    e = np.degrees(np.interp(acc, tf, yf) - gy(acc))
    emod = (e + 180) % 360 - 180
    # first acceptance and the rejection streak after it
    t1 = acc[0]; later = acc[acc > t1 + 1.0]
    rej_after = fl[(fl[:, 0] > acc[acc < t1 + 2][-1])]
    first_gap = (later[0] if len(later) else np.nan) - acc[acc < t1 + 2][-1]
    # whole-flight yaw-error slope
    w = (tf > t1 + 1)
    sl = np.polyfit(tf[w], np.degrees(yf[w] - gy(tf[w])), 1)[0]
    print(f'== {tr}: accepted {len(acc)}; late acceptances (t>{t1+2:.1f}): t =', np.round(later, 1))
    print('   yaw err at acceptances (unwrapped):', np.round(e, 1))
    print('   yaw err mod 360                   :', np.round(emod, 2))
    print(f'   slope {sl:+.3f} deg/s -> 360/slope = {360/abs(sl):.1f} s; first gap after the initial burst {first_gap:.1f} s')
    res[tr] = dict(acc_t=acc.tolist(), err_unwrapped=e.tolist(), err_mod360=emod.tolist(), slope_dps=float(sl),
                   wrap_period_s=float(360 / abs(sl)), first_gap_s=float(first_gap))
json.dump(res, open('/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/pw/a3.json', 'w'), indent=1)
