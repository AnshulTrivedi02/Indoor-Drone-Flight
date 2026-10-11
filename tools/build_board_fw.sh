#!/bin/bash
# build_board_fw.sh: one-command board build of the thesis fork (ArduCopter + the UKF/FGO backends) for a named hwdef.
#
#   tools/build_board_fw.sh <BOARD> [--without] [--dry-run] [--out DIR] [--ref REF] [--extra-hwdef FILE] [--no-lock-check]
#
# Rung-1 stock image (the pinned commit, UNMODIFIED source): tools/build_board_fw.sh <BOARD> --ref 7bac20cbcc --without
# (the fork repository contains that upstream commit; a detached worktree of it is a clean checkout).
# What it does (2026-10-12; keeps the board firmware READY for the exact board, METHODOLOGY ruling 2026-10-12):
#   1. checks the arguments, the toolchain and that <BOARD>'s hwdef exists ON THE REF (default: board-h743 of
#      ~/ardupilot_ukf) and is an STM32H7 (warns for anything but STM32H743xx);
#   2. creates a TEMPORARY detached git worktree of that commit (the branch itself is never checked out or changed),
#      initialises the submodules a ChibiOS build needs by --reference to the main checkout (no network);
#   3. ./waf configure --board <BOARD> --enable-THESIS_NAVUKF (or without the option, --without); ./waf copter;
#   4. copies the .apj / .hex / .bin / ELF / hwdef.h / build logs out to DIR (default
#      ~/thesis_data/fw_builds/<BOARD>_<with|without>_<commit8>_<date>), and writes DIR/summary.json:
#        - flash: image_size, flash_total and flash_free from the .apj header; PASS needs flash_free >= 32768 B;
#        - warnings: PASS needs 0 compiler warnings;
#        - backends: PASS needs the NavUKF/NavFGO symbols present (with) or absent (--without);
#        - stack: the build's -Werror=frame-larger-than limit (any larger frame already failed the build), the main
#          thread's HAL_PROCESS_STACK_SIZE from hwdef.h, and the thesis sources recompiled with -fstack-usage
#          (frames, largest first). PASS needs the largest frame <= the limit and a CONSERVATIVE chain bound (the
#          sum of the 6 largest thesis frames) <= half the main stack. The real margin is bench check P7;
#   5. removes the worktree (trap on EXIT: remove --force --force, rm -rf, prune) and checks that the ref did not move
#      and that the fork's worktree list is back to what it was.
#
# NOTHING IS EVER FLASHED. Exit status: 0 = built and every check PASSED; 1 = a check FAILED (artefacts kept);
# 2 = usage / validation error (nothing created); 3 = build error; 4 = cleanup/integrity error.
#
# A real (non --dry-run) build is heavy: run it under the lock protocol, one at a time, e.g.
#   python3 ~/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py "board fw KakuteH7" -- tools/build_board_fw.sh KakuteH7
# The script refuses a real build if ~/thesis_data/FLIGHT_LOCK exists, or if it is not running under the heavy.py
# that holds ~/thesis_data/BUILD_LOCK (override: --no-lock-check). --dry-run needs no lock: it validates, creates
# and lists the worktree, prints the commands it would run, and cleans up.
#
# The vehicle binary name is never written on a command line here (globs only), so a pgrep for the SITL vehicle does
# not mistake this script for a flight. Only waf's own link step names it, for a few seconds.
set -u -o pipefail

REPO="${BFW_REPO:-$HOME/ardupilot_ukf}"
REF="board-h743"
TOOLCHAIN="${BFW_TOOLCHAIN:-/opt/gcc-arm-none-eabi-10-2020-q4-major/bin}"
LOCK_DIR="$HOME/thesis_data"
MIN_FREE=32768
SUBMODULES=(modules/waf modules/mavlink modules/ChibiOS modules/DroneCAN/DSDL modules/DroneCAN/dronecan_dsdlc
            modules/DroneCAN/libcanard modules/DroneCAN/pydronecan modules/littlefs modules/lwip modules/CrashDebug)
NESTED=(modules/mavlink:pymavlink modules/CrashDebug:CrashCatcher modules/CrashDebug:mri)
THESIS_SRC=(AP_NavUKF/AP_NavUKF.cpp AP_NavUKF/AP_NavFGO.cpp AP_AHRS/AP_AHRS_UKF.cpp AP_AHRS/AP_AHRS_FGO.cpp
            AP_AHRS/AP_AHRS.cpp)

usage() { sed -n '2,4p' "$0" | sed 's/^# \{0,1\}//' >&2; exit 2; }
die() { echo "build_board_fw: ERROR: $1" >&2; exit "${2:-2}"; }
log() { echo "build_board_fw: $*"; }

# ---------------------------------------------------------------- arguments
BOARD=""; WITH=1; DRY=0; OUT=""; LOCKCHECK=1; XHW=""
while [ $# -gt 0 ]; do
  case "$1" in
    --without) WITH=0 ;;
    --dry-run) DRY=1 ;;
    --out) [ $# -ge 2 ] || usage; OUT="$2"; shift ;;
    --ref) [ $# -ge 2 ] || usage; REF="$2"; shift ;;
    --no-lock-check) LOCKCHECK=0 ;;
    --extra-hwdef) [ $# -ge 2 ] || usage; XHW=$(realpath -e "$2") || die "extra hwdef '$2' not found"; shift ;;
    -h|--help) usage ;;
    -*) echo "build_board_fw: unknown option $1" >&2; usage ;;
    *) [ -z "$BOARD" ] || die "only one board may be named (got '$BOARD' and '$1')"; BOARD="$1" ;;
  esac
  shift
done
[ -n "$BOARD" ] || { echo "build_board_fw: no board named" >&2; usage; }
[[ "$BOARD" =~ ^[A-Za-z0-9][A-Za-z0-9_.+-]*$ ]] || die "board name '$BOARD' has characters a hwdef directory never has"
VARIANT=$([ $WITH = 1 ] && echo with || echo without)

# ---------------------------------------------------------------- validation (nothing is created before this passes)
[ -d "$REPO/.git" ] || die "$REPO is not a git checkout"
SHA0=$(git -C "$REPO" rev-parse --verify --quiet "$REF^{commit}") || die "ref '$REF' not found in $REPO"
HW="libraries/AP_HAL_ChibiOS/hwdef"
git -C "$REPO" cat-file -e "$SHA0:$HW/$BOARD/hwdef.dat" 2>/dev/null \
  || die "no hwdef '$BOARD' on $REF ($SHA0): see $HW/ (names are case-sensitive)"

# Resolve the MCU through the hwdef's include chain (e.g. KakuteH7v2 -> KakuteH7-bdshot -> KakuteH7), on the ref.
resolve_mcu() {   # $1 = repo path of a hwdef file
  local f="$1" depth="${2:-0}" line inc dir
  [ "$depth" -lt 6 ] || return 1
  line=$(git -C "$REPO" show "$SHA0:$f" 2>/dev/null | grep -m1 -E '^MCU ' || true)
  if [ -n "$line" ]; then echo "$line"; return 0; fi
  dir=$(dirname "$f")
  for inc in $(git -C "$REPO" show "$SHA0:$f" 2>/dev/null | awk '$1=="include"{print $2}'); do
    resolve_mcu "$(python3 -c 'import os, sys; print(os.path.normpath(sys.argv[1]))' "$dir/$inc")" $((depth + 1)) \
      && return 0
  done
  return 1
}
MCU_LINE=$(resolve_mcu "$HW/$BOARD/hwdef.dat") || die "could not find the MCU line of '$BOARD' (include chain)"
MCU=$(echo "$MCU_LINE" | awk '{print $3}')
case "$MCU" in
  STM32H743xx) ;;
  STM32H7*) log "WARNING: $BOARD is $MCU, not STM32H743xx (the class the plan assumes); building anyway" ;;
  *) die "$BOARD is $MCU, not an STM32H7: this script only builds the H7 targets of the plan" ;;
esac
[ -x "$TOOLCHAIN/arm-none-eabi-gcc" ] || die "toolchain not found at $TOOLCHAIN (BFW_TOOLCHAIN overrides)"
for m in "${SUBMODULES[@]}"; do
  [ -e "$REPO/$m/.git" ] || die "submodule $m is not initialised in $REPO (needed as a --reference)"
done
for pc in "${NESTED[@]}"; do
  [ -e "$REPO/${pc%%:*}/${pc#*:}/.git" ] || die "nested submodule ${pc/:/\/} is not initialised in $REPO"
done

if [ $DRY = 0 ]; then
  [ ! -e "$LOCK_DIR/FLIGHT_LOCK" ] || die "FLIGHT_LOCK present: no heavy job during a flight"
  if [ $LOCKCHECK = 1 ]; then
    [ -f "$LOCK_DIR/BUILD_LOCK" ] || die "no BUILD_LOCK: run a real build under heavy.py (or pass --no-lock-check)"
    LPID=$(grep -o -E 'pid [0-9]+' "$LOCK_DIR/BUILD_LOCK" | awk '{print $2}')
    p=$$; ok=0
    while [ -n "$p" ] && [ "$p" -gt 1 ]; do
      [ "$p" = "$LPID" ] && { ok=1; break; }
      p=$(awk '{print $4}' "/proc/$p/stat" 2>/dev/null || true)
    done
    [ $ok = 1 ] || die "BUILD_LOCK is held by pid $LPID, which is not this script's heavy.py: refusing"
  fi
fi

STAMP=$(date +%Y%m%d_%H%M%S)
[ -n "$OUT" ] || OUT="$HOME/thesis_data/fw_builds/${BOARD}_${VARIANT}_${SHA0:0:8}_${STAMP}"
WT_BEFORE=$(git -C "$REPO" worktree list --porcelain | grep -c '^worktree ')
WT=$(mktemp -d "${TMPDIR:-/tmp}/bfw_${BOARD}_XXXXXX") || die "mktemp failed"

log "board $BOARD ($MCU), $VARIANT the backends; ref $REF = $SHA0"
log "temporary worktree $WT; output $OUT; dry-run=$DRY"

# ---------------------------------------------------------------- cleanup (always)
cleanup() {
  local rc=$? bad=0
  if [ -n "${WT:-}" ]; then
    git -C "$REPO" worktree remove --force --force "$WT" >/dev/null 2>&1 || true
    rm -rf "$WT"
    git -C "$REPO" worktree prune
    if [ -e "$WT" ]; then echo "build_board_fw: CLEANUP ERROR: $WT still exists" >&2; bad=1; fi
    local after; after=$(git -C "$REPO" worktree list --porcelain | grep -c '^worktree ')
    if [ "$after" != "$WT_BEFORE" ]; then
      echo "build_board_fw: CLEANUP ERROR: $REPO lists $after worktrees, $WT_BEFORE before" >&2; bad=1
    fi
    if git -C "$REPO" worktree list --porcelain | grep -q "^worktree $WT\$"; then bad=1; fi
    local sha1; sha1=$(git -C "$REPO" rev-parse "$REF^{commit}" 2>/dev/null || echo gone)
    if [ "$sha1" != "$SHA0" ]; then echo "build_board_fw: INTEGRITY ERROR: $REF moved ($SHA0 -> $sha1)" >&2; bad=1; fi
    [ $bad = 0 ] && echo "build_board_fw: cleanup OK (worktree removed, $WT_BEFORE worktrees listed, $REF unchanged)"
  fi
  [ $bad = 0 ] || exit 4
  exit $rc
}
trap cleanup EXIT
trap 'exit 130' INT TERM

# ---------------------------------------------------------------- worktree + submodules
git -C "$REPO" worktree add --detach "$WT" "$SHA0" >/dev/null 2>&1 || die "git worktree add failed" 3
[ "$(git -C "$WT" rev-parse HEAD)" = "$SHA0" ] || die "worktree HEAD is not $SHA0" 3
[ -f "$WT/$HW/$BOARD/hwdef.dat" ] || die "hwdef missing in the worktree" 3
log "worktree created at $(git -C "$WT" rev-parse --short=10 HEAD) ($(git -C "$WT" log -1 --format=%s | cut -c1-70))"
git -C "$REPO" worktree list

OPT=""; [ $WITH = 1 ] && OPT="--enable-THESIS_NAVUKF"
[ -n "$XHW" ] && OPT="$OPT --extra-hwdef=$XHW"   # e.g. define ALLOW_ARM_NO_COMPASS (UNTESTED path, see the plan)
if [ $DRY = 1 ]; then
  log "DRY RUN: would init ${#SUBMODULES[@]} submodules by --reference, then run in $WT:"
  echo "    ./waf configure --board $BOARD --no-submodule-update $OPT"
  echo "    ./waf copter"
  echo "    and write $OUT/{*.apj,*.hex,vehicle.elf,hwdef.h,summary.json}"
  exit 0
fi

for m in "${SUBMODULES[@]}"; do
  timeout 900 git -C "$WT" submodule update --init --reference "$REPO/$m" "$m" >/dev/null 2>&1 \
    || die "submodule $m failed to initialise" 3
done
for pc in "${NESTED[@]}"; do   # nested submodules (mavgen needs pymavlink's C headers)
  p=${pc%%:*}; c=${pc#*:}
  timeout 900 git -C "$WT/$p" submodule update --init --reference "$REPO/$p/$c" "$c" >/dev/null 2>&1 \
    || die "nested submodule $p/$c failed to initialise" 3
done
log "submodules initialised (by reference)"

mkdir -p "$OUT" || die "cannot create $OUT" 3
export PATH="$TOOLCHAIN:$PATH"
( cd "$WT" && ./waf configure --board "$BOARD" --no-submodule-update $OPT ) > "$OUT/configure.log" 2>&1 \
  || { tail -20 "$OUT/configure.log" >&2; die "waf configure failed (see $OUT/configure.log)" 3; }
( cd "$WT" && ./waf copter ) > "$OUT/build.log" 2>&1 \
  || { grep -m20 -E 'error|Error' "$OUT/build.log" >&2; die "waf copter failed (see $OUT/build.log)" 3; }
log "build finished"

BD="$WT/build/$BOARD"
cp "$BD"/bin/*.apj "$BD"/bin/*.hex "$OUT"/ 2>/dev/null || true
cp "$BD"/bin/*.bin "$OUT"/ 2>/dev/null || true
ELF=$(ls "$BD"/bin/* | grep -v -E '\.(apj|hex|bin|abin)$' | head -1)
[ -n "$ELF" ] && cat < "$ELF" > "$OUT/vehicle.elf"   # a redirect, so no process argv names the vehicle binary
cp "$BD/hwdef.h" "$BD/compile_commands.json" "$OUT/" 2>/dev/null || true
"$TOOLCHAIN/arm-none-eabi-size" -A "$OUT/vehicle.elf" > "$OUT/size_A.txt"
"$TOOLCHAIN/arm-none-eabi-nm" -C --size-sort -S "$OUT/vehicle.elf" > "$OUT/nm.txt"
grep -A12 -E "Target +Text" "$OUT/build.log" > "$OUT/waf_size_table.txt" || true

# ---------------------------------------------------------------- stack: -fstack-usage of the thesis sources
python3 - "$BD/compile_commands.json" "$OUT/stack" "$TOOLCHAIN" "${THESIS_SRC[@]}" > "$OUT/stack_usage.txt" 2>&1 <<'EOF'
import json, os, shlex, subprocess, sys
cc_path, out, tc, want = sys.argv[1], sys.argv[2], sys.argv[3], tuple(sys.argv[4:])
os.makedirs(out, exist_ok=True)
env = dict(os.environ, PATH=tc + ':' + os.environ['PATH'])
rows, limit = [], None
for e in json.load(open(cc_path)):
    f = e['file']
    if not f.endswith(want):
        continue
    args = e.get('arguments') or shlex.split(e['command'])
    for a in args:
        if 'frame-larger-than=' in a:
            limit = int(a.split('=')[-1])
    obj = os.path.join(out, os.path.basename(f) + '.o')
    # waf writes the output joined ('-o<path>'); a separate '-o <path>' is handled too. (Fixed 2026-10-12 after
    # the KakuteH7 test build kept waf's '-o<path>' and failed with "too many filenames".)
    if '-o' in args:
        i = args.index('-o'); args = args[:i] + args[i + 2:]
    args = [a for a in args if not a.startswith('-o')]
    args = [a for a in args if 'frame-larger-than' not in a] + ['-fstack-usage', '-Wno-error', '-o', obj]
    r = subprocess.run(args, cwd=e['directory'], env=env, capture_output=True, text=True)
    if r.returncode:
        print('COMPILE FAILED', f, r.stderr[-1500:]); continue
    for line in open(obj[:-2] + '.su'):
        loc, n, kind = line.rstrip('\n').split('\t')
        rows.append((int(n), kind, os.path.basename(f), loc.split(':')[-1]))
rows.sort(reverse=True)
thesis = [r for r in rows if r[2] != 'AP_AHRS.cpp' or 'UKF' in r[3] or 'FGO' in r[3]]
print(f'LIMIT {limit}')
print(f'MAXFRAME {thesis[0][0] if thesis else -1}')
print(f'CHAIN6 {sum(r[0] for r in thesis[:6])}')
for n, kind, f, fn in rows[:30]:
    print(f'{n:6d} {kind:8s} {f:20s} {fn}')
EOF

# ---------------------------------------------------------------- summary and checks
python3 - "$OUT" "$BOARD" "$VARIANT" "$SHA0" "$MCU" "$MIN_FREE" <<'EOF'
import glob, json, re, sys
out, board, variant, sha, mcu, min_free = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], int(sys.argv[6])
apj = glob.glob(out + '/*.apj')
j = json.load(open(apj[0])) if apj else {}
hdr = {k: j.get(k) for k in ('board_id', 'image_size', 'flash_total', 'flash_free', 'git_identity', 'image_maxsize')}
warn = [l for l in open(out + '/build.log') if 'warning:' in l]
nm = open(out + '/nm.txt').read()
has_ukf, has_fgo = 'NavUKF::' in nm, 'NavFGO::' in nm
hw = open(out + '/hwdef.h').read() if glob.glob(out + '/hwdef.h') else ''
m = re.search(r'#define HAL_PROCESS_STACK_SIZE\s+(0x[0-9A-Fa-f]+|\d+)', hw)
pstack = int(m.group(1), 0) if m else None
st = dict(re.findall(r'^(LIMIT|MAXFRAME|CHAIN6) (-?\d+|None)$', open(out + '/stack_usage.txt').read(), re.M))
limit = int(st['LIMIT']) if st.get('LIMIT', 'None') != 'None' else None
maxf, chain = int(st.get('MAXFRAME', -1)), int(st.get('CHAIN6', -1))
sec = {}
for line in open(out + '/size_A.txt'):
    p = line.split()
    if len(p) >= 2 and p[0].startswith('.') and p[1].isdigit():
        sec[p[0]] = int(p[1])
checks = {
    'flash_free_ge_32k': hdr['flash_free'] is not None and hdr['flash_free'] >= min_free,
    'zero_warnings': len(warn) == 0,
    'backends_as_requested': (has_ukf and has_fgo) if variant == 'with' else (not has_ukf and not has_fgo),
    'identity_matches_ref': (hdr['git_identity'] or 'x') == sha[:8],
}
if variant == 'with':   # without the option the thesis sources compile to nothing: no frames to check
    checks['max_thesis_frame_le_limit'] = limit is not None and 0 <= maxf <= limit
    checks['conservative_chain_le_half_main_stack'] = pstack is not None and maxf > 0 and 0 < chain <= pstack // 2
s = {'board': board, 'mcu': mcu, 'variant': variant, 'ref_commit': sha, 'apj': hdr,
     'apj_file': [a.split('/')[-1] for a in apj], 'n_warnings': len(warn),
     'symbols': {'NavUKF': has_ukf, 'NavFGO': has_fgo},
     'sections': {k: sec.get(k) for k in ('.text', '.data', '.bss', '.heap', '.pstack')},
     'stack': {'frame_limit_B': limit, 'main_stack_B': pstack, 'largest_thesis_frame_B': maxf,
               'conservative_chain_6_largest_B': chain,
               'note': 'chain bound = sum of the 6 largest thesis frames (an upper bound, not a call chain); '
                       'the real margin is bench check P7 (@SYS/threads.txt)'},
     'checks': checks, 'pass': all(checks.values()), 'flashed': False}
json.dump(s, open(out + '/summary.json', 'w'), indent=1)
print(json.dumps(s, indent=1))
sys.exit(0 if s['pass'] else 1)
EOF
RC=$?
md5sum "$OUT"/*.apj
if [ $RC = 0 ]; then log "PASS: $OUT/summary.json"; else log "A CHECK FAILED: see $OUT/summary.json"; fi
exit $RC
