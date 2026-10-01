# Decisions queue

Updated 2026-09-30. Only OPEN items are at the top. Ruled items are kept below as history.
Details for every item are in METHODOLOGY.

## OPEN

### D25. FGO ground test re-run: G5 fails as worded on PRE-ARM "FGO invalid or stale" text (node start-up clock map stamps states ~4 ms in the future; the backend's uint32 age wraps -> invalid). Arm-hold-disarm itself passes (BLOCKS shadow (b) and the FGO flights)
- G1-G4 pass; disarmed at 116.26 s; OV = 1 for 100% of arming -> disarm in all three FGO runs. The future
  stamps occur in all three runs, only during start-up (to 9.2 / 10.3 / 20.8 s). In this run they overlapped
  the arming attempts, so pre-arm refused 14 times until 20.8 s; arming succeeded at 23.81 s.
- Risk: a late low outlier in the node's 10 s lower-envelope window could repeat it mid-flight (not observed).
- Options:
  - **(a)** record G5 as failed as worded, but judge the arm-hold-disarm as shown; fly as is. The pre-arm check is
    the backend working as designed, and no in-flight occurrence has been seen in 3 runs;
  - (b) node fix: a settled, outlier-robust clock map. Send no state until the window holds 10 s of samples,
    and take a low percentile (e.g. the 1st) of header - time_ref instead of the minimum, since a single
    too-low offset is what stamps states in the future. This is a node change, so a new shadow (a) is needed
    for FG1-FG3;
  - (c) backend fix: treat a small negative age (state up to e.g. 20 ms ahead) as age 0, not as wrapped. This is
    a binary change, so a new shadow plus ground test is needed.
- **Recommendation: (b).** It removes the cause on the node side, which is where the clock map is wrong, leaves
  the backend's strict check intact, and costs one shadow run (~12 min).

### D24. FGO ground test: G5 fails as worded (no disarm), from the harness's sim clock, not the backend — RULED 2026-10-01
- **Ruling:** G5 failed as worded (harness hang after the deliberate node stop, not an FGO fault); the 130 ms
  node-stop result stands. `fly_trial.py`'s clock now falls back to `SYSTEM_TIME` (estimator-independent;
  nominal values identical, `eval/d24_clock_equiv.py`), and failure paths after arming land/disarm. Re-run
  `fgo_groundtest_half_b` without the node stop (METHODOLOGY "D24 RULED").
- G1–G4 and the FG2 node-stop pass: output invalid 130 ms after the last state; the FGO's ground yaw
  equals the integrated raw gyro to 0.0003°.
- After the deliberate mid-hold node stop, `LOCAL_POSITION_NED` stopped (correct: no valid position).
  `fly_trial.py` uses it as its sim clock, failed, and never sent the disarm. There were no failsafe
  messages before the stop.
- Options:
  - **(a)** re-run the ground test (~6 min) **without** the node stop, so G5 (arm-hold-disarm) is
    tested; then the node-stop separately after disarm, or accept the 130 ms result already measured;
  - (b) accept as is: the disarm path is the same AP_AHRS code as the UKF's, which passed.
- **Recommendation: (a).** It is cheap, and it closes G5 cleanly before the FGO flies.
- **D23 diagnosis, done:** the climb-top transient is a burst of short LiDAR returns (~0.13 m at 2.2 m)
  at the climb-to-cruise pitch-forward, fused by the FGO's un-gated range factor. The 3.8 m/s spike was
  the checker's proxy (true output velocity error max 0.66 m/s). The same short returns occur in every
  flight (6–11 at 29–30 s), and EKF3/UKF closed-loop flights already show a +0.2…+0.5 m climb-top
  overshoot.


### D23. FGO shadow (a): FG3 fails as worded at the climb top (position max 0.51 m, velocity max 3.8 m/s); FG1 (after a checker fix), FG2 and FG3b pass (BLOCKS the FGO ground test and flights)
- The FG3 failures are all at t ≈ 30.0–30.2 s: the FGO's own state revises height ~0.1 m per keyframe
  at the top of the climb (its known smoother transient), which the ~130 ms output predictor cannot
  anticipate. **Elsewhere the predictor is exact** (position p95 0.003 m; max 0.048 m excluding
  28.5–33 s).
- The FG1 first-version fail was a checker bug (count alignment against a node that outlives the log).
  Corrected: PASS (evo +0.003 m; yaw p95 0.08°). Both scores are reported.
- Options:
  - **(a)** record FG3 as failed as worded, with the diagnosis, and proceed: the ground test, the
    written predictions, then the flights. The climb-top revision is the FGO's own behaviour and is
    what the controller will see, stated with every FGO closed-loop result.
  - (b) investigate the FGO's climb-top height transient before flying (bounded, e.g. 2 h: which
    input, flow or range, drives it).
  - (c) both: proceed per (a), with (b) offline in parallel.
- **Recommendation: (c).** The 9 Oct target allows it.


### D22. Half-speed UKF with-heading r3 FAILS B4 (0.296 m/s > 0.25) at cruise +0.5 s; EKF3 half set 3/3 PASS, UKF 2/3 (BLOCKS the FGO gates and flights)
- **It is a cruise-start transient:** GT East +0.27 → +0.49 m in ~1 s at the hover-to-cruise
  transition, then settled. Yaw error 0.08°, all headings accepted. **Not a runaway.**
- **The same class, under the band:** EKF3 r1 at cruise +0.5 s, 0.140 m/s (full speed) and 0.181 m/s
  (half speed). Every other flight's peak is ≤ 0.044 m/s, later in cruise.
- Options:
  - **(a)** record the half-speed UKF set as FAILED (2/3) as worded, with this diagnosis, and continue
    with the FGO gates. The FGO set is scored the same way, so it can fail the same way.
  - (b) (a), plus a DIAGNOSTIC re-score of every closed-loop flight with B4 excluding the first 2 s of
    cruise, reported alongside and never replacing the result.
  - (c) re-fly UKF r3 once. Not recommended: a repeat must not replace a result.
- **Recommendation: (a) + (b).**
- **The cruise-start transient is a property of the mission profile** (the step from hover to a
  0.5 m/s velocity command). It is worth stating in the thesis, since B4 at cruise start measures that
  as much as the estimator.


### D21. Half-speed EKF3 set (a) PRIMARY MISS: contact +242.1 s (full speed +186.2; window [+155, +215]). The UKF passed (+198.0 against +163.0)
- **A systematic RTF effect:** both estimators' no-heading yaw drift is slower at half speed (EKF3 +2.1
  against +4.3 deg/min over the first 150 s; UKF +3.9 against +5.5). SITL's gyro drift is identical in
  sim time, so the effect is inferred to be the halved sim-time latencies (flow arrival etc.) acting
  through the flow→yaw coupling. Not tested.
- The half-speed comparison is still identical in timing across the three estimators, as ruled.
- Options:
  - **(a)** accept the miss as worded. Record the half-speed EKF3/UKF set (a) as the half-speed
    references, and re-derive the FGO's no-heading window from half-speed data (its shadow run), not
    from full-speed data. Continue with the ordered sequence (D20, then the with-heading sets).
  - (b) additionally test the mechanism: a Replay/offline check of flow-latency sensitivity of the
    closed-loop drift, e.g. re-timing flow in the UKF by the half-speed latency.
  - (c) re-think half speed for the no-heading comparison (e.g. compare the FGO at half speed against
    the half-speed EKF3/UKF only, which (a) already does).
- **Recommendation: (a)**, with (b) as a non-blocking diagnostic.
- **Note for the thesis:** no-heading closed-loop results depend on simulation timing; the full- and
  half-speed sets are not interchangeable.


### D20. `VISO_DELAY_MS` at half speed: (a) and (b) disagree by 5.4 ms (BLOCKS every half-speed flight)
- `gt_heading_half_b`: (a) node sent − capture min **20.0 ms**; (b) `VISP` receipt − capture min
  **25.4 ms** (sim time). The pre-registered tolerance is 5 ms, so the run stopped as worded.
- (The first attempt, `gt_heading_half`, was VOID: the Wi-Fi dongle faulted and broke gz multicast
  discovery. Fixed by loopback pinning for all half-speed flights.)
- Options:
  - **(a) 25 ms from (b)**, as D2 took (b): EKF3's timestamp is the receipt-based value;
  - (b) 20 ms from (a);
  - (c) repeat the ground test once and apply the rule to it.
- **Recommendation: (a) 25**, then run 2 (the G1–G5 verification ground test) before any
  half-speed flight. The 5.4 ms is a fifth of a camera frame and within the p5 spread of both
  measures.


### D19. D12 route and the take-off backlog fix (report: `docs/d12_fgo_backend_report.md`)
- **The backlog is throughput.** The FGO step is 42–49 ms (max 54) against the 33.3 ms keyframe
  period for ~6 s around lift-off → ~1.7 s lag. There is only ~10% headroom in cruise (29.8 ms), so it
  drains over ~16 s.
- **Route (a), the FGO AHRS backend** (reusing the UKF wiring, its own input route since `ODOMETRY`
  carries the camera heading, an in-ArduPilot output predictor, validity, full validation): about
  **4.5–5 working days**. No hard blocker. Fallback (b), EKF3 fusing the FGO via ExtNav: 1.5–2 days,
  labelled as ruled.
- **Backlog fix options:**
  - **(F1) SITL at `real_time_factor` 0.5**: the estimator is unchanged and no backlog is expected,
    but flights take 2× wall time, and the sim-time latencies change (risk iv: the heading delay would
    be re-measured, or the EKF3 references re-flown at the same RTF);
  - (F2) the D11 speed-up (days; needed for a real drone);
  - (F3) keyframe decimation while behind (tuning, not recommended);
  - (F4) EKF3 flies the take-off (not "the FGO flying", not recommended).
- **Recommendation: route (a) + F1, with the heading delay re-measured at RTF 0.5 and the latency
  budget (≤ 250 ms estimate age, arming to landing) pre-registered.** Also rule whether the EKF3/UKF
  closed-loop references are re-flown at the same RTF.

### D18. EKF3's STATIC yaw fusion on the ground (pre-arm gyro-z bias learning): give it to the UKF?
- From the gyro-bias diagnostic: with no yaw source, EKF3 fuses the yaw stored when the vehicle last moved
  whenever `onGroundNotMoving` (`MagFusion.cpp:262-277`), so it learns gyro-z bias while disarmed.
  In P3 it reached 0.0100 deg/s pre-arm, then froze once the motors spun.
- The UKF (offline and port) has only the zero-innovation form, so it learns nothing on the ground.
- Effect: a pre-flight bias head start for EKF3 in the **no-heading** comparison (~0.6 deg/min against
  cruise drifts of ~8–10). None with the heading.
- Options:
  - **(a)** port EKF3's STATIC branch to the UKF (offline and port), EKF3's approach as in D15; then
    re-run the no-heading UKF results (a D15-style re-run) and restate them;
  - (b) record it as a known asymmetry, with the magnitude above, and change nothing.
- **Recommendation: (a)**, for the same fairness reason as D15. The expected effect is small (a
  reduction of ≲ 0.6 deg/min in the UKF's no-heading drift), and it would be measured, not assumed.

### D17. RULED (a) 2026-09-30: UKF heading at EKF3's 5°. V1–V4 all PASS (the with-heading UKF set 3/3)
- **The no-heading UKF flight is done:** `cl_ukf_a_tex`, PRIMARY PASS, west-wall contact at cruise +163.0 s
  inside [+146, +218].
- **The port has no heading path yet** (noted at D9). "Validate the port's heading input" therefore
  needs the input built first. Proposed design, EKF3's own path throughout:
  - **Input:** hook `AP_AHRS::writeExtNavData` (called by `AP_VisualOdom_MAV` after its quality gate
    `VISO_QUAL_MIN 50` and the `angErr` clamp to [`VISO_YAW_M_NSE` 0.05 rad, 1.5]), so the UKF gets
    the identical message and quality gating. It is also hooked in `AP_DAL`'s replay of ExtNav
    (`AP_DAL.cpp:501`), so it runs in Replay.
  - **Timing:** EKF3's (`AP_NavEKF3_Measurements.cpp:1100-1105`): timestamp − `VISO_DELAY_MS` −
    filterStep/2, clamped to the horizon; an `EV_HEADING` event in the D5 queue.
  - **Update:** yaw from the quaternion, a scalar UKF update, gated at χ² 9 (`EK3_YAW_I_GATE` 300, as
    the offline heading arm).
  - `UKF=1` + `HEADING=1` enabled together in the launcher.
- **The open choice: the σ the UKF applies.**
  - **(a) EKF3's effective σ: max(angErr, 5°) = 5°** (`writeExtNavData`, `AP_NavEKF3_Measurements.cpp:1118`),
    as set (b) flew. This is EKF3's approach, as with D5/D15.
  - (b) `angErr` as received: 0.05 rad = 2.86° (the `VISO_YAW_M_NSE` floor), without EKF3's internal
    5° floor.
  - (c) the camera's measured 0.148° (offline Phase 4). This is not reachable through the same message
    path, whose clamp is ≥ 2.86°, so it would need a bypass.
- **Validation, to be pre-registered after the ruling:**
  - (1) Replay on set (b)'s `LOG_REPLAY` logs (`cl_bcpp_tex_r1..r3`): every ExtNav message EKF3
    consumed reaches the UKF, at EKF3's timestamp, with the same yaw and `angErr`.
  - (2) the UKF with heading in that Replay: yaw error against SIM within a band.
  - (3) a shadow run of the exact binary with `HEADING=1`.
  - (4) a ground test; then the set ×3, with bands mirroring set (b)'s B1–B5.
- **Recommendation: (a)**, with this design.

### D16. RULED (a), 2026-09-30: P3 yaw miss recorded as worded; flying not blocked (the no-heading flight has since PASSED)
- Run `ukf_groundtest_p3` (`AHRS_EKF_TYPE 12`, the exact P2 binary, md5 `2d631fa7…`; 65 s armed hold).
  `eval/results/ukf_p3_check.json`.
  - G1 config, G2 arming, G3 (the UKF is the ACTIVE attitude source: ATT = XUKO at 0.0005° p95,
    closer to the UKF than to EKF3 in 578/578 discriminating samples) and G5 (disarm, no
    failsafe/crash text) all PASS.
  - G4: horizontal 1.2 mm, height error 0.9 mm, healthy, EvO 0 all pass, but **yaw moved 3.09°
    (bound 1.0°): FAIL.**
- **Diagnosis:** the vehicle is stationary (SIM yaw ±0.00°), and SITL's gyro z drifts 0.047 deg/s
  (2.85 deg/min) over the hold. With no heading source, yaw is unobservable on the ground.
  **EKF3 drifts +2.15° over the same hold**, and the UKF +3.09°.
- The 1.0° bound was extrapolated from P2's 3.5 s arming-to-take-off segment. That basis ignored
  gyro drift over a 65 s hold. My error.
- Options:
  - **(a) record the miss as worded, with the diagnosis, and proceed to the no-heading flight.**
    Every backend check passed. The yaw behaviour is the no-heading configuration's, shared by the
    baseline EKF3 (2.15°), and the flight prediction already assumes a drifting yaw.
  - (b) pre-register a corrected yaw criterion (e.g. the UKF's hold yaw change within 2× EKF3's on
    the same hold, or within the integrated raw gyro ± 1°) and re-run P3 on the same binary.
  - (c) stop and investigate why the UKF drifts ~1.4× EKF3 on the ground (the UKF's gyro-bias
    learning while stationary) before flying.
- **Why the UKF drifts more on the ground (checked in the log):** the UKF learns essentially NO gyro-z
  bias while stationary.
  - Its state `XUKF.GBZ` stays at about −1.5e-6 rad/s (≈ 0.0001 deg/s) through the hold, against
    SITL's 0.047 deg/s.
  - 0.0474 deg/s × 65 s = 3.08°, which matches the UKF's 3.09°: it integrates the raw gyro.
  - EKF3's `XKF1.GZ` reaches 0.010 deg/s (≈ 21% of the drift), hence its smaller 2.15°.
  - (In cruise the ordering differs: on P2 the UKF drifted 4.3 deg/min against EKF3's 7.54.)
- **Recommendation: (a)**, with (c) as a DIAGNOSTIC in parallel (it does not block).
  - (b) would re-score what is, in substance, the same outcome.
  - (c) is now a specific question: why the UKF's z-bias state does not move on the ground when
    EKF3's does, with the same process noise.

## RULED (history)
- **D8** (flow timing): EKF3's timing kept in the port. Replay diagnostic done: re-timing costs EKF3
  nothing measurable (textured median −0.006 m, never helps > 2 mm; blank n/a). Fairness note recorded.
- **D9** (first UKF flight): (c), without heading first. Preconditions P1 and P2 and the predictor check
  PASS (after D15). P3 is D16.
- **D10** (FGO TUM typo): fixed, restated. **D11** (FGO speed-up): deferred. **D12** (FGO backend):
  prefer the AHRS backend; the effort/blocker report is owed. **D13** (FGO step 3): accepted.
  **D14** (comparison fixes): accepted.
- **D15** (UKF take-off kick): (b). EKF3's ground-proximity rule applied to the UKF (offline and port)
  and the FGO. Full re-run done (240 replays); numbers restated. Kick gone on the six poor dsn flights;
  a residual post-detection kick remains on fwdplainc r2/r3 (UKF-only). The confirmatory test holds.
- **D1** (B4 time-window scorer): bug fix. Set (b) with the Python node is "3/3 corrected, 2/3
  original".
- **D2** (C++ heading node): switched. `VISO_DELAY_MS 38`; ground test passed; set (b) re-flown 3/3.
- **D3:** withdrawn (the UKF step 2 bug).
- **D4:** information only (the port's binaries rebuilt); no ruling needed.
- **D5** (UKF flow delay buffer): added; step 3 re-run; shadow re-measured.
- **D6:** not needed.
- **D7** (the FGO node route): started. Steps 2–3, real-time, validity and shadow runs are done (see
  D11–D14).

### D15. UKF take-off yaw kick: adopt EKF3's low-height flow rule? (BLOCKS the UKF flights)
- P2's predictor check failed only at lift-off: the fused yaw jumped ~7° while truth stayed flat. The
  predictor itself is correct.
- The same kick is in the OFFLINE UKF on every poor textured flight (−5…−17° at take-off → 13–36 m),
  and absent from the 3 good ones (2.3–4.3 m). The FGO has none.
- EKF3 zeroes the flow while take-off is not detected and the height is below 0.5 m
  (`AP_NavEKF3_OptFlowFusion.cpp:45-51`). The UKF lacks this rule.
- Options:
  - **(a) adopt EKF3's rule in the UKF port only**, as with D5 (EKF3's approach, fair to EKF3). Then
    P2 and the predictor check are re-run and the flights proceed. The offline UKF results stay as
    they are, with this recorded as the explanation of their variability.
  - **(b) (a), plus a correction of the offline UKF** (a batched correction like (i)–(v): re-run the
    UKF replays, restate the UKF numbers, move the old values to the superseded section). This changes
    comparison results, so it needs your explicit ruling. It is likely to move "poor in most textured
    flights" substantially.
  - (c) no change: fly the UKF as is, with the ~7° take-off kick expected. The no-heading prediction
    already spans it.
- **Recommendation: (b).** The offline UKF's comparison is currently dominated by a missing EKF3
  behaviour, not by the filter, and correcting it is what fairness requires.
  - Minimum (a), so the port does not fly with a known take-off kick.
  - Take-off detection for the port: AP_AHRS's `likely_flying` flag (the vehicle's own detector), as
    EKF3 uses `takeOffDetected`. Offline: the same < 0.5 m height test with a take-off detector from
    the IMU/range data, stated.

### Former OPEN text of D8–D14 (all now ruled), kept as history


### D8. Flow timing (from D5's step-3 re-run)
- EKF3's flow timestamp hard-codes a 100 ms flow interval. Across the 28 re-flown trials with flow
  fused, EKF3 fuses our flow **31–44 ms before capture** (median 36), which is **15–27 ms before the
  frame's mid-time** (median 19). `EK3_FLOW_DELAY` cannot correct this (non-negative).
- The port with D5 copies EKF3's timing. On `dsn_tex_r2`, with flow at the offline UKF's time
  (capture), ArduPilot's other inputs cost the port only 0.41 m (5.06 m with EKF3's timing).
- Options:
  - **(a) keep EKF3's timing in the port** (fair: both fuse at the same time), and measure EKF3's own
    cost in Replay with the interval corrected (diagnostic only);
  - (b) time the port's flow correctly (a non-EKF3 improvement, stated as such);
  - (c) both.
- **Recommendation: (a) + the EKF3 Replay diagnostic.**

### D9. First UKF flight: with or without the forward-camera heading
- In live shadow the port drifts about 24 deg/min. That is the algorithm: the offline UKF drifts
  29.9 deg/min on the same flight. Without heading, wall contact would be expected at about +110 s.
- **Preconditions before any UKF flight, whichever option:**
  - the D5 event queue is not covered by step 2 (the harness calls the numerics directly), so confirm
    `_n_ev_overflow` = 0 (log it) and check the processed order against EKF3's timing rule from the
    Replay input dump;
  - a shadow run of the exact binary to be flown.
- Options: (a) with the heading (port the heading update, then steps 2–3 for it, then shadow, then
  fly); (b) without heading first, as a UKF set (a), with bands pre-registered from the drift;
  **(c) both, (b) first.**
- **Recommendation: (c).**

### D10. `fgo_replay.py` TUM quaternion typo
- The w component is written as `sr*sp*cy`, where it should be `sr*sp*sy`. The quaternion is
  non-unit, giving ~0.002° of yaw error in the offline FGO's TUM orientations. Positions and ATEs are
  unaffected.
- **Recommendation: fix it and re-derive only the numbers that read FGO yaw from TUM files.**

### D11. FGO speed-up route
- Under simulation load the step is 29.7 ms median and 49 ms p99, and 5.8% of keyframes exceed
  33 ms (absorbed by the queue). There is no margin for slower hardware.
- A C++ factor with identical numerics needs GTSAM 4.2.1 **and its Python wrapper** built from source
  (hours). Then step 2 re-passes on the new build.
- **Recommendation:** not needed for SITL; do it once, for Pi deployment.

### D12. External-estimator backend for the FGO
- **Route (a), exists:** EKF3 fuses the FGO pose/velocity as ExternalNav. Caveat: "EKF3 re-filtering
  the FGO", with double-counted IMU. **Route (b):** a new MAVLink External-AHRS backend (4–6 pw).
- **Precondition for route (a):** the node's queue lag must stay within EKF3's 250 ms ExtNav delay
  cap. Under load it does in steady cruise (median 135 ms), **but not during take-off:** a backlog
  rises from take-off (about 28 s), peaks at 1.9 s at the cruise start and clears by about +15 s.
  Needed first: warm-up / a readiness gate before arming, or holding ExtNav fusion until the lag
  settles.
- **Recommendation: (a), with that precondition solved and shown in a shadow run.**

### D13. Ruling on FGO step 3 (owed: the UKF gate was "step 2 passes AND step 3 is ruled on")
- FGO step 2 **passes** on both logs, with the final core.
- FGO step 3: the node's causal inputs cost < 0.1 m against truth on `dsn_tex_r2` (4.20–4.30 against
  the offline 4.298 m). **n = 1 flight**, at the 0.13 m noise floor.
- Shadow run 4 on its own bag: live 4.606 against offline 4.616 m.
- **Recommendation: accept step 3 as reported.** Optionally, add the step-3 comparison on 2 more
  textured flights to firm up n = 1.

### D14. Confirm the equivalence-test comparison fixes (the same category as D1)
- **FGO FE2** is scored with the node's attitude passed through the offline TUM writer, typo included,
  so both sides are in the same representation. The first score (0.0016°) compared unlike
  representations.
- **FGO FE1** is compared row by row, because interpolating at the reference file's rounded
  timestamps added ~1e-4 m in a blank runaway.
- **UKF step 3's matcher** was corrected: matching by value within a time window, not by scanning
  forward from index 0.
- **Recommendation: confirm these as comparison fixes, not criterion changes.**

