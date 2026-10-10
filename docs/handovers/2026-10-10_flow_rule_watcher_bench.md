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

(Results follow below; this section was committed before any p1c data were read.)

## 1. Task A result: r_min = 0.85, N_min = 20 (PRE-REGISTERED, pending user confirmation)

Written into `docs/real_flights_plan.md` §7.1 (rule, data, criterion, table, implementation spec) and §7.1a (D22
check). Commits: criterion `b9706ce` (before data) → r_min `eaa2011` → D22 check `31e05e7` (after r_min was fixed).

- **N_min today:** 20 (`min_valid_features`). In all six p1c bags the published `valid` flag equals
  `feature_count >= 20` exactly (0 mismatches). `feature_count` is the post-RANSAC inlier count.
- **Calibration (28,347 pooled airborne textured-floor frames valid today):** kept fraction 99.89% at 0.80,
  **99.11% at 0.85**, 94.57% at 0.90. So r_min = 0.85. Per flight, 98.94–99.26% are kept.
- **Blank floor:** essentially no change. Only 16 of about 28,400 airborne blank-floor frames are valid under
  today's count rule, and the new rule rejects all 16.
- **Climb:** 39 of the 177 climb frames valid today are rejected.
- **Truth residual (diagnostic):** the rule removes 19 of the 23 gross-error frames (> 0.5 rad/s), at a cost of
  about 0.9% of good textured frames.
- **Implementation (specified, not done):**
  - `flow_tracker.py`: a new parameter `min_inlier_ratio` 0.85, and `valid = count >= 20 and ratio >= 0.85`; a
    RANSAC-no-mask frame (with ≥ 4 points) is published INVALID; the thresholds go into `metadata.yaml`.
  - `flow_bridge.py`: unchanged. It already drops `!valid` and sends quality = ratio·255, which is ≥ 217 when valid.
  - EKF3 and the `~/ardupilot_ukf` UKF port both gate only on quality > 0 (`AP_NavEKF3_Measurements.cpp:203`,
    `AP_NavUKF.cpp:589`).
  - The Pi UKF/FGO consume `msg.valid`.
  - So there is one flag, from one source. The simulation pipeline is unchanged.
  - A stage-0 real-camera check is pre-registered: if fewer than 99% of the frames are kept, STOP, with no silent
    re-tune.

## 2. D22 check (after r_min): the rule is NOT a sufficient fix on its own

- **The METHODOLOGY bin means are inflated by an INVALID frame.** The "mean flow_x −1.37 / −2.27" values include
  an invalid lift-off frame (count 3, flow_x −22.9 / −22.6 rad/s) that no estimator uses. METHODOLOGY is NOT edited;
  this is flagged here for the user.
- **Lift-off (z 0.29–0.37 m):** the rule rejects all 5 spurious valid frames in the UKF flight (inlier 0.53–0.71).
  In the FGO flight it rejects 2 of 6 (−4.35 and −2.22 rad/s); 4 are kept (−1.29…−0.43, inlier 0.92–1.00).
- **Climb (z ~1.07–1.6 m), both flights:** a plateau of valid flow_x +0.65 → +0.24…0.35 rad/s, with inlier
  0.86–1.00, against a truth prediction of about 0…+0.17 rad/s.
  - It starts with zero roll rate and zero GT lateral velocity.
  - Roll and GT east velocity follow 0.1–0.3 s later.
  - The rule keeps 12/12 (UKF) and 11/14 (FGO) of these frames.
  - Both the timing and the direction point to this plateau, not the lift-off frames, as the driver of the B4
    bursts. Flow_x > 0 reads as a westward drift, so the correction is east, as observed; the FGO flight's lift-off
    frames were negative and would have pushed it west. That is unconfirmed: no replay was run, and the lateral
    sign is only weakly identified from p1c.
- **Not pre-registered, candidates for a user ruling (§7.1a):**
  - flow from the fitted similarity transform at the principal point (not the median displacement);
  - a fitted-scale check;
  - a climb-rate gate;
  - N consecutive valid frames after a re-detection.
  - The hypothesised mechanism (expansion during a fast climb acting on an off-centre feature set, which RANSAC's
    similarity model fits) is NOT verified: no images were inspected.

## 3. Task B result: bench tests B0–B10 (PRE-REGISTERED, pending user confirmation)

These are in `docs/real_flights_plan.md` §7.2, with stage 0 (§9.4) and §7 cross-referenced.
- **The tests:**
  - B0: control;
  - B1: no watcher → no arming, including the FC side (B1c);
  - B2: watcher killed (both layers, and the FC layer alone);
  - B3: link cut or watcher hung;
  - B4: hand-carried box breach, tilt, and a 2 m clearance check;
  - B5: mocap stopped or occluded;
  - B6: wrong rigid body;
  - B7: latency and clocks;
  - B8: estimator invalid:
    - EKF3 report-only, as in SITL;
    - the UKF port with ALL aiding killed (flow, tag and heading bridges), within 5.5 s of the last `OF`/`VISP` row
      received;
    - the FGO within 0.75 s;
    - the killed processes are kept out of the watcher's list, and the watcher's heartbeat stays up, so the watcher
      does not disarm first;
    - a fixed fallback if `HORIZ_POS_REL` is absent while landed: bench → hand-held ≥ 0.6 m (armed, props off) →
      first tethered hover;
  - B9: dependency loss, land/stop/SIGSTOP;
  - B10: RC override precedence, and RC failsafe.
- **Gaps that are not implemented for hardware (G1–G11):**
  - no mocap input;
  - no stale-pose check;
  - no rigid-body ID check;
  - a breach kills processes instead of sending a MAVLink LAND;
  - no watcher MAVLink heartbeat and no `FS_GCS_*` / `MAV_GCS_SYSID` setup;
  - the FC arms without a watcher, because the GCS failsafe is bypassed if the GCS was never seen;
  - `pgrep` liveness is local-only and blind to a hung process;
  - `--dep-loss stop` has no hardware meaning;
  - the heartbeat is a local file;
  - `--box` has no height limit;
  - heartbeat masking: any system ID-255 heartbeat (MAVProxy/pymavlink default) refreshes the GCS timer unless the
    watcher has its own ID.
- **Source facts checked:**
  - `FS_GCS_ENABLE` 5 = Land, `FS_GCS_TIMEOUT` (default 5, range 2–120), `FS_OPTIONS` bit 4 default (continue in
    pilot modes);
  - `failsafe_gcs_check` returns early if the GCS was never seen;
  - `should_disarm_on_failsafe` disarms when landed;
  - `failsafe_ekf_event` takes no action in non-position modes unless `FS_EKF_ACTION` is 3;
  - `thesis_nav_check` needs a relative position since arming.

## 4. Housekeeping
- **Scratch:** the decompressed bags were deleted after each extraction (the script removes its scratch dir). The
  compact npz extracts and scripts are in the session scratchpad (`flow/`); the npz files were deleted at the end.
  No original was touched.
- **Not edited:** METHODOLOGY, numbers.md, and all estimator and tracker code. No flights, no replays, no heavy jobs.
- **Next stage (for a fresh agent):**
  - the user confirms or rules on §7.1 and §7.2, and on the D22 candidates;
  - then implement G1–G11 and the tracker rule on a real-flight branch.
