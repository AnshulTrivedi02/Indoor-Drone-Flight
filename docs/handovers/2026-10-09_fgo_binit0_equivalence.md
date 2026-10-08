# FGO noise-model correction (`setBiasAccOmegaInit` → 0) and the C++-vs-Python equivalence re-check (2026-10-09)

Stage agent, worktree branch `worktree-agent-ab3173e5349728427` (from `fwd-camera` 104fd5e). Ruling: METHODOLOGY
"RULING (user, 2026-10-09): FGO noise-model correction". No simulator was run, and no harness file was touched. Nothing
was written to a trial directory. Nothing was installed to `~/opt/fgo_cpp`.

## Verdict in one line
**With both cores corrected, every pre-registered band that passed before still passes:**
- A (tex);
- B1–B5, plus the optional B6;
- C (all four bags);
- L1 and L2.

**Band A blank and trans FAIL as worded, as they did before.** Under the corrected model the cause is the same:
- the post-hoc emulate-gemv build is bit-identical to Python on all three dsn bags;
- the default-build difference is the last-bit rounding of one 3×3 mat-vec, amplified only where the Python FGO itself
  diverges.

## 1. The change (commit 2544585 on the worktree branch)
- `src/estimators/fgo/fgo_core.py` (`make_pim_params`): `p.setBiasAccOmegaInit(np.zeros((6, 6)))`.
- `src/estimators/fgo_cpp/src/fgo_core.cpp` (`make_pim_params`): `p->setBiasAccOmegaInit(gtsam::Matrix6::Zero())`.
- Each change has a three-line comment citing the ruling and `CombinedImuFactor.cpp:138-163`.
- **Unchanged:** the `B(0)` prior (`ACCEL_B0` 0.2, `GYRO_B0` 0.043633, `PriorFactorConstantBias`) and every other
  parameter.
- **Process:**
  - The edit guard refused the first edit, because flight `H_s2_r1` was running and the worktree sits under
    `~/thesis_ws`.
  - The change was held as a patch (`eval/results/fgo_cpp_equiv_binit0/binit0.patch`). It was built and run from a
    patched scratch copy of `src/estimators/`.
  - It was applied to the worktree once no flight was running (FLIGHT_LOCK absent, no arducopter), at 02:47.
  - `diff -r` then showed the worktree and the scratch tree to be identical, apart from `__pycache__`. **So the tested
    sources equal the committed ones.**

**Other places that build these params** (grep for `setBiasAccOmegaInit`, `biasAccOmegaInt` and
`PreintegrationCombinedParams` over `src`, `tools`, `sim`, `eval`, `docs` and `~/ardupilot_ukf`):
- Only the two cores construct them. Everything else (`fgo_replay`, `room_fgo_replay`, `fgo_node.py`, the probe)
  calls `make_pim_params()`.
- `eval/diag/fgo_tilt_trace/pimcov.py` and `diag_replay.py` set the term themselves. They are the tilt-trace
  DIAGNOSTICS (knobs) and were left unchanged.
- There are no hits in `~/ardupilot_ukf` or `sim/`.

## 2. Build (scratch; NOT installed)
- **Where:** built from the patched scratch tree into
  `/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/binit0/build`
  (default Eigen build, ROS node included).
- **How:** through `heavy.py`, with a clean `env -i` PATH and the same cmake line as `build_fgo_main.sh`, minus
  `make install`. The line is in `eval/results/fgo_cpp_equiv_binit0/scripts/step.sh`.
- **No warnings.**

| binary | md5 |
|---|---|
| fgo_cpp_node | `6002f76ebc1bb7fa1684a236ea9345b4` |
| fgo_cpp_live_replay | `22dfa5dfef159af48814160fb3d76fd9` |
| fgo_cpp_replay | `3591d69e7288b2ba95670b01d6378815` |
| fgo_cpp_frontend | `2bdf3a951b35cced34f42a2a9097bda2` |
| fgo_cpp_probe | `da4aeb0c8d497138cbda0e8fdeac4de9` |
| fgo_cpp_replay, emulate-gemv (diagnostic only) | `b885fd231d38868c73547007efbfaeef` |

- The currently installed `~/opt/fgo_cpp/bin/fgo_cpp_node` is `53831eae…`. That is the last md5 recorded in
  METHODOLOGY (C++ node regression, 2026-10-09), built from source before this correction.
- **Tested base:** `104fd5e` plus the patch. At hand-back, `git log 104fd5e..fwd-camera -- src/estimators/` is empty
  (`fwd-camera` is at `b1422b7`). So merging this branch builds exactly the tested source.
- **md5 may depend on the source path** (GTSAM headers embed `__FILE__`). A build from `~/thesis_ws` may therefore
  give different md5s. Use the functional check in §6 instead.

## 3. Proof that both cores picked up the change
- **Numerics probe, Python vs C++ (new):**
  - every line is bit-identical, including the 15×15 preintegration covariance;
  - the one exception is `kf2` (the flow keyframe), at 2.2e-15. That is the known gemv rounding (part 1).
- **Probe, new Python vs the old part-2 Python probe:**
  - `cov` differs (max |d| 3.7e-2, relative 1.0), and so do `kf1`/`kf2`;
  - every factor `[A|b]` is unchanged. So only the preintegration noise moved, as intended.
- **Import path:** `fgo_core.__file__` resolved to the patched scratch tree. `getBiasAccOmegaInit()` is all zeros.
- **Unchanged inputs:** the new exports' raw streams are byte-identical to the old ones (`dsn_tex_r1`, `fwdc_tex_r1`;
  for fwdc the processed stream too). The band-L tapes from the old run (`live/*.dj.tape`) were therefore reused. They
  are built from the bag and the frozen headings, not from estimator state.

## 4. Bands (default Eigen build; thresholds as registered: same count, |Δp| ≤ 1 mm, |Δyaw| ≤ 0.01°)
Python references were run with `FGO_BAG_ROOT` (scratch bag copies) and `FGO_OUT_ROOT` (scratch), exactly as
registered (`fgo_replay.py <t> 0.25 2 baseline|heading`, `room_fgo_replay.py <t>` with batch, `O_r1 --gnss`). Every
step ran single-threaded at nice 19 through `heavy.py`. **The full logs are in `eval/results/fgo_cpp_equiv_binit0/`.**

### Band A (part 1; Python vs C++ export-driven replay)
| bag | keyframes | decisions | max / p99 \|Δp\| | max / p99 \|Δyaw\| | band |
|---|---|---|---|---|---|
| dsn_tex_r1 | 10197 / 10197 | 0 mismatches | 2.3e-2 / 1.0e-4 mm | 7.6e-8 / 6.0e-9 ° | **PASS** |
| dsn_blank_r1 | 10048 / 10048 | 0 | 2.4e7 / 2.3e7 mm | 42.3 / 0.54 ° | **FAIL (as worded)** |
| dsn_trans_r1 | 10031 / 10031 | 0 | 5.4e5 / 3.2e5 mm | 3.4 / 0.56 ° | **FAIL (as worded)** |

**Onset of the divergence** (first |Δp| > 1 µm / 1 mm / 1 m):
- blank: 51.3 / 68.2 / 102.7 s;
- trans: 211.6 / 225.6 / 274.8 s, after the y = 80 m boundary (t = 190 s);
- tex: 346.1 s / never / never.

**The corrected Python FGO itself diverges on these bags:**
- blank: along-track 35.6 km, cruise |V| 105 m/s, 501 flow factors;
- trans: along-track 2.78 km.

**Post-hoc diagnostic** (emulate-gemv build, labelled post hoc, NOT a pre-registered pass): it is **bit-identical**
to Python on all three bags (whole kf export, `cmp`). The FAIL is therefore round-off amplified by a divergent
trajectory, not a port error. It is the same as the part-1 finding.

### Band B (C++ vs Python)
| row | run | keyframes | decisions | max / p99 \|Δp\| | max / p99 \|Δyaw\| | band |
|---|---|---|---|---|---|---|
| B1 | fwdc_tex_r1 heading | 10118 / 10118 | 0 (heading accepted 9184 of 9539) | 1.2e-4 / 1.1e-4 mm | 1.2e-10 / 1.7e-11 ° | **PASS** |
| B2 | T_A_r1 live (7774 anchored) | 8015 / 8015 | 0 (2394 tag factors) | 9.9e-8 / 6.6e-8 mm | 2.2e-10 / 9.1e-11 ° | **PASS** |
| B3 | T_D_r1 live (7755 anchored) | 8017 / 8017 | 0 (570 tag factors) | 3.2e-5 / 2.7e-5 mm | 4.3e-7 / 3.7e-7 ° | **PASS** |
| B4 | T_A_r1 batch | 7775 / 7775 keys, ids identical | n/a | 5.1e-9 / 4.6e-9 mm | 9.4e-12 ° | **PASS** |
| B5 | T_D_r1 batch | 7756 / 7756, ids identical | n/a | 3.1e-8 / 3.1e-8 mm | 4.6e-11 ° | **PASS** |
| B6 (optional) | O_r1 GNSS live (6895 anchored) / batch | 7288 / 7288; 6896 / 6896 keys | 0 (533 GNSS factors) | 3.8e-4 / 3.7e-5 mm; batch 1.1e-7 mm | 1.2e-6 °; batch 7.1e-10 ° | **PASS / PASS** |

- **Batch LM:** the error and iteration count are identical in both languages: T_A 135.736713 (4 iterations),
  T_D 58.605479 (5), O_r1 29.469094 (10). Under the old model they were T_A 111.673118 and T_D 40.574967, with 3
  iterations each.
- **Heading NIS, Python vs C++:** max |diff| 2.5e-7. The **smallest |NIS − 9| is now 0.028**, against 0.167 under the
  old model. That is closer to a flip, but no decision flipped.

### Band C (native front end vs export-driven C++)
| bag | keyframes | decisions | max / p99 \|Δp\| | max / p99 \|Δyaw\| | band |
|---|---|---|---|---|---|
| dsn_tex_r1 baseline | 10197 / 10197 | 0 | 1.7e-2 / 1.1e-4 mm | 9.4e-8 / 1.4e-8 ° | **PASS** |
| fwdc_tex_r1 heading | 10118 / 10118 | 0 | 6.7e-5 / 5.5e-5 mm | 4.8e-11 ° | **PASS** |
| T_A_r1 live (+ batch) | 8015 / 8015 | 0 | 1.3e-7 / 8.2e-8 mm (batch 3.1e-9) | 5.3e-11 ° | **PASS** (batch PASS) |
| T_D_r1 live (+ batch) | 8017 / 8017 | 0 | 4.4e-5 / 3.8e-5 mm (batch 3.4e-8) | 5.7e-7 ° | **PASS** (batch PASS) |

- **Stream diagnostics, as in part 2:**
  - event counts, kind order, non-IMU stamps and payloads are bit-identical;
  - the interval-averaged flow omega and forward gyro-z are bit-identical;
  - the dejittered IMU stamps differ from `np.polyfit` by ≤ 2.3e-13 s, so `t_init` differs in the last bits.
- **On T_A/T_D the batch printout says "key ids identical: False".** The key indices are identical; only the key
  stamps differ, by ≤ 2.8e-14 s, because of that `t_init` difference. The band is computed on the states and PASSES.

### Band L (live adapter vs export-driven C++; dejittered tape, `--imu-stamp header --arm-source param --delay 0.20`)
| row | keyframes | decisions | adapter states | decoded ODOMETRY | time_usec = `_sitl_us` | band |
|---|---|---|---|---|---|---|
| L1 dsn_tex_r1 | 10197 / 10197 | 0 | **bit-identical** | 7.8e-3 / 7.1e-3 mm; 3.0e-6 ° | 9919 / 9919 | **PASS** |
| L2 fwdc_tex_r1 heading (σ 0.148°, gate 9) | 10118 / 10118 | 0 | **bit-identical** | 7.6e-3 / 7.2e-3 mm; 2.0e-8 ° | 9840 / 9840 | **PASS** |

- CRC: 0 errors.
- The frames are byte-identical to pymavlink's encoding.
- Quality matches validity on every frame.
- The first 278 keyframes are held back by D25, as before.

### Not re-run
- The live IMU-stamp mode reports (part 3, no band).
- The part-4/5 SITL checks.
- The H S2/S3 tag-input bands FN1–FN4 (`abdb7b2`). They were not in this stage's brief. If S3's gate needs them,
  they still have to be run against the corrected node.

## 5. Old-vs-new indications (single bags, first indication only, NOT thesis results)
| | old | new (binit0) |
|---|---|---|
| dsn_tex_r1 baseline: unaligned apparatus ATE / yaw drift | 133.62 m / −9.14 °/min | 133.65 m / −9.05 °/min |
| fwdc_tex_r1 heading: apparatus ATE | 123.25 m | 123.22 m |
| fwdc_tex_r1 heading: heading frames accepted | 9480 / 9539 | **9184 / 9539** |
| Python step median (dsn_tex) | 21.6 ms | 15.6 ms (load-dependent) |

The apparatus ATE is the harness's unaligned metric, not evo -a (cruise). The consolidated re-run must give the real
numbers. The drop in heading acceptance (−296 frames) is worth a look in that re-run: the tighter IMU noise makes the
heading gate stricter.

## 6. Install recipe for the main session (after review and merge; only when no flight runs)
```bash
# 0. preconditions
pgrep -fa '[a]rducopter'; ls ~/thesis_data/FLIGHT_LOCK     # both must be empty / absent
# 1. merge the worktree branch (code commit 2544585 + results/handover commit) into fwd-camera, then:
cat > /tmp/build_binit0.sh <<'EOF'
env -i HOME=$HOME PATH=/usr/bin:/bin bash -c 'source /opt/ros/jazzy/setup.bash && B=$HOME/opt/src/build-fgo_cpp-binit0 && cmake -S $HOME/thesis_ws/src/estimators/fgo_cpp -B $B -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=$HOME/opt/fgo_cpp -DPython3_EXECUTABLE=/usr/bin/python3 "-DCMAKE_PREFIX_PATH=/opt/ros/jazzy;$HOME/thesis_ws/install/optical_flow_interfaces" && make -C $B -j4 && make -C $B install && md5sum $HOME/opt/fgo_cpp/bin/*'
EOF
python3 ~/thesis_ws/src/estimators/fgo_cpp/tools/heavy.py "install fgo_cpp binit0" -- bash /tmp/build_binit0.sh
```
**2. Functional acceptance check, instead of md5.**
- Replay the corrected dsn_tex export with the installed replay binary. Its keyframes must be **byte-identical** to
  this stage's:
  ```bash
  D=/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/binit0/dump
  ~/opt/fgo_cpp/bin/fgo_cpp_replay $D/dsn_tex_r1_baseline /tmp/accept_binit0 && cmp $D/cpp_dsn_tex_r1_baseline.kf.f64 /tmp/accept_binit0.kf.f64 && echo ACCEPT
  ```
- The node links the same `fgo_cpp_core` library. To check the node path too, run
  `~/opt/fgo_cpp/bin/fgo_cpp_live_replay` with the L1 command (`scripts/step.sh`, case `live`) and `cmp` its `.kf.f64`
  with `$D/L1.kf.f64`.
- **Reference sha256** (in case `/tmp` is cleaned):
  - `dsn_tex_r1_baseline.kf.f64` (Python export): `49227a44c4d28ab4160d6d7461c507f0572b18a5e76315151890ccd5efe136ab`;
  - `cpp_dsn_tex_r1_baseline.kf.f64` (C++ replay) and `L1.kf.f64` (live adapter; the same bytes):
    `fef3533ae18008048573d44554763a49137224c14122280830bb8c4dcabdd7ce`.
- To regenerate the export (~3 min), run `FGO_BAG_ROOT=<scratch bag copy> FGO_OUT_ROOT=<scratch> FGO_DUMP_EVENTS=<prefix>`
  `~/venv-fgo/bin/python src/estimators/fgo/fgo_replay.py dsn_tex_r1 0.25 2 baseline` and check the hashes. If ACCEPT
  fails on a source that has changed since `104fd5e`, the bands must be re-run on the merged source.
- **Fallback if the scratch dir is gone:** the probe pair (`fgo_cpp_probe.py` vs a freshly built `fgo_cpp_probe`)
  must give a bit-identical `cov` line, and that line must differ from the old `probe2_py.txt`.
- **Before S3:** record the new `fgo_cpp_node` md5 in METHODOLOGY. The old one is `53831eae…`.

## 7. Anything unexpected
- **The first fwdc Python run failed** (rc 1, 6 s). `measurement_models.forward_events` reads
  `../../eval/results/fwd_calibration.json` relative to the source tree, and the scratch tree lacked it. A byte-identical
  copy (checked with `cmp` against the main repo) was placed in the scratch tree, and the fwdc chain was re-run. No
  other effect.
- **heavy.py waited 23 min at the start**, for `H_s2_r1`'s FLIGHT_LOCK. The other agent's BUILD_LOCK was released before then.
- **The edit guard refused edits to the worktree** while the flight ran (§1). It worked as designed.

## Files
- **Committed (worktree branch):**
  - `src/estimators/fgo/fgo_core.py`, `src/estimators/fgo_cpp/src/fgo_core.cpp`;
  - `eval/results/fgo_cpp_equiv_binit0/`: every step log, the probe outputs, md5s, the patch, and the driver and step
    scripts;
  - this handover.
- **Scratch only** (`…/scratchpad/binit0/`): the exports and C++ outputs (`dump/`), the Python outputs (`out/`), and
  the builds.
