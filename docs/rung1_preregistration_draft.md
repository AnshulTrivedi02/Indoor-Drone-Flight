# Rung 1 pre-registration: DRAFT for user sign-off

> **Unheld 2026-10-11** (METHODOLOGY ruling 2026-10-11, item 1: "the scorer with a pre-registered window"). The two
> known defects of the 2026-10-10 draft are FIXED here:
> 1. **The start-aligned drift segment** (§4.3) was [t_to + 25 s, t_to + 30 s], inside the 30 s hover, where the
>    4-DoF yaw is noise. It is now the first `init_path_m` = 2.0 m of mocap horizontal travel after the motion onset
>    (the start of the first leg), from mocap only.
> 2. **The mocap clock-map windows** (§1, §8 step 2): `mocap_align`'s old default early window (arm, arm + 25 s) missed
>    the PRE-ARM sync wiggle. Its default is now the two DISARMED wiggle bursts (the last |ω| > 2 rad/s burst before
>    arming and the first after disarming, ± 2 s), and the scorer refuses a flight scored with other windows.
>
> **The machine-readable definitions** (window, metrics, drift segment, estimator records, clock-map rule) are in
> `docs/rung1_preregistration_draft.json`, which `eval/real_score.py` reads strictly (every key required, unknown keys
> refused, nothing defaulted). This text and that file must agree; the JSON is what the scorer applies.

**Status: DRAFT (R10), written 2026-10-10. Not signed off. Nothing in it is in force until the user signs it off (§11).**
No real flight has been flown, and no real log has been scored. Every value below that depends on the vehicle, the
sensors or the mocap volume is a placeholder marked **[TBD-S]** (supervisor input) or **[TBD-V]** (fixed from
VERIFICATION logs before any result flight is scored, §6). The scoring WINDOW is defined here by rule only: no value is
computed in advance.

Implements:
- METHODOLOGY "RULINGS (user, 2026-10-10, SUPERSEDING …): real flights built as RUNGS" (rung 1);
- METHODOLOGY "RULINGS (user, 2026-10-10): freeze scope; real-log flow timestamps; rung-1 software starts" (item 2, the
  timestamp rule);
- METHODOLOGY "STANDING RULE (user, 2026-10-10): verification flights are SHORT and never result data".

Companion documents: `docs/minimal_real_flight_plan.md` (the plan and its costing), `docs/rung1_flight_cards.md` (the
procedures), `realflight/params/rung1_template.parm` (the parameters).

---

## 1. What rung 1 tests

A **sim-to-real check of the standard-sensor comparison**. One real vehicle, stock ArduPilot at the pinned commit
`7bac20cbcc` (or `Copter-4.7.0`, if the supervisor rules so; §9 limit 3), its own flow sensor and downward rangefinder on
the flight controller (FC), flown by a safety pilot in ALT_HOLD. **Nothing of ours steers.** Afterwards, offline, on the
SAME logs:

| estimator | how it runs | input | output |
|---|---|---|---|
| **EKF3** | ArduPilot Replay of the flight's `LOG_REPLAY` records | the DAL records (`RFRH/RFRF`, `RISH/RISI`, `ROFH`, `RRNH/RRNI`, …) | the replayed `XKF1`, core 0 (`C = 100` in the Replay log) |
| **UKF port** | the fork's Replay (`~/ardupilot_ukf`, `AP_NavUKF`, branch with the R2 geometry change), the same pass | the same DAL records; sensor geometry read from the log (R2) | the replayed **`XUKO`** (its current-time output, the like-for-like counterpart of `XKF1`); `XUKF` (the fused state at the delayed horizon) as a secondary row |
| **FGO** | the corrected Python FGO (initial yaw σ 1°) via the dataflash → FGO-input converter (R1) | `RISI` (IMU deltas), `ROFH` (flow), `RRNI` (range), on the FC clock | the FGO trajectory TUM |
| **truth** | mocap, recorded throughout | mocap CSV | `eval/mocap_align.py` (time map fitted on the two DISARMED sync wiggles on `RISI`, found by its default rule: the last \|ω\| > 2 rad/s burst before arming and the first after disarming, ± 2 s; R8) → TUM on the FC clock |

All four series are on ONE clock (the FC's `TimeUS`); only mocap needs a clock map.

---

## 2. Sorties: verification or result-producing

Per the standing rule, every sortie is classified IN ADVANCE. **Verification sorties are never scored and never reused
as result data**, whatever they show. Their logs may be used ONLY for the purposes listed (and for §6's timing
measurement, which is a calibration, not a result).

| sortie | class | length (shortest that exercises it) | why that length suffices | its logs are used for |
|---|---|---|---|---|
| **B: bench checks** (props off) | verification | each check ≤ 1–2 min; see the flight cards B1–B8 | each checks one fact (a sensor healthy, a sign, a record present); repeating it longer adds nothing | pass/fail of the bench items; §6 timing (the sync-wiggle cross-correlation) |
| **H: hand-carried pass** (disarmed, in the volume) | verification | ~2 min: wiggle (5 s), one carried out-and-back leg at flight height (~40 s), wiggle (5 s), margins | disarmed, EKF3 stays "on ground" and does not aid with flow, so a longer carry tests nothing more. One leg exercises the plumbing, the clock map, the flow sign and Replay reproduction | the end-to-end pipeline rehearsal (same day); the Replay-fidelity check on a non-aiding EKF3; §6 timing |
| **V: first hover** (armed) | verification | ~1.5–2 min airborne: take-off, hover 45 s, one 2 m leg and back at ≤ 0.3 m/s, land | 45 s covers EKF3's flow-aiding start (about 16 s after take-off in SITL, set by gyro-bias convergence) with margin; one short leg shows flow drives the velocity with the right sign. That is all V checks | that flow aiding engages; the Replay-fidelity check WITH flow aiding; §6 timing |
| **R1…Rn: result flights** | **result-producing (pre-registered here)** | the §3 profile (~2.5–3.5 min) | set by what the result needs (§3) | scoring (§4–§8) |

A sortie flown under a result card but aborted before the window ends (§3.3) is NOT re-labelled as verification: it is a
result flight, excluded under §3.3 and reported as excluded.

---

## 3. Result flights

### 3.1 Profile (every result flight identical)

Flight volume: **[TBD-S]** (mocap-covered box: length × width × usable height; floor material). The leg lengths below
are fixed from it BEFORE the first result flight and are then the same for every flight.

1. **Disarmed, logging (`LOG_DISARMED 1`):** sync wiggle: the vehicle is lifted and rotated sharply about all three
   axes for ~5 s, then set down on its marked start spot. Stand clear.
2. **Arm, take off** in ALT_HOLD to the hover height **h = [TBD-S] m** (1.0–1.5 m; at least RNGFND1_MIN + 0.5 m and
   inside the flow sensor's working range).
3. **Hover 30 s** over the start spot. *Why:* EKF3 starts flow aiding only after gyro-bias convergence (~16 s after
   take-off in SITL, CLAUDE.md "EKF3 Solution Diagnosis"); the window starts at take-off + 25 s (§4.2).
4. **Cruise legs:** a rectangle (or out-and-back if the volume is narrow) at **0.3–0.5 m/s [TBD-S]**, legs **[TBD-S] m**,
   **two laps**, about **90 s** of cruise. Pilot-flown in ALT_HOLD; speed is the pilot's target, not enforced.
   *Why this length:* it gives the estimators a closed path (start ≈ end) with turns in both directions, and enough
   travel for a drift error to exceed the mocap/alignment floor (a few mm); it fits a mocap volume. It is NOT a
   long-duration test (§9 limit 9).
5. **Hover 10 s** over the start spot. Land, disarm.
6. **Disarmed, still logging:** second sync wiggle (~5 s). Stop logging.

Total ≈ 2.5–3.5 min per flight including the wiggles.

### 3.2 Number of flights

- **n = 5 result flights planned** on one floor, one day, one vehicle, in sequence, with a spare slot for **one** extra
  flight, used only to replace a flight excluded under §3.3 (so at most 6 result flights are flown).
- If the supervisor's floor input (S7) allows a plain (low-texture) sheet: a separate set of **n = 3** on it, labelled
  EXPLORATORY (no ordering claim; descriptive only).
- **No flight is added, dropped or re-flown because of what an estimator showed.** The decision to fly the spare is made
  from the §3.3 exclusion reasons only, before any estimator is run on that flight.

### 3.3 Exclusion rules (decided from logs and mocap only, BEFORE any estimator is run on the flight)

A result flight is EXCLUDED, and reported as excluded with its reason, if any of:
1. the pilot aborted before the window end (§4.2), or the profile deviated grossly (e.g. a leg skipped);
2. the log is incomplete for replay: any `DSF.Dp` > 0 (dropped writes) inside the window, or a gap in `RFRH` frames
   > 50 ms inside the window, or any of `RISI`/`ROFH`/`RRNI` missing;
3. mocap lost the rigid body for > 0.5 s cumulatively inside the window, or either sync wiggle is missing;
4. the mocap clock map fails (`mocap_align` residual above the bound **[TBD-V]**, set from the hand-carried pass).

An estimator that DIVERGES is **not** a reason to exclude: its score is reported as it is.

---

## 4. Metric

### 4.1 Primary metric (as the simulation's STANDING RULE metric)

**evo -a**: `evo_ape tum <mocap.tum> <estimator.tum> -a --t_max_diff 0.05` (Umeyama SE(3), no scale), translation RMSE
in metres, fitted and evaluated over the window only, per estimator per flight. Reference TUM with identity quaternions
(APE = translation part), as `eval/three_way_eval.py` (`real_score.py` imports its call; `t_max_diff` 0.05 is the only
value it accepts). Each estimator's TUM is aligned separately by evo's own fit, so the estimators' arbitrary yaw and
origin are absorbed (not their drift).

**Why evo -a (SE(3)) and not the 4-DoF fit (proposed, for sign-off):** the sim-to-real statement (§7) compares the real
DECISION CATEGORY with the simulation's, and every simulation category was decided on evo -a. A 4-DoF primary metric would
compare categories decided on different metrics. The 4-DoF fit (yaw + translation; both frames gravity-aligned) is
physically tighter and is reported as a **secondary** metric (`ate_4dof`); on SITL the two agree to 1 mm (handover
`2026-10-10_r1_mocap_align_scorer.md`). If they disagree on a real flight in a way that changes a decision category, that
is reported, but the category stands on evo -a.

**Estimator records (proposed):** EKF3 = the replayed `XKF1` core 0; UKF port = the replayed **`XUKO`**; FGO = the
converter's TUM. `XKF1` logs EKF3's output-predictor (current-time) state (`AP_NavEKF3_Logging.cpp:26-27` →
`getPosNE`/`getVelNED`, `AP_NavEKF3_Outputs.cpp:257-263`, `outputDataNew`); `XUKO` is the port's current-time output
(`AP_NavUKF.cpp` `log_state`). `XUKF` is the port's fused state at the delayed fusion horizon, so it is NOT the counterpart
of `XKF1`; it is reported as a secondary row (`UKF_horizon`). Onboard EKF3 (the flight's own `XKF1`) is the secondary row
`EKF3_onboard` (§4.3).

### 4.2 The window (defined from mocap ONLY, never from an estimator's output)

On the FC clock, after `mocap_align`'s time map (rule `airborne` in the JSON; `real_score.window_from_rule`):
- `z0` = the 5th percentile of mocap height over the WHOLE record (the resting height; the vehicle rests at both ends,
  while the record may START with it held up for the sync wiggle, so "the median before arming" is not used);
- airborne = mocap height > `z0 + 0.30 m`; the LONGEST airborne run of at least 1 s is the flight;
- **t_to** = its first sample (take-off), **t_ld** = its last sample (landing);
- **window W = [t_to + 25 s, t_ld − 5 s]**, refused if shorter than 20 s.

The 25 s matches §3.1 step 3 (EKF3's aiding start plus margin); the 5 s excludes the landing flare. The same W applies to
all three estimators on that flight. Nothing about W is tuned after scoring.

### 4.3 Secondary metrics (reported, no decision rule attached)

- **4-DoF ATE** (`ate_4dof`) over W: yaw + translation fit, RMSE (§4.1).
- **Start-aligned drift** (rule `motion_onset_path` in the JSON): each estimator aligned to mocap (4-DoF) on an initial
  segment ONLY, then the horizontal error at t_ld − 5 s and its ratio to the mocap path length in W. The segment is
  defined from mocap only: from the **motion onset** (the first time in W the mocap horizontal speed, 1 s boxcar, stays
  above 0.15 m/s for 1 s) until the mocap has travelled **2.0 m** horizontally, i.e. the start of the first leg. It is
  refused (reported as such) if it moves less than 1.0 m from its first point. 2.0 m must not exceed the first leg length
  **[TBD-S]**; it is confirmed when the leg length is fixed, before any result flight. (Fixes defect 1; the old segment
  [t_to + 25 s, t_to + 30 s] lay inside the hover.)
- **Validity:** the fraction of W each estimator flags its horizontal position valid (EKF3 `XKF4.SS` bit 3; UKF `SS`
  column; FGO its own flag), and EKF3's flow-innovation rejections (`XKF5`).
- **Onboard EKF3** (the flight's own `XKF1`, core 0; row `EKF3_onboard`) and **UKF at the horizon** (`XUKF`; row
  `UKF_horizon`) scored the same way, reported next to the primary rows.

---

## 5. Replay-fidelity gate (EKF3), per flight

Before scoring, Replay EKF3 is compared with the onboard EKF3 of the same flight (`XKF1` core 0 against replayed core
100, `Tools/Replay/check_replay.py` plus our own differences), over the armed period:

- **PASS if** the maximum horizontal position difference ≤ **0.01 m**, the maximum height difference ≤ **0.01 m**, and the
  maximum yaw difference ≤ **0.1°**.
- **PASS** → EKF3 is reported as "EKF3 (onboard, reproduced in Replay)".
- **FAIL** → EKF3 is reported as **"Replay EKF3"**, never as the onboard EKF3; the onboard `XKF1` row is reported next to
  it, and the size of the difference is stated. The flight is NOT excluded.
- Bit-exact equality is not expected on ARM (FMA contraction, single vs double on a non-H7 board). The bound is the
  plan's proposal; **[TBD-V]: it is confirmed or widened ONCE, on the verification logs (H and V), before any result
  flight is scored, and the reason is recorded.** After that it is fixed.

Pre-conditions (all from verification or SITL, before scoring):
- the R2 UKF port passes its regression (byte-identical on existing SITL `LOG_REPLAY` logs; handover
  `docs/handovers/2026-10-10_r1_port_params_cards.md`);
- the R1 converter passes its SITL acceptance test (its band is pre-registered with R1);
- the R8 `mocap_align` on `RISI` passes its SITL self-test.

---

## 6. Flow timestamp rule (placeholder; fixed BEFORE scoring)

Ruling 2026-10-10 item 2:
- **EKF3** keeps its own rule, as onboard: arrival − `EK3_FLOW_DELAY` − 50 ms (`flowTimeDeltaAvg_ms`/2) − 6 ms (half a
  filter step), clamped to the fusion horizon.
- **UKF port and FGO:** the best estimate of the TRUE capture time: **arrival − d_cap**, with **d_cap = [TBD-V] ms**.
  - d_cap is determined from the real sensor's MEASURED rate and delay, under D18: the flow update interval from the
    `ROFH` arrival times, and the delay from cross-correlating the flow sensor's rotational response with the `RISI`
    gyro during the sync wiggles and the bench rotations (props off), where translation is ~0.
  - **Measured on VERIFICATION logs only** (B, H, V), never on a result flight. The method, the value and its
    uncertainty are recorded in a METHODOLOGY entry before any result flight is scored. After that it is fixed.
  - `EK3_FLOW_DELAY` on the vehicle (`rung1_template.parm`) is set from the sensor's documentation, not from d_cap; the
    two are reported side by side.
- **Implementation gap, flagged:** the UKF port today fuses flow at EKF3's time (arrival − `EK3_FLOW_DELAY` − 50 − 6)
  with `EK3_FLOW_DELAY` read from the log (R2). Applying "arrival − d_cap" to the port needs a small port option
  (a capture-delay override). That change is a follow-up, made and regression-tested before scoring.
- Either way this differs from the simulation, where the UKF and FGO used capture stamps from the camera pipeline. That
  difference is stated next to any sim-to-real comparison.

---

## 7. Claims and decision rules (mirroring the simulation's confirmatory test)

**Primary comparison: EKF3 vs FGO** (as the simulation's confirmatory test). Secondary: EKF3 vs UKF, UKF vs FGO
(reported with the same rule, labelled secondary).

For each pair (A, B), per usable result flight i: **d_i = evo(A) − evo(B)** (§4.1, same flight, same W).

- **Claim "A lower than B on these real flights"** only if BOTH hold:
  - **(a)** d_i < 0 on **every** usable flight (one-sided sign test: p = 1/32 = 0.031 at 5/5; 1/16 = 0.0625 at 4/4);
  - **(b)** the 95% t-interval of mean d (df = n − 1) excludes 0.
- **Claim "B lower than A"** by the mirror rule.
- **Otherwise: no ordering is claimed**; mean d ± its 95% CI is reported as the difference.
- **If fewer than 4 result flights are usable: no ordering claim at all**; the per-flight values and their spread are
  reported (descriptive only).
- Why "every flight" rather than the simulation's 6/7: with n = 5 the simulation's ≥ 86% threshold rounds to 5/5, and a
  4/5 sign result (p = 0.19) would carry no weight. Requiring (a) and (b) together guards against one flight deciding the
  result and against a tiny consistent difference being over-read, as in the simulation.
- Multiplicity: the primary pair is the only one whose claim is used in the thesis's conclusions; the two secondary
  pairs are reported with the same rule and labelled secondary (3 pairs × p = 0.031 would be ~0.094 family-wise).

**Sim-to-real statement.** For each pair the real decision category (A lower / B lower / no ordering) is set next to the
simulation's category for the same pair on the textured floor (from the final restatement in force at the time of
scoring; e.g. corrected FGO vs EKF3: "no ordering claimed"). **"Consistent with the simulation"** is said ONLY if the
categories are the same. Magnitudes (real evo -a against simulated) are reported side by side with the differences of §9,
with no decision rule (different flight lengths, volumes and flow sensors make them non-comparable as numbers).

**Reported regardless of outcome:** every result flight's three scores, the excluded flights and their reasons, the
Replay-fidelity gate per flight, and the secondary metrics.

---

## 8. Analysis steps, in order (all offline; may run after the 23 Oct freeze, to ~30 Oct, per the freeze ruling)

1. Data-integrity checklist per flight (flight cards §7); §3.3 exclusions decided and recorded.
2. Mocap → FC clock map and the mocap TUM (`mocap_align`, R8) with its DEFAULT windows: the two disarmed sync-wiggle
   bursts (|ω| > 2 rad/s on `RISI`: the last before arming and the first after disarming, ± 2 s; JSON `clock_map`). If
   either burst is not found, the flight fails §3.3 item 3 ("either sync wiggle is missing"); windows are never set by
   hand for a result flight. The residual and rate are recorded. W computed (§4.2) and recorded.
3. EKF3 Replay (fork's Replay binary; also the stock Replay if 4.7.0 flew) → the §5 gate → EKF3 TUM.
4. UKF port (same Replay pass) → `ukf_csv_to_tum.py --frame enu --identity-quat` → UKF TUM.
5. FGO via the converter (R1) → FGO TUM.
6. Scorer (R9): `eval/real_score.py --prereg docs/rung1_preregistration.json --mocap-align-json <flight>/mocap_align.json
   ...`: evo -a over W for all three; secondary metrics; §7 decisions. The scorer refuses a prereg with missing or
   unknown keys, a record other than the registered one, and a mocap_align JSON with non-default windows.
7. A METHODOLOGY result entry; numbers into `docs/thesis/numbers.md` under the rules in force.

---

## 9. Stated limits (to appear next to every rung-1 result)

1. **The flow source differs:** a dedicated flow sensor (its own optics, integration window and quality metric), not the
   thesis's camera pipeline (Shi-Tomasi + LK + RANSAC). Flow validity is `Qual > 0` (EKF3's rule), not the pre-registered
   camera rule (inlier ≥ 0.85, features ≥ 20), which does not apply here.
2. **The degraded-sensing variable is not replicated** unless a plain floor is laid (§3.2, exploratory only). Rung 1
   speaks to the nominal arm.
3. **Firmware:** if `Copter-4.7.0` flies instead of the pinned commit, the real EKF3 is a different EKF3 version from the
   simulated one (about 20 + 4 differing commits, incl. flow-fusion and zero-velocity changes); stated, and the pinned
   EKF3 replayed on the 4.7.0 log is reported as a secondary row.
4. **No closed loop:** no estimator of ours steers; no stability or closed-loop claim.
5. **EKF3 is "the onboard EKF3" only if the §5 gate passes.**
6. **Small n:** 5 flights, one vehicle, one floor, one day; ordering claims only under §7.
7. **No-compass yaw** (if the nomag variant is ruled): real indoor yaw drift may differ from the simulation's ~8°/min;
   the alignment absorbs the initial yaw, not the drift. If the compass variant is ruled, EKF3 has an absolute yaw the
   UKF/FGO lack; then the like-for-like EKF3 row is a Replay with `EK3_SRC1_YAW 0`, and the onboard compass EKF3 is
   secondary.
8. **Flow timing:** EKF3 uses its own rule; the UKF/FGO use d_cap (§6). The simulation's UKF/FGO used camera capture
   stamps. **Derotation** (ruling 2026-10-11, D18): EKF3 uses the rate the flow backend delivers (onboard behaviour); the
   UKF port and the FGO derotate with their OWN bias-corrected gyro (`RISI`), not `ROFH.G`, which for MAV/Pixart sensors
   carries EKF3's gyro-bias estimate. In the simulation all three derotated with the same 20 Hz-filtered gyro, so this is
   a stated difference.
9. **Short flights** (~90 s of cruise in a mocap volume) against 300 s / 150 m corridors: the long-duration drift results
   are not re-tested.
10. **Mocap ↔ FC time** comes from the |ω| fit (validated on synthetic data until the hand-carried log); its residual is
    reported per flight.
11. **Rangefinder minimum range:** if RNGFND1_MIN exceeds the resting height, the rangefinder reads "out of range low"
    on the ground; EKF3 then uses `RNGFND1_GNDCLR`, but the UKF port initialises from the first in-range sample
    mid-climb (open item in the handover). Stated if it applies.

---

## 10. Open inputs before sign-off

- Supervisor (S1–S7 of the plan): the board, the flow sensor and rangefinder, the mocap system and volume, the firmware,
  the floor, the compass variant, the safety pilot.
- The §6 port option (capture-delay override). The R1/R7/R8/R9 tools are built and tested offline (handover
  `docs/handovers/2026-10-11_r1_converter_mocap_scorer.md`); none has seen real data.
- The user's rulings on: n = 5 (+1 spare); the window rule (§4.2); the primary metric evo -a vs 4-DoF and the UKF record
  `XUKO` (§4.1, proposed); the drift segment (§4.3, proposed); the "every flight" sign criterion (§7); the 1 cm / 0.1°
  Replay bound (§5).

## 11. Sign-off

| | name | date | changes requested |
|---|---|---|---|
| user | | | |
| supervisor (informed) | | | |

Once signed, this file is copied to `docs/rung1_preregistration.md` (status PRE-REGISTERED) and
`docs/rung1_preregistration_draft.json` to `docs/rung1_preregistration.json` (only its `status` changed); a METHODOLOGY
entry records the commit and the JSON's sha256 (which every score file carries). Any later change is a dated amendment, made before the affected data are scored.
