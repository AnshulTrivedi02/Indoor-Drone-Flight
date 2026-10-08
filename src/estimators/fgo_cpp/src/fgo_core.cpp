// C++ port of src/estimators/fgo/fgo_core.py (baseline) and measurement_models.GroundProximityFlow.
// Graph construction keeps the Python order: IMU factor, yaw cap, range, flow; values X, V, B.
#include "fgo_cpp/fgo_core.h"

#include <cmath>

#include <gtsam/inference/Symbol.h>
#include <gtsam/navigation/NavState.h>
#include <gtsam/nonlinear/LevenbergMarquardtParams.h>
#include <gtsam/nonlinear/NonlinearFactorGraph.h>
#include <gtsam/slam/PriorFactor.h>

namespace fgo_cpp {

using gtsam::symbol_shorthand::B;
using gtsam::symbol_shorthand::V;
using gtsam::symbol_shorthand::X;

namespace {
// numpy.radians: x * (pi / 180)
inline double np_radians(double deg) { return deg * (M_PI / 180.0); }
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

FGO::FGO(double window, double kf_dt_, int lm_maxiter) : kf_dt(kf_dt_) {
  gtsam::LevenbergMarquardtParams lm;
  lm.setMaxIterations(lm_maxiter);
  smoother_.reset(new gtsam::BatchFixedLagSmoother(window, lm));
  pim_.reset(new gtsam::PreintegratedCombinedMeasurements(make_pim_params(), Bias(Vector3::Zero(), Vector3::Zero())));
  flow_noise_ = gtsam::noiseModel::Isotropic::Sigma(2, 0.25);    // FLOW_M_NSE
  range_noise_ = gtsam::noiseModel::Isotropic::Sigma(1, 0.5);    // RNG_M_NSE
  yaw_noise_ = gtsam::noiseModel::Isotropic::Sigma(1, 0.5);      // EK3_YAW_M_NSE, §9.4
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
  gtsam::FixedLagSmoother::KeyTimestampMap ts;
  ts[X(0)] = t0; ts[V(0)] = t0; ts[B(0)] = t0;
  smoother_->update(g, vals, ts);
  prev_pose = pose0; prev_vel = vel0; prev_bias = bias0;
  t_last = t0;
}

void FGO::integrate_imu(const Vector3& accel, const Vector3& gyro, double dt) {
  if (0 < dt && dt < 0.2) {
    pim_->integrateMeasurement(accel, gyro, dt);
    ++n_imu;
  }
}

void FGO::keyframe(double t, const FlowMeas* flow, const Vector3& omega, double rng) {
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
  g.add(YawPriorFactor(yaw_noise_, X(kk), Xk.rotation().yaw()));
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
  gtsam::FixedLagSmoother::KeyTimestampMap ts;
  ts[X(kk)] = t; ts[V(kk)] = t; ts[B(kk)] = t;
  smoother_->update(g, vals, ts);
  const gtsam::Values est = smoother_->calculateEstimate();
  prev_pose = est.at<Pose3>(X(kk));
  prev_vel = est.at<Vector>(V(kk));
  prev_bias = est.at<Bias>(B(kk));
  pim_->resetIntegrationAndSetBias(prev_bias);
  k = kk;
  t_last = t;
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
