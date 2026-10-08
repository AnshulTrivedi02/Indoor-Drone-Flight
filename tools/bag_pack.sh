#!/usr/bin/env bash
# Lossless file-level compression of a trial's rosbag2 file (ruling 2026-10-08; docs/disk_report_2026-10-08.md).
#   pack <trial_dir>   : bag/<name>.db3 (the bag's single db3; bag_0.db3 or bag.db3) -> .db3.zst (zstd -9). Verified by decompressing to a pipe and comparing
#                        the sha256 with the original's; ONLY THEN is bag_0.db3 removed. Writes bag/PACKED.txt
#                        (original sha256 and size). Idempotent: a trial already packed is skipped.
#   unpack <trial_dir> : restores bag/bag_0.db3 from the .zst and checks the sha256 against PACKED.txt. The .zst is
#                        kept; `pack` afterwards only re-verifies and removes the db3 again.
# A packed bag cannot be read by rosbags/ros2 until unpacked (about 6 s per 3 GB bag).
set -euo pipefail
cmd=$1; d=${2%/}; b="$d/bag"; man="$b/PACKED.txt"
n_db=$(ls "$b"/*.db3 2>/dev/null | wc -l); [ "$n_db" -le 1 ] || { echo "ERROR $n_db .db3 files in $b" >&2; exit 2; }
if [ "$n_db" -eq 1 ]; then db=$(ls "$b"/*.db3); else z0=$(ls "$b"/*.db3.zst 2>/dev/null | head -1); db=${z0%.zst}; [ -n "$z0" ] || db="$b/bag_0.db3"; fi
z="$db.zst"
case "$cmd" in
  pack)
    if [ ! -f "$db" ] && [ -f "$z" ] && [ -f "$man" ]; then echo "SKIP already packed: $d"; exit 0; fi
    [ -f "$db" ] || { echo "ERROR no $db" >&2; exit 2; }
    sha=$(sha256sum "$db" | cut -d' ' -f1); size=$(stat -c %s "$db")
    if [ ! -f "$z" ]; then zstd -q -9 -T4 "$db" -o "$z.tmp" && mv "$z.tmp" "$z"; fi
    sha2=$(zstd -q -dc "$z" | sha256sum | cut -d' ' -f1)
    if [ "$sha" != "$sha2" ]; then echo "ERROR sha mismatch $d ($sha vs $sha2); original kept" >&2; rm -f "$z"; exit 3; fi
    printf "sha256 %s\nsize %s\npacked %s\nzst_size %s\n" "$sha" "$size" "$(date -Is)" "$(stat -c %s "$z")" > "$man"
    rm -f "$db"; echo "PACKED $d $size -> $(stat -c %s "$z")";;
  unpack)
    [ -f "$db" ] && { echo "SKIP not packed: $d"; exit 0; }
    zstd -q -d "$z" -o "$db.tmp"; sha=$(sha256sum "$db.tmp" | cut -d' ' -f1); want=$(awk '/^sha256/{print $2}' "$man")
    [ "$sha" = "$want" ] || { rm -f "$db.tmp"; echo "ERROR unpack sha mismatch $d" >&2; exit 3; }
    mv "$db.tmp" "$db"; echo "UNPACKED $d";;
  *) echo "usage: $0 pack|unpack <trial_dir>" >&2; exit 1;;
esac
