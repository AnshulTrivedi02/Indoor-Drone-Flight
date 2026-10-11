#!/usr/bin/env python3
"""board-h743 (2a): flash/RAM breakdown of the thesis backends from a build's nm dump (nm -C --size-sort -S).
  analyse_elf.py <out_with> [<out_without>]
Groups code (t/T/W/w) and data (b/B/d/D/r/R) by owner; prints the with-without deltas from size -A and the .apj."""
import json, glob, re, sys, collections

def nm(d):
    rows = []
    for line in open(d + '/nm.txt'):
        p = line.rstrip('\n').split(' ', 3)
        if len(p) < 4:
            continue
        rows.append((int(p[1], 16), p[2], p[3]))
    return rows

def owner(name):
    for k in ('NavUKF', 'NavFGO', 'AP_AHRS_UKF', 'AP_AHRS_FGO', 'thesis_nav_check', 'writeFGOState', 'ukf_'):
        if re.search(r'(^|[^A-Za-z_])' + k, name):
            return k
    return None

def sec_sizes(d):
    s = {}
    for line in open(d + '/size_A.txt'):
        p = line.split()
        if len(p) >= 2 and p[0].startswith('.') and p[1].isdigit():
            s[p[0]] = int(p[1])
    return s

def apj(d):
    a = glob.glob(d + '/*.apj')[0]
    j = json.load(open(a))
    return {k: j[k] for k in ('image_size', 'flash_total', 'flash_free', 'git_identity', 'board_id')}

w = sys.argv[1]
rows = nm(w)
code, data = collections.Counter(), collections.Counter()
big = []
for n, t, name in rows:
    o = owner(name)
    if o is None:
        continue
    (code if t in 'tTWw' else data)[o] += n
    big.append((n, t, name))
print('== thesis symbols in', w)
print('code (B):', dict(code), 'total', sum(code.values()))
print('static data (B):', dict(data), 'total', sum(data.values()))
print('largest thesis symbols:')
for n, t, name in sorted(big, reverse=True)[:25]:
    print(f'  {n:7d} {t} {name[:150]}')
# the AHRS singleton that holds NavUKF/NavFGO as members
for n, t, name in rows:
    if re.fullmatch(r'(copter|ahrs|AP::ahrs\(\)::.*|_singleton|AP_AHRS::_singleton)', name) or name in ('copter',):
        print('  object', n, t, name)
print('apj:', apj(w))
print('sections:', {k: v for k, v in sec_sizes(w).items() if k in ('.text', '.data', '.bss', '.ram0', '.heap', '.ARM.exidx', '.rodata')})
if len(sys.argv) > 2:
    wo = sys.argv[2]
    a, b = apj(w), apj(wo)
    print('== with - without')
    print('image_size delta:', a['image_size'] - b['image_size'], ' flash_free with/without:', a['flash_free'], b['flash_free'])
    sw, so = sec_sizes(w), sec_sizes(wo)
    for k in sorted(set(sw) | set(so)):
        if sw.get(k, 0) != so.get(k, 0):
            print(f'  {k:14s} {so.get(k, 0):9d} -> {sw.get(k, 0):9d}  ({sw.get(k, 0) - so.get(k, 0):+d})')
    dw = {name: n for n, t, name in nm(w)}
    do = {name: n for n, t, name in nm(wo)}
    for key in ('copter', 'AP_AHRS::_singleton'):
        if key in dw or key in do:
            print('  ', key, do.get(key), '->', dw.get(key))
    ch = sorted(((dw.get(k, 0) - do.get(k, 0), k) for k in set(dw) | set(do) if dw.get(k, 0) != do.get(k, 0)),
                key=lambda x: -abs(x[0]))
    print('  largest per-symbol changes:')
    for dlt, k in ch[:20]:
        print(f'    {dlt:+8d} {k[:140]}')
