# Experiment H — marker-relative position holding (supervisor item 3): DESIGN and DRAFT pre-registration

**Status:** REVIEWED 2026-10-08. The supervisor ruled: proceed with S0 + S1 before the Fri 16 Oct freeze; S2/S3 on Mon
19–Fri 23 Oct (the simulation freeze is extended for H only; the 23 Oct experiment freeze stands). The ruling's
further instructions are in §R below. The binding pre-registration is METHODOLOGY "Experiment H: pre-registration".

## R. Supervisor ruling 2026-10-08 (incorporated)

**R1. During tag loss, position hold falls back to optical flow (with IMU and rangefinder) until the tag returns.**
Loss segments of pre-registered duration (**5, 15 and 30 s**), both **while hovering** and **during a lateral move**.

**R2. EKF3, source check:** **one source set suffices; no switching is needed.**
- `EK3_SRC1_POSXY 6` (ExternalNav), `EK3_SRC1_VELXY 5` (OpticalFlow) and `EK3_SRC1_YAW 6` (ExternalNav) coexist in one
  set.
- `readyToUseOptFlow()` requires only that the velocity source is OpticalFlow, flow fresher than 200 ms, tilt
  alignment and gyro-bias learning (`AP_NavEKF3_Control.cpp:551-559`). It does not exclude an ExtNav position source.
- **Shown in our own data:** T used exactly this set. In T_D_r1's 46 s gaps between tag fixes, EKF3 kept fusing flow
  (`XKF5` flow innovations non-zero on 100% of 400 rows in 35–75 s) and kept a relative position
  (`horiz_pos_rel` 1.00).
- **The known discontinuity is not a source switch but `posTimeout`.**
  - After > 10 s without an accepted ExtNav fix (with flow), `posTimeout` latches (`horiz_pos_abs` false: T_D_r1 gaps
    0.80–1.00).
  - The next fix **resets** the horizontal position to the fix (`ResetPosition`): a jump equal to the accumulated
    dead-reckoning error. Later fixes fuse **without the innovation gate** until the timeout clears.
  - Below 10 s, the returning fix goes through the 5σ position gate (and 3σ for yaw), so a large drift could be
    rejected: a lockout until the timeout makes the reset happen.
  - The H metrics measure both effects (§c).

**R3. UKF and FGO: identical inputs** — the same tag fixes when visible (the `/tags/sent` stream EKF3 received), flow,
IMU and range. No gate on the tag fixes (as in T), no reset; they simply resume fusing.

**R4. Loss metrics:**
- drift at the end of each loss against its duration;
- re-lock time;
- position and yaw jump at re-lock;
- **lockout**: whether any estimator rejects the returning tag (EKF3 `VISP`/innovation-gate records; the UKF/FGO by
  construction do not gate).

**R5. A pre-registered prediction for drift and re-lock per estimator** (METHODOLOGY pre-registration).

**R6. Recording** (no full-rate forward-camera stream). The exact bag topics:
- **Simulator truth and clock:** `/clock`, `/ground_truth/pose`.
- **All estimator inputs:** `/imu/data_raw`, `/imu/time_ref`, `/attitude/angular_rates`, `/optical_flow/measurement`,
  `/downward_lidar/range`.
- **Tag measurement:** `/tags/raw` (every detection, camera-from-tag pose) and `/tags/sent` (the fixes sent to EKF3).
- **Audit images:** `/forward_camera/image_audit` (the forward image republished at **2 Hz**, every 15th frame, by the
  tag bridge) and `/forward_camera/camera_info`.
- **Estimator outputs:** `/ekf/pose` (the AHRS output), plus the dataflash log with `XKF*`, `VISP`, `XUK*`/`XFG*`
  where those backends run.
- **Not recorded:** `/forward_camera/image` at 30 Hz (~3.3 GB per 5 min) and `/downward_camera/image`.
- S0's characterisation flights are the exception: short flights that record the full forward stream, because the
  characterisation needs every frame.

## 0. Task

- The drone localises **relative to an AprilTag on a wall**, seen by the **forward camera**.
- It **holds** a set point in front of the tag (1.5 m away, centred, at the tag's height), makes **lateral moves**
  left and right while keeping the tag in view, and **returns** to the hold point.
- **Closed loop:** the controller steers by the tag-relative estimate of the estimator under test.
- **Reuse:** T's tag module (`src/tags/tag_measure.py`, pupil_apriltags) and its measurement models (`h_tag`, the UKF
  update, the FGO factor), in the simulated mocap room (`room_tags`, 10 × 10 m, assumed until the real room is
  confirmed).

## a. The tag frame as the navigation reference, and how each estimator receives it

**Wall tag.**
- tag36h11 **id 10** (an id not on the floor), same 0.5 m model (0.4 m black square).
- Mounted **vertically** on the north wall (y = +5 m), centre at x = 0, z = 1.5 m. Floor tags stay; floor flow is
  unchanged.
- The texture convention for a vertical tag is **re-determined and frozen on a check flight**, as for the floor tags
  in T.

**Navigation frame "W"** (the tag frame expressed as a local NED frame):
- origin at the tag centre;
- **N = into the wall** (along the tag normal, towards the tag), **E = to the right along the wall** (as seen facing
  the tag), D = down;
- yaw 0 = facing the tag.
- **Hold point:** W = (N −1.5, E 0, D 0) (1.5 m in front, centred, at the tag's height), yaw 0.
- The floor and the room are not used for navigation; the rangefinder still gives height above the floor (POSZ
  unchanged).

**Measurement** (one per forward image, the same information as a T fix):
- the vehicle pose in W from one detection: `tag_measure.vehicle_pose` with the tag at the origin;
- the forward camera's extrinsics: optical z = body +x, optical x = −body y, optical y = −body z, at body
  (0.15, 0, 0);
- output: **(N, E, yaw)** plus the tag-derived height, which is not fused (the rangefinder is the height source for
  all three estimators, as in T).

**Validity rule and noise** (measurement-intrinsic and shared; set by stage S0, not assumed):
- T's "central third" was measured for a downward camera at 2 m.
- For the forward camera at 1–2.5 m, S0 measures pose error against image radius and distance.
- The rule is fixed from the S0 data **before** any estimator uses it. σ_pos is the p95 of the valid region, as T's
  0.05 m was.

**EKF3:** ExternalNav, as in T.
- `ODOMETRY` (`LOCAL_FRD`, W as NED, position N/E/D and yaw quaternion, velocity NaN, cov[0] = σ_pos²,
  cov[20] = σ_yaw²).
- `VISO_TYPE 1`, `EK3_SRC1_POSXY 6`, `EK3_SRC1_YAW 6`, `EK3_SRC1_VELXY 5` (flow kept), `EK3_SRC1_POSZ 2`
  (rangefinder).
- `VISO_POS_M_NSE` = the S0 σ_pos.
- **Yaw clamp:** σ_yaw_eff = max(`VISO_YAW_M_NSE`, angErr, **5° floor**). The 5° floor binds.
- Gates 5σ (position) and 3σ (yaw). After > 10 s without a fix (with flow), `posTimeout` latches, the next fix
  **resets** position and later fixes fuse ungated.
- `VISO_DELAY_MS` by the D2/D20 rule (minimum receipt latency) from S0, ≤ the 60 ms horizon.
- `ARMING_SKIPCHK 262144`. No EKF origin is needed.
- Closed loop: `AHRS_EKF_TYPE 3`, with GUIDED position targets in LOCAL_NED = W.

**UKF (closed loop through the ArduPilot port, `~/ardupilot_ukf` `AP_NavUKF`, `AHRS_EKF_TYPE 12`):**
- The port already takes the ExtNav **yaw** on EKF3's path (D17: the same call, clamp, timing, 5° floor and 3σ gate).
- **To add:** the ExtNav **position**, through the same `writeExtNavData` fan-out, R = max(`VISO_POS_M_NSE`, posErr)²
  and EKF3's timing. The gate is an open item for the review: the offline T rule (none) or EKF3's 5σ.
- Plus the first-fix re-anchor (as offline T). An equivalence test against the offline UKF on a recorded flight comes
  first, as for the heading (D17 V1).

**FGO (closed loop through the node, `fgo_node.py` → ODOMETRY → `AP_NavFGO`, `AHRS_EKF_TYPE 13`):**
- **To add:** a `/tags/sent` subscription, the tag factor (offline T's `tag_factor`), and the re-anchor at the first
  fix (offline T's `FGO.reanchor`).
- The fixed-lag window, solver and LM cap stay the thesis configuration.
- Node-equivalence test against the offline FGO first, as for D19.

**Shadow (stage S1):** with EKF3 flying, the UKF and FGO run as live shadows (the existing shadow paths), and offline
on the recorded `/tags/sent` (the room replays, with the forward measurement).

## b. Flight profile (one flight ≈ 4.5 min of sim time)

1. **Take-off** at the hold point (spawn W = (−1.5, 0), yaw 0, facing the tag) to 1.5 m. Fly no profile until the
   first fix is fused (re-anchor/alignment logged).
2. **Hold 60 s.**
3. **Lateral moves:** 3 cycles of centre → E +0.5 m → centre → E −0.5 m → centre.
   - Commanded at 0.2 m/s with 5 s pauses at each end (moving-setpoint position commands, as T's laps).
   - At 1.5 m, a 0.5 m offset puts the tag centre ~185 px from the image centre. S0 must confirm that this is inside
     the validity region; if not, the amplitude is reduced to the region's edge **before** registration.
4. **Return and hold 30 s.**
5. **Tag-loss segments (ruling R1):** a visual-only occluder (a grey 1.6 m panel 0.3 m in front of the tag,
   `gz service .../set_pose`, scripted by the harness at a logged sim time) covers the tag.
   - **While hovering** at the hold point: **5 s**, then 20 s re-acquired hold; **15 s**, then 20 s; **30 s**, then
     30 s.
   - **During a lateral move:** a centre → +0.5 m → centre move at 0.2 m/s (5 s each way, 2 s pause), with the tag
     covered for the **whole 12 s move** (a 12 s loss), then 20 s hold.
   - The vehicle keeps holding (or tracking) on flow + IMU + range alone while the tag is covered.
6. **Land.** Repeats: 3 per stage and estimator. Open loop is not used, since this is a closed-loop task.

## c. Metrics (against ground truth; all positions in W via the known tag pose)

- **Hold error:** the GT horizontal distance from the hold point, mean and max over each hold window (excluding the
  first 5 s after a profile change). Height error is reported separately.
- **Lateral tracking error:** GT minus the moving setpoint over the lateral cycles (RMSE, max, and overshoot at the
  ends).
- **Smoothness:** gyro activity, the RMS of the body rates high-passed at 1 Hz (as the closed-loop B-metrics), over
  the hold windows; also attitude-setpoint jitter.
- **Drift during tag loss:** the GT displacement of the vehicle during each occlusion (the controller holds the
  *estimate*, so this is the estimator's drift), and the estimate error at the end of the occlusion.
- **Re-lock:** time from occluder removal to the first fused fix, and to GT back within 5 cm of the hold point.
  - **Jump:** the largest estimate step in the 2 s after re-lock (EKF3's reset shows here) and the GT excursion it
    causes.

## d. Stages

- **S0 (offline + check flights; no estimator uses the tag yet):**
  - wall-tag world;
  - forward-camera tag characterisation (detection range, pose error against distance and image radius, ids,
    timing);
  - the validity rule and σ;
  - texture convention frozen;
  - `VISO_DELAY_MS` measured;
  - EKF3 ground test (ExtNav position+yaw accepted, no origin needed, arming).
- **S1:** EKF3 flies; UKF and FGO in shadow (live) and offline. 3 flights.
- **S2:** the UKF flies through the port. Gates first: port position-input equivalence test and a ground test. 3
  flights.
- **S3:** the FGO flies through the node. Gates first: node-equivalence test and a ground test (D25 style). 3 flights.

Each stage has pre-registered gates. A failed gate stops the stage and is reported.

## e. Hypotheses (draft) with basis

- **H-H1 (primary): every estimator holds within tag-fix accuracy.** Mean hold error ≤ 0.05 m and max ≤ 0.15 m in
  3/3 flights per estimator.
  - Basis: T condition A (fixes every ~4 s) gave live RMSE of 0.018–0.039 m. Here fixes are continuous at 30 Hz,
    while the controller adds its own tracking error.
- **H-H2: the FGO's hold error is lowest.** FGO < EKF3 and FGO < UKF mean hold error in 3/3 flights.
  - Basis: T condition A, where FGO live was 0.018 m against 0.039 (EKF3) and 0.037 (UKF).
  - Stated risk: the closed-loop FGO had larger heading jitter (fig10), which may cost smoothness.
- **P-H3 (smoothness, prediction):** gyro activity in the hold windows within 1.5× across estimators.
- **H-H4 (tag loss):**
  - After the **15 s** occlusion, EKF3's re-lock jump (largest estimate step) is larger than the UKF's and the FGO's
    in 3/3 flights. Basis: EKF3 resets position after `posTimeout` (> 10 s); the UKF and FGO fuse continuously.
  - After the **5 s** occlusion (no timeout), the jumps are within 1.5× of each other.
- **P-H5 (drift during loss, prediction):** GT drift during the 15 s occlusion ≤ 0.3 m for every estimator.
  - Basis: hovering flow dead reckoning, with T's single-tag condition drifting ~0.1–0.2 m over ~45 s of motion.

**Flight length with the ruling's loss segments:** ~60 + 75 (lateral cycles) + 30 + 25 + 35 + 60 (hover losses) + 32
(loss during a move) ≈ **317 s** plus take-off and landing (~6 min of sim time).

## Effort (days, sim time only)

| item | days |
|---|---|
| S0: wall-tag world, vertical texture check, forward-camera measurement path, characterisation, validity rule, latency, EKF3 ground test | 1.5 |
| harness: hold / lateral / occluder profile in `fly_trial`, scorer | 1 |
| S1 flights + shadows + scoring | 1 |
| S2: UKF port ExtNav position + re-anchor + equivalence test + ground test + flights | 1.5–2 |
| S3: FGO node tag factor + re-anchor + node equivalence + ground test + flights | 1.5–2 |
| **total** | **6.5–7.5** |

**Against the freeze (Fri 16 Oct; Mon 12–Wed 14 for simulator work):** S0 + S1 fit, about 3.5 days if started on
review. **S2 and S3 do not fit before the freeze.** Options for the review: (i) extend the freeze for H; (ii) S0 + S1
only before the freeze, with S2/S3 after; (iii) drop H in simulation and go straight to the real room with EKF3 only.

## Transfer to the real mocap room

- **The same components fly:**
  - the same tag family and printed size;
  - the same detection module (pupil_apriltags on the Pi; ARM timing to be measured, with the 5–7 ms/frame
    workstation figure as the reference);
  - the same `ODOMETRY` → ExtNav path into the real EKF3;
  - the same flight profile through `fly_trial`-style scripts.
- **Mocap gives ground truth directly** (`eval/mocap_align.py`: clock map and frame fit). The wall tag's pose in mocap
  is surveyed with a mocap marker cluster.
- **Re-measured on hardware, not transferred:**
  - the validity rule and σ (S0 repeated on real images against mocap);
  - `VISO_DELAY_MS` (D2 procedure);
  - flow quality on the real floor.
- **Tag loss:** a physical cover on a pole, or a scripted yaw-away if the cover is impractical.
- **Safety:** a geofence inside the net, an RC override, and the hold point ≥ 1 m from the wall.
