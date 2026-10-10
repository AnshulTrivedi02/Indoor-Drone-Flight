# Handover, 2026-10-10: flow-validity rule (D22 fix) calibrated on p1c_*; mocap watcher bench tests

**Stage:** light analysis and documentation only. No replays, no flights, no estimator or tracker code changes,
METHODOLOGY and numbers.md NOT edited.

## 0. Calibration criterion, written down BEFORE any p1c number was read

Written at the start of the stage, before the p1c bags were decompressed or read.

- **Rule form (as ruled):** `valid = (feature_count >= N_min) AND (inlier_ratio >= r_min)`, one flag computed in
  `flow_tracker.py`, consumed by EKF3 (via `flow_bridge.py`), the UKF and the FGO.
- **N_min:** kept at today's value, 20 (`min_valid_features`, `flow_tracker.py:27/313`). Only r_min is calibrated.
  (`feature_count` is the post-RANSAC inlier count, since `tracked_count` is overwritten by the RANSAC survivors.)
- **Data:** the six simulation calibration flights only: `p1c_fwdc_{tex,trans,blank}`,
  `p1c_fwdplainc_{tex,trans,blank}` (not `p1c_fwdplainc_blank_ABORTED`; no dataset bag).
- **Population ("textured-floor frames"):** `/optical_flow/measurement` messages that are valid under today's rule
  (feature_count ≥ 20), taken while airborne (ground-truth z ≥ 0.30 m, i.e. > 0.1 m above the 0.195 m rest height),
  over a textured floor: the whole flight on the two `_tex` worlds, and ground-truth y < 78 m (2 m short of the 80 m
  boundary) on the two `_trans` worlds. GT is matched to each flow stamp by linear interpolation.
- **Criterion:** r_min = the LARGEST value on a 0.05 grid such that ≥ 99% of the pooled textured-floor frames
  (all four textured-floor sources together) satisfy `inlier_ratio >= r_min`. The per-flight kept fractions are
  reported alongside; they do not move the choice.
- **Reported, NOT used for the choice:**
  - the reject rate on the blank floor (currently valid airborne frames on the `_blank` worlds and on y > 82 m of the
    `_trans` worlds that the new rule would reject);
  - the per-flight kept fraction on the textured floor;
  - a truth-residual diagnostic (flow minus a truth-implied flow fitted on the textured frames) for accepted vs
    rejected frames;
  - what the rule would have done to the two D22 episodes (`cl_ukf_b_tex_r3_half`, `cl_fgo_b_tex_r3_half_v3`), looked
    at only AFTER r_min was fixed.

(Results follow below.)
