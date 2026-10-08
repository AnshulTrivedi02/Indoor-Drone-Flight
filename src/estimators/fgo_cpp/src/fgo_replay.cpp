// Replay executable for the C++ FGO port. Reads the event stream exported by
// src/estimators/fgo/fgo_replay.py with FGO_DUMP_EVENTS=<prefix> and drives fgo_cpp::FGO through the
// SAME loop as fgo_replay.py (IMU-clock keyframes at t_init + n*kf_dt accumulated by repeated addition,
// latest flow/range per keyframe, ground-proximity rule D15 ported, interval-averaged flow omega taken
// from the export because it does not depend on the estimator state).
//
// Usage: fgo_cpp_replay <prefix> <out_prefix>
//   reads  <prefix>.init.json, <prefix>.events.f64
//   writes <out_prefix>.kf.f64 (same 31-column layout as the Python export), <out_prefix>.step_ns.i64,
//          <out_prefix>.tum
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#include "fgo_cpp/fgo_core.h"

using namespace fgo_cpp;

namespace {

std::string slurp(const std::string& path) {
  std::ifstream f(path);
  if (!f) throw std::runtime_error("cannot open " + path);
  std::stringstream ss;
  ss << f.rdbuf();
  return ss.str();
}

// Minimal reader for the flat JSON the Python export writes (numbers, null, one numeric list).
const char* find_key(const std::string& js, const std::string& key) {
  const std::string pat = "\"" + key + "\":";
  const size_t p = js.find(pat);
  if (p == std::string::npos) throw std::runtime_error("missing key " + key);
  const char* c = js.c_str() + p + pat.size();
  while (*c == ' ' || *c == '\n') ++c;
  return c;
}
bool json_is_null(const std::string& js, const std::string& key) { return std::string(find_key(js, key), 4) == "null"; }
double json_num(const std::string& js, const std::string& key) { return std::strtod(find_key(js, key), nullptr); }
std::vector<double> json_list(const std::string& js, const std::string& key) {
  const char* c = find_key(js, key);
  if (*c != '[') throw std::runtime_error("not a list: " + key);
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

std::vector<double> read_f64(const std::string& path) {
  std::ifstream f(path, std::ios::binary | std::ios::ate);
  if (!f) throw std::runtime_error("cannot open " + path);
  const std::streamsize n = f.tellg();
  f.seekg(0);
  std::vector<double> v(n / sizeof(double));
  f.read(reinterpret_cast<char*>(v.data()), n);
  return v;
}

// fgo_replay.euler_to_quat (ruling D10 form)
void euler_to_quat(double r, double p, double y, double q[4]) {
  const double cr = std::cos(r / 2), sr = std::sin(r / 2), cp = std::cos(p / 2), sp = std::sin(p / 2);
  const double cy = std::cos(y / 2), sy = std::sin(y / 2);
  q[0] = sr * cp * cy - cr * sp * sy; q[1] = cr * sp * cy + sr * cp * sy;
  q[2] = cr * cp * sy - sr * sp * cy; q[3] = cr * cp * cy + sr * sp * sy;
}

}  // namespace

int main(int argc, char** argv) {
  if (argc < 3) {
    std::cerr << "usage: fgo_cpp_replay <dump_prefix> <out_prefix>\n";
    return 2;
  }
  const std::string pre = argv[1], out = argv[2];
  const std::string js = slurp(pre + ".init.json");
  const std::vector<double> am = json_list(js, "accel_mean");
  const double first_range = json_num(js, "first_range"), t_init = json_num(js, "t_init");
  const bool has_arm = !json_is_null(js, "t_arm");
  const double t_arm = has_arm ? json_num(js, "t_arm") : 0.0;
  const double window = json_num(js, "window"), kf_dt = json_num(js, "kf_dt");
  const int lm_iters = static_cast<int>(json_num(js, "lm_iters"));
  const int ncol = static_cast<int>(json_num(js, "event_cols"));
  const std::vector<double> ev = read_f64(pre + ".events.f64");
  const size_t nev = ev.size() / ncol;

  FGO fgo(window, kf_dt, lm_iters);
  fgo.init(Vector3(am[0], am[1], am[2]), first_range, t_init);
  GroundProximityFlow gp(t_arm, has_arm);

  std::vector<double> rows;
  std::vector<long long> step_ns;
  bool have_prev_imu = false;
  double t_prev_imu = 0.0;
  bool have_flow = false;
  FlowMeas flow_pend{Eigen::Vector2d::Zero(), false, 0.0};
  Vector3 flow_omega = Vector3::Zero();
  double rng_pend = NAN;
  double t_kf_next = t_init + fgo.kf_dt;

  for (size_t i = 0; i < nev; ++i) {
    const double* r = &ev[i * ncol];
    const int kind = static_cast<int>(r[0]);
    const double tt = r[1];
    if (tt < t_init) continue;            // before init only the attitude rate is used (folded into the export)
    if (kind == 1) continue;              // att: only the averager's fallback, already in the exported omega
    if (kind == 2) {                      // rng
      rng_pend = r[2];
      gp.on_range(tt, r[2]);
    } else if (kind == 3) {               // flow
      have_flow = true;
      flow_pend = FlowMeas{Eigen::Vector2d(r[2], r[3]), r[4] != 0.0, r[5]};
      flow_omega = Vector3(r[6], r[7], r[8]);
    } else if (kind == 0) {               // imu
      const Vector3 acc(r[2], r[3], r[4]), gyr(r[5], r[6], r[7]);
      gp.on_gyro(tt, gyr, fgo.prev_bias.gyroscope());
      if (have_prev_imu) fgo.integrate_imu(acc, gyr, tt - t_prev_imu);
      t_prev_imu = tt; have_prev_imu = true;
      while (tt >= t_kf_next) {
        const int k_before = fgo.k, nr0 = gp.n_replaced, nf0 = fgo.n_flow, nrg0 = fgo.n_range;
        const auto t0 = std::chrono::steady_clock::now();
        if (have_flow && flow_pend.valid && flow_pend.inlier > 0.0) {
          const Vector3 rpy = fgo.prev_pose.rotation().rpy();
          flow_pend.xy = gp.replace(flow_pend.xy, Vector3(flow_omega - fgo.prev_bias.gyroscope()), rpy[0], rpy[1]);
        }
        fgo.keyframe(t_kf_next, have_flow ? &flow_pend : nullptr, flow_omega, rng_pend);
        const auto t1 = std::chrono::steady_clock::now();
        step_ns.push_back(std::chrono::duration_cast<std::chrono::nanoseconds>(t1 - t0).count());
        const Pose3& P = fgo.prev_pose;
        const gtsam::Matrix3 R = P.rotation().matrix();
        double row[31] = {t_kf_next, fgo.t_last, double(k_before), double(fgo.k), double(gp.n_replaced - nr0),
                          double(fgo.n_flow - nf0), double(fgo.n_range - nrg0),
                          have_flow ? flow_pend.xy[0] : NAN, have_flow ? flow_pend.xy[1] : NAN, rng_pend,
                          P.x(), P.y(), P.z()};
        for (int a = 0; a < 3; ++a)
          for (int b = 0; b < 3; ++b) row[13 + 3 * a + b] = R(a, b);
        for (int a = 0; a < 3; ++a) row[22 + a] = fgo.prev_vel[a];
        for (int a = 0; a < 3; ++a) row[25 + a] = fgo.prev_bias.accelerometer()[a];
        for (int a = 0; a < 3; ++a) row[28 + a] = fgo.prev_bias.gyroscope()[a];
        rows.insert(rows.end(), row, row + 31);
        have_flow = false; rng_pend = NAN;
        t_kf_next += fgo.kf_dt;
      }
    }
  }

  {
    std::ofstream f(out + ".kf.f64", std::ios::binary);
    f.write(reinterpret_cast<const char*>(rows.data()), rows.size() * sizeof(double));
  }
  {
    std::ofstream f(out + ".step_ns.i64", std::ios::binary);
    f.write(reinterpret_cast<const char*>(step_ns.data()), step_ns.size() * sizeof(long long));
  }
  {
    FILE* f = std::fopen((out + ".tum").c_str(), "w");
    for (size_t i = 0; i < rows.size() / 31; ++i) {
      const double* w = &rows[i * 31];
      gtsam::Matrix3 R;
      for (int a = 0; a < 3; ++a)
        for (int b = 0; b < 3; ++b) R(a, b) = w[13 + 3 * a + b];
      const Vector3 rpy = gtsam::Rot3(R).rpy();
      double q[4];
      euler_to_quat(rpy[0], rpy[1], rpy[2], q);
      std::fprintf(f, "%.6f %.6f %.6f %.6f %.6f %.6f %.6f %.6f\n", w[1], w[10], w[11], w[12], q[0], q[1], q[2], q[3]);
    }
    std::fclose(f);
  }
  std::vector<long long> s = step_ns;
  std::sort(s.begin(), s.end());
  std::printf("[run] %zu keyframes, flow factors %d, range factors %d, imu %d, gp replaced %d\n", step_ns.size(),
              fgo.n_flow, fgo.n_range, fgo.n_imu, gp.n_replaced);
  if (!s.empty())
    std::printf("[timing] per-keyframe update: median=%.3fms p99=%.3fms\n", s[s.size() / 2] / 1e6,
                s[std::min(s.size() - 1, size_t(0.99 * (s.size() - 1) + 0.5))] / 1e6);
  return 0;
}
