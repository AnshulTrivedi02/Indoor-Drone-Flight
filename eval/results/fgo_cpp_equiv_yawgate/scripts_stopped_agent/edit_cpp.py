import sys
ROOT = sys.argv[1]
s = None


def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)


p = ROOT + '/src/estimators/fgo_cpp/include/fgo_cpp/fgo_core.h'
s = open(p).read()
rep('// CombinedImuFactor over every IMU sample, IMU-predicted zero-innovation yaw cap per keyframe, flow and range',
    '// CombinedImuFactor over every IMU sample, IMU-predicted zero-innovation yaw cap (variance-gated), flow and range')
rep('''constexpr double ACCEL_B0 = 0.2;       // EKF3 initial accel-bias 1 sigma (m/s^2)
''', '''constexpr double ACCEL_B0 = 0.2;       // EKF3 initial accel-bias 1 sigma (m/s^2)
// §9.4 yaw cap, VARIANCE-GATED (user ruling 2026-10-09, METHODOLOGY "MODEL AUDIT RESULT ... RULINGS" item 2): as EKF3's
// fuseEulerYaw(PREDICTED) and ukf_core.update_yaw_pseudo; fgo_core.py YAW_DT / ATT_VAR_GATE.
constexpr double YAW_DT = 0.14;        // fire opportunity every 140 ms (MagFusion.cpp:263)
constexpr double ATT_VAR_GATE = 0.04;  // fire only if trace(predicted attitude cov) > 0.04 rad^2 (MagFusion.cpp:274)

struct YawGateEntry {   // fgo_core.yawgate_log: (t, k, trace of the predicted attitude cov, fired)
  double t;
  int k;
  double trace;
  bool fired;
};
''')
rep('''  gtsam::Matrix cov_prev;                // 15x15, empty until set
''', '''  gtsam::Matrix cov_prev;                // 15x15, empty until set
  // §9.4 yaw-cap gate (ruling 2026-10-09): the same recursion, run whenever the cap is active (equal to cov_prev
  // under log_cov); cov_prev and reanchor() keep their old semantics.
  gtsam::Matrix cov_gate;
  double t_yawchk = 0.0;
  int n_yaw_check = 0, n_yaw_fire = 0;
  std::vector<YawGateEntry> yawgate_log;
''')
rep('''  gtsam::Matrix info(const gtsam::NonlinearFactorGraph& factors, const gtsam::Values& values, int km1, int kk) const;''',
    '''  gtsam::Matrix info(const gtsam::NonlinearFactorGraph& factors, const gtsam::Values& values, int km1, int kk,
                     const gtsam::Matrix* prior = nullptr) const;''')
rep('''  gtsam::Matrix posterior_cov(const gtsam::NonlinearFactorGraph& g, const gtsam::Values& est, int km1, int kk) const;''',
    '''  gtsam::Matrix posterior_cov(const gtsam::NonlinearFactorGraph& g, const gtsam::Values& est, int km1, int kk,
                              const gtsam::Matrix* prior = nullptr) const;
  double att_trace_pred(const gtsam::NonlinearFactorGraph& g, int km1, int kk, const Pose3& Xk, const Vector& Vk) const;''')
open(p, 'w').write(s)

p = ROOT + '/src/estimators/fgo_cpp/src/fgo_core.cpp'
s = open(p).read()
rep('''  if (log_cov) {
    gtsam::Vector s(15);
    s << pose_sig, 0.1, 0.1, 0.1, bias_sig;
    cov_prev = diag_sq(s);
  }
  prev_pose = pose0; prev_vel = vel0; prev_bias = bias0;''', '''  gtsam::Vector s0(15);
  s0 << pose_sig, 0.1, 0.1, 0.1, bias_sig;
  if (log_cov) cov_prev = diag_sq(s0);
  cov_gate = diag_sq(s0);
  t_yawchk = t0;                       // as ukf_replay: the first check 140 ms after init
  prev_pose = pose0; prev_vel = vel0; prev_bias = bias0;''')
rep('''  // §9.4 yaw cap: anchored to THIS keyframe's IMU-predicted yaw (zero innovation)
  long i_yawcap = -1;
  if (!no_yawcap) {
    i_yawcap = static_cast<long>(g.size());
    g.add(YawPriorFactor(yaw_noise_, X(kk), Xk.rotation().yaw()));
  }''', '''  // §9.4 yaw cap: anchored to THIS keyframe's IMU-predicted yaw (zero innovation).
  // VARIANCE-GATED (user ruling 2026-10-09, METHODOLOGY "MODEL AUDIT RESULT ... RULINGS" item 2; FGO_DESIGN §9.4): at
  // most one cap per 140 ms check, and only if the trace of THIS keyframe's predicted attitude covariance (gate-only
  // recursion: last keyframe's filtering cov + this IMU factor, before range/flow/forward) > 0.04 rad^2.
  long i_yawcap = -1;
  const bool cap_on = !no_yawcap;
  if (cap_on && t - t_yawchk >= YAW_DT) {
    t_yawchk = t;
    const double tr = att_trace_pred(g, km1, kk, Xk, Vk);
    const bool fire = tr > ATT_VAR_GATE;
    ++n_yaw_check;
    n_yaw_fire += fire ? 1 : 0;
    yawgate_log.push_back({t, kk, tr, fire});
    if (fire) {
      i_yawcap = static_cast<long>(g.size());
      g.add(YawPriorFactor(yaw_noise_, X(kk), Xk.rotation().yaw()));
    }
  }''')
rep('''  if (log_cov) cov_prev = posterior_cov(g, est, km1, kk);''', '''  if (log_cov) {
    cov_prev = posterior_cov(g, est, km1, kk);
    cov_gate = cov_prev;                   // the same recursion (the gate prior equals cov_prev)
  } else if (cap_on) {
    cov_gate = posterior_cov(g, est, km1, kk, &cov_gate);
  }''')
rep('''  if (log_cov) {
    gtsam::Vector s(15);
    s << pose_sig, vel_sig, bias_sig;
    cov_prev = diag_sq(s);
  }
  prev_pose = pose; prev_vel = vel;''', '''  gtsam::Vector s15(15);
  s15 << pose_sig, vel_sig, bias_sig;
  if (log_cov) cov_prev = diag_sq(s15);
  cov_gate = diag_sq(s15);                 // yaw-cap gate (keep_yawcap)
  prev_pose = pose; prev_vel = vel;''')
rep('''gtsam::Matrix FGO::info(const gtsam::NonlinearFactorGraph& factors, const gtsam::Values& values, int km1, int kk) const {''',
    '''gtsam::Matrix FGO::info(const gtsam::NonlinearFactorGraph& factors, const gtsam::Values& values, int km1, int kk,
                        const gtsam::Matrix* prior) const {''')
rep('''  L.topLeftCorner(15, 15) = cov_prev.inverse();''', '''  L.topLeftCorner(15, 15) = (prior == nullptr ? cov_prev : *prior).inverse();''')
rep('''gtsam::Matrix FGO::posterior_cov(const gtsam::NonlinearFactorGraph& g, const gtsam::Values& est, int km1, int kk) const {
  const gtsam::Values v = values_for(km1, kk, est.at<Pose3>(X(kk)), est.at<Vector>(V(kk)), est.at<Bias>(B(kk)), &est);
  const gtsam::Matrix cov = info(g, v, km1, kk).inverse().block(15, 15, 15, 15);
  return 0.5 * (cov + cov.transpose());
}''', '''gtsam::Matrix FGO::posterior_cov(const gtsam::NonlinearFactorGraph& g, const gtsam::Values& est, int km1, int kk,
                                 const gtsam::Matrix* prior) const {
  const gtsam::Values v = values_for(km1, kk, est.at<Pose3>(X(kk)), est.at<Vector>(V(kk)), est.at<Bias>(B(kk)), &est);
  const gtsam::Matrix cov = info(g, v, km1, kk, prior).inverse().block(15, 15, 15, 15);
  return 0.5 * (cov + cov.transpose());
}

// §9.4 gate quantity (fgo_core._att_trace_pred): trace of X(kk)'s PREDICTED rotation-tangent covariance, from cov_gate +
// this keyframe's IMU factor (g holds only it when called), linearised at the IMU prediction.
double FGO::att_trace_pred(const gtsam::NonlinearFactorGraph& g, int km1, int kk, const Pose3& Xk, const Vector& Vk) const {
  const gtsam::Matrix cov = info(g, values_for(km1, kk, Xk, Vk, prev_bias, nullptr), km1, kk, &cov_gate).inverse();
  return cov(15, 15) + cov(16, 16) + cov(17, 17);   // left to right, as the Python
}''')
open(p, 'w').write(s)
print("done")
