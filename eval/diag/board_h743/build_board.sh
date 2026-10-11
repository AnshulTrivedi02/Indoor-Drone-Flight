#!/bin/bash
# board-h743 (2a, 2026-10-11): build Copter for one ChibiOS board, with or without the thesis UKF/FGO backends
# (--enable-THESIS_NAVUKF), and copy the artefacts + size data out of the worktree. One heavy.py step.
#   build_board.sh <board> <with|without>
# Nothing is flashed. Globs are used so that the vehicle binary name never appears on a command line.
set -e
B=$1; V=$2
W=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/aph7
O=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/h7/out/${B}_${V}
export PATH=/opt/gcc-arm-none-eabi-10-2020-q4-major/bin:$PATH
rm -rf $O; mkdir -p $O
cd $W
OPT=""; [ "$V" = with ] && OPT="--enable-THESIS_NAVUKF"
./waf configure --board $B --no-submodule-update $OPT > $O/configure.log 2>&1
./waf copter > $O/build.log 2>&1
BD=build/$B
cp $BD/bin/*.apj $BD/bin/*.hex $O/ 2>/dev/null || true
ls $BD/bin/*.bin >/dev/null 2>&1 && cp $BD/bin/*.bin $O/ || true
ELF=$(ls $BD/bin/* | grep -v -E '\.(apj|hex|bin|abin)$' | head -1)
cp "$ELF" $O/vehicle.elf
cp $BD/hwdef.h $BD/Linker.map $BD/compile_commands.json $O/ 2>/dev/null || true
arm-none-eabi-size -A $O/vehicle.elf > $O/size_A.txt
arm-none-eabi-size $O/vehicle.elf > $O/size.txt
arm-none-eabi-nm -C --size-sort -S $O/vehicle.elf > $O/nm.txt
ls $BD/lib/*.a >/dev/null 2>&1 && arm-none-eabi-size -t $BD/lib/*.a > $O/libsize.txt 2>/dev/null || true
grep -A12 -E "Target +Text" $O/build.log > $O/waf_size_table.txt || true
grep -c "warning:" $O/build.log > $O/n_warnings.txt || true
grep "warning:" $O/build.log | sort | uniq > $O/warnings.txt || true
python3 - "$O" <<'EOF'
import json, glob, sys
o = sys.argv[1]
for a in glob.glob(o + '/*.apj'):
    j = json.load(open(a))
    print(a.split('/')[-1], {k: j.get(k) for k in ('board_id', 'image_size', 'flash_total', 'flash_free', 'git_identity', 'image_maxsize', 'extflash_total', 'extf_image_size')})
EOF
cat $O/waf_size_table.txt
md5sum $O/*.apj
