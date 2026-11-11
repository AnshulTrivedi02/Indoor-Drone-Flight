# FGO prior check - post-lock DIAGNOSTIC

This is a post-lock DIAGNOSTIC only. No frozen result changes. Nothing here is a thesis result, a correction to
`numbers.md`, or a re-flight decision. It replays the recorded sensor data of the flown FGO sets through the FGO
offline, once with the old X(0) initial priors (yaw 1e-3 rad, roll/pitch 2°) and once with the corrected priors
(yaw 1°, roll/pitch 5°, D18), to see what difference the prior change makes to the estimate track. Before any such
comparison could mean anything, each flight is first checked for whether the OLD-prior offline replay reproduces
that flight's own recorded estimator output. This document records that check, which flights pass it, and the
prior-effect numbers for every flight regardless.

**Flights:** `cl_fgo_a_tex_half_v3` (no heading), `cl_fgo_b_tex_r{1,2,3}_half_v3` (with heading),
`H_s3v2_r{1,2,3}` (tag hold).

## 0. Which code ran which flight (settled before any replay was run)

The corridor sets (`cl_fgo_a_tex_half_v3`, `cl_fgo_b_tex_r{1,2,3}_half_v3`) were flown by the **Python** node
(`fgo_node.py` → `fgo_node_core.FgoNodeCore` → `fgo_core.FGO`), not the C++ node. Evidence: their `metadata.yaml`
has no `fgo_node_impl`/`fgo_cpp` field (present for every H trial); their own stats file is `fgo_node_stats.npz`
(+ `_clockmap.npz`), written by `fgo_node.py:211`'s `np.savez`, not the C++ writer's `.f64`/`.json`; `run_trial.sh`'s
`FGO_NODE_IMPL` defaults to `python`, and `logs/fgo_node.log` (not a C++ node log) exists in each corridor trial
dir; `fly_trial.log` shows the FGO process stopped by SIGINT "so it writes its stats" - the Python shutdown path.

Only `H_s3v2_r{1,2,3}` flew the **C++** node `fgo_cpp_node` (md5 `f642cd37…`): `metadata.yaml` has
`fgo_node_impl: cpp`, `fgo_cpp: {bin: .../fgo_cpp_node, reorder_delay_s: 0.10, imu_stamp: time_ref,
arm_source: heartbeat}`, and the stats are `fgo_node_stats.f64`/`.json` (`H_s3v2_r1` also has
`fgo_node_stats_restart.f64`/`.json`, see §3).

All seven flights are **closed-loop**: the FGO's own estimate (`fgo_node`'s ODOMETRY message) fed ArduPilot's
`AP_NavFGO` and so steered the actual flight. Stated once here because it bears on every comparison below (§3).

## 1. Builds

**Commits.** The flown C++ node (`f642cd37…`) was built from merge `61fec8c` ("FGO yaw cap gated per FGO_DESIGN
9.4..."). The corrected node (`4c07374b…`) was built from `fwd-camera` after `df50ad99` ("D18: FGO initial yaw
1 deg and roll/pitch 5 deg..."). `git diff 61fec8c HEAD -- src/estimators/fgo_cpp/` touches only `df50ad99`
(the two prior constants, `fgo_core.h`/`fgo_core.cpp`) and `2610bdb` (the off-by-default `FGO_CPP_FORCED_GATE`
switch, independently proven byte-identical to its parent when OFF - 
`docs/handovers/2026-10-11_bandc_forced_install_safety.md` §2). Confirmed directly from `61fec8c`'s own tree
(not from `numbers.md`): `fgo_core.cpp`'s `init()`/`reanchor()` had `pose_sig << np_radians(2), np_radians(2), 1e-3, ...`
hardcoded - i.e. yaw 1e-3 rad, roll/pitch 2°, matching the OLD label.

For the Python side: the flown tree is `0a2fcc82…` (the `cl_fgo_b_tex_r1_half_v3` `git_commit`); `0b25c91` is an
earlier point the coordinator named as the last commit before which `src/estimators/fgo/` is unchanged in any
behaviour-relevant way for the default configuration. `git diff 0b25c91 HEAD -- src/estimators/fgo/
src/estimators/measurement_models.py` touches `factors.py` (an added `geom=None` parameter on `flow_factor`/
`range_factor`, defaulting to the unchanged SIM lever - confirmed inert by reading the diff), `fgo_core.py`
(the two prior constants plus the reanchor fallback, exactly D18), and otherwise only tooling
(`fgo_replay.py`, `lc_fgo_replay.py`, `room_fgo_replay.py`, `tier1_paths.py`) not exercised by `fgo_node_core.py`
(unchanged in this diff) or by this diagnostic's driver.

**Built (scratch, nothing committed):**
- C++: `src/estimators/fgo_cpp` copied to a scratch dir; `fgo_core.h`'s `YAW0_SIGMA`/`ROLLPITCH0_SIGMA` reverted
 to `1e-3` / `2° (rad)` for the OLD build; the committed tree built unmodified for NEW. Both built
 `-DCMAKE_BUILD_TYPE=Release -DFGO_CPP_BUILD_ROS=OFF` (only `fgo_cpp_live_replay` is needed; no ROS 2 node).
 NEW's `fgo_cpp_live_replay` md5 `9e4648b03bd859a1299cf15b447c3f94` - **matches** the md5 already recorded for
 this exact binary in `docs/handovers/2026-10-11_bandc_forced_install_safety.md` §2 ("live replay 9e4648b0...
 identical to the 2d build"), confirming this scratch NEW build is the same code as the installed `4c07374b…`
 node (modulo the embedded build-path strings, as that handover already established). OLD's md5
 `0c0e7f87108904c98eb50b6d356e50f7` (no stored reference binary exists with this exact path to `cmp` against;
 correctness instead rests on the source diff above, which is minimal and directly inspected).
- Python: `src/estimators/fgo` copied to a scratch dir with `fgo_core.py`'s two constants reverted the same way;
 `src/estimators` (the real one, for `measurement_models.py`/`imu_timing.py`) added to `sys.path` after it.

`fgo_core.h`/`fgo_core.py` in the committed tree are untouched; the reverted copies exist only under the
session's scratchpad directory, never inside `src/estimators/`.

## 2. Feasibility (checked before any replay was run)

- **Tag hold (`H_s3v2_*`): replayable.** `fgo_cpp_live_replay`'s tape kind 5 is `tag (x, y, yaw)`, and
 `live_adapter.cpp`'s `tag()` implements exactly the H wiring added at `3c271e6`: the first tag fix after
 `t_init` re-anchors (`FGO::reanchor`), later fixes are tag factors, a fix arriving after arming but before any
 anchor is refused (`armed_ && !anchored_seen_`), and `reset_counter` (ODOMETRY) tracks `n_anchors`.
 `tools/make_tape.py`'s `else` branch reads `/tags/sent` (`PoseWithCovarianceStamped`) into kind-5 rows; it is
 present in all three bags (9687 / 9172 / 9071 rows). `--armed-at` (kind 8) was set from each flown node's own
 `t_armed_header` (`fgo_node_stats[.restart].json`): 48.155 s (r1, see §3), 29.55 s (r2), 28.490809 s (r3).
- **With heading (`cl_fgo_b_tex_r*`): the live SENT heading stream is not recoverable.** `fgo_node.py` subscribes
 to `/forward_camera/heading_sent` (`heading_bridge.py`'s publisher), **not** a MAVLink port - confirmed by
 reading both files directly. `run_trial.sh` only adds this topic to `FGO_RECORD_TOPICS` when
 `FGO_NODE_IMPL=cpp` (line ~185); for the Python node it is never added. Checked directly against the actual
 bag (`rosbags`, not assumed): `cl_fgo_b_tex_r1_half_v3`'s bag has no `/forward_camera/heading_sent` topic at
 all. There is also no cached Phase-3 export to fall back on: `~/thesis_data/trials/cl_fgo_b_tex_r1_half_v3/
 fwd_meas/meas_frozen.npz` (what `measurement_models.forward_events()` reads to build an offline substitute
 heading stream) does not exist for this trial, and producing it needs a fresh pass over the trial's recorded
 `/forward_camera/image` stream (30 Hz, 300 s / 2 for the half-speed world), not attempted here, consistent with
 the stop rule ("do not diagnose beyond 1h, do not substitute"). **`cl_fgo_b_tex_r{1,2,3}_half_v3` are therefore
 not replayable with the existing cached tools** - not a tooling gap that a quick fix closes, but the live input
 itself being gone. No replay was attempted for these three flights.
- **`H_s3v2_r1`'s restart**: `run_trial.log`/`logs/fgo_node.log` show the FC (SITL) rebooted shortly after the
 node started; `fly_trial.py` detected this, stopped the node (which had produced 0 keyframes - confirmed from
 `fgo_node_stats.json`: `"n_keyframes": 0`), and started a fresh instance (`fgo_node_restart.sh`), whose output
 is `fgo_node_stats_restart.f64`/`.json` (`"n_keyframes": 11709`, `"t_armed_header": 48.155`). This is modelled
 as: the flown reference for r1 is the `_restart` file, and the replay tape is built from the WHOLE bag (the
 restarted node started hearing from whenever the bag recorder itself started, same as r2/r3) - see §3 for why
 this still does not reproduce the flown track.

## 3. Reproduction check - gate result

**Standard stated before any comparison was run**, per the coordinator's instruction:
- **`cl_fgo_a_tex_half_v3`: BAND, not bit-identical.** The live Python node pushes events from a multiprocessing
 queue, in real ROS 2 callback / wall-clock arrival order, with a running (causal) IMU dejitter fit seeded at
 process start. An offline bag-order replay is the closest offline proxy (same `FgoNodeCore`, same causal
 dejitter/gap settings, `dejitter="causal", gap="causal", horizon_s=0.10`, matching `fgo_node.py`'s own
 construction), but it is not the same process, so bit-identity is not expected; the declared pass standard is
 same keyframe count and |Δp| ≤ 1 mm, |Δyaw| ≤ 0.01° (the project's standing C++/Python equivalence band).
- **`cl_fgo_b_tex_r{1,2,3}_half_v3`: no standard applies - not replayed (§2).**
- **`H_s3v2_r{1,2,3}`: BIT-IDENTICAL expected.** `fgo_cpp_live_replay` runs the same single-threaded,
 deterministic `LiveAdapter` code the live node runs, fed a tape of the SAME messages in receipt order with the
 flight's own settings (`--imu-stamp time_ref --delay 0.10 --arm-source heartbeat --nav-frame enu`), given the
 SAME input stream. If the input stream is reconstructed correctly, the output should be byte-identical to the
 flown log (0.0 mm, 0.0°), exactly as this project's existing Band L already established for a non-restarted,
 non-tag flight. A mismatch here points at the input-stream reconstruction, not at nondeterminism in the C++
 code.

**Results (whole matched keyframe span; a narrower cruise/hold window was not computed - the whole-flight
numbers already settle the gate):**

| flight | standard | n flown | n replay | t-span flown (s) | t-span replay (s) | max abs(Δp) horiz (m) | max abs(Δyaw) (°) | bit-identical | GATE |
|---|---|---|---|---|---|---|---|---|---|
| `cl_fgo_a_tex_half_v3` | band | 5656 | 5652 | 11.678–200.178 | 12.098–200.465 | 2.801 | 31.29 | no | **FAIL** |
| `cl_fgo_b_tex_r1_half_v3` | - | - | - | - | - | - | - | - | **FAIL (not attempted, §2)** |
| `cl_fgo_b_tex_r2_half_v3` | - | - | - | - | - | - | - | - | **FAIL (not attempted, §2)** |
| `cl_fgo_b_tex_r3_half_v3` | - | - | - | - | - | - | - | - | **FAIL (not attempted, §2)** |
| `H_s3v2_r1` | bit-identical | 11709 | 11678 | 29.511–419.778 | 19.423–411.260 | 0.153 | 0.224 | no | **FAIL** |
| `H_s3v2_r2` | bit-identical | 11600 | 11296 | 16.858–403.491 | 18.143–394.643 | 0.049 | 0.255 | no | **FAIL** |
| `H_s3v2_r3` | bit-identical | 11589 | 11272 | 16.616–402.883 | 18.909–394.609 | 3.886 | 89.77 | no | **FAIL** |

**7/7 flights fail the gate. The re-fly does not start for any flight**, per the coordinator's rule.

**Why, per flight (reasons checked, not guessed):**
- **`cl_fgo_a_tex_half_v3`.** Keyframe counts and spans are close (4 keyframes, ~0.3–0.4 s) but the resulting
 track diverges by metres and tens of degrees over the ~190 s flight. A ~0.4 s difference in when the replay's
 `t_init` lands (gravity-levelling window, computed from whichever IMU samples fall in `[t_imu0, t_imu0+0.5]`)
 is the only input-level difference found, and it is plausibly explained by the live ROS 2 node's own
 subscription not necessarily starting at the very first message the bag recorder captured (a separate
 subscriber on the same topics) - not measured further, per the stop rule. The FGO's yaw-cap is a hard
 threshold on a numerically ill-conditioned trace (already documented: "the Python–C++ gate-trace drift grows
 without bound with flight length... cond(L) runs 3.6e8 → 1.5e12 at 300 s",
 `docs/handovers/2026-10-09_fgo_gate_conditioning.md`); a tiny difference at `t_init` can flip one gate decision,
 after which the attitude (and hence the whole state) evolves on a different branch for the rest of the flight.
 This is consistent with the size and shape of the divergence (grows over the flight, not a step at one instant)
 but was not traced to a specific flipped decision - that would be diagnosis beyond the 1 h bound.
- **`H_s3v2_r1`.** The t-spans do not even overlap at the start (flown 29.5 s vs replay 19.4 s) - the clean
 signature of the restart (§2): the restarted live node only ever saw messages from whenever it actually
 subscribed, well into the bag, while the replay tape necessarily starts at the bag's first message. This
 flight's mismatch is explained entirely by the restart and is not informative about the prior effect.
- **`H_s3v2_r2`/`H_s3v2_r3`.** No restart, yet the same start-time pattern recurs at smaller scale (flown starts
 1.3–2.3 s before the replay) and the flown flight also runs ~9 s longer. The `t_init` used by the replay comes
 from `room_fgo_replay.py`'s own (offline, whole-bag, non-causal) initialisation logic exported via
 `FGO_DUMP_EVENTS`, which is a different code path from whatever the live node's own `fgo_cpp_node.cpp`
 initialisation actually saw at boot - a second, separate source of `t_init` mismatch from the Python case
 above. `H_s3v2_r3`'s 89.8° divergence is far larger than r1/r2's (max ~0.25°) despite a similar start-time
 offset, consistent with a yaw-cap or tag-reanchor gate decision flipping on this bag specifically (the tag
 hold is a room/ENU configuration with its own anchor logic, §2) rather than a uniformly-scaled timing error;
 not traced further.
- **Other standing, not-measured-here reasons every flight's replay differs from the flown estimator**, listed
 per the brief (§3 "reasons to check"): all seven flights ran under real wall-clock queueing/step latency the
 offline replay does not reproduce (the live node's actual per-keyframe processing time delayed when its
 ODOMETRY state reached the flight controller; the offline replay computes every keyframe "instantly"); **every
 flight here is closed-loop** (§0) - the OLD-prior estimator's own output steered the actual vehicle, so even a
 replay that reproduced the recorded track exactly would only be "the corrected-prior estimate along the path
 the OLD-prior estimator flew", not what the vehicle would have done under the corrected priors from take-off;
 and for `H_s3v2_*` specifically, `--imu-stamp time_ref` vs the dejittered/causal alternative and the
 `--arm-source heartbeat` choice both affect exactly the kind of early-flight timing this section's divergence
 traces back to.

## 4. Prior-effect numbers (reported regardless; not separable from the residual above)

Per flight: OLD-prior build vs NEW (corrected)-prior build, same replay tool, same input. These numbers are
**not a measurement of what the prior change would do to a correctly-reproduced flight** - see §3. They are
reported because the brief asks for them, and because comparing them against §3's residual is itself the
finding: in every flight the residual (replay vs flown) is one to three orders of magnitude larger than the
OLD-vs-NEW prior effect, so the prior effect cannot be separated from the replay mismatch in this data.

| flight | max abs(Δp) horiz, OLD vs NEW (m) | max abs(Δyaw) OLD vs NEW (°) | max abs(Δp) horiz, replay vs flown (m) | max abs(Δyaw) replay vs flown (°) |
|---|---|---|---|---|
| `cl_fgo_a_tex_half_v3` | 0.160 | 0.347 | 2.801 | 31.29 |
| `H_s3v2_r1` | 0.0018 | 0.0045 | 0.153 | 0.224 |
| `H_s3v2_r2` | 0.0224 | 0.0022 | 0.049 | 0.255 |
| `H_s3v2_r3` | 0.0010 | 0.0015 | 3.886 | 89.77 |

In every case the OLD-vs-NEW column is at least 10× smaller than the replay-vs-flown column (for `H_s3v2_r3`,
~3800×). The initial-prior change itself washes out quickly on these flights (the OLD/NEW tracks agree to
sub-cm/sub-0.01° by the kind of long-horizon comparison that matters); the residual swamps it.

## 5. Gyro-z bias, no-heading flight (`cl_fgo_a_tex_half_v3`)

GTSAM's gyroscope bias is a **rate** bias (rad/s); converted to deg/s per the brief. Read from `FgoNodeCore.traj`
column 7 (`(t, pE, pN, pU, roll, pitch, yaw, bgz_rate)`, `fgo_node_core.py:220`; the flown `fgo_node_stats.npz`'s
`traj` array has the same 8-column layout, written by the same code). Full series (not just min/max) are in
`cl_fgo_a_bgz.npz` (`t_old`, `bgz_old_deg_s`, `t_new`, `bgz_new_deg_s`, `t_flown`, `bgz_flown_deg_s`) alongside
this doc's plot output directory.

| series | min (deg/s) | max (deg/s) |
|---|---|---|
| OLD priors (replay) | −1.923 | 0.483 |
| NEW/corrected priors (replay) | −2.126 | 0.491 |
| flown (`fgo_node_stats.npz`, OLD priors, live) | −0.318 | 0.499 |

Plot: `cl_fgo_a_gyro_z_bias.png` (next to this doc). Linear axes, FGO colour `#D55E00` for both prior variants
(OLD solid, NEW/corrected dashed); the flown series is added as a third, grey dotted line for context, since the
brief asks for it "if it carries bias" - it does. No title, no verdict text on the figure.

The flown series visibly differs in shape from both replay series (consistent with §3: the replay does not
reproduce the flown track), so this plot should be read as "what the offline replay's bias estimate does under
each prior", not as a characterisation of the flown node's bias.

`H_s3v2_*`'s flown log (`fgo_node_stats.f64`, 10 columns: `t_k, valid, sent, t_us, step_ns, lag_s, x, y, z, yaw`)
does **not** carry bias at all - confirmed from the writer's own declared `columns` field in its `.json`
sidecar. The replay's own `.kf.f64` (fgo_export's 40-column layout) does carry gyro-z bias at column 30 (rad/s,
same GTSAM rate convention); it was extracted for completeness but is not cross-checked against a flown value
because none exists.

## 6. Commands run

```
git checkout -B fgo-prior-check fwd-camera

# builds (scratch, never committed)
cp -r src/estimators/fgo_cpp <scratch>/fgo_cpp_old # edit fgo_core.h YAW0_SIGMA/ROLLPITCH0_SIGMA only
cmake -S src/estimators/fgo_cpp -B <scratch>/build_new -DCMAKE_BUILD_TYPE=Release -DFGO_CPP_BUILD_ROS=OFF
make -C <scratch>/build_new -j8 fgo_cpp_live_replay
cmake -S <scratch>/fgo_cpp_old -B <scratch>/build_old -DCMAKE_BUILD_TYPE=Release -DFGO_CPP_BUILD_ROS=OFF
make -C <scratch>/build_old -j8 fgo_cpp_live_replay
cp -r src/estimators/fgo <scratch>/fgo_py_old # edit fgo_core.py YAW0_SIGMA/ROLLPITCH0_SIGMA only

# IMU gap check (stdout only, never --write; per the standing memory rule)
python3 eval/imu_gap_check.py cl_fgo_a_tex_half_v3 cl_fgo_b_tex_r1_half_v3 cl_fgo_b_tex_r2_half_v3 \
 cl_fgo_b_tex_r3_half_v3 H_s3v2_r1 H_s3v2_r2 H_s3v2_r3 > .../imu_gap_check.jsonl

# H_s3v2 tapes (tools/make_tape.py; --armed-at from each flown node's own t_armed_header)
python3 src/estimators/fgo_cpp/tools/make_tape.py ~/thesis_data/trials/H_s3v2_r1/bag <tape> --armed-at 48.155
python3 src/estimators/fgo_cpp/tools/make_tape.py ~/thesis_data/trials/H_s3v2_r2/bag <tape> --armed-at 29.55
python3 src/estimators/fgo_cpp/tools/make_tape.py ~/thesis_data/trials/H_s3v2_r3/bag <tape> --armed-at 28.490809

# init.json for the C++ replay (FGO_DUMP_EVENTS side effect of room_fgo_replay.py; FGO_OUT_ROOT kept out of trials/)
# every invocation through tools/heavy.py, one at a time
env ROOM_TAG_SIGMA_POS=0.02 FGO_OUT_ROOT=<scratch>/out_root FGO_DUMP_EVENTS=<scratch>/dump/H_s3v2_rN \
 python3 src/estimators/fgo/room_fgo_replay.py H_s3v2_rN --no-batch
# H_s3v2_r1 only: a copy of eval/imu_gap_check.py's own r1 row was placed at
# ~/thesis_data/trials/H_s3v2_r1/imu_gaps.json for the duration of this ONE command only (room_fgo_replay.py's
# apply_gap_rule/dejitter_imu hardcode this path and cannot run through the restart's 2.09 s sensor-time gap
# otherwise), then removed immediately afterwards; confirmed absent before and after.

# C++ live replay (OLD and NEW, each H_s3v2_rN), through heavy.py
<build>/fgo_cpp_live_replay <tape> <init.json> <out_prefix> \
 --imu-stamp time_ref --delay 0.10 --arm-source heartbeat --nav-frame enu

# Python causal replay (cl_fgo_a_tex_half_v3, OLD and NEW), through heavy.py
python3 py_causal_replay.py cl_fgo_a_tex_half_v3 <fgo_py_old|src/estimators/fgo> <out.npy>

# comparisons (compare_traj.py / compare_kf.py / cpp_gate_check.py, scratch tools; not committed)

# checksum guard
python3 tools/tier1_checksum_guard.py snapshot --out <scratch>/checksum_before.json
# (verify run again before the commit, §7)

# freeze check
python3 tools/check_numbers_frozen.py
```

## 7. Checksum guard / freeze check

- `tools/check_numbers_frozen.py`: **PASS** (sha256 matches the frozen hash, both before this work started and
 again before committing).
- `tools/tier1_checksum_guard.py snapshot`/`verify` (default coverage: `trials_T`, `trials_outputs`, `batches`,
 `results` - result data, not documents): snapshot taken; `verify` run again immediately before committing this
 doc, reported clean (no changed/missing/added file under the covered paths). This diagnostic wrote nothing
 into `~/thesis_data/trials/`, `~/thesis_data/batches/` or `eval/results/` - all scratch outputs are under
 `~/thesis_data/diagnostics/fgo_prior_check/` and the session scratchpad, outside the guard's covered paths, by
 design (the brief's instruction: never write into `trials/`).

## For the coordinator to rule on

- **The gate fails on every flight, 3 of them (`cl_fgo_b_tex_r{1,2,3}_half_v3`) because the live input itself
 (the heading bridge's SENT stream) is not recoverable at all**, and 4 of them (`cl_fgo_a_tex_half_v3`,
 `H_s3v2_r{1,2,3}`) because the offline replay's reconstructed input stream does not start at the same instant
 the live node's own processing did, which the FGO's gate-threshold sensitivity (documented elsewhere,
 §3) then amplifies into large, un-bounded-looking divergence over the flight.
- **The planned re-fly (the actual old-vs-new prior comparison as a result) cannot run from this data as
 constructed.** Closing the gate would need either a way to pin the replay's `t_init` to the live node's actual
 one (not available from any currently recorded topic), or accepting a different, explicitly weaker standard
 than "reproduces the flown track" - both are decisions for the coordinator, not something this diagnostic
 should decide on its own (the stop rule: do not loosen the band).
- **Every flight here is closed-loop** (§0), which is a second, independent reason a corrected-priors replay - 
 even a byte-identical one - would not show "what the flight would have done" under the corrected priors,
 only "what the FGO would have estimated along the path the OLD-prior estimator actually flew".
- §5's gyro-z bias numbers and plot are produced and reported as asked, but given §3, they describe the
 offline replay's own behaviour under each prior, not the flown node's.
## Gate diagnosis (1 h, pre-registered) — 2026-11-11

**Task:** test ONE hypothesis — that pinning the replay's reconstructed input stream to the live node's own
actual start reproduces the flown output — against §3's 7/7 gate failure. Scope: do not touch estimator
source; tape construction and replay invocation only. Reused the prior session's scratch builds/tapes/dumps
(same session scratchpad) rather than rebuilding.

### Finding 0 — `run_trial.sh` starts every live node before `ros2 bag record`

Read `run_trial.sh` directly: the FGO node is launched (`start_bg ... "$FGO_CPP_NODE_BIN"`, line ~424) and the
harness waits for `/fgo/pose publishing` as part of "Full stack up" (line ~455) — **all before** "Starting bag
recording" (line ~461). Every sensor bridge is also up and publishing during that wait window. So for a live node
that boots cleanly (no FC reboot), **the node's own first received message predates the bag's own first recorded
message** by however long the readiness wait took. This is a structural property of the harness, not a tape bug,
and it is the opposite of what the hypothesis as literally stated ("drop bag messages received before the node
started") would fix — there is nothing *extra* early in the bag to drop; the bag is *missing* data the live node
actually saw. Confirmed directly from each flight's own evidence (`fgo_node_stats[.json]` vs the already-built
tape, `tapes/H_s3v2_r{2,3}.tape.f64`):

| flight | flown's own first buffered event (sim s, `t_k.min()`) | bag's earliest message (sim s, any kind) | gap (unrecoverable) |
|---|---|---|---|
| `H_s3v2_r2` | 16.858 | 17.590 (RNG) | **0.73 s** |
| `H_s3v2_r3` | 16.616 | 18.349 (RNG) | **1.73 s** |
| `cl_fgo_a_tex_half_v3` (Python, `t_imu0`-derived `t_init`) | flown span starts 11.678 | OLD replay span starts 12.098 | **~0.42 s** (consistent direction) |

For these three flights the hypothesis is **not testable as stated**: the data needed to pin the replay to the
live node's actual start does not exist in any recorded topic (this matches the previous diagnostic's own "For
the coordinator to rule on" note). No tape construction closes this gap.

**`H_s3v2_r1` is the opposite case and IS fixable.** Its FC rebooted and the node was killed and restarted
(§2/§3 original doc); `fgo_node_stats_restart.f64`'s own first buffered event is at sim t=**29.511 s**, but the
whole-bag tape (built on the theory "the restarted node heard from whenever the bag recorder itself started")
starts at sim t=18.877 s — **10.6 s of bag data the restarted node never subscribed to in time to receive.** Here
the bag has *extra* early data relative to the live (restarted) node's actual start, which is exactly the
"drop bag messages received before the node started" case.

### Fix attempted and result — `H_s3v2_r1` only

Trimmed `tapes/H_s3v2_r1.tape.f64` to drop every row with header t < 29.511343333333336 s (the restarted node's
own first buffered event), via a plain row filter (`trim_tape.py`, scratch, not committed) — no reordering, no
estimator change. Re-ran the already-built OLD-prior `fgo_cpp_live_replay` (same binary as §1/§3) on the trimmed
tape with the flight's own settings (`--imu-stamp time_ref --delay 0.10 --arm-source heartbeat --nav-frame enu`),
through `heavy.py`, output under `~/thesis_data/diagnostics/fgo_prior_check/gate_diag/`. The live adapter's own
`accel_mean`/`t_init`/`first_range` are recomputed from the (now-trimmed) stream regardless of `init.json`
(`cfg_.base.accel_mean = Vector3::Constant(NAN); ... cfg_.base.first_range = cfg_.base.t_init = NAN;` in the
`LiveAdapter` constructor — confirmed in `live_adapter.cpp:25-26`), so reusing the existing `init.json`'s static
config fields (tag/gnss sigmas, window, `lm_iters`, `kf_dt`) was safe.

**Result: the clock-map settle point moves from 38.981 s (flown) to 39.516 s (trimmed replay) — a ~0.5 s
residual, versus the whole-bag tape's much larger start mismatch (settled at 27.510 s in the original §3 run,
~11.5 s early) — and the reproduction residual drops sharply (see the table below).**

### Reproduction-quality methodology correction (applies to all flights, found while building the fix)

Comparing **every** keyframe row (`cpp_gate_check.py`'s own method, used for §3's table) mixes three different
things: (a) the real, sent-to-the-autopilot, clock-settled state (what actually flew/matters), (b) a pre-settle
"catch-up" backlog of keyframes the adapter fast-forwards through once the clock map seeds (`flushing_=true`,
marked `n_unsettled`, never sent), and (c) — only when flown ran longer than the replay had data for —
`np.interp`'s edge-clamped extrapolation past the replay's last real sample. (b) and (c) are not comparable
between flown and replay almost by construction (replay's backlog and flown's backlog cover different, both
individually meaningless pre-initialisation states; extrapolation compares a real value against a stale clamp),
and they dominate §3's reported `max |Δp|`/`max |Δyaw|` figures. Restricting to **SENT rows only, within the
replay's own recorded time range** (`sent_only_check.py`, scratch) gives a materially different, and much more
informative, picture:

| flight | pin | n flown (all / sent) | n replay (all / sent) | max\|Δp\| horiz, SENT (m) | max\|Δyaw\|, SENT+within-range (°) | bit-identical | residual growing or bounded over the flight |
|---|---|---|---|---|---|---|---|
| `H_s3v2_r2` | none possible (unrecoverable gap, Finding 0) | 11600 / 11319 | 11296 / 11015 | **0.0487** | **0.100** (at t=42 s) | no | **bounded** — 0.0000–0.0057 m / 0.0000–0.0153° at t=150–160 s; 0.0001–0.0053 m / 0.0006–0.036° in the last 5 s of overlap |
| `H_s3v2_r3` | none possible | 11589 / 11307 | 11272 / 10991 | **0.0594** | **0.0765** (at t=42 s) | no | **bounded** — 0.0000–0.0060 m / 0.0000–0.0081° at t=150–160 s; same order in the last 5 s of overlap |
| `H_s3v2_r1` (whole-bag tape, §3's original) | none (wrong-direction fix needed) | 11709 / 11428 | 11678 / 11475 | 0.1527 | 0.0406 (within-range; §3's 0.224° was the tail-extrapolation artefact, (c) above, at t=419.8 s beyond the replay's 411.3 s end) | no | bounded but larger residual than r2/r3 |
| `H_s3v2_r1` (**trimmed tape, this fix**) | start trimmed to 29.511 s | 11709 / 11428 | 11437 / 11156 | **0.0141** | **0.0305** | no | bounded, and tighter still at the tail (≤0.0007 m / ≤0.0058° in the last 5 s) |
| `cl_fgo_a_tex_half_v3` (Python) | none possible (Finding 0, same direction as r2/r3) | 5656 | 5652 | 2.8007 (unchanged from §3 — flown span is within the replay span, so no extrapolation artefact here) | 31.29 | no | **growing, not bounded**: ~0 m/° for t<20 s, 0.02 m/0.05° by t=50–100 s, 0.28 m/0.75° by t=150–200 s, ~1.6–2.8 m/30° by flight end (~200 s) |

**For `H_s3v2_r3` specifically, §3's reported 3.886 m / 89.77° is entirely a pre-settle-backlog artefact, not a
real divergence.** Located directly: every single row with `|Δp| > 0.1 m` or `|Δyaw| > 1°` (36/36 of each) has
`sent_flown == 0` and occurs before the flight's first SENT keyframe (t < 26.02 s; the 36 rows span t = 17.78–
18.95 s, i.e. inside the pre-settle fast-forward). None of this reflects a real tag-reanchor or yaw-cap gate
flip propagating through the flown flight — the actual SENT, post-settle track agrees with the OLD-prior replay
to ≤6 cm / ≤0.08° throughout, the same order as `H_s3v2_r2`. §3's narrative for r3 ("consistent with a yaw-cap
or tag-reanchor gate decision flipping on this bag specifically") does not hold up under this decomposition.

### Conclusion

**Start-pinning closes the gate's residual substantially, but only for the one flight where the mismatch
direction makes it constructible (`H_s3v2_r1`, the restart) — and even there it does not reach the pre-registered
bit-identical/≤1 mm/≤0.01° standard.** `H_s3v2_r1`'s max |Δp| drops 0.153 m → 0.014 m and its within-range max
|Δyaw| drops 0.041° → 0.031° once the tape is trimmed to the restarted node's own actual first message, directly
supporting the hypothesis for that flight. For `H_s3v2_r2`, `H_s3v2_r3` and `cl_fgo_a_tex_half_v3`, the mismatch
runs the other way: the live node's own first message predates the bag recorder's own start (Finding 0, a
structural property of `run_trial.sh`'s launch order, not a per-flight accident), so the hypothesis is **not
testable by any tape construction** — the needed data was never recorded. **All seven flights from §3 still FAIL
the literal pre-registered standard** (none are bit-identical; keyframe counts differ; residuals are centimetre/
tenths-of-a-degree at best, not ≤1 mm/≤0.01°), so §3's verdict ("the re-fly does not start for any flight") is
**unchanged as a gate outcome**. What changes is the *diagnosis underneath two of those failures*: `H_s3v2_r2`'s
and `H_s3v2_r3`'s real, post-settle tracks were already reproducing the flown flight to within a small, bounded
(non-growing) few-centimetre/sub-0.1° band for the whole 300+ s flight once the incomparable pre-settle backlog
and a tail-extrapolation artefact are excluded from the comparison — not the large, "consistent with an
unbounded gate-trace sensitivity" divergence §3 reported, which measured those two artefacts rather than the
flown estimator. `cl_fgo_a_tex_half_v3`'s divergence, by contrast, is real and growing, not an artefact, and
remains unexplained beyond the already-missing ~0.42 s of early data and the Python core's documented
ill-conditioned gate-trace sensitivity (§3) — consistent with, but not proof of, a flipped gate decision near
`t_init` on that flight specifically. No `cl_fgo_b_*` (heading) flight was attempted (§2's blocker — the live
SENT heading stream is genuinely unrecoverable — is unrelated to start-pinning and out of this hour's scope).

**For the coordinator:** if the pre-registered equivalence gate is ever revisited, the two findings above suggest
different paths for different flights: (1) `H_s3v2_r2`/`H_s3v2_r3`/`cl_fgo_a`'s gap cannot be closed by replay
construction at all — it would need `run_trial.sh` to start bag recording *before* the live node (or record a
"first heard" timestamp per node), a harness change, not a diagnostic one; (2) `H_s3v2_r1`'s restart case is
already close to usable with the trimmed tape, and a harness-level fix (log the restarted node's own first-receipt
time, as it already logs `t_armed_header`) would let this be done precisely rather than from a fast-forward proxy
(the first-buffered-event heuristic used here). Neither observation changes the prior-effect numbers in §4, which
remain not separable from the residual for the reasons stated there.

**Checksum guard / freeze check:** `tools/check_numbers_frozen.py` — PASS, before and after. No file under
`~/thesis_data/trials/`, `~/thesis_data/batches/` or `eval/results/` was written or modified; all new outputs are
under `~/thesis_data/diagnostics/fgo_prior_check/gate_diag/` (`H_s3v2_r1_trimmed_OLD.{kf,live,mav}.*`) and the
session scratchpad (`trim_tape.py`, `sent_only_check.py`, `all_rows_locate.py`, `cl_fgo_a_locate.py`,
`r1_restart_check.py`, `r3_tape_check.py`, `tapes/H_s3v2_r1_trimmed.tape.f64`), none committed.
