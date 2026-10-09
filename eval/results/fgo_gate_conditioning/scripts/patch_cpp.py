"""DIAGNOSTIC ONLY (scratch copy; never committed or installed): dump, at every keyframe where the gate-only recursion
updates cov_gate, the 30x30 information matrix L that is inverted and the new 15x15 cov_gate, to $FGO_CONDDUMP.
Row: t, kk, L (900, row-major), cov_gate_new (225). L is recomputed with the same call (same prior, same values)."""
import re
p = "/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/gatecond/src_fgo_cpp/src/fgo_core.cpp"
s = open(p).read()
s = s.replace('#include <map>\n', '#include <map>\n#include <cstdio>\n#include <cstdlib>\n', 1)
old = """  } else if (cap_on) {
    cov_gate = posterior_cov(g, est, km1, kk, &cov_gate);
  }"""
new = """  } else if (cap_on) {
    const gtsam::Matrix prior_old = cov_gate;
    cov_gate = posterior_cov(g, est, km1, kk, &cov_gate);
    static FILE* fdump = nullptr; static bool tried = false;
    if (!tried) { tried = true; const char* e = std::getenv("FGO_CONDDUMP"); if (e) fdump = std::fopen(e, "wb"); }
    if (fdump) {
      const gtsam::Values vd = values_for(km1, kk, est.at<Pose3>(X(kk)), est.at<Vector>(V(kk)), est.at<Bias>(B(kk)), &est);
      const gtsam::Matrix Ld = info(g, vd, km1, kk, &prior_old);
      double hdr[2] = {t, double(kk)};
      std::fwrite(hdr, sizeof(double), 2, fdump);
      for (int r = 0; r < 30; ++r) for (int c = 0; c < 30; ++c) { double x = Ld(r, c); std::fwrite(&x, sizeof(double), 1, fdump); }
      for (int r = 0; r < 15; ++r) for (int c = 0; c < 15; ++c) { double x = cov_gate(r, c); std::fwrite(&x, sizeof(double), 1, fdump); }
      std::fflush(fdump);
    }
  }"""
assert s.count(old) == 1
s = s.replace(old, new)
open(p, "w").write(s)
print("patched")
