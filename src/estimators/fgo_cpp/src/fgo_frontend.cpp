// Native-input replay (task C). Consumes the RAW bag-order stream (<prefix>.raw.f64: header stamps, before any
// processing) and does the input handling itself:
//   offline_imu_timing  gap rule + IMU dejitter (offline only; a live node stamps IMU with /imu/time_ref instead)
//   StreamFrontEnd      events pushed one at a time in arrival (bag) order: reorder buffer, init inputs (gravity
//                       levelling, first range, t_init), interval-averaged gyro for flow and forward frames, runner.
// From <prefix>.init.json it takes ONLY configuration (mode, window, LM, sigmas, arming time, the imu_gaps.json
// verdict), never the processed inputs; the exported init inputs are read only to REPORT the comparison.
//
// Usage: fgo_cpp_frontend <prefix> <out_prefix> [reorder_delay_s (default 1.0)]
//   writes the fgo_cpp_replay outputs plus <out>.events.f64 (its own released stream) and <out>.frontend.json
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>

#include "fgo_cpp/replay_common.h"

int main(int argc, char** argv) {
  if (argc < 3) {
    std::cerr << "usage: fgo_cpp_frontend <dump_prefix> <out_prefix> [reorder_delay_s]\n";
    return 2;
  }
  const std::string pre = argv[1], out = argv[2];
  const double delay = argc > 3 ? std::atof(argv[3]) : 1.0;
  const fgo_cpp::ReplayConfig exported = fgo_cpp::ReplayConfig::from_json(pre + ".init.json");
  fgo_cpp::ReplayConfig cfg = exported;
  cfg.accel_mean = fgo_cpp::Vector3::Constant(NAN);   // must be recomputed by the front end
  cfg.first_range = cfg.t_init = NAN;
  const std::vector<double> raw = fgo_cpp::read_f64(pre + ".raw.f64");
  fgo_cpp::FrontEndStats st;
  const std::vector<double> timed = fgo_cpp::offline_imu_timing(raw, cfg, &st);
  fgo_cpp::StreamFrontEnd fe(cfg, delay);
  for (size_t i = 0; i < timed.size() / fgo_cpp::EV_COLS; ++i) fe.push(&timed[i * fgo_cpp::EV_COLS]);
  fgo_cpp::ReplayResult res = fe.finish();
  const fgo_cpp::ReplayConfig& c = fe.config();
  {
    std::ofstream f(out + ".events.f64", std::ios::binary);
    f.write(reinterpret_cast<const char*>(fe.released().data()), fe.released().size() * sizeof(double));
  }
  FILE* f = std::fopen((out + ".frontend.json").c_str(), "w");
  std::fprintf(f, "{\"reorder_delay_s\": %.6f, \"max_lateness_s\": %.6f, \"n_out_of_order\": %zu, \"period_ms\": %.9f, "
               "\"resid_std_ms\": %.6f, \"resid_maxabs_ms\": %.6f, \"n_trimmed\": %zu, "
               "\"t_init\": %.17g, \"t_init_export\": %.17g, \"first_range\": %.17g, \"first_range_export\": %.17g, "
               "\"accel_mean\": [%.17g, %.17g, %.17g], \"accel_mean_export\": [%.17g, %.17g, %.17g]}\n",
               delay, fe.max_lateness, fe.n_out_of_order, st.period_ms, st.resid_std_ms, st.resid_maxabs_ms, st.n_trimmed,
               c.t_init, exported.t_init, c.first_range, exported.first_range, c.accel_mean[0], c.accel_mean[1],
               c.accel_mean[2], exported.accel_mean[0], exported.accel_mean[1], exported.accel_mean[2]);
  std::fclose(f);
  std::printf("[front end] reorder delay %.3f s, max lateness %.3f s, out-of-order %zu; dejitter period %.5f ms, "
              "resid std %.2f max %.2f ms, trimmed %zu\n[front end] vs export: t_init %s, accel_mean %s, first_range %s\n",
              delay, fe.max_lateness, fe.n_out_of_order, st.period_ms, st.resid_std_ms, st.resid_maxabs_ms, st.n_trimmed,
              c.t_init == exported.t_init ? "bit-identical" : "DIFFERENT",
              c.accel_mean == exported.accel_mean ? "bit-identical" : "DIFFERENT",
              c.first_range == exported.first_range ? "bit-identical" : "DIFFERENT");
  fgo_cpp::write_outputs(out, c, res);
  fgo_cpp::print_summary(res);
  return 0;
}
