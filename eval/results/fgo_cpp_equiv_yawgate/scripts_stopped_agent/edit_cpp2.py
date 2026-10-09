import sys
ROOT = sys.argv[1] + '/src/estimators/fgo_cpp/'
s = None


def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)


p = ROOT + 'include/fgo_cpp/replay_common.h'
s = open(p).read()
rep('''  std::vector<double> avg_log;      // per flow / forward frame after t_init: kind, t, omega xyz (forward: gz, NaN, NaN)
''', '''  std::vector<double> avg_log;      // per flow / forward frame after t_init: kind, t, omega xyz (forward: gz, NaN, NaN)
  std::vector<double> yawgate_log;  // §9.4 yaw-cap gate checks: t, k, trace of the predicted attitude cov, fired
  int n_yaw_check = 0, n_yaw_fire = 0;
''')
open(p, 'w').write(s)

p = ROOT + 'src/replay_common.cpp'
s = open(p).read()
rep('''  res_.n_tag = fgo_.n_tag; res_.n_gnss = fgo_.n_gnss; res_.n_replaced = gp_.n_replaced;
  return res_;''', '''  res_.n_tag = fgo_.n_tag; res_.n_gnss = fgo_.n_gnss; res_.n_replaced = gp_.n_replaced;
  res_.n_yaw_check = fgo_.n_yaw_check; res_.n_yaw_fire = fgo_.n_yaw_fire;
  res_.yawgate_log.clear();
  for (const auto& e : fgo_.yawgate_log)
    res_.yawgate_log.insert(res_.yawgate_log.end(), {e.t, double(e.k), e.trace, e.fired ? 1.0 : 0.0});
  return res_;''')
rep('''  write_bin(out + ".avg.f64", r.avg_log);
''', '''  write_bin(out + ".avg.f64", r.avg_log);
  write_bin(out + ".yawgate.f64", r.yawgate_log);
''')
rep('''  if (!r.batch_rows.empty())
    std::printf("[batch] %zu keys''', '''  std::printf("[yaw-cap gate] fired %d/%d checks (FGO_DESIGN §9.4)\\n", r.n_yaw_fire, r.n_yaw_check);
  if (!r.batch_rows.empty())
    std::printf("[batch] %zu keys''')
open(p, 'w').write(s)
print("done")
