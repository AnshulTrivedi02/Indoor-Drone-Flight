import sys, numpy as np
rep = np.load(sys.argv[1]); pub = np.load(sys.argv[2]); F = 554.0
R = rep['rows']; C = list(rep['cols']); gt = pub['gt']; gt = gt[np.argsort(gt[:, 0])]
g = lambda n: R[:, C.index(n)]
t = g('t'); tg, z = gt[:, 0], gt[:, 3]
zq = np.interp(t, tg, z)
zd = (np.interp(t + .05, tg, z) - np.interp(t - .05, tg, z)) / .1
h = zq - 0.25
tl = tg[np.argmax(z > 0.30)]
sel = (t > tl - 0.1) & (t < tl + float(sys.argv[3]) if len(sys.argv) > 3 else t < tl + 2.5) & (g('pub') == 1)
print(' t-tl  z    zd/h  -(s-1)/dt  cnt inl  offx_med offy_med  flow_x  flowx@PP  (s-1)*offx/dt/F  fitmed-tpp  res')
for i in np.where(sel)[0]:
    dt = g('dt')[i]; s = g('s')[i]
    k = zd[i] / h[i] if h[i] > .05 else np.nan
    fpp = g('tpp_x')[i] / dt / F
    exp_term = (s - 1) * g('offx_med')[i] / dt / F
    res = g('fx')[i] - fpp - exp_term
    print(f"{t[i]-tl:5.2f} {zq[i]:4.2f} {k:+5.2f} {-(s-1)/dt:+7.2f}  {int(g('cnt')[i]):3d} {g('inl')[i]:4.2f} "
          f"{g('offx_med')[i]:+7.1f} {g('offy_med')[i]:+7.1f}  {g('fx')[i]:+6.3f}  {fpp:+6.3f}   {exp_term:+6.3f}"
          f"   {(g('fitmed_dx')[i]-g('tpp_x')[i])/dt/F:+6.3f}  {res:+6.3f}")
