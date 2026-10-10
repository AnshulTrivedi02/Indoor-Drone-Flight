# Handover, 2026-10-10: rung-1 software R7 (mocap recorder), R8 (mocap_align on RISI), R9 (scorer)

**Stage:** coding and light tests only. No flights, no simulator, no replays. METHODOLOGY and numbers.md NOT edited.
Stored trial data only read: one packed bag (`cl_ukf_a_tex_half`) was decompressed to the scratchpad, the GT pose and
`/imu/time_ref` were extracted, and the copy was deleted.
Branch: `worktree-agent-a1325f77ec99bdd6a` (based on `fwd-camera` 3a2c3a8). Not merged.
A check (`find ~/thesis_data/trials -newermt '2026-10-10 12:00'`) found that no file in the stored trial data was
modified.

## STATUS AFTER THE USER'S TRIAGE (2026-10-10): R7 and R8 ON HOLD, R9 continued

R7 and R8 are **ON HOLD** until the supervisor confirms the hardware and a mocap booking. Both are committed in their
current state (`b13c494` R8, `d60b77b` R7). No further work was done on them after the triage.

**What exists:** everything described in the R8 and R7 sections below, tested as described there.

**What is left before either is used on real data.** These are review findings, NOT fixed because of the hold.

- **R8, blocks R13:** `mocap_align.main()` calls `default_windows(fc)` unconditionally.
  - That function takes the first `ArmState == 1` event. A disarmed hand-carry log (R13) has none, so the call raises
    `IndexError` even when `--early/--late/--init-seg` are given.
  - The default early window `(arm, arm + 25 s)` also starts AFTER the pre-arm sync wiggle (plan §3.2 step 1).
  - The late window is anchored on the last rangefinder reading above 0.5 m.
  - **Fix:** compute defaults only for the missing arguments. Make the early window run from log start (or first
    motion) to arm + N, and the late window from landing − N to log end. With no ARM record, stop with a clear request
    for explicit windows.
  - **Test:** a synthetic log with wiggles before arming and after disarming, and one with no ARM record.
- **R8:** the 25 Hz `IMU` fallback fails with the new fine-fit settings (see below). Remove it, or give it its own
  settings and re-validate.
- **R8:** absolute accuracy on real data is unmeasured. Measure it on the R13 log.
- **R7, blocks real use:** the recorder drops every frame with `frame_no <= last` as a duplicate.
  - A forwarder or Motive restart resets the frame counter, so the rest of the flight would be silently discarded.
  - **Fix:** treat a large backward jump (or N consecutive rejections) as a restart. Log an event, reset that body's
    state, and keep writing.
  - `export.py` must then refuse a log with a restart or clock faults unless a segment is named, because sorting by
    `t_mocap` would interleave the segments.
  - Add a test.
- **R7:** write the system-specific forwarder (NatNet / Vicon / VRPN → MCP1) once the system is known. Unify
  `realflight/mocap/source.py` with the watcher's `mocap.py`.

**R9 after the triage:**
- The end-to-end SITL test now aligns ground truth to the FC clock with the EXISTING tool,
  `input_timing.clock_offset`, not R8 (script `eval/results/r1_scorer/e2e_cl_ukf_clockmap.py`).
- Three review fixes were made, with synthetic tests in `eval/real_score_test.py` (3 tests, pass). See "R9 updates"
  below.

## R8: `eval/mocap_align.py` on the 400 Hz RISI records

**Changes:**
- **FC gyro from `RISI` (default `--gyro-src RISI`, instance 0).**
  - RISI has no `TimeUS`, so each record takes the TimeUS of the preceding `RFRH`.
  - Rate = DA/DADT.
  - **Stamping rule:** at the centre of the delta, TimeUS(RFRH) − DADT/2. This is recorded in the JSON.
  - **No group-delay shift for RISI** (raw-gyro deltas). The 25 Hz `IMU` path keeps its 11.3 ms shift (`--gyro-src IMU`).
  - **SITL finding:** the median DADT is **3.0 ms** in `cl_ukf_a_tex_half` (the plan said 2.0 ms). Check this on the
    first real log.
- **BUG FIXED (inverse time map).** The old `to_fc` carried an extra `rate·o1/(1+rate)` term. It was invisible at the
  self-test's 3.5 s offset, but is about 0.1 ms per second of offset, i.e. hours of error for an epoch-stamped mocap
  clock. Correct form: `t_fc = (t_mocap − o1 + rate·t1)/(1+rate)`.
- **Coarse offset:** whole-flight cross-correlation of the standardised |ω| (20 ms grid). Handles any offset size; the
  peak ratio is reported. The take-off rule and a given offset remain as options.
- **Fine fit:**
  - the normalised correlation of the standardised features (robust to gyro bias and scale);
  - mocap and FC **dropouts are masked** (a gap > 3× the median spacing, dilated by the boxcar);
  - the window offsets are **re-fitted with the in-window drift**, so each offset belongs to its window centre. Without
    this, 150 ppm over a 25 s window biased each offset by up to ~2 ms;
  - **parabola refinement** of the minimum (the old argmin of a 0.05 ms grid picked noise bumps, up to 1.4 ms).
- `--out-dir` is now required (it used to default to the current directory). Two or more windows are allowed, with a
  linear least-squares fit and residuals.

**Validation (`eval/mocap_align_validate.py`, results in `eval/results/r1_mocap_sync/`):**

| test | offset error | rate error | notes |
|---|---|---|---|
| **synthetic**, 8 seeds; offset 1.7e9 s ± 0.5 s; drift ±150 ppm; mocap 120 Hz, 0.05° and 0.3 mm noise, 0.2 ms stamp jitter, 4 dropouts (one in each fit window); RISI-like 400 Hz with bias and noise | mean −0.19 ms, \|max\| **0.64 ms** | mean +0.6 ppm, \|max\| **4.4 ppm** | mapped-time error ≤ 0.71 ms over 200 s. Noise-free floor: 0.01–0.02 ms |
| **SITL differential** (`cl_ukf_a_tex_half`, GT as mocap; inject +1.7e9 s, +150 ppm) | **−0.004 ms** | **−0.07 ppm** | the unknown base map cancels |
| **SITL absolute vs SIM2** (physics position, 400 Hz, velocity-matched; independent of gyro and attitude) | early −1.15 ms, late +3.0 ms | +22 ppm (161 vs 138) | about one 3 ms SITL physics step |
| **SITL absolute vs `/imu/time_ref` lower envelope** (an upper bound: it includes the bridge latency; window residual up to 3.9 ms) | early −0.4 ms, late −11.4 ms | −59 ppm (161 vs 220) | consistent with an upper bound; too coarse to judge the rate |
| **SIM self-test with RISI** (10 Hz SIM attitude) | −0.65 ms | +4.8 ppm | yaw −0.09° (previous IMU self-test: −3.7 ms, 4.9 ppm, 0.30°) |

- The recovered SITL map: 6.2 ms early, 36.1 ms late, 161 ppm. The METHODOLOGY figure for the earlier datasets is
  ~200 ppm.
- **Honest limit:** on SITL the absolute agreement is about ±1–3 ms, and the late-window correlation is lower (0.997).
  The synthetic test is the precise one. Real mocap noise and the real gyro will set the real figure: report it from
  the hand-carried log (R13).
- **IMU path, for comparison:** with the new defaults (0.1 s boxcar, 5 ms grid) the 25 Hz IMU path **failed** in the
  late window (−431 ms, −2078 ppm). The 25 Hz IMU signal is too slow for these settings. It was not tuned, because
  RISI supersedes it; do not use `--gyro-src IMU` without re-validating it.

## R9: `eval/real_score.py` (the rung-1 scorer)

**Inputs, all on the FC clock:**
- mocap TUM (the `mocap_align` output);
- estimators as TUM (`--est LABEL=path`), or read from a log (`--est-bin LABEL=RECORD --bin`): `XKF1` core 0 for
  EKF3; `XUKO` (the current-time output, the counterpart of `XKF1`) or `XUKF` for the UKF; NED → ENU;
- a pre-registration JSON. Its sha256 is in the output; `eval/real_score_prereg_example.json` is an EXAMPLE, and R10
  sets the real values.

**Window, from mocap only, the same for all estimators:**
- `airborne`: take-off + a to landing − b, from the mocap height above the initial ground level, using the longest
  airborne run;
- `speed`: three_way_eval's rule;
- `fixed`: tests only.

**Metrics:**
- `evo_ape_a_se3`: three_way_eval's own call, imported, so it is identical;
- `ate_4dof`: yaw plus translation, computed in house, since evo has no 4-DoF alignment;
- `drift_start_aligned`: a 4-DoF fit on the first 10 s, then RMSE, max, final, and final horizontal error as a
  percentage of the mocap path length;
- coverage.

The prereg names the primary metric.

**Tests (`eval/results/r1_scorer/`):**
- **Regression on `dsn_tex_r1`**, three_way's cruise window as a fixed window:
  - UKF **3.983563**, FGO **4.067897**: identical to `three_way_eval` to all printed digits;
  - the `speed` rule reproduces the window [30.348, 333.041] exactly.
- **End-to-end on `cl_ukf_a_tex_half`**:
  - GT as mocap, aligned by R8 on RISI;
  - EKF3 from `XKF1`, the UKF port from `XUKO`/`XUKF` (onboard records standing in for Replay output);
  - the FGO TUM mapped from the sim clock to the FC clock with R8's map, in the test script
    `test_map_fgo_to_fc.py`, not in the scorer;
  - example prereg (airborne, +25 s / −5 s); window [53.19, 223.23] s.

| est | evo -a SE3 (m) | 4-DoF (m) | drift final (m) | drift % of path |
|---|---|---|---|---|
| FGO | 0.682 | 0.682 | 5.94 | 6.9 |
| EKF3 (XKF1) | 0.893 | 0.893 | 8.61 | 10.0 |
| UKF (XUKO) | 0.983 | 0.983 | 8.69 | 10.0 |
| UKF (XUKF) | 0.983 | 0.983 | 8.69 | 10.0 |

These are SITL plumbing numbers, NOT results: a straight half-speed corridor flight with the UKF flying.
(Re-run with the updated scorer: `eval/results/r1_scorer/cl_ukf_a_tex_half_r8align_gt_as_mocap.json`; unchanged.)

### R9 updates after the triage (three review fixes, then re-tests)

**1. Mocap dropouts.**
- The in-house metrics (`ate_4dof`, `drift_start_aligned`) interpolate mocap only where the two bracketing samples
  are at most `max_mocap_interp_gap_s` apart (default 0.05 s). Other estimator samples are dropped from these metrics
  and counted (`n_dropped_mocap_gap`).
- evo is still given the full cropped estimate (it associates by nearest stamp within `t_max_diff`), so it stays
  identical to `three_way_eval`.

**2. Ground level for the airborne rule.**
- It is now the 5th percentile of mocap z over the WHOLE record. It was the median of the first 3 s, which a record
  starting with the vehicle held up for the sync wiggle would have broken.
- The prereg key changed from `ground_ref_s` to `ground_percentile`.

**3. Drift-segment guard.**
- `drift_start_aligned` is refused when its initial segment moves less than `drift_min_extent_m` (default 1.0 m)
  horizontally, because the yaw fit is undefined in a hover.
- The segment's extent is reported. **R10 must place the initial segment on horizontal motion.** The example's
  take-off + 25 s window start falls on the rectangle only if the hover ends by then.

**Re-tests:**

- **Synthetic** (`eval/real_score_test.py`, 3 tests, pass):
  - the window ignores a held start (ground 0.000 m, not 1.0 m);
  - a 1.5 s mocap gap across a rectangle corner drops 70–80 samples, with ATE < 10 µm. Without the mask the max error
    exceeds 0.1 m;
  - 1 cm/s drift is recovered within 0.15 m;
  - a hover initial segment is refused.
- **Regression `dsn_tex_r1`:** UKF 3.983563, FGO 4.067897, still identical to `three_way_eval`.
- **End-to-end `cl_ukf_a_tex_half` with the `input_timing.clock_offset` alignment** (TimeUS − sim: −6.0 ms early,
  −50.75 ms late, −275 ppm; the late window was moved to TimeUS > 170 s because this flight is 236 s long):

| est | evo -a SE3 (m) | 4-DoF (m) | drift final (m) | drift % of path |
|---|---|---|---|---|
| FGO | 0.682 | 0.682 | 5.94 | 6.9 |
| EKF3 (XKF1) | 0.893 | 0.893 | 8.61 | 10.0 |
| UKF (XUKO) | 0.984 | 0.984 | 8.69 | 10.0 |
| UKF (XUKF) | 0.984 | 0.984 | 8.69 | 10.0 |

  - This is within 1 mm of the R8-aligned run.
  - The two clock maps differ by ~15 ms late (the 10 Hz SIM-based fit is coarser), which does not move these metrics.

## R7: `realflight/mocap/` (the recorder)

**Adapter choice: the MCP1 UDP pose packet**, identical to the watcher's (`<4sIdI16sb7d`).

**Why:**
- the mocap system is unknown, so the system-specific part becomes one small forwarder (NatNet / Vicon DataStream /
  VRPN → MCP1);
- the same forwarder feeds the watcher;
- the packet keeps the frame number, the tracked flag and the body ID, which PoseStamped drops;
- it needs no ROS on the ground station;
- it is testable with plain sockets.

`pose_stamped_to_sample` is kept as the ROS hook.

**Modules:**
- `source.py`: `MocapSample`, the `PoseSource` interface, `UdpPoseSource`.
- `recorder.py`:
  - writes a raw CSV in the mocap frame and clock, plus `t_rx` (monotonic and wall);
  - writes a JSON sidecar, rewritten every 5 s, with counts, duplicates and out-of-order frames, malformed packets,
    other bodies, frame gaps, time gaps, silences and mocap clock faults;
  - refuses to overwrite an existing recording.
- `export.py`: the ONE conversion point to the `mocap_align` CSV:
  - quaternion order w-first → scalar-last;
  - up axis z or y (Rx(+90°), A R Aᵀ, as in the watcher's `frames.py`);
  - drops tracked = 0 rows, frozen repeats when tracked = −1, and non-increasing times;
  - the time column is `t_mocap` by default.

**Tests:** `realflight/mocap/tests/` (5 tests, pass):
- packet round trip and malformed packets;
- live localhost UDP on an ephemeral port: duplicates, out-of-order frames, malformed packets, another body, a 30-frame
  dropout, untracked rows;
- silence detection;
- y-up export with frozen and untracked rows;
- export read by `mocap_align.load_mocap`.

**What the real system must provide** is in the docstring of `realflight/mocap/__init__.py`:
- a forwarder to MCP1 that sends to BOTH the recorder and the watcher ports (or multicast);
- ≥ 100 Hz;
- the frame number and the mocap-clock stamp;
- a stable body ID or name;
- a tracked flag if available;
- metres, z or y up;
- a monotonic mocap clock with no resets;
- sync wiggles at both ends.

**MUST BE UNIFIED LATER:** `realflight/mocap/source.py` and the watcher's `realflight/watcher/mocap.py`
(worktree `agent-a272a337e54b5ebdc`, not merged at the time of writing) are two identical, independent copies of the
packet and interface. When both branches are merged, keep one module and import it from the other. Also, both add
`realflight/__init__.py` with identical content.

## Open questions

1. **R10 pre-registration** must fix:
   - the window parameters (the example uses +25 s / −5 s and 0.30 m);
   - the primary metric: `evo_ape_a_se3` (the sim's standing rule) or `ate_4dof` (the plan text says "evo -a (4-DoF)").
     The two are nearly equal on SITL, but a short real flight may differ;
   - the UKF record, `XUKO` or `XUKF`. The example uses `XUKO`, the like-for-like counterpart of `XKF1`;
   - the drift metric's initial segment, which must lie on horizontal motion (`drift_min_extent_m`), and
     `max_mocap_interp_gap_s` for the real mocap rate.
2. **RISI DADT is 3.0 ms in SITL against 2.5 ms frames.** Check `DADT` against the `RFRH` spacing on the first real
   log, as the converter spec already asks (R1).
3. **Absolute sync accuracy on real data is not yet measured.** It is synthetic plus SITL only (≤ 0.7 ms synthetic,
   ~±3 ms against SITL references). It is first measured on the hand-carried log (R13). Mocap orientation noise matters,
   so ask for the system's rotational noise.
4. **The mocap-system specifics** (S5): which SDK writes the forwarder, the frame-number semantics, and whether the
   tracked flag exists.
5. **The 25 Hz `IMU` fallback path** does not work with the new fine-fit defaults. It should either be removed or
   given its own settings and re-validated.
