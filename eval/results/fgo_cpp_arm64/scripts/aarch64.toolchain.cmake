# Item 2f: CMake toolchain for cross-building GTSAM 4.2.1 and the C++ FGO for aarch64 (Raspberry Pi 4/5, 64-bit OS).
# Compiler: Ubuntu 24.04 g++-aarch64-linux-gnu 13.3 (the real binary, NOT the /usr/lib/ccache wrapper; the x86 GTSAM
# configure had ccache off). Boost 1.83 arm64 comes from a scratch sysroot unpacked with dpkg-deb (fetch_boost_arm64.sh).
# -ffp-contract=off: GCC contracts a*b+c to FMA by default on aarch64; the x86 reference build is plain x86-64 (no FMA),
# so contraction would add a rounding source that x86 does not have (same choice as src/forward_camera/cpp/build_aarch64.sh).
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)
set(CMAKE_C_COMPILER /usr/bin/aarch64-linux-gnu-gcc)
set(CMAKE_CXX_COMPILER /usr/bin/aarch64-linux-gnu-g++)
set(ARM_SYSROOT_EXTRA "$ENV{ARM_SYSROOT_EXTRA}" CACHE PATH "scratch sysroot holding the arm64 Boost")
set(ARM_PREFIX "$ENV{ARM_PREFIX}" CACHE PATH "arm64 install prefix for GTSAM")
set(CMAKE_FIND_ROOT_PATH /usr/aarch64-linux-gnu "${ARM_SYSROOT_EXTRA}" "${ARM_SYSROOT_EXTRA}/usr" "${ARM_PREFIX}")
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)
set(CMAKE_LIBRARY_ARCHITECTURE aarch64-linux-gnu)
set(CMAKE_C_FLAGS_INIT "-ffp-contract=off")
set(CMAKE_CXX_FLAGS_INIT "-ffp-contract=off")
set(CMAKE_CROSSCOMPILING_EMULATOR "qemu-aarch64;-L;/usr/aarch64-linux-gnu")
