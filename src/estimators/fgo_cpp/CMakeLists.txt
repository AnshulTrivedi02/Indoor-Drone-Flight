cmake_minimum_required(VERSION 3.16)
project(fgo_cpp CXX)

# C++ port of the thesis FGO (option A of docs/real_flights_plan.md §9.3; see docs/fgo_cpp_port.md).
# GTSAM 4.2.1 built from source into ~/opt/gtsam-4.2.1 to match the venv-fgo wheel. Eigen comes ONLY
# from GTSAM's exported target (its bundled 3.3.7): do not add find_package(Eigen3) here, mixing
# Eigen versions in one binary is undefined.
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()
list(APPEND CMAKE_PREFIX_PATH "$ENV{HOME}/opt/gtsam-4.2.1")
find_package(GTSAM 4.2.1 EXACT REQUIRED)
find_package(GTSAM_UNSTABLE 4.2.1 EXACT REQUIRED)

option(FGO_CPP_EMULATE_NUMPY_GEMV "Diagnostic: reproduce numpy/OpenBLAS rounding of R.T @ v in h_flow_pose" OFF)

add_library(fgo_cpp_core src/fgo_core.cpp)
target_include_directories(fgo_cpp_core PUBLIC include)
target_link_libraries(fgo_cpp_core PUBLIC gtsam gtsam_unstable)
if(FGO_CPP_EMULATE_NUMPY_GEMV)
  target_compile_definitions(fgo_cpp_core PUBLIC FGO_CPP_EMULATE_NUMPY_GEMV)
endif()

add_executable(fgo_cpp_replay src/fgo_replay.cpp)
target_link_libraries(fgo_cpp_replay PRIVATE fgo_cpp_core)

add_executable(fgo_cpp_probe src/probe.cpp)
target_link_libraries(fgo_cpp_probe PRIVATE fgo_cpp_core)

set_target_properties(fgo_cpp_replay fgo_cpp_probe PROPERTIES
  BUILD_RPATH "$ENV{HOME}/opt/gtsam-4.2.1/lib" INSTALL_RPATH "$ENV{HOME}/opt/gtsam-4.2.1/lib")
# DT_RPATH (not RUNPATH) so libgtsam.so also finds libmetis-gtsam.so in the same directory.
target_link_options(fgo_cpp_replay PRIVATE "-Wl,--disable-new-dtags")
target_link_options(fgo_cpp_probe PRIVATE "-Wl,--disable-new-dtags")
