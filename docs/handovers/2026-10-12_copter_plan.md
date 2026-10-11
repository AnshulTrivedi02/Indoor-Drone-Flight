# Handover 2026-10-12: ONE Copter real-flight plan; readiness by rung updated; firmware build script

One stage agent. It implements METHODOLOGY "RULING (user, 2026-10-12): ArduCopter confirmed for the real vehicle (for
now)". No flight, no simulator. One firmware test build under `heavy.py` (two attempts, §3). Nothing flashed or installed.
METHODOLOGY.md, numbers.md and CLAUDE.md are NOT edited.

## State
- **thesis_ws:** worktree branch `worktree-agent-a47be912ce7f22813`, reset to `fwd-camera` `4220cc4` first (it had
  been created from the unrelated `main` root). Committed; NOT merged.
- **`~/ardupilot_ukf`:** untouched. `board-h743` is still `0156bfc34e`; the checked-out branch is still `ukf-jitter-fix`;
  the worktree list is back to its 2 entries (the script checks this itself).
- **Flight check before each heavy job and each commit:** no `FLIGHT_LOCK`, no `BUILD_LOCK` (other than the test
  build's own, under `heavy.py`), and no process named `arducopter` (`ps -eo comm`, exact match).
- **No locks held**; no leftover worktrees (every temporary worktree is in the scratchpad and was removed by the script).
- **New data outside git:** `~/thesis_data/fw_builds/` (the KakuteH7 build, and the attempt-1 log directory renamed
  `…_FAILED_nested_submodules`).

## 1. Files
- **`docs/realflight_plan_copter.md` (new):** the consolidated plan. It covers:
  - rung 1 and the UKF-only closed loop;
  - timelines from hardware arrival;
  - the no-hardware TODO with efforts and status;
  - what waits on the board, the sensors and mocap;
  - the DONE list;
  - the blocking matrix of the open rulings and defects;
  - the H743 target table;
  - the firmware test result.
  QuadPlane is dropped (`docs/quadplane_costing.md` is kept as reference).
- **`docs/real_flight_readiness_by_rung.md` (updated):**
  - Copter only;
  - a status column on every table;
  - "U" marks the rows the UKF-only loop needs;
  - QuadPlane mentions struck as dropped/reference;
  - §5's 23-Oct calendar marked SUPERSEDED;
  - rung 2 marked PARKED.
- **`tools/build_board_fw.sh` (new):** a one-command board build. Its use and checks are in plan §6.1.
- **`eval/results/board_fw_ready/` (new):**
  - the KakuteH7 `summary.json`, the waf size table, and the stack-usage output of the buggy sub-check (kept as
    evidence);
  - the stable `.apj` headers of 18 targets, with the script that fetches them (downloads go to a temp directory).

## 2. The plan's headline numbers (from hardware arrival, Day 0 = an already-flying H743 Copter + board name + mocap)
- **Rung 1:** 6 working days (+2 contingency), 3 mocap days.
- **UKF-only closed loop:** 14 working days (rung 1 first, then 8; +2–3 contingency), 7 mocap days in all.
- **If the vehicle is not already flying, add 3–6 d.**
- **No-hardware work left:** rung 1 about 3–4.25 d; the UKF-only loop about 6–9.5 d more (excluding the rulings).
- **New blocking item found while planning:** the U10 Replay-gate band must be pre-registered before any UKF Replay
  of a real log (before rung-1 day 3), or the gate is post hoc (plan U-d0, §5 item 17a).
- **All 18 target hwdefs exist on both `board-h743` and `7bac20cbcc`** (`git cat-file`).
- **The plan corrects the costing's SITL plan (U9).** `SIM_FLOW` is unusable with the Gazebo model (2c finding), so
  V1–V7 fly on the MAVLink camera-flow path, and as verification flights they are allowed now.

## 3. Firmware script test
- Dry runs (argument errors, an unknown board, an F4 board, an include-chain board, an H757 warning, the stock
  `--ref 7bac20cbcc --without`, `--extra-hwdef`, a real build refused without `heavy.py`): all as designed, with
  clean-up verified.
- **Real build, KakuteH7 with the backends** (not built before):
  - **Attempt 1** failed in seconds: the nested `pymavlink` submodule was missing (mavgen). Fixed.
  - **Attempt 2 BUILT:**
    - flash free **245,276 B** of 1,703,936 (PASS);
    - 0 warnings;
    - backends present;
    - identity `0156bfc3`;
    - `.apj` md5 `8677e30a…`.
  - **Its stack sub-check failed on a SCRIPT bug** (it kept waf's `-o<path>`). Fixed afterwards, but **not
    re-verified by a build**: the brief allowed one real build. The next real build is the fix's first test. The
    joined `-o<path>` form was confirmed in the stored 2a `compile_commands.json` (MatekH743), so the fix targets the
    real form.
- **Nothing flashed.**

## 4. Not done / for the next stage
1. **Rulings** (plan §5):
   - the pre-registration sign-off;
   - E5 post hoc;
   - the capture-delay option;
   - `XUKO` in Replay (check first: the Replay logger emits no FMT for UKF messages);
   - F6;
   - F2 (card line);
   - U4/GNDCLR;
   - the own-gyro FLOW_TYPEs;
   - multi-IMU;
   - the H10 guard;
   - B5/B8a;
   - compass / `ALLOW_ARM_NO_COMPASS`;
   - S6;
   - merging `rung1-geometry` / `board-h743`;
   - G6.
2. **The no-hardware TODO** (plan §3.2 R-a…R-i, §4.3 U-a…U-l), in that order of priority: blocking items first.
3. **The stale names** (plan R-i, an exhaustive token check against `pinned_param_names.txt`): CLAUDE.md
   `ARMING_CHECK` → `ARMING_SKIPCHK`, `FLOW_MAX` → `EK3_FLOW_MAX`, `FLOW_M_NSE` → `EK3_FLOW_M_NSE`;
   `minimal_real_flight_plan.md` and `ukf_only_closed_loop_costing.md` `RNGFND1_GNDCLEAR` → `RNGFND1_GNDCLR` (the
   costing also says `ARMING_CHECK`). Not edited here.
4. **The next real board build re-tests the stack sub-check.** The `--extra-hwdef` path is still unbuilt.
