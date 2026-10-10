"""Pre-registered one-parameter decay test of the expansion mechanism on the D22 published flow (no images).
du/dt = -(zd/h) u + F (c_rot wx + c_lat v_left/h);  flow_x(frame) = [u(t_i) - u(t_{i-1})] / dt / F.
u is set from the first plateau frame only. Coefficients from METHODOLOGY "FINDING - lateral optical-flow sign"."""
import sys, json, numpy as np
F = 554.0
C_LAT = 1.004


def load(path):
    d = np.load(path)
    gt = d['gt'][np.argsort(d['gt'][:, 0])]
    return gt, d['fl'], d['att']


def model(gt, att, t_a, t_b, u_start, c_rot, with_exp=True, step=1e-3):
    tg, z = gt[:, 0], gt[:, 3]
    ts = np.arange(t_a, t_b + 1e-9, step)
    u = u_start; out = [u]
    for t in ts[:-1]:
        tm = t + step / 2
        zq = np.interp(tm, tg, z); h = zq - 0.25
        zd = (np.interp(tm + .02, tg, z) - np.interp(tm - .02, tg, z)) / .04
        vE = (np.interp(tm + .02, tg, gt[:, 1]) - np.interp(tm - .02, tg, gt[:, 1])) / .04
        wx = np.interp(tm, att[:, 0], att[:, 1])
        du = (-(zd / h) * u if with_exp else 0.0) + F * (c_rot * wx + C_LAT * (-vE) / h)
        u = u + du * step; out.append(u)
    return ts, np.array(out)


def run(path, t_lo, t_hi, c_rot, name):
    gt, fl, att = load(path)
    w = np.where((fl[:, 0] >= t_lo) & (fl[:, 0] <= t_hi) & (fl[:, 5] == 1))[0]
    i0 = w[0]
    t_prev0 = fl[i0 - 1, 0]
    # flow of frame i0 is linear in u_start: solve with two runs
    def frame_flows(u_start, with_exp=True):
        ts, u = model(gt, att, t_prev0, fl[w[-1], 0], u_start, c_rot, with_exp)
        res = []
        for i in w:
            ua = np.interp(fl[i - 1, 0], ts, u); ub = np.interp(fl[i, 0], ts, u)
            res.append((ub - ua) / (fl[i, 0] - fl[i - 1, 0]) / F)
        return np.array(res)
    f0, f1 = frame_flows(0.0), frame_flows(1.0)
    u_start = (fl[i0, 1] - f0[0]) / (f1[0] - f0[0])
    pred = frame_flows(u_start)
    null = frame_flows(0.0, with_exp=False)
    obs = fl[w, 1]
    return dict(name=name, c_rot=c_rot, t=(fl[w, 0]).tolist(), obs=obs.tolist(), pred=pred.tolist(),
                null=null.tolist(), cnt=fl[w, 3].tolist(), u_start=float(u_start),
                z=np.interp(fl[w, 0], gt[:, 0], gt[:, 3]).tolist())


def rms(a): return float(np.sqrt(np.mean(np.square(a)))) if len(a) else float('nan')


if __name__ == '__main__':
    out = []
    # (file, lift-off time from climb.py, name)
    for path, tl, name in [(sys.argv[1], 27.93, 'cl_ukf_b_tex_r3_half'), (sys.argv[2], 28.16, 'cl_fgo_b_tex_r3_half_v3')]:
        gt, fl, att = load(path)
        zf = np.interp(fl[:, 0], gt[:, 0], gt[:, 3])
        # z 1.07-1.6 window of valid climb frames (real_flights_plan 7.1a), start = first valid frame with z >= 1.05
        cand = np.where((fl[:, 0] > tl) & (fl[:, 0] < tl + 2) & (fl[:, 5] == 1) & (zf >= 1.05) & (zf <= 1.62))[0]
        t_lo, t_hi_full = fl[cand[0], 0], fl[cand[-1], 0]
        # primary window: end before the first count drop of >= 5
        cnts = fl[cand, 3]; drop = np.where(np.diff(cnts) <= -5)[0]
        t_hi_prim = fl[cand[drop[0]], 0] if len(drop) else t_hi_full
        for c_rot in (1.0, 1.5):
            for lab, th in (('primary', t_hi_prim), ('full_z1.07-1.6', t_hi_full)):
                r = run(path, t_lo, th, c_rot, name); r['window'] = lab
                o, p, n = np.array(r['obs'][1:]), np.array(r['pred'][1:]), np.array(r['null'][1:])
                r['rms_pred'], r['rms_null'], r['n'] = rms(o - p), rms(o - n), len(o)
                out.append(r)
                print(f"{name:26s} c_rot={c_rot} {lab:15s} n={len(o):2d} u0={r['u_start']:+7.1f}px "
                      f"RMS(obs-pred)={r['rms_pred']:.3f}  RMS(obs-null)={r['rms_null']:.3f}")
    json.dump(out, open(sys.argv[3], 'w'), indent=1)
