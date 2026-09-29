#!/usr/bin/env bash
# Build the C++ heading library (system OpenCV 4.6). -ffp-contract=off: no FMA contraction, so the
# arithmetic rounds as numpy's does. nice'd: builds may run while a simulation flies.
set -e
cd "$(dirname "$0")"
nice -n 19 g++ -O2 -std=c++17 -ffp-contract=off -fPIC -shared -o libheading.so heading.cpp \
    $(pkg-config --cflags --libs opencv4 | tr ' ' '\n' | grep -E '^-I|opencv_core|opencv_imgproc' | tr '\n' ' ')
echo "built $(pwd)/libheading.so"
