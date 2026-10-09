import sys
ROOT = sys.argv[1] + '/src/estimators/'
s = None


def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)


p = ROOT + 'fgo/fgo_export.py'
s = open(p).read()
rep('''  P.batch.f64   whole-flight batch solution, if any: (k, t, p xyz, R row-major 9)
''', '''  P.batch.f64   whole-flight batch solution, if any: (k, t, p xyz, R row-major 9)
  P.yawgate.f64 §9.4 yaw-cap gate checks, if given: (t, k, trace of the predicted attitude cov, fired)
''')
rep('''def write(prefix, info, raw_ev, ev, flow_om, fwd_gz, kf_rows, batch_rows=None):''',
    '''def write(prefix, info, raw_ev, ev, flow_om, fwd_gz, kf_rows, batch_rows=None, yawgate=None):''')
rep('''    if batch_rows is not None:
        np.asarray(batch_rows, np.float64).reshape(-1, 14).tofile(prefix + ".batch.f64")
''', '''    if batch_rows is not None:
        np.asarray(batch_rows, np.float64).reshape(-1, 14).tofile(prefix + ".batch.f64")
    if yawgate is not None:
        np.asarray(yawgate, np.float64).reshape(-1, 4).tofile(prefix + ".yawgate.f64")
''')
open(p, 'w').write(s)

p = ROOT + 'fgo/fgo_replay.py'
s = open(p).read()
i = s.index('    fgo_export.write(DUMP, {"trial": TRIAL, "mode": "corridor"')
j = s.index('\n', s.index('_dump_kf', i))
seg = s[i:j]
assert seg.rstrip().endswith(')'), seg[-200:]
seg2 = seg.rstrip()[:-1] + ', yawgate=fgo.yawgate_log)'
s = s[:i] + seg2 + s[j:]
rep('''print(f"[timing] per-keyframe update: median={np.median(step_ms):.1f}ms  p99={np.percentile(step_ms,99):.1f}ms  "
      f"(deployability budget 33ms)")''', '''print(f"[timing] per-keyframe update: median={np.median(step_ms):.1f}ms  p99={np.percentile(step_ms,99):.1f}ms  "
      f"(deployability budget 33ms)")
print(f"[yaw-cap gate] fired {fgo.n_yaw_fire}/{fgo.n_yaw_check} checks (trace(P_att) > {_fc.ATT_VAR_GATE}, "
      f"every {_fc.YAW_DT} s; FGO_DESIGN §9.4)")''')
open(p, 'w').write(s)

p = ROOT + 'fgo/room_fgo_replay.py'
s = open(p).read()
rep('''                     _raw_ev, ev, _dump_flow_om, {}, _dump_kf, _batch_rows if (DO_BATCH and anchored) else None)''',
    '''                     _raw_ev, ev, _dump_flow_om, {}, _dump_kf, _batch_rows if (DO_BATCH and anchored) else None,
                     yawgate=fgo.yawgate_log)''')
rep('''print(json.dumps(stats))''', '''print(json.dumps(stats))
print(f"[yaw-cap gate] fired {fgo.n_yaw_fire}/{fgo.n_yaw_check} checks (before the anchor; FGO_DESIGN §9.4)")''')
open(p, 'w').write(s)
print("done")
