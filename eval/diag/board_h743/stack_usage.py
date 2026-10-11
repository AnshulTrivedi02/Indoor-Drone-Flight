#!/usr/bin/env python3
"""board-h743: recompile the thesis estimator sources for a board with -fstack-usage (output to scratch, the build tree
is not touched) and print every function's frame, largest first.  stack_usage.py <board> <outdir>"""
import json, os, shlex, subprocess, sys
W = '/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/aph7'
board, out = sys.argv[1], os.path.abspath(sys.argv[2])
os.makedirs(out, exist_ok=True)
env = dict(os.environ, PATH='/opt/gcc-arm-none-eabi-10-2020-q4-major/bin:' + os.environ['PATH'])
cc = json.load(open(f'{W}/build/{board}/compile_commands.json'))
want = ('AP_NavUKF/AP_NavUKF.cpp', 'AP_NavUKF/AP_NavFGO.cpp', 'AP_AHRS/AP_AHRS_UKF.cpp', 'AP_AHRS/AP_AHRS_FGO.cpp',
        'AP_AHRS/AP_AHRS.cpp')
rows = []
for e in cc:
    f = e['file']
    if not f.endswith(want):
        continue
    args = e.get('arguments') or shlex.split(e['command'])
    obj = os.path.join(out, os.path.basename(f) + '.o')
    args = [a for a in args if not a.startswith('-o')] + ['-o', obj]
    args = [a for a in args if not a.startswith('-Werror=frame-larger-than')] + ['-fstack-usage', '-Wno-error']
    r = subprocess.run(args, cwd=e['directory'], env=env, capture_output=True, text=True)
    if r.returncode:
        print('COMPILE FAILED', f, r.stderr[-2000:]); continue
    su = obj[:-2] + '.su'
    for line in open(su):
        loc, n, kind = line.rstrip('\n').split('\t')
        rows.append((int(n), kind, os.path.basename(f), loc.split(':')[-1]))
rows.sort(reverse=True)
for n, kind, f, fn in rows[:40]:
    print(f'{n:6d} {kind:8s} {f:20s} {fn}')
