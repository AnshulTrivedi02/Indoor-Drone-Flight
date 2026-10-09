import sys
p = sys.argv[1] + '/eval/diag/model_audit/free_inertial.py'
s = open(p).read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)


rep('''  C  as A, with the yaw-bounding mechanisms ON: UKF update_yaw_pseudo every 140 ms (variance-gated), FGO yaw cap
     factor (sigma 0.5 rad) at every keyframe; EKF3's fuseEulerYaw(PREDICTED) is variance-gated like the UKF's (its
     gate is reported from the harness's quaternion trace, not simulated).
Usage (~/venv-fgo): python3 free_inertial.py WINDOW.npz HARNESS OUT.json [T_TOTAL]"""''',
    '''  C  as A, with the yaw-bounding mechanisms ON: UKF update_yaw_pseudo every 140 ms (variance-gated), FGO yaw cap
     factor (sigma 0.5 rad); EKF3's fuseEulerYaw(PREDICTED) is variance-gated like the UKF's (its gate is reported
     from the harness's quaternion trace, not simulated).
  D  (yaw-cap gate stage, 2026-10-09) POSITIVE CONTROL: case B's configured bias sigmas with the yaw-bounding
     mechanisms ON, so that the gates must open (attitude variance grows with the 2.5 deg/s gyro-bias sigma).
FGO rows since the yaw-cap gate stage (2026-10-09, ruling "MODEL AUDIT RESULT ... RULINGS" item 2):
  fgo           fgo_core.FGO ITSELF (window 0.25 s, LM 2) driven keyframe by keyframe with no measurements, initialised
                with the case's priors (harness copy of FGO.init with those sigmas); its gate decides the cap. Values:
                the core's gate-only filtering covariance (cov_gate) at each keyframe.
  fgo_chain     the full-chain gtsam.Marginals (as the audit's FGO row) with the cap at exactly the keyframes where the
                core fired: checks the recursion against the smoother's marginal.
  fgo_ungated   case C/D only: the old behaviour, the cap at EVERY keyframe (full chain), for before/after.
Usage (~/venv-fgo): python3 free_inertial.py WINDOW.npz HARNESS OUT.json [T_TOTAL]"""''')

rep('''    return pick(times, rows), dict(stderr=r.stderr.strip(), quat_trace_max=max(qtr), yaw_gate_quat_trace=0.01)''',
    '''    t_open = next((tt for tt, q_ in zip(times, qtr) if q_ > 0.01), None)
    return pick(times, rows), dict(stderr=r.stderr.strip(), quat_trace_max=max(qtr), yaw_gate_quat_trace=0.01,
                                   gate_first_open_t=t_open)''')

rep('''    times, rows = [], []; fired = 0; tc = 0.0''', '''    times, rows = [], []; fired = 0; tc = 0.0; t_first = None''')
rep('''                    x, P, f = U.update_yaw_pseudo(x, P, p); fired += f; tc = t[i] - T0''',
    '''                    x, P, f = U.update_yaw_pseudo(x, P, p); fired += f; tc = t[i] - T0
                    t_first = t_first if (t_first is not None or not f) else t[i] - T0''')
rep('''                x, P, f = U.update_yaw_pseudo(x, P, p); fired += f; tc = bin_t[k]''',
    '''                x, P, f = U.update_yaw_pseudo(x, P, p); fired += f; tc = bin_t[k]
                t_first = t_first if (t_first is not None or not f) else bin_t[k]''')
rep('''    return pick(times, rows), dict(step_ms=1e3 * DT, yaw_pseudo_fired=fired)''',
    '''    return pick(times, rows), dict(step_ms=1e3 * DT, yaw_pseudo_fired=fired, first_fire_t=t_first)''')

rep('''def fgo(s_bg, s_ba, yawcap=False):''', '''def fgo(s_bg, s_ba, yawcap=False, cap_keys=None):
    """Full chain + gtsam.Marginals. yawcap=True: the cap at EVERY keyframe (the pre-2026-10-09 behaviour);
    cap_keys: the cap only at these keyframe indices (the core's fired keyframes)."""''')
rep('''            if yawcap:
                graph.add(F.yaw_prior_factor(yaw_noise, X(k), nk.pose().rotation().yaw()))''',
    '''            if yawcap or (cap_keys is not None and k in cap_keys):
                graph.add(F.yaw_prior_factor(yaw_noise, X(k), nk.pose().rotation().yaw()))''')
rep('''    return pick(times, rows), dict(keyframes=k)


_SIGMA_ORIG = U._sigma_points''', '''    return pick(times, rows), dict(keyframes=k)


def fgo_core_run(s_bg, s_ba, yawcap):
    """fgo_core.FGO itself, no measurements, keyframes at the replay's 1/30 s IMU-clock schedule. FGO.init is copied
    here only to set the case's prior sigmas (the core's own init uses the configured ones); everything after init
    (keyframe(), the gate, the cap, the recursion) is the core's code."""
    f = fgo_core.FGO(window=0.25, kf_dt=1.0 / 30.0, lm_maxiter=2)
    f.no_yawcap = not yawcap
    pose0 = gtsam.Pose3(gtsam.Rot3.Ypr(0.0, pitch0, roll0), np.array([0.0, 0.0, 2.0]))
    bias0 = gtsam.imuBias.ConstantBias(np.zeros(3), np.zeros(3))
    pose_sig = np.array([S_ATT] * 3 + [S_P] * 3); vel_sig = np.array([S_V] * 3); bias_sig = np.array([s_ba] * 3 + [s_bg] * 3)
    g0 = gtsam.NonlinearFactorGraph(); v0 = gtsam.Values()
    g0.add(gtsam.PriorFactorPose3(X(0), pose0, gtsam.noiseModel.Diagonal.Sigmas(pose_sig)))
    g0.add(gtsam.PriorFactorVector(V(0), np.zeros(3), gtsam.noiseModel.Diagonal.Sigmas(vel_sig)))
    g0.add(gtsam.PriorFactorConstantBias(B(0), bias0, gtsam.noiseModel.Diagonal.Sigmas(bias_sig)))
    v0.insert(X(0), pose0); v0.insert(V(0), np.zeros(3)); v0.insert(B(0), bias0)
    f.smoother.update(g0, v0, fgo_core._tsmap({X(0): T0, V(0): T0, B(0): T0}))
    f.cov_gate = np.diag(np.concatenate([pose_sig, vel_sig, bias_sig]) ** 2)
    f.t_yawchk = T0
    f.prev_pose, f.prev_vel, f.prev_bias = pose0, np.zeros(3), bias0
    f.t_last = T0; f.last = (T0, pose0, np.zeros(3))
    times, rows = [], []
    kf_next = T0 + 1.0 / 30.0
    for i in range(n):
        f.integrate_imu(acc[i], gyro[i], dts[i])
        if t[i] >= kf_next - 1e-9:
            f.keyframe(kf_next)
            C = f.cov_gate; Rk = f.prev_pose.rotation().matrix()
            Cth = Rk @ C[0:3, 0:3] @ Rk.T; Ct = Rk @ C[3:6, 3:6] @ Rk.T
            rows.append(metrics((Cth[0, 0] + Cth[1, 1]) / 2, Cth[2, 2], (C[6, 6] + C[7, 7]) / 2, C[8, 8],
                                (Ct[0, 0] + Ct[1, 1]) / 2, Ct[2, 2], np.trace(C[12:15, 12:15]) / 3, np.trace(C[9:12, 9:12]) / 3))
            times.append(kf_next - T0)
            kf_next += 1.0 / 30.0
    fired = [(e[0] - T0, e[1]) for e in f.yawgate_log if e[3]]
    tr = [e[2] for e in f.yawgate_log]
    return pick(times, rows), dict(keyframes=f.k, checks=f.n_yaw_check, fired=f.n_yaw_fire,
                                   first_fire_t=(fired[0][0] if fired else None), trace_max=(max(tr) if tr else None),
                                   gate=fgo_core.ATT_VAR_GATE, yaw_dt=fgo_core.YAW_DT), {k_ for _, k_ in fired}


_SIGMA_ORIG = U._sigma_points''')

rep('''                                                 "C": (S_BG_A, S_BA_A, S_BG_A, S_BA_A, True)}.items():
    if case == "B" and T_TOTAL > 10.0:
        continue''', '''                                                 "C": (S_BG_A, S_BA_A, S_BG_A, S_BA_A, True),
                                                 "D": (S_BG_B_EKF, S_BA_B, S_BG_B_OURS, S_BA_B, True)}.items():
    if case in ("B", "D") and T_TOTAL > 10.0:
        continue''')
rep('''    if case == "B":
        r["analytic_ekf3init"] = analytic(sbg_e, sba_e)''', '''    if case in ("B", "D"):
        r["analytic_ekf3init"] = analytic(sbg_e, sba_e)''')
rep('''    r["ukf_offline"], r["ukf_offline_info"] = ukf(sbg_o, sba_o, "offline", yawcap=(case == "C"))
    r["ukf_port"], r["ukf_port_info"] = ukf(sbg_o, sba_o, "port", yawcap=(case == "C"))''',
    '''    r["ukf_offline"], r["ukf_offline_info"] = ukf(sbg_o, sba_o, "offline", yawcap=yc)
    r["ukf_port"], r["ukf_port_info"] = ukf(sbg_o, sba_o, "port", yawcap=yc)''')
rep('''    r["fgo"], r["fgo_info"] = fgo(sbg_o, sba_o, yawcap=(case == "C"))''',
    '''    r["fgo"], r["fgo_info"], fired_keys = fgo_core_run(sbg_o, sba_o, yawcap=yc)
    r["fgo_chain"], r["fgo_chain_info"] = fgo(sbg_o, sba_o, cap_keys=fired_keys)
    if yc:
        r["fgo_ungated"], r["fgo_ungated_info"] = fgo(sbg_o, sba_o, yawcap=True)''')
open(p, 'w').write(s)
print("done")
