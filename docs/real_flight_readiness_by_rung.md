# Real-flight readiness, re-costed by RUNG

Status: PLANNING ONLY. Written 2026-10-10 on `fwd-camera` at `91e87c9`, implementing the ruling "RULINGS (user,
2026-10-10, SUPERSEDING …): real flights built as RUNGS" (METHODOLOGY, last entry). Nothing was run or built.

It re-costs every row of `docs/real_flight_readiness.md` (60 rows, IDs A1–I4), plus the watcher gaps G1–G11 of
`docs/real_flights_plan.md` §7.2 and the new rung-1 items R1–R15 of `docs/minimal_real_flight_plan.md`.

## The rungs

- **Rung 1:** a minimal logging flight. Stock firmware; the vehicle's own flow sensor and rangefinder on the FC; a pilot
  (or EKF3) flies; `LOG_REPLAY` and mocap. EKF3 and the UKF port run via Replay, the FGO via the converter. Costed in
  `docs/minimal_real_flight_plan.md`.
- **Rung 2:** open loop with OUR pipeline. Pi, camera flow, forward camera (only once verified); EKF3 flies; the UKF and
  FGO run alongside (offline by default; ruling Q6: an offline-only FGO is acceptable).
- **Rung 3:** closed loop. Board firmware with the UKF/FGO backends, the UKF/FGO steering, the full watcher, and the
  safety tests.

## Column key

| column | meaning |
|---|---|
| **rung** | The first rung that needs the row. "—" means no rung needs it as currently scoped. "1→2" means rung 1 needs a reduced form and rung 2 the full form. |
| **kind** | **SW** = software or paper only; it can start NOW with no hardware. **HW** = needs the vehicle, sensors, Pi or mocap. **SW+HW** = code now, then a hardware check. **SIM** = needs the simulator, so it waits until after the 16 Oct sim freeze. |
| **effort** | [E], one person, "d" = a working day. Taken from the readiness row unless re-costed here. Where rung 1 needs only part of a row, both parts are given. |

Hardware identities (FC board, flow sensor, rangefinder, camera(s), Pi, mocap) come from the supervisor and are inputs.

---

## 1. Rung 1: shortest path first

These are the items rung 1 needs, in dependency order. For details see `docs/minimal_real_flight_plan.md` §5.

| order | ID(s) | item | kind | effort |
|---|---|---|---|---|
| 1 | R10, H9(r1) | Rung-1 pre-registration: profile, n, window, metrics, Replay tolerance, converter band | SW | 0.5 d |
| 2 | R1, G11(r1), C7(r1) | Converter BIN → FGO inputs, geometry overrides (defaults unchanged), SITL acceptance test on `cl_a_tex_half` | SW (+1 light replay) | 2.5–3.5 d |
| 3 | R2, R3, C7(r1) | UKF port: real geometry and flow delay from DAL/params, byte-identical on SITL; Replay rebuild; CSV → TUM | SW | 0.75–1.25 d |
| 4 | R8, I3, I4(r1) | `mocap_align` on `RISI` (400 Hz, pre-filter), re-self-test | SW | 0.5 d |
| 5 | R9 | Scorer `real_score.py` (pre-registered window, evo -a, start-aligned drift) | SW | 1–1.5 d |
| 6 | R11, H5, H6(r1) | Flight cards; RC override switch; FC altitude fence (+ optional circle fence with an EKF origin) | SW | 1 d |
| 7 | R6, C1, C2, C3, C6(r1), I1 | Real-sensor parameter template (draft SW now), then bench readback, `DSF`, compass arming check | SW+HW | 1.5 d |
| 8 | G1a, R5 | Firmware: pinned `7bac20cbcc` from a clean checkout (or stock 4.7.0), flash, rollback | SW+HW | 0.5–1 d |
| 9 | A1, A2, C5, A8 | Vehicle flying with its flow sensor and rangefinder on the FC (supervisor's vehicle) | HW | **0 d if already flying**; otherwise 3–6 d (breaks 23 Oct) |
| 10 | R12, D3(r1), D4(r1), D5(r1) | Bench (props off): flow orientation (`OF.body*` against `flow*` signs), rangefinder, mount offsets, `EK3_FLOW_DELAY` from the datasheet | HW | 0.5–1 d |
| 11 | R7, I3 | Mocap recorder/adapter (Motive or Vicon export → CSV, Z-up) | SW+HW | 0.5–1.5 d |
| 12 | R4 | EKF3 Replay: 0 d if pinned, 0.5 d stock Replay if 4.7.0; `check_replay.py` acceptance on the first real log | SW+HW | 0.5–1 d |
| 13 | R13, H7, H4(r1) | Hand-carried check in the volume, with the whole offline pipeline run the same day | HW | 1 d |
| 14 | R14 | Flight day(s): first hovers, then n = 3–5 (+3 over a plain sheet) | HW | 1–1.5 d |
| 15 | R15 | Offline runs, scoring, METHODOLOGY entry | SW | 1 d |

**Rung 1 total:**
- software that can start now: **7–9.5 d** (agents);
- hardware and on-site work: **5–8 d**;
- **12–17.5 person-days in all.**
- The elapsed time is set by the vehicle.

**Verdict for rung 1: FITS ONLY IF** an already-flying H7 vehicle with its flow sensor and rangefinder is available by
about 16 Oct, and mocap time by about 19–21 Oct (calendar §5).

---

## 2. Every readiness row by rung

### A. Vehicle, sensor drivers and bridges

| ID | component (short) | rung | kind | effort | note |
|---|---|---|---|---|---|
| A1 | Airframe, FC, sensors assembled | 1→2 | HW | r1: 0 d (supervisor's flying vehicle) or 2–4 d; r2: +1–2 d Pi, cameras, FC↔Pi UART | |
| A2 | Baseline tune, hover learn, notch | 1 | HW | 0 d if already flying; else 1–2 d | |
| A3 | Downward-camera capture on the Pi | 2 | HW (driver choice SW) | 1–2 d | U4 |
| A4 | `flow_tracker.py` on the Pi | 2 | SW+HW | SW now 0.5 d (focal length from calibration, `use_sim_time` off); HW timing 1 d; +3–5 d if C++ is needed | |
| A5 | `flow_bridge.py` on the real link | 2 | SW | 0.5 d | lateral sign re-checked at D5 |
| A6 | Forward camera + C++ heading on the Pi | 2 (only if flown) | HW | 1–2 d native run + capture [E] | supervisor rule: fly only once verified |
| A7 | Wall-tag detector → ExtNav | 2/3 (P-HOLD only) | SW+HW | 1 d + D7 | |
| A8 | Rangefinder on the FC (native driver) | 1 | HW | 0.5–1 d (0 d if already fitted) | U6 |
| A9 | FC `DISTANCE_SENSOR` → ROS republisher | 2 | SW | 0.5 d | rung 1 uses `RRNI` offline |
| A10 | `HIGHRES_IMU` 333 Hz over a real UART | 2 | SW+HW | SW 0.25 d; bench 1 d | rung 1 uses `RISI` offline |

### B. MAVLink link, ports, clocks

| ID | component | rung | kind | effort | note |
|---|---|---|---|---|---|
| B1 | FC↔Pi link + router replacing the SITL UDP ports | 2 | SW+HW | SW config 0.5 d; HW 0.5–1 d | |
| B2 | FC↔Pi clock map (D25) on hardware | 2 | HW | 0.5 d | rung 1 has one clock (FC `TimeUS`) |
| B3 | Measured link latency | 2 (report), 3 (feeds H2) | HW | 0.5 d | |
| B4 | Pi time base, `use_sim_time` off | 2 | SW | 0.5 d | |

### C. Parameter files

| ID | component | rung | kind | effort | note |
|---|---|---|---|---|---|
| C1 | Core real-FC parameter file | 1 | SW+HW | in R6 (1.5 d) | never `AHRS_EKF_TYPE 10` |
| C2 | Rangefinder parameters | 1 | SW+HW | in R6 | |
| C3 | Flow parameters (`FLOW_TYPE` per sensor; `FLOW_POS_*`, `ORIENT_YAW`, `EK3_FLOW_DELAY`) | 1 | SW+HW | in R6 | rung 2 sets them again for camera flow (`FLOW_TYPE 5`) |
| C4 | ExtNav parameters | 2/3 (P-HOLD) | SW+HW | 0.5 d | after D4, D7 |
| C5 | `MOT_THST_HOVER`, gains | 1 | HW | in A2 | |
| C6 | INS filters, notch (recorded, no retune) | 1 | HW | 0.5 d | the group delay matters to `mocap_align` only for `IMU`, not `RISI` |
| C7 | Geometry constants in three implementations | 1→2 | SW | r1: in R1/R2 (Python FGO overrides, port reads DAL); r2/3: C++ `factors.h`, `fgo_core.cpp:69` + equivalence re-runs 1–3 d | defaults unchanged during the sim freeze |
| C8 | Fork parameters (`AHRS_EKF_TYPE 12/13`, `TFAIL 0`) | 3 | SW | 0.25 d (readback list) | |

### D. Calibration and re-validation

| ID | component | rung | kind | effort | note |
|---|---|---|---|---|---|
| D1 | Downward-camera intrinsics | 2 | HW | 0.5 d | tool exists |
| D2 | Forward-camera intrinsics, resampling | 2 (if flown) | HW | 0.5–1 d | tool exists |
| D3 | Extrinsics / lever arms | 1→2 | HW | r1: 0.5 d (flow sensor, rangefinder, mocap markers, tape measure); r2: +1–1.5 d cameras | |
| D4 | Sensor–FC time offsets | 1→2 | HW | r1: 0 d (datasheet `EK3_FLOW_DELAY`); r2: 1 d bench (camera) | |
| D5 | Flow sign/axis on the real mount | 1→2 | HW | r1: 0.5 d (sensor orientation, in R12/R13); r2: 0.5 d (camera) | |
| D6 | VP heading re-validation (new pre-registration) | 2 (if forward camera flown) | SW+HW | 2–4 d | |
| D7 | Wall-tag S0 on real images | 2/3 (P-HOLD) | HW | 1–2 d | |

### E. Flow-validity rule

| ID | component | rung | kind | effort | note |
|---|---|---|---|---|---|
| E1 | Inlier ≥ 0.85 and features ≥ 20, one flag for all three; calibrated on `p1c_*` | 2 | SW | 1.5 d (0.5 code, 0.5 calibration, 0.5 regression) | CONFIRMED for the camera path; not used in rung 1 (`Qual > 0`) |

### F. Mocap watcher

| ID | component | rung | kind | effort | note |
|---|---|---|---|---|---|
| F1 | Live mocap client → ROS 2 | 2 | SW (protocol per U7) | 1–2 d | rung 1 needs only the offline recorder (R7) |
| F2 | Watcher logic on hardware | 2 | SW | 1 d | closes G1–G4, G7, G8, G10 (below) |
| F3 | Watcher heartbeat → FC; FC-side LAND layer | 2 | SW+HW | code 1.5–2 d; bench 0.5–1 d | closes G5, G6, G9, G11 |
| F4 | Watcher bench tests B0–B10 | 2 | HW | 1 d (bench + tethered B2) | CONFIRMED |

**Watcher gaps G1–G11 (plan §7.2.0). Another agent BUILDS these now (ruling item 2). Listed here only.**

| gap | short | rung | kind |
|---|---|---|---|
| G1 | mocap input instead of Gazebo pose | 2 | SW (protocol per U7) |
| G2 | stale-pose check (0.5 s) | 2 | SW |
| G3 | rigid-body identity check | 2 | SW |
| G4 | breach → MAVLink LAND (latched) + audible alert | 2 | SW |
| G5 | watcher MAVLink HEARTBEAT; `FS_GCS_ENABLE 5`, `FS_GCS_TIMEOUT 3`, `MAV_GCS_SYSID` | 2 | SW + bench |
| G6 | no arming without the watcher | 2 | SW / procedure |
| G7 | networked liveness instead of `pgrep` | 2 | SW |
| G8 | `--dep-loss stop` → LAND + alert | 2 | SW |
| G9 | `watch_heartbeat` file local to the ground station | 2 | procedure |
| G10 | height limit (z_max) in `--box` | 2 | SW |
| G11 | unique system ID (heartbeat masking) | 2 | SW + bench |

All are needed by rungs 2–3. **None is needed by rung 1**: nothing of ours steers, and safety is the fence plus the pilot.

### G. Estimators and firmware

| ID | component | rung | kind | effort | note |
|---|---|---|---|---|---|
| G1a | Baseline firmware image (pinned or stock) | 1 | SW+HW | 0.5–1 d (R5) | |
| G1b | Fork firmware for the board (`AP_NAVUKF_ENABLED` SITL-only today) | 3 | SW+HW | SW now: guard change + ChibiOS compile + flash-size check 1–2 d, once U1 is named; HW: bench boot + "backends disabled reproduces EKF3" 1–2 d | ruling item 4: with a rollback plan |
| G2 | UKF CPU on the FC MCU | 3 | HW | 0.5 d | |
| G3 | UKF port algorithm | 3 | done in SITL | 0 d | open gate via H1 |
| G4 | `thesis_nav_check` | 3 | done in SITL | in G1b; +1–2 d if QuadPlane | |
| G5 | `AP_NavFGO` thin backend | 3 | done in SITL | 0 d | |
| G6 | C++ FGO node, x86 | 3 (2 only if a live shadow is wanted) | done | 0 d | |
| G7 | Corrected FGO (initial yaw σ 1°) equivalence + safety | 1 (offline FGO must be the corrected one) → 3 | SIM | already scheduled (~1 d + H1) | rung 1 uses the corrected Python FGO |
| G8 | C++ FGO on the Pi (arm64 GTSAM, timing, self-stop) | 3 (2 only if live) | SW+HW | cross-build SW 1 d; native timing + self-stop 2–4 d HW | |
| G9 | FGO node serial transport | 3 | SW | 0.5–1 d | |
| G10 | UKF live on the Pi (if U9 = Pi) | 3 (conditional) | SW+SIM | 3–5 d + SITL gates | |
| G11 | Offline replay on real logs | 1→2 | SW | r1: via R1/R2 (above); r2: bag-based with C7, 1–2 d | |

### H. Safety tests and staging

| ID | component | rung | kind | effort | note |
|---|---|---|---|---|---|
| H1 | SITL safety (a)/(b) on the corrected builds | 3 | SIM | ~1 d (scheduled) | |
| H2 | SITL rehearsal at Pi-like latency | 3 | SW + SIM | 1 d harness (SW now) + 1 d flights per estimator (after 16 Oct) | |
| H3 | P-HOLD / P-LAPS rehearsal | 2/3 | done | 0 d | |
| H4 | Bench stage 0 | 1→2→3 | HW | r1: in R12/R13; r2: 1–2 d; r3: +1 d forced invalidity → LAND | |
| H5 | RC override switch | 1 | HW + procedure | 0.5 d (in R11/R12) | |
| H6 | Geofence | 1→2 | SW+HW | r1: FC altitude fence (+ circle needs an EKF origin), in R6/R11; r2: mocap box 0.5 d | |
| H7 | Hand-carried stage | 1 | HW | in R13 | |
| H8 | Tethered hover | 3 (1 only if the vehicle is new) | HW | 0.5–1 d | |
| H9 | Per-stage pre-registration | 1→2→3 | SW | r1: 0.5 d (R10); r2: 1–2 d; r3: 2–3 d | |
| H10 | Real-vehicle flight script | 2 | SW | 1–2 d | rung 1 is pilot-flown |

### I. Logging, ground truth, time sync

| ID | component | rung | kind | effort | note |
|---|---|---|---|---|---|
| I1 | FC logging (`LOG_REPLAY`, `LOG_DISARMED`, buffer, `DSF`) | 1 | SW+HW | in R6 | |
| I2 | Pi recorder (bag + metadata) | 2 | SW | 1 d | |
| I3 | Mocap ground truth + `mocap_align` | 1 | SW+HW | R7 + R8 | |
| I4 | Time sync: mocap ↔ FC (r1); Pi ↔ mocap host (r2) | 1→2 | SW+HW | r1: in R8; r2: 0.5–1 d chrony/PTP | |

---

## 3. Rung 2 delta (beyond rung 1)

**Base items:**

| group | rows | effort |
|---|---|---|
| Pi and cameras | A1(r2), A3, A4, A5, A9, A10 | 4.75–7.5 d (+3–5 if C++ flow) |
| link and clocks | B1, B2, B3, B4 | 2–2.5 d |
| calibration | D1, D3(r2), D4(r2), D5(r2) | 3–3.5 d |
| flow rule | E1 | 1.5 d |
| watcher | F1, F2, F3, F4 (G1–G11) | 4.5–6 d |
| replay, geometry | C7(r2), G11(r2) | 2–5 d |
| staging, safety | H4(r2), H6(r2), H9(r2), H10 | 3.5–6.5 d |
| logging | I2, I4(r2) | 1.5–2 d |
| **total** | | **about 24–37 d** |

**Optional add-ons:**
- forward camera (A6, D2, D6): +3.5–7 d;
- P-HOLD (A7, D7, C4): +2.5–3.5 d;
- a live FGO shadow on the Pi (G8): +3–5 d.

**Software that can start NOW (no hardware): about 13–19.5 d.**
- A4 (SW part), A5, A9, B1 (config), B4;
- C7 (r2), E1;
- F1, F2, F3 (code), i.e. the G1–G11 gaps (being built by another agent);
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

## 4. Rung 3 delta (beyond rung 2)

From `real_flight_readiness.md` §4, re-split:

| rows | effort | kind |
|---|---|---|
| G7 + H1 (corrected FGO gates) | 2–3 d | SIM (scheduled) |
| G1b, G4, C8 (fork for the board) | 2–4 d (+1–2 QuadPlane) | SW now 1–2 d once U1 is named; HW 1–2 d |
| G2 (UKF CPU on the MCU) | 0.5 d | HW |
| G8, G9 (C++ FGO on the Pi, transport) | 3.5–5 d | SW 1.5–2 d; HW 2–3 d |
| B3 → H2 (latency rehearsal) | 2–3 d | SW harness 1 d; SIM after 16 Oct |
| H4 item (b) (forced invalidity → LAND on the real FC) | 1 d | HW |
| H8 (tethered hover) | 0.5–1 d | HW |
| H9 stage-2/3 pre-registrations | 2–3 d | SW |
| G10 (only if U9 = Pi) | 3–5 d | SW + SIM |
| **total** | **about 17–27 d** (excluding G10 and the heading arms) | **SW now about 5.5–8 d** |

Items needed only by rung 3 that are not reached by 23 Oct become future work, as the ruling says.

---

## 5. Calendar to Fri 23 Oct: which rung is reachable

- There are 10 working days (Mon 12 – Fri 23), plus this weekend.
- **Simulation work keeps priority until Fri 16 Oct.** Real-flight software runs as agent coding alongside it, with no
  heavy jobs and no competing simulator use.
- The supervisor's inputs are on the critical path.

| dates | rung 1 (critical) | rungs 2–3 software (parallel, agents) |
|---|---|---|
| Sat 10 – Sun 11 | R10 pre-registration draft; start R1, R2, R8 | G1–G11 (other agent, ongoing) |
| Mon 12 | **supervisor inputs S1–S7; firmware decision; mocap booking** | — |
| Mon 12 – Wed 14 | R1, R2/R3, R8, R9; R6 draft; R11 | E1 code (calibration on `p1c_*` is light); H10; I2 |
| Thu 15 – Fri 16 | R5 firmware, R6 bench, R12 bench; R1/R2 SITL acceptance tests (light) | G1b guard + board compile (once U1 is named); C7 (C++) |
| **Fri 16** | **Gate D2: flying vehicle with sensors on the bench** | sim freeze ends |
| Mon 19 | R7 + **R13 hand-carried + same-day pipeline** | H2 harness; G8 cross-build |
| Tue 20 – Wed 21 | first hovers; **R14 flights (n = 3–5)** | SIM: H1 on the corrected builds (if not done), H2 |
| Thu 22 – Fri 23 | R15 scoring; buffer; freeze | rung-2/3 software continues; hardware bench only if the Pi is in hand |

**Which rung is realistically reachable by 23 Oct:**

| rung | verdict |
|---|---|
| **Rung 1** | **FITS ONLY IF** the supervisor provides an already-flying H7 vehicle with its flow sensor and rangefinder on the FC by about 16 Oct, plus mocap time on about 19–21 Oct. It **does not fit** if the vehicle needs assembly or tuning (+3–6 d). |
| **Rung 2** | **DOES NOT FIT.** About 11–17.5 d of hardware-dependent work remains after the Pi, cameras and vehicle arrive, and that work cannot start before rung 1's hardware chain. Its 13–19.5 d of software can be largely done by 23 Oct with agents. That would make rung 2 the first real-flight work after the freeze. |
| **Rung 3** | **DOES NOT FIT.** 17–27 d on top of rung 2. Its software-only items (G1b compile once the board is named, G9, the H2 harness, the pre-registrations) can start. |

## 6. Open questions (beyond `minimal_real_flight_plan.md` §9)

1. **Rung 2 hardware:** Pi 4 or Pi 5, cameras, lenses. When will they be in hand? This sets when its 11–17.5 d hardware
   chain can start.
2. **Board name (U1)**, as early as possible. G1b's board compile, the flash-size check and the EKF precision (H7 =
   double) all wait on it.
3. **Freeze scope:** do the rung-2/3 software builds after 23 Oct still count toward the thesis, as future work
   "started", or are they out of scope?
4. **Rung 2's UKF/FGO "alongside":** offline (default, with no G8) or a live shadow on the Pi (+3–5 d)?
