"""Per bag: the first heading measurements, their NIS/accept in FGO and UKF, the meas error vs GT,
and the yaw-error slope just after (deg/s), FGO and UKF. Stored Phase-4 outputs only (read-only)."""
import numpy as np, sys, math, json
TD = '/home/makerspace/thesis_data/trials/'


def tumyaw(p):
    a = np.loadtxt(p); x, y, z, w = a[:, 4], a[:, 5], a[:, 6], a[:, 7]
    return a[:, 0], np.unwrap(np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))


sub = sys.argv[1]; trs = sys.argv[2:]
out = {}
for tr in trs:
    g = np.load(TD + tr + '/fwd_meas/gt_eval_only.npz')['g']
    gy = lambda t: np.interp(t, g[:, 0], g[:, 3]) - math.pi / 2
    z = np.load(TD + tr + f'/{sub}/timing_and_fwd.npz'); fl = z['fwd_log']; S = z['fwd_S']
    tf, yf = tumyaw(TD + tr + f'/{sub}/fgo_traj.tum')
    zu = np.load(TD + tr + '/ukf_heading/timing_and_fwd.npz'); nu = zu['nis_psi']; Su = zu['S_psi']
    tu, yu = tumyaw(TD + tr + '/ukf_heading/ukf_traj.tum')
    # GT takeoff: first time z rises 0.3 m above start
    gz = np.loadtxt(TD + tr + f'/{sub}/ground_truth.tum')
    t_to = gz[np.argmax(gz[:, 3] > gz[0, 3] + 0.3), 0]
    t0 = fl[0, 0]
    ef = lambda t: math.degrees(np.interp(t, tf, yf) - gy(t))
    eu = lambda t: math.degrees(np.interp(t, tu, yu) - gy(t))
    accF = fl[fl[:, 3] > 0, 0]
    # first lockout: first run of >= 3 s with no FGO acceptance while headings valid
    print(f'=== {tr} [{sub}] first heading t={t0:.2f}  GT takeoff t={t_to:.2f}  FGO fused {len(accF)}  first-2s fused {np.round(accF[accF < t0 + 2], 2)}')
    for i in range(8):
        tt = fl[i, 0]
        print(f'   t={tt:7.3f}  FGO nis {fl[i,2]:9.2f} ok {int(fl[i,3])} sd_pred {math.degrees(math.sqrt(S[i])):.3f}deg  e_yaw(FGO-GT) {ef(tt):+7.3f}'
              f' | UKF nis {nu[i,1]:8.2f} ok {int(nu[i,2])} sd_pred {math.degrees(math.sqrt(Su[i])):.3f}  e_yaw(UKF) {eu(nu[i,0]):+7.3f}')
    sF = (ef(t0 + 10) - ef(t0 + 1)) / 9.0; sU = (eu(t0 + 10) - eu(t0 + 1)) / 9.0
    print(f'   yaw-error slope t0+1..t0+10 s: FGO {sF:+.3f} deg/s ({60*sF:+.1f} deg/min)  UKF {sU:+.3f} deg/s')
    out[tr] = dict(t_first=float(t0), t_takeoff=float(t_to), fgo_fused=int(len(accF)), fgo_fused_first2s=accF[accF < t0 + 2].tolist(),
                   slope_fgo_dps=sF, slope_ukf_dps=sU, ef_end=ef(tf[-1]), eu_end=eu(tu[-1]))
json.dump(out, open(f'/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/pw/a2_{sub}.json', 'w'), indent=1)
