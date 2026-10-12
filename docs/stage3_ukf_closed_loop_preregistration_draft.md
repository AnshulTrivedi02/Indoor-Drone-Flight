# Stage 3 (UKF-only closed loop): DRAFT pre-registration for the user's sign-off

**Status: DRAFT, written 2026-10-12 (stage `2026-10-12_port_merge_u4_drafts`). NOT in force.** Nothing has flown on
the fork, and no real log exists. It must be signed off before the first stage-3 RESULT sortie. Verification sorties
may fly before it, under their own cards (§2). The U10 band it relies on (`docs/u10_replay_gate_band_draft.md`) must
be signed off earlier, before rung-1 day 3.

Implements:
- plan `docs/realflight_plan_copter.md` §4 (U-d / U14), which incorporates U-d0;
- costing `docs/ukf_only_closed_loop_costing.md` §§6–9 and §12;
- METHODOLOGY "STANDING RULE (user, 2026-10-10): verification flights are SHORT and never result data";
- METHODOLOGY "RULINGS (user, 2026-10-12)", items 1–2: the metric family of the signed-off rung-1
  pre-registration, including the two UNALIGNED drift-rate secondaries.

Labels:
- **[V]** verified;
- **[E]** an estimate;
- **[TBD-S]** supervisor or hardware input, fixed before the first result sortie;
- **[TBD-V]** fixed once from VERIFICATION or rung-1 data, before the first result sortie;
- **[RULING]** a choice for the user.

---

## 1. What flies, and what stage 3 tests

- **The vehicle:** the rung-1 vehicle (H743 ArduCopter, its own flow sensor and downward rangefinder on the FC).
- **The firmware:** the fork, built by `tools/build_board_fw.sh <BOARD>` from a NAMED, MERGED commit, recorded by
  commit and `.apj` md5. It contains:
  - `rung1-geometry` (merged into `ukf-jitter-fix` 2026-10-12);
  - `board-h743`;
  - U4 if the rangefinder minimum exceeds the resting clearance;
  - any fix the gates below require.
- **The configuration:**
  - `AHRS_EKF_TYPE 12`, `AHRS_UKF_ENABLE 1`, `AHRS_UKF_TFAIL 0`; EKF3 runs in shadow and is logged;
  - `LOG_REPLAY 1`, `LOG_DISARMED 1`;
  - the U7 failsafe parameter file (`FS_EKF_ACTION 1`, `FS_GCS_ENABLE 5`, `FS_GCS_TIMEOUT` from the measured link
    gap, the RC and battery failsafes);
  - `check_parm.py` in its stage-3 mode.
- **The watcher:** on the ground laptop, with live mocap (F1) and a MAVLink link to the FC (fail-closed: no
  heartbeat → GCS failsafe → LAND).
- **A safety pilot** holds the RC throughout, with an RC override that wins over every autonomous mode (`FS_OPTIONS`
  bit 4; bench B10).
- **The claim is a FEASIBILITY claim:** the thesis UKF, running onboard as the active estimator on real sensors, flies
  the pre-registered profile safely within the stated bands.
  - It is **not an accuracy comparison against EKF3**. The UKF's own error shapes the flown trajectory, so the EKF3
    shadow on the same flight is not like-for-like (§4.3).

## 2. Sorties: verification or result-producing (classified in advance)

**Verification sorties are never scored and never reused as result data, whatever they show.**

| sortie | class | length (the shortest that exercises it) | why that length suffices | its logs are used for |
|---|---|---|---|---|
| **P: bench P1–P10** (props off) | verification | each ≤ 1–2 min | each checks one fact (boot, readback, P4 backends off = EKF3, P5 TFAIL refusal normal + forced, P6 shadow, P7 stack, P8 CPU `PM`, P10 `MEMINFO`) | pass/fail of the bench items |
| **F: forced invalidity on the bench** (armed, motors safe) | verification | ~1 min per trigger | one trigger shows the `thesis_nav_check` → LAND mode change and its timing (S-A2b) | S-A2b on the real FC; the LAND mode change |
| **W: watcher, link and RC** | verification | ≤ 2 min each | heartbeat withdrawn → LAND; RC override wins; the link's worst gap | `FS_GCS_TIMEOUT`; card sign-off |
| **H3: hand-carried in the volume** (disarmed; type 12 active, nothing steers) | verification | ~2 min: wiggle, one carried out-and-back leg at flight height, wiggle | the output is computed exactly as in flight; one leg checks the flow sign, the UKF against mocap, the watcher live on mocap, and the IR check | the onboard `XUKF` replayed (S9); the U4 initialisation (S8) |
| **T: tethered hovers** | verification | EKF3 hover ≤ 1 min; then UKF-flying hovers ≤ 1 min each; one forced invalidity; one flow occlusion | each tests one transition on a tether | S-A1–S-A3 on the tether; the land detector trips (F2) |
| **V3: first free hover, UKF flying** | verification | take-off, hover 30 s, one 1 m leg and back at ≤ 0.2 m/s, land (~1.5 min airborne) | shows the UKF holds and moves the vehicle with the right sign; nothing more | go/no-go for the result sorties; the [TBD-V] values of §6 |
| **R1…Rn: result sorties** | **result-producing (this document)** | the §3 profile (~2 min airborne) | set by what the result needs (§3) | scoring (§4, §7) |

A result sortie aborted before its window ends is NOT re-labelled as verification. It is a result sortie, excluded
under §3.3 or failed under §7, and reported.

## 3. Result sorties

### 3.1 Profile [RULING: pilot-flown LOITER or scripted GUIDED]
- **Option A, scripted GUIDED.**
  - Every sortie is identical (setpoints from a script), which suits n-sortie statistics.
  - It needs the H10 takeover guard and F4 in the flight script (plan U-f, 1–2 d): no LAND when the FC is in a pilot
    mode or already LANDing, the FC system ID pinned, and the mode map from the FC heartbeat.
- **Option B, pilot-flown LOITER.** It needs no U-f; the UKF holds position and the pilot's sticks command velocity.
  The legs are less repeatable, and speed is the pilot's target.
- **Proposed default: A if U-f is done and bench-tested before the first result sortie, otherwise B.** The choice is
  recorded before the first result sortie and does not change during the set.

**The profile** (same steps in both options; lengths fixed from the volume **[TBD-S]** before R1):
1. Disarmed, logging: the sync wiggle (~5 s), then set down on the marked start spot.
2. Arm. Take off to **h = [TBD-S] m**: 1.0–1.5 m, and at least `RNGFND1_MIN` + 0.5 m.
3. **Hover 30 s** over the start spot (the take-off detector and flow aiding; the window starts at t_to + 25 s).
4. **One out-and-back leg** of **L = [TBD-S] m** (proposed 2–3 m) at **0.2–0.3 m/s**, a 5 s pause at the far end,
   back to the start spot. Cruise ~25–35 s.
5. **Hover 10 s.** Land; disarm.
6. Disarmed, logging: the second sync wiggle. Stop logging.

**Why this length (shorter than rung 1's two laps):**
- The vehicle steers on the UKF's own position, so the UKF's unaligned drift becomes PHYSICAL displacement.
- With no heading source, the UKF's yaw drifts.
  - SITL, no heading: shadow and offline |drift| 3–70 deg/min, typically 24–30 deg/min (METHODOLOGY D9
    pre-registration).
  - The jitter-corrected no-heading closed loop (`cl_ukf_a_tex_half_v2`) touched the west wall of the 20 m corridor at
    cruise +165.9 s, inside its pre-registered window.
- A position error from yaw grows like L·Δψ. One short leg keeps the excursion inside a mocap volume while still
  exercising hover, acceleration, cruise, stop and return. It is NOT a long-duration test (§9).
- About 2 min airborne (plus the wiggles) per sortie.

### 3.2 Number of sorties
- **n = 5 result sorties**, one floor, one day where possible, in sequence. One spare is allowed, used only to replace
  a sortie excluded under §3.3 (at most 6 flown). This mirrors rung 1.
- **No sortie is added, dropped or re-flown because of what the UKF showed.** The spare is flown on §3.3 reasons only,
  decided from logs and mocap before any scoring of that sortie.

### 3.3 Exclusions (from logs and mocap only, BEFORE scoring)
1. The pilot aborted or took over for a reason NOT attributable to the UKF, recorded at the time: traffic in the
   volume, a mocap-system fault, a battery swap, an RC or radio fault.
   - **A takeover or watcher LAND caused by the vehicle's behaviour is NOT an exclusion. It is a C1 failure (§7).**
2. The log is incomplete (rung-1 §3.3 item 2: `DSF.Dp` > 0 in the window, an `RFRH` gap > 50 ms, missing
   `RISI`/`ROFH`/`RRNI`).
3. Mocap lost the rigid body for > 0.5 s cumulatively inside the window, or a sync wiggle is missing.
4. The mocap clock map fails (residual above rung 1's [TBD-V] bound).

## 4. Metrics (the rung-1 family, adapted to a closed loop)

All on the FC clock. The window **W = [t_to + 25 s, t_ld − 5 s]** comes from mocap only (rung-1 §4.2 rule; refused if
shorter than 20 s).

### 4.1 Closed-loop criteria (these decide the result; §7)
- **C1 completion:** the profile completes under UKF control with all of:
  - no pilot takeover or watcher LAND caused by the vehicle's behaviour;
  - no `thesis_nav_check` / EKF failsafe event;
  - no crash.
  The landing is commanded (LAND/RTL-free procedure as carded), not a failsafe.
- **C2 physical excursion:** the maximum horizontal distance of the mocap position from the commanded path (the
  start spot during hovers, the leg segment during the leg) over W, ≤ **E_max** (§6).
- **C3 validity:** the UKF's `horiz_pos_rel` (`XUKF`/`XUKO` `SS` bit 3) set and `Healthy` on 100 % of W; no
  `XUKS.EvO` (queue overflow).
- **C4 smoothness** (as the SITL B4/B5):
  - the maximum mocap lateral speed during the hovers ≤ **0.25 m/s**;
  - the gyro rms (roll / pitch / yaw) in the cruise ≤ **2 × the rung-1 EKF3-flown value** of the same profile segment
    **[TBD-V]**, from the rung-1 result flights.
  - The SITL B5 band came from a SITL profile, so it does not transfer.

### 4.2 Estimation metrics (reported per sortie; descriptive; the rung-1 family)
- **Primary estimation metric:** evo -a SE(3) (`t_max_diff` 0.05) of the onboard **`XUKO`** against mocap over W.
  This is the signed-off rung-1 metric and UKF record.
- 4-DoF ATE over W.
- Start-aligned drift (rung-1 §4.3 rule).
- **Cross-track drift per minute** and **heading drift in deg/min, UNALIGNED** (ruling 2026-10-12 item 2): the onboard
  `XUKO` against mocap, with a linear fit over W. These are comparable with the simulation's corridor drift rates and
  with the U10 gate's replayed rates.
- `XUKF` (horizon) as a secondary row.
- Acceptance fractions (flow X/Y, range); the D15 replaced-flow count; the take-off-kick yaw step.

### 4.3 Diagnostic only (no decision attached)
- **The EKF3 shadow** (onboard `XKF1@0`) scored the same way.
  - **Not like-for-like:** the flown path is the UKF's, and EKF3 neither steers nor shapes it. In rung 1 the reverse
    held.
  - Any UKF-vs-EKF3 number from stage 3 is labelled "EKF3 shadow on a UKF-flown trajectory".
- **Replay fidelity on the board:** the fork's Replay of each stage-3 log against the onboard `XUKF`, with the U10 G6
  bands. This is the first real Replay-vs-board comparison if rung 1 flew stock firmware.

## 5. Safety gates (ALL passed and recorded before the first free flight, i.e. before V3)

| # | gate | pass | source |
|---|---|---|---|
| S1 | **SITL V1–V7** on the MAVLink camera-flow path with the exact source commit to be flown (SITL build) | each as pre-registered in the costing §6 table, plus the land detector trips after LAND (F2) in V3/V4. **V1 must show the D18 swap active** | plan §4.2 |
| S2 | **U10 Replay gate PASS** on the rung-1 logs | `docs/u10_replay_gate_band_draft.md` §4 | U-d0 |
| S3 | **Bench P1–P10** on the flashed image | incl. **P5: arming refused with `AHRS_UKF_TFAIL` ≠ 0, normal AND forced**; P4 backends off = EKF3 | `docs/board_firmware_plan.md` §5 |
| S4 | **Forced invalidity → LAND** on the bench, then on the tether | `thesis_nav_check` text + mode LAND (reason EKF failsafe) within **0.1 s** of TFAIL (S-A2 (a) band); on the tether S-A1 (attitude ≤ 3° / yaw ≤ 5°) and S-A3 (disarm ≤ 40 s, tilt ≤ 15°, horizontal displacement ≤ 1.5 m, touchdown ≤ 1.0 m/s) | METHODOLOGY H safety criteria |
| S5 | **Aiding-loss timing S-A2b on the FC:** flow occluded → LAND | within **5.5 s of the last flow received by the FC** (pre-registered 2026-10-11) | ruling 2026-10-11 |
| S6 | **Watcher heartbeat withdrawn → LAND** within `FS_GCS_TIMEOUT` (MAVLink path; first real test) | as carded | W cards |
| S7 | **RC override wins** over GUIDED/LOITER/LAND; F6 fixed (the watcher stops re-sending LAND once the FC shows LAND or a pilot mode) | B10 on the vehicle; F6 offline tests + 83 `realflight` tests | U-a |
| S8 | **U4 on the vehicle** (only if `RNGFND1_MIN` > the resting clearance): the UKF initialises on the ground from `RNGFND1_GNDCLR` (`UKF: rangefinder below minimum on ground` text) and arms in type 12 | as stated | U-b |
| S9 | **Hand-carried H3:** the onboard `XUKO` against mocap is sane (the flow sign is correct: the UKF moves the right way on every carried leg); the onboard `XUKF` replayed with the U10 G6 bands **[TBD-V]** | as stated | §2 |
| S10 | **The land detector trips** after a commanded LAND under type 12 (F2), on the tether; the card line "after any automatic LAND, the SP disarms if the FC has not disarmed within 5 s of touchdown" | as stated | R-g, U-g |
| S11 | **Battery and RC failsafes** read back; G6 arming procedure; the watcher system ID set | readback | U-e, U-k |
| S12 | **EKF origin set and VERIFIED at every boot** (ruling 1, 2026-10-12) | the origin sent (or set by AHRS from `AHRS_ORIGIN_*`) only after every EKF3 core has reported initialised; a `GPS_GLOBAL_ORIGIN` received with the lat/lon set; an `ORGN` record in the log before the ARM event. NO ARMING without it | `docs/rung1_flight_cards.md` §1a, D10 |
| S13 | **F7 yaw check** (ruling 2, 2026-10-12): the watcher refuses arming unless the FC yaw agrees with mocap within 5° for ≥ 1 s; informational once armed | real bench B11 (a)–(d) PASS; SITL `wbench3_f7` | `docs/real_flights_plan.md` §7.2 B11 |

Any gate failing stops the programme at that gate. A fix means a new image, its readback, and the gates it affects
re-run (as a minimum S3 and S4).

## 6. Predictions and the excursion band E_max (formula pre-registered now; values fixed from rung-1 data before R1)

- **The heading drift ψ̇** = the largest |heading drift rate| (deg/min) of the replayed UKF over the U10-gated rung-1
  flights (U10 §5).
- **The velocity-bias drift v_b** = the largest |cross-track drift per minute| over the same flights, in m/s.
- **Predicted maximum physical excursion over the sortie** (duration T from take-off to the end of the leg, ~70 s):

  **E_pred = L · sin(ψ̇ · T / 60 · π / 180) + v_b · T + 0.10 m**, with ψ̇ in deg/min, T in s, v_b in m/s and L in m
  - L · sin(ψ̇ · T): the far-end displacement from a yaw error;
  - v_b · T: dead-reckoned velocity bias;
  - 0.10 m: hover hold and mocap [E].
- **E_max = max(1.5 · E_pred, 0.30 m)**, and it must also satisfy E_max ≤ (watcher-box half-width − 0.5 m)
  **[TBD-S]**.
  - **If it does not fit, the profile is shortened** (L or the cruise reduced) until it does. This is recorded before
    R1.
  - **If no profile with L ≥ 1 m fits, stage 3 does not fly result sorties.** It is reported as such.
- **Point predictions recorded before R1:** E_pred; the onboard heading drift ≈ the U10 median (deg/min); the evo -a of
  `XUKO` ≈ the U10 median replayed value scaled to the shorter window. These are reported against the results, with no
  decision attached.
- **[TBD-V] check on V3:** the V3 excursion is compared with E_pred. **If V3 exceeds E_max, no result sortie is
  flown** until the cause is found. That is a verification outcome, and E_max is not widened because of it.

## 7. Decision rules

**Per sortie: PASS if C1, C2, C3 and C4 all hold.**

**The set:**
- **"The onboard UKF flew the profile safely on these flights"** is claimed ONLY if **every usable result sortie
  passes** and at least 4 are usable. One failing sortie fails the set.
- **Any C1 failure STOPS the set at once.** No further result sortie is flown until the cause is found and reported.
  A resumed set is a new, dated set; the failed one is reported as failed.
- With fewer than 4 usable sorties: **no claim**; the per-sortie values are reported (descriptive only).
- **Estimation metrics (§4.2):**
  - reported per sortie with mean ± 95 % t-interval (df = n − 1);
  - **no ordering claim** against EKF3 (not like-for-like, §4.3) or against the rung-1 replay (a different flight);
  - **sim-to-real** is stated only as the drift-rate comparison (deg/min and cross-track per minute against the
    simulation's corridor rates), side by side and with no decision rule.
- **Reported regardless of outcome:**
  - every result sortie's C1–C4 and §4.2 values, the excluded sorties and their reasons;
  - the predictions against the results;
  - every abort.

## 8. Abort criteria (in flight; the pilot takes over, or the watcher commands LAND)

The safety pilot aborts (takeover to ALT_HOLD/STABILIZE, then land) on any of:
1. the vehicle leaves the watcher box, or is predicted to within 1 s (the watcher LANDs automatically on a breach);
2. tilt > 25°, an oscillation, or an uncommanded climb or descent > 0.3 m;
3. lateral speed > 0.5 m/s with no commanded leg;
4. any `thesis_nav_check`, EKF failsafe, GCS failsafe or battery-failsafe text, or a mode change not commanded (the
   automatic LAND proceeds; the pilot only intervenes if it is unsafe);
5. mocap or watcher loss (the watcher fails closed → LAND);
6. anything the pilot judges unsafe. **The pilot's judgement is never overridden by this document.**

Every abort is logged with its time and reason. Whether it counts as an exclusion (§3.3 item 1) or a C1 failure is
decided from the log and the recorded reason, BEFORE any estimation metric of that sortie is computed.

## 9. Stated limits (next to every stage-3 result)

1. **Feasibility, not accuracy ordering:** one vehicle, one floor, one day, n ≤ 5, short sorties in a mocap volume.
2. **No heading source:** yaw drifts (SITL: tens of deg/min with no heading). The profile is kept short so that the
   physical excursion stays inside the volume. Long-duration closed-loop behaviour is not tested.
3. **The flow sensor is not the thesis camera pipeline** (rung-1 limit 1). If it pairs its own gyro (FLOW_TYPE 1, 3,
   6, 10), the closed-loop derotation uses that gyro with no UKF bias, pending the U-h ruling.
4. **The closed-loop derotation is the identity rule** (type 12: the UKF's own `gyro + drift`). The U10 gate tested
   the swap path on EKF3-flown logs.
5. **The aiding-loss response is a 5 s dead-reckoning interval, then LAND** (`AID_TIMEOUT_MS`; S-A2b). The watcher box
   is sized for it.
6. **The vertical hold** (15 s on height and attitude after a position loss) and the rangefinder-loss behaviour are
   tested in SITL (V5) and on the tether only.
7. **Single-lane UKF:** no IMU redundancy. The EKF3 shadow is logged.
8. **Firmware:** the fork (based on `7bac20cbcc`), not stock. The board's numerics differ from SITL's (no
   bit-identity).
9. **If U4 is in use:** the on-ground height is `RNGFND1_GNDCLR`, a port rule. EKF3 at the pinned commit falls back to
   baro there instead, and the UKF has no baro. After arming, no range is fused until the sensor reads above its
   minimum. If take-off follows arming by more than 5 s, the UKF's vertical flags lapse (`RNG_TIMEOUT_MS`) until it
   does. **RULED 2026-10-12 (ruling 7):** a flight-card rule now, on every sortie: take off within 5 s of arming
   (`docs/rung1_flight_cards.md` §5). The proper fix (extending the GNDCLR range to "armed but take-off not yet
   detected") is deferred to the closed-loop work.

## 10. Open inputs before sign-off

- **Supervisor [TBD-S]:**
  - the volume (sets L, h and the watcher box);
  - the board and its IMU count;
  - the flow sensor (FLOW_TYPE) and the rangefinder (minimum against the resting clearance → U4);
  - the mocap protocol (F1);
  - the safety pilot.
- **Rulings [RULING]:**
  - option A or B (§3.1);
  - n = 5 (+1 spare);
  - the C4 factor of 2;
  - E_max's 1.5 factor and 0.30 m floor;
  - ~~the take-off-within-5-s card line or the U4 extension (§9 item 9)~~ RULED 2026-10-12: the card line now, the
    extension deferred;
  - the own-gyro FLOW_TYPEs (U-h);
  - the multi-IMU rule (U-i).
- **From rung 1 / U10 [TBD-V]:** ψ̇, v_b, the C4 gyro reference, the mocap clock-map bound.

## 11. Sign-off

| | name | date | changes requested |
|---|---|---|---|
| user | | | |
| supervisor (informed) | | | |

Once signed, this file is copied to `docs/stage3_ukf_closed_loop_preregistration.md` (status PRE-REGISTERED). A
METHODOLOGY entry records the commit. Any later change is a dated amendment, made before the affected sorties are flown.
