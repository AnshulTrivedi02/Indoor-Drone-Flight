#!/usr/bin/env python3
"""Dump raw flow_y from a trial bag — no filtering, no trimming."""
import sys
import statistics
from pathlib import Path
from rosbag2_py import SequentialReader, StorageOptions, ConverterOptions
from rclpy.serialization import deserialize_message
from optical_flow_interfaces.msg import OpticalFlow

bag = Path(sys.argv[1]) if len(sys.argv) > 1 else \
    Path.home() / "thesis_data/trials/sweep_v1p0/bag"

reader = SequentialReader()
reader.open(
    StorageOptions(uri=str(bag), storage_id="sqlite3"),
    ConverterOptions(input_serialization_format="cdr",
                     output_serialization_format="cdr"),
)

flow_y_vals = []
n = 0
while reader.has_next():
    topic, data, t = reader.read_next()
    if topic != "/optical_flow/measurement":
        continue
    msg = deserialize_message(data, OpticalFlow)
    n += 1
    flow_y_vals.append(msg.flow_y)
    # Print every message so you can see the whole trajectory
    print(f"{n:4d}  flow_y={msg.flow_y:+8.2f}  "
          f"feat={msg.feature_count:3d}  "
          f"inlier={msg.inlier_ratio:.2f}  valid={msg.valid}")

print("\n── Summary ──")
print(f"Total messages:      {len(flow_y_vals)}")
if flow_y_vals:
    print(f"Median flow_y:       {statistics.median(flow_y_vals):+.2f}")
    print(f"Median |flow_y|:     {statistics.median(abs(v) for v in flow_y_vals):+.2f}")
    print(f"Min / Max flow_y:    {min(flow_y_vals):+.2f} / {max(flow_y_vals):+.2f}")
    # How many are near zero (the smoking gun for stationary frames)
    near_zero = sum(1 for v in flow_y_vals if abs(v) < 50)
    print(f"Frames |flow_y|<50:  {near_zero}  ({near_zero/len(flow_y_vals)*100:.0f}%)")