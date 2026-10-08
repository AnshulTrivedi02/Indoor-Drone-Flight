// Native-input replay (task C): consumes the RAW bag-order stream (<prefix>.raw.f64: header stamps, before any
// processing) and does the input handling itself - the gap rule, the IMU dejitter, the stable time sort, the
// gravity levelling / first range, and the interval-averaged gyro for flow and forward frames - then runs the same
// runner as fgo_cpp_replay. From <prefix>.init.json it takes ONLY configuration (mode, window, LM, sigmas, arming
// time, the imu_gaps.json verdict), never the processed inputs.
//
// Usage: fgo_cpp_frontend <prefix> <out_prefix>
//   writes the fgo_cpp_replay outputs plus <out>.events.f64 (its own processed stream) and <out>.frontend.json
#include <cstdio>
#include <fstream>
#include <iostream>

#include "fgo_cpp/replay_common.h"

int main(int argc, char** argv) {
  if (argc < 3) {
    std::cerr << "usage: fgo_cpp_frontend <dump_prefix> <out_prefix>\n";
    return 2;
  }
  const std::string pre = argv[1], out = argv[2];
  fgo_cpp::ReplayConfig cfg = fgo_cpp::ReplayConfig::from_json(pre + ".init.json");
  const fgo_cpp::ReplayConfig exported = cfg;   // only to REPORT the comparison of the init inputs
  const std::vector<double> raw = fgo_cpp::read_f64(pre + ".raw.f64");
  fgo_cpp::FrontEndStats st;
  const std::vector<double> ev = fgo_cpp::front_end(raw, cfg, &st);
  {
    std::ofstream f(out + ".events.f64", std::ios::binary);
    f.write(reinterpret_cast<const char*>(ev.data()), ev.size() * sizeof(double));
  }
  FILE* f = std::fopen((out + ".frontend.json").c_str(), "w");
  std::fprintf(f, "{\"period_ms\": %.9f, \"resid_std_ms\": %.6f, \"resid_maxabs_ms\": %.6f, \"n_trimmed\": %zu, "
               "\"t_init\": %.17g, \"t_init_export\": %.17g, \"first_range\": %.17g, \"first_range_export\": %.17g, "
               "\"accel_mean\": [%.17g, %.17g, %.17g], \"accel_mean_export\": [%.17g, %.17g, %.17g]}\n",
               st.period_ms, st.resid_std_ms, st.resid_maxabs_ms, st.n_trimmed, cfg.t_init, exported.t_init,
               cfg.first_range, exported.first_range, cfg.accel_mean[0], cfg.accel_mean[1], cfg.accel_mean[2],
               exported.accel_mean[0], exported.accel_mean[1], exported.accel_mean[2]);
  std::fclose(f);
  std::printf("[front end] dejitter period %.5f ms, resid std %.2f max %.2f ms, trimmed %zu; t_init %s, accel_mean %s, "
              "first_range %s the export\n", st.period_ms, st.resid_std_ms, st.resid_maxabs_ms, st.n_trimmed,
              cfg.t_init == exported.t_init ? "==" : "!=", cfg.accel_mean == exported.accel_mean ? "==" : "!=",
              cfg.first_range == exported.first_range ? "==" : "!=");
  fgo_cpp::ReplayResult res = fgo_cpp::run_processed(cfg, ev, /*own_averager=*/true);
  fgo_cpp::write_outputs(out, cfg, res);
  fgo_cpp::print_summary(res);
  return 0;
}
