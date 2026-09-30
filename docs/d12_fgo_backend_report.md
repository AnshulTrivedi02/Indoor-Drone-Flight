# D12 — FGO as an AHRS backend: effort and blocker report (2026-09-30)

Ruling D12: prefer an external-estimator AHRS backend, so that the FGO's estimate and validity drive the
controller, reusing the UKF's `AP_AHRS` wiring. Report the effort and any blocker first. Either route must
solve the take-off backlog (peak 1.9 s) first. This report was delivered after the UKF flights, as ruled.

## 1. The take-off backlog: cause (measured) and proposed fix

**Measured on `fgo_shadow_sitl_tex4`** (the live node, separate core process;
`~/thesis_data/batches/fgo_shadow4/fgo_shadow_sitl_tex4.npz`). Keyframe period 33.3 ms (30 Hz sim time),
RTF ≈ 0.98:

| window (sim s) | step median / p95 / max (ms, wall) | lag median |
|---|---|---|
| 20–27 (armed, on ground) | 25.5 / 28.3 / 29.9 | 150 ms |
| 27–29 (lift-off) | 43.6 / 51.7 / 52.9 | 179 ms |
| 29–31 | 49.0 / 52.5 / 53.9 | 1,063 ms |
| 31–33 (cruise start) | 42.4 / 51.2 / 54.0 | 1,694 ms |
| 33–37 | 25.4 / 28.5 / 31.1 | 1,369 ms |
| 37–45 | 29.6 / 33.0 / 59.2 | 509 ms |
| 45–330 (cruise) | 29.8 / 33.4 / 60 | 135 ms |

- **Cause:** for about 6 s around lift-off the smoother's step takes 42–49 ms, above the 33.3 ms period.
  That accrues ≈ 6 × (1 − 33.3/47) ≈ 1.7 s of lag.
- In cruise the step (29.8 ms) leaves only ~10% headroom, so the backlog drains at ~0.1 s per s and takes
  ~16 s. Steady lag returns at ~51 s, matching the recorded profile.
- The cause is throughput (Python `CustomFactor` callbacks), not a defect.
- Not yet re-measured with the D15 rule in the node core; the first shadow run on either route re-measures it.

**Fix options:**
- **(F1) Run the SITL simulation slower (Gazebo `real_time_factor` 0.5, lockstep SITL follows).** This is
  the recommendation for SITL.
  - The estimator is unchanged. Wall time per keyframe becomes 66.7 ms, against a take-off step max of
    ~54 ms and a cruise max of ~60 ms, so no backlog should form. The steady lag would stay near the
    current ~135 ms (sim time: about half, since the lag is wall-clock).
  - Cost: flights take ~2× wall time.
  - It needs world copies differing only in `real_time_factor`. Every other world property is unchanged,
    so the conditions are identical. It is SITL-only: it does not help a real drone.
- (F2) The D11 speed-up: C++ factors, or GTSAM's native factors in place of Python `CustomFactor`.
  This is the permanent fix, needed for the real drone. Effort: several days. Deferred by D11.
- (F3) Temporary keyframe decimation while behind (a longer `kf_dt` when lag > threshold). This changes
  the estimator during take-off, so it counts as tuning and is not recommended.
- (F4) EKF3 flies the take-off and the FGO takes over once its lag is inside budget. The flight is then
  not "the FGO flying" from arming, so it is not recommended as the main route.

**Budget, to be pre-registered:** estimate age (sim) at the controller ≤ 250 ms from arming to landing
(EKF3's ExtNav delay cap, as the reference). With F1, the expected worst case is ~70 ms plus transport.

## 2. Route (a): an FGO AHRS backend (preferred by D12)

The UKF work supplies most of the pattern:
- `EKFType`;
- the 52 generated switch arms (the generator script handles nesting);
- a backend class (`AP_AHRS_UKF` → `AP_AHRS_FGO`) with results, positions, variances, control limits,
  pre-arm and status;
- the launcher mode.

| item | work | estimate |
|---|---|---|
| A1 | `EKFType::FGO` (13), `AP_AHRS_FGO` backend, generated switch arms, `AHRS_EKF_TYPE 13` | 0.5 day |
| A2 | **Input path.** The node sends its delayed state: time of validity on the SITL clock (via the `/imu/time_ref` map the node already has), position, velocity, attitude, gyro/accel bias and valid flag. `ODOMETRY` is taken by the camera heading (it goes to `AP_VisualOdom`), so the FGO state needs its own route: `ODOMETRY` with a distinct `estimator_type` intercepted before `AP_VisualOdom`, or a dedicated UDP input in the backend. The input is logged (a DAL-style record), so Replay can re-drive the output predictor. | 1 day |
| A3 | **Output predictor in ArduPilot.** Buffer the DAL IMU deltas. On each FGO state, re-propagate from its time of validity to now (the UKF port's process model, mean only), then propagate forward each loop. This is EKF3's output-predictor role, and the same as the UKF's `compute_output`. | 1 day |
| A4 | **Validity.** Invalid when there has been no FGO state for > 250 ms, or its age exceeds budget, or the node flags invalid (its existing validity rule). Health and pre-arm follow from it. | 0.5 day |
| A5 | **Validation, mirroring the UKF.** Pre-registered checks: input equivalence (sent state = received state; time mapping); the predictor check on a shadow run; latency through take-off within budget; a ground test (G1–G5); then set (a) and set (b) flights. | 1.5–2 days, including flights |

**Total: about 4.5–5 working days** for route (a), including validation, with F1 for the backlog.

**Blockers:** none hard. The risks are:
- (i) the input route: A2 must not disturb the camera heading's `ODOMETRY` path. It is solved by the
  distinct route and verified in A5.
- (ii) wall-clock coupling: the node runs in wall time while SITL runs in lockstep, so the estimate age in
  sim time depends on RTF. F1 makes the margin explicit, and A5 measures it.
- (iii) the D15 node core's take-off step time has not been measured live yet.
- (iv) **F1 changes the wall-clock latencies as seen in sim time.** At RTF 0.5, each bridge's and node's
  wall-clock delay counts for about half as much sim time: flow arrival (median ~24 ms at RTF ~1), and the
  camera heading node's measured delay behind `VISO_DELAY_MS 38`. So the FGO flights would not run under
  the exact latency conditions of the EKF3/UKF closed-loop sets.
  - D8 shows EKF3 is insensitive to its flow timing at this scale.
  - The heading delay would need re-measuring at the new RTF (the `VISO_DELAY_MS` basis).
  - Alternatively, the EKF3 reference sets are re-flown at the same RTF. **This needs a ruling alongside
    F1.**

## 3. Fallback route (b): EKF3 fuses the FGO via ExternalNav

About 1.5–2 days: the node sends `ODOMETRY` position/velocity/yaw; EKF3 sources are set to ExtNav; plus
validation. As ruled, it must be labelled "EKF3 fusing the FGO's output" everywhere, with the IMU
double-counting and the 5° yaw clamp stated. It shares the camera heading's `ODOMETRY` path, which makes
heading-plus-FGO flights awkward. Not recommended unless route (a) is ruled infeasible.

## 4. Recommendation

- **Route (a), with F1** (a slowed-down world copy for FGO flights, with the budget pre-registered).
- D11 (the speed-up) stays deferred for SITL and becomes necessary only for the real drone.
