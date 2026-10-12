#!/bin/bash
# Rebase board-h743 and u4-gndclr onto f30f6ffa2f (ukf-jitter-fix) in temporary worktrees; board-h743 also gets the
# write_end_stats() AP_NAVUKF_REPLAY_IO_ENABLED fix-up commit. Refuses to start while a flight runs.
set -u
REPO=/home/makerspace/ardupilot_ukf
S=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/g5a
BASE=f30f6ffa2f
[ -e /home/makerspace/thesis_data/FLIGHT_LOCK ] && { echo "FLIGHT_LOCK present: not rebasing"; exit 3; }
pgrep -x arducopter > /dev/null && { echo "arducopter running: not rebasing"; exit 3; }
[ "$(git -C $REPO rev-parse ukf-jitter-fix)" = "$(git -C $REPO rev-parse $BASE)" ] || { echo "ukf-jitter-fix moved"; exit 2; }
for B in board-h743 u4-gndclr; do
  WT=$S/rb_$B
  git -C $REPO worktree add -q $WT $B || { echo "worktree add $B failed"; exit 2; }
  if git -C $WT rebase -q $BASE; then echo "REBASED $B -> $(git -C $WT rev-parse --short=10 HEAD)";
  else echo "CONFLICT $B"; git -C $WT status --short | head; git -C $WT rebase --abort; git -C $REPO worktree remove --force $WT; exit 1; fi
done
# board-h743 fix-up: write_end_stats() is Replay-only file I/O (no stdio on a board build)
F=$S/rb_board-h743/libraries/AP_NavUKF/AP_NavUKF.cpp
python3 - "$F" <<'EOF'
import sys
p = sys.argv[1]; t = open(p).read()
old = """void NavUKF::write_end_stats(const char *path) const
{
    FILE *f = fopen(path, "w");
    if (f != nullptr) {
        fprintf(f, "name,value\\nn_chol_retry,%u\\nn_chol_fail,%u\\n", (unsigned)_n_chol_retry, (unsigned)_n_chol_fail);
        fclose(f);
    }
}"""
new = """void NavUKF::write_end_stats(const char *path) const
{
#if AP_NAVUKF_REPLAY_IO_ENABLED
    FILE *f = fopen(path, "w");
    if (f != nullptr) {
        fprintf(f, "name,value\\nn_chol_retry,%u\\nn_chol_fail,%u\\n", (unsigned)_n_chol_retry, (unsigned)_n_chol_fail);
        fclose(f);
    }
#else
    (void)path;     // board-h743: Replay-only file I/O is not linked into flight code
#endif
}"""
assert t.count(old) == 1, "write_end_stats body not found exactly once"
open(p, "w").write(t.replace(old, new))
EOF
git -C $S/rb_board-h743 commit -q -am "board-h743 (2026-10-12, after the rebase onto f30f6ffa2f): write_end_stats() inside AP_NAVUKF_REPLAY_IO_ENABLED (Replay-only file I/O; SITL unchanged)" \
  && echo "FIXUP board-h743 -> $(git -C $S/rb_board-h743 rev-parse --short=10 HEAD)"
for B in board-h743 u4-gndclr; do
  git -C $S/rb_$B status --short | head -3
  git -C $REPO worktree remove $S/rb_$B && echo "removed rb_$B"
done
git -C $REPO worktree prune; git -C $REPO worktree list
git -C $REPO log --oneline $BASE..board-h743; git -C $REPO log --oneline $BASE..u4-gndclr
echo REBASE_DONE
