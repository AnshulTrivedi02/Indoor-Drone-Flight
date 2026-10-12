"""F8 investigation: dump the dataflash messages needed for the EKF3 ground-runaway analysis to a pickle.

Read-only on the data. Usage (in ~/venv-ardupilot):
    python dump_df.py <log.BIN> <out.pkl>
"""
import collections
import pickle
import sys

from pymavlink import DFReader

WANT = set("XKF1 XKF2 XKF3 XKF4 XKF5 XKFS XKT XKV1 XKV2 OF RFND IMU MODE EV MSG ERR ARM ORGN XKFD "
           "ATT RCOU CTUN PARM VIBE XKFM".split())


def main(f, out):
    r = DFReader.DFReader_binary(f, zero_time_base=True)
    d = collections.defaultdict(list)
    while True:
        m = r.recv_match()
        if m is None:
            break
        t = m.get_type()
        if t not in WANT:
            continue
        d[t].append(m.to_dict())
    pickle.dump(dict(d), open(out, "wb"))
    print({k: len(v) for k, v in d.items()})


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
