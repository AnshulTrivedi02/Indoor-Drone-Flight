// Numerics probe: the same operations as tools/fgo_cpp_probe.py, printed at %.17g, to confirm the
// source-built GTSAM matches the venv-fgo wheel (retract, Rot3 angles, tangent preintegration and
// its covariance, and the custom factors' linearisation) before any whole-flight comparison.
#include <cstdio>

#include <gtsam/inference/Symbol.h>
#include <gtsam/linear/JacobianFactor.h>

#include "fgo_cpp/fgo_core.h"

using namespace fgo_cpp;
using gtsam::symbol_shorthand::B;
using gtsam::symbol_shorthand::V;
using gtsam::symbol_shorthand::X;

static void pm(const char* name, const gtsam::Matrix& M) {
  std::printf("%s", name);
  for (int i = 0; i < M.rows(); ++i)
    for (int j = 0; j < M.cols(); ++j) std::printf(" %.17g", M(i, j));
  std::printf("\n");
}

int main() {
  const gtsam::Rot3 R = gtsam::Rot3::Ypr(0.1, -0.2, 0.3);
  pm("R", R.matrix());
  std::printf("yaw %.17g\n", R.yaw());
  pm("rpy", R.rpy());
  const Pose3 P(R, gtsam::Point3(1.0, 2.0, 3.0));
  gtsam::Vector6 d;
  d << 1e-6, -2e-6, 3e-6, 4e-6, -5e-6, 6e-6;
  pm("Pret+", P.retract(d).matrix());
  pm("Pret-", P.retract(-d).matrix());

  gtsam::PreintegratedCombinedMeasurements pim(make_pim_params(), Bias(Vector3(0.01, -0.02, 0.03), Vector3(0.001, 0.002, -0.003)));
  for (int i = 0; i < 200; ++i) {
    const Vector3 a(0.1 * i / 200, -0.05, 9.81 + 0.001 * i);
    const Vector3 w(0.01, -0.02 * i / 200, 0.03);
    pim.integrateMeasurement(a, w, 0.003);
  }
  pm("deltaRij", pim.deltaRij().matrix());
  pm("deltaPij", pim.deltaPij());
  pm("deltaVij", pim.deltaVij());
  pm("cov", pim.preintMeasCov());
  const Bias b0(Vector3(0.01, -0.02, 0.03), Vector3(0.001, 0.002, -0.003));
  const gtsam::NavState ns = pim.predict(gtsam::NavState(P, Vector3(0.4, 0.1, -0.05)), b0);
  pm("predP", ns.pose().matrix());
  pm("predV", ns.velocity());

  // custom factors linearised at a test point (whitened A | b)
  gtsam::Values vals;
  Vector vel(3);
  vel << 0.05, 0.45, -0.01;
  vals.insert(X(1), P);
  vals.insert(V(1), vel);
  vals.insert(B(1), b0);
  FlowFactor ff(gtsam::noiseModel::Isotropic::Sigma(2, 0.25), X(1), V(1), B(1), Eigen::Vector2d(0.02, 0.17),
                Vector3(0.011, -0.007, 0.002));
  auto jf = boost::dynamic_pointer_cast<gtsam::JacobianFactor>(ff.linearize(vals));
  pm("flowAb", jf->augmentedJacobian());
  RangeFactor rf(gtsam::noiseModel::Isotropic::Sigma(1, 0.5), X(1), 2.7);
  pm("rngAb", boost::dynamic_pointer_cast<gtsam::JacobianFactor>(rf.linearize(vals))->augmentedJacobian());
  YawPriorFactor yf(gtsam::noiseModel::Isotropic::Sigma(1, 0.5), X(1), 0.0995);
  pm("yawAb", boost::dynamic_pointer_cast<gtsam::JacobianFactor>(yf.linearize(vals))->augmentedJacobian());
  std::printf("wrap %.17g %.17g\n", wrap(-3.5), wrap(3.5));
  // part 2 factors
  HeadingFactor hf(gtsam::noiseModel::Isotropic::Sigma(1, 0.0026), X(1), 0.0981);
  pm("hdgAb", boost::dynamic_pointer_cast<gtsam::JacobianFactor>(hf.linearize(vals))->augmentedJacobian());
  YawRateFactor wf(gtsam::noiseModel::Isotropic::Sigma(1, 0.0028), B(1), 0.0021, 0.0013);
  pm("yrAb", boost::dynamic_pointer_cast<gtsam::JacobianFactor>(wf.linearize(vals))->augmentedJacobian());
  TagFactor tf(gtsam::noiseModel::Diagonal::Sigmas(gtsam::Vector3(0.05, 0.05, 0.0873)), X(1), 1.02, 1.97, 0.11);
  pm("tagAb", boost::dynamic_pointer_cast<gtsam::JacobianFactor>(tf.linearize(vals))->augmentedJacobian());
  GnssFactor gf(gtsam::noiseModel::Diagonal::Sigmas(gtsam::Vector4(0.5, 0.5, 0.3, 0.3)), X(1), V(1),
                gtsam::Vector4(1.1, 2.2, 0.04, 0.5));
  pm("gnssAb", boost::dynamic_pointer_cast<gtsam::JacobianFactor>(gf.linearize(vals))->augmentedJacobian());

  // one FGO keyframe through the real smoother: variant 0 = priors + CombinedImuFactor only (pure GTSAM),
  // 1 = + yaw cap + range, 2 = + flow. Attributes any difference to the library build or to the port.
  for (int variant = 0; variant < 3; ++variant) {
    FGO f(0.25, 1.0 / 30.0, 2);
    f.init(Vector3(-0.0009, 0.0009, 9.8107), 0.075, 10.0);
    for (int i = 0; i < 11; ++i) {
      const Vector3 a(0.1 * i / 200, -0.05, 9.81 + 0.001 * i);
      const Vector3 w(0.01, -0.02 * i / 200, 0.03);
      f.integrate_imu(a, w, 0.003);
    }
    const FlowMeas fm{Eigen::Vector2d(0.02, 0.17), true, 0.9};
    f.no_yawcap = (variant == 0);
    f.keyframe(10.0 + 1.0 / 30.0, variant == 2 ? &fm : nullptr, Vector3(0.011, -0.007, 0.002), variant >= 1 ? 0.08 : NAN);
    std::printf("kf%d", variant);
    const gtsam::Matrix4 M = f.prev_pose.matrix();
    for (int i = 0; i < 12; ++i) std::printf(" %.17g", M(i / 4, i % 4));
    for (int i = 0; i < 3; ++i) std::printf(" %.17g", f.prev_vel[i]);
    for (int i = 0; i < 6; ++i) std::printf(" %.17g", f.prev_bias.vector()[i]);
    std::printf("\n");
  }
  return 0;
}
