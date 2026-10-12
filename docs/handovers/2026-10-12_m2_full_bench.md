# Handover, 2026-10-12: M2 in the watcher, M1–M3 on the cards, and the FULL watcher bench with everything in (`wbench4_*`)

**Stage:** "RULING (user, 2026-10-12): F8 mitigations M1, M2, M3 APPROVED" (METHODOLOGY, last entry): M2 as a watcher
arming check, M1–M3 on the flight cards (B12 in `docs/real_flights_plan.md` §7.2), then ONE full watcher bench in SITL
with everything in (the F7 yaw check, M2, the H10 guard). The SITL sessions are VERIFICATION only (STANDING RULE
2026-10-10: short, never result data). Not edited: METHODOLOGY.md, fly_trial.py, run_trial.sh.

## 0. The M2 rule (code under test; `realflight/watcher/velcheck.py`)

- **While the FC is DISARMED** (or its arming state unknown), the watcher withholds its confirmation unless, held
  **continuously for ≥ 5 s**:
  1. **EKF velocity:** the 3-D Euclidean norm √(vx² + vy² + vz²) of MAVLink `LOCAL_POSITION_NED` (vx, vy, vz: the
     AHRS / primary EKF3 core NED velocity, `GCS_Common.cpp:3042-3061`) is **< 0.2 m/s on every sample**. All three
     components (the ruling names EKF3's velocity, unqualified). F8 was horizontal (lowest core-0 case 0.26 m/s), so the
     3-D norm catches all five F8 cases and is stricter. Stored bench logs (`wbench2_hoverB_…114206`, XKF1 core 0):
     |VD| ≤ 0.08 m/s in the 2.5 s before every arm.
  2. **Vehicle stationary (mocap):** on every mocap pose, the translational speed over a 0.5 s baseline,
     |p(t) − p(t − 0.5 s)| / Δt with Δt ≥ 0.4 s, is **< 0.05 m/s** (not a per-frame difference, which is
     noise-dominated at 100 Hz; rotation in place is not "motion": the F7 check covers heading).
  3. **Mocap valid** (fresh and tracked: the watcher's own rules).
  4. **`LOCAL_POSITION_NED` fresh:** the latest ≤ 0.5 s old. The FC sends it only once the AHRS has a position
     relative to the EKF origin (`GCS_Common.cpp:3047-3051`): **no origin → refused** (fail-closed).
  - Any single violation (a velocity sample ≥ 0.2, a moving or invalid pose, a stale `LOCAL_POSITION_NED`, too little
    pose history to measure the speed) restarts the 5 s.
- **Once the FC reports ARMED: INFORMATIONAL ONLY** (computed and logged, never withdraws the confirmation, never
  latches, never LANDs). A disarmed withdrawal on M2 is not a breach (no latch, no LAND), exactly as the F7 check.
- Withholding the confirmation = no MAVLink HEARTBEAT (the FC's GCS failsafe / Lua path refuse to arm) and file flag
  `box=0` (the flight script refuses).
- Wiring: `fc_link.request_streams` asks for `LOCAL_POSITION_NED` at 10 Hz (re-asserted every 2 s with the others);
  `('lpn', vx, vy, vz, time_boot_ms)` events; `core.on_fc_lpn`; `mocap_watch.py --vel-check require|off` (default
  require), `--vel-max 0.2`, `--vel-sustain-s 5`, `--vel-still-mps 0.05`; `mocap_watch_vel.csv` (every
  `LOCAL_POSITION_NED`: vx, vy, vz, |v|, the mocap speed, the hold time, the verdict); a `vel=` token in
  `watch_heartbeat`; summary lines. The library `Config` and the test `Rig` default it OFF (earlier tests unchanged).
- **Offline:** `pytest realflight/` → **118 passed** (106 before + 12 new in `realflight/watcher/tests/test_vel.py`;
  one existing assertion updated: `test_f6_heartbeat_rate_is_requested` now expects the `LOCAL_POSITION_NED` interval
  request too, ids {30, 0, 32}):
  - pass only after 5 s still and slow (|v| 0.164 passes);
  - **the F8 ground runaway** (mocap stationary, VE ramping at 0.145 m/s² past 0.2) → withdrawn at the crossing, ALERT
    "arming refused (F8)", refused for the next 20 s, no LAND, no latch;
  - a single 0.25 m/s sample resets the 5 s (confirms only ≥ 5 s after the spike);
  - mocap not stationary (0.3 and 0.06 m/s) → never confirms; 0.03 m/s counts as still; set down → 5 s later;
  - `LOCAL_POSITION_NED` never received (no origin) → refused; stale 0.7 s → refused, then a fresh 5 s;
  - mocap untracked → refused; a vz-only −0.25 m/s → refused;
  - **armed: |v| 1.2 m/s and moving → confirmation kept, no LAND, no ALERT**; disarmed again → gated;
  - end to end with the FakeFC (`LOCAL_POSITION_NED` added to it): the runaway withdraws the heartbeat, the FC model
    refuses to arm ("GCS failsafe"), no LAND/BREACH; converged → heartbeat back ≥ 4.5 s later and the arm is allowed;
    no `LOCAL_POSITION_NED` → never confirms; armed runaway → heartbeat continues, no LAND.

## 1. RE-REGISTRATION of the full bench `wbench4_*` (written and committed BEFORE any SITL session of this stage)

Base: the 2026-10-11 pre-registration (`2026-10-11_watcher_sitl_bench.md` §1, amendments A1–A8), the 2026-10-12 re-run
re-registration (`2026-10-12_watcher_bench_rerun.md` §1.1–§1.3, amendments A9, A10) and the F7 pre-registration
(`2026-10-12_f7_cards.md` §1.1–§1.5) apply UNCHANGED except where this section says otherwise. Any change after this
commit is a dated amendment in §1.6; no criterion is edited after data are seen.

### 1.1 Set-up: "everything in" (`tools/run_wbench.sh <session> --prefix wbench4 --checks all`)

- **S1 — the watcher's checks.** Every primary watcher runs `--yaw-check require` AND `--vel-check require`.
  - Sessions `ground`, `hoverA`, `hoverB`, `hoverC`, `m2` (the compass config, `EK3_SRC1_YAW 1`): **`--yaw-tie 90`**, the
    fixed SITL tie (Gazebo ENU, x = East; test `test_f7_sitl_tie_90_gazebo_enu`). The origin tie cannot be used here:
    B1-native, B9b, B9c, F6c, B10b(2) and M1 restart the watcher within a boot, and an origin-tie watcher never re-ties.
    **This is the first SITL run of the fixed-tie path** (unit-tested only so far).
  - Session `f7`: as registered (no compass, `--yaw-tie origin`, `--lua-auth`), plus `--vel-check require`.
  - The B6b observer (system ID 212) never gates arming: its yaw and velocity checks stay OFF.
- **S2 — H10 on every flight script.** Every bench flight script runs `--h10-guard`; the guard decision now calls the
  MERGED `fly_trial.fc_mode` and `fly_trial.H10_PILOT_OR_LAND` (harness edit in `flight_script.py`; `fly_trial.py`
  unchanged). Exercised: the passive FC-mode read and the pilot/LAND set (B10b(1), and any WatcherLost while the FC
  is already in LAND). Not exercised: `fly_trial.land()`'s takeover latch (covered by the mock test only).
  Declared consequence (the mock test's declared difference): on a WatcherLost with the FC already in LAND, the script
  sends no redundant LAND (in wbench2 the script's LAND followed the FC's own LAND, e.g. B2a +3.24 s). No criterion
  depends on that redundant LAND.
- **S3 — M1 in the harness.** Before every hover that follows a landing in the same FC boot: the carry home (A7/A9),
  then the watcher stopped, an FC reboot, a 45 s settle, the origin re-established and VERIFIED exactly as R1
  (`establish_origin`), then the watcher restarted with its previous arguments. So every hover is the first arming of
  its boot. Recorded as `M1_reboot`. (The F8 rate: 0 of 10 first arms showed a runaway.)
- **S4 — safety net.** If `ensure_watcher` does not see a confirmation within its 90 s cap and the watcher's ONLY
  reasons are M2 ("vel …"), the harness applies M1 once and waits another 90 s (recorded `M1_fallback`). Anything else
  aborts the session, as before.
- **S5 — M3 in the harness.** The simulated pilot (A7b) disarms after **2 s** on the ground in LAND (was 4 s).
- **S6 — sessions and order:** `ground`, `hoverA`, `hoverB`, `hoverC`, `f7`, `m2`; one simulation at a time, each
  through `tools/run_wbench.sh` (FLIGHT_LOCK; it waits for BUILD_LOCK, so it serialises with `heavy.py` builds),
  nothing heavy in parallel. Output `~/thesis_data/wbench/wbench4_<session>_<stamp>`. `bench.log` PROVENANCE must show
  no uncommitted change under `realflight/`. `--from`/`--only` only to resume an aborted session or for an A10 repeat
  (each use an amendment).

### 1.2 Criteria: unchanged, with the predicted M2/F7 interactions registered now

Every criterion of the base documents applies as worded: B0, B1a, B1b/B9d, B1c (i)–(iv), B1-native, B1c-Lua, B2a, B2b,
B3a, B3b, B4a (5 faces), B4b side, B4b top, B4c, B5a, B5b, B5b-noflag, B5c, B6a, B6b ×2, B7a, B7b, B8a, B9a ×2, B9b,
B9c ×2, B9-hang (observation), B10a, B10b (1)–(3), B10c, F6a, F6b, F6c, F7-0, F7-a, F7-b, F7-c, F7-d, plus the
validity rules R2 (an EKF failsafe before a test's criterion event voids it), A9 (|EKF − true yaw| ≤ 5° at every hover
ARM) and A10 (the incomplete-stimulus rule).

Predictions (written before any run; a miss is reported as worded, not re-worded):
- **B5c** (≥ 2.0 s of fresh poses before the confirmation returns): expected ≈ 5 s now (M2's hold restarts on the mocap
  outage), so PASS as worded, but it no longer isolates `recover_s`.
- **F7-a, F7-c** (re-confirmed within 5.0 s of the rotate-back): `rotate_in_place` sets z 0.2 m at the same x/y (rest
  0.195 m), a ≤ 5 mm move: mocap speed over 0.5 s ≈ 0.01 m/s < 0.05, so M2's window is NOT reset and the bounds stand.
  If it is reset, F7-a/F7-c fail as worded.
- **F7-0 (a)** ("reasons yaw only"): M2 will have held ≥ 5 s by the probe (≥ 45 s after the FC came up, the origin set
  early, 8 s after the rotation): yaw only expected.
- **B1-native, B1c-Lua (b), F6c, B9b, B4a/B4c (re-confirm between faces), B3b's re-confirmation (observation):** every
  re-confirmation now needs M2's 5 s; none has an upper bound.
- **B10b (2)** ("a NEW watcher confirms" while airborne in ALT_HOLD): F7 and M2 are informational once the new
  watcher has seen an ARMED FC heartbeat; it confirms as before.
- **In-flight tests:** no change expected. **New cross-check X1:** in every session, no watcher withdrawal whose
  reasons include "yaw" or "vel" while the FC is armed (between ARM and DISARM in `op_events.csv`), and no watcher
  LAND/BREACH caused by either check (they cannot call `_breach`; checked in the logs).
- **X2:** every M1 reboot's origin verified on the first try (else the session aborts).

### 1.3 New test M2-R (session `m2`; the SITL counterpart of B12; NOT a hardware test)

**Purpose:** show that the watcher refuses arming during a REAL EKF3 ground velocity runaway (F8), and that after M1
arming is allowed.

**Stimulus (faithful to F8, `2026-10-12_f8_investigation.md` §2.1, §2.9):** a landing followed by a re-arm in the SAME
boot (M1 is deliberately NOT applied between the attempts: this is the exposure M1 exists for). The F8 trigger is the
flow dropout on the final descent, which happens naturally in this SITL world below ~0.5 m camera height.
- Attempts 1–3 ("natural"): hover profile take-off 1.5 m / hold 5 s / LAND (GUIDED, flight script with H10); after the
  disarm (the FC's, or the simulated pilot's at 2 s, M3) watch 20 s.
- If none of 1–3 gives a runaway, attempts 4–5 ("flow-kill"): as 1–3, plus `flow_bridge.py` SIGKILLed when the true
  height drops below 0.75 m in the LAND descent (camera height ~0.5 m, where F8's tracker lost its features) and
  restarted at touchdown (true height < 0.23 m or disarm): the same dropout, made certain. Justified as faithful: F8's
  mechanism is exactly a flow dropout on the final descent followed by flow returning on the ground.
- Each next attempt re-arms only once the watcher confirms (i.e. M2 passed: the vehicle still and |v| < 0.2 for 5 s).
- **Runaway detected (V1)** when the operator-link `LOCAL_POSITION_NED` 3-D |v| ≥ 0.2 m/s continuously for ≥ 1.0 s,
  the FC disarmed, and the Gazebo truth speed (forwarder, 0.5 s baseline) < 0.05 m/s.
- **None in 5 attempts:** M2-R is NOT COMPLETED (reported), nothing more is run.

**After detection:**
- **Probe**, at ≥ 0.5 s after detection AND ≥ 3.5 s after the watcher's last confirmed tick (`FS_GCS_TIMEOUT` 3 s):
  (i) the operator's non-force MAVLink arm in GUIDED (system ID 255); (ii) the file flags at that instant (what
  `fly_trial.py`'s `watch_ok` reads).
- **V3 (probe validity):** every operator-link |v| sample in the 0.3 s before the probe ≥ 0.2 m/s (the runaway still
  on). If V3 fails, the session is repeated ONCE (A10), both reported.
- Then 6 s observed; then **M1:** the watcher stopped, FC reboot, 45 s settle, origin re-established and verified
  (R1), the watcher restarted; then the flight script's arm (`profile []`: arm, then LAND on the ground).

**PASS requires all of:**
- (a) from detection to the probe, the watcher's file never shows confirmed (20 Hz polls), and its last
  "confirmation 0" reason line at the probe contains a "vel …" reason and NO reason other than "vel …" (the refusal is
  M2's alone);
- (b) probe (i) is NOT armed (no ACK 0 / no ARM), and the FC texts include "GCS failsafe on";
- (c) at the probe the file has `box=0`, so `watch_ok` refuses ("watcher not confirming");
- (d) the watcher sends 0 LAND and logs no BREACH from the landing's disarm to the M1 reboot;
- (e) after M1, a `GPS_GLOBAL_ORIGIN` with the sent lat/lon is received (the origin re-verified);
- (f) the watcher confirms within 90 s of its restart, and the operator-link |v| < 0.2 m/s over the 5 s before;
- (g) the flight script then logs "Safety watcher confirmed before arming" and "Armed.".
- **Post-hoc validity V1b:** dataflash `XKF1` core 0 √(VN² + VE² + VD²) ≥ 0.2 m/s at the probe (± 0.5 s), and the
  truth stationary over the detection-to-probe span. If V1b fails, M2-R is reported INVALID (not PASS).

**Observations (not pass items):** the runaway's size, onset after touchdown and duration (operator link, the watcher's
`mocap_watch_vel.csv`, XKF1 cores 0/1); which attempt produced it; the 6 s after the probe (whether the watcher
would have re-confirmed in the same boot); the attempts' |v| maxima.

### 1.4 Why each length suffices (STANDING RULE 2026-10-10)

- The repeated sessions use the 2026-10-11/12 profiles and justifications unchanged; S3 adds ~60 s of reboot and
  settle per re-arm (not flight time).
- `m2`: ground plus ≤ 5 hovers of ~25 s airborne each (take-off 1.5 m at 0.5 m/s ≈ 3 s, 5 s hold, ~4 s descent): the
  landing is the stimulus; 20 s after each disarm covers F8's onsets (all at the touchdown) and its 6–10 s lock-out.

### 1.5 Not tested here (stated)

- The compass variant's F7 tie by origin; the fixed tie with no compass.
- B12 on hardware (`real_flights_plan.md` §7.2): the real `LOCAL_POSITION_NED` rate and noise at rest; a real runaway
  cannot be produced with the props off.
- `fly_trial.land()`'s takeover latch in SITL (mock-tested).

### 1.6 Amendments (dated, after this commit)

- **B1 (2026-10-12 ~17:16, after `wbench4_ground_20261012_170507` ABORTED; before any further run). No criterion
  change; a resume under S6.**
  - **What happened.** After B4c (the vehicle "carried" to roll 65° and dropped from 0.6 m, disarmed) EKF3 diverged
    on the ground while the vehicle lay still: the watcher's `LOCAL_POSITION_NED` |v| rose from 0.8 m/s at the drop
    to **192 m/s** within 90 s (mocap speed 0.000), and the FC yaw drifted to 24° off (mocap + tie). The watcher
    refused with BOTH a "vel" and a "yaw" reason, so the S4 M1 fallback (vel-only) did not apply, and `ensure_watcher`
    aborted after its 90 s cap, as registered. B1c-Lua was not reached.
  - This is the M2 and F7 checks refusing a genuinely diverged estimator (observation for §2; in wbench2 the same B4c
    was followed by B1c-Lua's reboot, and the watcher then had neither check).
  - **Resume:** a new session `tools/run_wbench.sh ground --prefix wbench4 --checks all --from B1c_lua` (a fresh SITL
    boot; B1c-Lua then reboots twice itself, as registered). Every test before B1c-Lua is taken from the aborted
    session, whose records stand.
- **B2 (2026-10-12 ~17:50, after `wbench4_hoverB_20261012_173841` ABORTED; before any further run). Harness fix (S3
  ordering) and a resume; no criterion change.**
  - **What happened.** After B9a (flow_bridge stub) landed, the session-level `ensure_watcher("--dep-loss", "stop",
    restart=True)` (B9b's set-up) ran BEFORE `hover()`'s M1, i.e. it demanded a confirmation after a landing in the
    same boot. EKF3 then ran away on the ground (|v| ≥ 0.2 throughout) and its yaw drifted (8–9.6° off, compass
    variant). The watcher refused with "vel" AND "yaw" reasons for the 90 s cap, so S4 did not apply and the session
    aborted, as registered. This is a second unplanned F8 occurrence refused by M2 (and F7) in this bench.
  - **Fix:** `ensure_watcher` now applies M1 first whenever a landing happened in this boot (the intent of S3: no
    confirmation is demanded after a landing without the power-cycle). The watcher logic is unchanged.
  - **Resume:** `tools/run_wbench.sh hoverB --prefix wbench4 --checks all --from B9b` (a fresh boot). B5b-noflag, B6b
    ×2, B8a and B9a ×2 are taken from the aborted session, whose records stand.
- **B3 (2026-10-12 ~18:08, after `wbench4_hoverC_20261012_175909`; before any further run). Harness fault; A10 repeat.**
  - **What happened.** In B10a the vehicle drifted in ALT_HOLD and, during the pilot's LAND, crossed x = −3.003 m: a
    box BREACH and a watcher LAND (the FC already in LAND; no mode change). That earlier "LAND command sent" line in
    the session's STOP_LOG satisfied B10b(2)'s unanchored search at once (`t_land_cmd_seen_w` = the kill time), and the
    follow-up check (anchored) then failed, so the simulated pilot's ALT_HOLD toggle was NEVER made: B10b(2)'s stimulus
    was incomplete (the vehicle completed the watcher's LAND). Under A10, **B10b is NOT COMPLETED** on this attempt.
  - **Fix:** `wait_text(..., since_bytes=nb)` for that search (harness only).
  - **Repeat once:** `tools/run_wbench.sh hoverC --prefix wbench4 --checks all --only B10b` (a fresh boot: B10b is then
    the first hover of its boot, unlike this attempt, which followed M1). Both attempts are reported. B10a, F6a and
    F6b are taken from this session.
- **B4 (2026-10-12 ~18:25, after `wbench4_m2_20261012_181437`; before any further run). Two harness faults; the one
  A10 repeat of M2-R.**
  - **What happened.** M2-R was recorded NOT COMPLETED (no runaway in 5 attempts), but the attempts did not run as
    registered: (i) in attempts 1–3 `wait_disarmed` returned at once on the operator link's stale pre-arm "disarmed"
    (`t_disarm_seen_w` = `t_arm_w`), so the 20 s runaway watch ran DURING the flight (no valid ground window);
    (ii) amendment B2's M1-in-`ensure_watcher` rebooted the FC before every attempt, contrary to §1.3 ("M1
    deliberately NOT applied between the attempts"). Attempts 4–5 (flow-kill) had valid ground windows: operator
    |v| max 0.015 and 0.267 m/s, never ≥ 0.2 for 1 s.
  - **Fix:** the attempt waits for the operator link to see ARMED before the disarm wait; M1 is suppressed during the
    attempts (re-enabled for the probe's M1 step).
  - **Repeat once (A10):** `tools/run_wbench.sh m2 --prefix wbench4 --checks all`. If it also yields no runaway, M2-R
    is reported NOT COMPLETED and nothing more is run.
- **B5 (2026-10-12 ~18:28, after `wbench4_m2_20261012_182305`, the B4 repeat; before any further run). V3 failed; one
  further repeat under §1.3's own V3 rule; a probe harness fault fixed.**
  - **What happened.** Attempt 1 produced a runaway (V1 met): on the ground after the disarm, the operator-link
    |v| was 0.42 → 0.69 m/s (VN ramping, truth still) and fell below 0.2 m/s 1.9 s after the disarm (the gate
    re-opened). The watcher withdrew with "vel EKF velocity |v| >= 0.2 m/s (F8)" and the ALERT (|v| 0.510) and
    re-confirmed 5.0 s after the runaway ended. The probe could only be made ≥ 3.5 s after the watcher's last confirmed
    tick (the FC-side refusal needs `FS_GCS_TIMEOUT`), at +12.4 s, when |v| was 0.02–0.06: **V3 FAILED**. Also, the
    probe's arm was refused "Arm: Land mode not armable" (the FC was still in LAND; the RC switch already at GUIDED,
    so `mav_arm` did not change the mode): a harness fault, not the watcher.
  - **Fix:** the probe commands GUIDED by MAVLink before arming (harness only). Probe timing and V3 unchanged.
  - **Repeat once (V3 rule, §1.3).** This is the last M2-R run whatever its outcome.

