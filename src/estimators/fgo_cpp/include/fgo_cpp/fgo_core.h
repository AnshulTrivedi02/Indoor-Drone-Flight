// C++ port of src/estimators/fgo/fgo_core.py (class FGO), BASELINE configuration only:
// BatchFixedLagSmoother (window, LM max iterations), CombinedImuFactor over every IMU sample,
// IMU-predicted zero-innovation yaw cap per keyframe, flow and range factors. The forward-camera,
// tag, GNSS, re-anchor, covariance-log and batch-record paths of the Python class are not ported.
#pragma once

#include <memory>

#include <gtsam/navigation/CombinedImuFactor.h>
#include <gtsam/nonlinear/Values.h>
#include <gtsam_unstable/nonlinear/BatchFixedLagSmoother.h>

#include "fgo_cpp/factors.h"

namespace fgo_cpp {

boost::shared_ptr<gtsam::PreintegrationCombinedParams> make_pim_params();

constexpr double GYRO_B0 = 0.043633;   // EKF3 initial gyro-bias 1 sigma (rad/s)
constexpr double ACCEL_B0 = 0.2;       // EKF3 initial accel-bias 1 sigma (m/s^2)

struct FlowMeas {
  Eigen::Vector2d xy;
  bool valid;
  double inlier;
};

class FGO {
 public:
  FGO(double window, double kf_dt, int lm_maxiter);

  void init(const Vector3& accel_mean, double first_range, double t0);
  void integrate_imu(const Vector3& accel, const Vector3& gyro, double dt);
  // flow: nullptr = none. omega: FLU rates for the flow factor. rng: NaN = none.
  void keyframe(double t, const FlowMeas* flow, const Vector3& omega, double rng);

  double kf_dt;
  int k = 0;
  int n_flow = 0, n_range = 0, n_imu = 0;
  Pose3 prev_pose;
  Vector prev_vel;
  Bias prev_bias;
  double t_last = 0.0;

 private:
  std::unique_ptr<gtsam::BatchFixedLagSmoother> smoother_;
  std::unique_ptr<gtsam::PreintegratedCombinedMeasurements> pim_;
  gtsam::SharedNoiseModel flow_noise_, range_noise_, yaw_noise_;
};

// measurement_models.GroundProximityFlow (ruling D15): EKF3's take-off / ground-proximity flow rule.
class GroundProximityFlow {
 public:
  explicit GroundProximityFlow(double t_arm, bool has_arm) : t_arm_(t_arm), has_arm_(has_arm) {}
  bool armed(double t) const { return has_arm_ && t >= t_arm_; }
  void on_range(double t, double rng);
  void on_gyro(double t, const Vector3& gyro, const Vector3& bias);
  Eigen::Vector2d replace(const Eigen::Vector2d& flow_xy, const Vector3& omega_flu, double roll, double pitch);

  bool takeoff = false;
  int n_replaced = 0;
  double t_takeoff = NAN;

 private:
  double t_arm_;
  bool has_arm_;
  bool have_rng_at_arm_ = false, have_last_rng_ = false;
  double rng_at_arm_ = 0.0, last_rng_ = 0.0;
};

}  // namespace fgo_cpp
