// C++ port of src/estimators/fgo/factors.py (flow, range, yaw-cap factors) and the parts of
// src/estimators/measurement_models.py they use (h_flow_pose, h_flow_rot, constants).
//
// Option A of docs/real_flights_plan.md §9.3: the Jacobians are the SAME numerical central
// differences as factors.py (EPS = 1e-6, Pose3::retract(+/-d), vector +/- d, component-wise
// ConstantBias), not analytic ones. Every arithmetic expression keeps the Python operation
// order so that the two implementations agree to floating-point round-off.
#pragma once

#include <cmath>
#include <algorithm>

#include <gtsam/base/Matrix.h>
#include <gtsam/base/Vector.h>
#include <gtsam/geometry/Pose3.h>
#include <gtsam/navigation/ImuBias.h>
#include <gtsam/nonlinear/NonlinearFactor.h>

namespace fgo_cpp {

using gtsam::Matrix;
using gtsam::Pose3;
using gtsam::Vector;
using gtsam::Vector3;
using Bias = gtsam::imuBias::ConstantBias;

// ---- measurement_models.py constants ----
constexpr double RANGE_LEVER = 0.12;   // LiDAR below base_link (m)
constexpr double CAM_OFFSET = 0.25;    // camera below base_link (m)
constexpr double H_MIN = 0.10;
constexpr double SIGN_X = +1.0;
constexpr double SIGN_Y = +1.0;
constexpr double EPS = 1e-6;           // factors.py EPS

// CPython float modulo: the result takes the sign of the divisor (C fmod takes the dividend's).
inline double py_fmod(double x, double w) {
  double m = std::fmod(x, w);
  if (m != 0.0 && ((w < 0.0) != (m < 0.0))) m += w;
  return m;
}

// factors._wrap: (a + pi) % (2 pi) - pi, with Python semantics.
inline double wrap(double a) { return py_fmod(a + M_PI, 2 * M_PI) - M_PI; }

// measurement_models.h_flow_rot: (+omega_x, -omega_y), FLU.
inline Eigen::Vector2d h_flow_rot(const Vector3& om) { return Eigen::Vector2d(+om[0], -om[1]); }

// measurement_models.h_flow_pose, in numpy's operation order.
inline Eigen::Vector2d h_flow_pose(const gtsam::Matrix3& R, const Vector3& v, double p_U, const Vector3& om) {
#ifdef FGO_CPP_EMULATE_NUMPY_GEMV
  // Diagnostic only (CMake option FGO_CPP_EMULATE_NUMPY_GEMV, default OFF): reproduce the rounding of
  // numpy's `R_wb.T @ v_world` on the thesis workstation, which goes to OpenBLAS dgemv and was measured
  // (2000/2000 random cases, every component) to equal fma(c2, v2, fma(c0, v0, c1 * v1)) per column c.
  // This depends on the BLAS kernel the CPU dispatches to; it is not part of the model.
  Vector3 vb;
  for (int j = 0; j < 3; ++j) vb[j] = std::fma(R(2, j), v[2], std::fma(R(0, j), v[0], R(1, j) * v[1]));
#else
  const Vector3 vb = R.transpose() * v;                       // R_wb.T @ v_world
#endif
  // np.cross(omega, [0, 0, -CAM_OFFSET]): (a1*b2 - a2*b1, a2*b0 - a0*b2, a0*b1 - a1*b0)
  const double b0 = 0.0, b1 = 0.0, b2 = -CAM_OFFSET;
  const Vector3 cr(om[1] * b2 - om[2] * b1, om[2] * b0 - om[0] * b2, om[0] * b1 - om[1] * b0);
  const Vector3 vs = vb + cr;
  const double h_cam = std::max(p_U - CAM_OFFSET, H_MIN);
  const double fxt = SIGN_X * (vs[1] / h_cam);
  const double fyt = SIGN_Y * (vs[0] / h_cam);
  const Eigen::Vector2d rot = h_flow_rot(om);
  return Eigen::Vector2d(fxt + rot[0], fyt + rot[1]);
}

// ---- numerical Jacobians on the manifold (factors._jac_pose / _jac_vec / _jac_bias) ----
template <class Err>
Matrix jac_pose(const Err& err, const Pose3& pose, const Vector& vel, const Bias& bias, int m) {
  Matrix H(m, 6);
  for (int j = 0; j < 6; ++j) {
    gtsam::Vector6 d = gtsam::Vector6::Zero();
    d[j] = EPS;
    H.col(j) = (err(pose.retract(d), vel, bias) - err(pose.retract(-d), vel, bias)) / (2 * EPS);
  }
  return H;
}

template <class Err>
Matrix jac_vec(const Err& err, const Pose3& pose, const Vector& vel, const Bias& bias, int m) {
  Matrix H(m, 3);
  for (int j = 0; j < 3; ++j) {
    Vector d = Vector::Zero(3);
    d[j] = EPS;
    H.col(j) = (err(pose, Vector(vel + d), bias) - err(pose, Vector(vel - d), bias)) / (2 * EPS);
  }
  return H;
}

template <class Err>
Matrix jac_bias(const Err& err, const Pose3& pose, const Vector& vel, const Bias& bias, int m) {
  Matrix H(m, 6);
  const Vector3 ba = bias.accelerometer(), bg = bias.gyroscope();
  for (int j = 0; j < 6; ++j) {
    gtsam::Vector6 d = gtsam::Vector6::Zero();
    d[j] = EPS;
    const Bias bp(Vector3(ba + d.head<3>()), Vector3(bg + d.tail<3>()));
    const Bias bm(Vector3(ba - d.head<3>()), Vector3(bg - d.tail<3>()));
    H.col(j) = (err(pose, vel, bp) - err(pose, vel, bm)) / (2 * EPS);
  }
  return H;
}

// ---- flow factor: 2-DOF on X(k), V(k), B(k) (factors.flow_factor) ----
// Velocity is a DYNAMIC gtsam::Vector, as the Python Values store it.
class FlowFactor : public gtsam::NoiseModelFactorN<Pose3, Vector, Bias> {
  using Base = gtsam::NoiseModelFactorN<Pose3, Vector, Bias>;
  Eigen::Vector2d meas_;
  Vector3 omega_meas_;

 public:
  FlowFactor(const gtsam::SharedNoiseModel& noise, gtsam::Key kx, gtsam::Key kv, gtsam::Key kb,
             const Eigen::Vector2d& flow_meas, const Vector3& omega_meas)
      : Base(noise, kx, kv, kb), meas_(flow_meas), omega_meas_(omega_meas) {}

  Vector err(const Pose3& pose, const Vector& vel, const Bias& bias) const {
    const gtsam::Matrix3 R = pose.rotation().matrix();
    const double p_U = pose.translation()[2];
    const Vector3 omega = omega_meas_ - bias.gyroscope();
    return Vector(h_flow_pose(R, Vector3(vel), p_U, omega) - meas_);
  }

  Vector evaluateError(const Pose3& pose, const Vector& vel, const Bias& bias,
                       boost::optional<Matrix&> H1 = boost::none, boost::optional<Matrix&> H2 = boost::none,
                       boost::optional<Matrix&> H3 = boost::none) const override {
    auto f = [this](const Pose3& p, const Vector& v, const Bias& b) { return err(p, v, b); };
    if (H1) *H1 = jac_pose(f, pose, vel, bias, 2);
    if (H2) *H2 = jac_vec(f, pose, vel, bias, 2);
    if (H3) *H3 = jac_bias(f, pose, vel, bias, 2);
    return err(pose, vel, bias);
  }

  gtsam::NonlinearFactor::shared_ptr clone() const override {
    return gtsam::NonlinearFactor::shared_ptr(new FlowFactor(*this));
  }
};

// ---- range factor: 1-DOF on X(k) (factors.range_factor) ----
class RangeFactor : public gtsam::NoiseModelFactorN<Pose3> {
  using Base = gtsam::NoiseModelFactorN<Pose3>;
  double r_;

 public:
  RangeFactor(const gtsam::SharedNoiseModel& noise, gtsam::Key kx, double range_meas) : Base(noise, kx), r_(range_meas) {}

  Vector err(const Pose3& pose) const {
    Vector e(1);
    e[0] = pose.translation()[2] - RANGE_LEVER - r_;
    return e;
  }

  Vector evaluateError(const Pose3& pose, boost::optional<Matrix&> H1 = boost::none) const override {
    auto f = [this](const Pose3& p, const Vector&, const Bias&) { return err(p); };
    if (H1) *H1 = jac_pose(f, pose, Vector(), Bias(), 1);
    return err(pose);
  }

  gtsam::NonlinearFactor::shared_ptr clone() const override {
    return gtsam::NonlinearFactor::shared_ptr(new RangeFactor(*this));
  }
};

// ---- weak yaw cap: 1-DOF zero-innovation anchor on yaw(X(k)) (factors.yaw_prior_factor) ----
class YawPriorFactor : public gtsam::NoiseModelFactorN<Pose3> {
  using Base = gtsam::NoiseModelFactorN<Pose3>;
  double yaw_ref_;

 public:
  YawPriorFactor(const gtsam::SharedNoiseModel& noise, gtsam::Key kx, double yaw_ref) : Base(noise, kx), yaw_ref_(yaw_ref) {}

  Vector err(const Pose3& pose) const {
    Vector e(1);
    e[0] = wrap(pose.rotation().yaw() - yaw_ref_);
    return e;
  }

  Vector evaluateError(const Pose3& pose, boost::optional<Matrix&> H1 = boost::none) const override {
    auto f = [this](const Pose3& p, const Vector&, const Bias&) { return err(p); };
    if (H1) *H1 = jac_pose(f, pose, Vector(), Bias(), 1);
    return err(pose);
  }

  gtsam::NonlinearFactor::shared_ptr clone() const override {
    return gtsam::NonlinearFactor::shared_ptr(new YawPriorFactor(*this));
  }
};

// ---- forward-camera heading (Phase 4): wrap(h_heading(yaw) - psi), h_heading = identity (factors.heading_factor) ----
class HeadingFactor : public gtsam::NoiseModelFactorN<Pose3> {
  using Base = gtsam::NoiseModelFactorN<Pose3>;
  double psi_;

 public:
  HeadingFactor(const gtsam::SharedNoiseModel& noise, gtsam::Key kx, double psi) : Base(noise, kx), psi_(psi) {}

  Vector err(const Pose3& pose) const {
    Vector e(1);
    e[0] = wrap(pose.rotation().yaw() - psi_);
    return e;
  }
  // the 1x6 central-difference Jacobian, also used by the chi-square gate (fgo_core._forward_factors Hx)
  Matrix H(const Pose3& pose) const {
    auto f = [this](const Pose3& p, const Vector&, const Bias&) { return err(p); };
    return jac_pose(f, pose, Vector(), Bias(), 1);
  }

  Vector evaluateError(const Pose3& pose, boost::optional<Matrix&> H1 = boost::none) const override {
    if (H1) *H1 = H(pose);
    return err(pose);
  }

  gtsam::NonlinearFactor::shared_ptr clone() const override {
    return gtsam::NonlinearFactor::shared_ptr(new HeadingFactor(*this));
  }
};

// ---- forward-camera yaw rate (Phase 4): (gyro_z_avg - b_gz) - omega on B(k) (factors.yawrate_factor) ----
class YawRateFactor : public gtsam::NoiseModelFactorN<Bias> {
  using Base = gtsam::NoiseModelFactorN<Bias>;
  double om_, gz_;

 public:
  YawRateFactor(const gtsam::SharedNoiseModel& noise, gtsam::Key kb, double omega_meas, double gyro_z_avg)
      : Base(noise, kb), om_(omega_meas), gz_(gyro_z_avg) {}

  Vector err(const Bias& b) const {
    Vector e(1);
    e[0] = (gz_ - b.gyroscope()[2]) - om_;
    return e;
  }

  Vector evaluateError(const Bias& b, boost::optional<Matrix&> H1 = boost::none) const override {
    auto f = [this](const Pose3&, const Vector&, const Bias& bb) { return err(bb); };
    if (H1) *H1 = jac_bias(f, Pose3(), Vector(), b, 1);
    return err(b);
  }

  gtsam::NonlinearFactor::shared_ptr clone() const override {
    return gtsam::NonlinearFactor::shared_ptr(new YawRateFactor(*this));
  }
};

// ---- AprilTag absolute fix (experiments T/L): (p_E - x, p_N - y, wrap(yaw - yaw_fix)) (factors.tag_factor) ----
class TagFactor : public gtsam::NoiseModelFactorN<Pose3> {
  using Base = gtsam::NoiseModelFactorN<Pose3>;
  double pE_, pN_, yaw_;

 public:
  TagFactor(const gtsam::SharedNoiseModel& noise, gtsam::Key kx, double pE, double pN, double yaw)
      : Base(noise, kx), pE_(pE), pN_(pN), yaw_(yaw) {}

  Vector err(const Pose3& pose) const {
    const gtsam::Point3 t = pose.translation();
    Vector e(3);
    e << t[0] - pE_, t[1] - pN_, wrap(pose.rotation().yaw() - yaw_);
    return e;
  }

  Vector evaluateError(const Pose3& pose, boost::optional<Matrix&> H1 = boost::none) const override {
    auto f = [this](const Pose3& p, const Vector&, const Bias&) { return err(p); };
    if (H1) *H1 = jac_pose(f, pose, Vector(), Bias(), 3);
    return err(pose);
  }

  gtsam::NonlinearFactor::shared_ptr clone() const override {
    return gtsam::NonlinearFactor::shared_ptr(new TagFactor(*this));
  }
};

// ---- GNSS (experiment O): (p_E, p_N, v_E, v_N) - fix on X(k), V(k) (factors.gnss_factor) ----
class GnssFactor : public gtsam::NoiseModelFactorN<Pose3, Vector> {
  using Base = gtsam::NoiseModelFactorN<Pose3, Vector>;
  gtsam::Vector4 z_;

 public:
  GnssFactor(const gtsam::SharedNoiseModel& noise, gtsam::Key kx, gtsam::Key kv, const gtsam::Vector4& z)
      : Base(noise, kx, kv), z_(z) {}

  Vector err(const Pose3& pose, const Vector& vel) const {
    const gtsam::Point3 t = pose.translation();
    Vector e(4);
    e << t[0] - z_[0], t[1] - z_[1], vel[0] - z_[2], vel[1] - z_[3];
    return e;
  }

  Vector evaluateError(const Pose3& pose, const Vector& vel, boost::optional<Matrix&> H1 = boost::none,
                       boost::optional<Matrix&> H2 = boost::none) const override {
    auto f = [this](const Pose3& p, const Vector& v, const Bias&) { return err(p, v); };
    if (H1) *H1 = jac_pose(f, pose, vel, Bias(), 4);
    if (H2) *H2 = jac_vec(f, pose, vel, Bias(), 4);
    return err(pose, vel);
  }

  gtsam::NonlinearFactor::shared_ptr clone() const override {
    return gtsam::NonlinearFactor::shared_ptr(new GnssFactor(*this));
  }
};

}  // namespace fgo_cpp
