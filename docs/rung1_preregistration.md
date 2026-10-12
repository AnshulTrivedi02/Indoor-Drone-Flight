# Rung 1 pre-registration (PRE-REGISTERED)

**Status: PRE-REGISTERED. The user signed it off on 2026-10-12** (METHODOLOGY "RULINGS (user, 2026-10-12)", item 2):
- the primary metric is evo -a SE(3);
- the UKF record is `XUKO`;
- cross-track drift per minute and heading drift in deg/min (UNALIGNED) were added as secondary metrics BEFORE ANY
  DATA, for comparability with the simulation corridor results (§4.4).

This file and `docs/rung1_preregistration.json` are what is in force. The drafts (`docs/rung1_preregistration_draft.md`
and `.json`, sha256 `3c412e16…` / `1680a22f…`) are kept unchanged as the record of what was signed.

No real flight has been flown, and no real log has been scored. Every value that depends on the vehicle, the sensors or
the mocap volume is a placeholder:
- **[TBD-S]**: a supervisor input;
- **[TBD-V]**: fixed from VERIFICATION logs before any result flight is scored (§5, §5b, §6).

The scoring WINDOW is defined by rule only: no value is computed in advance. Any later change is a dated amendment,
made before the affected data are scored.

> **Changes at sign-off (2026-10-12), against the draft as signed:**
> 1. **Status** (this header and §11).
> 2. **§4.4, NEW: the two secondary drift metrics** ruled before any data. The JSON gains a REQUIRED `secondary`
>    section, so the JSON is no longer "the draft with only `status` changed": `name`, `status`, two `rationale`
>    entries and `secondary` were changed or added. `window`, `metrics`, `drift`, `estimator_records` and `clock_map`
>    are identical to the draft's (checked by `eval/real_score_test.py`).
> 3. **§4.1, implementation flag (the record is unchanged): `XUKO` is not decodable from a Replay output of a
>    stock-flown log.** The source the scorer reads it from needs a user ruling (§4.1).
> 4. **§5b, NEW: the converter acceptance band**, pre-registered (task "the converter band").
> 5. **§6: the capture-delay procedure** is fixed (method, file, uncertainty rule). The VALUES stay [TBD-V].
> 6. **§8: the analysis steps** follow 3–5 (the strict log reader, the 25 Hz IMU fallback, the delays file).
> 7. **§9 item 11, a FACTUAL CORRECTION** (not a change to any metric or criterion): EKF3 does NOT use
>    `RNGFND1_GNDCLR` for an out-of-range-low rangefinder.
>
> **The machine-readable definitions** (window, metrics, drift segment, estimator records, clock-map rule, secondary
> metrics) are in `docs/rung1_preregistration.json`. `eval/real_score.py` reads it strictly: every key is required,
> unknown keys are refused, and nothing is defaulted. This text and that file must agree; the JSON is what the scorer
> applies.
>
> *(Kept from the draft, 2026-10-11: the two defects of the 2026-10-10 draft were fixed before sign-off:
> (1) the start-aligned drift segment now starts at the motion onset, not inside the hover (§4.3);
> (2) the mocap clock-map windows are the two DISARMED sync-wiggle bursts (§1, §8 step 2).)*

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
| **UKF port** | the fork's Replay (`~/ardupilot_ukf`, `AP_NavUKF`, the merged R2 geometry change, installed `be7c4d18`), the same pass | the same DAL records; sensor geometry read from the log (R2) | the replayed **`XUKO`** (its current-time output, the like-for-like counterpart of `XKF1`; for where it is read from, see §4.1); `XUKF` (the fused state at the delayed horizon) as a secondary row |
| **FGO** | the corrected Python FGO (initial yaw σ 1°) via the dataflash → FGO-input converter (R1), accepted under §5b | `RISI` (IMU deltas), `ROFH` (flow), `RRNI` (range), on the FC clock, with the §6 capture delays | the FGO trajectory TUM |
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

**Why evo -a (SE(3)) and not the 4-DoF fit (signed off 2026-10-12):** the sim-to-real statement (§7) compares the real
DECISION CATEGORY with the simulation's, and every simulation category was decided on evo -a. A 4-DoF primary metric would
compare categories decided on different metrics. The 4-DoF fit (yaw + translation; both frames gravity-aligned) is
physically tighter and is reported as a **secondary** metric (`ate_4dof`); on SITL the two agree to 1 mm (handover
`2026-10-10_r1_mocap_align_scorer.md`). If they disagree on a real flight in a way that changes a decision category, that
is reported, but the category stands on evo -a.

**Estimator records (signed off 2026-10-12):** EKF3 = the replayed `XKF1` core 0, record **`XKF1@100`**; UKF port = the replayed
**`XUKO`**; FGO = the converter's TUM. The core is part of the record because an ArduPilot Replay output log carries BOTH
the flight's original records (`C` = 0, 1, …) and the replayed ones (`C` = 100 + core; `Tools/Replay/check_replay.py`
pairs C with C + 100): a bare `XKF1` would silently be the ONBOARD EKF3. The scorer refuses `XKF1` without a core.
Stock rung-1 firmware runs no UKF, so every `XUKO`/`XUKF` record in that log is the fork's Replay. `XKF1` logs EKF3's output-predictor (current-time) state (`AP_NavEKF3_Logging.cpp:26-27` →
`getPosNE`/`getVelNED`, `AP_NavEKF3_Outputs.cpp:257-263`, `outputDataNew`); `XUKO` is the port's current-time output
(`AP_NavUKF.cpp` `log_state`). `XUKF` is the port's fused state at the delayed fusion horizon, so it is NOT the counterpart
of `XKF1`; it is reported as a secondary row (`UKF_horizon`). Onboard EKF3 (the flight's own `XKF1`) is the secondary row
`EKF3_onboard` (§4.3).

**Implementation flag (2026-10-12): where `XUKO` is read from. The record is unchanged; the source is a USER RULING,
needed before scoring.**
- **The finding** (handover `docs/handovers/2026-10-12_r1_scoring_items.md` §C;
  `eval/results/r1_scorer/xuko_replay_check_2026-10-12.json`). The fork's Replay of a log that does not already declare
  the UKF messages writes `XUKF`, `XUKO`, `XUKS` and `XUKH` WITHOUT their FMT records. That covers every stock-flown
  rung-1 log. It was checked on the installed Replay `be7c4d18` and on older builds.
  - So **`XUKO` is not decodable from the Replay output log**.
  - The same undeclared records make pymavlink unable to read the log at all: it exits, or returns about 15 `XKF1` per
    core. The scorer therefore reads logs with `eval/df_reader.py`. It refuses a log whose replayed `XKF1@100` TimeUS
    sequence differs from `XKF1@0`'s, and it refuses `XUKO` when the log has no FMT for it.
  - The sentence above, "every `XUKO`/`XUKF` record in that log is the fork's Replay", holds. Those records are simply
    undeclared.
- **What the scorer must use instead, until the port is fixed** (port spec `docs/rung1_port_spec_capture_delay_xuko.md`
  §S2):
  - **(a) preferred:** the port emits the FMT records in Replay. `XUKO` is then read from the Replay output log, as
    registered.
  - **(b)** the port writes `ukf_output.csv` in Replay with EXACTLY `XUKO`'s columns and values (current time, not the
    horizon), read with `real_score.py --est-csv UKF=…`.
  - `ukf_shadow.csv` is NOT a substitute: it is the horizon state, i.e. `XUKF`.
- **Not acceptable:** decoding the undeclared records by their length; or re-wording the record to `XUKF`, which would
  change a signed-off item and needs a dated amendment.
- **For a Replay of a FORK-flown log** (the U10 gate, not rung 1), the onboard and the replayed `XUKO` are interleaved
  under one FMT and cannot be told apart. The scorer refuses non-increasing `XUKO` stamps.

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
  above 0.15 m/s for 1 s) until the mocap has travelled **2.0 m** horizontally: the first 2 m of mocap travel after
  the onset. This is normally the start of the first leg, but not guaranteed: ALT_HOLD has no horizontal position hold,
  so a hover correction can exceed 0.15 m/s for 1 s. The segment is then partly a drift correction; it is refused
  (reported as such) only if it moves less than 1.0 m from its first point, which keeps the fitted yaw defined.
  **[TBD-S]**, confirmed when the profile is fixed and before any result flight: 2.0 m must not exceed the first leg length,
  and `onset_speed_mps` (0.15) must lie well below the leg speed (0.3–0.5 m/s) and above typical hover-correction
  speeds. (Fixes defect 1; the old segment [t_to + 25 s, t_to + 30 s] lay inside the hover.)
- **Validity:** the fraction of W each estimator flags its horizontal position valid (EKF3 `XKF4.SS` bit 3; UKF `SS`
  column; FGO its own flag), and EKF3's flow-innovation rejections (`XKF5`).
- **Onboard EKF3** (the flight's own `XKF1`, core 0, record `XKF1@0` in the same Replay log; row `EKF3_onboard`) and **UKF at the horizon** (`XUKF`; row
  `UKF_horizon`) scored the same way, reported next to the primary rows.

### 4.4 Secondary drift metrics, ruled BEFORE ANY DATA (2026-10-12): heading drift and cross-track drift, UNALIGNED

These were added at sign-off for comparability with the simulation corridor results. They are reported per estimator
and per flight next to §4.1–4.3, with **no decision rule** (§7 is unchanged).

**Code and tests:**
- JSON section `secondary`;
- `eval/real_score.py` `heading_drift()` and `cross_track()`;
- tests in `eval/real_score_test.py`;
- the SITL regression against stored corridor values: `eval/results/r1_scorer/regress_secondary_2026-10-12.py` →
  `regression_secondary_2026-10-12.json` (all pass).

**Heading drift, deg/min** (`heading_drift`). This is exactly the corridor rule of `eval/d15_drift.py` (also
`eval/phase4_eval.py` and `eval/d15_port_score.py`):
- **Yaw error** = estimator heading − mocap heading at the estimator stamps. Both series are unwrapped over the WHOLE
  record first.
- **Wrap:** the error is wrapped to (−180°, 180°] unless it runs away, i.e. max |err − err₀| ≥ `wrap_limit_deg` (170°).
- **The value** is the least-squares slope of the error against minutes, over the window **W** (§4.2).
- **NED sense:** clockwise from above is positive, as `XKF1.Yaw` and `XUKO.Yaw`. ENU-sense figures are the negative.
- **Unaligned by construction:** the slope does not depend on a constant heading offset, so no alignment enters.
- **Sources:**
  - `XKF1@100` / `XKF1@0` / `XUKO` / `XUKF`: their `Yaw` field;
  - the FGO TUM: its quaternions;
  - mocap: the `mocap_align` TUM's quaternions.
- **Regression:**
  - reproduces the stored corridor values to rounding (≤ 2e-15 deg/min): `d15_drift.json` UKF and FGO on
    `dsn_tex_r1..r3` (TUM path, sign-flipped from ENU);
  - and `d15_port/dsn_tex_r8` `cruise_yaw_drift_dpm_NED` 9.294 (the NED-yaw path).

**Cross-track drift, m/min** (`cross_track`). This is the corridor's cross-track generalised to a closed path:
- **In the corridor**, cross-track was the lateral (East, across the corridor) error growth over the pinned cruise
  window, with both frames shared by construction:
  - the "position error growth re-referenced at cruise start" of `eval/ukf_shadow_replay_check.py`;
  - and the heading-share decomposition `xtrack_err_m` of `eval/phase5_analysis.py`.
- **Rung 1:**
  - **Lateral axis:** the RIGHT normal of the MOCAP horizontal direction of travel, `n = (u_y, −u_x)` in ENU, with u
    taken from the mocap velocity through a 1 s boxcar (`smooth_s`). A northward leg has n = East, so on a straight
    northward path the corridor's axis and sign are reproduced exactly. **Sign:** + = to the right of the direction of
    travel. A clockwise (NED-positive) heading error drifts the path to the right, as in the corridor (+8°/min with
    +40 m East).
  - **Samples:** only CRUISE samples, inside W, where the mocap smoothed horizontal speed is > `min_speed_mps` = 0.15
    m/s **[TBD-S]**. That threshold must lie below the leg speed; it is confirmed with the profile, like
    `onset_speed_mps`. The direction of travel is undefined in a hover, so hovers and stops are left out.
  - **The value:** the integral of `(v_est − v_mocap) · n` over consecutive selected estimator samples (trapezoid),
    divided by the selected cruise time in minutes. The cruise time, the signed metres and |m/min| are also reported.
  - **Velocities:** `np.gradient` of the POSITIONS, for every estimator, since a TUM carries no velocity. The integral
    is therefore the lateral POSITION-error growth.
    - The corridor's heading-share figure integrated EKF3's logged `XKF1.VE` instead. That differs from its own `PE` by
      3.65–3.68 m over 302 s on `dsn_tex_r1..r3`, an EKF3 output property, not a metric difference.
    - The regression shows both:
      - with `XKF1` VE/VN given, it reproduces the stored `xtrack_err_m` to ≤ 4e-5 relative;
      - with the registered position rule, it equals the position-growth form to ≤ 7e-5 relative (7.06 / 6.56 / 7.24
        m/min for EKF3 on `dsn_tex_r1..r3`).
  - **UNALIGNED, with ONE stated anchor** (a departure from the corridor, stated):
    - In the corridor the frames were related by construction: every estimator started on the true heading.
    - With no compass, the real estimator frames have arbitrary headings, so the minimal stand-in is used: the estimator
      frame is rotated into the mocap frame by ONE yaw. That yaw is the circular mean of (estimator heading − mocap
      heading) over the `anchor_avg_s` = 1 s ending at mocap take-off t_to (§4.2), from mocap and the estimator's own
      heading only.
    - There is no fit, and nothing after take-off is absorbed. Heading error that builds up before take-off is removed;
      error in the hover is kept. (In the corridor even the pre-take-off error counted.)
  - **Requirement on the mocap rigid body.** Its x axis must lie along the vehicle's nose, so that the mocap heading is
    the body heading (flight cards: rigid-body definition).
    - A residual offset d° adds `speed · sin(d)` of lateral rate to EVERY estimator alike: a common-mode bias, which does
      not change the between-estimator differences.
    - The scorer reports it as `anchor_sensitivity_m_per_min_per_deg`, about 0.42 m/min per degree at 0.4 m/s.
  - **Each source's heading must be its body heading in the frame of its own positions.** This holds for
    `XKF1`/`XUKO`/`XUKF` and for the FGO TUM.
    - It does NOT hold for the stored corridor bag TUMs: their ground-truth quaternions follow the estimator's yaw-0
      convention while their positions are ENU. So `real_score` run end to end on those TUMs gives meaningless
      cross-track values, and the regression uses `XKF1` against `SIM` instead.
- **Comparability, stated next to any comparison** (descriptive only):
  - the corridor flew 0.5 m/s straight for ~300 s; rung 1 flies 0.3–0.5 m/s on a rectangle for ~90 s;
  - cross-track per minute scales with speed;
  - the corridor EKF3 heading-drift figure +6.6…+11.1 deg/min (n = 9) has no stated window (METHODOLOGY, source-pack
    flag resolutions §2).

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
- the R1 converter passes its SITL acceptance test (its band is pre-registered with R1), AND §5b on the first real log;
- the R8 `mocap_align` on `RISI` passes its SITL self-test.

---

## 5b. Converter acceptance band (pre-registered 2026-10-12, before any real log)

The dataflash → FGO converter (`eval/bin2fgo.py`) is accepted on the FIRST real log, a verification sortie (B, H or
V), only if every test below passes. Until then no FGO row is scored. The band checks the converter against EKF3's OWN
inputs and the FC's own sensor records in the same log, so it needs no bag and no truth.

**Code and tests:**
- `eval/bin2fgo_accept.py --conv <out.npz> --bin <flight.BIN> --timing-json <sensor_timing.json>`;
- tests in `eval/bin2fgo_test.py`, which inject an axis-sign fault, a ROFH mismatch, a missing flow-sign test, a wrong
  loop rate and a 10 cm range error, and each is caught;
- SITL `cl_a_tex_half`: ACCEPTED (`eval/results/r1_converter/accept_sitl_cl_a_tex_half_2026-10-12.json`).

| test | what | bound |
|---|---|---|
| A1 | `LOG_REPLAY` | = 1 |
| A2 | `DSF` dropped blocks, whole log | = 0 |
| A3 | `RISI` samples dropped for flags; \|DVDT − DADT\| > 0.5 ms; DVDT within 0.5 ms of the frame spacing | 0; ≤ 0.1 % of samples; ≥ 99 % of samples |
| A4 | IMU frame rate (mean frame period) against `SCHED_LOOP_RATE` | within ± 2 % |
| A5 | the converter's raw IMU through the INS 2-pole filters (`INS_GYRO_FILTER`/`INS_ACCEL_FILTER`) against the FC's logged `IMU` record (same instance), sample by sample over the whole log (sync wiggles included) | best common lag within ± 10 ms; per-axis RMS ≤ 0.05 rad/s and ≤ 0.3 m/s²; correlation ≥ 0.95 on every axis whose record std > 0.1 rad/s / 0.5 m/s² |
| A6 | rest, [arming − 3 s, arming − 0.5 s], if still (gyro std < 0.05 rad/s) | \|specific force\| = 9.80665 ± 0.15 m/s²; \|gyro mean\| < 0.05 rad/s (else NOT TESTED, not a failure) |
| A7 | flow = EKF3's flow input: `OF` vs `ROFH` (counts; flowX/Y, bodyX/Y float32-identical; Qual) | exact |
| A8 | geometry: `FLOW_POS_*` vs `ROFH.posOffset`; `RNGFNDn_POS_*` vs `RRNI.pos_offset` | to 1e-6 |
| A9 | range vs the FC's `RFND` (same instance, Good), the RFND sample within 60 ms of each converter range emission | ≥ 50 pairs; median \|diff\| ≤ 0.02 m; p95 ≤ 0.05 m |
| A10 | flow sign and response: `eval/sensor_timing_from_log.py --window <a sync wiggle>` | gain > 0 on both axes and peak correlation ≥ 0.5 on both; without it: NOT accepted |

- **Reported, with no bound:**
  - the flow rate and inter-arrival percentiles;
  - the range update period;
  - the fraction with Qual > 0;
  - the initial-height source, and |init range − `RNGFNDn_GNDCLR`|.
- **ACCEPTED** = A1–A5 and A7–A10 pass, and A6 passes or is NOT TESTED.
- **Why these bounds:** the band is meant to catch CONVERSION faults.
  - A sign or axis error gives an RMS of the order of the signal (2–3 rad/s in a wiggle); a units error gives ~1000×; a
    stamp error gives a lag.
  - The A5 bounds leave room for what the filter replica does not model: the harmonic notch, and the `IMU` record's
    logging time. On SITL the residual is 0.2–0.4 mrad/s and the lag −1 ms.
- **If NOT accepted:**
  - the converter is fixed and re-run on the same log;
  - the fault, the fix and the re-acceptance are recorded (a METHODOLOGY entry) before any FGO row is scored;
  - the band itself is not changed after a real log has been seen, except by a dated amendment.
- **Separate from this band:** the SITL band FGO-from-BIN vs FGO-from-bag on the full `cl_a_tex_half` (plan R-f) is
  still open.

---

## 6. Flow and range timestamp rule: the capture delays (procedure fixed 2026-10-12; values [TBD-V])

Ruling 2026-10-10 item 2:
- **EKF3** keeps its own rule, as onboard: arrival − `EK3_FLOW_DELAY` − 50 ms (`flowTimeDeltaAvg_ms`/2) − 6 ms (half a
  filter step), clamped to the fusion horizon.
- **UKF port and FGO:** the best estimate of the TRUE capture time, from the real sensor's MEASURED rate and delay.
  - Flow: **arrival − d_flow**; range: **emission − d_range**.
  - d is defined as in the converter. For flow it is the FC arrival (`OF.TimeUS`) minus the END of the flow
    integration interval, the simulation's convention (the flow stamp was the newer camera frame).
  - **d_flow = [TBD-V] ms, d_range = [TBD-V] ms.**
- `EK3_FLOW_DELAY` on the vehicle (`rung1_template.parm`) is set from the sensor's documentation, not from d_flow. The
  two are reported side by side.

**The configuration.** The values live in ONE file per vehicle and sensor set, read strictly by the converter
(`eval/bin2fgo.py --delays-json`, `load_delays`; template `docs/rung1_capture_delays_TEMPLATE.json`):
- `delays_ms` {flow, range, imu = 0};
- `uncertainty_ms`;
- `measured_on` (each verification log and its sha256);
- `method`;
- `status`.

How it is used:
- **Result flights:** they are converted with `--result-flight`, which refuses anything but `status: PRE-REGISTERED`.
  The output JSON records the file's path, sha256 and status.
- **The UKF port** takes the SAME values (rounded to integer ms) as `UKF_FLOW_DCAP_MS` / `UKF_RNG_DCAP_MS` in Replay
  (port spec `docs/rung1_port_spec_capture_delay_xuko.md` §S1). The converter is given the same rounded values, so the
  two agree exactly.

**Procedure, fixed now, run on VERIFICATION logs only (B, H, V; never on a result flight):**
1. **Flow delay, measured per sync wiggle.** For each disarmed sync wiggle, found by `mocap_align`'s burst rule, and
   each bench rotation period (props off) where translation is ~0, run `eval/sensor_timing_from_log.py <log.BIN>
   --window T0 T1`. It cross-correlates the high-passed flow with the RISI gyro averaged over each flow interval.
   - Per window, the script's per-axis rule applies: if the axes agree within 5 ms, the correlation-weighted mean;
     otherwise the higher-correlation axis, flagged.
     - **Stated:** that rule was written after seeing the SITL result, so its SITL agreement (16.06 against 16.0 ms) is
       consistency, not independent validation.
     - The synthetic test is the independent one: 16.0 / 39.7 ms for d = 16 / 40 ms without capture jitter, and a
       −2.5 ms bias with 4 ms jitter.
   - A window whose peak correlation is < 0.5 on both axes is discarded, and counted.
2. **The flow value:** d_flow = the median over all retained windows. At least 4 windows are required, e.g. two wiggles
   on each of two logs; otherwise more verification is flown.
   - **Uncertainty** = max(half the range of the retained window estimates, 2.5 ms). The 2.5 ms is the known jitter bias.
   - The measured flow rate (median inter-arrival) and its percentiles are recorded.
3. **Range delay.** Use the climbs and descents of V (take-off and landing) and any vertical lifts of H. Run
   `--truth-tum <mocap_align TUM on the FC clock> --range-window T0 T1` per segment: the lag minimising the RMS of
   range against mocap height minus the lever, over moving samples (|dh/dt| > 0.1 m/s).
   - d_range = the median over at least 4 segments. One SITL climb gave an RMS of 3.6 cm, i.e. a coarse estimate, which
     is why several segments are needed.
   - **Uncertainty** = max(half the range of the segment estimates, the half-width of the lag interval where the pooled
     RMS ≤ 1.1 × its minimum).
   - The mocap → FC clock-map error (≤ ~1 ms on the RISI path, §8 step 2) is part of it.
4. **IMU:** d = 0 (the IMU is the time base).
5. **Record and fix.** The filled file is set to `status: PRE-REGISTERED` and committed. Its sha256, the values, the
   uncertainties and the logs go into a METHODOLOGY entry BEFORE any result flight is scored. After that the file is
   fixed.

**Implementation status:**
- the converter: DONE (`--delays-json`; the outputs are array-identical to the command-line form and to the
  pre-change converter on SITL);
- the UKF port option: SPECIFIED, not implemented (port spec §S1, including its regression: unset = byte-identical;
  `UKF_FLOW_DCAP_MS=66` = EKF3's rule at the defaults, byte-identical). It must pass that regression before scoring.

This differs from the simulation, where the UKF and the FGO used capture stamps from the camera pipeline. The
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
   - **Gyro source:** `RISI` (`--gyro-src RISI`, or `auto`).
   - **Fallback, pre-registered 2026-10-12 (`--gyro-src auto`):** when the log has no `RISI`, the ~25 Hz `IMU` record
     is used. It was re-validated on the sync wiggles (`eval/mocap_align_test.py`): about +0.3…+0.6 ms of bias,
     |max| < 1 ms, against |max| 0.26 ms for RISI. In addition, up to +2.5 ms comes from the record's logging time
     (one 400 Hz loop, not modelled): a bias of ≤ ~3.5 ms in all, i.e. ≤ 1.8 mm at 0.5 m/s.
   - A log without `RISI` cannot be replayed or converted, so it fails §3.3 item 2 for the EKF3, UKF and FGO rows.
     Only `EKF3_onboard` (`XKF1@0`) is then scorable, as a descriptive row.
   - The scorer records which gyro fitted the map.
3. **EKF3:** Replay (the fork's Replay binary; also the stock Replay if 4.7.0 flew) → the §5 gate → EKF3 read from the
   Replay output log as `XKF1@100`.
   - The log is read with `eval/df_reader.py`, NOT pymavlink: the fork's Replay output carries undeclared UKF records,
     §4.1.
   - The scorer refuses a log whose `XKF1@100` TimeUS sequence differs from `XKF1@0`'s.
4. **UKF port** (same Replay pass, `UKF_FLOW_DCAP_MS` / `UKF_RNG_DCAP_MS` from the §6 file) → `XUKO`, from the source
   the user rules on (§4.1: the Replay log once the port emits the FMT records, or `ukf_output.csv` via `--est-csv`).
5. **FGO:**
   - the converter acceptance (§5b) must pass on the first real log;
   - then the converter runs with `--result-flight --delays-json <§6 file>` → `fgo_replay.py` events mode → FGO TUM.
6. Scorer (R9): `eval/real_score.py --prereg docs/rung1_preregistration.json --mocap-align-json <flight>/mocap_align.json
   ...`: evo -a over W for all three; secondary metrics (§4.3, §4.4); §7 decisions. The scorer refuses a prereg with
   missing or unknown keys, a record other than the registered one, and a mocap_align JSON with non-default windows.
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
11. **Rangefinder minimum range:** if `RNGFND1_MIN` exceeds the resting height, the rangefinder reads "out of range
    low" on the ground.
    - **FACTUAL CORRECTION (2026-10-12):** this is not a change to any metric or criterion.
      - The draft said "EKF3 then uses `RNGFND1_GNDCLR`". That is wrong: at `7bac20cbcc` EKF3 pushes NO range sample
        for an `OutOfRangeLow` rangefinder and falls back to baro height (METHODOLOGY "The port geometry branch MERGED,
        Replay INSTALLED; U4 …", U4 FINDING).
      - EKF3's height on the ground is then baro, not `GNDCLR`.
    - **The UKF port** initialises from the first in-range sample, i.e. mid-climb, UNLESS the PORT rule of branch
      `u4-gndclr` (`53bac01636`, NOT merged or installed) is adopted. That rule: while disarmed and `OutOfRangeLow`,
      `max(GNDCLR, 0.05)` is used to initialise and as a ~5 Hz range sample, until arming. It is a port rule, not
      EKF3's.
    - **The FGO converter** initialises from the Good range at the end of levelling, else the first Good range before
      arming, else `RRNH.GCl` (= `RNGFNDn_GNDCLR`).
    - The rule used by each estimator is stated if this applies.

---

## 10. Open inputs (after sign-off; each needed before the item it blocks)

- **Supervisor (S1–S7 of the plan):** the board, the flow sensor and rangefinder, the mocap system and volume, the
  firmware, the floor, the compass variant, the safety pilot. The [TBD-S] values above follow from them.
- **User ruling, the `XUKO` source (§4.1),** and the port work it needs (port spec §S2). This blocks the UKF row.
- **The capture-delay port option (§6; port spec §S1)**, implemented and regression-tested. This blocks the UKF row.
- **The §6 delays file**, measured on verification logs and PRE-REGISTERED. This blocks the UKF and FGO rows.
- **§5b converter acceptance** on the first real log. This blocks the FGO row.
- **The §5 Replay bound**, confirmed or widened once on H/V logs. This blocks the EKF3 row.
- **The U4 port rule** (§9 item 11), only if the rangefinder minimum exceeds the ground clearance.
- **The R1/R7/R8/R9 tools** are built and tested offline (handovers `2026-10-11_r1_converter_mocap_scorer.md`,
  `2026-10-12_r1_scoring_items.md`). None has seen real data.

## 11. Sign-off

| | name | date | changes requested |
|---|---|---|---|
| user | signed off (METHODOLOGY "RULINGS (user, 2026-10-12)", item 2) | 2026-10-12 | evo -a SE(3) primary; `XUKO` as the UKF record; ADD cross-track drift per minute and heading drift in deg/min (UNALIGNED) as secondary metrics before any data (§4.4) |
| supervisor (informed) | | | |

- **The files in force:**
  - this file;
  - `docs/rung1_preregistration.json`, sha256 `884ff35171a1f7679d6aec5b55ed99f0807c69bdfac5bc761778268afda0ed19` at
    this commit. Every score file carries the JSON's sha256.
- **The JSON differs from the draft JSON** in `name`, `status`, `rationale` (two entries) and the new `secondary`
  section. The scored sections are unchanged.
- **The METHODOLOGY entry** that records the commit and this sha256 is the user's or the coordinator's to write; this
  stage does not edit METHODOLOGY.
- Any later change is a dated amendment, made before the affected data are scored.
