#!/usr/bin/env python3
"""Peek at a .BIN: selected PARM values and counts of the replay/UKF records."""
import sys
from pymavlink import DFReader
want = {"AHRS_EKF_TYPE", "LOG_REPLAY", "AHRS_UKF_ENABLE", "AHRS_UKF_EXTYAW", "AHRS_UKF_EXTPOS", "FLOW_POS_Z",
        "RNGFND1_POS_Z", "EK3_FLOW_DELAY", "EK3_HGT_DELAY", "FLOW_TYPE"}
for fn in sys.argv[1:]:
    r = DFReader.DFReader_binary(fn)
    p = {}
    cnt = {}
    while True:
        m = r.recv_match(type=["PARM", "ROFH", "XUKF", "XUKO", "RFRH"])
        if m is None:
            break
        t = m.get_type()
        cnt[t] = cnt.get(t, 0) + 1
        if t == "PARM" and m.Name in want:
            p.setdefault(m.Name, []).append(m.Value)
    print(fn, cnt, {k: v for k, v in sorted(p.items())})
