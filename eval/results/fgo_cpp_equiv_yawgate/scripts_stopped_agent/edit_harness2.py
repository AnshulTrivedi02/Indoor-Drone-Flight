import sys
p = sys.argv[1] + '/eval/diag/model_audit/free_inertial.py'
s = open(p).read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)


rep('''    """Full chain + gtsam.Marginals. yawcap=True: the cap at EVERY keyframe (the pre-2026-10-09 behaviour);
    cap_keys: the cap only at these keyframe indices (the core's fired keyframes)."""''',
    '''    """Full chain + gtsam.Marginals. yawcap=True: the cap at EVERY keyframe (the pre-2026-10-09 behaviour);
    cap_keys: the cap only at these keyframe indices (the core's fired keyframes).
    Yaw-cap gate stage (2026-10-09): the marginal at each checkpoint is now taken from the chain TRUNCATED at that
    keyframe (the FILTERING marginal, what a fixed-lag smoother holds at its newest keyframe). The audit's version took
    every checkpoint from the full chain (the SMOOTHED marginal); the two differ only where later factors inform earlier
    states, i.e. with yaw caps (case C's FGO at 10 s), and agree at the last checkpoint."""''')
rep('''    k = 0; pose, vel = pose0, np.zeros(3); kf_next = T0 + 1.0 / 30.0; kts = []
    for i in range(n):''', '''    k = 0; pose, vel = pose0, np.zeros(3); kf_next = T0 + 1.0 / 30.0; kts = []
    want = {max(1, int(round(c * 30.0))) for c in CHK}
    times, rows = [], []
    for i in range(n):''')
rep('''            kts.append((k, t[i] - T0)); pim.resetIntegration(); kf_next += 1.0 / 30.0
    marg = gtsam.Marginals(graph, vals)
    times, rows = [], []
    want = sorted({min(kts, key=lambda kt: abs(kt[1] - c))[0] for c in CHK})
    for kk, tt in kts:
        if kk not in want:
            continue
        Rk = vals.atPose3(X(kk)).rotation().matrix()''', '''            kts.append((k, t[i] - T0)); pim.resetIntegration(); kf_next += 1.0 / 30.0
            if k not in want:
                continue
            kk, tt = k, t[i] - T0
            marg = gtsam.Marginals(graph, vals)            # chain up to keyframe k: the filtering marginal
            Rk = vals.atPose3(X(kk)).rotation().matrix()''')
rep('''        Cp = marg.marginalCovariance(X(kk)); Cv = marg.marginalCovariance(V(kk)); Cb = marg.marginalCovariance(B(kk))
        Cth = Rk @ Cp[0:3, 0:3] @ Rk.T; Ct = Rk @ Cp[3:6, 3:6] @ Rk.T
        rows.append(metrics((Cth[0, 0] + Cth[1, 1]) / 2, Cth[2, 2], (Cv[0, 0] + Cv[1, 1]) / 2, Cv[2, 2], (Ct[0, 0] + Ct[1, 1]) / 2,
                            Ct[2, 2], np.trace(Cb[3:6, 3:6]) / 3, np.trace(Cb[0:3, 0:3]) / 3)); times.append(tt)''',
    '''            Cp = marg.marginalCovariance(X(kk)); Cv = marg.marginalCovariance(V(kk)); Cb = marg.marginalCovariance(B(kk))
            Cth = Rk @ Cp[0:3, 0:3] @ Rk.T; Ct = Rk @ Cp[3:6, 3:6] @ Rk.T
            rows.append(metrics((Cth[0, 0] + Cth[1, 1]) / 2, Cth[2, 2], (Cv[0, 0] + Cv[1, 1]) / 2, Cv[2, 2],
                                (Ct[0, 0] + Ct[1, 1]) / 2, Ct[2, 2], np.trace(Cb[3:6, 3:6]) / 3, np.trace(Cb[0:3, 0:3]) / 3))
            times.append(tt)''')
open(p, 'w').write(s)
print("done")
