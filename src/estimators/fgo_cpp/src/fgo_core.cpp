// C++ port of src/estimators/fgo/fgo_core.py and measurement_models.GroundProximityFlow.
// Graph construction keeps the Python order: IMU factor, yaw cap, range, flow, forward (gated), tag, GNSS;
// values X, V, B. Line references are to fgo_core.py.
#include "fgo_cpp/fgo_core.h"

#include <cmath>
#include <map>

#include <gtsam/inference/Symbol.h>
#include <gtsam/linear/JacobianFactor.h>
#include <gtsam/navigation/NavState.h>
#include <gtsam/nonlinear/LevenbergMarquardtParams.h>
#include <gtsam/slam/PriorFactor.h>

namespace fgo_cpp {

using gtsam::symbol_shorthand::B;
using gtsam::symbol_shorthand::V;
using gtsam::symbol_shorthand::X;

namespace {
inline double np_radians(double deg) { return deg * (M_PI / 180.0); }   // numpy.radians: x * (pi / 180)
gtsam::FixedLagSmoother::KeyTimestampMap tsmap(int kk, double t) {
  gtsam::FixedLagSmoother::KeyTimestampMap ts;
  ts[X(kk)] = t; ts[V(kk)] = t; ts[B(kk)] = t;
  return ts;
}
// numpy: np.diag(v) ** 2
gtsam::Matrix diag_sq(const gtsam::Vector& v) {
  gtsam::Matrix M = gtsam::Matrix::Zero(v.size(), v.size());
  for (int i = 0; i < v.size(); ++i) M(i, i) = v[i] * v[i];
  return M;
}
constexpr int DIMS[3] = {6, 3, 6};
}  // namespace

boost::shared_ptr<gtsam::PreintegrationCombinedParams> make_pim_params() {
  auto p = gtsam::PreintegrationCombinedParams::MakeSharedU(9.81);   // ENU Z-up, +9.81 at rest
  p->setAccelerometerCovariance(gtsam::Matrix3::Identity() * 1.53125e-3);   // NSE*sqrt(dt), FGO §5
  p->setGyroscopeCovariance(gtsam::Matrix3::Identity() * 2.8125e-6);
  p->setBiasAccCovariance(gtsam::Matrix3::Identity() * 5.0e-6);
  p->setBiasOmegaCovariance(gtsam::Matrix3::Identity() * 1.25e-8);
  p->setIntegrationCovariance(gtsam::Matrix3::Identity() * 1e-8);          // conditioning floor (unmatched)
  gtsam::Vector6 d;
  d << 0.2 * 0.2, 0.2 * 0.2, 0.2 * 0.2, 0.043633 * 0.043633, 0.043633 * 0.043633, 0.043633 * 0.043633;
  p->setBiasAccOmegaInit(d.asDiagonal().toDenseMatrix());
  return p;
}

FGO::FGO(double window, double kf_dt_, int lm_maxiter, const FwdConfig& fwd, bool log_cov_)
    : kf_dt(kf_dt_), log_cov(log_cov_ || fwd.enabled), window_(window), lm_maxiter_(lm_maxiter), fwd_(fwd) {
  gtsam::LevenbergMarquardtParams lm;
  lm.setMaxIterations(lm_maxiter);
  smoother_.reset(new gtsam::BatchFixedLagSmoother(window, lm));
  pim_.reset(new gtsam::PreintegratedCombinedMeasurements(make_pim_params(), Bias(Vector3::Zero(), Vector3::Zero())));
  flow_noise_ = gtsam::noiseModel::Isotropic::Sigma(2, 0.25);    // FLOW_M_NSE
  range_noise_ = gtsam::noiseModel::Isotropic::Sigma(1, 0.5);    // RNG_M_NSE
  yaw_noise_ = gtsam::noiseModel::Isotropic::Sigma(1, 0.5);      // EK3_YAW_M_NSE, §9.4
  if (fwd.enabled) {
    heading_noise_ = gtsam::noiseModel::Isotropic::Sigma(1, fwd.sigma_psi);
    if (!std::isnan(fwd.sigma_omega)) yawrate_noise_ = gtsam::noiseModel::Isotropic::Sigma(1, fwd.sigma_omega);
  }
}

void FGO::init(const Vector3& a, double first_range, double t0) {
  const double roll0 = std::atan2(a[1], a[2]);
  const double pitch0 = std::atan2(-a[0], std::hypot(a[1], a[2]));
  const Pose3 pose0(gtsam::Rot3::Ypr(0.0, pitch0, roll0), gtsam::Point3(0.0, 0.0, first_range + 0.12));
  const Vector vel0 = Vector::Zero(3);
  const Bias bias0(Vector3::Zero(), Vector3::Zero());
  gtsam::NonlinearFactorGraph g;
  gtsam::Values vals;
  gtsam::Vector6 pose_sig;
  pose_sig << np_radians(2), np_radians(2), 1e-3, 1e-3, 1e-3, 0.5;   // [roll,pitch,yaw, x,y,z] (§8)
  g.add(gtsam::PriorFactor<Pose3>(X(0), pose0, gtsam::noiseModel::Diagonal::Sigmas(pose_sig)));
  g.add(gtsam::PriorFactor<Vector>(V(0), vel0, gtsam::noiseModel::Isotropic::Sigma(3, 0.1)));
  gtsam::Vector6 bias_sig;
  bias_sig << ACCEL_B0, ACCEL_B0, ACCEL_B0, GYRO_B0, GYRO_B0, GYRO_B0;
  g.add(gtsam::PriorFactor<Bias>(B(0), bias0, gtsam::noiseModel::Diagonal::Sigmas(bias_sig)));
  vals.insert(X(0), pose0);
  vals.insert(V(0), vel0);
  vals.insert(B(0), bias0);
  smoother_->update(g, vals, tsmap(0, t0));
  if (batch_record) {
    all_g = gtsam::NonlinearFactorGraph();
    all_g.push_back(g);
    all_est = gtsam::Values();
    all_est.insert(X(0), pose0); all_est.insert(V(0), vel0); all_est.insert(B(0), bias0);
    key_t.clear();
  }
  if (log_cov) {
    gtsam::Vector s(15);
    s << pose_sig, 0.1, 0.1, 0.1, bias_sig;
    cov_prev = diag_sq(s);
  }
  prev_pose = pose0; prev_vel = vel0; prev_bias = bias0;
  t_last = t0;
}

void FGO::integrate_imu(const Vector3& accel, const Vector3& gyro, double dt) {
  if (0 < dt && dt < 0.2) {
    pim_->integrateMeasurement(accel, gyro, dt);
    ++n_imu;
  }
}

void FGO::keyframe(double t, const FlowMeas* flow, const Vector3& omega, double rng, const FwdMeas* fwd,
                   const gtsam::Vector3* tag, const gtsam::Vector4* gnss) {
  if (pim_->deltaTij() <= 0) return;   // no IMU since last keyframe - skip (§8)
  const int km1 = k, kk = k + 1;
  const gtsam::NavState pred = pim_->predict(gtsam::NavState(prev_pose, Vector3(prev_vel)), prev_bias);
  const Pose3 Xk = pred.pose();
  const Vector Vk = Vector(pred.velocity());
  gtsam::NonlinearFactorGraph g;
  gtsam::Values vals;
  vals.insert(X(kk), Xk);
  vals.insert(V(kk), Vk);
  vals.insert(B(kk), prev_bias);
  g.add(gtsam::CombinedImuFactor(X(km1), V(km1), X(kk), V(kk), B(km1), B(kk), *pim_));
  // §9.4 yaw cap: anchored to THIS keyframe's IMU-predicted yaw (zero innovation)
  long i_yawcap = -1;
  if (!no_yawcap) {
    i_yawcap = static_cast<long>(g.size());
    g.add(YawPriorFactor(yaw_noise_, X(kk), Xk.rotation().yaw()));
  }
  if (!std::isnan(rng) && 0.05 <= rng && rng <= 40.0) {
    g.add(RangeFactor(range_noise_, X(kk), rng));
    ++n_range;
  }
  if (flow != nullptr) {
    if (flow->valid && flow->inlier > 0.0 && std::abs(flow->xy[0]) < 4.2 && std::abs(flow->xy[1]) < 4.2) {
      g.add(FlowFactor(flow_noise_, X(kk), V(kk), B(kk), flow->xy, omega));
      ++n_flow;
    }
  }
  if (fwd_.enabled) forward_factors(g, t, km1, kk, Xk, Vk, fwd);
  if (tag != nullptr && tag_noise) {                 // experiment T: tag fix (no gate, pre-registered)
    g.add(TagFactor(tag_noise, X(kk), (*tag)[0], (*tag)[1], (*tag)[2]));
    ++n_tag;
  }
  if (gnss != nullptr && gnss_noise) {               // experiment O: GNSS fix (no gate)
    g.add(GnssFactor(gnss_noise, X(kk), V(kk), *gnss));
    ++n_gnss;
  }
  smoother_->update(g, vals, tsmap(kk, t));
  const gtsam::Values est = smoother_->calculateEstimate();
  if (batch_record) {
    for (size_t i = 0; i < g.size(); ++i)
      if (!(batch_drop_yawcap && static_cast<long>(i) == i_yawcap)) all_g.push_back(g.at(i));
    for (const auto& kv : est) {
      if (all_est.exists(kv.key)) all_est.update(kv.key, kv.value);
      else all_est.insert(kv.key, kv.value);
    }
  }
  if (log_cov) cov_prev = posterior_cov(g, est, km1, kk);
  prev_pose = est.at<Pose3>(X(kk));
  prev_vel = est.at<Vector>(V(kk));
  prev_bias = est.at<Bias>(B(kk));
  pim_->resetIntegrationAndSetBias(prev_bias);
  k = kk;
  t_last = t;
  if (batch_record) key_t.emplace_back(kk, t);
}

// ---------- experiment T / O: first-fix re-anchor (fgo_core.reanchor) ----------
void FGO::reanchor(double pE, double pN, double yaw_fix, double sig_pos, double sig_yaw, const double* vel_EN,
                   double sig_vel, bool keep_yawcap) {
  const Vector3 rpy = prev_pose.rotation().rpy();
  const double r = rpy[0], pch = rpy[1], y = rpy[2];
  const double d = wrap(yaw_fix - y);
  const double c = std::cos(d), s_ = std::sin(d);
  gtsam::Matrix3 R3;
  R3 << c, -s_, 0, s_, c, 0, 0, 0, 1.0;
  const Pose3 pose(gtsam::Rot3::Ypr(yaw_fix, pch, r), gtsam::Point3(pE, pN, prev_pose.translation()[2]));
  Vector vel = Vector(R3 * Vector3(prev_vel));
  const Bias bias = prev_bias;
  gtsam::Matrix C;
  if (cov_prev.size() != 0) {
    C = cov_prev;
  } else {
    gtsam::Vector s(15);
    s << np_radians(2), np_radians(2), 1e-3, 1e-3, 1e-3, 0.5, 0.1, 0.1, 0.1, ACCEL_B0, ACCEL_B0, ACCEL_B0, GYRO_B0,
        GYRO_B0, GYRO_B0;
    C = diag_sq(s);
  }
  gtsam::Vector6 pose_sig;
  pose_sig << std::sqrt(C(0, 0)), std::sqrt(C(1, 1)), sig_yaw, sig_pos, sig_pos, std::sqrt(C(5, 5));
  const gtsam::Matrix3 Cv = R3 * C.block<3, 3>(6, 6) * R3.transpose();
  Vector vel_sig(3);
  for (int i = 0; i < 3; ++i) vel_sig[i] = std::sqrt(Cv(i, i));
  gtsam::Vector6 bias_sig;
  for (int i = 0; i < 6; ++i) bias_sig[i] = std::sqrt(C(9 + i, 9 + i));
  if (vel_EN != nullptr) {   // experiment O: velocity reset to the GNSS sample (as EKF3's alignment)
    vel = (Vector(3) << vel_EN[0], vel_EN[1], vel[2]).finished();
    vel_sig[0] = vel_sig[1] = sig_vel;
  }
  const int kk = k + 1;
  const double t = t_last;
  gtsam::LevenbergMarquardtParams lm;
  lm.setMaxIterations(lm_maxiter_);
  smoother_.reset(new gtsam::BatchFixedLagSmoother(window_, lm));
  gtsam::NonlinearFactorGraph g;
  gtsam::Values vals;
  g.add(gtsam::PriorFactor<Pose3>(X(kk), pose, gtsam::noiseModel::Diagonal::Sigmas(pose_sig)));
  g.add(gtsam::PriorFactor<Vector>(V(kk), vel, gtsam::noiseModel::Diagonal::Sigmas(vel_sig)));
  g.add(gtsam::PriorFactor<Bias>(B(kk), bias, gtsam::noiseModel::Diagonal::Sigmas(bias_sig)));
  vals.insert(X(kk), pose); vals.insert(V(kk), vel); vals.insert(B(kk), bias);
  smoother_->update(g, vals, tsmap(kk, t));
  if (batch_record) {
    all_g = gtsam::NonlinearFactorGraph();
    all_g.push_back(g);
    all_est = gtsam::Values();
    all_est.insert(X(kk), pose); all_est.insert(V(kk), vel); all_est.insert(B(kk), bias);
    key_t.assign(1, std::make_pair(kk, t));
  }
  if (log_cov) {
    gtsam::Vector s(15);
    s << pose_sig, vel_sig, bias_sig;
    cov_prev = diag_sq(s);
  }
  prev_pose = pose; prev_vel = vel;
  k = kk;
  no_yawcap = !keep_yawcap;
  tag_noise = gtsam::noiseModel::Diagonal::Sigmas((gtsam::Vector(3) << sig_pos, sig_pos, sig_yaw).finished());
}

// ---------- Phase 4: chi-square gate via the gate-only filtering covariance (fgo_core._info etc.) ----------
gtsam::Matrix FGO::info(const gtsam::NonlinearFactorGraph& factors, const gtsam::Values& values, int km1, int kk) const {
  const gtsam::Key keys[6] = {X(km1), V(km1), B(km1), X(kk), V(kk), B(kk)};
  std::map<gtsam::Key, std::pair<int, int>> off;
  int o = 0;
  for (int i = 0; i < 6; ++i) {
    off[keys[i]] = {o, DIMS[i % 3]};
    o += DIMS[i % 3];
  }
  gtsam::Matrix L = gtsam::Matrix::Zero(o, o);
  L.topLeftCorner(15, 15) = cov_prev.inverse();
  for (size_t i = 0; i < factors.size(); ++i) {
    const auto jf = boost::dynamic_pointer_cast<gtsam::JacobianFactor>(factors.at(i)->linearize(values));
    const gtsam::Matrix A = jf->jacobian().first;
    std::vector<int> idx;
    for (const gtsam::Key key : jf->keys())
      for (int j = 0; j < off[key].second; ++j) idx.push_back(off[key].first + j);
    const gtsam::Matrix AtA = A.transpose() * A;
    for (size_t a = 0; a < idx.size(); ++a)
      for (size_t b = 0; b < idx.size(); ++b) L(idx[a], idx[b]) += AtA(a, b);
  }
  return L;
}

gtsam::Values FGO::values_for(int km1, int kk, const Pose3& pose_k, const Vector& vel_k, const Bias& bias_k,
                              const gtsam::Values* src) const {
  gtsam::Values v;
  if (src == nullptr) {
    v.insert(X(km1), prev_pose); v.insert(V(km1), prev_vel); v.insert(B(km1), prev_bias);
  } else {
    v.insert(X(km1), src->exists(X(km1)) ? src->at<Pose3>(X(km1)) : prev_pose);
    v.insert(V(km1), src->exists(V(km1)) ? src->at<Vector>(V(km1)) : prev_vel);
    v.insert(B(km1), src->exists(B(km1)) ? src->at<Bias>(B(km1)) : prev_bias);
  }
  v.insert(X(kk), pose_k); v.insert(V(kk), vel_k); v.insert(B(kk), bias_k);
  return v;
}

void FGO::forward_factors(gtsam::NonlinearFactorGraph& g, double t, int km1, int kk, const Pose3& Xk, const Vector& Vk,
                          const FwdMeas* fwd) {
  if (fwd == nullptr) return;
  const gtsam::Matrix cov = info(g, values_for(km1, kk, Xk, Vk, prev_bias, nullptr), km1, kk).inverse();
  const gtsam::Matrix cXX = cov.block(15, 15, 6, 6), cBB = cov.block(24, 24, 6, 6);
  if (!std::isnan(fwd->psi)) {
    HeadingFactor f(heading_noise_, X(kk), fwd->psi);
    const double e = wrap(Xk.rotation().yaw() - fwd->psi);
    const gtsam::Matrix Hx = f.H(Xk);
    const double S = (Hx * cXX * Hx.transpose())(0, 0) + fwd_.sigma_psi * fwd_.sigma_psi;
    const double nis = e * e / S;
    const bool ok = std::isfinite(nis) && nis <= fwd_.gate;
    if (ok) g.add(f);
    fwd_log.push_back({t, 0, nis, ok, S});
  }
  if (!std::isnan(fwd->omega)) {
    const double e = (fwd->gz - prev_bias.gyroscope()[2]) - fwd->omega;
    const double S = cBB(5, 5) + fwd_.sigma_omega * fwd_.sigma_omega;
    const double nis = e * e / S;
    const bool ok = std::isfinite(nis) && nis <= fwd_.gate;
    if (ok) g.add(YawRateFactor(yawrate_noise_, B(kk), fwd->omega, fwd->gz));
    fwd_log.push_back({t, 1, nis, ok, S});
  }
}

gtsam::Matrix FGO::posterior_cov(const gtsam::NonlinearFactorGraph& g, const gtsam::Values& est, int km1, int kk) const {
  const gtsam::Values v = values_for(km1, kk, est.at<Pose3>(X(kk)), est.at<Vector>(V(kk)), est.at<Bias>(B(kk)), &est);
  const gtsam::Matrix cov = info(g, v, km1, kk).inverse().block(15, 15, 15, 15);
  return 0.5 * (cov + cov.transpose());
}

// ---------------- GroundProximityFlow (measurement_models.py, ruling D15) ----------------
constexpr double GP_HEIGHT_M = 0.5, GP_ARM_GUARD_S = 1.0, GP_GYRO_RADPS = 0.1, GP_RANGE_RISE_M = 0.1;

void GroundProximityFlow::on_range(double t, double rng) {
  if (!(0.05 <= rng && rng <= 40.0)) return;
  last_rng_ = rng; have_last_rng_ = true;
  if (!armed(t)) {
    rng_at_arm_ = rng; have_rng_at_arm_ = true;
  } else if (!takeoff && t - t_arm_ > GP_ARM_GUARD_S && have_rng_at_arm_ && rng > rng_at_arm_ + GP_RANGE_RISE_M) {
    takeoff = true; t_takeoff = t;
  }
}

void GroundProximityFlow::on_gyro(double t, const Vector3& gyro, const Vector3& bias) {
  if (!armed(t)) { takeoff = false; return; }
  if (!takeoff && t - t_arm_ > GP_ARM_GUARD_S) {
    if ((gyro - bias).norm() > GP_GYRO_RADPS) { takeoff = true; t_takeoff = t; }
  }
}

Eigen::Vector2d GroundProximityFlow::replace(const Eigen::Vector2d& flow_xy, const Vector3& omega_flu,
                                             double roll, double pitch) {
  if (takeoff || !have_last_rng_) return flow_xy;
  if (last_rng_ * std::cos(roll) * std::cos(pitch) >= GP_HEIGHT_M) return flow_xy;
  ++n_replaced;
  return h_flow_rot(omega_flu);   // EKF3's flowRadXYcomp = 0
}

}  // namespace fgo_cpp
