# Rung 1 flight cards (R11): DRAFT

**Status: DRAFT, written 2026-10-10, not yet used.** To be walked through once with the safety pilot and the mocap
operator before the bench day, and amended there. Placeholders: **[TBD-S]** (supervisor/vehicle input).

**Amended 2026-10-12** (rulings 1, 2 and 7 of "RULINGS (user, 2026-10-12, safety first)", METHODOLOGY; handover
`docs/handovers/2026-10-12_f7_cards.md`):
- the EKF ORIGIN is set and VERIFIED at every power-on, and there is NO ARMING without it (§1a, B6, §7 D10);
- the F7 yaw check is a card step before every arming (§1a step 6, §4, §5);
- U4: take off within 5 s of arming (§4, §5);
- the mocap rigid body's x axis along the nose (§1);
- the sync wiggle in the first log run through the converter acceptance (B9).

**Amended 2026-10-12 (later)**, "RULING (user, 2026-10-12): F8 mitigations M1, M2, M3 APPROVED" (METHODOLOGY; the
mechanism in `docs/handovers/2026-10-12_f8_investigation.md`; handover `docs/handovers/2026-10-12_m2_full_bench.md`).
None of them changes EKF3's configuration:
- **M1:** power-cycle the FC before ANY re-arm after a landing, then the whole §1a again (origin set and re-verified)
  (§1a "M1", §4, §5, §6 ABORT – LURCH, §7 D12);
- **M2:** the EKF velocity pre-arm check: |v| < 0.2 m/s for 5 s with the vehicle still; manual on rung 1, the
  watcher's arming check on rungs 2–3 (§1a step 7, §5, B10);
- **M3:** land in ALT_HOLD where safe; after any LAND-mode touchdown the SP disarms within 2 s (§0, §5 step 4, §6);
- M4 (stated): U4 (take off within 5 s of arming) does NOT address F8; the bad velocity exists before arming.
The verification/result classification below is unchanged.

**Amended 2026-10-12 (latest)**, ruling 5 of "RULINGS (user, 2026-10-12): on the full watcher bench `wbench4`"
(METHODOLOGY): **NO RE-ARM WITHIN 10 s OF ANY DISARM** (§1a "M1", §5 pre-arm, §7 D12). It codifies M1's implication
and closes the ~3.3 s gap in which the FC itself still accepts an arm after the watcher has withdrawn (the FC refuses
only once `FS_GCS_TIMEOUT` (3 s) has passed without the watcher's heartbeat; handover
`docs/handovers/2026-10-12_m2_full_bench.md` §4 item 3).

Governing documents: `docs/rung1_preregistration_draft.md` (what is flown and scored; ON HOLD until the supervisor
confirms the hardware, so the RESULT card's profile follows it only once it is signed off), `docs/minimal_real_flight_plan.md`
(the plan), `realflight/params/rung1_template.parm` + one compass variant (the parameters).

**Classification (METHODOLOGY standing rule, 2026-10-10):** every card says whether it is **VERIFICATION** (shortest
profile that exercises the check; never scored, never reused as result data) or **RESULT** (pre-registered; scored).

| card | class | length | scored? |
|---|---|---|---|
| §2 bench B1–B8 | VERIFICATION | each ≤ 1–2 min (B8 ~5 min of checking) | **never** |
| §3 hand-carried pass | VERIFICATION | ~2 min | **never** |
| §4 first hover | VERIFICATION | ~1.5–2 min airborne | **never** |
| §5 result sortie | RESULT | the pre-registered profile (~2.5–3.5 min) | yes, under the pre-registration |

**Verification sorties are excluded from scoring and are never reused as result data, whatever they show.** Their logs
may be used only for what their card states (pass/fail of the check, the pipeline rehearsal, the Replay-fidelity bound
and the flow-delay calibration of the pre-registration §5–§6). They are stored in a separate directory from result
sorties (§8).

Rung 1 does NOT use the mocap watcher, the Pi or `realflight/params/watcher_fc.parm` (those are rungs 2–3). Nothing of
ours steers: safety is the safety pilot, the FC's altitude fence and failsafes, and a person watching mocap.

---

## 0. Roles

| role | who | duties | authority |
|---|---|---|---|
| **Safety pilot (SP)** | [TBD-S] | flies every armed sortie in ALT_HOLD; owns the transmitter, the mode switch (STABILIZE / ALT_HOLD / LAND) and the disarm; lands in ALT_HOLD where safe and, after ANY touchdown in LAND mode, disarms within 2 s (M3) | **final authority** in the air: calls and executes every abort |
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
- [ ] `python3 realflight/params/check_parm.py --final rung1_template.parm rung1_variant_<x>.parm rung1_failsafe_fc.parm` → **OK (final)**
      (no TODO_SUPERVISOR left; never AHRS_EKF_TYPE 10; no SIM_*).
- [ ] The offline pipeline runs on an existing SITL log end to end (Replay with the R2 port, converter, scorer), so
      that the same-day rehearsal after H is only a data change.
- [ ] Mocap rigid body defined on the vehicle (≥ 4 markers, asymmetric); its pivot near the FC; marker offsets measured.
- [ ] **Rigid-body axes (2026-10-12): the rigid body's +x axis lies along the vehicle's NOSE, +z up.** This is required
      by the cross-track metric (pre-registration §4.4) and by the F7 yaw check.
  - How: place the vehicle level with its nose along a taped line on the mocap +x axis. Create the rigid body with its
    local axes aligned to the mocap world axes at that moment.
  - Check: with the vehicle on the line, the mocap heading reads 0° ± 2°. Turned by hand to face +y, it reads 90° ± 2°
    (record the sense the mocap software uses).
  - Record the residual offset d° on the sheet. It adds `speed · sin(d)` of common-mode lateral rate, about
    0.42 m/min per degree at 0.4 m/s (pre-registration §4.4).
  - If the asset cannot be re-defined, the offset goes into the watcher's `--body-yaw-offset-deg` (rungs 2–3) and is
    recorded.
- [ ] Sortie log sheet printed (one row per sortie: id, class, battery, start/end FC time, mocap take name, notes).

---

## 1a. Power-on procedure: EKF ORIGIN and the F7 yaw tie (EVERY boot of the FC, every card below)

**Why** (METHODOLOGY RULINGS 2026-10-12, rulings 1 and 2):
- Without an EKF origin, Copter's EKF failsafe never runs (`ekf_check.cpp:35-39`). A no-origin EKF3 also reports
  (0, 0) after an aiding loss, and in SITL the vehicle ran away at 3.6 m/s (B8a). With a verified origin, the stock EKF
  failsafe landed the vehicle 1.94 s after the flow stopped (B8a repeat).
- F7: the stock arming checks allowed arming with a 22° EKF yaw error, and the vehicle flew away on take-off
  (wbench2, A9). On a flow-only vehicle a yaw error means a flyaway.

Steps (GS; repeated after ANY reboot of the FC, including a parameter reboot):
1. **The vehicle is on the start mark, level, with its nose along the mocap +x axis (the taped line). It stays STILL**
   from power-on until step 5.
   - **Rungs 2–3:** the mocap watcher must ALREADY BE RUNNING and receiving the FC's ATTITUDE before the FC's origin is
     set. With `--yaw-tie origin` it captures the yaw tie from the FC's one-off `GPS_GLOBAL_ORIGIN` broadcast. A
     watcher started later never ties, and it refuses to confirm until the FC is rebooted.
2. **Wait until EVERY EKF3 core has initialised.** The boot messages show "EKF3 IMUn initialised" for every core in
   `EK3_IMU_MASK` (`EK3_IMU_MASK` is read back in B1).
3. **Only then set the origin.**
   - With `AHRS_OPTIONS 16` and the `AHRS_ORIGIN_*` parameters (`rung1_failsafe_fc.parm`), the FC sets it itself as
     soon as EKF3 accepts it ("AHRS: using recorded origin"). AHRS retries every update (`AP_AHRS.cpp:446-447`).
   - Otherwise the GS sends `SET_GPS_GLOBAL_ORIGIN` (the lab's lat/lon/alt), but only after step 2. This is the same
     logic as the SITL harness's `bench.py establish_origin`. A GS tool for the real link is **[open]**.
   - An origin sent before EKF3 has initialised is silently rejected (`setOriginLLH`, `AP_NavEKF3_Control.cpp:686-696`).
4. **VERIFY the origin:**
   - (a) the FC sends a `GPS_GLOBAL_ORIGIN` (request it with `MAV_CMD_REQUEST_MESSAGE` 49) with the lat/lon that were
     set;
   - (b) after the sortie, this boot's dataflash holds an `ORGN` record BEFORE the ARM event (§7 D10).
   - **NO ARMING without (a).** If (a) still fails after 30 s of retries: reboot and repeat from step 1.
   - If (b) is missing after a sortie: no further sortie until the cause is found. This is a safety stop, not a scoring
     exclusion: the pre-registration §3.3 is unchanged.
5. **Record the yaw tie (F7).** The tie is the FC yaw of a vehicle whose nose points along the mocap +x axis.
   - **No-compass variant.** EKF3 starts at yaw 0 (`AP_NavEKF3_core.cpp:527`), so only this boot fixes the tie.
     - Tie = the FC yaw (`ATTITUDE.yaw`) minus the mocap heading, averaged over ~1 s at the origin step, with the
       vehicle still.
     - Rungs 2–3: the watcher does this itself.
     - Rung 1: the GS writes both numbers and the tie on the sheet.
   - **Compass variant.** The tie is the SURVEYED bearing of the mocap +x axis, measured once in stage 0 (the watcher's
     `--yaw-tie <deg>`). At this step the measured FC-minus-mocap value must also lie within 5° of it. Otherwise the
     compass is unusable in the volume: NO-GO.
6. **The F7 yaw check, before EVERY arming** (also after a carry, a landing or a long wait):
   - |FC yaw − (mocap heading + tie)|, wrapped to ±180°, must be **≤ 5° and steady for ≥ 1 s**, with the rigid body
     tracked. Otherwise NO-GO: do not arm. Reboot the FC and repeat from step 1. Under the compass, wait for the
     compass to converge instead.
   - **Rung 1** (no watcher): a manual GS check of the FC yaw on the GCS against the mocap heading read by MO. It is a
     card line, signed off by GS before "GO".
   - **Rungs 2–3:** the watcher enforces it.
     - While the FC is disarmed, it withholds its confirmation and logs the reason "yaw …". It then sends no MAVLink
       heartbeat, so the FC cannot arm; the Lua path refuses too.
     - Once the FC is armed, the check is informational only and never lands the vehicle.
   - **Ground drift under no compass.** The EKF yaw drifts with the gyro bias (SITL in flight: +6.6…+11.1°/min).
     - A long wait between the origin step and arming can itself exceed 5°.
     - After a sortie the FC is rebooted before the next one (M1 below), which repeats steps 1–7.
7. **M2: the EKF velocity check, before EVERY arming** (F8; ruling 2026-10-12 M2). Vehicle on the start mark, STILL.
   - The FC's EKF velocity, `LOCAL_POSITION_NED` vx, vy, vz on the GCS (3-D magnitude), must stay **< 0.2 m/s for
     5 s continuously** while MO confirms from mocap that the rigid body is tracked and not moving. Otherwise NO-GO:
     do not arm; power-cycle the FC (M1) and repeat from step 1.
   - **Why:** after a landing, EKF3's flow gate can lock one axis out on the ground while the other axis keeps every
     fall-back off, so EKF3's velocity runs away (1–2 m/s in SITL) while the vehicle sits still, and NO stock arming
     check looks at it (F8; 5 of 46 SITL arms, ALL re-arms after a landing in the same boot). `EKF_STATUS_REPORT`
     cannot show it (its velocity variance stays small), so read the velocity itself.
   - `LOCAL_POSITION_NED` exists only once the origin is set (step 4). No velocity shown = no origin = NO-GO.
   - **Rung 1** (no watcher): a manual GS card line, signed off before "GO".
   - **Rungs 2–3:** the watcher enforces it (`realflight/watcher/velcheck.py`, `--vel-check require`). While the FC is
     disarmed it withholds its confirmation (reason "vel …"), so the FC cannot arm; armed, it is informational only and
     never lands the vehicle.

**M1: power-cycle the FC before any re-arm after a landing** (F8; ruling 2026-10-12 M1).
- Every F8 runaway in SITL followed a landing in the same boot; 0 of 10 first arms of a boot showed one.
- After ANY landing (a normal one, an abort, a bounced landing, "land and go again"), the vehicle is NOT re-armed in the
  same boot: disarm, power-cycle the FC (a battery change does this only if the FC is powered from the flight battery:
  **[TBD-S] confirm the real power wiring**; otherwise a deliberate reboot), then §1a steps 1–7 again: the origin set
  and RE-VERIFIED, the tie, F7, M2.
- A battery change between sorties is therefore also a §1a restart.
- **No re-arm within 10 s of ANY disarm** (ruling 5, 2026-10-12), whatever the reason for the disarm (a landing, an
  aborted arm, a bench arm, a disarm on the ground without a flight). GS calls the 10 s from the disarm; SP does not
  touch the arm input before the call.
  - Why: after a disarm the watcher withdraws at once if EKF3's velocity runs away (M2), but the FC itself refuses
    an arm only ~3.3 s later (`FS_GCS_TIMEOUT` 3 s without the watcher's heartbeat). Inside that gap only M1 and this
    rule stop a manual re-arm. 10 s covers the gap with margin, and M2's own 5 s hold.
  - After a landing M1 applies as well (the power-cycle and §1a take far longer than 10 s); this rule is the one that
    still applies to a disarm WITHOUT a landing.

---

## 2. Bench checks (props OFF): VERIFICATION

Each is the shortest check of one fact. Logging on (`LOG_DISARMED 1`). Not scored. **Card B is complete only when every
line passes; any FAIL stops the day's flying until fixed.**

| # | check | how | duration and why it suffices | pass |
|---|---|---|---|---|
| B1 | **Parameter readback** | download all parameters from the FC; diff against `rung1_template.parm` + the variant + `rung1_failsafe_fc.parm` (2026-10-12); **AHRS_EKF_TYPE = 3**, LOG_REPLAY = 1, LOG_DISARMED = 1, ARMING_SKIPCHK = 0, GPS1_TYPE = 0, EK3_SRC1_* as filed. If any differs: PARAM_SET, reboot, read back again (eeprom gotcha) | ~2 min: a readback is a single dump | every value as filed |
| B2 | **Sensors healthy** | ground station status: flow sensor, rangefinder, compass (healthy even in nomag: arming gate), IMU, logging | ~1 min: a status screen | all healthy; no pre-arm message other than the expected "props off" items |
| B3 | **Rangefinder** | on the ground: reading ≈ `RNGFND1_GNDCLR`; then lift the vehicle by hand to ~1 m and back | ~30 s: one lift spans the range used | ground reading within ±2 cm of GNDCLR (or "out of range low" if RNGFND1_MIN > resting height: RECORD, it is a known limit, §9 item 11 of the pre-registration); ~1 m when lifted |
| B4 | **Flow sign (ArduPilot's standard flow check)** | over the textured floor, at ~0.5–1 m, roll the vehicle by hand left/right, then pitch forward/back, ~3 cycles each | ~1 min: three cycles per axis show the sign unambiguously | in the log, `OF.flowX` follows `OF.bodyX` and `OF.flowY` follows `OF.bodyY` (same sign, similar size). If not: `FLOW_ORIENT_YAW` is wrong; fix and repeat |
| B5 | **Arming checks run** | attempt to arm with props off (motor safety per lab rules) | ~30 s | arming either succeeds with every check run, or fails only on the props-off/safety item; never a skipped check |
| B6 | **Fence and EKF origin** (origin procedure re-written 2026-10-12, ruling 1) | ground station fence status; then the §1a origin procedure, steps 1–5 (every EKF3 core initialised FIRST, then the origin, then verified) | ~30 s | altitude fence enabled, FENCE_ALT_MAX as filed, no pre-arm fence error; the reported height ≈ 0 on the ground; the origin set only after "EKF3 IMUn initialised" for EVERY core; a `GPS_GLOBAL_ORIGIN` received with the lat/lon that were set; an `ORGN` record in the bench log (B8). (The old pass line, "AHRS: using recorded origin" seen, is not sufficient on its own.) |
| B6b | **F7 yaw check** (ruling 2) | §1a steps 5–6 on the bench: record the tie; then turn the vehicle by hand to +90°, HOLD IT STILL ≥ 5 s, and turn it back (the FC sees the turn, so the check must keep passing) | ~1 min | \|FC yaw − (mocap heading + tie)\| ≤ 5° at rest before the turn, **while held at +90°** (this tests the heading SENSE: a wrong sense reads ≈ 180° there and ≈ 0° again after the return) and after the turn back; the tie on the sheet |
| B7 | **Failsafes** | RC transmitter off for 2 s (props off, disarmed): RC failsafe message; battery failsafe values read back | ~1 min | messages as expected; values as filed |
| B8 | **Log completeness** | download the bench log; run §7 items D2–D5 on it | ~5 min of checking; the log is the B1–B7 period | LOG_REPLAY records present; `DSF.Dp` = 0 |
| B9 | **Sync wiggle in the first acceptance log** (2026-10-12) | before B8's download, with the vehicle disarmed on the bench: a sync wiggle (~5 s, sharp rotations about all three axes, \|ω\| > 2 rad/s); then run `eval/bin2fgo_accept.py` on the B8 log | ~1 min: the wiggle is what A5 tests against | the converter's A5 (IMU against the FC's own IMU record) is TESTED and passes. Without a wiggle in the disarmed span, A5 is NOT TESTED and the converter is NOT accepted on that log (METHODOLOGY, rung-1 scoring items). The first real log that goes through the acceptance must contain the wiggle |
| B10 | **M2 EKF velocity check** (2026-10-12) | §1a step 7 on the bench, vehicle still: read `LOCAL_POSITION_NED` vx, vy, vz on the GCS for 5 s; then carry the vehicle by hand ~1 m and set it down; read again for 5 s | ~1 min | \|v\| < 0.2 m/s at rest before and after the carry; the at-rest maximum on the sheet (rungs 2–3: the watcher's B12, `real_flights_plan.md` §7.2) |

The B4 wiggle and the bench rotations are also the input for the flow-delay measurement (pre-registration §6).

---

## 3. Hand-carried pass in the volume (disarmed, props OFF): VERIFICATION

**Length: ~2 min.** *Why it suffices:* disarmed, EKF3 stays "on ground" (`AP_NavEKF3_VehicleStatus.cpp:466-480`) and
does not navigate on flow, so a longer carry tests nothing more. One leg exercises the plumbing, the mocap clock map,
the flow sign over the real floor and Replay reproduction of a non-aiding EKF3. **Never scored.**

0. Power-on procedure §1a, steps 1–5: the origin set and verified, the tie recorded. The vehicle is never armed, so
   step 6 does not apply.
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

Card: as the result card (§5), including its pre-arm block (M1, the origin verified, the F7 yaw check, M2, U4), with this
profile instead: take-off to h **within 5 s of arming** → hover 45 s → 2 m forward and back at ≤ 0.3 m/s → hover 10 s →
land. Sync wiggles before arming and after disarming as usual.

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
- [ ] **EKF origin verified at this boot** (§1a steps 2–4): every core initialised before it; `GPS_GLOBAL_ORIGIN`
      received with the lat/lon that were set. **NO ARMING without it.**
- [ ] **M1:** NO landing earlier in this FC boot (after any landing in this boot → power-cycle and redo §1a; a
      props-off bench arm without a flight does not count)
- [ ] **No re-arm within 10 s of any disarm** (ruling 5, 2026-10-12): last disarm at __:__:__; GS calls "10 s" before
      the arm
- [ ] **F7 yaw check** (§1a step 6): tie __°; FC yaw __°; mocap heading __°; |diff| = __° **≤ 5°**, steady ≥ 1 s,
      rigid body tracked. Rungs 2–3: the watcher shows confirmed (no "yaw" reason).
- [ ] **M2 EKF velocity check** (§1a step 7): vehicle still (MO); `LOCAL_POSITION_NED` |v| max over 5 s = __ m/s
      **< 0.2**. Rungs 2–3: the watcher shows confirmed (no "vel" reason).
- [ ] M4 (stated): U4 below does NOT address F8. Taking off quickly cannot clear a bad pre-arm velocity; M1 and M2 do.
- [ ] **U4 (ruling 7): take off within 5 s of arming.** SP and GS agree that the take-off follows the arming at once.
      If the take-off is delayed beyond 5 s after arming: DISARM, and re-arm when ready.
      - Why: if the rangefinder reads below its minimum on the ground, the UKF's vertical flags lapse 5 s after arming
        (`RNG_TIMEOUT_MS`).
      - A proper fix is deferred to the closed-loop work.
- [ ] Volume clear of people (Observer: "CLEAR")
- [ ] GS: "GO" / "NO-GO"

Profile (SP flies; GS calls the times from a stopwatch started at take-off):
1. [ ] Sync wiggle, disarmed (~5 s); set down on the start mark; stand clear
2. [ ] Arm; **take off within 5 s of arming (U4)** to h = __ m; **hover 30 s** over the start mark
3. [ ] **Two laps** of the rectangle/out-and-back (legs __ m; FIRST LEG = 3 m if the mocap volume allows it with the 2 m clearance at both ends, otherwise ≥ 2 m, so that U10 G5 can be computed; ruling 2026-10-13, PENDING the supervisor's room size) at ~__ m/s (~90 s); GS calls each corner
4. [ ] Hover 10 s over the start mark; **land in ALT_HOLD** (M3: throttle down to touchdown, then disarm at once).
      If LAND mode was used (an abort, or ALT_HOLD judged unsafe): **SP disarms within 2 s of touchdown** (M3; do not
      wait for the FC's land detector: F2/F8, the phantom velocity can make LAND lean the vehicle on the ground). After
      this landing, no re-arm in this boot (M1)
5. [ ] Sync wiggle, disarmed (~5 s); MO: stop the take; GS: note the end time
6. [ ] GS: anything unusual (gusts from air conditioning, a skipped leg, a pilot correction) noted on the sheet

---

## 6. Abort criteria (any sortie)

Called by anyone; **SP executes**. Default action: **LAND mode** (switch), or SP lands manually in ALT_HOLD if LAND
would be worse. **STABILIZE** is the last resort if ALT_HOLD misbehaves (height oscillation, climb-away).
**M3 (2026-10-12):** where it is safe, SP lands in ALT_HOLD rather than LAND. After ANY touchdown in LAND mode, SP
disarms **within 2 s** (this tightens the earlier F2 rule from 4 s): on the ground EKF3's phantom velocity (F8) makes
LAND demand up to 30° of lean, the land detector never trips, and in SITL the vehicle tipped over (F2, B9b).

| call | condition | action |
|---|---|---|
| ABORT – BOUNDARY | the vehicle within 1.0 m [TBD-S] of a volume wall/net, or above the fence altitude (the fence lands it anyway) | SP stops, returns to centre if safe, else LAND |
| ABORT – MOCAP | MO: rigid body lost > 1 s | SP holds position by sight and lands (the flight is then excluded, §3.3) |
| ABORT – HEIGHT | ALT_HOLD height oscillating > ±0.3 m, or an uncommanded climb/descent | STABILIZE if needed, land |
| ABORT – FAILSAFE | any failsafe message (EKF, battery, RC, fence) | the FC's action stands; SP takes over only if it is unsafe |
| ABORT – VEHICLE | vibration, noise, a loose part, smoke, a motor/ESC fault | land immediately; disarm; LiPo procedure |
| ABORT – LURCH | an uncommanded horizontal lurch or drift on take-off (F7: a yaw error; F8: EKF3's velocity diverged on the ground before arming) | SP takes ALT_HOLD/STABILIZE at once, lands, disarms (within 2 s of touchdown if in LAND, M3); GS records it; the next arming only after a power-cycle (M1) and §1a steps 1–7 again |
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
| D8 | **Mocap synced:** `mocap_align` run on this sortie; its default windows (since 2026-10-11) are the two DISARMED sync-wiggle bursts (`RISI` \|ω\| > 2 rad/s: the last burst before arming and the first after disarming, ± 2 s; the old default, arm to arm + 25 s, missed the pre-arm wiggle). Check `window_sources` in the JSON. A hand-carried (never armed) log needs `--early`, `--late` and `--init-seg` given explicitly. Both found, residual reported, rate within ±100 ppm | yes (residual noted) |
| D9 | Sortie sheet complete: class (VERIFICATION/RESULT), battery, times, take name, any deviation | yes |
| D10 | **EKF origin in the log** (ruling 1): an `ORGN` record in this boot's dataflash BEFORE the ARM event; the boot's "EKF3 IMUn initialised" messages (every core) precede the origin | yes. If not: no further sortie until the cause is found (a safety stop; NOT a scoring exclusion, since the pre-registration §3.3 is unchanged) |
| D11 | **F7 and U4 as flown:** the sheet's yaw-check line filled in (\|diff\| ≤ 5°); the `ARM` event to take-off (the first `CTUN`/`RFND` climb) ≤ 5 s | yes. A deviation is recorded; it does not change the classification |
| D12 | **M1/M2/M3 as flown (2026-10-12):** no landing (`EV` LAND_COMPLETE / LAND_COMPLETE_MAYBE after a take-off) before this sortie's `ARM` in this boot's log (M1); the sheet's M2 line filled in, and `XKF1` (core 0) √(VN²+VE²+VD²) < 0.2 m/s over the 5 s before `ARM`; if the landing was in LAND mode, the disarm ≤ 2 s after touchdown (`EV` LAND_COMPLETE_MAYBE) (M3); every `ARM` ≥ 10 s after the previous disarm `ARM` record in the same boot (ruling 5, 2026-10-12) | yes. A deviation is recorded and is a safety stop for the day until understood; it does not change the classification |

A RESULT sortie failing D2–D4, D7 or D8 is excluded under the pre-registration §3.3 (the reason recorded) BEFORE any
estimator is run on it.

---

## 8. End of day

- [ ] All logs and mocap takes copied to the workstation (`~/thesis_data/realflight/<date>/`) and a second medium.
- [ ] Sortie sheet scanned/transcribed; verification and result sorties clearly separated (directory per class).
- [ ] Vehicle: batteries to storage charge; props inspected.
- [ ] No estimator is run on a result log until the pre-registration's §6 timestamp value and §5 bound are recorded
      (from the verification logs).
