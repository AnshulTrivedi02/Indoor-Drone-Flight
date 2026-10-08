# Handover: FGO C++ live time_ref defect — found and fixed (offline), 2026-10-08

**From:** a short-lived stage agent (one stage). Branch `worktree-agent-adb43f10b108d4913`, based on `fwd-camera`
`ca71593`; not merged. No simulator was run. Nothing was installed into `~/opt/fgo_cpp`.
**For:** the main session (review, install, then one live SITL shadow check).

## Mechanism (with numbers)

**The IMU clock offset was seeded from the first, UNSETTLED time_ref samples.** `LiveAdapter::imu_time_ref_paired`
set `off_used_` from `envelope_offset(require_settle = false)` at the first paired IMU sample. Afterwards it moved
only by the slew limit, 50 µs per sample (16.7 ms/s at 333 Hz).

- At node start-up the imu_bridge's first messages carry a large header − sensor offset (a receipt backlog). The
  live node started before the recorder, so it saw them; the bag starts after them (first bag time_ref at
  th 8.315 s, offset 1.8 ms). **The size of the initial excess is inferred from the fingerprint below, not observed.**
- The envelope itself recovers within seconds, but `off_used_` then closes the error at exactly the slew rate.
- IMU stamps (ts + off_used_) were therefore up to ~0.45–0.55 s in the FUTURE relative to every other input for
  the first ~30 s. Keyframes were stamped ahead of the FC clock: XFGO.Age wrapped and the FC flagged the output
  invalid.

**Fingerprint, `fgo_cpp_shadow_ii` (0.10 s):**
- `/fgo/pose` stamp minus the recorder's sim time: −340 ms (median, t_k 7.5–17.5 s), −184 ms (17.5–27.5 s),
  −13 ms (27.5–37.5 s), then a steady +104…+108 ms (the reorder delay plus latency) for the rest of the flight.
  752 of 10154 poses were stamped ahead of sim time, all before t_k ≈ 37 s.
- FC side (`XFGI`: arrival TimeUS − Tv): −252 ms median at FC 15–20 s, −180, −98, −15, +74, then +104.6 ms from
  40 s on. The slope is −16 ms/s, the slew cap. All 713 wrapped `XFGO` ages lie before FC 32.9 s.
- The clock map used for `time_usec` was right throughout (node `t_k − t_us` equals the bag's lower envelope, 1–60 ms
  drift over the flight); the error was in the IMU stamps only.
- Reorder buffer: live max lateness 0.694 s and 2685 out-of-order releases; the same bag replayed: 0.033 s and 0.
  The future IMU stamps pushed the buffer's newest stamp ahead, so header-stamped flow/range/attitude arrived "late".

**`fgo_cpp_shadow_i` (0.20 s):** the same: −276 ms median at t_k 7.9–17.9 s, −102, +69, then +203…+206 ms; 592
wrapped ages, all before FC 28.4 s.

**δ_att is entirely this start-up window.** Refit with only t_k > 45 s:

| flight | δ_att whole flight, live | live, t_k > 45 s | same-bag replay (time_ref), whole / t_k > 45 s |
|---|---|---|---|
| (i) | 149.0 | **23.0** | 2.5 / 22.5 |
| (ii) | 140.5 | **23.5** | 1.0 / 22.0 |

Live and replay agree within 0.5–1.5 ms once the start-up window is excluded, so there is no second mechanism.
The whole-flight live δ_att is dominated by the take-off and climb, which fall inside the bad window
(halves: 200 ms (grid edge) and 23.5 ms).

**Why the replay never showed it:** the tape starts with the bag, after the transient, so its first time_ref offsets
are already 2–9 ms.

## The fix (`live_adapter.{h,cpp}`; time_ref mode only)

1. **Seed the IMU offset only from the SETTLED envelope.** This is the same D25 settle (10 s of time_ref, median
   ± 20 ms outlier band, lower envelope) that already gates the ODOMETRY `time_usec`. The 50 µs/sample slew is
   unchanged and applies only after the seed (it only has to track the ~0.02 % clock-rate drift).
2. **Hold, then flush.** Every input that arrives before the settle is held (the clock map itself is updated on
   arrival). At the settle the held block is pushed in FINAL-stamp order (IMU: sensor time + seeded offset; others:
   header stamp), with the reorder buffer's tie-break (stamp, rank, arrival). The deferred gap-rule checks sort just
   before their IMU sample. So the estimator still starts from the first IMU sample, as before.
3. **Keyframes produced during the flush are not sent** to the autopilot (they are up to 10 s old); they count in
   `n_unsettled`, as the pre-settle keyframes did before.
4. **FIFO pairing per header stamp** (`std::map<double, std::deque<…>>`). The old `std::map` overwrote a waiting
   sample when two IMU messages shared a receipt stamp (153 of 112 563 in shadow_ii; tape order hid it). Not the cause
   of the 140 ms; fixed because live arrival order is not guaranteed.
5. **Diagnostics** in `fgo_node_stats.json` (keys appended; the old keys are unchanged): `tref_settled`,
   `tref_seed_th`, `tref_seed_offset_s`, `n_held`, `tref_max_track_err_s` (max |envelope − applied offset| after
   the seed), `n_dup_stamp`. `fgo_cpp_live_replay` prints the same as a `[tref]` line (time_ref mode only).

Causal and header modes take none of the new branches (`holding()` is false; pairing is time_ref-only). The
Python node is untouched.

## Verification (offline; every replay through `heavy.py`)

Baseline = the unmodified `ca71593` sources, fixed = this commit; both built in my scratch build dirs.

**Header and causal modes: byte-identical outputs, baseline against fixed** — `kf.f64` and `mav.bin` identical,
`live.f64` identical in every column except the measured step time:

| row | tape | mode |
|---|---|---|
| L1 (band L) | dsn_tex_r1 dejittered | header, delay 0.20, arm param |
| L2 (band L) | fwdc_tex_r1 dejittered, heading | header, delay 0.20, arm param |
| — | dsn_tex_r1 raw / fwdc_tex_r1 raw (heading) | causal, 0.20 |
| — | shadow_ii raw | causal, 0.10, heartbeat |
| — | shadow_ii start-up reproduction (ramp) | causal, 0.10 |

Band L therefore still passes exactly as recorded in `docs/fgo_cpp_port.md` part 3.

**Live-timing reproduction** (`tools/make_startup_repro.py`, scored by `tools/score_startup_repro.py`). The
shadow_ii tape with a synthetic imu_bridge start-up backlog, calibrated to the fingerprint: initial excess 0.55 s.
- `ramp`: draining linearly over 1.5 s.
- `burst`: one receipt instant for 0.55 s of samples, all IMU before all time_ref (worst executor order, duplicate
  stamps).

| tape / mode | binary | keyframes ahead of receipt clock (max) | sent ahead of SITL clock (= wrapped Age) | out-of-order / max lateness | δ_att whole (halves) | δ_att t_k > 45 s |
|---|---|---|---|---|---|---|
| ramp, time_ref | baseline | **761 (424 ms)** | **476** | **2739 / 0.541 s** | **161.5** (200, 23.5) | 23.5 |
| burst, time_ref | baseline | **779 (445 ms)** | **493** | **2802 / 0.564 s** | **170.5** (200, 23.5) | 23.5 |
| ramp, time_ref | **fixed** | 0 | 0 | 0 / 0.033 s | **1.0** (−18.5, 22.5) | 22.5 |
| burst, time_ref | **fixed** | 0 | 0 | 0 / 0.033 s | **1.0** (−18.5, 22.5) | 22.5 |
| ramp, causal | both (identical) | 0 | 0 | 1129 / 0.138 s | −22.5 | 33.5 |

The baseline reproduces the live signature: the grid-edge first half, δ_att 160–170 ms, future stamps and
thousands of out-of-order releases. The fix removes all of it.

**time_ref replays of the real bags** (report rows, no band; the IMU time base changes by ≤ 2 ms at the tape start):

| tape | baseline δ_att / future / out-of-order | fixed | fixed `[tref]` |
|---|---|---|---|
| shadow_ii, 0.10 | 1.0 ms / 0 / 0 | 1.0 ms / 0 / 0 | seed 1.797 ms at th 18.32 s; max track err 2.0 ms; 1 dup stamp |
| shadow_i, 0.10 | 2.5 / 0 / 2 | 2.0 / 0 / 0 | seed 2.320 ms; max track err 2.0 ms |
| shadow_i, 0.20 | 2.5 / 0 / 0 | 2.0 / 0 / 0 | as above |
| dsn_tex_r1, 0.20 | — / — / 0 | — / — / 0 | seed 1.772 ms; max track err 3.0 ms |
| fwdc_tex_r1 heading, 0.20 | — / — / 0 | — / — / 0 | seed 1.772 ms; max track err 4.0 ms; 150 dup stamps |

- Position differences of the fixed against the baseline time_ref replay: |Δp| p99 6.7–59 mm, max 15–132 mm.
- Keyframe times shift ≤ 2 ms, with the same keyframe counts.
- This is the expected sensitivity of the FGO to a ≤ 2 ms IMU time-base change over the first 10 s. These rows had
  no band (part 3: "differ by construction").

## Binaries (NOT installed; the main session installs after review)

Built from this commit's sources in my scratch dir. md5: `fgo_cpp_node` `3256a931…`, `fgo_cpp_live_replay`
`a2f31661…`. To install, run it through `heavy.py`, from a script file. Use a clean PATH: with
`~/venv-ardupilot` first on PATH, cmake picks its python and ament's `templates_2_cmake.py` fails with "No module
named 'ament_package'".

```
#!/bin/bash   # e.g. /tmp/.../install_fgo_cpp.sh
export PATH=/usr/local/bin:/usr/bin:/bin; set +u; source /opt/ros/jazzy/setup.bash; set -u
cmake -S ~/thesis_ws/src/estimators/fgo_cpp -B <build> -DCMAKE_BUILD_TYPE=Release -DPython3_EXECUTABLE=/usr/bin/python3 \
  "-DCMAKE_PREFIX_PATH=/opt/ros/jazzy;$HOME/thesis_ws/install/optical_flow_interfaces" -DCMAKE_INSTALL_PREFIX=$HOME/opt/fgo_cpp
make -C <build> -j4 && make -C <build> install
```

## Still needed: one live SITL shadow check (main session)

As stage-5 flight (ii), with a new trial name, after merging this branch and installing:

```
cd ~/thesis_ws
env FGO_NODE=1 FGO_NODE_IMPL=cpp FGO_CPP_DELAY=0.10 FGO_CPP_IMU_STAMP=time_ref FGO_CPP_ARM_SOURCE=heartbeat \
  LOOPBACK_ONLY=1 GZ_IP=127.0.0.1 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST ARDUPILOT_TREE=$HOME/ardupilot_ukf \
  EXTRA_PARM_FILES=$HOME/thesis_ws/fgo_shadow.parm EXPECT_OVERRIDE=AHRS_FGO_ENABLE=1,SERIAL3_PROTOCOL=2 \
  ./run_trial.sh --world corridor_textured_half_fwdc --velocity 0.5 --altitude 2.0 --duration 300 --trial-name fgo_cpp_shadow_ii_fix
# then (through heavy.py):
python3 src/estimators/fgo_cpp/tools/heavy.py "score ii_fix" -- $HOME/venv-fgo/bin/python eval/fgo_cpp_sitl_check.py \
  score fgo_cpp_shadow_ii_fix --json eval/results/fgo_cpp_sitl_ii_fix.json --replay-pair $HOME/opt/fgo_cpp/bin
```

Suggested pass criteria (written here before that flight):
- check (a): `n_age_wrapped` = 0 and the `OV` = 0 share = 0 over W_a;
- `fgo_node_stats.json`: `tref_settled` true, `n_out_of_order` ≈ 0, `max_lateness_s` ≲ 0.1 s,
  `tref_max_track_err_s` < 0.020 s (if not, the start-up transient outlasted the median, see below);
- δ_att (live, whole flight) within about 10 ms of the same-bag time_ref replay. For context, also refit with
  t_k > 45 s.

## Open issues

- **The start-up transient itself is not observed.** It precedes the bag (the recorder starts after the node). Its
  cause — most likely the imu_bridge reading a UDP backlog with fresh receipt stamps — is inferred from the slope and
  size. The new stats fields will show the settled seed live. If the recorder were started before the node, the bag
  would show the transient directly.
- **The fix assumes the transient is shorter than about half the 10 s settle window**, so that the median excludes it.
  A longer one would seed wrongly. `tref_max_track_err_s` would then be large; that is the alarm.
- **The node publishes nothing for the first ~10 s** of the time_ref stream (it holds), then catches up in one burst.
  ODOMETRY was already withheld for those 10 s. A take-off within ~10 s of the IMU stream starting would still be
  estimated correctly after the flush, but not live during it.
- With `arm_source heartbeat`, an arming before the settle uses the newest header stamp seen at arrival, which is
  correct for held inputs too.
- The stage-5 RESULT entry in METHODOLOGY.md still reads "not yet traced". The mechanism above is for the main
  session to record there after review. I did not edit METHODOLOGY.md.
- Not merged; not installed.
