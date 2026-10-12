#!/usr/bin/env python3
"""Print the key lines of a check_logs.py JSON."""
import json, sys
d = json.load(open(sys.argv[1]))
x = d["df_reader"]
print({k: x[k] for k in ["undeclared_types", "skipped_bytes", "bad_fmt", "declared_UKF", "counts", "XKF1_per_core",
                         "XUKO_strictly_increasing", "XUKO_dt_ms_median", "XUKO_dt_ms_max"]})
for k in ["pymavlink_fast", "pymavlink_python"]:
    p = d[k]
    print(k, p.get("error"), p.get("XKF1_per_core"), p.get("XUKO"), p.get("XUKO_first_equals_df_reader"))
print(d["time_base"])
if "byte_identity_vs_old" in d:
    b = d["byte_identity_vs_old"]
    print(b["removed_records"], b["structural"])
print("PASS_a", d["PASS_a"])
