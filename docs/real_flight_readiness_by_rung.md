# Real-flight readiness, re-costed by RUNG (ArduCopter only)

Status: PLANNING ONLY. Written 2026-10-10 on `fwd-camera` at `91e87c9`, implementing the ruling "RULINGS (user,
2026-10-10, SUPERSEDING …): real flights built as RUNGS". Nothing was run or built to write it.

> **UPDATED 2026-10-12** (ruling "ArduCopter confirmed for the real vehicle (for now)"):
> - **Copter only.** QuadPlane is DROPPED from the active plan. `docs/quadplane_costing.md` is kept as **reference
>   only**, and the QuadPlane mentions below are marked "(QuadPlane: dropped, reference)".
> - **The consolidated plan, with timelines from hardware arrival, is `docs/realflight_plan_copter.md`.** It covers
>   rung 1 and the **UKF-only closed loop** (the onboard UKF steering with the vehicle's own flow sensor and
>   rangefinder; costing `docs/ukf_only_closed_loop_costing.md`), which is now the planned first closed loop. The
>   Pi-based rungs 2 and 3 below stay as costed; rung 2 stays PARKED (ruling 2026-10-11).
> - **A status column** (as of 2026-10-12) is added to every table. "→ plan §x" points into the consolidated plan.
> - **§5's calendar to 23 Oct is SUPERSEDED** by the hardware-relative timelines of the consolidated plan (§3.1,
>   §4.1). The "SIM after 16 Oct" restriction is also superseded: short verification flights are allowed now (ruling
>   2026-10-11).

It re-costs every row of `docs/real_flight_readiness.md` (60 rows, IDs A1–I4), plus the watcher gaps G1–G11 of
`docs/real_flights_plan.md` §7.2 and the new rung-1 items R1–R15 of `docs/minimal_real_flight_plan.md`.

## The rungs

- **Rung 1:** a minimal logging flight. Stock firmware; the vehicle's own flow sensor and rangefinder on the FC; a pilot
  (or EKF3) flies; `LOG_REPLAY` and mocap. EKF3 and the UKF port run via Replay, the FGO via the converter. Costed in
  `docs/minimal_real_flight_plan.md`; scheduled in `docs/realflight_plan_copter.md` §3.
- **UKF-only closed loop (rung 3, quickest form):** the fork on the board, the onboard UKF steering, the vehicle's own
  sensors, no Pi. Scheduled in `docs/realflight_plan_copter.md` §4.
- **Rung 2:** open loop with OUR pipeline. Pi, camera flow, forward camera (only once verified); EKF3 flies; the UKF and
  FGO run alongside (offline by default; ruling Q6: an offline-only FGO is acceptable). **PARKED.**
- **Rung 3 (full):** closed loop. Board firmware with the UKF/FGO backends, the UKF/FGO steering, the full watcher, and
  the safety tests.

## Column key

| column | meaning |
|---|---|
| **rung** | The first rung that needs the row. "—" means no rung needs it as currently scoped. "1→2" means rung 1 needs a reduced form and rung 2 the full form. **"U"** marks rows the UKF-only closed loop also needs. |
| **kind** | **SW** = software or paper only; it can start NOW with no hardware. **HW** = needs the vehicle, sensors, Pi or mocap. **SW+HW** = code now, then a hardware check. **SIM** = needs the simulator (short verification flights are allowed now, under the locks). |
| **effort** | [E], one person, "d" = a working day. Taken from the readiness row unless re-costed here. Where rung 1 needs only part of a row, both parts are given. |
| **status** | As of 2026-10-12. DONE / BUILT (not merged or installed) / DRAFT / OPEN / WAITS (on hardware) / PARKED / DROPPED. |

Hardware identities (FC board, flow sensor, rangefinder, camera(s), Pi, mocap) come from the supervisor and are inputs.

---

## 1. Rung 1: shortest path first

These are the items rung 1 needs, in dependency order. For details see `docs/minimal_real_flight_plan.md` §5; for the
remaining work and the timeline see `docs/realflight_plan_copter.md` §3.

| order | ID(s) | item | kind | effort | status (2026-10-12) |
|---|---|---|---|---|---|
| 1 | R10, H9(r1) | Rung-1 pre-registration: profile, n, window, metrics, Replay tolerance, converter band | SW | 0.5 d | **DRAFT**, awaiting sign-off (→ plan R-a) |
| 2 | R1, G11(r1), C7(r1) | Converter BIN → FGO inputs, geometry overrides (defaults unchanged), SITL acceptance test on `cl_a_tex_half` | SW (+1 light replay) | 3–4 d | **DONE**, merged (`dde0061`); the full-flight acceptance band OPEN (→ R-f) |
| 3 | R2, R3, C7(r1) | UKF port: real geometry and flow delay from DAL/params, byte-identical on SITL; Replay rebuild; CSV → TUM | SW | 0.75–1.25 d | **BUILT** (`rung1-geometry` `16535f9a29`), NOT merged or installed; E5 post hoc (→ R-b); CSV → TUM DONE |
| 4 | R8, I3, I4(r1) | `mocap_align` on `RISI` (400 Hz, pre-filter), re-self-test | SW | 0.5 d | **DONE** (wiggle windows, masking) |
| 5 | R9 | Scorer `real_score.py` (pre-registered window, evo -a, start-aligned drift) | SW | 1–1.5 d | **DONE**; `XUKO` in Replay to check (→ R-d) |
| 6 | R11, H5, H6(r1) | Flight cards; RC override switch; FC altitude fence (+ optional circle fence with an EKF origin) | SW | 1 d | **DRAFT**; F2 line to add (→ R-g) |
| 7 | R6, C1, C2, C3, C6(r1), I1 | Real-sensor parameter template (draft SW now), then bench readback, `DSF`, compass arming check | SW+HW | 1.5 d | template + `check_parm.py` **DONE**; values WAIT (sensors) |
| 8 | G1a, R5 | Firmware: pinned `7bac20cbcc` from a clean checkout (or stock 4.7.0), flash, rollback | SW+HW | 0.5–1 d | build **READY** (`tools/build_board_fw.sh <B> --ref 7bac20cbcc --without`); WAITS (board, S6) |
| 9 | A1, A2, C5, A8 | Vehicle flying with its flow sensor and rangefinder on the FC (supervisor's vehicle) | HW | **0 d if already flying**; otherwise 3–6 d | WAITS |
| 10 | R12, D3(r1), D4(r1), D5(r1) | Bench (props off): flow orientation (`OF.body*` against `flow*` signs), rangefinder, mount offsets, `EK3_FLOW_DELAY` from the datasheet | HW | 0.5–1 d | WAITS |
| 11 | R7, I3 | Mocap recorder/adapter (Motive or Vicon export → CSV, Z-up) | SW+HW | 0.5–1.5 d | recorder **DONE**; vendor forwarder WAITS (mocap system) |
| 12 | R4 | EKF3 Replay: 0 d if pinned, 0.5 d stock Replay if 4.7.0; `check_replay.py` acceptance on the first real log | SW+HW | 0.5–1 d | WAITS (first real log) |
| 13 | R13, H7, H4(r1) | Hand-carried check in the volume, with the whole offline pipeline run the same day (disarmed: EKF3 stays on-ground, so flow aiding is first tested in the first hover) | HW | 1 d | WAITS |
| 14 | R14 | Flight day(s): first hovers, then n = 3–5 (+3 over a plain sheet) | HW | 1–1.5 d | WAITS |
| 15 | R15 | Offline runs, scoring, METHODOLOGY entry | SW | 1 d | WAITS |

**Rung 1 total (original costing):**
- software that can start now: 7.5–10 d (agents); **remaining 2026-10-12: about 3–4.25 d** (plan §3.2);
- hardware and on-site work: **5–8 d**;
- **12.5–18 person-days in all.**
- **Timeline: 6 working days from hardware arrival** (+2 contingency; +3–6 d if the vehicle is not already flying).
  See plan §3.1.

~~**Verdict for rung 1: FITS ONLY IF** an already-flying H7 vehicle with its flow sensor and rangefinder is available by
about 16 Oct, and mocap time by about 19–21 Oct (calendar §5).~~ Superseded: rung 1 finishes by Fri 23 Oct only if
hardware arrives by Thu 15 Oct (plan §0).

---

## 2. Every readiness row by rung

### A. Vehicle, sensor drivers and bridges

| ID | component (short) | rung | kind | effort | note | status |
|---|---|---|---|---|---|---|
| A1 | Airframe, FC, sensors assembled | 1→2, U | HW | r1: 0 d (supervisor's flying vehicle) or 2–4 d; r2: +1–2 d Pi, cameras, FC↔Pi UART | | WAITS |
| A2 | Baseline tune, hover learn, notch | 1, U | HW | 0 d if already flying; else 1–2 d | | WAITS |
| A3 | Downward-camera capture on the Pi | 2 | HW (driver choice SW) | 1–2 d | U4 | PARKED |
| A4 | `flow_tracker.py` on the Pi | 2 | SW+HW | SW now 0.5 d (focal length from calibration, `use_sim_time` off); HW timing 1 d; +3–5 d if C++ is needed | | PARKED |
| A5 | `flow_bridge.py` on the real link | 2 | SW | 0.5 d | lateral sign re-checked at D5 | PARKED |
| A6 | Forward camera + C++ heading on the Pi | 2 (only if flown) | HW | 1–2 d native run + capture [E] | supervisor rule: fly only once verified | PARKED |
| A7 | Wall-tag detector → ExtNav | 2/3 (P-HOLD only) | SW+HW | 1 d + D7 | | PARKED |
| A8 | Rangefinder on the FC (native driver) | 1, U | HW | 0.5–1 d (0 d if already fitted) | U6 | WAITS (sensor) |
| A9 | FC `DISTANCE_SENSOR` → ROS republisher | 2 | SW | 0.5 d | rung 1 uses `RRNI` offline | PARKED |
| A10 | `HIGHRES_IMU` 333 Hz over a real UART | 2 | SW+HW | SW 0.25 d; bench 1 d | rung 1 uses `RISI` offline | PARKED |

### B. MAVLink link, ports, clocks

| ID | component | rung | kind | effort | note | status |
|---|---|---|---|---|---|---|
| B1 | FC↔Pi link + router replacing the SITL UDP ports | 2 | SW+HW | SW config 0.5 d; HW 0.5–1 d | the UKF-only loop needs only a GCS link (telemetry radio or Wi-Fi) for the watcher | PARKED |
| B2 | FC↔Pi clock map (D25) on hardware | 2 | HW | 0.5 d | rung 1 has one clock (FC `TimeUS`) | PARKED |
| B3 | Measured link latency | 2 (report), 3 (feeds H2) | HW | 0.5 d | UKF-only: the telemetry link's worst gap instead (plan §4.1 day 8) | PARKED |
| B4 | Pi time base, `use_sim_time` off | 2 | SW | 0.5 d | | PARKED |

### C. Parameter files

| ID | component | rung | kind | effort | note | status |
|---|---|---|---|---|---|---|
| C1 | Core real-FC parameter file | 1, U | SW+HW | in R6 (1.5 d) | never `AHRS_EKF_TYPE 10` | template DONE; values WAIT |
| C2 | Rangefinder parameters | 1, U | SW+HW | in R6 | `RNGFND1_GNDCLR` (not `GNDCLEAR`) | template DONE; values WAIT |
| C3 | Flow parameters (`FLOW_TYPE` per sensor; `FLOW_POS_*`, `ORIENT_YAW`, `EK3_FLOW_DELAY`) | 1, U | SW+HW | in R6 | rung 2 sets them again for camera flow (`FLOW_TYPE 5`) | template DONE; values WAIT |
| C4 | ExtNav parameters | 2/3 (P-HOLD) | SW+HW | 0.5 d | after D4, D7 | PARKED |
| C5 | `MOT_THST_HOVER`, gains | 1, U | HW | in A2 | | WAITS |
| C6 | INS filters, notch (recorded, no retune) | 1, U | HW | 0.5 d | the group delay matters to `mocap_align` only for `IMU`, not `RISI` | WAITS |
| C7 | Geometry constants in three implementations | 1→2 | SW | r1: in R1/R2 (Python FGO overrides, port reads DAL); r2/3: C++ `factors.h`, `fgo_core.cpp:69` + equivalence re-runs 1–3 d | defaults unchanged during the sim freeze | r1 DONE (converter) / BUILT (port); C++ PARKED |
| C8 | Fork parameters (`AHRS_EKF_TYPE 12/13`, `TFAIL 0`) | 3, U | SW | 0.25 d (readback list) | UKF-only: the real-FC failsafe file (plan U-e) | OPEN |

### D. Calibration and re-validation

| ID | component | rung | kind | effort | note | status |
|---|---|---|---|---|---|---|
| D1 | Downward-camera intrinsics | 2 | HW | 0.5 d | tool exists | PARKED |
| D2 | Forward-camera intrinsics, resampling | 2 (if flown) | HW | 0.5–1 d | tool exists | PARKED |
| D3 | Extrinsics / lever arms | 1→2, U | HW | r1: 0.5 d (flow sensor, rangefinder, mocap markers, tape measure); r2: +1–1.5 d cameras | | WAITS |
| D4 | Sensor–FC time offsets | 1→2, U | HW | r1: 0 d (datasheet `EK3_FLOW_DELAY`); r2: 1 d bench (camera) | d_flow/d_range measured on verification logs (`eval/sensor_timing_from_log.py`) | WAITS |
| D5 | Flow sign/axis on the real mount | 1→2, U | HW | r1: 0.5 d (sensor orientation, in R12/R13); r2: 0.5 d (camera) | | WAITS |
| D6 | VP heading re-validation (new pre-registration) | 2 (if forward camera flown) | SW+HW | 2–4 d | | PARKED |
| D7 | Wall-tag S0 on real images | 2/3 (P-HOLD) | HW | 1–2 d | | PARKED |

### E. Flow-validity rule

| ID | component | rung | kind | effort | note | status |
|---|---|---|---|---|---|---|
| E1 | Inlier ≥ 0.85 and features ≥ 20, one flag for all three; calibrated on `p1c_*` | 2 | SW | 1.5 d (0.5 code, 0.5 calibration, 0.5 regression) | CONFIRMED for the camera path; not used in rung 1 or the UKF-only loop (`Qual > 0`) | PARKED |

### F. Mocap watcher

| ID | component | rung | kind | effort | note | status |
|---|---|---|---|---|---|---|
| F1 | Live mocap client → ROS 2 | 2, U | SW (protocol per U7) | 1–2 d | rung 1 needs only the offline recorder (R7) | WAITS (mocap protocol) |
| F2 | Watcher logic on hardware | 2, U | SW | 1 d | closes G1–G4, G7, G8, G10 (below) | DONE (G1–G11, 73 tests) |
| F3 | Watcher heartbeat → FC; FC-side LAND layer | 2, U | SW+HW | code 1.5–2 d; bench 0.5–1 d | closes G5, G6, G9, G11 | code DONE; bench WAITS; **F6 ruling OPEN** |
| F4 | Watcher bench tests B0–B10 | 2, U | HW | 1 d (bench + tethered B2) | CONFIRMED | SITL bench DONE (2c): B5a/B5b-noflag fail as worded, B8a void (rulings OPEN); hardware-only items WAIT |

**Watcher gaps G1–G11 (plan §7.2.0). BUILT and merged 2026-10-10 (`0502282`); SITL bench 2c done 2026-10-11.**

| gap | short | rung | kind | status |
|---|---|---|---|---|
| G1 | mocap input instead of Gazebo pose | 2, U | SW (protocol per U7) | DONE (adapter); live client WAITS (F1) |
| G2 | stale-pose check (0.5 s) | 2, U | SW | DONE (B5 wording ruling OPEN) |
| G3 | rigid-body identity check | 2, U | SW | DONE |
| G4 | breach → MAVLink LAND (latched) + audible alert | 2, U | SW | DONE (alert: hardware; **F6 retry ruling OPEN**) |
| G5 | watcher MAVLink HEARTBEAT; `FS_GCS_ENABLE 5`, `FS_GCS_TIMEOUT 3`, `MAV_GCS_SYSID` | 2, U | SW + bench | DONE (SITL B2b); bench WAITS |
| G6 | no arming without the watcher | 2, U | SW / procedure | procedure + Lua draft DONE; **ruling OPEN** (procedure or Lua) |
| G7 | networked liveness instead of `pgrep` | 2, U | SW | DONE |
| G8 | `--dep-loss stop` → LAND + alert | 2, U | SW | DONE |
| G9 | `watch_heartbeat` file local to the ground station | 2, U | procedure | DONE |
| G10 | height limit (z_max) in `--box` | 2, U | SW | DONE |
| G11 | unique system ID (heartbeat masking) | 2, U | SW + bench | DONE; the ID (211/213 placeholders) to confirm |

All are needed by rungs 2–3 and the UKF-only loop. **None is needed by rung 1**: nothing of ours steers, and safety is
the fence plus the pilot.

### G. Estimators and firmware

| ID | component | rung | kind | effort | note | status |
|---|---|---|---|---|---|---|
| G1a | Baseline firmware image (pinned or stock) | 1 | SW+HW | 0.5–1 d (R5) | | READY (script); WAITS (board, S6) |
| G1b | Fork firmware for the board | 3, U | SW+HW | SW now: guard change + ChibiOS compile + flash-size check 1–2 d, once U1 is named; HW: bench boot + "backends disabled reproduces EKF3" 1–2 d | ruling item 4: with a rollback plan | **BUILT** (`board-h743` `0156bfc34e`, not merged; MatekH743, Pixhawk6X, + KakuteH7 test 2026-10-12); one-command script READY; bench WAITS |
| G2 | UKF CPU on the FC MCU | 3, U | HW | 0.5 d | | WAITS (bench P8) |
| G3 | UKF port algorithm | 3, U | done in SITL | 0 d | open gate via H1 | DONE |
| G4 | `thesis_nav_check` | 3, U | done in SITL | in G1b; ~~+1–2 d if QuadPlane~~ (QuadPlane: dropped, reference) | | DONE (Copter) |
| G5 | `AP_NavFGO` thin backend | 3 | done in SITL | 0 d | | DONE |
| G6 | C++ FGO node, x86 | 3 (2 only if a live shadow is wanted) | done | 0 d | | DONE; corrected node `4c07374b` INSTALLED |
| G7 | Corrected FGO (initial yaw σ 1°) equivalence + safety | 1 (offline FGO must be the corrected one) → 3 | SIM | already scheduled (~1 d + H1) | rung 1 uses the corrected Python FGO | **DONE** (Band C forced PASS; safety `a_v4`/`b_v4` PASS) |
| G8 | C++ FGO on the Pi (arm64 GTSAM, timing, self-stop) | 3 (2 only if live) | SW+HW | cross-build SW 1 d; native timing + self-stop 2–4 d HW | | cross-build DONE (emulated, 2f); HW PARKED |
| G9 | FGO node serial transport | 3 | SW | 0.5–1 d | | PARKED |
| G10 | UKF live on the Pi (if U9 = Pi) | 3 (conditional) | SW+SIM | 3–5 d + SITL gates | not needed: the UKF runs on the FC | DROPPED for the UKF-only loop |
| G11 | Offline replay on real logs | 1→2, U | SW | r1: via R1/R2 (above); r2: bag-based with C7, 1–2 d | UKF-only: the U10 Replay gate on rung-1 logs | r1 DONE/BUILT (as R1/R2) |

### H. Safety tests and staging

| ID | component | rung | kind | effort | note | status |
|---|---|---|---|---|---|---|
| H1 | SITL safety (a)/(b) on the corrected builds | 3, U | SIM | ~1 d (scheduled) | | **DONE**: UKF (a) PASS, (b) S-A2 FAILED AS WORDED (S-A2b pre-registered for future tests); FGO `a_v4`/`b_v4` PASS |
| H2 | SITL rehearsal at Pi-like latency | 3 | SW + SIM | 1 d harness + 1 d flights per estimator | not needed for the UKF-only loop (no Pi) | PARKED |
| H3 | P-HOLD / P-LAPS rehearsal | 2/3 | done | 0 d | | DONE |
| H4 | Bench stage 0 | 1→2→3, U | HW | r1: in R12/R13; r2: 1–2 d; r3: +1 d forced invalidity → LAND | UKF-only: + the FC trigger-timing test (ruling 2026-10-11) | WAITS |
| H5 | RC override switch | 1, U | HW + procedure | 0.5 d (in R11/R12) | | cards DRAFT; WAITS |
| H6 | Geofence | 1→2, U | SW+HW | r1: FC altitude fence (+ circle needs an EKF origin), in R6/R11; r2: mocap box 0.5 d | UKF-only: the watcher box (no origin under type 12) | r1 in template; WAITS |
| H7 | Hand-carried stage | 1, U | HW | in R13 | | WAITS |
| H8 | Tethered hover | 3, U (1 only if the vehicle is new) | HW | 0.5–1 d | | WAITS |
| H9 | Per-stage pre-registration | 1→2→3, U | SW | r1: 0.5 d (R10); r2: 1–2 d; r3: 2–3 d | UKF-only: stage-3 prereg 1–1.5 d (plan U-d) | r1 DRAFT; stage 3 OPEN |
| H10 | Real-vehicle flight script | 2, U (if scripted) | SW | 1–2 d | rung 1 is pilot-flown; must carry the B10b takeover guard and F4 | OPEN (prototype guard in the bench driver only) |

### I. Logging, ground truth, time sync

| ID | component | rung | kind | effort | note | status |
|---|---|---|---|---|---|---|
| I1 | FC logging (`LOG_REPLAY`, `LOG_DISARMED`, buffer, `DSF`) | 1, U | SW+HW | in R6 | | template DONE; WAITS |
| I2 | Pi recorder (bag + metadata) | 2 | SW | 1 d | | PARKED |
| I3 | Mocap ground truth + `mocap_align` | 1, U | SW+HW | R7 + R8 | | DONE (SW); WAITS (mocap) |
| I4 | Time sync: mocap ↔ FC (r1); Pi ↔ mocap host (r2) | 1→2, U | SW+HW | r1: in R8; r2: 0.5–1 d chrony/PTP | | r1 DONE (SW); WAITS |

---

## 3. Rung 2 delta (beyond rung 1): PARKED

**Base items:**

| group | rows | effort |
|---|---|---|
| Pi and cameras | A1(r2), A3, A4, A5, A9, A10 | 4.75–7.5 d (+3–5 if C++ flow) |
| link and clocks | B1, B2, B3, B4 | 2–2.5 d |
| calibration | D1, D3(r2), D4(r2), D5(r2) | 3–3.5 d |
| flow rule | E1 | 1.5 d |
| watcher | F1, F2, F3, F4 (G1–G11) | 4.5–6 d (largely DONE: F2, F3 code, F4 SITL) |
| replay, geometry | C7(r2), G11(r2) | 2–5 d |
| staging, safety | H4(r2), H6(r2), H9(r2), H10 | 3.5–6.5 d |
| logging | I2, I4(r2) | 1.5–2 d |
| **total** | | **about 24–37 d** (before the watcher work already done) |

**Optional add-ons:**
- forward camera (A6, D2, D6): +3.5–7 d;
- P-HOLD (A7, D7, C4): +2.5–3.5 d;
- a live FGO shadow on the Pi (G8): +3–5 d.

**Software that could start NOW (no hardware), as costed on 2026-10-10: about 13–19.5 d.**
- A4 (SW part), A5, A9, B1 (config), B4;
- C7 (r2), E1;
- F1, F2, F3 (code), i.e. the G1–G11 gaps (since BUILT, 2026-10-10);
- G11 (r2), H6 (r2), H9 (r2), H10, I2.

**Hardware-dependent: about 11–17.5 d** after the Pi, the cameras and the vehicle are in hand.

**Rung-1 items reused by rung 2:**
- the firmware image (R5);
- the parameter template (R6), re-targeted to `FLOW_TYPE 5`;
- the mocap recorder and `mocap_align` (R7, R8);
- the scorer (R9);
- the flight cards (R11);
- the Replay checks (R2, R4).

Rung 1 is therefore not throw-away work.

## 4. Rung 3 delta

### 4.1 UKF-only closed loop (the planned first closed loop; Copter)
It skips rung 2 entirely. Costed in `docs/ukf_only_closed_loop_costing.md` (about 14–20 d in all) and scheduled in
`docs/realflight_plan_copter.md` §4: **14 working days from hardware arrival** (rung 1 first, then 8; +2–3
contingency). Rows it needs are marked "U" above. Its SITL plan is corrected there (§4.2: the MAVLink camera-flow path,
not `SIM_FLOW`, which is unusable with the Gazebo model).

### 4.2 Full rung 3 (beyond rung 2; UKF and FGO, Pi)

From `real_flight_readiness.md` §4, re-split:

| rows | effort | kind | status |
|---|---|---|---|
| G7 + H1 (corrected FGO gates) | 2–3 d | SIM (scheduled) | DONE |
| G1b, G4, C8 (fork for the board) | 2–4 d (~~+1–2 QuadPlane~~: dropped, reference) | SW now 1–2 d once U1 is named; HW 1–2 d | BUILT + script READY; HW WAITS |
| G2 (UKF CPU on the MCU) | 0.5 d | HW | WAITS |
| G8, G9 (C++ FGO on the Pi, transport) | 3.5–5 d | SW 1.5–2 d; HW 2–3 d | cross-build DONE; rest PARKED |
| B3 → H2 (latency rehearsal) | 2–3 d | SW harness 1 d; SIM | PARKED |
| H4 item (b) (forced invalidity → LAND on the real FC) | 1 d | HW | WAITS |
| H8 (tethered hover) | 0.5–1 d | HW | WAITS |
| H9 stage-2/3 pre-registrations | 2–3 d | SW | OPEN |
| G10 (only if U9 = Pi) | 3–5 d | SW + SIM | DROPPED (UKF on the FC) |
| **total** | **about 17–27 d** (excluding G10 and the heading arms) | **SW now about 5.5–8 d** | |

---

## 5. ~~Calendar to Fri 23 Oct: which rung is reachable~~ (SUPERSEDED 2026-10-12)

Superseded by the hardware-relative timelines in `docs/realflight_plan_copter.md` (§0, §3.1, §4.1):
- **Rung 1:** 6 working days from hardware arrival (+2 contingency; +3–6 d if the vehicle is not already flying). It
  finishes by Fri 23 Oct only if hardware arrives by Thu 15 Oct, with no contingency left.
- **UKF-only closed loop:** 14 working days from hardware arrival (+2–3). Not reachable by 23 Oct.
- **Rung 2:** PARKED. **Full rung 3:** after rung 2; not scheduled.

The original table is kept in git history (`91e87c9`).

## 6. Open questions

1. ~~**Rung 2 hardware:** Pi 4 or Pi 5~~: rung 2 is PARKED; a Pi 5 is recommended for any later FGO path (ruling
   2026-10-11).
2. **Board name (U1)**, as early as possible. The final build is one command (`tools/build_board_fw.sh <B>`); the
   flash margin, the IMU count and the compass question wait on it.
3. **Freeze scope:** do flights after 23 Oct still count toward the thesis?
4. ~~**Rung 2's UKF/FGO "alongside"**~~: rung 2 is PARKED.
5. **The rulings listed in `docs/realflight_plan_copter.md` §5** (pre-registration sign-off, E5, capture delay, `XUKO`,
   F6, F2, U4/GNDCLR, own-gyro drivers, multi-IMU, H10 guard, B5/B8a, compass, S6, merges, G6).
