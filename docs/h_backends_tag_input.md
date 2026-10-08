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

---

*(Everything below was written after the pre-registration above was committed at `abdb7b2`.)*

## 2. What changed

### 2.1 UKF port (`~/ardupilot_ukf`, branch `ukf-port-tag` from `ukf-port`, commit `eb86bada`)

**New parameter `AHRS_UKF_EXTPOS`** (0/1, default 0 = unchanged; index 3 in the `AHRS_UKF_` group).

**Input path (EKF3's).**
- `AP_AHRS::writeExtNavData` passes EKF3's full argument set (`pos`, `quat`, `posErr`, `angErr`, `timeStamp_ms`,
  `delay_ms`) to `NavUKF::writeExtNavData`, after `AP_VisualOdom_MAV`'s quality gate and its clamps
  (posErr ≥ `VISO_POS_M_NSE`, angErr ∈ [`VISO_YAW_M_NSE`, 1.5]).
- In Replay, DAL's `REPH` hook now carries the position too. `UKF_EXTPOS=1` forces the parameter.
- `posErr` comes from `ODOMETRY` as `sqrt(cov[0] + cov[6] + cov[11])` (`GCS_Common.cpp`). The tag bridge sets only
  cov[0] = σ_pos², so posErr = σ_pos = 0.02 m.

**With `AHRS_UKF_EXTPOS 1`:**
- **Acceptance and timing, in EKF3's order** (`AP_NavEKF3_Measurements.cpp:1072-1122`):
  - a NaN position is dropped;
  - one `extNavMeasTime_ms` is shared with the yaw: the 20 ms rate limit, and nothing is written until the filter is
    initialised;
  - event time = max(TS − `VISO_DELAY_MS` − 6, arrival − 60), the fusion horizon clamp.
- **One `EV_TAG` event per fix** carries N, E and yaw. It replaces the D17 yaw-only `EV_HDG` path (exclusive), so the
  yaw is never fused twice.
- **Noise:**
  - R_pos = constrain(posErr, 0.01, 10)² per axis (`PosVelFusion.cpp:801`);
  - R_yaw = max(angErr, 5°, 0.05)², as D17.
  - Height is not fused: the rangefinder stays the POSZ source.
- **The T/H rule** (`room_ukf_replay.py`; METHODOLOGY "Experiment T: pre-registration"):
  - **First processed fix: re-anchor** (`tag_reanchor`, `measurement_models.reanchor_jacobian` in NED). Position and
    yaw are set to the fix, and horizontal velocity is rotated by the yaw change. P ← diag(J P Jᵀ), with the N, E and
    yaw variances set to the fix noise and every cross-covariance zeroed.
  - **Later fixes** (`tag_update`, `ukf_core.update_tag`): scalar E, then N, then a yaw update in `update_heading`'s
    form, all with **no innovation gate**.
  - **The yaw pseudo-measurement stops** at the anchor (as EKF3 after ExtNav yaw alignment).
- **Reset reporting (new; needed to fly).** The re-anchor is a position and yaw reset, reported through
  `getLastPosNorthEastReset` / `getLastYawResetAngle` as EKF3's are. The values are the fused-state change, at the
  DAL time of the anchor.
  - **Why:** these are the only reset queries Copter consumes: `AC_PosControl::NE_handle_ekf_reset` and
    `Copter::check_ekf_reset`.
  - **Without them** (the `ukf-port` behaviour: both returned 0), the GUIDED target left by take-off, near W(0, 0) and
    so on the wall, would stay where it was when the estimate jumps about 1.5 m into W at the first fix.
  - **EKF3 avoided this in S1 only because its `ResetPositionNE` is reported.** The UKF now does exactly the same.
- **Logging:**
  - `XUKT`, per processed fix: measurement, state after it, anchor flag, fused count, and the reset (on the anchor
    row);
  - a GCS text "UKF tag re-anchor: dN dE dyaw";
  - Replay-dump rows `T` (accepted fix) and `TP` (processed fix).
- **Not used, and why:** `CorrectExtNavForSensorOffset` (`VISO_POS_{X,Y,Z}` are all 0 in H's PARM dump, and no EKF
  origin is used). The `resetTime_ms` / `reset_counter` path is also unused (the bridge never resets).

### 2.2 FGO backend (`AP_NavFGO`, same commit)

- `GCS_MAVLINK::handle_odometry` now passes `ODOMETRY.reset_counter` to `AP_NavFGO::writeState`.
- A changed counter marks the node's re-anchor. The change of the current-time output across that state (position NE,
  yaw) is reported through the same two AHRS reset queries.
- Logged as `XFGR` and a GCS text "FGO re-anchor: …".

### 2.3 FGO node (`src/estimators/fgo/fgo_node_core.py`, `fgo_node.py`)

**New ROS parameters:**
- `tags` (bool, default false = unchanged);
- `tag_sigma_pos_m` (default 0.02, S0's σ_pos = `VISO_POS_M_NSE`).

**With `tags` true, the node** subscribes to `/tags/sent` (W written as ENU: x = E_W, y = N_W, yaw ENU) and pushes
`("tag", (E, N, yaw))` at the capture stamp.

**The core handles it exactly as `room_fgo_replay.py`:**
- the gate-only covariance recursion (`log_cov`) is on from initialisation until the anchor, and off after it (it
  supplies the re-anchor prior);
- the first fix after initialisation calls `FGO.reanchor` with (σ_pos, 5°), which also turns the yaw cap off;
- later fixes give a tag factor on the next keyframe (the newest fix since the last keyframe), with no gate.

**Output to ArduPilot:**
- **Before the anchor:** the corridor mapping (x forward = N).
- **From the anchor on:** W-as-ENU → NED, i.e. (N, E, D) = (y, x, −z) and yaw_NED = π/2 − yaw_ENU. `reset_counter` is
  incremented, and `AP_NavFGO` reports the reset.
- **Why the pre-anchor mapping is kept:** the FGO starts at yaw 0 along body x, and H spawns facing the tag (W north).
  So the anchor's yaw step is small, as EKF3's is.

**Other details:**
- **`tags` and `heading` are exclusive:** the corridor-frame heading cannot be fused in W. If both are set, the heading
  is disabled, with an error log.
- **New core diagnostics:**
  - `anchor_log` (per keyframe: anchored, re-anchor count);
  - `t_anchor`, `n_anchors`;
  - the stats file also gets `n_tag`.

### 2.4 Tools (thesis_ws)

| file | purpose |
|---|---|
| `eval/ukf_tag_event_export.py` | tier A: exports the unmodified `room_ukf_replay.py` event stream (re-anchor self-check; trial directory redirected; byte-identical live track checked) |
| `eval/ukf_tag_equivalence.py` | tier A: UA1–UA5 |
| `eval/ukf_tag_tierB.py` | tier B: UB1–UB6 from the Replay dump and CSV, the original `REPH`, the bag |
| `eval/fgo_node_tag_equiv.py` | FN1–FN4: offline reference reproduced into scratch; node core on the offline stream and on causal inputs |
| `h_ukf_tag.parm` | `AHRS_UKF_EXTPOS 1`, `AHRS_UKF_EXTYAW 1` for S2. Not yet wired into any launcher |

`~/ardupilot_ukf` `examples/UKF_Equiv`:
- event types 4 (tag fix) and 5 (re-anchor);
- the DIAGNOSTIC option `UKF_EQ_QDIAG` (§3.1).

## 3. Results: UKF port

### 3.1 Tier A (identical event stream): **FAIL as worded** (UA1, UA3, UA5). Cause found: the D27 process-noise form, not the tag code

`eval/results/expH/ukf_tag_tierA_H_s1_r1.json`. The export's wrapped `ukf_live.tum` is **byte-identical** to the
stored one, and the stored `room_ukf/` was untouched (mtimes checked).

| # | band | result as worded |
|---|---|---|
| UA1 | max ≤ 1 mm | **FAIL: 3.6 mm** (rms 0.43 mm; before the anchor 1.6 mm) |
| UA2 | max ≤ 0.01° | PASS: 0.0039° |
| UA3 | gyro-z ≤ 0.1 deg/min; accel ≤ 0.001 m/s² | **FAIL** on accel: 0.0036 m/s² (gyro-z 0.011 deg/min) |
| UA4 | gate decisions | PASS: all identical (flow 11,481/11,548 per axis, range 11,547, pseudo-yaw 27/204) |
| UA5 | anchor, no gate, no pseudo-yaw after it | **FAIL** on "state right after the anchor ≤ 1e-9": 2.7 mm. The non-fix states differ by what had accumulated before. Every other UA5 item PASSES: the anchor is the first tag event on both sides; position and yaw equal the fix exactly; 8,670/8,670 fixes fused on both; 0 pseudo-yaw after the anchor |

**Diagnosis.**
- The first difference above 1e-6 m appears at **event 22, a plain predict at t = 18.70 s**, long before any tag. The
  tag code cannot be the cause.
- **The cause is ruling D27** (2026-10-01). The offline UKF scales EKF3's per-step process noise by DT_REF/dt
  (DT_REF = 12.5 ms), and it fixes Q at the replay's 15.0024 ms step. The port uses EKF3's own per-step form,
  (dt·NSE)², at the step's actual dt.
  - At the port's own steps (12.5 ms, five 2.5 ms frames) the two forms coincide; that was D27's point.
  - The harness, however, feeds the port the offline 15 ms steps, so the port's Q there is 1.2× the offline Q.
- The step-2 harness predates D27, and this is the first harness run since.

**DIAGNOSTIC re-run (post hoc, labelled; the bands are not changed):**
- The harness option `UKF_EQ_QDIAG` replaces, after each predict, the port's per-step Q diagonal with the offline one.
  It is harness only; the port source is unchanged. The offline diagonal is exported by
  `ukf_tag_event_export.py` as `<prefix>.qdiag`.
- Result (`ukf_tag_tierA_H_s1_r1_diagD27q.json`): **every band passes by 4–5 orders of magnitude**:
  - UA1: max **3.2e-8 m**;
  - UA2: 1.7e-7°;
  - UA3: 9.9e-7 deg/min and 8.6e-9 m/s²;
  - UA4: identical;
  - UA5: the anchor state agrees to **2.5e-10**;
  - no difference above 1e-6 anywhere.
- **Reading:** with the same per-step noise, the port's tag code (re-anchor, ungated E/N/yaw updates, pseudo-yaw stop)
  is numerically the offline UKF's. The as-worded failure is the known, ruled D27 noise-form difference at 15 ms
  steps. It does not apply at the port's own 12.5 ms steps.
- **Queued for the user:** whether to accept tier A on this evidence, or re-register UA with the D27 form applied in
  the harness.

### 3.2 Regression UR1: **PASS** (both checks)

- **Replay:** `cl_bcpp_tex_r1`, `UKF_EXTYAW=1`, old Replay (`1acfca00`, md5 `77b35d5f…`) against new. `ukf_shadow.csv`
  (8,680 rows) and `ukf_inputs.csv` (206,963 rows, including 2,385 `H` / 2,385 `HP` heading rows, as D17 V1) are
  **byte-identical**.
- **Harness:** a re-exported `dsn_tex_r2` step-2 stream (45,277 events; the trial directory under a fake HOME, packed
  bag unpacked into scratch). The 30 Sep `UKF_Equiv` and the new one give **byte-identical** state files (md5
  `13f63580…`).

### 3.3 Tier B (Replay of `H_s1_r1/ardupilot.bin`, `UKF_EXTPOS=1 UKF_EXTYAW=1`): **UB1–UB5 PASS; the UB6 prediction holds**

`eval/results/expH/ukf_tag_tierB_H_s1_r1.json`; Replay binary md5 `ea486dea…` (`ukf-port-tag`).

| # | result |
|---|---|
| UB1 | **PASS.** 8,670 `REPH`; EKF3's rule accepts 8,670; the port accepted 8,670. TS and D match 1:1. The event-time rule holds exactly for every fix (**100% clamped** to arrival − 60, see below). Position ≤ 5e-9 m, yaw ≤ 2.7e-9 rad from `REPH`; R_pos and R_yaw ≤ 3e-10 relative |
| UB2 | **PASS.** Each fix processed once, in time order, horizon − event time ≥ 2 ms |
| UB3 | **PASS.** One anchor, at the first processed fix (event 49,110 ms); the state equals the fix exactly; 39 pseudo-yaw fusions before, **0 after**. GCS text: "UKF tag re-anchor: dN −1.48 dE 0.00 dyaw −1.1" |
| UB4 | **PASS.** 8,670 processed = 8,670 fused (no gate) |
| UB5 | **PASS.** Tag-visible (6,934 of 8,760 samples after the anchor): horizontal p50 0.6 mm, **p95 4.1 mm, max 11.2 mm** (band 20 / 50 mm); yaw p95 0.015°, max 0.024° (band 1° / 2°) |

**Structural difference 2, quantified (fix timing).**
- The port's event time minus the fix's capture stamp (bag clock, `/imu/time_ref` envelope map: 161 ppm, +4.3 ms) is
  median **−24.7 ms** (p5 −28.8, p95 −13.7, range −34.4…−8.3).
- **Every fix is clamped to the horizon.** The MAVLink offboard-timestamp correction places TS about 45 ms before
  arrival, so TS − 31 − 6 lands before arrival − 60. The port therefore fuses each fix ~25 ms *before* its capture
  instant.
- **This is EKF3's own rule and timing,** reproduced exactly (UB1). At hover it is negligible; at the 0.2 m/s lateral
  move it is ~5 mm.
- D17 V1 found the same clamping for the heading (`VISO_DELAY_MS` 38).

**Losses (report) and the UB6 prediction (P-H5 UKF bands; drift = |estimate − GT| before the returning fix):**

| loss | port drift as worded / effective | offline UKF drift (effective) | port − offline (effective) | band | UB6 |
|---|---|---|---|---|---|
| hover 5 s | 12 / 6 mm | 32 mm | 36 mm | 100 mm | holds |
| hover 15 s | 7 / 10 mm | 120 mm | 127 mm | 200 mm | holds |
| hover 30 s | 11 / 16 mm | 292 mm | 303 mm | 400 mm | holds |
| move ~7 s | 19 / 13 mm | 40 mm | 52 mm | 300 mm | holds |

**FINDING (Replay; to be confirmed in S2 flight).**
- On ArduPilot's own inputs, the port drifts **6–19 mm** in the tag losses. That is EKF3's scale in S1 (3–31 mm),
  where the offline UKF on the bridged inputs drifted 28–292 mm.
- **The same algorithm** (tier A) on different inputs. So the offline UKF's large hover drift in S1 is an
  **input-path effect**, not the UKF formulation.
  - The offline path: bridged 333 Hz IMU at 15 ms steps, frame-averaged gyro, flow at capture time.
  - The port path: DAL INS deltas at 12.5 ms, EKF3's flow timing and gyro pairing (step 3's three costs).
- This answers in part S1's open question ("EKF3's much smaller hover drift may come partly from … estimator
  differences in the flow model at near-zero speed"): the UKF port, like EKF3, holds.
- Not yet attributed to a single input (step 3's swap-one-input method would do it); the method is noted, not run.

## 4. Results: FGO node

`eval/fgo_node_tag_equiv.py`; `eval/results/expH/fgo_node_tag_equiv_H_s1_r1.json`. Single-threaded BLAS.

**Reference reproduced:** a fresh `room_fgo_replay.py H_s1_r1 --no-batch` (`ROOM_TAG_SIGMA_POS=0.02`) into scratch
gives an `fgo_live.tum` **byte-identical** to the stored one. The stored `room_fgo/` was untouched (mtimes checked).

### 4.1 FN1–FN3 (node core on the offline stream): **PASS**

- The node's anchored keyframes, written through `room_fgo_replay.py`'s writer, give a file **byte-identical** to the
  stored `fgo_live.tum`: 10,515 rows each.
- **FN1:** Δp = 0. **FN2:** Δyaw = 0.
- **FN3:** keyframe times identical; t_anchor 49.138 s on both; tag factors 8,584 = 8,584, flow 11,366 = 11,366,
  range 11,432 = 11,432; 0 keyframe failures on either side.

### 4.2 FN4 (causal inputs: causal dejitter, arrival order, causal gap detection, `/tags/sent` in arrival order): **PASS**

| item | result | band |
|---|---|---|
| anchor | the same fix, t_anchor 49.138 s | same fix |
| tag factors | 8,582 against 8,584 (−0.02%) | within 1% |
| horizontal, tag-visible (8,323 of 10,514 keyframes) | p50 0.3 mm, **p95 2.5 mm, max 12.3 mm** | p95 ≤ 20 mm, max ≤ 150 mm |
| yaw, tag-visible | p50 0.003°, **p95 0.023°, max 0.076°** | p95 ≤ 0.2°, max ≤ 0.5° |

Other results:
- 0 re-initialisations; valid at the end; 0 keyframe failures.
- **Reported (no band):** the whole track after the anchor differs by at most 49 mm horizontally and 0.89° in yaw.
  The yaw maximum falls inside a loss.
- **Just before each returning fix:** 2.3 mm / 0.024° (5 s), 0.8 mm / 0.000° (15 s), 19.6 mm / 0.39° (30 s), and
  16.6 mm / 0.13° (the ~7 s move).

### 4.3 Keyframe step time (DIAGNOSTIC, workstation Python, single-threaded)

| | median | p95 | p99 | max |
|---|---|---|---|---|
| before the anchor (gate-only covariance recursion ON), offline stream | 18.4 ms | 21.2 | 32.4 | 35.4 |
| after the anchor (recursion off, tag factors on), offline stream | 29.8 ms | 33.6 | 37.4 | 70.2 |
| before / after, causal | 18.3 / 30.0 ms | 20.4 / 33.0 | 32.4 / 37.1 | 33.2 / 51.3 |

**Reading:**
- The feared pre-anchor cost (the replay's comment: "~45 ms/keyframe") does **not** appear on this flight. Before the
  anchor the vehicle is mostly on the ground or climbing, so the windows are cheap.
- After the anchor, the median is near the 33 ms keyframe budget, and the p95 is just over it. This is the same scale
  as the corridor FGO's (~29 ms median on textured bags), and the node runs its core in its own process. Any lag shows
  in `XFGO.Age` (§5.2).

### 4.4 Regression FR1: **PASS**

`FgoNodeCore` (new code, `tags` false) on FGO step 2 of `dsn_tex_r1` (`eval/fgo_node_equiv.py --mode step2`; the packed
bag unpacked under a fake HOME into scratch; `eval/results/expH/fgo_node_FR1_dsn_tex_r1.json`):
- FE1: 8.3e-7 m (the reference's `%.6f` rounding);
- FE2: 0;
- FE3: 10,197 keyframes, 10,018 flow, 10,196 range, all identical;
- FE4: 0.

## 5. What the live SITL ground tests must check (to be run later by the main session; not run here)

**Binary.** `~/ardupilot_ukf` branch `ukf-port-tag`, commit `eb86bada`:
- `arducopter` md5 `447f8036…` (version string `eb86bada`);
- Replay md5 `ea486dea…`.

Rebuild if anything is committed later.

### 5.1 S2 ground test (UKF active): `UKF=1`, `h_extnav.parm` + `h_ukf_tag.parm`, `room_wall_tag`

Arm, take off to 1.5 m at the hold point, wait for the fix, hold about 60 s, land. G1–G5 in the D9/D17 style:
- **G1 (configuration, from the PARM dump):**
  - `AHRS_EKF_TYPE 12`, `AHRS_UKF_ENABLE 1`, `AHRS_UKF_EXTPOS 1`, `AHRS_UKF_EXTYAW 1`;
  - `VISO_TYPE 1`, `VISO_POS_M_NSE 0.02`, `VISO_DELAY_MS 31`;
  - `LOG_REPLAY 1`, `LOG_DISARMED 1`.
- **G2 (fix accepted):**
  - `XUKT` row count = the `VISP` count with `Ign` 0, less the fixes before UKF initialisation and those within 20 ms;
  - in practice `XUKT` = `VISP` = `/tags/sent` after the first fix;
  - no fix dropped for NaN.
- **G3 (re-anchor visible):**
  - exactly **one** `XUKT` row with `Anc` = 1, at the first fix;
  - its PN/PE/Yaw equal MN/ME/MY;
  - DN ≈ −1.5 m (the spawn is at W (−1.5, 0)), DY small;
  - the GCS text "UKF tag re-anchor";
  - `XUKS.YF` (pseudo-yaw count) constant from the anchor on.
- **G4 (reset consumed):** a Copter `EKF_YAW_RESET` event at the anchor, and the GUIDED target follows the reset.
  - `wait_fix` completes **within 0.5 m of W (−1.5, 0)**;
  - GT never moves towards the wall by more than 0.2 m at the anchor;
  - the minimum wall clearance stays ≥ 0.5 m (the S1 G5 watcher must be running: `--box=…`).
- **G5 (no gate):** after the anchor, every `XUKT` row fuses (`NF` increments by one per row); `XUKO.EvO` = 0.
- **G6 (estimate):**
  - in the hold, `XUKO` horizontal against GT (in W) mean ≤ 0.05 m;
  - yaw against GT p95 ≤ 1°.

Also re-run tier B (`eval/ukf_tag_tierB.py`) on the ground test's own log (Replay with `UKF_EXTPOS=1`), as D17 V2 did.

### 5.2 S3 ground test (FGO active): `FGO=1`, node with `-p tags:=true -p tag_sigma_pos_m:=0.02`, `room_wall_tag`

**Same profile, with these checks:**
- **G1 (configuration):**
  - `AHRS_EKF_TYPE 13`, `AHRS_FGO_ENABLE 1`;
  - the node's parameters logged `tags` true and heading false;
  - the D25 clock-map settle as before.
- **G2:** the node's stats file has `t_anchor` = the first `/tags/sent` stamp after the node's initialisation;
  `n_tag` ≈ the fixes after the anchor (the newest per keyframe: ~99% of fixes, cf. 8,584/8,669 offline).
- **G3 (re-anchor visible):**
  - exactly one `XFGR` row (RC 1);
  - DN ≈ −1.5 m, DY small;
  - the GCS text "FGO re-anchor";
  - `XFGI` PN/PE in W from then on, with NED yaw ≈ 0 when facing the tag.
- **G4:** as the UKF's G4 (the reset is consumed, `wait_fix` completes near W (−1.5, 0), wall clearance).
- **G5:** D25 C1–C3 and FG2/FG3b as before. Also check `XFGO.OV` = 1 through the anchor: the output must not go
  invalid at the frame change.
- **Timing check:** keyframe step time **before** the anchor, with the gate-only covariance recursion on (§4): compare
  `XFGO.Age` against the 250 ms validity budget over the pre-anchor period.

## 6. Open issues and process notes

1. **Tier A (UKF) FAILS as worded.** The diagnosis (§3.1) points to the D27 per-step Q form in the harness, and with
   the offline Q every band passes by 4–5 orders of magnitude. The ruling is the user's: accept on this evidence, or
   re-register UA with the D27 form in the harness.
2. **The UKF/FGO re-anchor is now reported as a reset.** Before this change both backends returned "no reset". With the
   ~1.5 m anchor step at the first fix, a GUIDED target near the wall would have stayed where take-off left it. The
   reset path is coded and builds, but has **not been exercised live**; it is S2/S3 ground-test G4.
3. **The port fuses each tag fix ~25 ms before its capture** (EKF3's clamp, reproduced exactly). The offline replays use
   the capture stamp. The difference is ≤ ~5 mm at 0.2 m/s; stated, not changed.
4. **Finding to confirm in S2:** on ArduPilot's inputs (Replay), the UKF port's loss drift (6–19 mm) is EKF3's scale,
   not the offline UKF's (28–292 mm). This is an input-path effect, not yet attributed to a single input.
5. **`tags` and `heading` are exclusive** in the FGO node.
6. **Process:**
   - Another agent's lock wrapper overwrote and then deleted my `BUILD_LOCK` during my first `waf copter` (19:39–19:40;
     no flight ran; reported by the main session).
   - My wrapper uses an exclusive create (noclobber) and removes the lock only if it still holds its own PID.
   - My early process check (`pgrep -f '[a]rducopter'`) falsely matched my own command lines, which contained the
     word. That only caused refusals or waits, never a run under a simulator. It now matches the process name or a
     command line that starts with the binary.
   - No simulator was run.
