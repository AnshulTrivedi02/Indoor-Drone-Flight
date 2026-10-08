// Live input/output adapter for the C++ FGO: the C++ counterpart of fgo_node.py + fgo_node_core.py, with no ROS
// dependency (the ROS 2 node fgo_cpp_node.cpp and the deterministic bag-replay harness fgo_cpp_live_replay.cpp are
// both thin shells around this class, so the code tested offline is the code that runs live).
//
// Inputs, pushed in ARRIVAL order with their header stamps (the bag / sim header clock):
//   imu(acc, gyro) + time_ref(sensor time)  - IMU stamp source selectable (see LiveConfig::imu_stamp)
//   flow, range, attitude rates             - as fgo_replay.py; the interval-averaged gyro is computed here
//   heading (the heading bridge's sent ODOMETRY: NED yaw, quality, angErr) - gated as fgo_node._hdg
//   tag fix (x, y, yaw)                     - experiment T: first fix re-anchors, later fixes are tag factors
//   armed flag (from the autopilot's HEARTBEAT) - sets the ground-proximity rule's arming time (D15)
// Output per keyframe: the state, the validity flag (fgo_node_core.valid_now) and, once the clock map has settled
// (D25), the ODOMETRY message for ArduPilot's AP_NavFGO (AHRS_EKF_TYPE 13) exactly as fgo_node._send_state.
#pragma once

#include <deque>
#include <functional>
#include <map>
#include <memory>
#include <string>
#include <vector>

#include "fgo_cpp/mavlink_io.h"
#include "fgo_cpp/replay_common.h"

namespace fgo_cpp {

struct LiveConfig {
  ReplayConfig base;                 // window, LM, kf_dt, mode ("corridor" | "room"), forward config, tag sigmas
  double reorder_delay = 0.20;       // s; stamp-ordered release up to newest stamp - delay (bags: lateness <= 0.185 s)
  // IMU stamp source:
  //   "time_ref": HIGHRES_IMU time_usec (/imu/time_ref, paired FIFO by header stamp) mapped to the header clock by
  //               the D25 lower envelope, slew-limited so stamps stay monotonic (the live default; no offline
  //               dejitter). The offset is SEEDED only from the SETTLED envelope (the same D25 settle as the
  //               ODOMETRY time_usec): every input that arrives before the settle is held, and at the settle the
  //               held block is pushed in final-stamp order; keyframes it produces are not sent (they are stale).
  //               Fix 2026-10-08 (docs/handovers/2026-10-08_fgo_cpp_timeref_fix.md): seeding from the first,
  //               unsettled samples took the bridge's start-up backlog offset (~0.5 s) and the 50 us/sample slew
  //               then needed ~30 s to remove it, stamping states up to ~0.4 s in the future.
  //   "causal":   fgo_node_core's running least-squares fit of the receipt stamps (the Python node's choice)
  //   "header":   the header stamp as given (replay of an already dejittered stream)
  std::string imu_stamp = "time_ref";
  double slew_s_per_sample = 50e-6;  // time_ref mode: max change of the applied clock offset per IMU sample
  bool gap_rule = true;              // causal IMU-gap rule on /imu/time_ref (fgo_node_core gap="causal")
  double clock_settle_s = 10.0, clock_outlier_s = 0.020, clock_window_s = 10.0;   // D25
  std::string arm_source = "heartbeat";   // "heartbeat" (live) | "param" (base.t_arm) | "none" (as fgo_node.py today)
  bool heading = false;
  double heading_sigma = 5.0 * M_PI / 180.0;   // fgo_node: fixed 5 deg (sigma = max(angErr, 5 deg) set as fixed)
  std::string nav_frame = "corridor";  // ODOMETRY frame: "corridor" (x fwd = N, y W, z U) | "enu" (room world ENU)
};

struct LiveOutput {
  double t_k = 0;                    // keyframe time (header clock)
  const double* row = nullptr;       // the KF_COLS keyframe row (state in fgo_export layout)
  bool valid = false;
  bool sent = false;                 // an ODOMETRY message was produced (clock settled)
  uint64_t t_us = 0;                 // its time_usec (SITL clock)
  std::vector<uint8_t> frame;        // the encoded MAVLink frame (empty if not produced)
  long long step_ns = 0;
  size_t arrival_index = 0;          // index of the input whose arrival released this keyframe
};

class LiveAdapter {
 public:
  LiveAdapter(const LiveConfig& cfg, std::function<void(const LiveOutput&)> sink);
  void imu(double th, const Vector3& acc, const Vector3& gyro);
  void time_ref(double th, double t_sensor);
  void flow(double th, double fx, double fy, bool valid, double inlier);
  void range(double th, double r);
  void att(double th, const Vector3& w);
  void heading(double th, double yaw_ned, double quality, double ang_err);
  void tag(double th, double x, double y, double yaw);
  void armed(bool is_armed);
  void flush();

  // diagnostics
  size_t n_arrivals = 0, n_reinits = 0, n_sent = 0, n_unsettled = 0, n_hdg_rejected = 0, n_imu_unpaired = 0;
  double max_lateness() const;
  size_t n_out_of_order() const;
  bool gap_invalid = false;
  double t_armed_header = -1.0;   // header-clock arming instant used for D15 (heartbeat source); -1 = none
  std::vector<std::array<double, 3>> gaps_seen;   // (sensor t, gap, airborne)
  // time_ref clock-map diagnostics (fix 2026-10-08)
  bool tref_settled = false;          // the IMU offset has been seeded from the settled envelope
  double tref_seed_offset = NAN;      // the seeded offset (header - sensor, s)
  double tref_seed_th = NAN;          // header time of the time_ref arrival that settled the map
  size_t n_held = 0;                  // inputs held before the settle and pushed at it
  double tref_max_track_err = 0;      // max |envelope - applied offset| over IMU samples after the seed (s)
  size_t n_dup_stamp = 0;             // IMU or time_ref arrivals whose header stamp was already waiting (FIFO-paired)
  // clock integrity (ruling 2026-10-09): a FC (SITL) reboot after the node started steps the sensor clock back and
  // breaks the clock map. Detected by (a) /imu/time_ref sensor time stepping back > CLOCK_BACK_S, (b) the time_ref
  // offset tracking error > CLOCK_TRACK_LIMIT_S after the seed, (c) a sent time_usec stepping back. LATCHED: from then
  // on every state is sent INVALID (quality 0), so the FC's output goes invalid and its landing trigger applies.
  static constexpr double CLOCK_BACK_S = 0.5, CLOCK_TRACK_LIMIT_S = 0.10;
  bool clock_broken = false;
  std::string clock_broken_reason;
  double clock_broken_th = NAN;

 private:
  void push(const double* row, int rank);
  void reset_front_end();
  bool airborne() const;
  void on_keyframe(const double* row);
  bool sitl_us(double t, uint64_t* out);
  double envelope_offset(bool require_settle, bool* ok);
  void imu_time_ref_paired(double th, double ts, const Vector3& acc, const Vector3& gyro);
  void gap_check(double ts);
  void settle_and_flush();
  void break_clock(double th, const char* why);
  double ts_prev_any_ = NAN;
  uint64_t last_sent_tus_ = 0;
  bool holding() const { return cfg_.imu_stamp == "time_ref" && !tref_settled; }
  std::vector<uint8_t> odometry(const double* row, bool valid, uint64_t t_us);

  LiveConfig cfg_;
  std::function<void(const LiveOutput&)> sink_;
  std::unique_ptr<StreamFrontEnd> fe_;
  double newest_th_ = -1e300;
  // causal dejitter (fgo_node_core._dejitter)
  double dj_n_ = 0, dj_mx_ = 0, dj_my_ = 0, dj_cxx_ = 0, dj_cxy_ = 0;
  // time_ref pairing and clock map
  // FIFO per header stamp: the bridge can give two samples the same receipt stamp (153 of 112563 in shadow_ii)
  std::map<double, std::deque<std::pair<Vector3, Vector3>>> imu_wait_;   // IMU waiting for its time_ref
  std::map<double, std::deque<double>> tref_wait_;                       // time_ref waiting for its IMU
  // inputs held before the clock map settles (time_ref mode): what 0 = a row push (row, rank), 1 = a paired IMU
  // sample (row[1] = sensor time), 2 = a gap-rule check (row[1] = sensor time)
  struct Held { int what; int rank; std::array<double, EV_COLS> row; };
  std::vector<Held> held_;
  bool flushing_ = false;
  std::deque<std::pair<double, double>> toff_;               // (th, th - ts) over the last clock_window_s
  bool have_tref0_ = false;
  double tref_t0_ = 0;
  bool have_tref_prev_ = false;
  double tref_prev_ = 0;
  bool have_off_used_ = false;
  double off_used_ = 0;
  double hdg_last_ = -1e300;
  bool have_hdg_last_ = false;
  // validity
  bool have_flow_fused_ = false;
  double t_last_flow_fused_ = 0;
  uint8_t seq_ = 0;
  bool armed_ = false;
};

}  // namespace fgo_cpp
