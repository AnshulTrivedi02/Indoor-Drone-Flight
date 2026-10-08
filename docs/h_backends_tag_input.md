# Experiment H, stages S2/S3: the AprilTag-fix input for the closed-loop UKF and FGO backends

**Status:** coding and offline equivalence only (no simulator run). Written 2026-10-08 for the S2 (UKF flies) and S3
(FGO flies) stages of experiment H, which fly 19–23 Oct (METHODOLOGY "Experiment H: pre-registration";
`docs/tag_hold_design.md` §a and §R).

**Section order is the order of work.** §1 (the pre-registered bands) was committed **before** any comparison was run.
Its commit SHA is the proof of order. §2 onwards (what changed, results) was added afterwards.

## 1. PRE-REGISTRATION: equivalence bands (written before any comparison is run)

### 1.0 Common basis

- **Flight:** `H_s1_r1`. EKF3 flew on the wall tag. `LOG_REPLAY 1`, 8,670 `REPH` = 8,670 `VISP` = 8,670 `/tags/sent`,
  `VISO_DELAY_MS 31`, `VISO_POS_M_NSE 0.02`, `VISO_POS_{X,Y,Z}` all 0. The IMU-gap rule is `ok`.
- **Offline references:**
  - UKF: `src/estimators/room_ukf_replay.py H_s1_r1` with `ROOM_TAG_SIGMA_POS=0.02`. The stored output is
    `H_s1_r1/room_ukf/` (t_anchor 49.138 s, 8,670 fixes fused, 27 pseudo-yaw fusions before the anchor).
  - FGO: `src/estimators/fgo/room_fgo_replay.py H_s1_r1 --no-batch` with `ROOM_TAG_SIGMA_POS=0.02`, the live
    track. The stored output is `H_s1_r1/room_fgo/` (t_anchor 49.138 s, 8,584 tag factors, 0 keyframe failures).
  - Before either reference is used, a fresh run into scratch must reproduce the stored live track **byte for byte**,
    single-threaded (`OMP/OPENBLAS/MKL_NUM_THREADS=1`). If it does not, stop and report. The stored trial outputs
    are never written.
- **Why the bands are tighter than the corridor E1 band (0.05 m):** the H quantities interpreted are cm-scale (EKF3
  hold error 8 mm; UKF/FGO hover-loss drifts 14–292 mm). The tag-aided regime is bounded, so round-off is not
  amplified. These are the C++ FGO port's bands (|Δp| ≤ 1 mm, |Δyaw| ≤ 0.01°), which apply to aided bags.

### 1.1 UKF port, tier A: the algorithm on the identical event stream (PASS/FAIL)

**Test.**
- `eval/ukf_tag_event_export.py` runs the **unmodified** `room_ukf_replay.py` (runpy). It wraps `ukf_core`
  (`init_state`, `predict`, `predict_rts`, `update_range`, `update_flow`, `update_yaw_pseudo`, `update_tag`) and
  `measurement_models.reanchor_jacobian`, and records every call's inputs and the Python state after it.
- Everything is converted to NED/FRD. The re-anchor conversion is self-checked on random states against the Python
  `reanchor_jacobian`.
- The trial directory is redirected to scratch (symlinks to `bag/` and `imu_gaps.json`), so `H_s1_r1/room_ukf/` is
  never written. The wrapped run's `ukf_live.tum` must be byte-identical to the stored one.
- `~/ardupilot_ukf` `examples/UKF_Equiv` drives the port's own `predict` / `update_scalar` / `yaw_pseudo` and the new
  `tag_reanchor` / `tag_update` through that sequence.
- Compared per event over the **whole replay** (initialisation to the end), and reported per predict step.

**Bands (all must hold):**

| # | metric | band |
|---|---|---|
| UA1 | 3-D position difference, every event | **max ≤ 1 mm** |
| UA2 | yaw difference, every event | **max ≤ 0.01°** |
| UA3 | gyro-z bias (rate form); accelerometer bias | **\|Δ\| ≤ 0.1 deg/min; ≤ 0.001 m/s²** (E4) |
| UA4 | gate decisions (flow X/Y, range, pseudo-yaw firings) | **≥ 99.9% identical**; accepted counts within 0.1% (E5) |
| UA5 | tag handling | the re-anchor is at the same event (the first tag event), and the state right after it agrees to **≤ 1e-9** (m, rad); **every** tag event is fused on both sides (8,670, no gate); **0** pseudo-yaw fusions after the anchor on both sides |

A failure is a porting bug: find it, fix it, report each fix, re-run. The bands are not changed.

### 1.2 UKF port, tier B: the ArduPilot input path (Replay of `H_s1_r1/ardupilot.bin`)

**Configuration:** `UKF_EXTPOS=1 UKF_EXTYAW=1` (as `h_extnav.parm` will set `AHRS_UKF_EXTPOS 1`, `AHRS_UKF_EXTYAW 1`),
on the Replay-only input dump.

**Checks (PASS/FAIL; D17 V1's R1–R3 template):**
- **UB1 (same input):**
  - every replayed `REPH` reaches `NavUKF::writeExtNavData`;
  - the accepted fixes are exactly those EKF3's acceptance rule keeps (20 ms rate limit, initialised), applied to
    `REPH`;
  - each accepted fix has event time = max(TS − D − 6, arrival − 60) exactly;
  - its N, E = `REPH` PX, PY exactly; R_pos = constrain(PEr, 0.01, 10)²;
  - its yaw = the quaternion's 321 yaw (≤ 1e-6 rad); R_yaw = max(AEr, 5°, 0.05)².
- **UB2 (queue):** every accepted fix is processed exactly once, in time order, at a horizon ≥ its event time;
  `EvO` = 0.
- **UB3 (anchor):**
  - the re-anchor happens at the first processed fix;
  - the state after it equals the fix (N, E, yaw to float precision);
  - **0** pseudo-yaw fusions after it.
- **UB4 (no gate):** every processed fix after the anchor is fused (processed = accepted).

**Quantified difference from the offline UKF (the input-path cost):**
- Measured on the horizon state (the Replay CSV, 25 Hz), mapped to the bag clock by the `/imu/time_ref` lower
  envelope (as `eval/h_score.py`), against `room_ukf/ukf_live.tum` interpolated.
- **UB5 (band, tag visible):** in "tag-visible" time, the horizontal difference must have p95 ≤ 0.02 m (σ_pos) and
  max ≤ 0.05 m, and the yaw difference p95 ≤ 1.0° and max ≤ 2.0° (D17 R5's bands).
  - "Tag-visible" = a `/tags/sent` fix within the previous 0.2 s, excluding the first 2 s after the anchor and after
    each re-acquisition.
  - Basis: with 30 Hz fixes at σ 0.02 m, both filters are pinned to the same fixes. The input-path differences
    (step 3: IMU path, flow gyro, timing) act on dead-reckoning, which the fixes bound within a few fix periods.
- **Reported, no band:** the difference during each loss and at its end, and the per-fix offset of the port's event
  time from the fix's capture stamp (clock-mapped).
- **UB6 (PREDICTION for S2, not an equivalence criterion; reported either way):** the Replay port's own drift
  against GT at the end of each loss is within the P-H5 UKF bands: ≤ 0.10 / 0.20 / 0.40 m (hover 5 / 15 / 30 s) and
  ≤ 0.30 m (during the move). Both the as-worded (at OCCLUDER OFF) and effective (first fix after the gap) values
  are reported.

**Structural differences, stated beforehand (quantified in §4):**
1. **IMU:** the port predicts on DAL INS deltas accumulated to EKF3's 12 ms target (~12.5 ms). The offline replay
   uses dejittered 333 Hz samples at 15 ms steps.
2. **Fix timing:** the port fuses each fix at max(TS − 31 − 6, arrival − 60) on EKF3's delayed horizon. TS is the
   capture time after MAVLink's offboard-timestamp correction. The offline replay fuses at the capture stamp.
3. **Flow:** the port uses EKF3's flow timing rule (D5 buffer) and the AHRS-paired gyro; the offline replay uses
   capture stamps and the frame-averaged IMU gyro.
4. **Pre-anchor yaw frame:** the port starts at NED yaw 0 (facing W north, the tag); the offline replay starts at ENU
   yaw 0 (NED 90°). The re-anchor sets the yaw to the fix either way. The rotation it applies to velocity and its
   covariance therefore differs (by 90° at the anchor), which slightly changes the post-anchor velocity variance.
5. **Range:** the port samples the cm-quantised rangefinder at ≥ 33 ms; the offline replay uses the bag's float ranges.

### 1.3 FGO node: the node core on the offline stream (PASS/FAIL)

**Test.** `eval/fgo_node_equiv.py H_s1_r1 --mode step2 --tags` drives `FgoNodeCore(tags=True)` with
`room_fgo_replay.py`'s own event stream. That stream has the same bag reading (including `/tags/sent`), IMU-gap rule,
whole-flight dejitter and stable stamp sort, with dejitter "none" and gap "off". It is compared with the reproduced
`room_fgo/fgo_live.tum` (keyframes at or after the anchor), with both written through `room_fgo_replay.py`'s TUM writer.

**Bands (all must hold; FE1–FE4's bit-level template):**

| # | metric | band |
|---|---|---|
| FN1 | 3-D position difference per keyframe | **max ≤ 1e-6 m** (the `%.6f` print rounding) |
| FN2 | yaw difference per keyframe (same writer) | **max ≤ 1e-6°** |
| FN3 | structure | the same keyframe count and times; t_anchor = 49.138 s on both; tag factors equal (8,584); flow and range factor counts equal; 0 keyframe failures |

### 1.4 FGO node: causal inputs (band as FG1, plus a report)

The node on its causal inputs (variant i+ii+iii of FGO step 3: causal dejitter, arrival order through the horizon
queue, causal IMU-gap detection), with `/tags/sent` in arrival order. Compared against the offline live track at the
offline keyframe times (interpolated), in the W frame with no alignment.

- **FN4 (band; FG1's (b) bands, the position band tightened to the tag scale):**
  - in tag-visible time (as UB5): horizontal difference p95 ≤ 0.02 m, max ≤ 0.15 m (FG1(a)'s ±0.15 m);
  - yaw difference p95 ≤ 0.2°, max ≤ 0.5° (FG1(b));
  - the re-anchor uses the same fix (t_anchor 49.138 s);
  - tag factors within 1% of 8,584.
- **Reported, no band:** the difference in each loss; the keyframe step time before the anchor (with the gate-only
  covariance recursion on, as the offline replay) and after it, against the 33 ms keyframe budget.

### 1.5 Regression (PASS/FAIL): the new code is off by default

- **UR1:** with `AHRS_UKF_EXTPOS 0`, the port behaves as before on the D17 path. Two checks:
  - the D17 V1 Replay of `cl_bcpp_tex_r1` (`UKF_EXTYAW=1`) with the new Replay binary gives a `ukf_shadow.csv` and
    `ukf_inputs.csv` byte-identical to those of the `ukf-port` Replay binary (`1acfca00`, built 30 Sep 22:22, md5
    `77b35d5f…`, copied aside before any build);
  - the new `UKF_Equiv` on a step-2 `dsn_tex_r2` event file (re-exported by `eval/ukf_event_export.py`) gives a state
    file byte-identical to that of the 30 Sep `UKF_Equiv` binary (md5 `cd16858b…`, the step-2 harness).
- **FR1:** `FgoNodeCore` with `tags=False` reproduces FGO step 2 on `dsn_tex_r1` (FE1–FE4 as registered).
