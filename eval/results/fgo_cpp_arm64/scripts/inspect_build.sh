#!/bin/bash
# Item 2f: identify the arm64 build products (architecture, linkage, no x86 rpath, GTSAM found from the arm prefix,
# and whether any fused multiply-add instructions were emitted despite -ffp-contract=off).
A=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/arm64
grep -E "^GTSAM_DIR|^GTSAM_UNSTABLE_DIR|^CMAKE_CXX_FLAGS:|^CMAKE_CXX_COMPILER:" "$A/build-fgo/CMakeCache.txt"
for f in "$A/build-fgo/fgo_cpp_replay" "$A/gtsam-4.2.1/lib/libgtsam.so.4.2.1" "$A/gtsam-4.2.1/lib/libgtsam_unstable.so.4.2.1" "$A/gtsam-4.2.1/lib/libmetis-gtsam.so"; do
  echo "== $(basename "$f"): $(file -b "$f" | cut -c1-80)"
  readelf -d "$f" | grep -E "NEEDED|RPATH|RUNPATH"
done
for f in "$A/build-fgo/fgo_cpp_replay" "$A/gtsam-4.2.1/lib/libgtsam.so.4.2.1" "$A/gtsam-4.2.1/lib/libgtsam_unstable.so.4.2.1"; do
  echo "$(basename "$f"): scalar fmadd/fmsub/fnmadd/fnmsub $(aarch64-linux-gnu-objdump -d "$f" | grep -cE '\sf(n)?m(add|sub)\s'), vector fmla/fmls $(aarch64-linux-gnu-objdump -d "$f" | grep -cE '\sfml[as]\s')"
done
md5sum "$A/gtsam-4.2.1/lib/libgtsam.so.4.2.1" "$A/gtsam-4.2.1/lib/libgtsam_unstable.so.4.2.1" "$A/gtsam-4.2.1/lib/libmetis-gtsam.so"
du -sh "$A/gtsam-4.2.1/lib" "$A/build-fgo/fgo_cpp_replay"
