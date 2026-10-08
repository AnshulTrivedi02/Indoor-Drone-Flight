// Replay executable for the C++ FGO port, driven by the PROCESSED event stream exported by fgo_replay.py /
// room_fgo_replay.py with FGO_DUMP_EVENTS=<prefix> (layout: src/estimators/fgo/fgo_export.py). It runs the SAME
// loop as the Python harness of the export's mode:
//   corridor: fgo_replay.py (baseline / heading / heading_yawrate arms)
//   room:     room_fgo_replay.py (experiment T tags, or experiment O GNSS), with the whole-flight batch if exported
// The state-independent inputs (gap rule, dejitter, sort, interval-averaged gyro) come from the export; the
// state-dependent ones (ground-proximity rule D15, re-anchor) are computed here.
//
// Usage: fgo_cpp_replay <prefix> <out_prefix>
//   writes <out>.kf.f64 (fgo_export KF_COLS layout), <out>.step_ns.i64, <out>.tum, <out>.batch.f64 (if batch)
#include <cstdio>
#include <iostream>

#include "fgo_cpp/replay_common.h"

int main(int argc, char** argv) {
  if (argc < 3) {
    std::cerr << "usage: fgo_cpp_replay <dump_prefix> <out_prefix>\n";
    return 2;
  }
  const std::string pre = argv[1], out = argv[2];
  const fgo_cpp::ReplayConfig cfg = fgo_cpp::ReplayConfig::from_json(pre + ".init.json");
  const std::vector<double> ev = fgo_cpp::read_f64(pre + ".events.f64");
  fgo_cpp::ReplayResult res = fgo_cpp::run_processed(cfg, ev);
  fgo_cpp::write_outputs(out, cfg, res);
  fgo_cpp::print_summary(res);
  return 0;
}
