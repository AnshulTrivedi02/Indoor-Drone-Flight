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

add_library(fgo_cpp_core src/fgo_core.cpp src/replay_common.cpp src/live_adapter.cpp)
target_include_directories(fgo_cpp_core PUBLIC include)
target_link_libraries(fgo_cpp_core PUBLIC gtsam gtsam_unstable)
if(FGO_CPP_EMULATE_NUMPY_GEMV)
  target_compile_definitions(fgo_cpp_core PUBLIC FGO_CPP_EMULATE_NUMPY_GEMV)
endif()

add_executable(fgo_cpp_replay src/fgo_replay.cpp)
target_link_libraries(fgo_cpp_replay PRIVATE fgo_cpp_core)

add_executable(fgo_cpp_frontend src/fgo_frontend.cpp)
target_link_libraries(fgo_cpp_frontend PRIVATE fgo_cpp_core)

add_executable(fgo_cpp_probe src/probe.cpp)
target_link_libraries(fgo_cpp_probe PRIVATE fgo_cpp_core)

add_executable(fgo_cpp_live_replay src/fgo_live_replay.cpp)
target_link_libraries(fgo_cpp_live_replay PRIVATE fgo_cpp_core)

set_target_properties(fgo_cpp_replay fgo_cpp_frontend fgo_cpp_probe fgo_cpp_live_replay PROPERTIES
  BUILD_RPATH "$ENV{HOME}/opt/gtsam-4.2.1/lib" INSTALL_RPATH "$ENV{HOME}/opt/gtsam-4.2.1/lib")
# DT_RPATH (not RUNPATH) so libgtsam.so also finds libmetis-gtsam.so in the same directory.
target_link_options(fgo_cpp_replay PRIVATE "-Wl,--disable-new-dtags")
target_link_options(fgo_cpp_probe PRIVATE "-Wl,--disable-new-dtags")
target_link_options(fgo_cpp_frontend PRIVATE "-Wl,--disable-new-dtags")
target_link_options(fgo_cpp_live_replay PRIVATE "-Wl,--disable-new-dtags")

# The live ROS 2 node (needs ROS 2 Jazzy and the thesis workspace's optical_flow_interfaces on CMAKE_PREFIX_PATH,
# e.g. -DCMAKE_PREFIX_PATH="/opt/ros/jazzy;$HOME/thesis_ws/install/optical_flow_interfaces").
option(FGO_CPP_BUILD_ROS "Build the ROS 2 node fgo_cpp_node" ON)
if(FGO_CPP_BUILD_ROS)
  find_package(rclcpp QUIET)
  if(rclcpp_FOUND)
    find_package(sensor_msgs REQUIRED)
    find_package(geometry_msgs REQUIRED)
    find_package(std_msgs REQUIRED)
    find_package(optical_flow_interfaces REQUIRED)
    add_executable(fgo_cpp_node src/fgo_cpp_node.cpp)
    target_link_libraries(fgo_cpp_node PRIVATE fgo_cpp_core rclcpp::rclcpp ${sensor_msgs_TARGETS} ${geometry_msgs_TARGETS}
                          ${std_msgs_TARGETS} ${optical_flow_interfaces_TARGETS})
    set_target_properties(fgo_cpp_node PROPERTIES BUILD_RPATH "$ENV{HOME}/opt/gtsam-4.2.1/lib"
                          INSTALL_RPATH "$ENV{HOME}/opt/gtsam-4.2.1/lib")
    # run_trial.sh (FGO_NODE_IMPL=cpp) runs $HOME/opt/fgo_cpp/bin/fgo_cpp_node: configure with
    # -DCMAKE_INSTALL_PREFIX=$HOME/opt/fgo_cpp and `make install`
    install(TARGETS fgo_cpp_node RUNTIME DESTINATION bin)
    target_link_options(fgo_cpp_node PRIVATE "-Wl,--disable-new-dtags")
  else()
    message(STATUS "rclcpp not found: fgo_cpp_node not built (add /opt/ros/jazzy to CMAKE_PREFIX_PATH)")
  endif()
endif()
install(TARGETS fgo_cpp_live_replay fgo_cpp_replay fgo_cpp_frontend RUNTIME DESTINATION bin)
