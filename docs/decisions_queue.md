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

## D2. Switch the live heading node to the C++ computation? (METHODOLOGY "C++ heading port")
- Equivalence passes all pre-registered bands. The SITL latency falls from a median of 141 ms to
  47 ms, which is inside the 60 ms horizon.
- If switched, `VISO_DELAY_MS` must be re-measured by the ORIGINAL G4 rule (the minimum latency,
  about 40 ms), and G5 re-checked in a ground test, because the delay now takes effect.
- Options: **(a) switch, re-measure the delay, and repeat the ground test**; (b) keep Python for the
  thesis's SITL flights and use C++ only for hardware.
- **Recommendation: (a)** for any further closed-loop flights. Set (b)'s results stand as flown
  with Python.

## D3. UKF step 2, E2 on `dsn_blank_r1` (METHODOLOGY "UKF port validation STEP 2")
- One porting bug was found and fixed: a float `asin` inside the sigma propagation.
- `dsn_tex_r2` then passes E1–E5 at about 1e-3 of the bands.
- `dsn_blank_r1` passes E3–E5 but fails E2 as worded: ratio 1.19, on 0.6% of events. That comes
  only after two E5-permitted yaw-gate flips (the ratio is ≤ 0.674 before them), in a 14 km
  unaided runaway.
- Options: **(a) accept step 2 as passed, with the E2 exceedance recorded as flip-driven round-off**;
  (b) run a further diagnostic (the harness follows Python's yaw-gate decisions; needs a
  diagnostic-only gate bypass); (c) re-register E2 for another blank log.
- **Recommendation: (a), with (b) as supporting evidence if wanted.**

## D4. Rebuild of the port's SITL binary and Replay tool (information, no ruling needed)
- The shadow-UKF SITL result predates the step-2 fix. The binaries are rebuilt after the `dsn`
  batch. Any future shadow run uses the fixed port.
