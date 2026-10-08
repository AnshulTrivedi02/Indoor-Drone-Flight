// Replay loop (fgo_replay.py / room_fgo_replay.py) and native input handling. See replay_common.h.
#include "fgo_cpp/replay_common.h"

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <numeric>
#include <sstream>
#include <stdexcept>

#include <gtsam/inference/Symbol.h>
#include <gtsam/nonlinear/LevenbergMarquardtOptimizer.h>

namespace fgo_cpp {

using gtsam::symbol_shorthand::X;

// ---------------- minimal reader for the flat JSON written by fgo_export.write ----------------
namespace {
std::string slurp(const std::string& path) {
  std::ifstream f(path);
  if (!f) throw std::runtime_error("cannot open " + path);
  std::stringstream ss;
  ss << f.rdbuf();
  return ss.str();
}
const char* find_key(const std::string& js, const std::string& key) {
  const std::string pat = "\"" + key + "\":";
  const size_t p = js.find(pat);
  if (p == std::string::npos) return nullptr;
  const char* c = js.c_str() + p + pat.size();
  while (*c == ' ' || *c == '\n') ++c;
  return c;
}
bool j_null(const std::string& js, const std::string& key) {
  const char* c = find_key(js, key);
  return c == nullptr || std::string(c, 4) == "null";
}
double j_num(const std::string& js, const std::string& key, double dflt = NAN) {
  if (j_null(js, key)) return dflt;
  const char* c = find_key(js, key);
  if (std::string(c, 4) == "true") return 1.0;
  if (std::string(c, 5) == "false") return 0.0;
  return std::strtod(c, nullptr);
}
std::string j_str(const std::string& js, const std::string& key) {
  if (j_null(js, key)) return "";
  const char* c = find_key(js, key);
  if (*c != '"') return "";
  const char* e = std::strchr(c + 1, '"');
  return std::string(c + 1, e);
}
std::vector<double> j_list(const std::string& js, const std::string& key) {
  const char* c = find_key(js, key);
  if (c == nullptr || *c != '[') throw std::runtime_error("not a list: " + key);
  ++c;
  std::vector<double> out;
  while (true) {
    while (*c == ' ' || *c == '\n' || *c == ',') ++c;
    if (*c == ']') break;
    char* e;
    out.push_back(std::strtod(c, &e));
    c = e;
  }
  return out;
}

// numpy's pairwise summation (numpy/_core/src/umath/loops_utils.h.src, double), as used by add.reduce on a
// contiguous 1-D array: the reduction starts from a[0] and adds pairwise_sum(a[1:]).
double np_pairwise(const double* a, size_t n) {
  if (n < 8) {
    double res = 0.;
    for (size_t i = 0; i < n; ++i) res += a[i];
    return res;
  } else if (n <= 128) {
    double r[8];
    for (int j = 0; j < 8; ++j) r[j] = a[j];
    size_t i;
    for (i = 8; i < n - (n % 8); i += 8)
      for (int j = 0; j < 8; ++j) r[j] += a[i + j];
    double res = ((r[0] + r[1]) + (r[2] + r[3])) + ((r[4] + r[5]) + (r[6] + r[7]));
    for (; i < n; ++i) res += a[i];
    return res;
  }
  size_t n2 = n / 2;
  n2 -= n2 % 8;
  return np_pairwise(a, n2) + np_pairwise(a + n2, n - n2);
}
// np.mean(1-D float64 list)
double np_mean(const std::vector<double>& v) { return (v[0] + np_pairwise(v.data() + 1, v.size() - 1)) / double(v.size()); }

double cpy_hypot(double a, double b) { return std::hypot(a, b); }
}  // namespace

ReplayConfig ReplayConfig::from_json(const std::string& path) {
  const std::string js = slurp(path);
  ReplayConfig c;
  c.mode = j_str(js, "mode");
  if (c.mode.empty()) c.mode = "corridor";
  if (find_key(js, "accel_mean")) {
    const auto am = j_list(js, "accel_mean");
    c.accel_mean = Vector3(am[0], am[1], am[2]);
  }
  c.first_range = j_num(js, "first_range");
  c.t_init = j_num(js, "t_init");
  c.has_arm = !j_null(js, "t_arm");
  c.t_arm = j_num(js, "t_arm", 0.0);
  c.window = j_num(js, "window");
  c.kf_dt = j_num(js, "kf_dt");
  c.lm_iters = static_cast<int>(j_num(js, "lm_iters"));
  c.log_cov = j_num(js, "log_cov", 0.0) != 0.0;
  if (!j_null(js, "fwd_sigma_psi")) {
    c.fwd.enabled = true;
    c.fwd.sigma_psi = j_num(js, "fwd_sigma_psi");
    c.fwd.sigma_omega = j_num(js, "fwd_sigma_omega", NAN);
    c.fwd.gate = j_num(js, "fwd_gate", 9.0);
  }
  c.gnss = j_num(js, "gnss", 0.0) != 0.0;
  c.batch = j_num(js, "batch", 0.0) != 0.0;
  c.tag_sigma_pos = j_num(js, "tag_sigma_pos", 0.0);
  c.tag_sigma_yaw = j_num(js, "tag_sigma_yaw", 0.0);
  c.gnss_sigma_pos = j_num(js, "gnss_sigma_pos", 0.0);
  c.gnss_sigma_vel = j_num(js, "gnss_sigma_vel", 0.0);
  c.gnss_align_speed = j_num(js, "gnss_align_speed", 0.0);
  c.gnss_align_n = static_cast<int>(j_num(js, "gnss_align_n", 0.0));
  if (!j_null(js, "imu_gaps")) {
    c.gap_verdict = j_str(js, "verdict");
    c.gap_replay_start = j_num(js, "replay_start_s", 0.0);
  }
  return c;
}

std::vector<double> read_f64(const std::string& path) {
  std::ifstream f(path, std::ios::binary | std::ios::ate);
  if (!f) throw std::runtime_error("cannot open " + path);
  const std::streamsize n = f.tellg();
  f.seekg(0);
  std::vector<double> v(n / sizeof(double));
  f.read(reinterpret_cast<char*>(v.data()), n);
  return v;
}

// ---------------- runner ----------------
Runner::Runner(const ReplayConfig& cfg, bool own_averager)
    : cfg_(cfg), own_avg_(own_averager), fgo_(cfg.window, cfg.kf_dt, cfg.lm_iters, cfg.fwd, cfg.log_cov),
      gp_(cfg.t_arm, cfg.has_arm) {
  fgo_.batch_record = cfg.batch;
  fgo_.batch_drop_yawcap = (cfg.mode == "room");
  fgo_.init(cfg.accel_mean, cfg.first_range, cfg.t_init);
  t_kf_next_ = cfg.t_init + fgo_.kf_dt;
  anchored_ = (cfg.mode != "room");
  gyro_t_prev_ = fwd_t_prev_ = cfg.t_init;
}

// measurement_models.FlowFrameGyroAverager.average (np.mean per component over (t_prev, t_flow])
Vector3 Runner::average(std::vector<std::array<double, 4>>& buf, double& t_prev, double t_flow) {
  std::vector<double> c[3];
  for (const auto& g : buf)
    if (g[0] > t_prev)
      for (int j = 0; j < 3; ++j) c[j].push_back(g[1 + j]);
  Vector3 om = omega_;
  if (!c[0].empty()) om = Vector3(np_mean(c[0]), np_mean(c[1]), np_mean(c[2]));
  t_prev = t_flow;
  buf.erase(std::remove_if(buf.begin(), buf.end(), [t_flow](const std::array<double, 4>& g) { return !(g[0] > t_flow); }),
            buf.end());
  return om;
}

void Runner::on_event(const double* r) {
  const int kind = static_cast<int>(r[0]);
  const double tt = r[1];
  if (tt < cfg_.t_init) {
    if (kind == ATT) omega_ = Vector3(r[2], r[3], r[4]);
    return;
  }
  switch (kind) {
    case ATT:
      omega_ = Vector3(r[2], r[3], r[4]);
      break;
    case RNG:
      rng_pend_ = r[2];
      gp_.on_range(tt, r[2]);
      break;
    case FLOW:
      have_flow_ = true;
      flow_pend_ = FlowMeas{Eigen::Vector2d(r[2], r[3]), r[4] != 0.0, r[5]};
      flow_omega_ = own_avg_ ? average(gyro_buf_, gyro_t_prev_, tt) : Vector3(r[6], r[7], r[8]);
      res_.avg_log.insert(res_.avg_log.end(), {double(FLOW), tt, flow_omega_[0], flow_omega_[1], flow_omega_[2]});
      break;
    case FWD:
      have_fwd_ = true;
      fwd_pend_ = FwdMeas{r[2], r[3], own_avg_ ? average(fwd_buf_, fwd_t_prev_, tt)[2] : r[4]};
      res_.avg_log.insert(res_.avg_log.end(), {double(FWD), tt, fwd_pend_.gz, NAN, NAN});
      break;
    case GNSS:
      if (!anchored_) {
        const double spd = cpy_hypot(r[4], r[5]);
        n_fast_ = spd > cfg_.gnss_align_speed ? n_fast_ + 1 : 0;
        if (n_fast_ >= cfg_.gnss_align_n) {
          const double vEN[2] = {r[4], r[5]};
          fgo_.reanchor(r[2], r[3], std::atan2(r[5], r[4]), cfg_.gnss_sigma_pos,
                        std::asin(std::min(1.0, cfg_.gnss_sigma_vel / spd)), vEN, cfg_.gnss_sigma_vel, true);
          fgo_.gnss_noise = gtsam::noiseModel::Diagonal::Sigmas(
              (gtsam::Vector(4) << cfg_.gnss_sigma_pos, cfg_.gnss_sigma_pos, cfg_.gnss_sigma_vel, cfg_.gnss_sigma_vel).finished());
          anchored_ = true; res_.t_anchor = tt;
        }
      } else {
        have_gnss_ = true;
        gnss_pend_ << r[2], r[3], r[4], r[5];
      }
      break;
    case TAG:
      if (!anchored_) {
        fgo_.reanchor(r[2], r[3], r[4], cfg_.tag_sigma_pos, cfg_.tag_sigma_yaw);
        anchored_ = true; res_.t_anchor = tt;
        fgo_.log_cov = false;   // as room_fgo_replay.py: the recursion was needed only for the re-anchor prior
      } else {
        have_tag_ = true;
        tag_pend_ << r[2], r[3], r[4];
      }
      break;
    case IMU: {
      const Vector3 acc(r[2], r[3], r[4]), gyr(r[5], r[6], r[7]);
      gp_.on_gyro(tt, gyr, fgo_.prev_bias.gyroscope());
      if (own_avg_) {
        gyro_buf_.push_back({tt, r[5], r[6], r[7]});
        if (cfg_.fwd.enabled) fwd_buf_.push_back({tt, r[5], r[6], r[7]});
      }
      if (have_prev_imu_) fgo_.integrate_imu(acc, gyr, tt - t_prev_imu_);
      t_prev_imu_ = tt; have_prev_imu_ = true;
      keyframes_due(tt);
      break;
    }
    default:
      break;
  }
}

void Runner::keyframes_due(double tt) {
  const bool room = cfg_.mode == "room";
  while (tt >= t_kf_next_) {
    const int k_before = fgo_.k, nr0 = gp_.n_replaced, nf0 = fgo_.n_flow, nrg0 = fgo_.n_range, nt0 = fgo_.n_tag,
              ng0 = fgo_.n_gnss, nfail0 = res_.n_fail;
    const size_t nfw0 = fgo_.fwd_log.size();
    const auto t0 = std::chrono::steady_clock::now();
    if (have_flow_ && flow_pend_.valid && flow_pend_.inlier > 0.0) {
      const Vector3 rpy = fgo_.prev_pose.rotation().rpy();
      flow_pend_.xy = gp_.replace(flow_pend_.xy, Vector3(flow_omega_ - fgo_.prev_bias.gyroscope()), rpy[0], rpy[1]);
    }
    try {
      fgo_.keyframe(t_kf_next_, have_flow_ ? &flow_pend_ : nullptr, flow_omega_, rng_pend_, have_fwd_ ? &fwd_pend_ : nullptr,
                    have_tag_ ? &tag_pend_ : nullptr, have_gnss_ ? &gnss_pend_ : nullptr);
    } catch (const std::exception& e) {
      ++res_.n_fail;
      std::fprintf(stderr, "[warn] keyframe at %.3f failed: %s\n", t_kf_next_, e.what());
    }
    const auto t1 = std::chrono::steady_clock::now();
    res_.step_ns.push_back(std::chrono::duration_cast<std::chrono::nanoseconds>(t1 - t0).count());
    const Pose3& P = fgo_.prev_pose;
    const gtsam::Matrix3 R = P.rotation().matrix();
    double row[KF_COLS];
    row[0] = t_kf_next_; row[1] = fgo_.t_last; row[2] = k_before; row[3] = fgo_.k; row[4] = gp_.n_replaced - nr0;
    row[5] = fgo_.n_flow - nf0; row[6] = fgo_.n_range - nrg0;
    row[7] = have_flow_ ? flow_pend_.xy[0] : NAN; row[8] = have_flow_ ? flow_pend_.xy[1] : NAN; row[9] = rng_pend_;
    row[10] = P.x(); row[11] = P.y(); row[12] = P.z();
    for (int a = 0; a < 3; ++a)
      for (int b = 0; b < 3; ++b) row[13 + 3 * a + b] = R(a, b);
    for (int a = 0; a < 3; ++a) row[22 + a] = fgo_.prev_vel[a];
    for (int a = 0; a < 3; ++a) row[25 + a] = fgo_.prev_bias.accelerometer()[a];
    for (int a = 0; a < 3; ++a) row[28 + a] = fgo_.prev_bias.gyroscope()[a];
    row[31] = row[32] = row[33] = row[34] = NAN;
    for (size_t i = nfw0; i < fgo_.fwd_log.size(); ++i) {
      const auto& e = fgo_.fwd_log[i];
      row[e.kind == 0 ? 31 : 33] = e.nis;
      row[e.kind == 0 ? 32 : 34] = e.ok ? 1.0 : 0.0;
    }
    row[35] = fgo_.n_tag - nt0; row[36] = fgo_.n_gnss - ng0;
    row[37] = anchored_ ? 1 : 0;
    row[38] = room ? res_.n_fail - nfail0 : 0; row[39] = room ? res_.n_fail : 0;
    res_.kf_rows.insert(res_.kf_rows.end(), row, row + KF_COLS);
    have_flow_ = have_fwd_ = have_tag_ = have_gnss_ = false;
    rng_pend_ = NAN;
    t_kf_next_ += fgo_.kf_dt;
  }
}

ReplayResult Runner::finish() {
  if (cfg_.batch && anchored_) {
    const auto t0 = std::chrono::steady_clock::now();
    gtsam::LevenbergMarquardtParams prm;
    prm.setMaxIterations(50);
    prm.setRelativeErrorTol(1e-6);
    gtsam::LevenbergMarquardtOptimizer opt(fgo_.all_g, fgo_.all_est, prm);
    const gtsam::Values r = opt.optimize();
    res_.batch_s = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    res_.batch_error = opt.error();
    res_.batch_iterations = static_cast<int>(opt.iterations());
    for (const auto& kt : fgo_.key_t) {
      if (!r.exists(X(kt.first))) continue;
      const Pose3 p = r.at<Pose3>(X(kt.first));
      const gtsam::Matrix3 R = p.rotation().matrix();
      res_.batch_rows.push_back(kt.first);
      res_.batch_rows.push_back(kt.second);
      res_.batch_rows.push_back(p.x()); res_.batch_rows.push_back(p.y()); res_.batch_rows.push_back(p.z());
      for (int a = 0; a < 3; ++a)
        for (int b = 0; b < 3; ++b) res_.batch_rows.push_back(R(a, b));
    }
  }
  res_.n_flow = fgo_.n_flow; res_.n_range = fgo_.n_range; res_.n_imu = fgo_.n_imu;
  res_.n_tag = fgo_.n_tag; res_.n_gnss = fgo_.n_gnss; res_.n_replaced = gp_.n_replaced;
  return res_;
}

ReplayResult run_processed(const ReplayConfig& cfg, const std::vector<double>& ev, bool own_averager) {
  Runner run(cfg, own_averager);
  for (size_t i = 0; i < ev.size() / EV_COLS; ++i) run.on_event(&ev[i * EV_COLS]);
  return run.finish();
}

// ---------------- native front end ----------------
std::vector<double> offline_imu_timing(const std::vector<double>& raw, const ReplayConfig& cfg, FrontEndStats* st) {
  const size_t n = raw.size() / EV_COLS;
  std::vector<std::array<double, EV_COLS>> ev(n);
  for (size_t i = 0; i < n; ++i) std::copy(&raw[i * EV_COLS], &raw[i * EV_COLS] + EV_COLS, ev[i].begin());
  // gap rule (imu_timing.apply_gap_rule)
  if (cfg.gap_verdict == "unusable") throw std::runtime_error("unusable for the replay estimators (imu_gaps.json)");
  if (cfg.gap_verdict == "trim") {
    const size_t n0 = ev.size();
    ev.erase(std::remove_if(ev.begin(), ev.end(),
                            [&](const std::array<double, EV_COLS>& e) { return !(e[1] >= cfg.gap_replay_start); }),
             ev.end());
    if (st) st->n_trimmed = n0 - ev.size();
  }
  // dejitter (imu_timing.dejitter_imu): least-squares line t_i = a + b*i through the IMU receipt stamps, bag order
  std::vector<size_t> idx;
  for (size_t i = 0; i < ev.size(); ++i)
    if (static_cast<int>(ev[i][0]) == IMU) idx.push_back(i);
  const size_t m = idx.size();
  for (size_t j = 1; j < m; ++j)
    if (ev[idx[j]][1] < ev[idx[j - 1]][1]) throw std::runtime_error("IMU receipt stamps not monotonic; refusing to dejitter");
  // closed form about the means, in long double (numpy.polyfit uses a scaled SVD least squares: the fitted stamps
  // agree to round-off, not bit for bit; the difference is reported by the front-end tool)
  const long double mi = (static_cast<long double>(m) - 1.0L) / 2.0L;
  long double mt = 0;
  for (size_t j = 0; j < m; ++j) mt += ev[idx[j]][1];
  mt /= m;
  long double sxy = 0, sxx = 0;
  for (size_t j = 0; j < m; ++j) {
    const long double dx = static_cast<long double>(j) - mi;
    sxy += dx * (ev[idx[j]][1] - mt);
    sxx += dx * dx;
  }
  const long double b = sxy / sxx, a = mt - b * mi;
  double maxres = 0, ss = 0, sres = 0;
  for (size_t j = 0; j < m; ++j) {
    const double fit = static_cast<double>(a + b * static_cast<long double>(j));
    const double res = ev[idx[j]][1] - fit;
    maxres = std::max(maxres, std::abs(res));
    sres += res; ss += res * res;
    ev[idx[j]][1] = fit;
  }
  if (maxres > 0.025) throw std::runtime_error("IMU dejitter residual > 25 ms (dropped samples?); refusing");
  if (st) {
    st->period_ms = 1e3 * static_cast<double>(b);
    st->resid_maxabs_ms = 1e3 * maxres;
    st->resid_std_ms = 1e3 * std::sqrt(ss / m - (sres / m) * (sres / m));
  }
  std::vector<double> out;
  out.reserve(ev.size() * EV_COLS);
  for (const auto& e : ev) out.insert(out.end(), e.begin(), e.end());
  return out;
}

StreamFrontEnd::StreamFrontEnd(const ReplayConfig& cfg, double reorder_delay) : cfg_(cfg), delay_(reorder_delay) {}
StreamFrontEnd::~StreamFrontEnd() = default;

void StreamFrontEnd::push(const double* row) {
  std::array<double, EV_COLS> e;
  std::copy(row, row + EV_COLS, e.begin());
  const double t = e[1];
  max_lateness = std::max(max_lateness, t_newest_ - t);
  if (t < t_last_released_) ++n_out_of_order;
  t_newest_ = std::max(t_newest_, t);
  buf_.emplace(std::make_pair(t, seq_++), e);
  while (!buf_.empty() && buf_.begin()->first.first <= t_newest_ - delay_) {
    const auto e0 = buf_.begin()->second;
    buf_.erase(buf_.begin());
    release(e0);
  }
}

void StreamFrontEnd::release(const std::array<double, EV_COLS>& e) {
  t_last_released_ = std::max(t_last_released_, e[1]);
  released_.insert(released_.end(), e.begin(), e.end());
  if (runner_) {
    runner_->on_event(e.data());
    return;
  }
  pre_.push_back(e);
  const int kind = static_cast<int>(e[0]);
  if (kind == IMU && !have_imu0_) { have_imu0_ = true; t_imu0_ = e[1]; }
  if (kind == RNG && !have_rng_ && 0.05 <= e[2] && e[2] <= 40.0) { have_rng_ = true; cfg_.first_range = e[2]; }
  if (have_imu0_ && e[1] > t_imu0_ + 0.5) level_done_ = true;   // every IMU sample up to t_imu0 + 0.5 is released
  try_init();
}

void StreamFrontEnd::try_init() {
  if (runner_ || !have_imu0_ || !have_rng_ || !level_done_) return;
  Vector3 acc = Vector3::Zero();
  size_t na = 0;
  for (const auto& e : pre_)   // np.mean(list of 3-vectors, axis=0): sequential row sum, then divide
    if (static_cast<int>(e[0]) == IMU && e[1] <= t_imu0_ + 0.5) {
      acc = na == 0 ? Vector3(e[2], e[3], e[4]) : Vector3(acc[0] + e[2], acc[1] + e[3], acc[2] + e[4]);
      ++na;
    }
  cfg_.accel_mean = Vector3(acc[0] / na, acc[1] / na, acc[2] / na);
  cfg_.t_init = t_imu0_ + 0.5;
  runner_.reset(new Runner(cfg_, /*own_averager=*/true));
  for (const auto& e : pre_) runner_->on_event(e.data());
  pre_.clear();
}

ReplayResult StreamFrontEnd::finish() {
  while (!buf_.empty()) {
    const auto e0 = buf_.begin()->second;
    buf_.erase(buf_.begin());
    release(e0);
  }
  if (!runner_) throw std::runtime_error("stream ended before the init inputs were complete");
  return runner_->finish();
}

// ---------------- outputs ----------------
namespace {
void euler_to_quat(double r, double p, double y, double q[4]) {   // fgo_replay.euler_to_quat (ruling D10 form)
  const double cr = std::cos(r / 2), sr = std::sin(r / 2), cp = std::cos(p / 2), sp = std::sin(p / 2);
  const double cy = std::cos(y / 2), sy = std::sin(y / 2);
  q[0] = sr * cp * cy - cr * sp * sy; q[1] = cr * sp * cy + sr * cp * sy;
  q[2] = cr * cp * sy - sr * sp * cy; q[3] = cr * cp * cy + sr * sp * sy;
}
void write_tum(const std::string& path, const std::vector<double>& rows, int ncol, int it, int ip, int iR, int ianch) {
  FILE* f = std::fopen(path.c_str(), "w");
  for (size_t i = 0; i < rows.size() / ncol; ++i) {
    const double* w = &rows[i * ncol];
    if (ianch >= 0 && w[ianch] == 0) continue;
    gtsam::Matrix3 R;
    for (int a = 0; a < 3; ++a)
      for (int b = 0; b < 3; ++b) R(a, b) = w[iR + 3 * a + b];
    const Vector3 rpy = gtsam::Rot3(R).rpy();
    double q[4];
    euler_to_quat(rpy[0], rpy[1], rpy[2], q);
    std::fprintf(f, "%.6f %.6f %.6f %.6f %.6f %.6f %.6f %.6f\n", w[it], w[ip], w[ip + 1], w[ip + 2], q[0], q[1], q[2], q[3]);
  }
  std::fclose(f);
}
template <class T>
void write_bin(const std::string& path, const std::vector<T>& v) {
  std::ofstream f(path, std::ios::binary);
  f.write(reinterpret_cast<const char*>(v.data()), v.size() * sizeof(T));
}
}  // namespace

void write_outputs(const std::string& out, const ReplayConfig& cfg, const ReplayResult& r) {
  write_bin(out + ".kf.f64", r.kf_rows);
  write_bin(out + ".step_ns.i64", r.step_ns);
  write_bin(out + ".avg.f64", r.avg_log);
  write_tum(out + ".tum", r.kf_rows, KF_COLS, 1, 10, 13, cfg.mode == "room" ? 37 : -1);
  if (!r.batch_rows.empty()) {
    write_bin(out + ".batch.f64", r.batch_rows);
    write_tum(out + ".batch.tum", r.batch_rows, 14, 1, 2, 5, -1);
  }
  FILE* f = std::fopen((out + ".info.json").c_str(), "w");
  std::fprintf(f, "{\"n_kf\": %zu, \"n_flow\": %d, \"n_range\": %d, \"n_imu\": %d, \"n_tag\": %d, \"n_gnss\": %d, "
               "\"n_replaced\": %d, \"n_fail\": %d, \"t_anchor\": %.17g, \"batch_s\": %.6f, \"batch_error\": %.17g, "
               "\"batch_iterations\": %d, \"n_batch\": %zu}\n",
               r.step_ns.size(), r.n_flow, r.n_range, r.n_imu, r.n_tag, r.n_gnss, r.n_replaced, r.n_fail,
               std::isnan(r.t_anchor) ? -1.0 : r.t_anchor, r.batch_s, r.batch_error, r.batch_iterations, r.batch_rows.size() / 14);
  std::fclose(f);
}

void print_summary(const ReplayResult& r) {
  std::vector<long long> s = r.step_ns;
  std::sort(s.begin(), s.end());
  std::printf("[run] %zu keyframes, flow %d, range %d, imu %d, tag %d, gnss %d, gp replaced %d, failures %d\n", s.size(),
              r.n_flow, r.n_range, r.n_imu, r.n_tag, r.n_gnss, r.n_replaced, r.n_fail);
  if (!s.empty())
    std::printf("[timing] per-keyframe update: median=%.3fms p99=%.3fms\n", s[s.size() / 2] / 1e6,
                s[std::min(s.size() - 1, size_t(0.99 * (s.size() - 1) + 0.5))] / 1e6);
  if (!r.batch_rows.empty())
    std::printf("[batch] %zu keys, error %.6f, %d iterations, %.1f s\n", r.batch_rows.size() / 14, r.batch_error,
                r.batch_iterations, r.batch_s);
}

}  // namespace fgo_cpp
