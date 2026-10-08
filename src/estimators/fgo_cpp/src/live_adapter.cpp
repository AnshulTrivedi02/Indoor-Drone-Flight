// Live adapter: see live_adapter.h. Line references are to src/estimators/fgo/fgo_node.py and fgo_node_core.py.
#include "fgo_cpp/live_adapter.h"

#include <algorithm>
#include <cmath>
#include <tuple>

namespace fgo_cpp {

namespace {
constexpr double GAP_S = 0.010;          // fgo_node_core.GAP_S (the IMU-gap rule's gap)
constexpr double AIRBORNE_DZ = 0.30;     // fgo_node_core.AIRBORNE_DZ
constexpr double FLOW_TIMEOUT_S = 5.0;   // fgo_node_core.FLOW_TIMEOUT_S (EKF3 flowFusionTimeout)

double np_median(std::vector<double> v) {   // numpy.median: mean of the two middle values for an even count
  std::sort(v.begin(), v.end());
  const size_t n = v.size();
  return n % 2 ? v[n / 2] : (v[n / 2 - 1] + v[n / 2]) / 2.0;
}
}  // namespace

LiveAdapter::LiveAdapter(const LiveConfig& cfg, std::function<void(const LiveOutput&)> sink)
    : cfg_(cfg), sink_(std::move(sink)) {
  if (cfg_.arm_source != "param") cfg_.base.has_arm = false;
  cfg_.base.accel_mean = Vector3::Constant(NAN);   // computed by the front end
  cfg_.base.first_range = cfg_.base.t_init = NAN;
  if (cfg_.heading) {
    cfg_.base.fwd.enabled = true;
    cfg_.base.fwd.sigma_psi = cfg_.heading_sigma;
    cfg_.base.fwd.sigma_omega = NAN;             // no yaw-rate input live
  }
  cfg_.base.batch = false;                       // no whole-flight batch live
  fe_.reset(new StreamFrontEnd(cfg_.base, cfg_.reorder_delay));
  fe_->keep_released = false;
  fe_->on_keyframe = [this](const double* row) { on_keyframe(row); };
}

double LiveAdapter::max_lateness() const { return fe_->max_lateness; }
size_t LiveAdapter::n_out_of_order() const { return fe_->n_out_of_order; }

void LiveAdapter::push(const double* row, int rank) {
  newest_th_ = std::max(newest_th_, row[1]);
  if (holding()) {   // time_ref mode before the clock map settles: hold (pushed at the settle, in stamp order)
    Held h{0, rank, {}};
    std::copy(row, row + EV_COLS, h.row.begin());
    held_.push_back(h);
    return;
  }
  fe_->push(row, rank);
}

bool LiveAdapter::airborne() const {   // fgo_node_core._airborne
  if (!fe_->initialised() || !fe_->have_last_rng) return false;
  return fe_->last_rng > fe_->config().first_range + AIRBORNE_DZ;
}

void LiveAdapter::reset_front_end() {   // fgo_node_core._reset_filter (+ the dejitter reset); the queue is kept
  fe_->reset_estimator();
  dj_n_ = dj_mx_ = dj_my_ = dj_cxx_ = dj_cxy_ = 0;
  have_flow_fused_ = false;
}

// ---------------- inputs ----------------
void LiveAdapter::imu(double th, const Vector3& acc, const Vector3& gyro) {
  ++n_arrivals;
  if (cfg_.imu_stamp == "time_ref") {
    auto it = tref_wait_.find(th);   // FIFO per header stamp (duplicate receipt stamps occur)
    if (it != tref_wait_.end()) {
      const double ts = it->second.front();
      it->second.pop_front();
      if (it->second.empty()) tref_wait_.erase(it);
      imu_time_ref_paired(th, ts, acc, gyro);
    } else {
      auto& q = imu_wait_[th];
      if (!q.empty()) ++n_dup_stamp;
      q.emplace_back(acc, gyro);
    }
    return;
  }
  double t = th;
  if (cfg_.imu_stamp == "causal") {   // fgo_node_core._dejitter (Welford co-moments of stamp against index)
    const double x = dj_n_;
    dj_n_ += 1;
    const double dx = x - dj_mx_;
    dj_mx_ += dx / dj_n_;
    dj_my_ += (th - dj_my_) / dj_n_;
    dj_cxx_ += dx * (x - dj_mx_);
    dj_cxy_ += dx * (th - dj_my_);
    if (dj_cxx_ > 0) t = dj_my_ + (dj_cxy_ / dj_cxx_) * (x - dj_mx_);
  }
  const double row[EV_COLS] = {double(IMU), t, acc[0], acc[1], acc[2], gyro[0], gyro[1], gyro[2], NAN};
  push(row, 0);
}

void LiveAdapter::imu_time_ref_paired(double th, double ts, const Vector3& acc, const Vector3& gyro) {
  if (holding()) {   // before the settle: keep the sensor time; the stamp is applied at the settle
    newest_th_ = std::max(newest_th_, th);
    held_.push_back({1, 0, {double(IMU), ts, acc[0], acc[1], acc[2], gyro[0], gyro[1], gyro[2], NAN}});
    return;
  }
  bool ok = false;
  const double env = envelope_offset(false, &ok);
  if (!ok) return;
  // the offset was seeded from the SETTLED envelope in settle_and_flush (never from unsettled samples)
  tref_max_track_err = std::max(tref_max_track_err, std::abs(env - off_used_));
  if (std::abs(env - off_used_) > CLOCK_TRACK_LIMIT_S) break_clock(th, "time_ref offset tracking error over the limit");
  off_used_ += std::max(-cfg_.slew_s_per_sample, std::min(cfg_.slew_s_per_sample, env - off_used_));
  const double row[EV_COLS] = {double(IMU), ts + off_used_, acc[0], acc[1], acc[2], gyro[0], gyro[1], gyro[2], NAN};
  push(row, 0);
}

void LiveAdapter::settle_and_flush() {
  bool ok = false;
  const double env = envelope_offset(true, &ok);
  if (!ok) return;
  tref_settled = true;
  have_off_used_ = true;
  off_used_ = env;
  tref_seed_offset = env;
  tref_seed_th = toff_.back().first;
  n_held = held_.size();
  // push the held block in FINAL-stamp order (IMU: sensor time + seeded offset), with the reorder buffer's tie-break
  // (stamp, rank, arrival); a gap-rule check sorts just before the IMU sample whose time_ref it came with
  std::vector<std::tuple<double, int, size_t>> order;
  order.reserve(held_.size());
  for (size_t i = 0; i < held_.size(); ++i) {
    const Held& h = held_[i];
    order.emplace_back(h.what == 0 ? h.row[1] : h.row[1] + env, h.what == 2 ? -1 : h.rank, i);
  }
  std::sort(order.begin(), order.end());
  flushing_ = true;   // keyframes produced now are up to clock_settle_s old: not sent to the autopilot
  for (const auto& o : order) {
    const Held& h = held_[std::get<2>(o)];
    if (h.what == 0) push(h.row.data(), h.rank);
    else if (h.what == 1) imu_time_ref_paired(NAN, h.row[1], Vector3(h.row[2], h.row[3], h.row[4]), Vector3(h.row[5], h.row[6], h.row[7]));
    else gap_check(h.row[1]);
  }
  flushing_ = false;
  held_.clear();
  held_.shrink_to_fit();
}

void LiveAdapter::break_clock(double th, const char* why) {
  if (clock_broken) return;
  clock_broken = true; clock_broken_reason = why; clock_broken_th = th;
}

void LiveAdapter::time_ref(double th, double ts) {
  ++n_arrivals;
  if (std::isfinite(ts_prev_any_) && ts < ts_prev_any_ - CLOCK_BACK_S) break_clock(th, "time_ref sensor time stepped back (FC reboot?)");
  ts_prev_any_ = std::isfinite(ts_prev_any_) ? std::max(ts_prev_any_, ts) : ts;
  if (holding()) held_.push_back({2, -1, {NAN, ts, NAN, NAN, NAN, NAN, NAN, NAN, NAN}});   // gap check deferred
  else gap_check(ts);
  // clock map (fgo_node._tref): offsets header - sensor over the last clock_window_s
  if (!have_tref0_) { have_tref0_ = true; tref_t0_ = th; }
  toff_.emplace_back(th, th - ts);
  while (!toff_.empty() && toff_.front().first < th - cfg_.clock_window_s) toff_.pop_front();
  if (cfg_.imu_stamp == "time_ref") {
    auto it = imu_wait_.find(th);   // FIFO per header stamp
    if (it != imu_wait_.end()) {
      const auto ag = it->second.front();
      it->second.pop_front();
      if (it->second.empty()) imu_wait_.erase(it);
      imu_time_ref_paired(th, ts, ag.first, ag.second);
    } else {
      auto& q = tref_wait_[th];
      if (!q.empty()) ++n_dup_stamp;
      q.push_back(ts);
    }
    // drop stale unpaired entries (> 1 s behind)
    while (!imu_wait_.empty() && imu_wait_.begin()->first < th - 1.0) {
      n_imu_unpaired += imu_wait_.begin()->second.size();
      imu_wait_.erase(imu_wait_.begin());
    }
    while (!tref_wait_.empty() && tref_wait_.begin()->first < th - 1.0) tref_wait_.erase(tref_wait_.begin());
    if (holding()) settle_and_flush();   // seeds the offset and pushes the held block once D25 has settled
  }
}

void LiveAdapter::gap_check(double ts) {
  // causal IMU-gap rule (fgo_node_core._gap_check)
  if (cfg_.gap_rule && have_tref_prev_ && ts - tref_prev_ > GAP_S) {
    const bool air = airborne();
    gaps_seen.push_back({ts, ts - tref_prev_, air ? 1.0 : 0.0});
    if (!air) {
      ++n_reinits;
      reset_front_end();
    } else {
      gap_invalid = true;
    }
  }
  have_tref_prev_ = true;
  tref_prev_ = ts;
}

void LiveAdapter::flow(double th, double fx, double fy, bool valid, double inlier) {
  ++n_arrivals;
  const double row[EV_COLS] = {double(FLOW), th, fx, fy, valid ? 1.0 : 0.0, inlier, NAN, NAN, NAN};
  push(row, 0);
}

void LiveAdapter::range(double th, double r) {
  ++n_arrivals;
  const double row[EV_COLS] = {double(RNG), th, r, NAN, NAN, NAN, NAN, NAN, NAN};
  push(row, 0);
}

void LiveAdapter::att(double th, const Vector3& w) {
  ++n_arrivals;
  const double row[EV_COLS] = {double(ATT), th, w[0], w[1], w[2], NAN, NAN, NAN, NAN};
  push(row, 0);
}

void LiveAdapter::heading(double th, double yaw_ned, double quality, double ang_err) {   // fgo_node._hdg
  ++n_arrivals;
  (void)ang_err;   // fgo_node: sigma = clamp(angErr) floored at 5 deg, applied as the core's fixed heading noise
  if (!cfg_.heading) return;
  if (quality < 50) { ++n_hdg_rejected; return; }                                 // VISO_QUAL_MIN
  if (have_hdg_last_ && th - hdg_last_ < 0.020) { ++n_hdg_rejected; return; }     // extNavIntervalMin_ms
  have_hdg_last_ = true;
  hdg_last_ = th;
  const double row[EV_COLS] = {double(FWD), th, -yaw_ned, NAN, NAN, NAN, NAN, NAN, NAN};   // corridor yaw = -NED yaw
  push(row, 1);
}

void LiveAdapter::tag(double th, double x, double y, double yaw) {
  ++n_arrivals;
  const double row[EV_COLS] = {double(TAG), th, x, y, yaw, NAN, NAN, NAN, NAN};
  push(row, 0);
}

void LiveAdapter::armed(bool is_armed) {
  if (cfg_.arm_source == "heartbeat" && is_armed && !armed_) {
    cfg_.base.has_arm = true;
    cfg_.base.t_arm = newest_th_;   // the arming time on the header clock: the newest stamp seen at the transition
    fe_->set_arm(newest_th_);
    t_armed_header = newest_th_;
  }
  armed_ = is_armed;
}

void LiveAdapter::flush() {
  if (fe_->initialised()) fe_->finish();
}

// ---------------- clock map (fgo_node._sitl_us, D25) ----------------
double LiveAdapter::envelope_offset(bool require_settle, bool* ok) {
  *ok = false;
  if (toff_.empty() || !have_tref0_) return 0;
  if (require_settle && toff_.back().first - tref_t0_ < cfg_.clock_settle_s) return 0;
  std::vector<double> o;
  o.reserve(toff_.size());
  for (const auto& p : toff_) o.push_back(p.second);
  const double med = np_median(o);
  double mn = INFINITY;
  for (double x : o)
    if (std::abs(x - med) <= cfg_.clock_outlier_s) mn = std::min(mn, x);
  *ok = std::isfinite(mn);
  return mn;
}

bool LiveAdapter::sitl_us(double t, uint64_t* out) {
  bool ok = false;
  const double mn = envelope_offset(true, &ok);
  if (!ok) { ++n_unsettled; return false; }
  *out = static_cast<uint64_t>(std::nearbyint((t - mn) * 1e6));   // Python int(round(.)): ties to even
  return true;
}

// ---------------- output ----------------
void LiveAdapter::on_keyframe(const double* row) {
  // validity (fgo_node_core.valid_now), evaluated at the keyframe as the Python core does
  if (row[5] > 0) { have_flow_fused_ = true; t_last_flow_fused_ = row[0]; }
  bool valid;
  if (gap_invalid) valid = false;
  else if (!have_flow_fused_) valid = !airborne();
  else valid = (row[0] - t_last_flow_fused_) <= FLOW_TIMEOUT_S;
  LiveOutput o;
  o.t_k = row[1];
  o.row = row;
  o.valid = valid;
  o.step_ns = fe_->last_step_ns();
  o.arrival_index = n_arrivals;
  uint64_t tus = 0;
  if (flushing_) ++n_unsettled;   // produced from inputs held before the clock map settled: stale, not sent
  else if (sitl_us(row[1], &tus)) {
    if (last_sent_tus_ && tus < last_sent_tus_) break_clock(row[1], "sent time_usec stepped back");
    last_sent_tus_ = std::max(last_sent_tus_, tus);
    if (clock_broken) { valid = false; o.valid = false; }
    o.sent = true;
    o.t_us = tus;
    o.frame = odometry(row, valid, tus);
    ++n_sent;
  }
  sink_(o);
}

std::vector<uint8_t> LiveAdapter::odometry(const double* row, bool valid, uint64_t t_us) {   // fgo_node._send_state
  const double p[3] = {row[10], row[11], row[12]}, v[3] = {row[22], row[23], row[24]};
  double R[3][3];
  for (int a = 0; a < 3; ++a)
    for (int b = 0; b < 3; ++b) R[a][b] = row[13 + 3 * a + b];
  const double ba[3] = {row[25], row[26], row[27]}, bg[3] = {row[28], row[29], row[30]};
  // navigation frame -> NED: corridor (x fwd = N, y = W, z = U): (x, -y, -z); room ENU: (y, x, -z)
  const bool enu = cfg_.nav_frame == "enu";
  const int perm[3] = {enu ? 1 : 0, enu ? 0 : 1, 2};
  const double sgn[3] = {1.0, enu ? 1.0 : -1.0, -1.0};
  const double fb[3] = {1.0, -1.0, -1.0};   // FLU <-> FRD
  double pn[3], vn[3], Rn[3][3];
  for (int i = 0; i < 3; ++i) {
    pn[i] = sgn[i] * p[perm[i]];
    vn[i] = sgn[i] * v[perm[i]];
    for (int j = 0; j < 3; ++j) Rn[i][j] = sgn[i] * R[perm[i]][j] * fb[j];
  }
  double qw, qx, qy, qz;   // the same branch formula as fgo_node._send_state
  const double tr = Rn[0][0] + Rn[1][1] + Rn[2][2];
  if (tr > 0) {
    const double S = std::sqrt(tr + 1.0) * 2;
    qw = 0.25 * S; qx = (Rn[2][1] - Rn[1][2]) / S; qy = (Rn[0][2] - Rn[2][0]) / S; qz = (Rn[1][0] - Rn[0][1]) / S;
  } else if (Rn[0][0] > Rn[1][1] && Rn[0][0] > Rn[2][2]) {
    const double S = std::sqrt(1.0 + Rn[0][0] - Rn[1][1] - Rn[2][2]) * 2;
    qw = (Rn[2][1] - Rn[1][2]) / S; qx = 0.25 * S; qy = (Rn[0][1] + Rn[1][0]) / S; qz = (Rn[0][2] + Rn[2][0]) / S;
  } else if (Rn[1][1] > Rn[2][2]) {
    const double S = std::sqrt(1.0 + Rn[1][1] - Rn[0][0] - Rn[2][2]) * 2;
    qw = (Rn[0][2] - Rn[2][0]) / S; qx = (Rn[0][1] + Rn[1][0]) / S; qy = 0.25 * S; qz = (Rn[1][2] + Rn[2][1]) / S;
  } else {
    const double S = std::sqrt(1.0 + Rn[2][2] - Rn[0][0] - Rn[1][1]) * 2;
    qw = (Rn[1][0] - Rn[0][1]) / S; qx = (Rn[0][2] + Rn[2][0]) / S; qy = (Rn[1][2] + Rn[2][1]) / S; qz = 0.25 * S;
  }
  mav::Odometry m;
  m.time_usec = t_us;
  m.x = float(pn[0]); m.y = float(pn[1]); m.z = float(pn[2]);
  m.q[0] = float(qw); m.q[1] = float(qx); m.q[2] = float(qy); m.q[3] = float(qz);
  m.vx = float(vn[0]); m.vy = float(vn[1]); m.vz = float(vn[2]);
  m.rollspeed = float(fb[0] * bg[0]); m.pitchspeed = float(fb[1] * bg[1]); m.yawspeed = float(fb[2] * bg[2]);   // gyro bias, FRD
  for (int i = 0; i < 21; ++i) m.pose_covariance[i] = m.velocity_covariance[i] = NAN;
  for (int i = 0; i < 3; ++i) m.pose_covariance[i] = float(fb[i] * ba[i]);   // accel bias, FRD (D19 backend)
  m.quality = valid ? 100 : 0;
  // experiment H (ruling 2026-10-08): reset_counter = the number of re-anchors so far (row[37], 0/1), as fgo_node.py's
  // n_anchors; the FC's NavFGO reports a change of it as a position + yaw reset
  m.reset_counter = row[37] > 0.5 ? 1 : 0;
  return mav::encode_odometry(m, seq_++);
}

}  // namespace fgo_cpp
