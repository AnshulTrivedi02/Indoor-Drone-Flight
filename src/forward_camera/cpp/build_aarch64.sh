#!/usr/bin/env bash
# Cross-build the C++ heading library for ARM64 (Raspberry Pi 4/5, 64-bit OS) — real-flight plan, tooling item 2.
# Same source and flags as build.sh (-O2 -std=c++17 -ffp-contract=off: on aarch64 GCC contracts to FMA BY DEFAULT,
# which would change the rounding against numpy), linked against OpenCV 4.6.0 core+imgproc cross-built from the
# official 4.6.0 source into $OCV (the frozen calibration used OpenCV 4.6's LSD). The OpenCV libraries are copied
# next to the output with an $ORIGIN rpath, so the folder is self-contained for deployment.
# Toolchain: g++-aarch64-linux-gnu (Ubuntu 13.3). OpenCV: ~/cross/opencv-4.6.0-aarch64 (see docs/real_flights_pi_readiness.md).
set -e
cd "$(dirname "$0")"
OCV="${OCV:-$HOME/cross/opencv-4.6.0-aarch64}"
OUT=aarch64; mkdir -p "$OUT"
nice -n 19 aarch64-linux-gnu-g++ -O2 -std=c++17 -ffp-contract=off -fPIC -shared -o "$OUT/libheading.so" heading.cpp \
    -I"$OCV/include/opencv4" -L"$OCV/lib" -lopencv_core -lopencv_imgproc -Wl,-rpath,'$ORIGIN'
cp -P "$OCV"/lib/libopencv_core.so* "$OCV"/lib/libopencv_imgproc.so* "$OUT/"
nice -n 19 aarch64-linux-gnu-g++ -O2 -std=c++17 -ffp-contract=off -o "$OUT/heading_test" heading_test_main.cpp \
    -L"$OUT" -lheading -Wl,-rpath,'$ORIGIN'
echo "built $(pwd)/$OUT/libheading.so and heading_test"
