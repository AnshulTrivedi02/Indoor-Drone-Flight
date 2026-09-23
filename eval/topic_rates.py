#!/usr/bin/env python3
"""Per-topic message counts and mean sim-time rates for trial bags.

The bags are recorded with sim-time receive stamps (their starting_time is sim
seconds), so count / bag duration is a sim-time rate. That is the rate that matters
here, not the wall-clock `ros2 topic hz` (CLAUDE.md, RTF note).

Usage (any python with PyYAML): python3 eval/topic_rates.py TRIAL [TRIAL...]
"""
import os, sys
import yaml

TRIALS_DIR = os.path.expanduser("~/thesis_data/trials")


def rates(trial):
    m = yaml.safe_load(open(f"{TRIALS_DIR}/{trial}/bag/metadata.yaml"))["rosbag2_bagfile_information"]
    dur = m["duration"]["nanoseconds"] / 1e9
    return dur, {t["topic_metadata"]["name"]: (t["message_count"], t["message_count"] / dur)
                 for t in m["topics_with_message_count"]}


if __name__ == "__main__":
    res = {t: rates(t) for t in sys.argv[1:]}
    topics = sorted({k for _, r in res.values() for k in r})
    print(f"{'topic':30}" + "".join(f"{t:>18}" for t in res))
    print(f"{'bag duration (sim s)':30}" + "".join(f"{d:18.1f}" for d, _ in res.values()))
    for k in topics:
        print(f"{k:30}" + "".join(
            f"{r[k][1]:12.2f} Hz   " if k in r else f"{'—':>18}" for _, r in res.values()))
