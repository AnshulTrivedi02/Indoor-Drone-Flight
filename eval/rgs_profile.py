import sys, os, json, numpy as np
sys.path.insert(0, os.path.expanduser("~/thesis_ws/eval")); import scale_check as S
res = {}
for path in sys.argv[1:]:
    S.TD, tr = os.path.dirname(path), os.path.basename(path)
    gt, fl, imu = S.read_bag(tr)
    t, z = gt[:, 0], gt[:, 3]
    vy = np.convolve(np.gradient(gt[:, 2], t), np.ones(51) / 51, "same")
    tc = t[vy > 0.3]; c0, c1 = tc[0], tc[-1]
    lift = t[np.argmax(z > 0.3)]; reach = t[np.argmax(z >= 1.8)]
    climb = (t >= lift) & (t <= c0)
    cw = (t > c0 + 5) & (t < c1 - 5)
    r = {"takeoff_s": float(reach - lift), "climb_peak_z": float(z[climb].max()), "cruise_z_mean": float(z[cw].mean()),
         "cruise_speed_mean": float(vy[cw].mean()), "cruise_s": float(c1 - c0), "gt_absx_max_cruise": float(np.abs(gt[cw, 1]).max())}
    ti = imu[:, 0]; sel = (ti > c0 + 5) & (ti < c1 - 5)
    for ax, nm in ((1, "x"), (2, "y"), (3, "z")):
        v = imu[sel, ax] - imu[sel, ax].mean(); f = np.fft.rfftfreq(len(v), 0.003)
        p = np.abs(np.fft.rfft(v * np.hanning(len(v)))) ** 2; ok = (f > 2) & (f < 160); b = (f > 15) & (f < 20)
        r[f"gyro_{nm}_rms"] = float(v.std()); r[f"gyro_{nm}_1520_rms"] = float(v.std() * np.sqrt(p[b].sum() / p[ok].sum()))
        r[f"gyro_{nm}_peak_hz"] = float(f[np.argmax(p * ok)])
    res[tr] = r
    print(tr, {k: round(v, 4) for k, v in r.items()})
if len(sys.argv) > 1 and os.environ.get("OUT"): json.dump(res, open(os.environ["OUT"], "w"), indent=1)
