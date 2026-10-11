#!/usr/bin/env python3
"""board-h743 (2a): flash (text+rodata+data init) and RAM (bss/data) per ArduPilot library, from a build's Linker.map
and compile_commands.json.  map_by_lib.py <outdir> [N]
Sizes are the linked (kept, after --gc-sections) input sections, attributed to the object's source directory."""
import json, os, re, sys, collections
d = sys.argv[1]; topn = int(sys.argv[2]) if len(sys.argv) > 2 else 45
obj2lib = {}
for e in json.load(open(d + '/compile_commands.json')):
    args = e.get('arguments') or []
    o = [a[2:] for a in args if a.startswith('-o') and len(a) > 2]
    if not o:
        continue
    f = os.path.normpath(e['file']).replace('../../', '')
    parts = f.split('/')
    lib = parts[1] if parts[0] in ('libraries', 'modules') else parts[0]
    obj2lib[os.path.basename(o[0])] = lib
flash, ram = collections.Counter(), collections.Counter()
lines = open(d + '/Linker.map', errors='replace').read().split('\n')
start = next(i for i, l in enumerate(lines) if l.startswith('Linker script and memory map'))
cur = None
pend = None
for l in lines[start:]:
    m = re.match(r'^ (\.[\w.$-]+)\s*$', l)            # section name alone, details on the next line
    if m:
        pend = m.group(1); continue
    m = re.match(r'^ (\.[\w.$-]+)?\s+0x([0-9a-f]+)\s+0x([0-9a-f]+)\s+(\S.*)$', l)
    if not m:
        pend = None; continue
    sec = m.group(1) or pend; pend = None
    if sec is None:
        continue
    size = int(m.group(3), 16); src = m.group(4)
    if size == 0 or int(m.group(2), 16) == 0:
        continue
    mo = re.search(r'\(([^)]+\.o)\)$', src) or re.search(r'([^/]+\.o)$', src)
    obj = mo.group(1) if mo else src
    lib = obj2lib.get(obj, 'toolchain/other' if ('arm-none-eabi' in src or 'libc' in src or 'libm' in src or 'libgcc' in src) else 'other:' + obj)
    if lib.startswith('other:') and 'ChibiOS' in src:
        lib = 'ChibiOS'
    if sec.startswith(('.text', '.rodata', '.ARM')):
        flash[lib] += size
    elif sec.startswith('.data'):
        flash[lib] += size; ram[lib] += size
    elif sec.startswith(('.bss', 'COMMON')):
        ram[lib] += size
tot = sum(flash.values())
print(f'flash attributed: {tot} B over {len(flash)} groups')
for lib, n in flash.most_common(topn):
    print(f'  {n:8d}  {lib}   (RAM {ram.get(lib, 0)})')
json.dump({'flash': flash, 'ram': ram}, open(d + '/by_lib.json', 'w'), indent=1)
