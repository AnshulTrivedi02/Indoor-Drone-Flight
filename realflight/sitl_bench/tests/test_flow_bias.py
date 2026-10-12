"""Offline check of the wbench5_m2r stimulus maths (realflight/sitl_bench/flow_bias_bridge.py); no ROS needed."""
import pytest

from realflight.sitl_bench.flow_bias_bridge import CAM_BELOW_LIDAR_M, bias_rad


def test_velocity_equivalent_bias_scales_with_camera_height():
    # v_b / r with r = rng - 0.13: 1.0 m/s at a LiDAR range of 1.63 m (camera 1.5 m) is 0.667 rad/s
    assert bias_rad(1.0, 0.0, 0.0, 5.0, 1.63, 2.0) == pytest.approx(1.0 / 1.5)
    assert bias_rad(1.5, 0.0, 0.0, 5.0, 0.89, 2.0) == pytest.approx(1.5 / (0.89 - CAM_BELOW_LIDAR_M))


def test_ramp():
    assert bias_rad(1.0, 1.0, 10.0, 10.0, 1.13, 2.0) == pytest.approx(0.0)
    assert bias_rad(1.0, 1.0, 10.0, 10.5, 1.13, 2.0) == pytest.approx(0.5)
    assert bias_rad(1.0, 1.0, 10.0, 12.0, 1.13, 2.0) == pytest.approx(1.0)


def test_cut_above_max_rate_and_without_range():
    # the cut height for v = 1.0 m/s, max 2.0 rad/s: r < 0.5 m, i.e. a LiDAR range < 0.63 m
    assert bias_rad(1.0, 0.0, 0.0, 1.0, 0.64, 2.0) is not None
    assert bias_rad(1.0, 0.0, 0.0, 1.0, 0.62, 2.0) is None
    assert bias_rad(1.5, 0.0, 0.0, 1.0, 0.87, 2.0) is None      # v 1.5: cut below 0.88 m
    assert bias_rad(1.0, 0.0, 0.0, 1.0, -1.0, 2.0) is None      # stale range (flow_bridge reports -1)
    assert bias_rad(1.0, 0.0, 0.0, 1.0, 0.15, 2.0) is None      # camera at or below the floor
