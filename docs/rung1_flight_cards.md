# Rung 1 flight cards (R11): DRAFT

**Status: DRAFT, written 2026-10-10, not yet used.** To be walked through once with the safety pilot and the mocap
operator before the bench day, and amended there. Placeholders: **[TBD-S]** (supervisor/vehicle input).

Governing documents: `docs/rung1_preregistration_draft.md` (what is flown and scored), `docs/minimal_real_flight_plan.md`
(the plan), `realflight/params/rung1_template.parm` + one compass variant (the parameters).

**Classification (METHODOLOGY standing rule, 2026-10-10):** every card says whether it is **VERIFICATION** (shortest
profile that exercises the check; never scored, never reused as result data) or **RESULT** (pre-registered; scored).

Rung 1 does NOT use the mocap watcher, the Pi or `realflight/params/watcher_fc.parm` (those are rungs 2–3). Nothing of
ours steers: safety is the safety pilot, the FC's altitude fence and failsafes, and a person watching mocap.

---

## 0. Roles

| role | who | duties | authority |
|---|---|---|---|
| **Safety pilot (SP)** | [TBD-S] | flies every armed sortie in ALT_HOLD; owns the transmitter, the mode switch (STABILIZE / ALT_HOLD / LAND) and the disarm | **final authority** in the air: calls and executes every abort |
| **Mocap operator (MO)** | [TBD-S] | starts/stops the mocap take; watches the rigid body live (tracked, inside the box); calls "MOCAP LOST" / "BOUNDARY" | calls aborts on tracking loss or boundary; never touches the vehicle controls |
| **Ground station / logger (GS)** | the student | parameter readback, arming pre-checks, sortie log sheet, log download, the data-integrity checklist (§6) | calls "NO-GO" before arming; may call an abort; never flies |
| **Observer** (if lab rules require) | [TBD-S] | volume clear of people; fire/LiPo safety | may call an abort |

Calls are spoken and acknowledged ("ABORT" → SP: "landing"). One person speaks to SP during a sortie: GS.

---

## 1. Day-before / pre-session (once)

- [ ] Mocap booked for the day(s) [TBD-S]; volume size measured; floor as planned (textured; plain sheet if S7).
- [ ] Vehicle: props, battery count (≥ 6 charged packs for n = 5 + spare + verification), spare props, LiPo bag.
- [ ] Firmware on the vehicle recorded (version string from the boot messages). If newly flashed: the `.apj` archived, the
      previous image and parameter dump kept for rollback (`minimal_real_flight_plan.md` R5).
- [ ] `python3 realflight/params/check_parm.py --final rung1_template.parm rung1_variant_<x>.parm` → **OK (final)**
      (no TODO_SUPERVISOR left; never AHRS_EKF_TYPE 10; no SIM_*).
- [ ] The offline pipeline runs on an existing SITL log end to end (Replay with the R2 port, converter, scorer), so
      that the same-day rehearsal after H is only a data change.
- [ ] Mocap rigid body defined on the vehicle (≥ 4 markers, asymmetric); its pivot near the FC; marker offsets measured.
- [ ] Sortie log sheet printed (one row per sortie: id, class, battery, start/end FC time, mocap take name, notes).

---

## 2. Bench checks (props OFF): VERIFICATION

Each is the shortest check of one fact. Logging on (`LOG_DISARMED 1`). Not scored. **Card B is complete only when every
line passes; any FAIL stops the day's flying until fixed.**

| # | check | how | duration and why it suffices | pass |
|---|---|---|---|---|
| B1 | **Parameter readback** | download all parameters from the FC; diff against `rung1_template.parm` + the variant; **AHRS_EKF_TYPE = 3**, LOG_REPLAY = 1, LOG_DISARMED = 1, ARMING_SKIPCHK = 0, GPS1_TYPE = 0, EK3_SRC1_* as filed. If any differs: PARAM_SET, reboot, read back again (eeprom gotcha) | ~2 min: a readback is a single dump | every value as filed |
| B2 | **Sensors healthy** | ground station status: flow sensor, rangefinder, compass (healthy even in nomag: arming gate), IMU, logging | ~1 min: a status screen | all healthy; no pre-arm message other than the expected "props off" items |
| B3 | **Rangefinder** | on the ground: reading ≈ `RNGFND1_GNDCLR`; then lift the vehicle by hand to ~1 m and back | ~30 s: one lift spans the range used | ground reading within ±2 cm of GNDCLR (or "out of range low" if RNGFND1_MIN > resting height: RECORD, it is a known limit, §9 item 11 of the pre-registration); ~1 m when lifted |
| B4 | **Flow sign (ArduPilot's standard flow check)** | over the textured floor, at ~0.5–1 m, roll the vehicle by hand left/right, then pitch forward/back, ~3 cycles each | ~1 min: three cycles per axis show the sign unambiguously | in the log, `OF.flowX` follows `OF.bodyX` and `OF.flowY` follows `OF.bodyY` (same sign, similar size). If not: `FLOW_ORIENT_YAW` is wrong; fix and repeat |
| B5 | **Arming checks run** | attempt to arm with props off (motor safety per lab rules) | ~30 s | arming either succeeds with every check run, or fails only on the props-off/safety item; never a skipped check |
| B6 | **Fence** | ground station fence status | ~30 s | altitude fence enabled, FENCE_ALT_MAX as filed, no pre-arm fence error; the reported height ≈ 0 on the ground |
| B7 | **Failsafes** | RC transmitter off for 2 s (props off, disarmed): RC failsafe message; battery failsafe values read back | ~1 min | messages as expected; values as filed |
| B8 | **Log completeness** | download the bench log; run §7 items D2–D5 on it | ~5 min of checking; the log is the B1–B7 period | LOG_REPLAY records present; `DSF.Dp` = 0 |

The B4 wiggle and the bench rotations are also the input for the flow-delay measurement (pre-registration §6).

---

## 3. Hand-carried pass in the volume (disarmed, props OFF): VERIFICATION

**Length: ~2 min.** *Why it suffices:* disarmed, EKF3 stays "on ground" (`AP_NavEKF3_VehicleStatus.cpp:466-480`) and
does not navigate on flow, so a longer carry tests nothing more. One leg exercises the plumbing, the mocap clock map,
the flow sign over the real floor and Replay reproduction of a non-aiding EKF3. **Never scored.**

1. MO: start mocap take `H_<date>`. GS: confirm logging (disarmed logging on).
2. Sync wiggle on the start spot (~5 s, sharp rotations about all axes). Set down 3 s.
3. Carry the vehicle level at flight height (h) along ONE leg of the result profile and back, at walking speed ≤ 0.5 m/s
   (~40 s).
4. Set down on the start spot 3 s; second sync wiggle (~5 s). MO: stop the take.
5. **Same day, before any armed sortie:** run the whole offline pipeline on this log (Replay EKF3 + UKF port, converter
   → FGO, `mocap_align`, scorer). Pass = every tool runs, the clock map residual is reported, Replay EKF3 vs onboard is
   computed (gate of the pre-registration §5, here on a non-aiding EKF3).

---

## 4. First hover: VERIFICATION

**Length: ~1.5–2 min airborne.** *Why it suffices:* 45 s of hover covers EKF3's flow-aiding start (~16 s after take-off
in SITL) with margin; one 2 m leg and back shows that flow drives the velocity with the right sign. **Never scored.**

Card: as the result card (§5) with this profile instead: take-off to h → hover 45 s → 2 m forward and back at ≤ 0.3 m/s →
hover 10 s → land. Sync wiggles before arming and after disarming as usual.

Pass (GS, from the log the same day): `XKF4.SS` shows horizontal position relative valid after aiding starts; `XKF5`
flow innovations not rejected; EKF3 velocity sign matches the leg direction; the Replay-fidelity numbers WITH flow aiding
are computed (they decide the pre-registration §5 bound, [TBD-V]). If V fails: no result flight that day.

---

## 5. Result sortie card: RESULT (one per flight, R1…Rn)

Pre-registered profile (pre-registration §3.1). Copy this card per sortie.

**Sortie id:** R__  **Battery:** __  **Mocap take:** `R__<date>`  **FC log no.:** __

Pre-arm (GS reads, SP confirms):
- [ ] Battery fully charged, voltage __ V (≥ [TBD-S])
- [ ] Mode switch at ALT_HOLD; LAND and STABILIZE positions confirmed by SP
- [ ] Mocap: rigid body tracked, inside the box, take recording (MO: "MOCAP RECORDING")
- [ ] FC: logging, no pre-arm errors, rangefinder reading ≈ GNDCLR, flow healthy
- [ ] Volume clear of people (Observer: "CLEAR")
- [ ] GS: "GO" / "NO-GO"

Profile (SP flies; GS calls the times from a stopwatch started at take-off):
1. [ ] Sync wiggle, disarmed (~5 s); set down on the start mark; stand clear
2. [ ] Arm; take off to h = __ m; **hover 30 s** over the start mark
3. [ ] **Two laps** of the rectangle/out-and-back (legs __ m) at ~__ m/s (~90 s); GS calls each corner
4. [ ] Hover 10 s over the start mark; land; disarm
5. [ ] Sync wiggle, disarmed (~5 s); MO: stop the take; GS: note the end time
6. [ ] GS: anything unusual (gusts from air conditioning, a skipped leg, a pilot correction) noted on the sheet

---

## 6. Abort criteria (any sortie)

Called by anyone; **SP executes**. Default action: **LAND mode** (switch), or SP lands manually in ALT_HOLD if LAND
would be worse. **STABILIZE** is the last resort if ALT_HOLD misbehaves (height oscillation, climb-away).

| call | condition | action |
|---|---|---|
| ABORT – BOUNDARY | the vehicle within 1.0 m [TBD-S] of a volume wall/net, or above the fence altitude (the fence lands it anyway) | SP stops, returns to centre if safe, else LAND |
| ABORT – MOCAP | MO: rigid body lost > 1 s | SP holds position by sight and lands (the flight is then excluded, §3.3) |
| ABORT – HEIGHT | ALT_HOLD height oscillating > ±0.3 m, or an uncommanded climb/descent | STABILIZE if needed, land |
| ABORT – FAILSAFE | any failsafe message (EKF, battery, RC, fence) | the FC's action stands; SP takes over only if it is unsafe |
| ABORT – VEHICLE | vibration, noise, a loose part, smoke, a motor/ESC fault | land immediately; disarm; LiPo procedure |
| ABORT – PEOPLE | anyone enters the volume | land immediately |

After any abort: the sortie is recorded with its reason. A result sortie aborted before the window end is excluded
(pre-registration §3.3), and the spare slot may be used **once**. Any hardware fault: no more flying until checked.

---

## 7. Data-integrity checklist after EACH sortie (before the next battery)

GS, on the downloaded `.BIN` and the mocap export (a script will implement D1–D6; until then by hand with pymavlink):

| # | check | pass |
|---|---|---|
| D1 | `.BIN` downloaded, file size plausible, copied to two places; named `<sortie>_<date>.BIN` | yes |
| D2 | **LOG_REPLAY records present**: `RFRH`, `RFRF`, `RISH`, `RISI`, `ROFH`, `RRNH`, `RRNI` counts > 0; `RFRH` at ≈ 400 Hz | all present |
| D3 | `RFRH` continuity: no gap > 50 ms between take-off and landing | none |
| D4 | **`DSF.Dp` = 0** (no dropped writes) for the whole flight | 0 |
| D5 | `PARM` dump in the log: AHRS_EKF_TYPE = 3, LOG_REPLAY = 1, the EK3_SRC1_* and sensor values as filed | as filed |
| D6 | `ARM`/`EV` records: one arm and one disarm; both sync wiggles visible in `RISI` gyro (rates > 2 rad/s) **while disarmed** | yes |
| D7 | **Mocap file present** (`<take>.csv`, exported as `t_s, x, y, z, qx, qy, qz, qw`, metres, z up), covering both sync wiggles; tracking loss in the flight < 0.5 s cumulative | yes |
| D8 | **Mocap synced:** `mocap_align` run on this sortie: clock map early and late windows found, residual reported, rate within ±100 ppm | yes (residual noted) |
| D9 | Sortie sheet complete: class (VERIFICATION/RESULT), battery, times, take name, any deviation | yes |

A RESULT sortie failing D2–D4, D7 or D8 is excluded under the pre-registration §3.3 (the reason recorded) BEFORE any
estimator is run on it.

---

## 8. End of day

- [ ] All logs and mocap takes copied to the workstation (`~/thesis_data/realflight/<date>/`) and a second medium.
- [ ] Sortie sheet scanned/transcribed; verification and result sorties clearly separated (directory per class).
- [ ] Vehicle: batteries to storage charge; props inspected.
- [ ] No estimator is run on a result log until the pre-registration's §6 timestamp value and §5 bound are recorded
      (from the verification logs).
