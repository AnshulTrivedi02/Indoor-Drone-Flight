#!/usr/bin/env bash
# Item 2f (FGO Pi path): fetch the arm64 Boost 1.83 packages that GTSAM 4.2.1 links against and unpack them into a
# SCRATCH sysroot with `dpkg-deb -x`. Nothing is installed (no apt, no sudo). The version is pinned to the host's
# x86 Boost (1.83.0-2.1ubuntu3.2, Ubuntu 24.04 noble-updates), so both architectures use the same Boost source.
# GTSAM 4.2.1 needs serialization filesystem program_options timer chrono (cmake/HandleBoost.cmake:26); filesystem
# pulls in atomic/system; thread/date_time/regex are fetched for completeness of the Boost CMake config.
set -euo pipefail
A=${A:-/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/arm64}
V=1.83.0-2.1ubuntu3.2
M=http://ports.ubuntu.com/ubuntu-ports/pool/main/b/boost1.83
U=http://ports.ubuntu.com/ubuntu-ports/pool/universe/b/boost1.83
mkdir -p "$A/debs" "$A/sysroot"
cd "$A/debs"
MAIN="libboost1.83-dev libboost-atomic1.83-dev libboost-atomic1.83.0 libboost-chrono1.83-dev libboost-chrono1.83.0t64
 libboost-date-time1.83-dev libboost-date-time1.83.0 libboost-filesystem1.83.0 libboost-program-options1.83-dev
 libboost-program-options1.83.0 libboost-regex1.83-dev libboost-regex1.83.0 libboost-serialization1.83-dev
 libboost-serialization1.83.0 libboost-system1.83-dev libboost-system1.83.0 libboost-thread1.83-dev libboost-thread1.83.0"
UNIV="libboost-filesystem1.83-dev libboost-timer1.83-dev libboost-timer1.83.0"
for f in $MAIN; do [ -f "${f}_${V}_arm64.deb" ] || curl -sf -O "$M/${f}_${V}_arm64.deb"; done
for f in $UNIV; do [ -f "${f}_${V}_arm64.deb" ] || curl -sf -O "$U/${f}_${V}_arm64.deb"; done
for d in ./*.deb; do dpkg-deb -x "$d" "$A/sysroot"; done
sha256sum ./*.deb > "$A/debs.sha256"
echo "fetched $(ls ./*.deb | wc -l) debs into $A/sysroot"
