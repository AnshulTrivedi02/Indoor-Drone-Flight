# UKF port specification for rung 1: the capture-delay option and XUKO in Replay (2026-10-12)

**Status: SPECIFICATION ONLY.** Written by the rung-1 scoring stage (handover
`docs/handovers/2026-10-12_r1_scoring_items.md`). The port agent implements it in `~/ardupilot_ukf`
(`libraries/AP_NavUKF/AP_NavUKF.cpp`). Nothing here has been built or run.

It implements:
- METHODOLOGY "RULINGS (user, 2026-10-10): … real-log flow timestamps": the UKF and the FGO use the best estimate of
  the TRUE capture time, from the measured sensor rate and delay;
- the signed-off rung-1 pre-registration (`docs/rung1_preregistration.md` §4.1, §6): the UKF record is `XUKO`.

## S1. Capture-delay option (flow and range), Replay only

### Today (the default, to stay byte-identical)
The port stamps each event as follows (`AP_NavUKF.cpp`, the event-queue block in `update()`, at `16535f9a29`):
- **Flow:** `t = arrival − _flow_delay_ms − FLOW_DT_AVG_MS/2 − FILTER_STEP_MS/2`, clamped to `≥ arrival − _horizon_ms`.
  This is EKF3's own rule: 10 + 50 + 6 = 66 ms at the defaults, with `_flow_delay_ms` from the log's `EK3_FLOW_DELAY`.
- **Range:** sampled at 30 Hz while the status is Good, and stamped at the DAL time `now`, with no delay subtracted.

### New
- **Environment options, read once in Replay** (like the existing `UKF_EXTYAW` / `UKF_DEROT_ROFH`):
  - `UKF_FLOW_DCAP_MS=<d>`: the flow event time is `t = arrival − d`, clamped to the horizon exactly as now.
    All three of today's terms are replaced: `EK3_FLOW_DELAY`, the half nominal interval and the half filter step.
  - `UKF_RNG_DCAP_MS=<d>`: the range event time is `t = now − d`, clamped to the horizon.
  - Values are integer milliseconds and must be ≥ 0.
- **Unset (the default):** every line runs as today. Outputs must be byte-identical.
- **The definition of d is the converter's** (`eval/bin2fgo.py`; `docs/rung1_preregistration.md` §6):
  - **Flow:** arrival minus the END of the flow sensor's integration interval. This is the same instant the FGO stamps
    the flow at, so the UKF and the FGO fuse flow at the same time.
  - Do NOT subtract half an interval in the port. EKF3's `− flowTimeDeltaAvg_ms/2` (a fixed 50 ms) is EKF3's own
    rule; it is kept for EKF3 and stated as a difference (prereg §9 limit 8).
  - **Range:** emission minus measurement.
  - Both values come from the PRE-REGISTERED delays file (`docs/rung1_capture_delays_TEMPLATE.json` → the filled
    file), the same file the converter reads with `--delays-json`.
- **The derotation window is unchanged.** The port uses the gyro the flow driver averaged over the sensor's own
  interval, with the D18 bias swap. That average belongs to the sensor interval whatever the stamp, so it does not
  move with d. The FGO averages its own RISI gyro over (previous flow, this flow], both ends shifted by d. On a real
  sensor the two intervals agree to the driver's message timing; state this, do not change it.
- **Log it:**
  - `ukf_geometry.csv` gains `flow_time_rule,<ekf3|dcap>,<d or ->` and `range_time_rule,<arrival|dcap>,<d or ->`;
  - one GCS text at start, and a count of flow/range events clamped to the horizon (a d larger than the horizon is
    clamped, as EKF3 clamps);
  - `ukf_inputs.csv` keeps its format (the event time column already exists for flow; confirm, else add none).
- **Onboard:** not needed for rung 1 (stock firmware flies). A parameter for the closed loop is a separate decision.

### Regression (before scoring; one light `heavy.py` step per Replay, on the five SITL logs of the 2026-10-11 handover)
1. **Unset:** `ukf_shadow.csv`, `ukf_inputs.csv`, `ukf_derot.csv` and `ukf_geometry.csv` byte-identical to the
   installed Replay (`be7c4d18`). `ukf_geometry.csv` may differ only by the new lines; then compare it with those lines
   removed.
2. **`UKF_FLOW_DCAP_MS=66`** (= 10 + 50 + 6, the EKF3 rule at the logs' defaults): `ukf_shadow.csv` byte-identical to
   (1). This proves the substitution is exact.
3. **`UKF_FLOW_DCAP_MS=16`:** only the state columns differ, the counts of accepted flows may differ, and the TimeUS
   column is unchanged. Report the size of the change, as a diagnostic.
4. **`UKF_RNG_DCAP_MS=0`:** byte-identical to (1).

## S2. XUKO in Replay

### Finding
The finding (handover §C; `eval/results/r1_scorer/xuko_replay_check_2026-10-12.json`) concerns Replay of a log that
does not declare the UKF messages, which is every stock-flown rung-1 log:
- the fork's Replay writes `XUKF`, `XUKO`, `XUKS` and `XUKH` with NO FMT record (per-run dynamic type ids);
- `XUKO` cannot be decoded, and pymavlink cannot read the output log at all;
- this was checked on the installed `be7c4d18` and on older builds.

In a Replay of a FORK-flown log, the onboard and the replayed `XUKO` are interleaved under one FMT and cannot be told
apart.

### Required (either one; S2a preferred)
- **S2a. Emit the FMT records in Replay.** Before its first `WriteStreaming("XU…")` in Replay, the UKF makes sure the
  output log carries a correct FMT (and FMTU, if used) for each message.
  - One way: declare the messages as static `LogStructure` entries in the fork, with fixed ids, instead of
    dynamically named streaming messages.
  - Acceptance:
    - `eval/df_reader.py` on a Replay output of `cl_a_tex_half` reports `XUKO` with ≥ 1 record per 40 ms;
    - 0 undeclared types and 0 skipped bytes;
    - pymavlink reads the log end to end.
  - **For a fork-flown input** (the U10 gate), the replayed records must be distinguishable from the copied onboard
    ones. Use different message names, or a core/instance field (e.g. `C = 100`, as EKF3 does). Otherwise the scorer
    refuses (`real_score.bin_trajs`: non-increasing TimeUS).
- **S2b. A current-time CSV.** In Replay, write `ukf_output.csv` with EXACTLY `XUKO`'s columns and values, at the same
  instant and rate as `XUKO`: `TimeUS,PN,PE,PD,VN,VE,VD,Roll,Pitch,Yaw,OV,EvO,EvMx,GpT,GpN`.
  - TimeUS is the same `AP_HAL::micros64()` stamp as `XUKO` (the current time, NOT the horizon).
  - Same units: NED metres and m/s, degrees, Yaw wrapped to [0, 360).
  - `real_score.py --est-csv UKF=ukf_output.csv` reads it, checking the header exactly.
  - `ukf_shadow.csv` is NOT a substitute: it holds the HORIZON state, stamped at the horizon, which is `XUKF`.
  - Acceptance:
    - on a SITL type-12 log (where the flying port logs `XUKO`), the CSV equals the onboard `XUKO` in count and
      TimeUS, and in values to float printing;
    - the default outputs are otherwise byte-identical.
- **Which source the scorer uses (the log via S2a, or the CSV via S2b) is a USER RULING**, recorded before scoring. The
  pre-registration names the record (`XUKO`), not its file.
