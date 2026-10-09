import sys
ROOT = sys.argv[1] + '/src/estimators/fgo_cpp/'
s = None


def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)


p = ROOT + 'tools/fgo_cpp_probe.py'
s = open(p).read()
rep('''# one FGO keyframe through the real smoother (see probe.cpp): 0 = IMU only, 1 = + yaw cap + range, 2 = + flow
from fgo_core import FGO
for variant in range(3):
    f = FGO(window=0.25, kf_dt=1.0 / 30.0, lm_maxiter=2)
    f.init(np.array([-0.0009, 0.0009, 9.8107]), 0.075, 10.0)
    f.no_yawcap = variant == 0
''', '''# one FGO keyframe through the real smoother (see probe.cpp): 0 = IMU only, 1 = + range (the yaw-cap gate is not yet
# checked, < 140 ms after init), 2 = + flow; 3 = as 2 with a forced gate check (closed), 4 = as 3 with the gate prior's
# attitude variances inflated so that the gate opens and the cap factor is added (§9.4 gate, ruling 2026-10-09)
from fgo_core import FGO
for variant in range(5):
    f = FGO(window=0.25, kf_dt=1.0 / 30.0, lm_maxiter=2)
    f.init(np.array([-0.0009, 0.0009, 9.8107]), 0.075, 10.0)
    f.no_yawcap = variant == 0
    if variant >= 3:
        f.t_yawchk = 9.0
    if variant == 4:
        f.cov_gate = f.cov_gate.copy()
        for i in range(3):
            f.cov_gate[i, i] = 0.02
''')
rep('''    f.keyframe(10.0 + 1.0 / 30.0, flow=((np.array([0.02, 0.17]), True, 0.9) if variant == 2 else None),''',
    '''    f.keyframe(10.0 + 1.0 / 30.0, flow=((np.array([0.02, 0.17]), True, 0.9) if variant >= 2 else None),''')
rep('''    print(f"kf{variant}" + "".join(f" {v:.17g}" for v in vals))''', '''    print(f"kf{variant}" + "".join(f" {v:.17g}" for v in vals))
    if variant >= 3:
        print(f"gate{variant}" + "".join(f" {float(v):.17g}" for v in f.yawgate_log[0]))''')
open(p, 'w').write(s)

p = ROOT + 'src/probe.cpp'
s = open(p).read()
rep('''  // 1 = + yaw cap + range, 2 = + flow. Attributes any difference to the library build or to the port.
  for (int variant = 0; variant < 3; ++variant) {
    FGO f(0.25, 1.0 / 30.0, 2);
    f.init(Vector3(-0.0009, 0.0009, 9.8107), 0.075, 10.0);''', '''  // 1 = + range (yaw-cap gate not yet checked), 2 = + flow, 3 = as 2 with a forced gate check (closed), 4 = as 3 with
  // the gate prior's attitude variances inflated so that the cap is added (§9.4 gate, ruling 2026-10-09).
  // Attributes any difference to the library build or to the port.
  for (int variant = 0; variant < 5; ++variant) {
    FGO f(0.25, 1.0 / 30.0, 2);
    f.init(Vector3(-0.0009, 0.0009, 9.8107), 0.075, 10.0);
    if (variant >= 3) f.t_yawchk = 9.0;
    if (variant == 4)
      for (int i = 0; i < 3; ++i) f.cov_gate(i, i) = 0.02;''')
rep('''    f.keyframe(10.0 + 1.0 / 30.0, variant == 2 ? &fm : nullptr,''', '''    f.keyframe(10.0 + 1.0 / 30.0, variant >= 2 ? &fm : nullptr,''')
rep('''    for (int i = 0; i < 6; ++i) std::printf(" %.17g", f.prev_bias.vector()[i]);
    std::printf("\\n");
  }''', '''    for (int i = 0; i < 6; ++i) std::printf(" %.17g", f.prev_bias.vector()[i]);
    std::printf("\\n");
    if (variant >= 3) {
      const auto& e = f.yawgate_log.at(0);
      std::printf("gate%d %.17g %.17g %.17g %.17g\\n", variant, e.t, double(e.k), e.trace, e.fired ? 1.0 : 0.0);
    }
  }''')
open(p, 'w').write(s)
print("done")
