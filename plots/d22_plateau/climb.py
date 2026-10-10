import sys, numpy as np
F = 554.26
d = np.load(sys.argv[1])
gt, fl, rg, att = d["gt"], d["fl"], d["rg"], d["att"]
gt = gt[np.argsort(gt[:, 0])]
t = gt[:, 0]; z = gt[:, 3]
# GT vertical velocity: central difference over +-0.05 s
def deriv(tq, tt, yy, w=0.05):
    return (np.interp(tq + w, tt, yy) - np.interp(tq - w, tt, yy)) / (2 * w)
# first time z exceeds 0.3 (lift-off)
i_lo = np.argmax(z > 0.30)
tl = t[i_lo]
sel = (fl[:, 0] > tl - 0.5) & (fl[:, 0] < tl + 6)
print(f"lift-off t={tl:.2f}")
print(" t-tl   z     zdot  h_cam zdot/h  vE    vN   ωx(FRD) cnt  inl  valid flow_x  flow_y  need_off_px")
for r in fl[sel]:
    tq = r[0]
    zq = np.interp(tq, t, z)
    zd = deriv(tq, t, z)
    vE = deriv(tq, t, gt[:, 1]); vN = deriv(tq, t, gt[:, 2])
    h = zq - 0.25
    k = zd / h if h > 0.05 else np.nan
    wx = np.interp(tq, att[:, 0], att[:, 1]) if len(att) else np.nan
    need = -r[1] * F / k if (k and np.isfinite(k) and abs(k) > 1e-3) else np.nan
    print(f"{tq-tl:5.2f} {zq:5.2f} {zd:+5.2f} {h:5.2f} {k:+6.2f} {vE:+5.2f} {vN:+5.2f} {wx:+6.2f} {int(r[3]):3d} {r[4]:4.2f} {int(r[5])} {r[1]:+6.2f} {r[2]:+6.2f} {need:+8.0f}")
