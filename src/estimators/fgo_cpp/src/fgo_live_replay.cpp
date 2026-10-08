// Deterministic bag-replay harness for the live adapter (no ROS, no SITL). Feeds a "message tape" - the bag's
// messages in RECEIPT order with their header stamps, written by tools/make_tape.py - through LiveAdapter exactly as
// the ROS 2 node's callbacks would, and records every output.
//
// Usage: fgo_cpp_live_replay <tape.f64> <config.init.json> <out_prefix> [--imu-stamp time_ref|causal|header]
//          [--delay S] [--heading] [--heading-sigma-deg D] [--arm-source heartbeat|param|none] [--nav-frame corridor|enu]
//          [--no-gap-rule]
// Tape rows (9 float64): kind, header t, payload. Kinds: 0 IMU (acc xyz, gyro xyz), 1 attitude rates, 2 range,
// 3 flow (fx, fy, valid, inlier), 4 heading_sent (NED yaw, quality, angErr), 5 tag (x, y, yaw), 7 time_ref (sensor
// t), 8 armed (flag; a HEARTBEAT transition).
// Writes <out>.kf.f64 (fgo_export KF_COLS rows), <out>.live.f64 (t_k, valid, sent, t_us, step_ns, arrival index)
// and <out>.mav.bin (the ODOMETRY frames, concatenated, as they would go on the wire).
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>

#include "fgo_cpp/live_adapter.h"

using namespace fgo_cpp;

int main(int argc, char** argv) {
  if (argc < 4) {
    std::cerr << "usage: fgo_cpp_live_replay <tape.f64> <config.init.json> <out_prefix> [options]\n";
    return 2;
  }
  LiveConfig cfg;
  cfg.base = ReplayConfig::from_json(argv[2]);
  for (int i = 4; i < argc; ++i) {
    const std::string a = argv[i];
    if (a == "--imu-stamp") cfg.imu_stamp = argv[++i];
    else if (a == "--delay") cfg.reorder_delay = std::atof(argv[++i]);
    else if (a == "--heading") cfg.heading = true;
    else if (a == "--heading-sigma-deg") cfg.heading_sigma = std::atof(argv[++i]) * M_PI / 180.0;
    else if (a == "--heading-sigma-rad") cfg.heading_sigma = std::strtod(argv[++i], nullptr);
    else if (a == "--arm-source") cfg.arm_source = argv[++i];
    else if (a == "--nav-frame") cfg.nav_frame = argv[++i];
    else if (a == "--no-gap-rule") cfg.gap_rule = false;
    else { std::cerr << "unknown option " << a << "\n"; return 2; }
  }
  const std::string out = argv[3];
  const std::vector<double> tape = read_f64(argv[1]);
  std::vector<double> rows, live;
  std::ofstream mav(out + ".mav.bin", std::ios::binary);
  LiveAdapter ad(cfg, [&](const LiveOutput& o) {
    rows.insert(rows.end(), o.row, o.row + KF_COLS);
    const double l[6] = {o.t_k, o.valid ? 1.0 : 0.0, o.sent ? 1.0 : 0.0, double(o.t_us), double(o.step_ns),
                         double(o.arrival_index)};
    live.insert(live.end(), l, l + 6);
    if (o.sent) mav.write(reinterpret_cast<const char*>(o.frame.data()), o.frame.size());
  });
  for (size_t i = 0; i < tape.size() / 9; ++i) {
    const double* r = &tape[i * 9];
    switch (static_cast<int>(r[0])) {
      case 0: ad.imu(r[1], Vector3(r[2], r[3], r[4]), Vector3(r[5], r[6], r[7])); break;
      case 1: ad.att(r[1], Vector3(r[2], r[3], r[4])); break;
      case 2: ad.range(r[1], r[2]); break;
      case 3: ad.flow(r[1], r[2], r[3], r[4] != 0.0, r[5]); break;
      case 4: ad.heading(r[1], r[2], r[3], r[4]); break;
      case 5: ad.tag(r[1], r[2], r[3], r[4]); break;
      case 7: ad.time_ref(r[1], r[2]); break;
      case 8: ad.armed(r[2] != 0.0); break;
      default: break;
    }
  }
  ad.flush();
  {
    std::ofstream f(out + ".kf.f64", std::ios::binary);
    f.write(reinterpret_cast<const char*>(rows.data()), rows.size() * sizeof(double));
    std::ofstream g(out + ".live.f64", std::ios::binary);
    g.write(reinterpret_cast<const char*>(live.data()), live.size() * sizeof(double));
  }
  std::vector<double> st;
  size_t n_valid = 0;
  for (size_t i = 0; i < live.size() / 6; ++i) {
    st.push_back(live[i * 6 + 4] / 1e6);
    n_valid += live[i * 6 + 1] != 0.0;
  }
  std::sort(st.begin(), st.end());
  std::printf("[live] %zu keyframes, %zu ODOMETRY sent (%zu before the clock map settled), %zu valid; reinits %zu, "
              "gaps %zu, gap-invalid %d; heading rejected %zu; IMU unpaired %zu; max lateness %.3f s, out-of-order %zu\n",
              live.size() / 6, ad.n_sent, ad.n_unsettled, n_valid, ad.n_reinits, ad.gaps_seen.size(), int(ad.gap_invalid),
              ad.n_hdg_rejected, ad.n_imu_unpaired, ad.max_lateness(), ad.n_out_of_order());
  if (!st.empty())
    std::printf("[timing] per-keyframe step: median %.3f ms, p99 %.3f ms, max %.3f ms\n", st[st.size() / 2],
                st[std::min(st.size() - 1, size_t(0.99 * (st.size() - 1) + 0.5))], st.back());
  return 0;
}
