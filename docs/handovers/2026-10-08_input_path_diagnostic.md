# Brief: input-path diagnostic (user ruling 2026-10-08) — ONE stage, report only

## Question
Does the input path explain part of the estimator gap? EKF3 runs **inside ArduPilot** on the FC's IMU and flow
handling. The offline UKF/FGO run on the **recorded bag inputs**:
- `/imu/data_raw`: the `HIGHRES_IMU` bridge, 333 Hz instantaneous filtered samples, dejittered (CLAUDE.md "IMU Bridge");
- `/optical_flow/measurement`: our tracker.

Evidence prompting this:
- On `H_s1_r1`, the UKF **port** replayed on ArduPilot's own inputs (Replay) drifted 7–19 mm in tag losses.
- The **offline** UKF on the bag inputs drifted 28–292 mm (METHODOLOGY "H S2/S3 backends ... Finding").

## Tasks
1. **Document**, with file:line citations at `~/ardupilot` 7bac20cbcc / `~/ardupilot_ukf` `ukf-port-tag`, what EKF3 and
   the UKF port receive: IMU rate, delta-angle/delta-velocity integration and coning, filtering (`INS_GYRO_FILTER` /
   `INS_ACCEL_FILTER` 20 Hz; what `get_delta_angle` sees vs `get_gyro`), timing, and the flow path
   (`AP_OpticalFlow_MAV` → EKF3: body-rate compensation with the FC's own gyro, timing).
   Set this against what the bags give the offline estimators. **Quantify the differences**, where possible from the
   logs.
2. **Run the offline UKF** (`src/estimators/room_ukf_replay.py` for `H_s1_r1`, with `ROOM_TAG_SIGMA_POS=0.02`;
   `src/estimators/ukf_replay.py` for `dsn_tex_r2`, standard config) on:
   - **(a)** the bridged bag inputs, unchanged;
   - **(b)** ArduPilot-derived inputs from the dataflash/Replay log: the IMU from the log's Replay records (`LOG_REPLAY`
     data: e.g. RISH/RISI or IMU/IMT records, the delta-angle/delta-velocity the EKF consumed), and the flow as
     ArduPilot logged it (`OF`) if feasible.

   Check first whether `dsn_tex_r2`'s log has Replay records (`LOG_REPLAY` may have been 0 for that dataset). If not,
   say so and use the best available (e.g. the `IMU` records) or another `dsn`-equivalent bag with Replay data, and
   state the substitution.

   Add **(b)** as an **OFF-by-default input option**, producing outputs in a SEPARATE output directory (e.g.
   `room_ukf_apin/`, `ukf_apin/`). The default code path must stay byte-identical: prove it with a regression on one
   bag. **Never overwrite the existing thesis outputs.**
3. **Report:**
   - tag-loss drift (`H_s1_r1`, the S1 loss windows; `eval/h_score.py` effective metrics) for (a) against (b);
   - cruise error (`dsn_tex_r2`, the standing evo -a (cruise) metric via `eval/three_way_eval.py --est`) for (a)
     against (b);
   - whether, and roughly by how much, the input path could account for part of the main EKF3-vs-FGO and EKF3-vs-UKF
     results. Give an estimated size; say what would be needed to confirm it.
   - **Report only. Do not change any thesis number, result file or figure.**

## Rules
- **No simulator use** (the main session flies H flights during this stage).
- **Every heavy run:** `src/estimators/fgo_cpp/tools/heavy.py` (atomic `BUILD_LOCK` with your PID, waits on
  `FLIGHT_LOCK`/other locks/sims, removes only its own). Never touch `FLIGHT_LOCK`.
- **Packed bags:** many trial bags are zstd-packed (`bag/bag_0.db3.zst`). Decompress a COPY in scratch; never in place.
  `H_s1_*` is not packed.
- **State the comparison you will make** (metrics, windows) in your report doc and commit it before running (b).
- Commit only on your worktree branch, never while `pgrep -f '[a]rducopter'` matches.
- **End:** write `docs/handovers/2026-10-08_input_path_diagnostic_result.md` (findings, numbers, open questions, exact
  commands), commit it, report back in under 300 words, and stop.
