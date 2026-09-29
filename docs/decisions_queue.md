# Decisions queued for the user (overnight 2026-09-29/30)

Each item gives the options and a recommendation. Nothing below blocked other work. Details and
evidence are in METHODOLOGY (section named per item).

## D1. B4 scorer fix on `cl_b_tex_r1` (METHODOLOGY "Closed-loop set (b) r1 ... scorer bug fix")
- The first scorer computed "1 s-smoothed lateral speed" with a sample-count boxcar and
  `np.gradient` on the raw GT stamps. A 1 ms stamp gap produced 0.333 m/s, a false B4 failure.
- A literal 1 s time window gives 0.033 m/s. The band and wording are unchanged.
- Options: **(a) accept it as an implementation fix** (then set (b) passes 3/3); (b) count r1 as a
  B4 failure as first scored.
- **Recommendation: (a).**
- Extra evidence: under the ORIGINAL scorer r2 / r3 give 0.099 / 0.100 m/s (pass). So (b) passes at
  least 2/3 either way, and 3/3 with the fix.

## D2. Switch the live heading node to the C++ computation? (METHODOLOGY "C++ heading port")
- Equivalence passes all pre-registered bands. The SITL latency falls from a median of 141 ms to
  47 ms, which is inside the 60 ms horizon.
- If switched, `VISO_DELAY_MS` must be re-measured by the ORIGINAL G4 rule (the minimum latency,
  about 40 ms), and G5 re-checked in a ground test, because the delay now takes effect.
- Options: **(a) switch, re-measure the delay, and repeat the ground test**; (b) keep Python for the
  thesis's SITL flights and use C++ only for hardware.
- **Recommendation: (a)** for any further closed-loop flights. Set (b)'s results stand as flown
  with Python.

## D3. WITHDRAWN (2026-09-30): UKF step 2 now PASSES on both logs
- A second porting bug was found: ArduPilot's `-fsingle-precision-constant` made every constant in
  the port a float. It is fixed.
- `dsn_blank_r1` E2 ratio is 0.80 (was 1.19), and the gate flips are gone. The earlier "flip-driven
  round-off" reading was wrong. No ruling is needed; listed so you can see the correction.

## D4. Rebuild of the port's SITL binary and Replay tool (information, no ruling needed)
- The shadow-UKF SITL result predates the step-2 fix. The binaries are rebuilt after the `dsn`
  batch. Any future shadow run uses the fixed port.

## D5. UKF port input path (step 3 report; METHODOLOGY "UKF port validation STEP 3")
- On `dsn_tex_r2` the port on ArduPilot's inputs differs from the offline UKF by 5.1 m / 3.8°
  (end of cruise), from three sources:
  - flow fused at arrival: 4.8 m alone;
  - the IMU path: 3.2 m alone;
  - the flow-gyro pairing: 1.5 m alone.
- The full post-fix Replay port scores about 3.4 m evo -a (cruise), between the offline UKF (2.3) and
  EKF3 (3.9).
- Options: **(a) add a flow delay buffer to the port** (fuse at the measurement time, as EKF3 does
  with `EK3_FLOW_DELAY`), keeping ArduPilot's IMU and gyro inputs; (b) keep the port as is (pure
  arrival-time fusion); (c) also reproduce the offline IMU/gyro inputs (not possible onboard, so not
  a drop-in).
- **Recommendation: (a).** It matches EKF3's own treatment of flow latency, so it is fair to EKF3.
  The remaining IMU/gyro differences are properties of the onboard input path, and they are
  reported, not hidden.

## D6. Replacement flight for `dsn_tex_r10` (IMU-gap rule: unusable for UKF/FGO)
- The paired test runs with r10 counted conservatively (METHODOLOGY). A replacement `dsn_tex_r11`
  would give 7 usable flights.
- Options: **(a) fly `dsn_tex_r11`** (about 7 min plus the pipeline) and report the test on
  r4–r9 + r11, alongside the conservative version; (b) keep the conservative version only.
- **Recommendation: (a)** if the conservative verdict is "no ordering" only because of r10;
  otherwise (b).
- **Resolved by that rule:** the conservative verdict is "EKF3 lower" (both criteria), so **(b)**: no
  replacement flight is needed. Listed for your confirmation only.

## D7. Next FGO track (none is registered yet)
- Candidates:
  - (a) the `fgo_node.py` ROS 2 node plus its pending validation (fair yaw anchor, §9 gating checks,
    window sweep, NEES);
  - (b) the C++ GTSAM companion port for Part C route (a), where EKF3 fuses the FGO as ExtNav
    (5–8 pw);
  - (c) proper FGO covariance logging for NEES (it is a gate-only approximation now).
- **Recommendation: (a) then (c).** (a) is the prerequisite for any live or onboard use, and it
  reuses the validated offline core. (c) is small and removes a caveat on every FGO consistency
  claim. (b) is only worth starting after (a) runs live. I did not start any of them without a ruling.

## D8. Flow timing (from D5's step-3 re-run)
- EKF3's flow timestamp hard-codes a 100 ms flow interval, so our 30 Hz flow is fused about 45 ms
  before capture. `EK3_FLOW_DELAY` cannot correct this (non-negative).
- The port with D5 copies that. With flow at its true capture time, ArduPilot's inputs would cost the
  port only 0.41 m against the offline UKF (against 5.06 m now).
- Options:
  - **(a) keep EKF3's timing in the port** (fair: both fuse at the same, equally wrong time), and
    measure EKF3's own cost in Replay with the interval corrected (diagnostic only, never flown);
  - (b) time the port's flow correctly (capture − half the frame interval), a non-EKF3 improvement,
    stated as such;
  - (c) both, reporting the port under each.
- **Recommendation: (a)**, plus the EKF3 Replay diagnostic, because it quantifies a property of the
  baseline itself.
