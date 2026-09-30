# Decisions queue

Updated 2026-09-30. Only OPEN items are at the top. Ruled items are kept below as history.
Details for every item are in METHODOLOGY.

## OPEN

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

## RULED (history)
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
