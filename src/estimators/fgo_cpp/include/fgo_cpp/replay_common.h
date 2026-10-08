// The replay loop of fgo_replay.py / room_fgo_replay.py as a streaming runner, plus the native input handling
// (front end): gap rule, IMU dejitter, stable time sort, gravity levelling and the interval-averaged gyro.
#pragma once

#include <array>
#include <map>
#include <memory>
#include <string>
#include <vector>

#include "fgo_cpp/fgo_core.h"

namespace fgo_cpp {

constexpr int EV_COLS = 9;    // fgo_export.EV_COLS
constexpr int KF_COLS = 40;   // fgo_export.KF_COLS
enum Kind { IMU = 0, ATT = 1, RNG = 2, FLOW = 3, FWD = 4, TAG = 5, GNSS = 6 };

struct ReplayConfig {
  std::string mode;            // "corridor" | "room"
  Vector3 accel_mean = Vector3::Zero();
  double first_range = 0, t_init = 0, window = 0.25, kf_dt = 1.0 / 30.0;
  int lm_iters = 2;
  bool has_arm = false;
  double t_arm = 0;
  bool log_cov = false;
  FwdConfig fwd;
  bool gnss = false, batch = false;
  double tag_sigma_pos = 0, tag_sigma_yaw = 0, gnss_sigma_pos = 0, gnss_sigma_vel = 0, gnss_align_speed = 0;
  int gnss_align_n = 0;
  // imu_gaps.json (gap rule)
  std::string gap_verdict;     // "" = no file
  double gap_replay_start = 0;
  static ReplayConfig from_json(const std::string& path);
};

struct ReplayResult {
  std::vector<double> kf_rows;   // KF_COLS per keyframe
  std::vector<long long> step_ns;
  std::vector<double> batch_rows;   // 14 per key
  std::vector<double> avg_log;      // per flow / forward frame after t_init: kind, t, omega xyz (forward: gz, NaN, NaN)
  double batch_s = 0, batch_error = 0;
  int batch_iterations = 0;
  int n_flow = 0, n_range = 0, n_imu = 0, n_tag = 0, n_gnss = 0, n_replaced = 0, n_fail = 0;
  double t_anchor = NAN;
};

// Streaming runner: feed events in time order. own_averager = true computes the interval-averaged gyro itself
// (native front end); false takes it from the processed export (columns 6-8 of flow rows, 4 of forward rows).
class Runner {
 public:
  Runner(const ReplayConfig& cfg, bool own_averager);
  void on_event(const double* row);   // one EV_COLS row
  ReplayResult finish();              // runs the whole-flight batch if configured

 private:
  void keyframes_due(double tt);
  Vector3 average(std::vector<std::array<double, 4>>& buf, double& t_prev, double t_flow);

  ReplayConfig cfg_;
  bool own_avg_;
  FGO fgo_;
  GroundProximityFlow gp_;
  ReplayResult res_;
  Vector3 omega_ = Vector3::Zero();
  bool have_prev_imu_ = false;
  double t_prev_imu_ = 0;
  bool have_flow_ = false, have_fwd_ = false, have_tag_ = false, have_gnss_ = false;
  FlowMeas flow_pend_{Eigen::Vector2d::Zero(), false, 0.0};
  Vector3 flow_omega_ = Vector3::Zero();
  FwdMeas fwd_pend_{NAN, NAN, NAN};
  gtsam::Vector3 tag_pend_;
  gtsam::Vector4 gnss_pend_;
  double rng_pend_ = NAN;
  double t_kf_next_;
  bool anchored_;
  int n_fast_ = 0;
  std::vector<std::array<double, 4>> gyro_buf_, fwd_buf_;
  double gyro_t_prev_, fwd_t_prev_;
};

std::vector<double> read_f64(const std::string& path);

// Native front end. Two parts:
//  (1) offline_imu_timing: the gap rule and the IMU dejitter (least-squares line through the receipt stamps, in
//      bag order; imu_timing.py). Offline only: it fits the whole flight. A live node uses HIGHRES_IMU time_usec
//      (/imu/time_ref) instead, and skips this step.
//  (2) StreamFrontEnd: everything else, streaming, in arrival order - a reorder buffer that releases events in
//      (stamp, arrival) order once they are older than `reorder_delay` behind the newest stamp seen (equal to
//      Python's stable sort whenever the delay exceeds the largest lateness), the init inputs (gravity levelling
//      over the first 0.5 s of IMU, first valid range) gathered from the released stream before the estimator
//      starts, then the Runner with its own interval-averaged gyro.
struct FrontEndStats {
  double period_ms = 0, resid_std_ms = 0, resid_maxabs_ms = 0;
  size_t n_trimmed = 0;
};
std::vector<double> offline_imu_timing(const std::vector<double>& raw, const ReplayConfig& cfg, FrontEndStats* st);

class StreamFrontEnd {
 public:
  StreamFrontEnd(const ReplayConfig& cfg, double reorder_delay);
  ~StreamFrontEnd();
  void push(const double* row);          // one EV_COLS row, in arrival order
  ReplayResult finish();
  const std::vector<double>& released() const { return released_; }   // the processed stream, as released
  const ReplayConfig& config() const { return cfg_; }                  // with the init inputs filled in
  double max_lateness = 0;               // largest (newest stamp seen - stamp) at arrival
  size_t n_out_of_order = 0;             // events that arrived after a later-stamped event had been released

 private:
  void release(const std::array<double, EV_COLS>& e);
  void try_init();
  ReplayConfig cfg_;
  double delay_;
  std::multimap<std::pair<double, size_t>, std::array<double, EV_COLS>> buf_;
  size_t seq_ = 0;
  double t_newest_ = -1e300, t_last_released_ = -1e300;
  std::vector<double> released_;
  std::vector<std::array<double, EV_COLS>> pre_;   // released before the estimator is initialised
  bool have_imu0_ = false, have_rng_ = false, level_done_ = false;
  double t_imu0_ = 0;
  std::unique_ptr<Runner> runner_;
};

ReplayResult run_processed(const ReplayConfig& cfg, const std::vector<double>& ev, bool own_averager = false);
void write_outputs(const std::string& out, const ReplayConfig& cfg, const ReplayResult& r);
void print_summary(const ReplayResult& r);

}  // namespace fgo_cpp
