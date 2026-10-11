// C++ port of src/estimators/fgo/fgo_core.py (class FGO): BatchFixedLagSmoother (window, LM max iterations),
// CombinedImuFactor over every IMU sample, IMU-predicted zero-innovation yaw cap (variance-gated), flow and range
// factors; the Phase 4 forward-camera heading / yaw-rate factors with the chi-square gate on the gate-only
// filtering covariance recursion; the first-fix re-anchor with tag (experiment T) and GNSS (experiment O)
// factors; and the whole-flight batch record. Not ported: the offline F-test variants (robust heading noise,
// injected initial yaw) and the diagnostic covariance log output (the recursion itself is ported).
#pragma once

#include <memory>
#include <utility>
#include <vector>

#include <gtsam/navigation/CombinedImuFactor.h>
#include <gtsam/nonlinear/NonlinearFactorGraph.h>
#include <gtsam/nonlinear/Values.h>
#include <gtsam_unstable/nonlinear/BatchFixedLagSmoother.h>

#include "fgo_cpp/factors.h"

namespace fgo_cpp {

boost::shared_ptr<gtsam::PreintegrationCombinedParams> make_pim_params();

constexpr double GYRO_B0 = 0.043633;   // EKF3 initial gyro-bias 1 sigma (rad/s)
constexpr double ACCEL_B0 = 0.2;       // EKF3 initial accel-bias 1 sigma (m/s^2)
// X(0) initial yaw 1 sigma (rad) = the UKF's 1 deg; fgo_core.py YAW0_SIGMA (np.radians(1): x * (pi / 180)). MODEL
// CORRECTION under D18 (user ruling 2026-10-10, METHODOLOGY "RULINGS (user, 2026-10-10): FGO initial yaw sigma"): was 1e-3.
constexpr double YAW0_SIGMA = 1.0 * (3.14159265358979323846 / 180.0);
// X(0) initial roll/pitch 1 sigma (rad) = the UKF's 5 deg; fgo_core.py ROLLPITCH0_SIGMA (np.radians(5)). D18, same change
// (initial-uncertainty audit, docs/handovers/2026-10-10_initial_sigma_audit.md): was np_radians(2).
constexpr double ROLLPITCH0_SIGMA = 5.0 * (3.14159265358979323846 / 180.0);
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

struct FlowMeas {
  Eigen::Vector2d xy;
  bool valid;
  double inlier;
};

struct FwdMeas {        // forward-camera frame: psi / omega NaN = not measured; gz = interval-averaged gyro-z
  double psi, omega, gz;
};

struct FwdLogEntry {    // fgo_core.fwd_log: (t, kind 0 heading / 1 yaw rate, nis, accepted, S)
  double t;
  int kind;
  double nis;
  bool ok;
  double S;
};

struct FwdConfig {
  bool enabled = false;
  double sigma_psi = 0.0;
  double sigma_omega = NAN;   // NaN = no yaw-rate factor
  double gate = 9.0;
};

class FGO {
 public:
  FGO(double window, double kf_dt, int lm_maxiter, const FwdConfig& fwd = FwdConfig(), bool log_cov = false);

  void init(const Vector3& accel_mean, double first_range, double t0);
  void integrate_imu(const Vector3& accel, const Vector3& gyro, double dt);
  // nullptr = no measurement. rng NaN = none. tag = (x, y, yaw). gnss = (E, N, vE, vN).
  void keyframe(double t, const FlowMeas* flow, const Vector3& omega, double rng, const FwdMeas* fwd = nullptr,
                const gtsam::Vector3* tag = nullptr, const gtsam::Vector4* gnss = nullptr);
  void reanchor(double pE, double pN, double yaw_fix, double sig_pos, double sig_yaw, const double* vel_EN = nullptr,
                double sig_vel = 0.0, bool keep_yawcap = false);

  double kf_dt;
  int k = 0;
  int n_flow = 0, n_range = 0, n_imu = 0, n_tag = 0, n_gnss = 0;
  Pose3 prev_pose;
  Vector prev_vel;
  Bias prev_bias;
  double t_last = 0.0;

  bool no_yawcap = false;
  bool log_cov;
  gtsam::Matrix cov_prev;                // 15x15, empty until set
  // §9.4 yaw-cap gate (ruling 2026-10-09): the same recursion, run whenever the cap is active (equal to cov_prev
  // under log_cov); cov_prev and reanchor() keep their old semantics.
  gtsam::Matrix cov_gate;
  double t_yawchk = 0.0;
  int n_yaw_check = 0, n_yaw_fire = 0;
  std::vector<YawGateEntry> yawgate_log;
  std::vector<FwdLogEntry> fwd_log;
  gtsam::SharedNoiseModel tag_noise;     // set by reanchor (experiment T)
  gtsam::SharedNoiseModel gnss_noise;    // set by the caller (experiment O)

  // whole-flight batch record (F2 / experiment T hindsight)
  bool batch_record = false, batch_drop_yawcap = false;
  gtsam::NonlinearFactorGraph all_g;
  gtsam::Values all_est;
  std::vector<std::pair<int, double>> key_t;

 private:
  gtsam::Matrix info(const gtsam::NonlinearFactorGraph& factors, const gtsam::Values& values, int km1, int kk,
                     const gtsam::Matrix* prior = nullptr) const;
  gtsam::Values values_for(int km1, int kk, const Pose3& pose_k, const Vector& vel_k, const Bias& bias_k,
                           const gtsam::Values* src) const;
  void forward_factors(gtsam::NonlinearFactorGraph& g, double t, int km1, int kk, const Pose3& Xk, const Vector& Vk,
                       const FwdMeas* fwd);
  gtsam::Matrix posterior_cov(const gtsam::NonlinearFactorGraph& g, const gtsam::Values& est, int km1, int kk,
                              const gtsam::Matrix* prior = nullptr) const;
  double att_trace_pred(const gtsam::NonlinearFactorGraph& g, int km1, int kk, const Pose3& Xk, const Vector& Vk) const;

  double window_;
  int lm_maxiter_;
  FwdConfig fwd_;
  std::unique_ptr<gtsam::BatchFixedLagSmoother> smoother_;
  std::unique_ptr<gtsam::PreintegratedCombinedMeasurements> pim_;
  gtsam::SharedNoiseModel flow_noise_, range_noise_, yaw_noise_, heading_noise_, yawrate_noise_;
};

// measurement_models.GroundProximityFlow (ruling D15): EKF3's take-off / ground-proximity flow rule.
class GroundProximityFlow {
 public:
  explicit GroundProximityFlow(double t_arm, bool has_arm) : t_arm_(t_arm), has_arm_(has_arm) {}
  bool armed(double t) const { return has_arm_ && t >= t_arm_; }
  void set_arm(double t_arm) { t_arm_ = t_arm; has_arm_ = true; }
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

// EQUIVALENCE TESTING ONLY (ruling 2026-10-11 item 1, Band C option (ii)); OFF by default. Only a build configured with
// -DFGO_CPP_FORCED_GATE=ON (never the installed / flown build) compiles it. The §9.4 yaw-cap gate decision at keyframe
// kk is then read from a recorded Python gate log (env FGO_CPP_FORCED_GATE_LOG: fgo_core.yawgate_log rows t, k, trace,
// fired) instead of trace > ATT_VAR_GATE; the trace is still computed and logged. It aborts if the variable is unset or
// if a check falls on a keyframe that the Python log never checked.
#ifdef FGO_CPP_FORCED_GATE
namespace fgo_cpp { bool forced_gate_fire(int kk, double trace); }
#define FGO_GATE_FIRE(kk, tr) ::fgo_cpp::forced_gate_fire((kk), (tr))
#else
#define FGO_GATE_FIRE(kk, tr) ((tr) > ATT_VAR_GATE)
#endif
