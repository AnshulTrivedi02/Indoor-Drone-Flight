#!/bin/bash
# Commit the U10 rule-2 port change on replay-rukx (scratch worktree).
set -e
cd /tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/apr
git add libraries/AP_NavUKF/AP_NavUKF.cpp
git commit -q -F - <<'MSG'
U10 rule 2 (2026-10-12): Replay logs the UKF records as RUKF/RUKO/RUKS/RUKH/RUKT

A Replay of a fork-flown log copies the onboard XUK* records through; under one name the onboard and the replayed
series interleaved and could not be told apart. Replay now writes the same records under distinct names (an R prefix;
fields, units and values unchanged). The flying port's names (XUK*) are unchanged: UKF_LOG_NAME() expands to the same
"XUK?" literals outside APM_BUILD_Replay. An instance field (as EKF3's C = 100 + core) was not used: the records have
none, and adding one would change the flying port's log format.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
MSG
git log --oneline -2
