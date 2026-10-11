#!/bin/bash
# Prints the header (not the image) of the published STABLE Copter .apj for each likely H743 target
# (2026-10-12: git_identity dbe79216). Downloads go to a temporary directory, never into the repository.
D=$(mktemp -d); trap 'rm -rf "$D"' EXIT; cd "$D" || exit 1
for b in CubeOrange CubeOrangePlus Pixhawk6X Pixhawk6C Durandal MatekH743 MatekH743-bdshot KakuteH7v2 KakuteH7Mini KakuteH7-bdshot MambaH743v4 FlywooH743Pro TBS_LUCID_H7 MicoAir743 JHEMCU-H743HD FoxeerH743v1 AEROFOX-H7; do
  [ -f "$b.apj" ] || timeout 60 curl -sSf -o "$b.apj" "https://firmware.ardupilot.org/Copter/stable/$b/arducopter.apj" || echo "MISSING $b"
done
python3 - <<'EOF'
import json, glob
for f in sorted(glob.glob('*.apj')):
    try:
        j = json.load(open(f))
    except Exception as e:
        print(f, 'ERR', e); continue
    print(f"{f[:-4]:20s} {j['description'][-12:]:12s} id={j['board_id']:5d} total={j['flash_total']:9d} "
          f"image={j['image_size']:9d} free={j['flash_free']:8d} ident={j['git_identity']}")
EOF
