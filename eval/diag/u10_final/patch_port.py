#!/usr/bin/env python3
"""U10 rule 2 (2026-10-12): in Replay, the UKF's five dataflash records get distinct names (RUKF/RUKO/RUKS/RUKH/RUKT),
so a Replay of a FORK-flown log (which copies the onboard XUK* through) cannot interleave the two. The flying port's
names (XUK*) are unchanged. Applied once to the scratch worktree; asserts every substitution happens exactly once."""
import sys

p = sys.argv[1] + "/libraries/AP_NavUKF/AP_NavUKF.cpp"
s = open(p).read()
anchor = "#define D(n, d) (double(n) / double(d))\n"
assert s.count(anchor) == 1
macro = anchor + """
// Dataflash record names (thesis fork, 2026-10-12, U10 rule 2). The flying port logs XUKF/XUKO/XUKS/XUKH/XUKT. Replay
// logs the SAME records as RUKF/RUKO/RUKS/RUKH/RUKT: a Replay of a fork-flown log copies the onboard XUK* records
// through, and under one name the onboard and the replayed series interleaved and could not be told apart (EKF3 solves
// the same problem with its core field, C = 100 + core in Replay; the UKF records have no such field, and adding one
// would change the flying port's log format). Fields, units and values are unchanged; only the name differs.
#if APM_BUILD_TYPE(APM_BUILD_Replay)
#define UKF_LOG_NAME(s) "R" s
#else
#define UKF_LOG_NAME(s) "X" s
#endif
"""
s = s.replace(anchor, macro)
for n in ("UKH", "UKT", "UKF", "UKO", "UKS"):
    old = f'WriteStreaming("X{n}",'
    assert s.count(old) == 1, (n, s.count(old))
    s = s.replace(old, f'WriteStreaming(UKF_LOG_NAME("{n}"),')
assert 'WriteStreaming("X' not in s
open(p, "w").write(s)
print("patched", p)
