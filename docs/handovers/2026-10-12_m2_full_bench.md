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


## 2. Results (`wbench4_*`, VERIFICATION data only, never result data)

All under `~/thesis_data/wbench/`; driver logs `run4_*.out`; per-session `analysis/results.txt`
(`python3 -m realflight.sitl_bench.results <session>`). Every session's `bench.log` PROVENANCE shows the committed HEAD
of its run and no uncommitted change under `realflight/`. One simulation at a time, each under FLIGHT_LOCK.

| session | content |
|---|---|
| `wbench4_ground_20261012_170507` | B1a, B1c (i)–(iv), B0, B1b, B5c, B6a, B1-native, B7b, F6c, B10c, B4a ×5, B4c; then ABORTED (B1) |
| `wbench4_ground_20261012_171552` | B1c-Lua (resume, B1) |
| `wbench4_hoverA_20261012_171840` | B2a, B2b, B3a, B3b, B4b side, B4b top, B5a, B5b, observations |
| `wbench4_hoverB_20261012_173841` | B5b-noflag, B6b ×2, B8a, B9a ×2; then ABORTED (B2) |
| `wbench4_hoverB_20261012_175117` | B9b, B9c ×2, B9-hang (resume, B2) |
| `wbench4_hoverC_20261012_175909` | B10a, B10b (attempt 1, NOT COMPLETED, B3), F6a, F6b |
| `wbench4_hoverC_20261012_180710` | B10b repeat (A10, B3) |
| `wbench4_f7_20261012_180923` | F7-0, F7-a, F7-b, F7-c, F7-d |
| `wbench4_m2_20261012_181437`, `…_182305`, `…_182609` | M2-R: the void first run (B4), the repeat (V3 failed, B5), the final repeat |

**Set-up checks.** All 37 origin establishments of wbench4 (initial boots, the Lua reboots and every M1 reboot) were
verified on the first try (**X2 PASS**). A9: |EKF − true yaw| at every hover ARM ≤ 0.2°. R2: every EKF failsafe falls
after its test's criterion event, except in B8a and B10b(3), where it IS the criterion; no test is voided.

### 2.1 Per test, as worded

- **B0 PASS** ("confirmed before arming", armed). **B1a PASS.** **B1b PASS** ("watcher not confirming (box=0 bridge=0)").
- **B1c:** (i) ARMED (predicted; stock FC side); **(ii) PASS** (not armed); (iii) ARMED (predicted); (iv) ARMED
  (predicted).
- **B1-native PASS:** refused ("Arm: GCS failsafe on"); after the restart "GCS Failsafe Cleared" (+6.48 s, M2's hold
  included) and the script armed.
- **B1c-Lua PASS:** (a) MAVLink and stick both refused "Watcher: never seen"; (b) the script armed; (c) refused ("GCS
  failsafe on", "heartbeat 6.1s old"); (d) force armed (predicted bypass).
- **B2a PASS:** LAND +2.22 s W (bound 4.0). First to act: the flight script's WatcherLost LAND (FC in GUIDED, so the
  H10 guard did not apply); the FC's GCS failsafe followed at +2.41 s.
- **B2b PASS:** FAILSAFE_GCS and MODE LAND +3.199 s F (bound 3.5).
- **B3a PASS:** +2.747 s F (bound 3.5); the watcher withdrew on "FC link lost", 0 LAND.
- **B3b PASS:** LAND +2.17 s W (bound 4.0); after SIGCONT 0 watcher LAND and no FC mode events.
- **B4a PASS (5 faces):** BREACH on the first outside pose (+0.000 s), one LAND each, ACKed, FC LAND; the arm after the
  north face refused.
- **B4b side PASS** (BREACH +0.001 s, FC LAND +0.032 s W, one LAND). **B4b top PASS** (+0.001 s, +0.007 s).
- **B4c PASS** ("BREACH: tilt 65.0 deg > 60.0", one LAND, ACKed, FC LAND).
- **B5a PASS:** stale +0.502 s (bound 0.525), LAND +0.561 s W (bound 1.0), withdrawn; the one heartbeat after the stop
  (+0.25 s) precedes the detection.
- **B5b PASS:** (1) no event while frozen with tracked = 1; (2) BREACH on the first untracked frame, LAND +0.075 s W.
- **B5b-noflag PASS:** frozen +0.500 s (bound 0.525), LAND +0.567 s W.
- **B5c PASS**, as predicted: the confirmation returned 7.53 s after the restore (≥ 2.0 s). M2's 5 s hold dominates,
  so the test no longer isolates `recover_s`. No command followed.
- **B6a PASS** (never confirmed; the script refused).
- **B6b run 1 PASS** (observer identity CONFIRMED, max roll/pitch diff 0.91°). **Run 2 PASS** (identity FAILED, 12.5°;
  0 heartbeats).
- **B7a PASS:** n = 66,155 poses (the +150 ms and SIGSTOP windows excluded), median 0.1 ms, p99 0.5 ms.
- **B7b PASS:** warm-up 0.93 s; 12 commands, all S1; send → MODE LAND median 0.006 s, **p99 0.042 s** (bound 0.3).
- **B8a PASS:** preconditions met (ORGN before the kill; HORIZ_POS_REL true for the 3 s before). MODE LAND reason
  EKF_FAILSAFE **+1.920 s F** after the last OF row (bound 3.0). It was the first protective action (the script's
  WatcherLost at +11.4 s and the GCS failsafe at +13.2 s came later). Max true excursion **1.218 m** (bound 2.0); no
  BREACH; no reported-position jump.
- **B9a PASS:** flow_tracker stub: withdrawal +0.959 s (bound 1.5), LAND +1.003 s W (bound 2.5); flow_bridge stub:
  +0.807 s, +0.847 s.
- **B9b PASS:** +0.856 s, +1.039 s. **B9c PASS:** tracker SIGSTOP +0.925/+0.960 s; bridge SIGSTOP +0.911/+0.955 s.
- **B9-hang (observation):** "no progress for 2.00 s" at +1.982 s; LAND +1.994 s.
- **B10a:** the four RC changes reached the FC in 0.205/0.216/0.218/0.237 s (bound 0.3), with no mode change back:
  **PASS on the mode criteria.** (Reading chosen here: "vehicle holds" read strictly, as a position hold; wbench2 passed
  the same wording on "no mode change back" alone, so this is a stricter reading, not a regression; the drift away
  from the GUIDED hold target is itself evidence the setpoints had no effect.) In ALT_HOLD with no pilot correction the vehicle drifted, and during the pilot's LAND
  it crossed x = −3.003 m: a watcher BREACH and one LAND (the FC already in LAND, so no mode change). The criterion's
  "vehicle holds" is therefore **not met as worded** (an ALT_HOLD drift, as in wbench2's B10b; not a watcher matter).
- **B10b attempt 1: NOT COMPLETED** (B3: the pilot's toggle was never made). (1) and (3) behaved as registered.
- **B10b repeat (A10, fresh boot) PASS:**
  - (1) "GCS Failsafe - Continuing Pilot Control", no mode change; the H10 guard (merged `fly_trial.fc_mode` = 2) logged
    NOT commanding LAND;
  - (2) the new watcher confirmed; ONE LAND (ACKed, S1); the pilot's switch → ALT_HOLD **+0.219 s** (bound 1.0); nothing
    re-commanded LAND until the pilot's LAND switch (+49.6 s);
  - (3) "EKF Failsafe" 1.94 s after the kill, **no mode change**.
- **B10c PASS** ("Radio Failsafe - Disarming", disarm +1.15 s W).
- **F6a PASS:** one send; LAND +0.004 s; ALT_HOLD +0.213 s after the switch; no FC mode change in 9.79 s; S1.
- **F6b PASS, valid:** COMMAND_ACK 176 stripped, no "LAND ACK", 5 heartbeats held; one send; LAND +0.003 s; ALT_HOLD
  +0.214 s; no mode change in 9.79 s; stop S3.
- **F6c PASS, valid:** exactly one dropped DO_SET_MODE(LAND); 2 sends 0.312 s apart (window 0.30–0.60); FC LAND
  −0.001 s after send 2; no third send (S1).
- **F7-0 PASS:** never confirmed, the reasons yaw only (`vel=1`); MAVLink arm refused "Arm: Watcher: never seen"; the
  script refused.
- **F7-a FAIL AS WORDED:** re-confirmed **7.59 s** after the rotate-back (bound 5.0 s).
  - The yaw agreed after 1.4 s.
  - But the `rotate_in_place` teleport (set to z 0.2 m; rest 0.195 m) gave EKF3 a vertical-velocity transient: vz
    0.314 m/s, below 0.2 m/s only ~2.3 s later. The mocap speed stayed 0.000.
  - M2 (the 3-D norm) refused on it, then held 5 s. The §1.2 prediction considered the mocap side only and missed the
    EKF vz transient. The script then armed.
- **F7-b PASS:** withdrawn +0.38 s (bound 1.0); arm refused ("GCS failsafe on", "Watcher: heartbeat 5.6s old");
  0 LAND, no BREACH, latch 0.
- **F7-c PASS:** re-confirmed +1.41 s (bound 5.0; no vz transient this time); the script armed after "GCS Failsafe
  Cleared".
- **F7-d PASS:** armed, rotated +15° (diff 18°): 0 of ~160 polls unconfirmed, 0 LAND, no BREACH, armed in GUIDED
  throughout, "INFORMATIONAL" logged. (The script's early exit and the missing re-confirmation at the end recur as in
  wbench3.)
- **X1 (no yaw/vel withdrawal while armed): FAILS AS WORDED against `op_events.csv`; holds on the watcher's own FC
  state.**
  - 26 "confirmation 0" lines with a yaw/vel reason fall inside the operator link's ARMED span.
  - 24 of them lie 0.03–0.95 s before the operator link saw the disarm: the watcher's own link saw it first.
  - The other 2 are B10b(2)'s new watcher before its first FC heartbeat (an unknown arming state counts as disarmed,
    as §1.2's B10b note registered).
  - In every session the watcher's `mocap_watch_vel.csv` and `mocap_watch_yaw.csv` have **0** samples with
    `fc_armed=True` and a failing gate. **0** watcher LANDs or BREACHes came from either check.
- **X2 PASS** (above).

### 2.2 M2-R (the M2 runaway test): NOT COMPLETED

- **First run (`…181437`): void** (B4: in attempts 1–3 the runaway window ran in flight; M1 was wrongly applied between
  attempts). The driver recorded it NOT COMPLETED.
- **Repeat (`…182305`): a runaway was produced (V1 met), but V3 FAILED.**
  - Attempt 1, natural landing: after the disarm, the operator-link |v| was 0.42 → 0.69 m/s (VN ramping on the ground,
    the truth still). It dropped below 0.2 m/s 1.9 s after the disarm.
  - **The watcher refused at once:** "vel EKF velocity |v| >= 0.2 m/s (F8)" and the ALERT (|v| 0.510) at the first
    sample over the limit; `box=0` throughout (so `watch_ok` and the flight script would refuse); 0 LAND, no BREACH. It
    re-confirmed ~5 s after |v| fell below 0.2.
  - The FC-side probe needs ≥ 3.5 s of heartbeat absence. It came at +12.4 s, when |v| was 0.02–0.06: V3 failed. The
    probe's arm was also refused for a harness reason ("Land mode not armable", B5).
  - After M1 the origin was re-verified, the watcher confirmed (|v| ≤ 0.001 over the 5 s before) and the flight script
    armed: criteria (e)–(g) were met.
- **Final repeat (`…182609`): NOT COMPLETED.**
  - 3 natural + 2 flow-kill landings. Operator-link |v| maxima 0.10, 0.30, 0.10, 0.25 and 0.29 m/s; none ≥ 0.2 for 1.0 s.
  - The watcher refused on each short excursion (ALERTs at 0.33, 0.30, 0.25, 0.25 and 0.31 m/s).
  - Per §1.3 nothing more was run. V1b (the dataflash check) was therefore not evaluated.
- **So the registered M2-R (a)–(d) were never evaluated on a valid probe.** What stands is the observational evidence
  (§2.3) and the unit/e2e tests.

### 2.3 Observations (not pass items): M2 refusing REAL ground runaways in this bench

- **After B9a (flow_bridge stub) in `hoverB_…173841`.**
  - EKF3's |v| ran from 0.93 m/s at the disarm to **42.6 m/s** over 90 s with the vehicle still (mocap speed 0.000;
    910 of 923 samples ≥ 0.2). The EKF yaw drifted to 9.6° off.
  - The watcher refused for the whole 90 s (vel AND yaw), with no LAND. This is an F8-type runaway that did NOT
    re-capture. It caused the B2 abort.
- **After B4c (the 65° tilt drop, ground session).** EKF3 diverged to **192 m/s** on the ground (vz first, then
  horizontal) with 24° of yaw error. It was refused throughout (the B1 abort).
- **Short excursions.** There were 34 M2 ALERTs across all sessions, |v| 0.21–2.56 m/s, at touchdowns and at the
  carry/rotate teleports (vz spikes from the z 0.2 m set-down). Each held the confirmation for ≥ 5 s afterwards.
- **Interpretation, stated as such.** M2 also refuses on brief, physically real vz transients after a set-down (the 3-D
  norm). On hardware a hand set-down is gentler than a SITL teleport, but this is the cost behind F7-a's fail and
  B5c's longer re-confirmation.

### 2.4 Summary

- **PASS as worded:** B0, B1a, B1b, B1c (ii), B1-native, B1c-Lua, B2a, B2b, B3a, B3b, B4a ×5, B4b side, B4b top, B4c,
  B5a, B5b, B5b-noflag, B5c, B6a, B6b ×2, B7a, B7b, B8a, B9a ×2, B9b, B9c ×2, B10b (repeat, A10), B10c, F6a, F6b, F6c,
  F7-0, F7-b, F7-c, F7-d, X2; B10a on its mode criteria.
- **Recorded as predicted (stock FC side):** B1c (i), (iii), (iv); B1c-Lua (d).
- **FAIL as worded:**
  - **F7-a** (7.59 s > 5.0 s: M2 on a teleport vz transient);
  - **B10a's "vehicle holds"** (an ALT_HOLD drift to the box face);
  - **X1** against the operator link's timing (it holds on the watcher's own FC state).
- **NOT COMPLETED:**
  - **M2-R**, the runaway test: the one valid runaway ended 1.9 s after the disarm, before the FC-side probe, and the
    final repeat produced none;
  - B10b attempt 1 (repeated, PASS).
- **Observation:** B9-hang.

## 3. Code changes

- **Watcher (under test):**
  - new `realflight/watcher/velcheck.py`;
  - `core.py`: Config `require_vel` etc.; `on_fc_lpn`; the `vel` reason only while not armed; the `vel=` flag;
  - `fc_link.py`: the `LOCAL_POSITION_NED` 10 Hz request and the `lpn` event;
  - `mocap_watch.py`: `--vel-check` (default require), `--vel-max`, `--vel-sustain-s`, `--vel-still-mps`,
    `mocap_watch_vel.csv`, summary lines.
  - The reason texts are static (the values are in the CSV and the ALERT), so the STOP_LOG does not log a line per
    sample.
  - No watcher change after the pre-registration commit.
- **Tests:**
  - `realflight/watcher/tests/test_vel.py` (12 tests);
  - `fakes.py` (FakeFC `LOCAL_POSITION_NED`);
  - `conftest.py` (`vel_check="off"` default);
  - `test_fc_link.py` (the interval set now includes id 32).
  - **`pytest realflight/` → 118 passed**, before the runs and again at the end.
- **Bench harness:**
  - `bench.py`: `--checks all`, M1 (`m1_if_needed`, plus amendment B2), the S4 fallback, the 2 s M3 disarm, the `m2`
    session, amendments B3–B5;
  - `stack.py`: the watcher defaults, `--vel-check`, the last-args restart, the operator's `LOCAL_POSITION_NED`;
  - `flight_script.py`: the H10 decision through `fly_trial.fc_mode` and `H10_PILOT_OR_LAND`;
  - `results.py`: B8a picks the BIN that holds the kill;
  - `tools/run_wbench.sh`: the usage line.
  - `fly_trial.py` was NOT modified.
- **Docs:**
  - `docs/rung1_flight_cards.md`: M1 in §1a; M2 as §1a step 7 and a §5 pre-arm line; M3 in §0, §5 step 4 and §6; M4
    stated; ABORT – LURCH; bench B10; D12.
  - `docs/real_flights_plan.md`: the §7 bullet; the §7.2 daily list; **B12**.

## 4. Open (for the user / the next stage)

1. **M2-R is not completed.** The SITL runaways here were either short (the gate re-opened 1.9 s after the disarm) or
   persistent and gross (42.6 and 192 m/s, both refused). A valid FC-side probe of a short runaway would need the
   probe inside the runaway, but the FC only refuses once FS_GCS_TIMEOUT has passed. A re-registered test is the
   user's call: for example, probe the file gate at detection and the FC at +3.5 s regardless of |v|, or use a
   persistent runaway.
2. **F7-a failed as worded on M2's vz term.** Options for a ruling:
   - keep the 3-D norm (stricter; costs ~5–8 s after a set-down);
   - a horizontal-only norm (what F8 was);
   - a separate vz limit.
   No logic was changed here.
3. **The FC-side lag (a safety statement).** The watcher's refusal reaches the FC only after `FS_GCS_TIMEOUT` (3 s)
   without its heartbeat (the Lua path is similar), i.e. ~3.3 s after the withdrawal. F8 onsets come at touchdown and
   the watcher withdraws at the disarm, so **for a runaway shorter than ~3 s that starts at the disarm, the FC never
   refuses during it**: in `…182305` the whole above-threshold span (0–1.9 s after the disarm) fell inside that hole,
   and only the file gate (the flight script) refused during the runaway. A manual non-force MAVLink re-arm inside
   that window is stopped only by M1 and the card. M2's 5 s hold does make the FC refuse from withdrawal + ~3.3 s until
   the re-confirmation. To be stated in the safety case.
4. **EKF3 runaways that never re-capture** (§2.3: 42.6 and 192 m/s on the ground) are new relative to the F8
   investigation, where every case re-captured. Not investigated; M1 is the cure on the cards.
5. B12 on hardware (props off) and the rung-1 manual M2 step are untested.
