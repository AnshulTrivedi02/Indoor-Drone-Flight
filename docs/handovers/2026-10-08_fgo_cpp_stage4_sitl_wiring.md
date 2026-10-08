# Handover: FGO C++ port, stage 4 (SITL wiring + scoring script) — 2026-10-08

**From:** the main session (the previous port agent was stopped by user ruling "one stage per agent"; it held no lock
when stopped. Its running step was terminated with SIGTERM and its wrapper removed only its own `BUILD_LOCK`.)

## State
- **Merged into `fwd-camera` (verified):** the C++ FGO port parts 1–3 (`src/estimators/fgo_cpp/`, `docs/fgo_cpp_port.md`).
  - Part 1: baseline equivalence. Part 2: heading/tag/GNSS + native front end. Part 3: live ROS 2/MAVLink adapter.
  - Band L PASS on `dsn_tex_r1`, `fwdc_tex_r1`.
  - Build: GTSAM 4.2.1 at `~/opt/gtsam-4.2.1`. The C++ binaries' install path is in `docs/fgo_cpp_port.md`.
- **UNVERIFIED WIP, NOT merged:** branch `worktree-agent-ad8931075b742e8fd`, commit `b641287`.
  - `run_trial.sh` option `FGO_NODE_IMPL=cpp` (`FGO_CPP_DELAY`, `FGO_CPP_IMU_STAMP`, `FGO_CPP_ARM_SOURCE`);
  - node parameter wiring in `fgo_cpp_node.cpp`;
  - a draft `eval/fgo_cpp_sitl_check.py`.
  - **Review it and adopt or discard it as a whole.** Anything adopted is verified before use.

## Task (this stage only)
1. **Wiring:** `FGO_NODE_IMPL=cpp` in `run_trial.sh` runs the C++ node in place of `fgo_node.py` in the `FGO_NODE` path:
   - the same SERIAL3 port (udpclient 127.0.0.1:14558) and `ODOMETRY`;
   - SIGINT stop with stats;
   - the node's states recorded in the bag.

   Unset means unchanged behaviour (prove it: a dry check that the Python path is unchanged).
2. **Scoring script `eval/fgo_cpp_sitl_check.py`** for the user's two open checks:
   - **(a) State age at the FC:** from the dataflash `XFGI`/`XFGO` of `AP_NavFGO` (`~/ardupilot_ukf`
     `libraries/AP_NavUKF/AP_NavFGO.cpp`; the FG3b analysis in `eval/fgo_groundtest_check.py`). Give the median, p95,
     p99 and max, and the share of time the output is invalid, against the **250 ms staleness limit**, for the
     **0.20 s** late-message wait. **Rule (user):** if the age can exceed 250 ms, use the **0.10 s** option (matches the
     Python node) and record why.
   - **(b) IMU timing accuracy:** the node's live state against `/ground_truth/pose` (position and yaw error), for
     **FC-clock (time_ref)** stamping against the **Python node's timing (causal)**, on matched flights. Record which is
     more accurate.
3. **Pre-register the decision rules and bands** for (a) and (b) in `docs/fgo_cpp_port.md` and commit **before** any
   SITL data exists.
4. **Hand back:** the exact env/params for three shadow flights the MAIN SESSION will fly (EKF3 flies, the FGO in
   shadow, same world and profile):
   - (i) cpp, 0.20 s, time_ref;
   - (ii) cpp, 0.10 s, time_ref;
   - (iii) cpp, 0.10 s, causal.

   Suggest the shortest suitable world/profile (e.g. the half-speed `fwdc` shadow setup used for `fgo_shadow_half_*`).

## Rules
- **No simulator use at all by the agent** (no `run_trial.sh`, `closed_loop_run.sh`, SITL, `gz`). The main session flies.
- **Locks:**
  - every compile/run goes through `src/estimators/fgo_cpp/tools/heavy.py`: it waits on `FLIGHT_LOCK`, any
    `BUILD_LOCK` and running sims; creates `BUILD_LOCK` atomically (`O_EXCL`) with its PID; removes only its own;
  - never create, edit or delete `FLIGHT_LOCK`;
  - `tools/flight_lock.sh` is the flight side.
- **Pre-registered bands before any comparison;** report as measured; no loosening.
- Commits on your worktree branch only; no commit while anything flies (`pgrep -f '[a]rducopter'`).
- Trial bags may be zstd-packed (`bag_0.db3.zst`): decompress a COPY in scratch, never in place.
- **At the end, write a handover note** `docs/handovers/<date>_fgo_cpp_stage5_*.md` (state, what was verified, what is
  open, exact commands), commit it, and stop. One stage per agent.
