# Result: input-path diagnostic (brief `2026-10-08_input_path_diagnostic.md`) — REPORT ONLY

No thesis number, result file or figure is changed by this stage. All new outputs are in new directories.

## 0. Comparison stated BEFORE running (b) (committed before any (b) run)

**Variants of the offline UKF** (same code, same noise form, same 15.0 ms predict step, same range, tags, gap rule and
D15 rule; only the inputs named change; env `UKF_APIN`, OFF by default):

| label | IMU (predict + flow-derotation average + take-off detector) | flow (values, time, derotation gyro) |
|---|---|---|
| (a) | bag `/imu/data_raw` (HIGHRES_IMU, 20 Hz-filtered instantaneous samples, OI-2 dejittered) | bag `/optical_flow/measurement` at capture stamp, frame-averaged bag gyro |
| (b) `UKF_APIN=both` | FC INS deltas (`RISI` instance 0, per FC frame, DADT), on the FC clock | `ROFH` values, at EKF3's / the UKF port's time (arrival − 60 ms), EKF3's `bodyRate` gyro |
| (b-imu) `UKF_APIN=imu` | as (b) | as (a) |
| (b-flow) `UKF_APIN=flow` | as (a) | as (b) |

(b-imu) and (b-flow) are a diagnostic decomposition (the "swap one input" method), reported alongside.

**Metrics.**
- `H_s1_r1` (`room_ukf_replay.py`, `ROOM_TAG_SIGMA_POS=0.02`): `eval/h_score.py H_s1_r1 --profile
  batches/expH/s1_profile.json --sigma 0.02`, per loss (hover 5 / 15 / 30 s, move ~7 s): the **effective drift**
  (|estimate − GT| just before the first returning fix) and the as-worded drift (at OCCLUDER OFF). Reference points:
  EKF3 (same flight) and the UKF port on Replay (tier B: 12 / 8 / 11 / 13 mm effective).
- `dsn_tex_r2` (`ukf_replay.py`, standard config): **evo -a (cruise)** via `eval/three_way_eval.py --est`, window
  pinned from the stored `ukf/ground_truth.tum` (unchanged), plus the replay's own along-track and yaw-drift lines.
- **Share of the gap closed** per loss: (a − b) / (a − port). ≥ 0.7 = the input path accounts for most of the
  offline-vs-port gap; 0.3–0.7 = part; < 0.3 = little.

**Regression (default path byte-identical):** the modified scripts with `UKF_APIN` unset, run into a scratch HOME,
must give output files byte-identical to the unmodified scripts (HEAD `b918455`) on `dsn_tex_r2` and `H_s1_r1`, and
are also compared with the stored thesis outputs.
