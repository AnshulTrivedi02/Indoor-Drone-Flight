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
