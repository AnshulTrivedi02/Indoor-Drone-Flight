#!/usr/bin/env bash
# p1c_img CALIBRATION flights (ruling 2026-10-10; docs/p1c_img_calibration_spec.md, signed off). NEVER datasets.
# Open loop on simulator truth (run_trial defaults), downward images recorded, profile batches/p1c_img/profile.json
# (take-off climb, hover with two 2.0<->3.5 m climb cycles, 90 m cruise at 0.5 m/s, hover, land). One per argument:
#   tex | trans | blank   ->  p1c_img_{tex,trans,blank} on corridor_{textured,transition,blank}
set -u; cd "$(dirname "$0")/.."; source tools/flight_lock.sh
P="$PWD/batches/p1c_img/profile.json"
for t in "$@"; do
  case "$t" in tex) w=corridor_textured;; trans) w=corridor_transition;; blank) w=corridor_blank;; *) echo "bad arg $t"; exit 2;; esac
  name="p1c_img_$t"
  [ -e "$HOME/thesis_data/trials/$name" ] && { echo "$name exists; stopping"; exit 1; }
  flight_lock_acquire "$name" 7200 || { echo "no flight lock; stopping"; exit 1; }
  HPROFILE="$P" EXTRA_RECORD_TOPICS="/downward_camera/image /downward_camera/camera_info" \
    ./run_trial.sh --world "$w" --velocity 0.5 --altitude 2.0 --duration 180 --trial-name "$name"
  rc=$?
  flight_lock_release
  grep -q "HPROFILE: 11 segments" "$HOME/thesis_data/trials/$name/logs/fly_trial.log" 2>/dev/null \
    || { echo "p1cimg: $name did NOT fly the profile (pass-through failed); stopping"; exit 1; }
  [ "$rc" = 0 ] || { echo "p1cimg: $name run_trial rc=$rc; stopping"; exit 1; }
  echo "p1cimg: $name flown"
done
