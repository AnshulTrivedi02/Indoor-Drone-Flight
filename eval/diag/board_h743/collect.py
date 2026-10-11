#!/usr/bin/env python3
"""board-h743 (2a): collect the text results (no binaries) into thesis_ws eval/results/board_h743/."""
import glob, json, os, shutil, subprocess
S = '/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/h7'
R = '/home/makerspace/thesis_ws/.claude/worktrees/agent-ad2bca097d9980188/eval/results/board_h743'
os.makedirs(R, exist_ok=True)

def su(d, n):
    rows = []
    for f in glob.glob(f'{S}/{d}/*.su'):
        for line in open(f):
            loc, sz, kind = line.rstrip('\n').split('\t')
            rows.append((int(sz), loc.replace('../../libraries/', '')))
    return [f'{a:6d}  {b}' for a, b in sorted(rows, reverse=True)[:n]]

with open(f'{R}/stack_usage.txt', 'w') as f:
    f.write('# -fstack-usage frames (bytes) of the thesis sources compiled with the board flags (stack_usage.py)\n')
    f.write('# BEFORE the static-scratch change (MatekH743 flags):\n' + '\n'.join(su('su_before', 15)) + '\n\n')
    f.write('# AFTER (board-h743 6280a35745), MatekH743 flags:\n' + '\n'.join(su('su_after', 15)) + '\n\n')
    f.write('# AFTER, Pixhawk6X flags:\n' + '\n'.join(su('su_px6', 10)) + '\n')

summary = {}
for d in ('MatekH743_with', 'MatekH743_without', 'Pixhawk6X_with', 'Pixhawk6X_without', 'MatekH743_with_6280a357', 'Pixhawk6X_with_6280a357'):
    o = f'{S}/out/{d}'
    if not os.path.isdir(o):
        continue
    a = glob.glob(o + '/*.apj')
    j = json.load(open(a[0])) if a else {}
    sec = {}
    for line in open(o + '/size_A.txt'):
        p = line.split()
        if len(p) >= 2 and p[0].startswith('.') and p[1].isdigit():
            sec[p[0]] = int(p[1])
    md5 = subprocess.run(['md5sum'] + a, capture_output=True, text=True).stdout.split()[0] if a else None
    summary[d] = {k: j.get(k) for k in ('board_id', 'image_size', 'flash_total', 'flash_free', 'git_identity')}
    summary[d].update({'apj_md5': md5, 'text': sec.get('.text'), 'data': sec.get('.data'), 'bss': sec.get('.bss'),
                       'heap_ram0': sec.get('.heap'), 'pstack': sec.get('.pstack'),
                       'n_warnings': int(open(o + '/n_warnings.txt').read().strip() or 0)})
    for f in ('waf_size_table.txt', 'hwdef.h'):
        if os.path.exists(f'{o}/{f}'):
            shutil.copy(f'{o}/{f}', f'{R}/{d}_{f}')
    for script, args, name in (('analyse_elf.py', [o], 'thesis_symbols'), ('map_by_lib.py', [o, '80'], 'flash_by_library')):
        r = subprocess.run(['python3', f'{S}/{script}'] + args, capture_output=True, text=True)
        open(f'{R}/{d}_{name}.txt', 'w').write(r.stdout + r.stderr)
for b in ('MatekH743', 'Pixhawk6X'):
    if f'{b}_with' in summary and f'{b}_without' in summary:
        r = subprocess.run(['python3', f'{S}/analyse_elf.py', f'{S}/out/{b}_with', f'{S}/out/{b}_without'], capture_output=True, text=True)
        open(f'{R}/{b}_with_minus_without.txt', 'w').write(r.stdout[r.stdout.find('== with - without'):])
        w, wo = summary[f'{b}_with'], summary[f'{b}_without']
        summary[f'{b}_delta'] = {'image_size': w['image_size'] - wo['image_size'], 'bss': w['bss'] - wo['bss']}
json.dump(summary, open(f'{R}/sizes.json', 'w'), indent=1)
print(json.dumps(summary, indent=1))
