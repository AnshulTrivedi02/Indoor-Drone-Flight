# Handover, 2026-10-12: rung-1 scoring items (prereg final + secondary metrics, capture delays, XUKO, converter band, 25 Hz IMU path, parameter names)

**Stage:** one stage agent; coding only.
- **Branch:** `worktree-agent-a8e6b43cf069fb800`, reset to `fwd-camera` `4449869` first ("Rulings: no-hardware coding
  start …"). NOT merged. `fwd-camera` has moved on since (to `140a946`); none of its changes touch the files edited
  here.
- **Not run:** no SITL, no flights.
- **Run:** ONE light Replay, under `heavy.py` (the installed fork Replay on `cl_a_tex_half`, into the scratchpad), plus
  light converter, timing and scoring runs on stored logs, all read only.
- METHODOLOGY.md and numbers.md are NOT edited. Stored trial data are NOT modified.
- **Implements:** METHODOLOGY "RULINGS (user, 2026-10-12)":
  - item 1: the capture-delay option, the XUKO check, the converter band, the alignment 25 Hz IMU path and the
    parameter-name fixes;
  - item 2: the rung-1 pre-registration SIGNED OFF, with the secondary drift metrics.

## A. The pre-registration is final

- **New files:**
  - `docs/rung1_preregistration.md`, status PRE-REGISTERED, signed off 2026-10-12;
  - `docs/rung1_preregistration.json`, sha256 **`884ff35171a1f7679d6aec5b55ed99f0807c69bdfac5bc761778268afda0ed19`**.
  - The drafts are kept unchanged as the signed record: `.md` `3c412e16…`, `.json` `1680a22f…`.
- **Not "only `status` changed"** (as the draft's §11 had said). The ruling ADDED metrics, so the JSON also changes
  `name`, two `rationale` entries and a new REQUIRED `secondary` section.
  - `window`, `metrics`, `drift`, `estimator_records` and `clock_map` are identical to the draft's; a test checks this.
  - The draft JSON no longer loads, because `secondary` is missing.
- **The changes are listed at the top of the doc:**
  - §4.4 (new) the secondary metrics;
  - the §4.1 `XUKO` implementation flag;
  - §5b (new) the converter band;
  - the §6 delay procedure;
  - the §8 steps;
  - the §9 item 11 factual correction;
  - §10 and §11.
- **The METHODOLOGY entry** (the commit and the JSON sha256) is left to the coordinator or user.

### The secondary metrics (prereg §4.4; `eval/real_score.py` `heading_drift()`, `cross_track()`)
- **Heading drift, deg/min, NED sense** (clockwise positive): the corridor rule exactly (`eval/d15_drift.py`; also
  phase4_eval and d15_port_score).
  - The yaw error (est − mocap) is unwrapped over the whole series, then wrapped to ±180 unless it runs away (≥ 170°).
  - The value is the OLS slope against minutes over the window W. It is offset-invariant, so unaligned.
- **Cross-track drift, m/min:** the lateral position-error growth over the CRUISE samples in W (mocap smoothed speed
  > 0.15 m/s), divided by the cruise minutes.
  - **Lateral** = the right normal of the mocap direction of travel. On a straight northward path that is the
    corridor's East axis and sign. On a closed rectangle a fixed axis would cancel; the path normal does not.
  - **Velocities** come from d/dt of the positions, for every estimator.
  - **UNALIGNED, with one stated anchor:** the estimator frame is rotated by the heading difference at mocap take-off
    (a 1 s circular mean), with no fit. This is a departure from the corridor, where the frames were related by
    construction.
  - **Requirement:** the mocap rigid body's x axis lies along the vehicle's nose. A residual offset is common-mode across
    estimators, and the scorer reports its sensitivity (m/min per degree).
- **The SITL regression** (`eval/results/r1_scorer/regress_secondary_2026-10-12.py` →
  `regression_secondary_2026-10-12.json`, `all_pass: true`):
  - **H1:** heading on `dsn_tex_r1..r3`, UKF and FGO TUMs, against `d15_drift.json` (sign-flipped ENU → NED). Equal
    to ≤ 2e-15.
  - **H2:** heading on the NED-yaw path, `d15_port/dsn_tex_r8` `ukf_shadow.csv` against SIM: 9.293967, equal to the
    stored `score.json`.
  - **X1:** cross-track with `XKF1` VE/VN given reproduces the stored `heading_share_restated.json` `xtrack_err_m` to
    ≤ 4e-5 relative.
  - **H3 (information):** EKF3 `XKF1@0` against SIM on the pinned window: +7.96 / +7.59 / +8.10 deg/min, inside
    +6.6…+11.1.
  - **X2:** the REGISTERED position rule equals the corridor's position-growth form (`ukf_shadow_replay_check.py`
    cross_E) to ≤ 7e-5 relative. The values for EKF3 on `dsn_tex_r1..r3` are 7.06 / 6.56 / 7.24 m/min.
  - **Why X1 and X2 differ by ~9 %:** EKF3's logged VE is not integrally consistent with its PE (∫VE − ΔPE ≈ 3.65 m
    over 302 s). The metric is not the cause.
- **Caveat:** `real_score` run end to end on the stored corridor bag TUMs gives meaningless cross-track values. Their GT
  quaternions use the estimator's yaw-0 convention while their positions are ENU (90° apart). Real sources (XKF1/XUKO,
  the FGO TUM, mocap) are self-consistent. The primary-metric regression is unchanged: dsn_tex_r1 UKF 3.983563 and FGO
  4.04733, identical to three_way_eval.

## B. Capture delays (ruling: UKF/FGO at the best estimate of the true capture time)

- **Converter (`eval/bin2fgo.py`):**
  - `--delays-json` is a strict configuration file: values, uncertainty, the verification logs (with sha256), method
    and status. The template is `docs/rung1_capture_delays_TEMPLATE.json`, which the loader refuses.
  - `--result-flight` refuses anything but `PRE-REGISTERED`.
  - The CLI form still works, recorded as `command_line`.
  - The file's path, sha256 and status go into the output JSON.
- **Proof on SITL `cl_a_tex_half` (16/40 ms):** the npz is array-identical between the CLI form and the JSON form, and
  array-identical to the pre-change converter (`git show fwd-camera:eval/bin2fgo.py`).
- **Tests:** `eval/bin2fgo_test.py`, 2 tests on the delays.
- **Procedure (prereg §6; fixed now, run on verification logs only):**
  - **d_flow:** `sensor_timing_from_log.py --window` per sync wiggle or bench rotation; per-axis rule; windows with
    corr < 0.5 on both axes discarded; the median over ≥ 4 windows.
    - Uncertainty = max(half the range, 2.5 ms of jitter bias).
    - The per-axis rule was written after the SITL data: stated.
  - **d_range:** truth-height method against the `mocap_align` TUM on ≥ 4 climb/descent segments; the median.
    - Uncertainty = max(half the range, the RMS-within-10 % half-width), including the clock-map error.
  - Then a METHODOLOGY entry with the file's sha256, before any result flight is scored.
- **UKF port: SPECIFICATION ONLY,** `docs/rung1_port_spec_capture_delay_xuko.md` §S1.
  - `UKF_FLOW_DCAP_MS` / `UKF_RNG_DCAP_MS` in Replay. The flow time becomes `arrival − d`, replacing all three EKF3
    terms (`EK3_FLOW_DELAY` + 50 + 6), with the horizon clamp kept. The definition is END of the integration interval,
    as in the converter.
  - The derotation window is unchanged.
  - **Regression:** unset = byte-identical; `UKF_FLOW_DCAP_MS=66` = byte-identical to the default (an exact
    substitution test); `=16` changes only the state columns.

## C. XUKO check: ABSENT in Replay of a stock-flown log (FLAG for the user; it is in the signed-off prereg)

`eval/results/r1_scorer/xuko_replay_check_2026-10-12.json`; scripts in `eval/diag/r1_scoring/`.

- **The new light Replay by the INSTALLED fork Replay** (`be7c4d18`, rung1-geometry) of `cl_a_tex_half`, an EKF3-flown
  log with no UKF FMT:
  - the output has NO FMT for XUKF, XUKO or XUKS;
  - their records ARE written, under undeclared dynamic type ids 228/229/230, about 6 672 each;
  - so **XUKO is not decodable**.
- **The same on stored outputs** of older builds: `d15_port/dsn_tex_r8`, scratch `ub` (H_s1_r1, plus XUKH as 227).
- **Fork-flown input** (`d17_v2/ukf_shadow_hdg_v2`): XUKO is declared, but 17 283 = 8 654 copied onboard + 8 629
  replayed, interleaved, with no instance field. They cannot be told apart.
- **A bigger consequence:** the undeclared records break pymavlink on these outputs.
  - Its fast indexer EXITS the process ("Invalid length in FMT message"); its pure-Python reader returns ~15 XKF1 per
    core instead of ~3 457.
  - The old `real_score.bin_trajs` (pymavlink) would therefore have failed, or scored ~15 samples, for the PRIMARY EKF3
    row `XKF1@100`. Its test used fake records and could not catch it.
- **Fixed in the scorer:**
  - **`eval/df_reader.py`:** a strict FMT-driven walk that resynchronises past undeclared records and counts them.
    Every core is read in full (2 684–3 956 per core); the TimeUS of `XKF1@100` equals that of `XKF1@0`.
  - **`bin_trajs` now refuses:**
    - `XKF1@1xx` whose TimeUS sequence differs from `XKF1@(C−100)`'s;
    - a record with no FMT (XUKO here), with the reason;
    - non-increasing XUKO/XUKF stamps (the fork-flown case).
- **The §5 Replay-fidelity gate tool had the same problem.** `Tools/Replay/check_replay.py` uses pymavlink (checked:
  `mavutil.mavlink_connection`), so on the fork's output it would exit or compare ~15 samples.
  - New: `eval/replay_gate.py`, the same criterion computed via df_reader. SITL `be7c4d18` on `cl_a_tex_half`: 0 / 0 /
    0, PASS (`eval/results/r1_scorer/replay_gate_sitl_cl_a_tex_half_be7c4d18_2026-10-12.json`).
  - A TimeUS mismatch between `XKF1@100` and `@0` counts as §3.3 item 2 (prereg §8).
- **What the scorer must use instead (prereg §4.1; user ruling needed):** either one of these, per port spec §S2:
  - **(a)** the port emits the FMTs in Replay. Preferred: XUKO is then read from the log, as registered.
  - **(b)** `ukf_output.csv`, with EXACTLY XUKO's columns and current-time values, read by
    `real_score.py --est-csv UKF=…`. Implemented and tested; the header is checked exactly.
  - **`ukf_shadow.csv` is NOT a substitute:** it is the horizon state, i.e. XUKF.
  - Re-wording the record to XUKF would be an amendment to a signed-off item.
- **Scope:** Replay builds up to `e8e9feac` (stored outputs) and the installed `be7c4d18` (new run). `run_one.sh` deleted
  the 2026-10-11 rung1-geometry outputs.

## D. The converter acceptance band (prereg §5b; `eval/bin2fgo_accept.py`)

- **A1–A10, against EKF3's own inputs and the FC's own sensor records in the same log:**
  - A1 `LOG_REPLAY` = 1;
  - A2 DSF = 0;
  - A3 RISI flags 0, DVDT≠DADT ≤ 0.1 %, DVDT vs frame ≥ 99 %;
  - A4 rate ± 2 % of `SCHED_LOOP_RATE`;
  - A5 the converter IMU through the INS 2-pole filters against the FC `IMU` record, on the DISARMED spans only (the
    sync wiggles; in flight, prop vibration would cause false rejections): lag ± 10 ms, RMS ≤ 0.05 rad/s and ≤ 0.3 m/s²,
    correlation ≥ 0.95 on excited axes. With no gyro axis above 0.1 rad/s there, A5 is NOT TESTED, so NOT accepted;
  - A6 rest specific force 9.80665 ± 0.15 (or NOT TESTED);
  - A7 OF == ROFH, exact;
  - A8 geometry PARM == ROFH/RRNI;
  - A9 range vs RFND: median ≤ 2 cm, p95 ≤ 5 cm;
  - A10 flow sign and correlation ≥ 0.5 from `sensor_timing_from_log` on a wiggle (required).
- **Accepted** = all pass, with A6 allowed to be NOT TESTED.
  - A2 covers the whole log: a log with a drop cannot accept, and another verification log is used.
- **SITL `cl_a_tex_half`** (`eval/results/r1_converter/accept_sitl_cl_a_tex_half_2026-10-12.json`):
  - A1–A4 and A6–A10 pass;
  - A5 is NOT TESTED, by design: SITL has no disarmed wiggle;
  - the replica on the whole log, as a diagnostic: RMS 0.2–0.4 mrad/s, lag −1 ms;
  - A9 exact.
  - So the first real acceptance log must contain a wiggle (B rotations, H or V).
- **Synthetic tests:** an axis flip, a ROFH mismatch, no flow-sign evidence, a wrong loop rate and a 10 cm range error
  are all rejected.
- **bin2fgo gained two check keys** (`imu_dvdt_ne_dadt_gt_0p5ms`, `imu_frame_period_ms_mean`); the npz is unchanged.
- The SITL FGO-from-BIN vs FGO-from-bag band (plan R-f) is still open.

## E. The 25 Hz IMU path (`eval/mocap_align.py`)

- **`--gyro-src auto`:** RISI if present, else the ~25 Hz IMU records. The reason is recorded; `gyro_period_ms_median`
  is recorded; the scorer reports which gyro fitted the map.
- **Re-validated on the sync-wiggle windows.** The 2026-10-10 failure (−431 ms) was on SITL's arm-anchored windows with
  no wiggle.
  - Synthetic (8 seeds; truth through the INS 2-pole 20 Hz filter, sampled at 25 Hz): mapped-time error mean +0.27…+0.62
    ms, |max| 0.96 ms, against |max| 0.26 ms for RISI.
  - **ACCURACY COST:** ~+0.5 ms of bias from the DC group-delay model, plus up to +2.5 ms from the IMU record's logging
    time (one 400 Hz loop, not modelled), plus a small notch lag. In all: a bias ≤ ~3.5 ms (≤ 1.8 mm at 0.5 m/s).
  - Tests: `test_imu_25hz_path_recovers_map_on_sync_wiggles`, `test_gyro_src_auto_falls_back_to_imu`.
- **Stated in the prereg (§8):** a log without RISI cannot be replayed or converted, so only `EKF3_onboard` is
  scorable.

## F. Parameter-name edits (pinned firmware `7bac20cbcc`, verified in `~/ardupilot`)

- **The names in that source:**
  - `AP_Arming.cpp:195-201`: `SKIPCHK`; `:324-327`: `check_enabled` = `(checks_to_skip & bit) == 0`, i.e. a SKIP mask,
    so behavioural sentences were inverted, not just renamed;
  - `AP_RangeFinder_Params.cpp:141-148`: `GNDCLR`.
- **Every edit:**
  - `docs/minimal_real_flight_plan.md`:
    - :47 `GNDCLEAR` → `GNDCLR`;
    - :142 `GNDCLEAR` → `GNDCLR`;
    - :282 `RNGFND1_GNDCLEAR` → `RNGFND1_GNDCLR`.
  - `docs/ukf_only_closed_loop_costing.md`:
    - :68 `RNGFNDn_GNDCLEAR` → `RNGFNDn_GNDCLR`, plus a bracketed correction: NOT "as EKF3 does" (the U4 finding);
    - :216 `ARMING_CHECK` default → `ARMING_SKIPCHK` default (0: no check skipped);
    - :295 `RNGFND1_GNDCLEAR` → `RNGFND1_GNDCLR`;
    - :344 `GNDCLEAR` → `GNDCLR`.
  - `docs/real_flight_readiness.md`:
    - :85 `GNDCLEAR` → `GNDCLR`.
  - `gnss_denied.parm`:
    - :29 (comment) "runs whenever the GPS bit is set in ARMING_CHECK" → "runs unless the GPS bit is set in
      ARMING_SKIPCHK (the 4.7 rename, now a skip mask)".
  - `gnss_denied_nomag.parm`:
    - :35–36 (comment) `ARMING_CHECK` → `ARMING_SKIPCHK`, with the old name noted.
  - `CLAUDE.md` (current instructions only; history gets a bracketed note):
    - :834–836 (a statement of current firmware behaviour) → "runs unless the GPS bit … is set in `ARMING_SKIPCHK`
      (at 7bac20cbcc; the 4.7 rename of `ARMING_CHECK`, a skip mask)";
    - :840 (HISTORICAL "ARMING_CHECK was not modified on the old machine") → bracketed note only: "(now
      `ARMING_SKIPCHK` at 7bac20cbcc)";
    - :853 (current behaviour) "not gated behind `ARMING_CHECK`" → "`ARMING_SKIPCHK` (the 4.7 name of
      `ARMING_CHECK`)".
  - `eval/lidar_short_returns.py`:
    - :44 reads `RNGFND1_GNDCLR` (it read the non-existent `RNGFND1_GNDCLEAR`, hence the `null`s). The stored
      `eval/results/lidar_short_returns.json` is NOT regenerated; it keeps the old key with `null`.
  - `eval/bin2fgo.py`:
    - docstring :53, :56 and the init-source string `GNDCLEAR` → `GNDCLR`.
- **Left alone on purpose:**
  - METHODOLOGY;
  - the handovers;
  - `docs/thesis/export_*`;
  - `eval/results`;
  - `PROGRESS.md` :715/:717 (a historical log);
  - `realflight/params/check_parm.py` (it uses the stale names deliberately, in its refusal tests);
  - `tags_extnav.parm` and `watcher_fc.parm` (they already describe the rename).
- **Remaining stale names outside the two in this task** (plan R-i): CLAUDE.md `FLOW_MAX` → `EK3_FLOW_MAX` and
  `FLOW_M_NSE` → `EK3_FLOW_M_NSE` (the UKF Design robustness table and text). NOT edited.

## G. Factual correction from the coordinator (U4; fwd-camera `9077acf`)

- **Prereg §9 item 11 is corrected and marked as a FACTUAL CORRECTION, not a change to any metric or criterion:**
  - at `7bac20cbcc`, EKF3 pushes no range sample for `OutOfRangeLow` and falls back to baro;
  - the UKF port uses a PORT rule (branch `u4-gndclr` `53bac01636`, NOT merged): while disarmed and `OutOfRangeLow`,
    `max(GNDCLR, 0.05)` as the initialisation and a range sample until arming.
- The same premise is also corrected in the costing U4 row (F).
- **Plan R-e in `docs/realflight_plan_copter.md` still says "as EKF3 does".** That file changed on `fwd-camera` after
  this branch's base, so it is NOT edited here, to avoid a merge conflict. To fix at merge.

## State at stop
- **Commits on the branch:**
  - `d692127` (scorer, reader, secondary metrics, final JSON);
  - `b7a7003` (converter delays and acceptance band);
  - `62e9127` (25 Hz IMU path);
  - `306cd20` (prereg doc, port spec, XUKO check, parameter names, this handover);
  - the last commit, after review: `eval/replay_gate.py` (the §5 gate via df_reader), A5 restricted to the disarmed
    spans with an excitation requirement, the H3 information check, and the doc updates.
- **Tests:** `real_score_test` 15, `mocap_align_test` 6, `bin2fgo_test` 3; all pass (`~/venv-ardupilot`).
- No locks held. The scratch outputs are in the session scratchpad `s12/`, not in the repo.

## Follow-ups
1. **USER RULING:** the XUKO source (port §S2a log, or §S2b CSV). The UKF row cannot be scored without it.
2. **The port agent:** implement §S1 (capture delay) and §S2 (FMT emission or `ukf_output.csv`), with their regressions.
3. **METHODOLOGY entry:** the final prereg commit and JSON sha256 `884ff351…`; the XUKO finding; the reader fix.
4. Fix plan R-e's "as EKF3 does" at merge; the CLAUDE.md `FLOW_MAX`/`FLOW_M_NSE` names.
5. Plan R-f (the FGO-from-BIN vs bag band) is still open. On the first real log, run `bin2fgo_accept.py`.
