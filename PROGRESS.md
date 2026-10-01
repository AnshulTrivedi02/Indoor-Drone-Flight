# Thesis Progress Log

Master's thesis: Indoor drone state estimation (EKF / UKF / online FGO) in
GNSS-denied environments, with emphasis on robustness under degraded sensing.

---

## Current Status — 2026-09-30 (late) — D18/D19 ruled; FGO backend built and plumbing-tested; half-speed sequence STOPPED (D20, D21)

- **D18 principle recorded:** sensor-validity rules are shared; design features are not.
- **D19 route (a) built:**
  - ArduPilot: `EKFType::FGO` 13, `AP_NavFGO` output predictor, `AP_AHRS_FGO`, 52 switch arms, its own
    `ODOMETRY` route on SERIAL3.
  - Node: state out (corridor frame → NED), heading in (same message and trust as EKF3).
  - Harness: `FGO_NODE`, `FGO=1|shadow`, loopback pinning for half speed.
  - **3 dev smoke tests:** plumbing fixed and verified (age 134/149/171 ms median/p95/max at half
    speed; no take-off backlog).
- **The half-speed `VISO_DELAY_MS` measurement stopped by rule** ((a) 20.0 against (b) 25.4 ms,
  > 5 ms): **D20.** Its first attempt was VOID (the Wi-Fi dongle fault broke gz multicast); fixed by
  loopback pinning.
- **Half-speed set (a):** EKF3 PRIMARY MISS (+242 s against +186 at full speed); the UKF passes
  (+198 against +163). A systematic RTF effect on no-heading drift: **D21.** The sequence is stopped.
- **Offline:** F1–F3 and C0 pre-registered. C0 reported (FGO lower position on 6/6 textured; UKF
  lower yaw RMS on 5/6).
- FGO gates pre-registered. FGO offline no-heading prediction: west +168…+171 s.

## Current Status — 2026-09-30 (evening) — the UKF flies: no-heading PASS, with-heading 3/3 PASS; D12 report; D18/D19 queued

- **D16 (a):** the P3 yaw miss was recorded as worded.
- **The no-heading prediction** was checked for the pre-take-off heading offset, found not to account
  for it, and was superseded before flying. It was re-derived by the set-(a)-validated open-loop
  East-error method: west wall [+146, +218] s.
- **`cl_ukf_a_tex` (the UKF flies, no heading): PRIMARY PASS**, west-wall contact at cruise +163.0 s.
- **D17 (a), heading at EKF3's 5°:** the port's ExtNav heading input was built on EKF3's path, and the
  pre-registered V1–V4 all PASS:
  - V1: Replay on set (b) logs; the input is identical to EKF3's 1:1.
  - V2: shadow with heading; live equals Replay; the predictor check passes.
  - V3: ground test, yaw error 0.05°.
  - **V4: the with-heading UKF set, 3/3 PASS** (B2 0.16–0.29 m; B3 p95 0.17–0.21°).
  - The binary had md5 `85179298…` (port `60887dea`, version string matching).
- **Gyro-bias diagnostic:** EKF3 learns gyro-z bias only while disarmed and still (STATIC yaw fusion);
  the UKF lacks that branch. **D18** is queued.
- **D12 report:** the take-off backlog is throughput (step 42–49 ms > 33.3 ms period). Route (a) is
  ~4.5–5 days. The recommendation is SITL RTF 0.5 for FGO flights. **D19** is queued.
- **Lesson** (saved to memory): waiter command lines must not contain sim process patterns; the
  watcher's leftover sweep killed one.

## Current Status — 2026-09-30 (afternoon) — D15 and D8 carried out; P2 passes; P3 misses on yaw (D16)

- **D15 (EKF3's ground-proximity flow rule), applied to the offline UKF, the FGO (replay and node) and
  the UKF port.** Defined from EKF3's source before any re-run. A full re-run (`eval/d15_pipeline.sh`,
  240 replays, all audited) followed, and `numbers.md` is restated (old values superseded).
  - The take-off yaw kick is gone on all six previously poor dsn flights (|Δ| ≤ 0.76°).
    UKF `dsn_tex` median 17.45 → 5.39 m.
  - A residual post-detection kick remains on fwdplainc r2/r3. It is UKF-only: EKF3 shows none.
  - **The confirmatory EKF3-vs-FGO test holds** (CI [−1.16, −0.21]). FGO node step 2 passes (a
    harness `.typo` bug was fixed).
- **D8 diagnostic:** re-timing flow costs EKF3 nothing measurable (16 bags; baselines reproduce to
  ≤ 1 mm).
- **Correction:** the four panicked Replays were not killed at 12:38 as recorded. They ran until 13:13
  and overlapped the old P2 (RTF 0.92 vs 0.98). That P2 is superseded.
- **P2 re-run** on the fixed binary: PASS. **Output-predictor check: PASS** (yaw max 0.22°, was 4.57°).
  The no-heading prediction is re-derived and pre-registered: U2 +100 s, U3 west wall
  [+160, +217] s.
- **P3 ground test (UKF active, `AHRS_EKF_TYPE 12`):** G1–G3 and G5 pass, and the UKF is confirmed
  as the active attitude source. **G4 yaw fails as worded** (3.09° over a 65 s hold, bound 1.0°): SITL
  gyro drift with no heading source, and EKF3 drifts 2.15° on the same hold. **UKF flights stopped;
  D16 queued.**
- Finding: the UKF's on-ground height converges slowly after initialisation (P2).
- Still owed: the D12 FGO backend effort/blocker report and the take-off backlog fix.

## Current Status — 2026-09-30 (morning) — rulings D1–D7 carried out

- **D2:** C++ heading node, `VISO_DELAY_MS 38` (original G4 rule). Ground test G1–G5 pass. **Set (b)
  re-flown with C++: 3/3 pass** (cross-track 0.23–0.34 m; yaw p95 0.28–0.31°).
  `closed_loop_run.sh` defaults to C++.
- **D5:** the UKF port has a 60 ms delayed horizon with EKF3's flow timestamp.
  - Step 3: the remaining cost is flow timing (0.41 m with flow at capture, against 5.06 m).
  - EKF3 fuses our flow 31–44 ms before capture (28 trials; D8).
  - Buffered Replay port 2.79 m.
  - Live shadow drift about 24 deg/min, which is the UKF algorithm (the offline UKF does 29.9 on the
    same flight); D9.
- **D7 (FGO node):**
  - step 2 PASS (both logs, the final core);
  - step 3: < 0.1 m against truth (n = 1);
  - real time without load: keeps up;
  - a live-shadow defect (in-callback processing lost 1.4% of IMU → false invalid) was fixed with a
    separate core process;
  - under load: no loss, valid 100%, live 4.61 against offline 4.62 m, steady lag 135 ms, but a
    **take-off backlog up to 1.9 s** (D12 precondition);
  - validity rule: flow timeout 5 s, or a post-take-off gap.
- **Established:** EKF3 < FGO on textured (confirmatory); `dsn` noise floor closed; UKF "poor in most
  textured flights".
- **Queue:** `docs/decisions_queue.md` (open D8–D14).

## Current Status — 2026-09-30 (overnight) — closed loop flown; C++ heading port; UKF port steps 2–3; confirmatory EKF3-vs-FGO test

- **Ground test (live forward-camera heading → EKF3 ExtNav yaw).**
  - Run 1 stopped at G4: the Python node's latency was about 100 ms, more than the 60 ms horizon.
  - Ruled: `VISO_DELAY_MS 60`. The fusion time is set by the horizon clamp, so the delay is nearly
    inert, and the residual timing error is < 0.2° at the conservative yaw rate.
  - Run 2 failed G5.3 on drops (11%). Run 3, at `every_n` 4 (7.5 Hz), passes everything.
- **Closed loop.**
  - Set (a), EKF3 without heading: hit the west wall at cruise +186.2 s (predicted +187 s).
  - Set (b), EKF3 with the live heading: 3/3 pass B1–B5. Cross-track 0.27–0.31 m; yaw p95
    0.28–0.36°, max ≤ 0.54°.
  - A B4 scorer bug was fixed (queued D1).
- **C++ heading port:** bit-exact numpy RNG; equivalence C1–C4 pass on 10,238 frames. 15 ms per
  frame against 55 ms in Python; SITL latency 47 ms against 141 ms. Switching is queued (D2);
  Pi times are estimates only.
- **UKF port:**
  - Shadow SITL run: healthy and valid, but about 21 deg/min yaw drift.
  - Step 2 found two porting bugs and fixed both: a float `asin` in the Euler extraction, and
    every constant float-rounded by ArduPilot's `-fsingle-precision-constant`. After the fixes it
    PASSES E1–E5 on both logs (blank E2 ratio 0.80). The live yaw drift (about 22 deg/min) persists
    after the fixes, so it comes from the input path.
  - Step 3: input-path cost 5.1 m (flow at arrival 4.8, IMU path 3.2, gyro pairing 1.5); the
    post-fix port scores about 3.4 m evo-a equivalent (D5).
- **Confirmatory `dsn_tex_r4..r10`: EKF3 lower than the FGO on the textured floor.**
  - d < 0 on 6/7; mean −0.69 m, CI [−1.20, −0.19]. r10 is unusable by the IMU-gap rule and was
    counted against.
  - Noise floor SD: EKF3 0.31, FGO 0.13 m.
  - The UKF is poor on 6 of 9 textured flights (median 17.5 m).
- **`numbers.md` restated** from the re-run; the old sections are superseded, not edited.
- **Queued decisions:** `docs/decisions_queue.md` (D1–D6).
- **Next open track:** the FGO (D7: node and validation, then covariance logging). Not started.

## Current Status — 2026-09-29 (afternoon) — queue items 1–3 done

- **Heading share restated:** 74% → 69% (`dsn_tex_r3`, pinned window); batched correction
  (iii).
- **UKF checkerboard r2:** terminal gate lockout; the onset during degraded measurements at
  y 125–140 m is not separable.
- **Consistency (5b),** 72 identity-checked replays:
  - EKF3 cross-track is consistent on textured and transition, overconfident on blank.
  - UKF and FGO baselines are overconfident everywhere. With heading they are consistent on
    textured only.
  - The FGO's wider heading acceptance comes from a ~9× larger predicted yaw σ (0.48° vs
    0.05°): conservative on textured floors, closer to consistent than the UKF on the
    checkerboard.
  - At the end wall the FGO accepted wrong headings while its estimate was already ~3° off.
  - The FGO covariance is a gate-only approximation.

## Current Status — 2026-09-29 — distance-scale check DONE: two baseline corrections queued

- **EKF3 reads +7% (textured):** `FLOW_POS_Z = 0.13` is wrong in practice. The logged HAGL
  is body-origin referenced (2.29 m, not the lidar's 2.18 m), so the flow range is 5–6% too
  long. The fix is 0.25; it needs re-flying.
- **The UKF reads −15%:** its predict step spans 15.00 ms (5 IMU samples), but it integrates
  position and gravity with a fixed 12.5 ms. Its accel z-bias of 1.97 m/s² absorbs the
  gravity mismatch. The fix is the accumulated dt; it needs re-replaying.
- **The FGO (1.01) follows the flow sensor,** which itself reads 1.009.
- **Blocked until the corrected re-run:** FGO-vs-UKF with heading, EKF3/UKF cross-estimator
  ATE claims, and the UKF's Phase 5 magnitudes.

## Current Status — 2026-09-29 (later still) — Phase 5 evaluated; scale check next

- **Prediction (a), "the heading-driven share falls": PASS** in all 12 cells. The heading
  part falls from 0.02–0.31 to ≤ 0.004 m/s.
- **Prediction (b), "the residual stays roughly unchanged": FAIL as worded** in 10 of 12
  cells.
  - Textured: the residual shrank 50–88% (tiny in absolute terms).
  - Transition and blank: it grew 16–87%. In the FGO it grew by more than the heading part
    removed.
  - The pre-registration classes this as a finding, not a failure.
- **UKF transition got worse:** in the baseline, the heading part and the residual cancelled.
- **End wall:** confident wrong headings (> 3°) were fused 0/47 and 0/59 by the UKF, and
  29/47 and 2/59 by the FGO.
- **Plain walls over the checker floor:** acceptance UKF 66–71%, FGO 77–81%. UKF r2 ends
  17° off.
- FGO-vs-UKF with heading is conditional on the scale check.

## Current Status — 2026-09-29 (later) — Phase 4 DONE (90/90), reported for Phase 5

- **Phase 4 offline forward fusion (UKF/FGO):** 90/90 replays done. The baselines are
  byte-identical to the stored runs (36/36).
- **Heading cuts yaw error** from 20–120° RMS to 0.1–0.4° (1.6–2.0° on plain walls over a
  checker floor).
- **Textured evo -a (cruise):**
  - FGO 4.7 → **0.47 m** (textured walls) and 0.54 m (plain walls);
  - UKF 14.3 → 6.6 m, with ratio 0.85, a ~15% under-travel;
  - EKF3 3.8 m, with no heading by ruling, so not like-for-like.
- **Transition:** FGO 26.0 → 20.7 m, onset 95 → 110 m.
- **Blank:** yaw fixed, position unchanged.
- **Yaw rate** adds nothing to ATE but improves gyro-bias tracking (FGO 55% → ~90%).
- **Timing is diagnostic:** UKF 1.6 ms; FGO 33 → 40 ms textured.
- **Found and fixed:** thread oversubscription in the batch (identity-checked).
- **Next:** Phase 5, the hypothesis test.

## Current Status — 2026-09-29 — SCOPE CHANGE (supervisor) + EKF3 ruling; Phase 4 starting

- **Supervisor direction, scope change** (details pending the supervisor's reply):
  - real indoor flights with motion-capture ground truth are in scope;
  - the UKF and FGO should ideally run **online, onboard ArduPilot**, as drop-in
    replacements for EKF3;
  - the forward camera goes on the real vehicle only once verified in simulation.
- **Consequences:**
  - The Python UKF and FGO are now the reference implementations.
  - Offline Phases 4 and 5 are the simulation verification.
  - Current flights fly on simulator truth, so all three estimators are offline
    observers. Closed-loop flight is planned.
  - All future flights log with `LOG_REPLAY=1` and `LOG_DISARMED=1`.
- **EKF3 ruling (option 3):**
  - EKF3 is the fixed no-yaw-source baseline; only the UKF and FGO get forward arms.
  - Live injection is rejected (separate-run confound; the `VISO_YAW_M_NSE` floor).
  - Re-recording for Replay plus `REPH` injection is deferred until after Phase 5.
  - Reason: our logs have `LOG_REPLAY=0`, so Replay is not possible on them.
- **Next:**
  - Phase 4, offline fusion in the UKF and FGO only;
  - Part C, an onboard-feasibility investigation (read-only, one day).
- **Supervisor answers (same day):**
  - One build with parameter selection is preferred.
  - **Real flights are the main result** (SITL-only only if delayed by outside
    circumstances).
  - The offline comparison is written up with less weight.
  - Target: H743 flight controller on an ArduPlane quadplane, flown in multirotor mode.
  - The UKF runs onboard as an EKF3 drop-in.
  - The FGO may run with GTSAM on a companion computer, if shown working and beating
    EKF3. If EKF3 flies, the FGO must show a clear benefit in a clear case.

## Current Status — 2026-09-24 — Phase 2 COMPLETE (one recorded miss); plain-wall dataset started

- **Ruling:** `fwd_tex_r1` is kept.
  - Its P4 FGO miss (5.158 against ≤ 5.14) stays recorded.
  - Excluding it without an input defect would be selection bias.
  - The excess error is unobservable-heading drift.
  - It is flagged for Phase 5 and reported individually.
- **Phase 2 COMPLETE:** P1 and P3 pass 9/9, P4 passes 8/9.
- **Next:** the plain-wall dataset `fwdplain_*` (featureless case; textured walls are
  the upper bound).
- **Plain-wall work:**
  - Reframing, design and pre-registration recorded.
  - Worlds built; the plain-wall Phase 1 check passes every primary criterion (3/3).
  - **The `fwdplain_*` batch is HELD.** The render check shows the forward camera sees
    a textured cloud skybox: no world has a ceiling, and the sky fills ~46% of the
    frame. So the "featureless" case has a far-field heading cue.
  - Awaiting a ruling: (a) a plain ceiling [recommended], (b) no sky, or (c) keep the
    sky and document it.

- **Ceiling ruling applied:**
  - Six ceiling worlds `*_fwdc` / `*_fwdplainc` built; the sky-visible worlds and
    `fwd_*` are superseded.
  - Six check flights: the render check passes (no sky); P1 passes everywhere.
  - **P3 FAILS on `p1c_fwdplainc_trans`** (`flow_y_raw` 73.01 against ≤ 72.86), so
    the work STOPPED per the pre-registration.
  - Also pending: `p1c_fwdc_trans` UKF/FGO. A pre-arm IMU receipt bunching (92 samples
    at one stamp, no sensor-time gap) is not covered by the gap rule.
  - The datasets are not flown; awaiting a ruling.

- **Ceiling datasets flown:** 18/18 in 140.9 min.
  - The render check passes (no sky).
  - The timing rule trimmed 3 bags; none is unusable.
  - `fwdplainc_*` passes 9/9, so under Ruling 1 the check-flight miss is run-to-run
    variability.
  - **`fwdc_*` passes 8/9. `fwdc_trans_r1` P3 `flow_y_raw` is 73.57 against ≤ 72.86:
    a primary miss, reported.** 2 of 8 ceiling-world transition flights exceed the
    band, against 0 of 8 without a ceiling. Awaiting a ruling.

- **Ruling:** `fwdc_trans_r1` is run-to-run variability.
  - Effect size: ceiling vs no-ceiling transition forward flow +0.43 px/s (+0.6%),
    p = 0.31. The textured half is unchanged; the blank half is more variable.
  - Standing rule: state this when comparing the ceiling datasets with `dsn` on the
    transition world.
- **Ceiling datasets COMPLETE:** `fwdc` 8/9 (one recorded miss), `fwdplainc` 9/9.
- **Next:** Phase 3, forward-camera measurements.

- **Phase 3 (forward-camera measurements) DONE within the time-box.**
  - **Method:** LSD + RANSAC vanishing point for heading; median LK flow near the VP
    for yaw rate. Calibrated on `p1c_*` and validated on the 18 dataset bags without
    re-tuning.
  - **Heading:** textured walls 9/9 (noise 0.1–0.2°). Plain walls pass on blank and
    transition floors but fail on the checkerboard floor, where floor aliasing
    outvotes the junctions.
  - **Yaw rate:** textured walls 9/9 (0.13–0.21 deg/s); plain walls 0/9.
  - **Static response bar: 1/6 pass; it stands as failed.** It is linear and unit-slope away from the
    end wall, but wrong near it.

### Earlier the same day — Phase 2 flown (9/9); stopped pending two rulings

- **Freeze diagnosed:** a kernel panic when the rt2800usb Wi-Fi dongle disconnected
  (xhci NULL dereference, recovered from pstore). It was not disk, memory or OOM, and
  no trial was running at the time.
- **New `run_resumable_batch.sh`:** a crash-safe runner that runs in tmux.
  - Keeps a per-trial `trials.log` and writes DONE and FAILED markers.
  - Gives any partial trial `ABORTED.txt` and resumes from it.
  - Uses no network inside the loop.
- **Phase 2 `fwd_*`:** 9/9 complete first time in 69.0 min (estimate 70).
- **Primary results:**
  - P1 and P3 pass in all nine.
  - P4 passes except:
    - **`fwd_tex_r1` FGO 5.158 > 5.14:** a primary miss; the user rules.
    - **`fwd_trans_r3` UKF/FGO:** not evaluated. The dejitter guard caught one real
      pre-arm IMU dropout; options are in METHODOLOGY.
- **Diagnostics:** P2 blank_r1 p95 is 39.4 against 38.2; the UKF on tex_r1 is 42.73.
- See METHODOLOGY "Phase 2 result — STOPPED pending ruling".
- **Update, same day.**
  - Ruling 2 was recorded as a general IMU-gap rule and applied: a pre-arm gap means
    the replay trims to after the gap; a post-arm gap makes the bag unusable for the
    UKF/FGO.
  - It caught `fwd_trans_r1` too (a 20 ms gap, missed by the guard). Its result is
    essentially unchanged.
  - `fwd_trans_r3` now passes, so 8/9 pass.
  - The Ruling 1 check on `fwd_tex_r1` localises the miss to larger UKF/FGO yaw drift.
    Drift phase and the IMU stream are identical, so nothing explains it; that is
    reported and the user rules.
  - Plain-wall (`fwdplain_*`) work waits for that ruling.

## Current Status — 2026-09-24 (night) — forward-camera Phase 1 COMPLETE under the revised criterion

**Update — OI-2 done, plus a clock finding.**
- **Clock rate.** SITL's dataflash clock runs ~0.02% slow against Gazebo sim time.
  With `TimeUS` mapped by offset and rate, the flow→EKF3 latencies are superseded:
  they are now positive and tight.
  - All three fwd worlds still pass P2, but transition and blank have thin p95
    margins (0.3–1.1 ms).
  - The forward camera adds ~5–10 ms of median EKF3 flow latency. That is real, and
    flagged for Phase 2.
- **OI-2** (IMU sensor time vs receipt time, offline on `dsn_tex_r1..r3`):
  - FGO evo -a (cruise) 4.81 → 4.52 (−6%, all three repeats), which flips the tiny
    EKF3–FGO gap;
  - UKF 17.07 → 17.73 (mixed);
  - yaw drift essentially unchanged.
- **Awaiting a ruling** on OI-2 and the go for Phase 2.

- **User ruling:** the IMU gap-share miss is benign.
- **New standing pre-registration rule:** each criterion is labelled PRIMARY or
  DIAGNOSTIC, no band uses a bare observed range, and only primary criteria can gate.
- **Revised Phase 1 criterion**, stated as revised after the failures, testing the
  confound directly:
  - input sim-time timing
  - flow → EKF3 latency (one EKF3 step, 12.5 ms)
  - downward-flow conditions
  - outcome (textured evo -a (cruise); failure metrics on the degraded worlds)
- **`p1_fwd_tex`, `p1_fwd_trans` and `p1_fwd_blank` all pass every primary check.**
  - RTF, now a diagnostic, was 0.74–0.77.
  - The transition latency median, 38.4 against ≤ 40.0, is the closest call.

**OI-2 opened:** IMU timestamp asymmetry. EKF3 integrates on sensor time, the UKF/FGO
on bridge receipt time. Offline quantification is next.

## Status — 2026-09-24 (late) — Phase 1 RTF follow-up: stopped on one sub-criterion

**RTF diagnosis** (60 s runs):
- The whole ~20% loss appears once the forward image is **bridged**: 0.957 without it,
  0.759–0.761 with it. Recording is free.
- Rendering is **hardware** (Quadro P620, EGL).
- The desktop-apps-closed run was not done; it needs the user.

**Direct test**, `p1rtf_dsn_tex` (the unchanged `dsn` world with the Gazebo RTF target
throttled to 0.762):
- Flow and lidar sim-time timing are identical to `dsn_*`.
- Flow → EKF3 latency and evo -a (cruise) pass: FGO 4.80, EKF3 3.90, UKF 7.75.
- **The IMU ">1.5× gap" share, 18.24%, fell just outside a zero-margin band
  (18.4–18.7%) on the benign side**: the IMU receipt stamps are more regular at the
  lower RTF.

`p1_fwd_tex` re-scored on the same checks passes everything (FGO 4.55). **Stopped per
the decision rule; awaiting a ruling.** See METHODOLOGY "Direct-test result".

## Status — 2026-09-24 — forward-camera Phase 1 STOPPED at confound check (a)

Before Phase 1, the cruise thresholds were justified, and a threshold-sensitivity check
(0.20 and 0.40 m/s) changed no conclusion (≤ 0.046 m). OI-1 (the FGO blank-floor
failure mode changed with the correction) was logged as an open item.

The Phase 1 build is committed at `c89d05a`:
- **Model:** `iris_fwd` adds a level forward camera: 60°, 640×480, 30 Hz, mono.
- **Worlds:** `corridor_*_fwd`, with line-textured walls in all three plus an end wall.
- **Harness:** an opt-in, name-driven path in `run_trial.sh`.
- **Pre-registration:** the acceptance criteria were committed before flying.

**Result:**
- The forward camera costs ~19% RTF: `p1_fwd_tex` ran at **0.768**, against
  **0.954** for the same-session control. That fails the pre-registered (a). Flights
  were stopped, with no tuning; `p1_fwd_blank` was aborted and `p1_fwd_trans` not flown.
- Downward-flow conditions (b) **pass**.
- The forward images are good and complete (30.30 Hz).
- The ground-truth pose rate turned out to be wall-clock-driven, so the ±2% band was
  the wrong test for it.

**Awaiting a ruling** on how to proceed. See METHODOLOGY "Phase 1 result".

## Status — 2026-09-24 — forward-camera workstream, Phase 0 COMPLETE

**Metric ruling: evo -a (cruise) is the primary cross-estimator metric.** It uses one
window defined from ground truth (speed > 0.30 m/s, 0.42 s centred boxcar, largest
contiguous run), applied to all three estimators, with the SE3 alignment fitted on
cruise only. The window is pinned in `eval/three_way_eval.py`.
- **Clock sensitivity** (±0.5 s): at most 0.015 m on textured, so the Hidden
  Configuration Audit §1 clock item is closed as *bounded, not proven*.
- **Textured, restated:** EKF3 **4.66** ≈ FGO **4.81** ≪ UKF **17.07**, with ranges
  2.29 / 0.39 / 12.42.
- **Every quoted ATE was audited.** Each historical run was re-run from its original
  commit, reproduced exactly on the full window, then restated on cruise. All
  conclusions survive.
- **Flagged:** before the `h_flow` correction, the FGO *froze* on blank (displacement
  ratio 0.04–0.18) rather than dead-reckoning. The attribution of the failure mode to
  §9.5 alone is qualified.
- **Smoke test (b) PASS** (`p0_smoke_tex`): FGO 4.81, EKF3 5.74, UKF 19.36; topic rates
  within ±2%; parameters verified.
- The METHODOLOGY, eval and CLAUDE.md corrections are cherry-picked to `master`.

**Next:** Phase 1 (forward-camera model variant and corridor worlds with textured
walls), waiting on go.

## Status — 2026-09-23 — forward-camera workstream, Phase 0 (stopped at gate a)

Branch `fwd-camera`, from `master` at `5b14ce3`. **Phase 0 (a), the reproducibility
gate, stopped with a finding.** `eval/three_way_eval.py` is the new single evaluation
entry point. It now writes EKF3's TUMs to `<trial>/ekf3/`, which were never stored
before. It shows that the published three-way table **mixes windows**:
- Every mean and every UKF/FGO per-repeat value reproduces on the **full** window.
- The EKF3 textured per-repeat values (4.6/3.5/5.8) reproduce only on **cruise**.
- The UKF r1 and r2 values are transposed in the table.

The ordering EKF3 ≈ FGO ≪ UKF holds on both windows. Full is not a common window
(EKF3 starts 2.6–4 s later). Cruise agrees across clocks to ≤ 0.34 s. See METHODOLOGY
"WINDOW PENDING RULING". **Waiting on a window ruling** before pinning it and running
the smoke test (b).

---

## Current Status — 2026-08-01

**Critical path cleared: all three estimators produce numbers on all nine `dsn_*`
bags, and the first same-metric three-way is in.** On evo `-a` (fair metric under no
compass): **textured EKF3 4.97 ≈ FGO 5.46, UKF-gated 19.96** (evo `-a`, full-window, mean of n=3;
on the now-primary **evo -a (cruise)**: EKF3 4.66 ≈ FGO 4.81, UKF 17.07 — see 2026-09-24).
*(Superseded: this block originally read FGO 4.87 / UKF 16.4, from before the corrected-`h_flow`
nine-bag re-run; the transition/blank figures it quoted are superseded too — those conditions
are failure regimes where evo `-a` is not a quality metric, see METHODOLOGY "Three-way comparison".)*

**FGO now deployable and affordable.** The iSAM2 `IncrementalFixedLagSmoother` is
UNUSABLE — GTSAM `marginalizeLeaves` cascades on the Python flow `CustomFactor` (diagnosed
4 ways; not our logic; FGO_DESIGN §6). Primary solver is `BatchFixedLagSmoother`; the cost
knob is the **window**. Sweep: ATE window-independent (5.10/5.07/4.23 at 1.0/0.5/0.25 s),
step-time 96/48/27 ms. **0.25 s is the primary config — the largest window meeting the 33 ms
deployability budget — declared as a config choice (not a default, not tuned for ATE).** The
FGO meets the budget only in this short-window config: a real "compute is FGO's weakness"
result. 9-bag run ~40 min (was 2.4 h at 1.0 s). LM capped at 2 iters, verified vs full-LM
(RMS 0.029 m, identical ATE).

**A derotation-sign investigation, and the methodological control that caught it.** State-
vs-time diagnostics (EKF3/UKF, `plots/*_diag_*`) localised the lateral drift to the lateral
optical-flow channel and a real roll-*rate* coupling in `h_flow` (slope −2.07, stable). A
sign fix was evidenced **three ways offline** and still **wrong** — the re-run degraded the
UKF (ATE 11.7→16.3), so it was reverted. **The empirical re-run gate is now a standing
control** (METHODOLOGY): gate every measurement-model change on a from-scratch estimator
re-run. No prior result retracted; the four-estimator yaw finding stands.

---

## Current Status — 2026-07-30

**All three estimators now produce numbers offline on the recorded bags.** EKF3
(from `XKF1`), the UKF (`src/estimators`, Euler 15-state, filterpy-free), and a
first FGO (`src/estimators/fgo`, GTSAM batch fixed-lag smoother in `venv-fgo`).
Shared `h_flow`/`h_range` (`measurement_models.py`) is imported by both UKF and
FGO — fairness made structural.

**Comparison dataset is nomag (`dsn_*`, 3 worlds × 3 repeats).** Flown under
`gnss_denied_nomag.parm` so EKF3 also has no yaw source; the compass-active `ds_*`
are retained as the noise floor + EKF3-with-yaw reference. Both datasets carry a
`yaw_source:` block in metadata (labelled positively). Physical yaw drift is
**+9.8 deg/min** (raw gyro-z; corrected from an earlier 8.9). Under no yaw source
EKF3 itself corrects only **14–33%** of it — both estimators struggle with
unobservable heading; that framing, not an accuracy race, is the interesting axis.

**HEADLINE FINDING — yaw leak under unobservable heading is a capping-frequency
effect, NOT a parameterisation or filter-vs-smoother effect.** Four configurations,
all drift near the physical +9.8 deg/min and **none recovers yaw from flow**:
EKF3 (quaternion filter) **8.4**, FGO (SO(3) smoother) **9.24**, UKF-Euler
unconditional-cap **9.52**, UKF-Euler gated-cap **12.7**. The spread is explained
*only* by how often each caps yaw variance (EKF3/FGO/UKF-uncond cap often → drift
near physical, stable bias; UKF-gated caps ~1% → flow corrupts gyro-z bias, overshoot
~220–450%, drifts above physical). `h_flow` verified correct (injecting true flow
removes the leak).

**Euler-vs-SO(3) negative result.** A controlled single-`flow_x`-residual test:
Euler-UKF and SO(3)-FGO partition **identically** — both **69% velocity / 31% yaw**.
So the attitude chart does not change the partition. This was run because the earlier
"Euler-vs-SO(3) formulation difference" attribution was only held at ~70–75% and
qualified; the direct test **refuted** it. See METHODOLOGY "FINDING".

**FGO first result** (`dsn_tex_r1`, n=1, batch, fair zero-innovation yaw anchor to
the IMU-predicted yaw — matches EKF3 `fuseEulerYaw(PREDICTED)`, `MagFusion.cpp:1062-1064`):
yaw drifts **−9.24 deg/min** (as predicted). **On par with EKF3, not better** — same
metric (`evo -a`): EKF3 **4.79 m** vs FGO **5.10 m**. (An earlier 0.49 m from an
over-strong *absolute* yaw anchor is VOID — labelled in METHODOLOGY.) **Metric-mismatch
near-miss:** the 5.10 m (`evo -a`) almost read as a 5× win over EKF3's 24.3 m
(apparatus/unaligned) — different metrics. **Standing rule: every ATE states its
metric wherever quoted.** Scale check (instrumented): FGO tracks flow (residual ≈ 0),
`|V(k)|`=0.517 (+4.7%) so it *does* inherit the flow scale — smaller than EKF3's
+12.6% (open n=1 question: why, on the same flow through the same `h_flow_pose`).
Timing: **batch 101 ms/step median, p99 167 ms — 3–5× over the 33 ms budget**;
incremental (iSAM2) 0.2 ms but cascades after ~590 keyframes (isolated to the solver
layer — same factors run clean under batch). §9.5 **closed**: UKF/FGO dead-reckon on
aiding loss, do NOT replicate EKF3's `const_pos` (formulation difference).

---

## Current Status — 2026-07-22 (evening)

**Machine migration COMPLETE.** The new desktop (i7-8700, 65 W, + NVIDIA
Quadro P620) is fully provisioned and has flown trials end-to-end. **RTF
improved from 0.05–0.17 to ≈0.86** — Known Issue #9 resolved.

**But the migration's headline finding is not the speedup — it is three
separate discoveries that invalidate prior results.** In priority order:

1. **`/ekf/pose` has never carried EKF3.** `AHRS_EKF_TYPE=10` routes
   `LOCAL_POSITION_NED` through `EKFType::SIM`, i.e. simulator ground
   truth. **Stage B's 6.4 mm and Stage C's 7.7/10.0 mm ATEs compared
   ground truth against ground truth** and are pipeline validation only,
   not EKF3 accuracy. The 320 s no-yaw drift result (±0.03°) is void for
   the same reason. See CLAUDE.md "Hidden Configuration Audit".
2. **Known Issue #11 was never a CPU problem.** `corridor_textured.sdf`
   contains **8 coincident infinite collision planes** (`<plane>`
   collision is an unbounded half-space; `<size>` is visual-only).
   Removing collision from 7 of 8 tiles gives a **29× speedup**
   (RTF 0.0134 → 0.3934) **with all 8 tiles still rendering**. The
   hardware upgrade could never have fixed a 30× algorithmic gap.
3. **Three config values the working setup depended on existed in no
   committed file** — they lived only in the gitignored `eeprom.bin`
   (`GPS1_TYPE`, and the still-unexplained provenance of others). A full
   1379-parameter old-vs-new audit is committed as
   `param_audit_migration_2026-07-22.txt`; the old config is fully
   enumerable and nothing is unrecoverable.

**Corridor worlds are now usable — this unblocks the dataset flight.** All
three fly end-to-end at RTF 0.919 with zero link flapping; `corridor_blank`
arms for the first time. See the 2026-07-23 session entry.

**Next**: re-measure the EKF3 dead-reckoning baseline and the no-yaw yaw
drift **on the corridor** (neither is measurable on `iris_textured.sdf`, see
Known Issue #6); build `preflight_check.sh`; then rewire `evaluate_trial.sh`
to source EKF3 from `XKF1`, which first requires proving the `TimeUS`->sim-time
alignment on an existing bag.

Old machine (ThinkPad X1 Carbon, i5-10210U) retained for now; `~/thesis_data`
(14 trials) and `~/ardupilot_gazebo` both transferred to the new machine.

### Phase 1 checklist

| Task                                         | Status        | Notes |
|----------------------------------------------|---------------|-------|
| Downward camera in Gazebo                    | Done          | Publishes `/downward_camera/image` and `/downward_camera/camera_info` |
| Basic optical flow (Shi-Tomasi + LK)         | Done          | `flow_tracker.py` — pixel flow output to terminal |
| Mean → median displacement                   | Done          | `np.median` over inlier displacements |
| RANSAC outlier rejection                     | Done          | Tested — working; blank floor gives 4–10 features (too few); textured floor gives 60+ |
| Textured Gazebo world                        | Done, too small | `iris_textured.sdf` — 20 m × 20 m; needs enlarging to ≥50 m × 50 m before nominal-condition data is trustworthy |
| Optical flow validated                       | Done          | ~145 px/s at 0.5 m/s, 2 m alt — matches theory (138 px/s) |
| Simulation launch / teardown scripts         | Done          | `start_sim.sh`/`stop_sim.sh`; now also `run_trial.sh` for fully headless, unattended trials |
| ROS2 timestamp sync                          | Done          | `/clock` bridged; `use_sim_time:=true` everywhere |
| Ground truth bridging                        | Done          | `ground_truth_pub.py` → `/ground_truth/pose`, 57–227 Hz, sim-time |
| Custom OpticalFlow message + publisher       | Done          | `flow_x_raw`/`flow_y_raw` (production), `flow_x`/`flow_y` (derotated, characterisation-only), `flow_x_rad`/`flow_y_rad` (rad/s, fed to EKF3) |
| Data collection pipeline                     | Done          | `record_trial.sh` (manual) and `run_trial.sh` (fully automated, headless) |
| Shadow rejection                             | Not started   | — |
| Attitude bridge (`/attitude/angular_rates`)  | Done          | `attitude_bridge.py`; raw gyro rates, common raw input across all estimators |
| Manual flow derotation (characterisation)    | Done, deprioritised | Characterisation tool only — see CLAUDE.md "Sensor Fusion Architecture" |
| Pixel-to-radian (rad/s) conversion           | Done          | `flow_x_rad`/`flow_y_rad`, altitude-independent (focal length only) |
| Downward LiDAR in model.sdf                  | Done          | Stage 1 (sensor + ROS bridge) and Stage 2 (`RNGFND1` MAVLink injection) both verified |
| MAVLink injection (optical flow → EKF3)      | Done          | `OPTICAL_FLOW` (message 100), **not** `OPTICAL_FLOW_RAD` — unhandled by this ArduPilot build. Fusion verified via dataflash `XKF5`/`XKF1` |
| EKF3 state estimate → ROS2 + evo evaluation  | Done          | `ekf_bridge.py` → `/ekf/pose`; `evaluate_trial.sh` wraps `evo_ape`/`evo_rpe`/`evo_traj` |
| GNSS-denied config (flow + rangefinder only) | Done          | `gnss_denied.parm` — standing baseline for EKF3/UKF/FGO comparison |
| Automated, unattended trial harness          | Done          | `fly_trial.py` + `run_trial.sh` + `run_batch_trials.sh` |
| Accelerometer bridge (`/imu/data_raw`)       | Done          | `imu_bridge.py`; specific-force confirmed empirically (+9.81 m/s² at rest), 50 Hz, sim-time aligned with the other estimator inputs |
| UKF design                                   | Confirmed, no code yet | State vector, process/measurement models, matched robustness params, Q derivation, position reference, covariance logging, validation plan all decided — see CLAUDE.md "UKF Design" |
| No-yaw / compass-denied investigation        | Done          | Found EKF3 fusing compass outside the stated sensor suite; verified fix (`gnss_denied_nomag.parm`) not yet folded into the standing baseline — see CLAUDE.md "No-Yaw / Compass-Denied Investigation" |
| Corridor worlds — actual flight-tested       | **DONE, all three verified** | All three fly full 151 m trials at **RTF 0.919** (live lockstep). Collision fix: floor tiles visual-only + one `ground_collision` per world; `spawn_margin` removed. Known Issues #11 and #12 both resolved. Degradation confirmed: `inlier_ratio` textured **0.9752** vs blank **0.3101** (target 0.28), transition switches at **y=80.01 m**. Batch of 9 trials = **58 min** (was ~66 h) |
| EKF3 accuracy vs ground truth                | **VOID — must be redone** | `/ekf/pose` is simulator truth (`AHRS_EKF_TYPE=10`), so all Stage B/C ATE/RPE figures measured truth against truth. EKF3's real solution (from `XKF1`) shows ~5% scale error over the 6 m window where flow aiding was active — honest dead reckoning, not a misconfiguration |
| `iris_textured.sdf` usability                | **Unusable beyond ~10 m** | Mat edge starves `RNGFND1` (41.0 no-return, 100% of samples), which kills flow fusion outright via HAGL loss — not merely "feature-poor segments". See Known Issue #6 |
| FGO (GTSAM) implementation                   | Not started   | Uses `gnss_denied.parm` baseline |

---

## Work Sessions

### Session — 2026-07-23 — corridor worlds fixed and verified; IMU rate raised

**All three corridor worlds now fly end-to-end.** `corridor_textured` had
never completed a reliable trial; `corridor_blank` had never armed. Both do
now, along with `corridor_transition`.

**The collision fix (Known Issue #11).** `<plane>` collision is an infinite
half-space — `<size>` bounds only the visual — so tiling `textured_ground` 8×
stacked 8 coincident infinite planes at z=0. Applied Option B across all three
worlds: floor tiles are visual-only (`textured_ground_visual`,
`blank_ground_visual`) and each world includes exactly one
`ground_collision`. Also removed `spawn_margin`, which carried its own
`<plane>` collision and existed in only two of three worlds — an asymmetry
between conditions — replaced by a full tile at y=−10 applied identically
everywhere. All three worlds now have 0 inline `<collision>` blocks, 1
`ground_collision`, and 9 tiles at identical poses, so physics below the
visual layer is bit-identical across conditions. That is stronger than the
previous design, which had 8 vs 5 vs 1 collision planes.

**The rendered-floor fix (Known Issue #12).** `corridor_blank` had a single
inline 20×164 m plane and its LiDAR read the 41.0 no-return sentinel. Replaced
with 9 `blank_ground_visual` tiles at the same poses as the checkerboard,
differing only in material. This matters scientifically: a world with nothing
rendered beneath the drone gives skybox — static features, deceptively HIGH
inlier_ratio, and zero flow — which is absence of a scene, not degradation.

**Verified, all of it:**
- **LiDAR**: 0.075 m at y = 0, 80, 150 in all three worlds (9/9 probes), never
  41.0. Exactly `base_link 0.195 − LiDAR 0.12`.
- **RTF (live lockstep)**: textured 0.917, blank 0.912, transition 0.927 —
  mean **0.919**, from 0.0134 pre-fix. Standalone figures (0.40–0.44) understate
  it because standalone has no SITL and the plugin blocks on timeouts.
- **Link health**: **0** `no link` events in all three (was 37); 0 JSON stalls.
- **Heartbeat timeout resolved with no timeout change** — MAVProxy vehicle
  detect went 71 s → **1 s**. It was never a separate bug: MAVProxy waits on a
  1 Hz *sim-time* heartbeat, which at RTF 0.0134 arrived every ~75 s wall-clock.
- **Degradation**: textured `inlier_ratio` **0.9752** (0% below 0.5, features
  52.5, flow_y 131.6 px/s) vs blank **0.3101** (85% below 0.5, features 7.9,
  flow_y −0.71 px/s) — against the `iris_runway` baseline of 0.28. Flat across
  all four 40 m bands. Correct degraded signature: LOW confidence *and* zero
  flow, not the high-confidence-zero-flow skybox failure mode.
- **Transition boundary**: 0.9611 at y 75–80 → **0.3846 at y 80–85** → 0.3147
  at y 85–100, crossing measured at sim t=190.3 s, ground-truth **y = 80.01 m**.
- **Flow validated against theory**: `flow_y_raw` 137.13 px/s vs 137.1 px/s
  predicted (`v/h·f`, v=0.4999 m/s, camera height 2.020 m, f=554) — 0.02%.
  Note `flow_x_raw` oscillates ±182 px/s with ≈zero mean: the documented
  ~0.4 rad/s roll vibration coupling into *un-derotated* flow, expected.
  Report per-axis, not `hypot`, which conflates translation with rotation.
- **Batch cost**: 386 s/trial → **58 min for 3 worlds × 3 repeats** at 320 s
  cruise. The same batch pre-fix would have taken ~66 hours.

**IMU bridge raised 50 → 333 Hz** and EKF3's prediction dt corrected to 80 Hz —
see the CLAUDE.md sections and the preceding commit.


### Session — 2026-07-22 (evening) — machine migration; three invalidating discoveries

**Migration.** New desktop provisioned from scratch: ROS2 Jazzy, Gazebo
Harmonic (Sim **8.14.0** — 8.11.0 is no longer in the OSRF repo, which
carries only the current point release), `ros_gz_bridge` 1.0.22 (same as
the old machine), ArduPilot SITL **pinned to `7bac20cbcc`** and tagged
`thesis-baseline` so the autopilot is a controlled constant rather than
silently upgraded by 1070 commits of upstream master. Both venvs rebuilt
from the committed requirements files at exact pinned versions.
**Measured RTF ≈0.86** (10.3 s sim in 12.0 s wall-clock) vs 0.05–0.17.

**Discovery 1 — `/ekf/pose` is ground truth, not EKF3.** Traced
`ekf_bridge.py` → `LOCAL_POSITION_NED` → `send_local_position()` →
`AP_AHRS::get_relative_position_NED_origin()` → `case EKFType::SIM`.
`AHRS_EKF_TYPE=10` selects the simulator's own state; the `EKFType::THREE`
branch that reads `EKF3.getPosNE()` is never taken. Measured: `/ekf/pose`
tracks ground truth to **3 mm over a 4.78 m flight**, while `XKF1` (EKF3's
own logged state) is unrelated to both. **This voids every ATE/RPE figure
in Stages B and C**, and voids the no-yaw yaw-drift result, which used the
same topic and so compared truth against truth — it would have returned
≈zero with or without a compass. It also *explains* Stage C's previously
unreconciled puzzle (stark sensor-level `inlier_ratio` collapse, only a
"modest" ATE gap): the metric never contained an estimator, so it could not
respond to sensor degradation. **Decision: keep `AHRS_EKF_TYPE=10` and
evaluate EKF3 offline from `XKF1`** — with EKF3 in the loop the estimator
under test would determine its own test trajectory, an asymmetry against
the passive UKF/FGO sitting directly on top of the degradation variable.

**Discovery 2 — Known Issue #11 is collision geometry, not CPU.**
`textured_ground` uses `<plane>` collision = an infinite half-space
(`<size>` is visual-only), and `corridor_textured.sdf` includes 8 copies.
Standalone measurements: as-is **RTF 0.0134** / 99.5% CPU; shadows disabled
0.0135 (ruled out); 1 tile + walls 0.3928; **8 tiles rendering with 1
collision plane 0.3934** / 65.5%; `iris_textured` reference 0.3965. A **29×
speedup with the full 160 m checkerboard intact** — the fix is
scientifically free. `gpu_lidar` verified to raycast the rendering scene
(0.076 m at rest in a collision-stripped world, matching the 0.195−0.12 m
mount geometry). The new machine still failed a corridor trial (37 `no
link` flapping events, one `ArduPilot controller has reset`), confirming
hardware was never going to fix a 30× algorithmic gap.

**Discovery 3 — hidden configuration.** Arming failed on the clean machine
with `Arm: GPS 1: Bad fix`. Cause: `GPS1_TYPE` (is a GPS *fitted*) is
distinct from `SIM_GPS1_ENABLE` (does the simulated sensor produce data);
`AP_Arming::gps_checks()` runs on the `ARMING_CHECK` GPS bit regardless of
the `EK3_SRC` selections. `GPS1_TYPE=0` existed only in the old machine's
gitignored `eeprom.bin`. `ARMING_CHECK` was never modified — it is absent
from `stage_c_textured`'s PARM dump entirely. Now pinned in
`gnss_denied.parm` and added to `fly_trial.py`'s self-healing
`EXPECTED_PARAMS`. A full **1379-parameter** live old-vs-new diff is
committed: 16 differences, 15 of them calibration state or counters, and
the 16th (`SIM_FLOW_ENABLE`) proven inert by source inspection.

**Also found: `iris_textured.sdf` is unusable beyond ~10 m** (Known Issue
#6, now with a much sharper mechanism) — past the mat edge the LiDAR
returns the 41.0 no-return sentinel on 100% of samples, starving `RNGFND1`,
which is the `EK3_SRC1_POSZ=2` height source, which kills flow fusion
outright. Flow *quality* is not the mechanism: `inlier_ratio` stayed
0.93–0.99 off the mat.

**EKF3's real accuracy, measured for the first time** (over the only valid
window — after the ~16 s `const_pos_mode` aiding transient, before the mat
edge): **+0.307 m over 6.085 m travelled, ≈5% scale over-estimate**, smooth,
no divergence, no axis error, 0/183 flow rejections, yaw within 0.65° of
North. Honest dead reckoning — EKF3 is **not** misconfigured.

**Not yet done**: apply the collision fix to the three corridor worlds;
re-run `corridor_textured` end-to-end; build `preflight_check.sh`; rewire
`evaluate_trial.sh` to source EKF3 from `XKF1` (requires proving
`TimeUS`→sim-time alignment on an existing bag first); re-measure no-yaw
yaw drift on the corridor.

### Session — 2026-07-22 — IMU bridge, UKF design, no-yaw investigation, corridor-world bugs, machine migration

**Accelerometer bridge (`imu_bridge.py`).** The one raw sensor no prior
bridge provided — needed because a gyro-only process model can't observe
roll/pitch at all (only integrate them, open-loop). Bridges MAVLink
`HIGHRES_IMU` (chosen over `RAW_IMU`/`SCALED_IMU` after reading
`GCS_MAVLINK::send_highres_imu` directly — float32 SI units, no lossy
milli-g int16 encoding) to `/imu/data_raw` (`sensor_msgs/Imu`), FRD→FLU,
50 Hz. Verified empirically, not just asserted: 50.0 Hz achieved (message
count ÷ span from `ros2 bag info`), specific force confirmed
(`+9.811 m/s²` at rest, matching standard gravity; `+9.670 m/s²`
mid-cruise, consistent with a small forward pitch), sim-time alignment
against the other three estimator inputs confirmed to within ~20 ms.
`angular_velocity` is deliberately re-sourced from this same message
(not `/attitude/angular_rates`) so accel and gyro share one timestamped
sample — matters for a UKF predict step and GTSAM's IMU preintegration.
2 commits.

**UKF design report — confirmed, no filter code written.** Full design
pass before any implementation, per instruction. State vector: 9-state
scaffold (position/velocity ENU, Euler FLU) → 15-state IMU-driven
deliverable (+3-axis `gyro_bias`/`accel_bias`, matching EKF3's own state
structure exactly). Measurement models mirror EKF3's own formulation
(confirmed from `AP_NavEKF3_OptFlowFusion.cpp`/`PosVelFusion.cpp`
directly, not assumed). Robustness parameters (flow/range noise, gates,
quality handling) matched to EKF3's actual live values rather than
self-derived — the point being to isolate filter formulation from tuning
in the eventual comparison. One real correction found mid-review: process
noise parameters can't be copied from EKF3 unchanged, because EKF3's own
predict step runs at 400 Hz (`SCHED_LOOP_RATE`, read from a dataflash
`PARM` dump) while the UKF's is capped at 50 Hz — derived the correct
dt-rescaling from EKF3's own confirmed formulas rather than assuming
"same parameter = same behaviour." Full detail in CLAUDE.md, "UKF Design."

**No-yaw / compass-denied investigation.** Audit of every sensor EKF3
consumes under `gnss_denied.parm` vs what the UKF/FGO receive found a real
confound: `EK3_SRC1_YAW` is untouched, so EKF3 still fuses the compass for
yaw — a sensor outside the thesis's stated IMU+flow+LiDAR suite, and the
same category of unfair advantage the accelerometer gap was. Traced
ArduPilot's arming logic to find a working fix (counter-intuitively,
`COMPASS_ENABLE` must stay `1` — a separate, unconditional Copter arming
gate requires the compass to report healthy even though `EK3_SRC1_YAW=0`
+ `COMPASS_USE*=0` keep it out of actual fusion) — first attempt failed
exactly as source analysis predicted (`"Compass 1 not healthy"`), second
attempt (with the corrected param set) armed and flew cleanly. Verified
compass genuinely not fusing via dataflash (`XKFS.MAG_FUSION=0`, frozen
mag states) — not just assumed from the config. A 320 s flight
(`iris_textured.sdf`, since corridor worlds weren't usable yet — see
below) showed essentially zero yaw drift (±0.03° over the whole flight) —
**not evidence yaw drift is a non-issue generally**: EKF3 still estimates
gyro bias even without yaw fusion, the simulated gyro is very clean, and
the flight was pure straight-line with minimal actual yaw rotation. Fix
lives only in the throwaway `gnss_denied_nomag.parm` — **not folded into
the standing `gnss_denied.parm` baseline**, pending a decision. Full
detail in CLAUDE.md, "No-Yaw / Compass-Denied Investigation."

**Corridor worlds don't actually work yet — found by trying to fly a real
trial in them, which hadn't been done before.** `corridor_textured.sdf`
and `corridor_blank.sdf` were both previously "verified" only at the
Gazebo level (spawn pose, rendering, feature counts) — a real
`run_trial.sh` flight surfaced two separate, unresolved bugs:
- A Gazebo↔SITL JSON lockstep stall (confirmed via `gdb`: SITL blocks in
  `SITL::JSON::recv_fdm()`) that can take ~90–110 s to self-heal once a
  MAVLink client attaches. Initially misdiagnosed as corridor-specific
  slow world-loading (more floor tiles) — that theory is wrong, it
  reproduces on `iris_textured.sdf` too, and all worlds load in ~5-6s
  regardless. Mitigated (not fixed) by raising `run_trial.sh`'s relevant
  timeout 60s→240s.
- `corridor_blank.sdf` fails to arm outright — the downward LiDAR never
  returns a valid reading at the spawn point (`range: 41.0`, out of
  sensor range), so `RNGFND1` never gets data. Root cause not found; this
  world cannot currently fly a trial at all.
- Separately, an intermittent loss of the `PARAM_REQUEST_READ`/
  `PARAM_VALUE` round trip in `fly_trial.py`'s param-verification step was
  found (3/3 in one session) and partially mitigated (5x retry), but the
  root cause wasn't pinned down — reproduction attempts with `strace`
  wrapping the network syscalls of every relevant process succeeded
  cleanly 2/2, so this remains a genuinely open, intermittent issue.

Given these, the planned long-duration GNSS-denied flight (Next Priorities
#2, below) still hasn't been run on an actual corridor world — the no-yaw
320 s flight above used `iris_textured.sdf` instead as a substitute.

**Machine migration.** This machine's RTF (0.05–0.17) makes iteration
slow enough that a second Ubuntu 24 PC is being set up as the new
workstation. Repo brought up to date and pushed to GitHub to support the
move — ROS2/Gazebo/ArduPilot SITL setup on the new machine is a separate,
outstanding task.

---

### Session — 2026-07-22 (cont.) — corridor-world instability root-caused to CPU saturation

Follow-up on Known Issue #11 (the `corridor_textured.sdf` Gazebo↔SITL JSON
lockstep stall), done jointly — user ran manual/GUI-mode tests side by
side with automated ones, which is what actually cracked this.

**Tried a partial fix first.** Live `strace` on `arducopter`, `mavproxy.py`,
and `fly_trial.py` during a failing run caught MAVProxy's own `param`
module auto-downloading the full ~1000+ parameter set (1229 sequential
`PARAM_REQUEST_READ`-by-index sends) at the same time `fly_trial.py` was
trying its own targeted named lookup — a real, contributing factor.
Excluding it via `mavproxy.py --default-modules` (drop `param` from the
default list) cut MAVProxy's traffic ~72% (1692 → 461 `sendto` calls) and
changed instant hard-failures into recoverable-with-retries. **Confirmed
not a full fix** — a run with it applied still stalled indefinitely at
arming, showing `"Accels inconsistent"` and MAVProxy's own link
repeatedly flapping (`"no link"` / `"link 1 down"` / `"link 1 OK"`) for
several minutes with no improvement, until manually stopped.

**The actual breakthrough: isolating headless-vs-GUI vs world-specific.**
The user's own earlier "manual testing usually works, just slow due to
gyros" experience turned out to have never actually used
`corridor_textured.sdf` — it was `iris_textured.sdf`, which has always
been reliable. Ran `corridor_textured.sdf` manually via `start_sim.sh`
(with the Gazebo GUI, unlike the automated harness's headless launch) as
a direct, apples-to-apples comparison. **Same failure signature showed up
immediately** — `"no link"` flapping, plus a new, more basic rejection
(`"AP: Arm: System not initialised"`) — ruling out headless-vs-GUI as the
explanation. It's specific to the world, not how Gazebo is launched.

**Root cause, found by checking `gz sim`'s live CPU usage during that
manual run**: the `gz sim server` process was pegged at **102% CPU** —
saturating a full core. `corridor_textured.sdf` (2 wall boxes + 8 floor
tiles, 20×160 m) is a genuinely heavier world to simulate every tick than
`iris_textured.sdf` (one small 20×20 m plane) — not just slower to load,
which had already been ruled out. On a machine already known to struggle
holding real-time factor on the *light* world, that extra steady-state
load appears to push Gazebo below the responsiveness the JSON lockstep
interface needs — explaining the SITL blocking, the ArduPilotPlugin
resets, the link flapping, the lost param round-trips, and the arm
failures as one unified mechanism rather than several unrelated bugs. The
~100% figure is on essentially one core, not spread across several — this
looks single-thread/single-core-bound, which matters for judging whether
the new machine actually fixes it (needs better per-core performance
specifically, not just more cores or a newer chip in general).

**Prediction, not yet verified**: this should improve on the new machine,
given it's the same underlying limitation the migration is already
motivated by. Re-test `corridor_textured.sdf` there directly (watch
`gz sim server`'s CPU% live, and whether an arm attempt completes without
the link flapping) as an early, concrete validation once it's set up —
don't assume it's resolved without checking.

**One loose end, flagged rather than swept under the rug**: an earlier
session's report claimed this same stall "reproduces identically on
`iris_textured.sdf`" — that was never independently re-confirmed under a
live CPU-saturation check the way the corridor-world case now has been,
and sits awkwardly next to `iris_textured.sdf`'s otherwise unbroken
reliability across dozens of trials this project. Possibly a different,
more transient phenomenon (a single early connection-reset event, seen
occasionally even in healthy runs, that normally self-heals in seconds)
got conflated with the sustained, CPU-bound flapping documented here.
Not resolved.

`corridor_blank.sdf`'s separate arming bug (downward LiDAR never returns
a valid reading at the spawn point) is untouched — a different root
cause, unrelated to CPU load.

---

### Session — 2026-07-14 — LiDAR, EKF3 flow fusion, GNSS-denied baseline, automated trial harness

This was a large session covering the rest of the sensing pipeline and closing
out Phase 1's remaining infrastructure work. Full technical detail (params,
frame transforms, verification numbers) is in `CLAUDE.md` — this is the
condensed log.

**Downward LiDAR (Stages 1 & 2).** Added a single-beam `gpu_lidar` to
`iris_with_standoffs/model.sdf` (z = −0.12 m, straight down), bridged to ROS2
as `sensor_msgs/Range` on `/downward_lidar/range`. Verified sub-mm accuracy
against ground truth during a hover. Found and root-caused two gotchas along
the way: `min_angle`/`max_angle` must both be exactly `0` for a 1-sample
sensor (Ogre2GpuRays silently ignores a small nonzero FOV), and this
machine's real-time factor (RTF ≈ 0.05–0.17, confirmed via `gz topic -e -t
/stats`) means wall-clock `ros2 topic hz` numbers are misleading — always
check sim-time header-stamp spacing instead. Stage 2 (`lidar_bridge.py`)
injects each reading into ArduPilot as `RNGFND1` via MAVLink
`DISTANCE_SENSOR`, verified against ground truth (mean error 0.17 mm,
~3% transient dropout under aggressive attitude changes — currently harmless
since `EK3_RNG_USE_HGT=-1` keeps it out of the height estimate).

**Optical flow → ArduPilot EKF3 fusion (Stage A).** Traced ArduPilot's
message dispatch directly and found `OPTICAL_FLOW_RAD` is silently dropped
by this build — no handler exists for it at all. Switched to the older
`OPTICAL_FLOW` message (100) via `flow_bridge.py`, using its MAVLink v2
`flow_rate_x`/`flow_rate_y` extension fields (required setting `MAVLINK20=1`
before importing pymavlink). Derived and empirically confirmed the
camera-optical-frame → MAVLink-body-frame sign mapping
(`flow_rate_x = -flow_x_rad`, `flow_rate_y = +flow_y_rad`). Verified fusion
is genuinely active (not just arriving) by parsing the ArduPilot dataflash
log directly: 0/251 flow innovations rejected, and the EKF's own fused
velocity state matched the commanded 0.4 m/s to within 1.3%.

Also hit the **`eeprom.bin` persistence gotcha** for the first time here:
once a param has any explicitly-stored value in ArduPilot SITL's persisted
`eeprom.bin`, `--add-param-file` silently stops overriding it. Fixed with a
live `PARAM_SET` + soft in-process reboot rather than deleting the eeprom —
this recurred in Stage C and is now handled automatically by
`fly_trial.py`'s `ensure_params()`.

**EKF3 state estimate → ROS2 + evo evaluation (Stage B).** `ekf_bridge.py`
reads ArduPilot's `LOCAL_POSITION_NED` + `ATTITUDE_QUATERNION` and republishes
as `/ekf/pose`, transformed from NED/FRD into the same ENU/FLU frame as
`/ground_truth/pose` (frame transform independently derived and verified,
not assumed — see CLAUDE.md). `evaluate_trial.sh` wraps `evo_ape`/`evo_rpe`/
`evo_traj`, reading bags directly via the `rosbags` library. Verification
trial: ATE RMSE 6.4 mm, RPE RMSE 4.6 mm — validates the pipeline end-to-end,
but GPS was still the position source at this stage, so this isn't yet a
flow-only accuracy number.

**GNSS-denied baseline (Stage C) — the config the thesis actually studies.**
`gnss_denied.parm` sets `EK3_SRC1_POSXY=0` (None — flow position isn't a
direct source, it becomes AID_RELATIVE dead-reckoning once
`readyToUseOptFlow()` is satisfied), `EK3_SRC1_POSZ=2` (RangeFinder),
`EK3_SRC1_VELZ=0`, and `SIM_GPS1_ENABLE=0`. Confirmed genuinely GPS-free by
decoding the `nav_filter_status` bitfield in the dataflash log (`using_gps`
False for 100% of samples), not just param readback. Flew this config over
both worlds:
- Textured floor: ATE RMSE 7.7 mm, `inlier_ratio` mean 0.94.
- Blank floor: ATE RMSE 10.0 mm, `inlier_ratio` mean 0.47 (62% of samples
  below 0.5, feature count dropping to zero on some frames).

**The real thesis signal here is at the sensor level, not (yet) the
position-error level** — `inlier_ratio` collapses sharply on the blank floor
exactly as expected, but the ~40 s flight is short enough that EKF3's
innovation gating and dead-reckoning haven't had time to turn that
sensor-level degradation into dramatic drift yet. Flagged as the direct
motivation for the next item.

**Automated, unattended trial harness.** Built to make longer/more varied
flights (needed to actually see drift accumulate) practical to collect
without babysitting each one:
- `fly_trial.py` — MAVLink flight controller: connect, self-heal the eeprom
  gotcha, arm, climb, cruise for a specified **sim-time** duration, stop,
  land. Every phase gates on measured vehicle state, never wall-clock sleep
  (this machine's RTF makes that unreliable — a real bug hit in Stage A's
  first draft).
- `run_trial.sh` — full headless stack launch (Gazebo, SITL, MAVProxy,
  bridges, flow node) with state-polled readiness at each step, drives
  `fly_trial.py`, records the full topic set, copies the ArduPilot log,
  writes `metadata.yaml`. Idempotent cleanup trap kills whole process
  groups, not single PIDs (`ros2 run`/`ros2 bag` fork/exec a real binary
  under a wrapper). Found and fixed two real bugs during verification: a
  missing hard-kill fallback that orphaned the recorder, and — more
  seriously — `ros2 bag record` silently *ignoring* SIGINT once detached
  from a tty (confirmed via `/proc/<pid>/status`), which meant trials were
  reporting success while producing bags with no `metadata.yaml`. Fixed by
  switching recorder shutdown to SIGTERM.
- `run_batch_trials.sh` — reads a `(world, velocity, altitude, duration)`
  list from a config file and runs them back-to-back unattended, logging and
  continuing past individual trial failures rather than aborting the batch.

All three verified end-to-end (zero orphan processes, valid bags, correct
metadata, and a deliberate-failure test proving the batch continues past a
bad row) and committed as three separate commits.

---

### Session — 2026-07-02 (cont.) — Attitude bridge, derotation, and architecture reframe

**Attitude bridge and manual derotation implemented.** `attitude_bridge.py`
(new) bridges MAVLink `ATTITUDE` body rates to `/attitude/angular_rates`
(`geometry_msgs/Vector3Stamped`, raw FRD, on a dedicated MAVLink port 14551
so it doesn't collide with `fly_forward.py`'s port 14550).
`flow_tracker.py` gained a manual derotation path (`enable_derotation`
param, default on) that maps FRD body rates into the camera optical frame
and subtracts rotational pixel flow from measured flow; `OpticalFlow.msg`
gained `flow_x_raw`/`flow_y_raw`/`derotation_enabled` fields so raw and
derotated flow are both available.

Bugs found and fixed along the way:
- Sign error on the roll term in derotation (correction was adding instead
  of subtracting) — fixed, commit `cab84c1`.
- Attitude stream rate silently decaying to ~4 Hz because MAVProxy
  periodically re-issues its own low default stream-rate request, clobbering
  our one-time `SET_MESSAGE_INTERVAL` — fixed with a periodic re-assert
  timer, commit `8baa64e`.
- `ros2 bag record` silently dropped the custom `OpticalFlow` topic when
  only `/opt/ros/jazzy/setup.bash` was sourced (not the workspace overlay).
- Stale duplicate `flow_tracker`/`attitude_bridge` processes from
  incomplete prior restarts corrupted a recorded bag with mixed
  message-definition versions — fixed by always killing stale PIDs before a
  clean run.

**Isolated pure-rotation hover validation — partial, then deprioritised.**
Only the yaw test was completed (pitch/roll not attempted — an earlier
attempt to isolate pitch via `ALT_HOLD` crashed the drone; `ALT_HOLD`
interprets RC3 as a climb-rate command, not absolute throttle). Yaw result:
flow_x median |raw| 185 px/s → |derotated| 157 px/s (15% reduction), not
the clean collapse the pass/fail criterion called for. Investigation
surfaced a persistent ~0.4 rad/s (23°/s) roll-rate oscillation present even
at idle hover with zero commanded motion — real (visible camera shake,
confirmed independently), but with ArduPilot's own `VIBRATION` and
`EKF_STATUS_REPORT` reporting healthy/low levels, consistent with fast
self-cancelling motor/frame buzz rather than a control-loop problem.

**Design decision — supervisor guidance (Mitchell), 2026-07-02.** Each
estimator should consume raw sensor data and perform its own rotation
compensation on its own terms, rather than all three being fed one
identically pre-processed input:
- **ArduPilot EKF3** is the fixed baseline — native `OPTICAL_FLOW` input
  (raw flow only; see the 2026-07-14 session above for why `OPTICAL_FLOW_RAD`
  isn't usable), derotates internally using its own AHRS gyro. No shortcuts.
- **FGO** will do rotation compensation inside its own flow factor
  (referencing IMU/attitude state from within the graph), not by consuming
  a separately pre-derotated flow topic.
- **UKF** (if implemented) follows the same principle for its own
  measurement model.
- Fairness comes from each estimator being correctly implemented on its own
  terms, not identical preprocessing.

**Practical consequence:** the manual derotation path built this session
is **not a production data path** for any estimator — `flow_x_raw`/
`flow_y_raw` (plus `/attitude/angular_rates`) are the production values.
`flow_x`/`flow_y` (derotated) and `enable_derotation` are retained as a
**characterisation tool** — useful for the methodology write-up and for
informing the FGO's flow-factor design — not deleted. Chasing the
background-vibration confound to get a clean collapse-to-zero is
**deprioritised/deferred indefinitely**; it was only relevant to validating
a production path that no longer exists. `analyse_derotation.py` and the
sign-fix work remain valid characterisation tooling. See CLAUDE.md,
"Sensor Fusion Architecture", for the full write-up.

**Velocity-dependent flow error reframed as an experimental axis, not a
bug.** `analyse_flow_sweep.py` (new this session) measured optical flow
error growing from roughly +7.8% at 0.25 m/s to +12.5% at 1.0 m/s.
Supervisor guidance: "filters will start to break down at higher speeds,
that's kinda expected and okay — can be a test case for you." Commanded
velocity is now a planned second experimental axis alongside sensing
degradation (see CLAUDE.md, "Experimental Design Notes") — not an open
defect to fix.

**Still open / deferred (not blocking):**
- Pitch-only and roll-only isolated hover tests — not attempted; low
  priority now that manual derotation is characterisation-only.
- Background sim vibration source — deferred indefinitely, no longer
  blocking anything.

---

### Session — 2026-07-02

**Data collection pipeline built and verified (Sessions 1 & 2).**

One command now records a self-contained trial:
```bash
./record_trial.sh <name> --world <w> --velocity <v> --altitude <a> --notes "<n>"
```
Produces `~/thesis_data/trials/<name>/` containing `bag/` (ROS2 bag),
`metadata.yaml` (ISO timestamp, world, velocity, altitude, git hash, hostname,
notes), and `ardupilot.bin` (dataflash log copied from
`~/ardupilot/ArduCopter/logs/`).

**Ground truth pose bridging.** Gazebo drone pose →
`/ground_truth/pose` (`geometry_msgs/PoseStamped`) via `ground_truth_pub.py`.
Verified: sim-time timestamps, 57–227 Hz, stable tracking of `iris_with_ardupilot`.

**Custom optical flow message.** New `optical_flow_interfaces` package
(ament_cmake) defines `OpticalFlow.msg` (`flow_x`, `flow_y`, `feature_count`,
`inlier_ratio`, `valid`, `flow_x_rad`, `flow_y_rad`). `flow_tracker.py` now
publishes on `/optical_flow/measurement` in addition to terminal logging.
Angular flow fields (`_rad`) reserved but not yet populated (zero).

**Lightweight recording.** Raw camera images dropped from trials by default.
A 35 s trial is now ~2.7 MiB vs ~2.4 GiB with images (~900× reduction).
Images available via `--with-images` for dedicated flow-development runs.

**Trial metadata** includes git commit hash for reproducibility, plus
ArduPilot dataflash log retrieval (newest `.BIN` by mtime from
`~/ardupilot/ArduCopter/logs/`).

**Bugs found and fixed during verification (lessons):**

- `gz.msgs.Pose_V → tf2_msgs/TFMessage` bridge in ros_gz_bridge 1.0.22 strips
  all frame names and timestamps (all `child_frame_id` empty, all stamps zero).
  Switched to `Pose_V → geometry_msgs/PoseArray`, selecting `poses[0]` (the
  top-level model, always `iris_with_ardupilot`). **Do not use TFMessage for
  ground truth.**
- Raw image recording made trials multi-gigabyte and contributed to sim
  instability on the laptop. Estimators consume flow measurements, not pixels,
  so images are excluded from evaluation trials by default.

**Flagged for later (not yet actioned):**

- The 20 m × 20 m textured checkerboard is too small — the drone flies off it
  during normal forward flight, contaminating "nominal" trials with off-mat
  (feature-poor) segments. Need a larger textured plane (e.g. 50 m × 50 m) or
  flight paths constrained to stay within the mat before collecting real
  nominal-condition data. **Still not actioned as of 2026-07-14.**
- Feature count is a deceptive quality metric: the camera reported ~100
  "features" even on featureless off-mat texture. Use `inlier_ratio` (RANSAC
  survivors) as the real flow-quality signal, not raw feature count.
- `flow_x` gyro coupling still present (unchanged Phase 1 task): rigid camera
  mount means drone attitude oscillation swamps translational flow; needs gyro
  decoupling before `flow_x_rad` can be populated.

---

### Session — 2026-06-28

- **Tested RANSAC** in simulation on blank floor (`iris_runway.sdf`). Confirmed
  working but blank floor yields only 4–10 features — insufficient for reliable
  RANSAC. Flow values ±300–900 px/s while hovering: pure noise.
- **Created textured Gazebo world** (`iris_textured.sdf`) with a custom
  `textured_ground` model: 20 m × 20 m plane, 64×64 checkerboard PNG texture
  (~0.31 m per square). Camera FOV 60°, altitude 2 m → ~7.5 squares visible
  across frame.
- **Validated optical flow** on textured floor at 0.5 m/s forward:
  - 60–66 features tracked per frame (vs 4–10 on blank floor)
  - flow_y ≈ +145 px/s — consistent signal, matches kinematic prediction
    (v/h × f = 0.5/2 × 554 = 138 px/s)
  - flow_x oscillates ±250 px/s around zero — gyro coupling from drone
    attitude oscillation, not a flow algorithm bug
- **Fixed `stop_sim.sh`**: removed `pkill gnome-terminal` (was killing Claude
  terminal). Now uses sentinel file `/tmp/thesis_sim_stop` — tabs poll for the
  file and exit naturally when it appears, closing gnome-terminal tabs cleanly.
- **Updated `start_sim.sh`**: accepts optional world argument
  (`./start_sim.sh iris_textured.sdf`); defaults to `iris_runway.sdf`.
- **Added `fly_forward.py`**: pymavlink script that sends continuous velocity
  commands every 100 ms — works around ArduPilot GUIDED mode timeout.
  Usage: `python3 ~/thesis_ws/fly_forward.py [vx] [vy] [vz]`

### Session — ~2026-06-18 (lost, reconstructed from code)

- Added **RANSAC outlier rejection** to `flow_tracker.py` using
  `cv2.estimateAffinePartial2D`. Inlier mask applied before median computation.
- Added **simulation launch script** (`start_sim.sh`): 5 gnome-terminal tabs
  with staggered sleep delays.
- Added **simulation teardown script** (`stop_sim.sh`).
- Last colcon build: 2026-06-18.

---

## Key Files

| File | Purpose |
|------|---------|
| `src/optical_flow_node/optical_flow_node/flow_tracker.py` | Main optical flow node — publishes `/optical_flow/measurement` (`flow_x_raw`/`flow_y_raw` are production; `flow_x_rad`/`flow_y_rad` fed to EKF3; `flow_x`/`flow_y` derotated, characterisation-only) |
| `src/optical_flow_interfaces/msg/OpticalFlow.msg` | Custom flow message definition |
| `ground_truth_pub.py` | Republishes Gazebo drone pose as `/ground_truth/pose` |
| `attitude_bridge.py` | Republishes MAVLink `ATTITUDE` body rates as `/attitude/angular_rates` — common raw input across all estimators |
| `lidar_bridge.py` | Injects `/downward_lidar/range` into ArduPilot as `RNGFND1` via MAVLink `DISTANCE_SENSOR` |
| `flow_bridge.py` | Injects `/optical_flow/measurement` into ArduPilot EKF3 as MAVLink `OPTICAL_FLOW` |
| `ekf_bridge.py` | Republishes ArduPilot EKF3's state estimate as `/ekf/pose`, transformed NED/FRD → ENU/FLU |
| `imu_bridge.py` | Republishes MAVLink `HIGHRES_IMU` accel + a co-sampled gyro copy as `/imu/data_raw` — the UKF/FGO process model's accelerometer input |
| `evaluate_trial.sh` | Wraps `evo_ape`/`evo_rpe`/`evo_traj` to score a trial's `/ekf/pose` against `/ground_truth/pose` |
| `fly_trial.py` | State-gated flight controller (arm/climb/cruise/land) for the automated harness |
| `run_trial.sh` | One-command, headless, unattended single-trial harness (launch → fly → record → teardown) |
| `run_batch_trials.sh` | Runs a config-file list of trials back-to-back, continuing past individual failures |
| `analyse_derotation.py` | Characterisation tool — quantifies rotational coupling in raw flow (not a production pipeline component) |
| `analyse_flow_sweep.py` | Velocity-sweep flow validation — feeds the velocity experimental axis |
| `dump_flow.py` | Ad-hoc debug script — dumps raw `flow_y` + feature/inlier stats from a bag (untracked scratch tool) |
| `record_trial.sh` | Manual/interactive trial recording (bag + metadata + ArduPilot log); superseded for unattended use by `run_trial.sh` |
| `gnss_denied.parm` | GNSS-denied EK3 source config — the standing baseline for EKF3/UKF/FGO comparison |
| `gnss_denied_nomag.parm` | Throwaway — verified fix for EKF3 fusing the compass for yaw outside the stated sensor suite; not yet folded into `gnss_denied.parm` |
| `flow_ekf.parm` | `FLOW_TYPE`/EK3 params enabling optical-flow velocity fusion |
| `lidar_rangefinder.parm` | `RNGFND1` params for the MAVLink-injected downward LiDAR |
| `start_sim.sh` | Manual/interactive launch of the full simulation stack — `./start_sim.sh [world.sdf]` |
| `stop_sim.sh` | Tear down stack and close terminal tabs |
| `fly_forward.py` | Continuous MAVLink velocity commands for manual/ad-hoc testing |
| `~/ardupilot_gazebo/worlds/iris_runway.sdf` | Blank floor — **degraded baseline** |
| `~/ardupilot_gazebo/worlds/iris_textured.sdf` | Checkerboard floor — **nominal baseline**, still too small (20×20 m) |
| `~/ardupilot_gazebo/worlds/corridor_textured.sdf` / `corridor_blank.sdf` / `corridor_transition.sdf` | 20×160 m long-duration worlds — built and Gazebo-level verified, but **not yet flown end-to-end successfully** via `run_trial.sh`, see Known Issues |
| `~/ardupilot_gazebo/models/textured_ground/` | Checkerboard ground plane model |
| `~/ardupilot_gazebo/models/iris_with_standoffs/model.sdf` | Drone model (downward camera + LiDAR defined here) |

---

## Next Priorities (Phase 1 remainder → Phase 2)

> **SUPERSEDED (stale), 2026-09-29.** This block is kept as the historical log. It still lists the corridor worlds as unflyable (#11), low RTF, and the Stage C ATE gap. All of these are resolved or VOID (CLAUDE.md Known Issues; METHODOLOGY). The current status and priorities are in "Current Status" at the top of this file.


0. **Set up ROS2/Gazebo/ArduPilot SITL on the new Ubuntu 24 machine** —
   migration motivated by this machine's low RTF (0.05–0.17); this
   machine remains primary until the new one is ready.
1. **Fix the two corridor-world bugs** before relying on them for real
   trials — the JSON lockstep stall (mitigated with a longer timeout, not
   fixed) and `corridor_blank.sdf`'s LiDAR-no-surface arming failure
   (unresolved). See Known Issues.
2. **Decide on the no-yaw compass fix** (`gnss_denied_nomag.parm`) — fold
   into the standing `gnss_denied.parm` baseline, or keep EKF3's compass
   active as a deliberate, documented asymmetry? Affects every future
   trial and the fairness of the eventual EKF3/UKF/FGO comparison.
3. **Enlarge textured world** — current 20 m × 20 m mat is still too small
   for forward-flight trials; need ≥50 m × 50 m before nominal-condition
   data collection is fully trustworthy. Not yet actioned. (Corridor
   worlds address the length problem for GNSS-denied trials specifically,
   but not this one for nominal-condition data.)
4. **Shadow rejection** — detect and mask the drone's shadow in the downward
   camera frame before feature detection.
5. **Longer / more aggressive GNSS-denied flights on an actual corridor
   world** — Stage C's ~40 s flights showed a sharp sensor-level
   texture-quality gap (`inlier_ratio` 0.94 vs 0.47) but only a modest ATE
   gap (7.7 mm vs 10.0 mm); the working hypothesis is that drift
   accumulates more starkly over longer flights. A 320 s no-yaw flight was
   run on `iris_textured.sdf` as a substitute (yaw drift ~0°, see the
   2026-07-22 session) but the actual textured-vs-blank corridor
   comparison is still blocked on priority #1 above.
6. **UKF implementation** — design confirmed (see CLAUDE.md "UKF Design"),
   no code written yet. Build the constant-velocity scaffold first
   (plumbing only, not a thesis result), then the IMU-driven deliverable.
7. **FGO (GTSAM) implementation** — flow-factor rotation compensation done
   inside the graph itself, not via pre-derotated flow. Same baseline config.

---

## Architecture (current)

```
Gazebo (iris_textured.sdf — checkerboard floor, nominal)
  OR   (iris_runway.sdf   — blank floor, degraded baseline)
  └─ iris_with_ardupilot → iris_with_standoffs → downward camera + downward LiDAR
       │  gz transport
       ▼
  ros_gz_bridge
       ├─ /downward_camera/image + /downward_camera/camera_info
       ├─ /downward_lidar/range   (sensor_msgs/Range)
       ├─ /clock  (sim time)
       └─ /world/<world>/dynamic_pose/info  (PoseArray — NOT TFMessage)
                │
         ground_truth_pub.py  [poses[0] = iris_with_ardupilot]
                │
         /ground_truth/pose  (PoseStamped, sim-time stamps)
       │
       ├─ flow_tracker.py
       │    ├─ Shi-Tomasi + Lucas-Kanade + RANSAC
       │    └─ /optical_flow/measurement  (flow_x_raw/rad, sim-time stamps)
       ├─ attitude_bridge.py  →  /attitude/angular_rates  (raw gyro, MAVLink)
       │
       ▼ (flow_bridge.py, lidar_bridge.py inject into ArduPilot via MAVLink)
  ArduPilot SITL — EKF3 (gnss_denied.parm: no GPS, flow VELXY, RangeFinder POSZ)
       │
       ▼ (ekf_bridge.py, MAVLink → ROS2, NED/FRD → ENU/FLU)
  /ekf/pose  (PoseStamped, sim-time stamps)
       │
       ▼
  run_trial.sh  (headless, unattended: launch stack → fly_trial.py → record → teardown)
       └─ ~/thesis_data/trials/<name>/
               ├─ bag/           (ROS2 bag: clock, ground_truth, ekf pose,
               │                  lidar, attitude, flow)
               ├─ metadata.yaml
               ├─ ardupilot.bin  (dataflash log)
               └─ logs/          (per-process stdout/stderr)
                        │
                 evaluate_trial.sh  (evo ATE/RPE/traj vs ground truth)
```

---

## Known Issues (open)

> **SUPERSEDED (stale), 2026-09-29.** This block is kept as the historical log. It still lists the corridor worlds as unflyable (#11), low RTF, and the Stage C ATE gap. All of these are resolved or VOID (CLAUDE.md Known Issues; METHODOLOGY). The current status and priorities are in "Current Status" at the top of this file.


1. **Manual derotation partial collapse (deprioritised, not blocking)** — isolated
   pure-rotation hover testing found only a 5–15% reduction in flow_x/flow_y
   magnitude, not a clean collapse, confounded by a persistent ~0.4 rad/s
   background sim vibration present even at idle hover. Deferred indefinitely
   — manual derotation is a characterisation tool only, not a production
   input for any estimator (see CLAUDE.md, "Sensor Fusion Architecture").
2. **Drone shadow** contaminates downward flow (not yet characterised on textured floor).
3. **Textured world too small** — 20 m × 20 m mat; drone exits mat during
   forward-flight trials, producing feature-poor segments inside nominally
   "textured" recordings.
4. **Feature count is a deceptive quality metric** — camera reports ~100
   "features" even on featureless off-mat texture; use `inlier_ratio` (RANSAC
   survivors) as the real flow-quality indicator.
5. **TFMessage bridge broken for ground truth** — `gz.msgs.Pose_V →
   tf2_msgs/TFMessage` in ros_gz_bridge 1.0.22 zeros all stamps and clears all
   frame names; use `PoseArray` instead (see `ground_truth_pub.py`).
6. **Real-time factor is low on this machine** — RTF ≈ 0.05–0.17, even
   headless. Every sim-time-dependent wait (sensor rates, flight phases) must
   be gated on measured state, never wall-clock sleep — see `fly_trial.py`
   and CLAUDE.md's Known Issues #9 for the full reasoning.
7. **SITL's `eeprom.bin` can silently defeat `--add-param-file`** — once a
   param has any explicitly-stored value in the persisted eeprom, new
   `--defaults`/`--add-param-file` values are ignored for it. Self-healed
   automatically in `fly_trial.py` (`ensure_params()`) via a live `PARAM_SET`
   + soft reboot; watch for this if any future param addition seems to not
   take effect.
8. **Downward LiDAR RNGFND1 dropouts under aggressive attitude changes** —
   ~3% of readings during a dynamic climb briefly read near-zero. Currently
   harmless (`EK3_RNG_USE_HGT=-1` keeps RNGFND1 out of the height estimate);
   revisit before ever enabling range-based height switching.
9. **GNSS-denied ATE gap is currently modest, not yet conclusive** — Stage C's
   short (~40 s) flights show a sharp sensor-level `inlier_ratio` gap between
   textured/blank floors but only a modest ATE gap; whether that gap widens
   over longer/more aggressive flights is untested — see Next Priorities #5.
10. **`gnss_denied.parm` lets EKF3 fuse the compass for yaw** — outside the
    thesis's stated IMU+flow+LiDAR sensor suite, a confound vs UKF/FGO's
    no-yaw setup. Verified fix exists (`gnss_denied_nomag.parm`) but not
    applied to the standing baseline — see CLAUDE.md "No-Yaw /
    Compass-Denied Investigation" and Next Priorities #2.
11. **Corridor worlds can't currently fly a real trial** — `corridor_textured.sdf`
    needs a 240 s (not 60 s) timeout to ride out a Gazebo↔SITL JSON
    lockstep stall (self-heals, not fixed); `corridor_blank.sdf` fails to
    arm outright (downward LiDAR never returns a valid reading at the
    spawn point — root cause not found). See CLAUDE.md Known Issues #11/#12.
12. **Intermittent loss of the `PARAM_REQUEST_READ`/`PARAM_VALUE` round trip**
    in `fly_trial.py`'s param-verification step — reproduced 3/3 in one
    session, 0/2 in strace-instrumented follow-up reproduction attempts.
    Genuinely racy, root cause not found; MAVProxy's own forwarding logic
    ruled out via source (`mavfwd` defaults `True`, `no_fwd_types` only
    excludes `BAD_DATA`). 5x retry added as a mitigation, not a fix. Watch
    for this on the new machine too.

## Camera Parameters (confirmed)

| Parameter        | Value                        |
|------------------|------------------------------|
| Resolution       | 640 × 480 px                 |
| Horizontal FOV   | 60° (1.047 rad)              |
| Focal length     | ~554 px                      |
| Mount            | Rigid downward, no gimbal    |

## 2026-10-01 (afternoon)
- Supervisor figures: `plots/supervisor_2026-10-01/figures.pdf` (8 PNGs, INDEX.md), `0ab58eb`.
- D24: `fly_trial.py`'s clock falls back to SYSTEM_TIME (nominal values identical on the recorded tlog); land/disarm on
  failure after arming. Re-run `fgo_groundtest_half_b`: G1–G4 pass, arm–hold–disarm completes; G5 fails as worded
  on pre-arm "FGO invalid or stale" (node start-up clock map future-stamps states) -> **D25 open, blocks FGO
  shadow (b) and flights**.
- LiDAR short returns: ArduPilot does not reject them (EKF3 median passes 2–3, SH <= 0.68; UKF port 0 rejected).
  Nothing changed; known artefact for all three. Closed-loop overshoot ≈ the flying estimator's dip.
- FGO predictions written: no-heading west [+145, +196] s (caveat: the method missed EKF3 by +55 s at half speed);
  climb-top overshoot >= +0.75 m.
- F3c: (a) false, (b) true as worded; both remove 10/30° at the first heading, so no speed difference at resolution.
- Rulings recorded: F3b representation limit, pattern, D22 validity note.

## 2026-10-01 (late afternoon)
- D25 ruled and done: node clock map settles 10 s and rejects outliers. Mechanism confirmed in `fgo_shadow_half_a2`
  (40 stale-clock time_ref samples at -126 ms, rejected). a2 itself was a launch error (EKF3 flew). `fgo_shadow_half_a3`:
  C1-C3 pass; FG1/FG2/FG3b pass; FG3 climb-top only.
- Edit guard narrowed to the job runners and their descendants.
- Shadow (b), with heading: all gates except the FG3 climb-top pass. FGO open-loop cross-track 0.075 m.
- **FGO no-heading flight `cl_fgo_a_tex_half`: PRIMARY PASS** (west +165.8 s in [+145, +196]; climb top +0.94 m).
- **FGO with-heading set: 2/3.** r3 fails B5 (pitch 0.023) at the end-wall heading degradation. Stopped; **D26 open**.
- Next: D26 ruling; then the plan to the 16 Oct simulation freeze.

## 2026-10-01 (evening)
- D26 ruled: the FGO with-heading set is recorded failed as worded (2/3).
- D26 (b), exploratory diagnosis:
  - degraded-but-valid end-wall headings (up to 11.6°) are accepted by all three estimators;
  - the FGO weights each heading ~5.5× more (gate σ 2.17° against the UKF's 0.86°);
  - its fast jitter (~5× theirs, intrinsic) couples into vehicle yaw motion in closed loop (corr +0.68 … +0.74).
- Recorded: climb-top miss (0/1/3 short returns), B3 max, heading timing closed as negligible.
- Three-way closed-loop summary table in METHODOLOGY.
- No open decisions. Next: plan to the 16 Oct simulation freeze.

## 2026-10-01 night / 2026-10-02 early
- D27 done: the offline UKF noise is aligned. All post-29-Sep offline-UKF results are re-run; no verdict changes;
  plain-wall per-bag flips are flagged; EKF3/FGO byte-identical.
- Plan step 2(a), 12 fresh flights (2 unusable, counted against): P1 FAILS (9/12), S1 passes (5/6), S2 fails (6/12).
  Robust weighting cuts wrongly accepted headings 3–6×; it does not reliably lower the yaw maximum.
- Plan step 2(b): node parameter (regression byte-identical); robust shadow gates pass (FG3 climb-top only); robust
  closed-loop set 2/3 as scored.
- **B5 checker bug:** a landing vy spike extended the window into the stop. Both FGO r3 B5 failures reverse
  (both sets 3/3 corrected). **D28 open.** D26's B5 attribution needs correcting.
- Robust against hard-gated FGO (descriptive): lower end-wall swings (2/3), cruise yaw/roll gyro activity ~25% lower;
  jitter and coupling unchanged.

## 2026-10-02 (morning)
- D28 ruled and done: the B5 window is fixed in the scorer; 21 with-heading flights rescored (only the two FGO r3
  change); both FGO with-heading sets restated 3/3; D26 corrected; both scores kept.
- Cruise-window audit: 174 trials, 0 windows changed (the largest-contiguous-run definition is immune).
- 2(a)/2(b) recorded as ruled. Step 3 ON HOLD (no new simulation without a ruling).
- Consolidated restating: numbers.md §15 (closed loop after D28) and §15.1 (robust weighting). Supervisor figures
  regenerated, with fig9 (closed-loop summary) and fig10 (half-speed paths, all three estimators).
