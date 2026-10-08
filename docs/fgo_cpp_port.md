# FGO C++ port — option A (equivalence to the thesis FGO)

Supervisor ruling 2026-10-08: start the FGO C++ port as coding work and prove equivalence to the
thesis FGO on recorded bags before any further step. Option A of `docs/real_flights_plan.md` §9.3:
a C++ port with the SAME numerical central-difference Jacobians as `src/estimators/fgo/factors.py`.
SymForce exact Jacobians are a later, separate step and are not started here. No simulator was used.

## Pre-registered equivalence band (written 2026-10-08, before the first comparison run)

On the same recorded bag, the C++ FGO and the Python FGO (`fgo_replay.py <trial> 0.25 2 baseline`)
must give:

- an **identical keyframe count**;
- per keyframe, **position difference ≤ 1 mm** (Euclidean, base_link, world ENU);
- per keyframe, **yaw difference ≤ 0.01°**.

Bags, in order: `dsn_tex_r1` (300 s corridor, textured), then `dsn_blank_r1`, `dsn_trans_r1`.
If the band is not met, the cause is found (LM, linearisation order, floating point) rather than the
band being loosened; any unavoidable residual is reported with its size and cause.

(Results, build steps and timing are added below after the runs.)

## What was built

| Item | Where |
|---|---|
| GTSAM 4.2.1 (gtsam + gtsam_unstable), from the release tarball `borglab/gtsam/archive/refs/tags/4.2.1.tar.gz` (sha256 `96ea77d6…dd92c2`) | source `~/opt/src/gtsam-4.2.1`, build `~/opt/src/build-gtsam-4.2.1`, install `~/opt/gtsam-4.2.1` |
| C++ FGO core (baseline arm only), factors, ground-proximity rule (D15), replay | `src/estimators/fgo_cpp/` |
| Python export switch (off by default) | `src/estimators/fgo/fgo_replay.py`: `FGO_DUMP_EVENTS`, `FGO_BAG_ROOT`, `FGO_OUT_ROOT` |

### GTSAM build options (chosen to match the `~/venv-fgo` wheel)

The wheel (`gtsam 4.2.1`, manylinux, GCC 10.2.1) links no TBB and no OpenMP (`ldd`), and its
`Rot3`/`Pose3` retract equal `Expmap` exactly (checked in Python). So:

```
cmake -S ~/opt/src/gtsam-4.2.1 -B ~/opt/src/build-gtsam-4.2.1 -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX=$HOME/opt/gtsam-4.2.1 -DGTSAM_WITH_TBB=OFF -DGTSAM_USE_SYSTEM_EIGEN=OFF \
  -DGTSAM_BUILD_WITH_MARCH_NATIVE=OFF -DGTSAM_BUILD_UNSTABLE=ON -DGTSAM_BUILD_PYTHON=OFF \
  -DGTSAM_UNSTABLE_BUILD_PYTHON=OFF -DGTSAM_BUILD_TESTS=OFF -DGTSAM_BUILD_EXAMPLES_ALWAYS=OFF \
  -DGTSAM_BUILD_TIMING_ALWAYS=OFF -DGTSAM_BUILD_WITH_CCACHE=OFF -DGTSAM_INSTALL_MATLAB_TOOLBOX=OFF
nice -n 19 make -C ~/opt/src/build-gtsam-4.2.1 -j4 gtsam gtsam_unstable && make -C ~/opt/src/build-gtsam-4.2.1 install
```

Resulting configuration (CMake summary): GCC 13.3.0, `-O3 -DNDEBUG`, bundled Eigen 3.3.7, system
Boost 1.83.0, no TBB, no MKL, Rot3/Pose3 retract = full Expmap, quaternions off, tangent-space
preintegration on, Metis nested dissection on. Defaults were kept for every GTSAM model flag.
Eigen comes only from GTSAM's exported target; the port does not `find_package(Eigen3)`, because
system Eigen 3.4 must not be mixed with the bundled 3.3.7.

### The port

- `include/fgo_cpp/factors.h`: `FlowFactor` (X, V, B), `RangeFactor` (X) and `YawPriorFactor` (X), as
  `NoiseModelFactorN`. Their Jacobians are the **same central differences** as `factors.py`
  (EPS 1e-6, `Pose3::retract(±d)`, vector ±d, component-wise `ConstantBias`). `h_flow_pose`,
  `h_flow_rot` and `_wrap` follow the Python operation order, and `_wrap` uses CPython float-modulo
  semantics. As in Python, velocities are stored as dynamic `gtsam::Vector`.
- `src/fgo_core.cpp`: `FGO::init/integrate_imu/keyframe`. The baseline arm of `fgo_core.py` is ported:
  `BatchFixedLagSmoother(0.25 s, LM max 2 iterations)`, `make_pim_params`, the X0/V0/B0 priors, the
  IMU-predicted yaw cap, range and flow gating, and the factor and value order. The forward-camera,
  tag, GNSS, re-anchor, covariance-log and batch-record paths are **not** ported.
- `src/fgo_replay.cpp`: the `fgo_replay.py` loop. It covers keyframes at `t_init + kf_dt` accumulated
  by `+=`, latest flow/range per keyframe, `on_gyro → integrate → while tt >= t_kf_next`, and the
  ground-proximity replacement. The ground-proximity rule is ported because it reads the estimator
  state (`prev_bias`, `prev_pose`). The state-independent inputs come from the export as float64:
  the gap rule, the dejitter, the sort, and each flow's interval-averaged omega.
- `src/probe.cpp` + `tools/fgo_cpp_probe.py`: the same operations in both languages, printed at
  `%.17g`. They cover Rot3/retract, preintegration (Δ and covariance), `predict`, the three factors'
  whitened `[A|b]`, and one smoother keyframe in three variants (IMU only; + yaw cap + range; + flow).
- `tools/compare_kf.py`, `tools/run_equiv.py`, `tools/compare_probe.py`: the comparisons.

Build: `cmake -S src/estimators/fgo_cpp -B <build> -DCMAKE_BUILD_TYPE=Release && make -C <build> -j4`.
The CMake option `-DFGO_CPP_EMULATE_NUMPY_GEMV=ON` (default OFF) is a **diagnostic** (see below).

### Procedure

1. Python reference: `fgo_replay.py <trial> 0.25 2 baseline`, reading a scratch copy of the bag
   (`FGO_BAG_ROOT`) and writing to scratch (`FGO_OUT_ROOT`). No trial directory was written. For
   `dsn_tex_r1` the fresh TUM is byte-identical to the stored `~/thesis_data/trials/dsn_tex_r1/fgo_baseline/fgo_traj.tum`.
   For `dsn_blank_r1` and `dsn_trans_r1` it is byte-identical to the stored legacy `fgo/fgo_traj.tum`
   (same computation, n_kf 10048 / 10031). The round-off-sensitive runs therefore reproduce on this
   machine, and the reference is the thesis result.
2. The same run with `FGO_DUMP_EVENTS=<prefix>`. Its `fgo_traj.tum`, `ground_truth.tum`,
   `fwd_stats.json`, `bgz_series.txt` and `metrics.txt` (without the `step_*` timing lines) are
   **byte-identical** to the run without the export (`dsn_tex_r1`), so the export changes nothing.
3. `fgo_cpp_replay <prefix> <out>`, then `compare_kf.py`. All runs were single-threaded at nice 19,
   with no simulator running. The background bag compression (`packall`) was running throughout.

## Results

### Numerics probe

With the default build, every probe line is **bit-identical** between Python and C++. That covers
Rot3, retract, Δ and the 15×15 preintegration covariance, `predict`, all three factors' `[A|b]`, the
IMU-only keyframe and the keyframe with yaw cap + range. The **one exception** is the keyframe with a
flow factor, which differs at 1.3e-15 (relative 1.6e-10).

Cause: `h_flow_pose` computes `R_wb.T @ v_world`. In Python that is numpy → OpenBLAS `dgemv`. On this
workstation the result was measured to equal `fma(c2,v2, fma(c0,v0, c1*v1))` per component, in
2000/2000 random cases and on all three components. Eigen's product is a plain multiply-add. So the
last bit can differ, and the central difference divides that by 2e-6.

With `FGO_CPP_EMULATE_NUMPY_GEMV=ON`, the C++ does that one product with the same FMA order, and
**all probe lines are bit-identical**, the flow keyframe included.

### Whole-flight equivalence (pre-registered band: same count, |Δp| ≤ 1 mm, |Δyaw| ≤ 0.01°)

**Pre-registered verdict.** The verdict applies to the default build, which was committed before any
comparison: **tex PASS, blank FAIL, trans FAIL.** The emulate-gemv rows were added post hoc, after
the tex and probe results had been seen. They are a diagnostic of the failures' cause, not a
pre-registered pass.

| bag | build | keyframes (Py / C++) | flags¹ | max / p99 \|Δp\| | max / p99 \|Δyaw\| | band | bit-identical |
|---|---|---|---|---|---|---|---|
| dsn_tex_r1 | default | 10197 / 10197 | 0 mismatches | 4.1e-4 / 3.7e-4 mm | 3.2e-8 / 3.2e-8 ° | **PASS** | no |
| dsn_tex_r1 | emulate-gemv (diagnostic, post hoc) | 10197 / 10197 | 0 | 0 / 0 | 0 / 0 | **PASS** | **yes** (whole export and TUM) |
| dsn_blank_r1 | default | 10048 / 10048 | 0 | 1.97e6 / 1.89e6 mm | 20.8 / 0.066 ° | **FAIL** | no |
| dsn_blank_r1 | emulate-gemv (diagnostic, post hoc) | 10048 / 10048 | 0 | 0 / 0 | 0 / 0 | **PASS** | **yes** |
| dsn_trans_r1 | default | 10031 / 10031 | 0 | 1.44e6 / 1.16e6 mm | 19.6 / 2.5 ° | **FAIL** | no |
| dsn_trans_r1 | emulate-gemv (diagnostic, post hoc) | 10031 / 10031 | 0 | 0 / 0 | 0 / 0 | **PASS** | **yes** |

¹ Per keyframe: keyframe created, flow replaced (D15), flow factor added, range factor added.

**Diagnosis of the default-build failures (not a port error).** With the emulation the C++ is
bit-identical to the Python on all three bags. The whole default-build difference therefore comes
from the last-bit rounding of one 3×3 mat-vec. That rounding is amplified only where the Python
FGO itself diverges:

- `dsn_blank_r1`: 501 flow factors in 10048 keyframes. The Python estimate reaches 28.6 km along-track
  against 151 m true, and |V| is about 200 m/s by t = 300 s. |Δp| first exceeds 1 µm at t = 38 s,
  1 mm at t = 51 s and 1 m at t = 98 s.
- `dsn_trans_r1`: within the band until t = 214 s, which is after the y = 80 m blank boundary
  (crossed at t = 189.99 s on this bag's ground truth). The Python estimate then diverges (7.8 km along-track).
- `dsn_tex_r1`, which is well conditioned, stays at sub-micrometre throughout.

So the blank and transition baseline trajectories are sensitive to floating-point round-off at the
level of one BLAS kernel's FMA order. By implication, the Python FGO's blank and transition
divergence numbers are not bit-reproducible across machines or BLAS builds either; the textured
result is.

### Timing (per-keyframe step: the D15 replacement + `keyframe()`, the same timed region; single thread)

| bag | Python median / p99 | C++ (default) median / p99 | median speed-up |
|---|---|---|---|
| dsn_tex_r1 | 21.6 / 41.8 ms² | 0.61 / 1.44 ms | ~35× |
| dsn_blank_r1 | 4.0 / 37.3 ms | 0.86 / 3.70 ms | ~4.7× |
| dsn_trans_r1 | 17.3 / 59.7 ms | 0.86 / 3.25 ms | ~20× |

² A dedicated re-run with nothing else heavy running. The earlier `dsn_tex_r1` run, made during the
GTSAM compile, gave 34.1 / 87.9 ms. Python timing varies with machine load by this much.

The C++ times on blank and transition are for the default build's own (diverged) trajectories.
With the emulation build (an extra libm `fma` call), the medians were tex 0.87, blank 0.73 and
trans 0.58 ms. All of these are DIAGNOSTIC workstation numbers, not onboard (Pi) numbers.

## Open issues

- Only the baseline arm is ported. The forward-camera heading/yaw-rate factors with the gate-only
  covariance recursion, and the tag, GNSS and re-anchor paths, are still to do.
- The replay reads the export and does not decode bags. The interval-averaged flow omega, the gap
  rule and the dejitter come from Python. A live node needs `FlowFrameGyroAverager`, which is
  state-independent and easy to port, plus a bag/ROS front end.
- Which build is the deployable one? The default (Eigen) build is the natural one. The emulation
  build exists only to prove the port exact. The blank and transition baseline are
  round-off-chaotic in both languages.
- SymForce exact Jacobians are a later step and were not started.

---

# Part 2: aided-regime arms, native input handling, Pi estimate (started 2026-10-08)

The user ruled on part 1 (2026-10-08). The result stands as recorded above: the pre-registered band
PASSES on textured and FAILS as worded on blank and transition, with the evidence and the post-hoc
emulation diagnosis. The band is not re-stated. The default (Eigen) C++ build is accepted for
real-flight use in the AIDED regime only. SymForce is dropped.

## Pre-registration 2 (written and committed BEFORE any part-2 comparison was run)

**Band B (unchanged from part 1).** Default Eigen build (`FGO_CPP_EMULATE_NUMPY_GEMV` OFF), same
keyframe count, and per keyframe |Δp| ≤ 1 mm and |Δyaw| ≤ 0.01° against the Python FGO on the same
bag, run with the same arguments. Each row below is a separate PASS/FAIL, reported as measured. A
failure is diagnosed and the band is not loosened.

| row | Python reference | compared |
|---|---|---|
| B1 | `fgo_replay.py fwdc_tex_r1 0.25 2 heading` | every keyframe |
| B2 | `room_fgo_replay.py T_A_r1`, live track | every keyframe that is anchored in both runs |
| B3 | `room_fgo_replay.py T_D_r1`, live track | as B2 |
| B4 | `T_A_r1` whole-flight batch (hindsight) | every batch key (X(k) of `key_t`): |Δp| ≤ 1 mm, |Δyaw| ≤ 0.01°, same key set |
| B5 | `T_D_r1` whole-flight batch | as B4 |
| B6 (only if time allows) | `room_fgo_replay.py O_r1 --gnss`, live (+ batch as a separate row) | as B2 / B4 |

**Also reported, with no band:**
- agreement of the per-keyframe decisions (flow replaced, flow / range / tag / GNSS factor added,
  heading and yaw-rate gate accepted, anchored);
- the smallest |NIS − 9| over the forward frames, which shows how close the gate came to a flip;
- step time per keyframe (C++ vs Python, single thread).

**Band C (native front end, task C).** `fgo_cpp_frontend` reads only the raw bag-order stream and the
configuration. It must reproduce the export-driven `fgo_cpp_replay` result on the same bag: same
keyframe count, and per keyframe |Δp| ≤ 1 mm and |Δyaw| ≤ 0.01°. Bags: `dsn_tex_r1` (baseline),
`fwdc_tex_r1` (heading), `T_A_r1` and `T_D_r1` (live). Also reported, with no band: the dejittered
IMU stamps against Python's `np.polyfit` stamps (max |Δt|), whether the interval-averaged gyro and
the init inputs (gravity levelling, first range, t_init) are bit-identical, and decision agreement.

## Part 2: what was added

- **Python export, extended (off by default).** `src/estimators/fgo/fgo_export.py` is used by both
  `fgo_replay.py` and `room_fgo_replay.py`, and is enabled by the same three environment variables
  (`FGO_DUMP_EVENTS`, `FGO_BAG_ROOT`, `FGO_OUT_ROOT`). It writes:
  - the RAW bag-order stream (for the native front end);
  - the processed stream, plus the interval-averaged gyro for forward frames;
  - 40-column keyframe rows, including the heading and yaw-rate NIS and accept decisions, the tag and
    GNSS factor flags, and the anchored flag;
  - the whole-flight batch solution.
- **C++ core.**
  - The forward-camera heading and yaw-rate factors, with the chi-square gate on the gate-only
    covariance recursion (`_info`, `_posterior_cov`).
  - `reanchor` (tag, and GNSS with velocity and `keep_yawcap`), and the tag and GNSS factors.
  - The batch record, including `batch_drop_yawcap`, and the whole-flight batch: LM, 50 iterations,
    relative tolerance 1e-6.
- **C++ runner** (`replay_common.cpp`). The loops of both Python harnesses are ported: corridor, and
  room with the tag/GNSS anchoring logic.
- **Native front end** (`fgo_cpp_frontend`):
  - `offline_imu_timing` runs the gap rule and the IMU dejitter. It is offline only; a live node uses
    `/imu/time_ref`.
  - `StreamFrontEnd` takes events one at a time, in arrival order. It runs a reorder buffer
    (1 s delay; ties broken by source rank, then arrival), the init inputs and its own
    interval-averaged gyro (numpy pairwise summation reproduced), then the runner.
  - The configuration is the only thing read from the export.
- **`tools/heavy.py`.** This is the lock protocol for every compile and run: it waits on
  `FLIGHT_LOCK` and on arducopter / `gz sim`, holds `BUILD_LOCK` for one bounded step, and runs at
  nice 19 with one BLAS thread.

All runs were made on scratch copies of the bags. `fwdc_tex_r1` was decompressed from its `.zst` into
scratch, and its sha256 matched `PACKED.txt`. No trial directory was written.

**Reference checks.**
- `fwdc_tex_r1 heading`: the fresh Python TUM and `fwd_stats.json` are byte-identical to the stored
  `fgo_heading/`.
- `dsn_tex_r1 baseline`: the fresh TUM is byte-identical to the stored one.
- The export did not change the room replay: on `T_A_r1`, the live TUM with and without the export is
  byte-identical.

## Part 2 results (band B: C++ default build vs Python, pre-registered above)

| row | bag / run | keyframes Py / C++ | decisions | max / p99 \|Δp\| | max / p99 \|Δyaw\| | band |
|---|---|---|---|---|---|---|
| B1 | fwdc_tex_r1 heading | 10118 / 10118 | 0 mismatches (heading accepted 9480 of 9539) | 1.7e-4 / 1.6e-4 mm | 6.3e-11 / 2.5e-11 ° | **PASS** |
| B2 | T_A_r1 live (7774 anchored) | 8015 / 8015 | 0 (2394 tag factors) | 4.6e-8 / 1.3e-8 mm | 1.7e-10 / 1.2e-10 ° | **PASS** |
| B3 | T_D_r1 live (7755 anchored) | 8017 / 8017 | 0 (570 tag factors) | 7.8e-6 / 6.8e-6 mm | 1.3e-7 / 1.1e-7 ° | **PASS** |
| B4 | T_A_r1 batch | 7775 / 7775 keys (ids identical) | n/a | 1.4e-8 / 9.4e-9 mm | 8.2e-11 / 4.8e-11 ° | **PASS** |
| B5 | T_D_r1 batch | 7756 / 7756 keys (ids identical) | n/a | 1.6e-7 / 1.6e-7 mm | 1.3e-9 / 1.2e-9 ° | **PASS** |

- The smallest |NIS − 9| over the 9539 heading frames was 0.167. No gate decision was near a flip.
- The heading NIS differed between Python and C++ by at most 7.6e-8. That difference is numpy/LAPACK
  against Eigen in the gate-only recursion (`inv`, `A.T @ A`).
- The batch LM gave the same error to the printed digits (T_A_r1 111.673118, T_D_r1 40.574967) and
  the same iteration count (3) in both languages.

## Part 2 results (band C: native front end vs export-driven C++, pre-registered above)

| bag | keyframes | decisions | max / p99 \|Δp\| | max / p99 \|Δyaw\| | band |
|---|---|---|---|---|---|
| dsn_tex_r1 baseline | 10197 / 10197 | 0 mismatches | 7.9e-4 / 1.3e-4 mm | 1.9e-8 / 1.5e-8 ° | **PASS** |
| fwdc_tex_r1 heading | 10118 / 10118 | 0 | 1.1e-4 / 1.0e-4 mm | 1.3e-10 / 4.0e-11 ° | **PASS** |
| T_A_r1 live (+ batch) | 8015 / 8015 | 0 | 7.3e-8 / 1.4e-8 mm (batch 1.8e-9) | 1.9e-10 ° | **PASS** (batch PASS) |
| T_D_r1 live (+ batch) | 8017 / 8017 | 0 | 8.4e-6 / 4.4e-6 mm (batch 8.7e-8) | 8.4e-8 ° | **PASS** (batch PASS) |

Stream diagnostics, the same on all four bags:
- Event count, kind order, non-IMU stamps and all measurement payloads are bit-identical to Python's
  processed stream.
- The interval-averaged gyro is **bit-identical**: flow omega on every frame, and forward gyro-z on
  9635 of 9635 frames.
- Gravity levelling and the first range are bit-identical.
- The dejittered IMU stamps differ from `np.polyfit` by at most 2.3e-13 s, so `t_init` differs in the
  last bits. This is the only input difference: the closed-form fit is not numpy's SVD least squares.
- The reorder buffer saw at most 0.185 s of lateness and released nothing out of order.

## Finding outside the port: some stored experiment-T FGO outputs predate `imu_gaps.json`

The stored `T_A_r1` and `T_D_r1` `room_fgo/` outputs are NOT reproduced by the current code. Against
the fresh runs:

| run | max \|Δp\| | median \|Δp\| |
|---|---|---|
| T_A_r1 live | 1.7 mm | 0.03 mm |
| T_A_r1 batch | 1.2 mm | not computed |
| T_D_r1 live | **163 mm** | 0.68 mm |
| T_D_r1 batch | **90 mm** | 0.15 mm |

Diagnosis (scratch copies only; nothing in the repository or the trial directories was changed):
- Leaving the BLAS threads at their defaults changes `T_D_r1` live by only 0.001 mm.
- Keeping `log_cov` on after the anchor changes nothing (byte-identical).
- Running the current code **as if `imu_gaps.json` did not exist** reproduces the stored `T_D_r1`
  `fgo_live.tum` **and** `fgo_batch.tum` byte for byte. With no file there is no D15 arming time, so
  no ground-proximity flow rule.

From the file times, the `room_fgo/` outputs of **T_A_r1, T_B_r1, T_C_r1, T_C_r3, T_D_r1 and
T_D_r3** were written (04:48–04:49) before their `imu_gaps.json` (04:59–05:01). Their `room_ukf/`
outputs were written afterwards (06:38–06:40), as were all r2 runs, the other T runs, O and H.
Those FGO results therefore lack the D15 rule that the UKF had. This was flagged to the coordinator;
nothing was re-run in the trial directories.

### B6 (optional row, run): O_r1 GNSS

The fresh Python `O_r1 --gnss` live and batch TUMs are byte-identical to the stored `room_fgo/` ones.
The C++ results, compared over 6895 anchored keyframes:
- Live: 7288 / 7288 keyframes, 533 GNSS factors, 0 decision mismatches, max / p99 |Δp| 2.6e-5 /
  4.0e-6 mm, max |Δyaw| 3.8e-8° → **PASS**.
- Batch: 6896 / 6896 keys with identical key ids, max |Δp| 1.1e-7 mm → **PASS**.

### Part 2 numerics probe

The heading, yaw-rate, tag and GNSS factors' whitened `[A|b]` are **bit-identical** between Python
and C++. The part-1 lines are unchanged: everything is bit-identical except the flow keyframe
(1.3e-15), whose cause is the gemv rounding found in part 1.

## Timing (task D)

Per-keyframe step, same timed region in both languages, single thread, nice 19. These are
workstation numbers on an i7-8700 with a generic x86-64 build (no `-march=native`), and DIAGNOSTIC
only. Other jobs were running at times, so medians varied by about ±40% between repeat runs (for
example, T_A_r1 C++ 0.92 ms in one run and 0.57 ms in another).

| run | Python median / p99 | C++ median / p99 (max) |
|---|---|---|
| dsn_tex_r1 baseline | 21.6 / 41.8 ms | 0.54–0.61 / 0.94–1.44 ms |
| fwdc_tex_r1 heading (gate recursion every keyframe) | 43.5 / 86.1 ms | 1.14–1.19 / 1.77–2.20 ms (max 12.9 ms) |
| T_A_r1 live (tags) | 19.4 ms (median only, from stats.json) | 0.57–0.92 / 1.36–1.80 ms |
| T_D_r1 live (tags) | 18.4 ms | 0.55 / 1.17–1.29 ms |
| O_r1 live (GNSS, recursion on throughout) | 19.0 ms | 0.67 / 1.53 ms |
| whole-flight batch, T_A_r1 / T_D_r1 / O_r1 | 834 / 661 / 642 s | 1.2–1.4 s |

The C++ batch is about 500× faster. It makes the hindsight batch cheap enough to run routinely.

### Raspberry Pi estimate (an ESTIMATE, not a measurement)

**Basis.** Published Geekbench 6 single-core scores:
- i7-8700: about 1527 (Geekbench processor page).
- Raspberry Pi 5: about 764–787.
- Raspberry Pi 4: about 293–340 (Geekbench browser comparisons and published reviews).

These give single-core ratios of about **1.9–2.0× (Pi 5)** and about **4.5–5.2× (Pi 4)**.

**Scaling the worst observed C++ run** (the heading arm, p99 2.2 ms):

| | median | p99 |
|---|---|---|
| Pi 5 | ~2.3 ms | **~4.3 ms** |
| Pi 4 | ~5.4–6.2 ms | **~10–11.5 ms** |

Both are inside the 33 ms keyframe budget. Even with a further 2× margin, the Pi 4 p99 (~23 ms)
fits.

**Caveats.**
- Geekbench is a composite; it is not this workload (small dense factorisations, allocation, cache).
- The Pi may throttle thermally.
- The ARM build will use NEON while this x86 build uses no AVX.
- Single spikes (max 12.9 ms here) would scale to ~25 ms on a Pi 5 and ~65 ms on a Pi 4. A live
  node must tolerate an occasional late keyframe; the replay cadence does not drop keyframes.

**Not done.** Neither a qemu run nor a cross-compile was done. qemu timing would not be
representative, and correctness is already established on x86. A timing run on a real Pi is the next
step.

## Part 2 open issues

- **Live node.**
  - IMU stamping must come from `/imu/time_ref`; the dejitter is offline only.
  - A ROS 2 or MAVLink adapter is needed that calls `StreamFrontEnd::push`.
  - The reorder delay (1 s here) needs to be set for real latencies; the measured maximum lateness
    in the bags was 0.185 s.
- **Not ported.** The offline F-test variants (F1 robust heading, F3 injected yaw, F_MASK /
  F_HDG_FROM_CRUISE) and the diagnostic covariance-log output. The recursion itself is ported.
- **Experiment T.** Six stored room_fgo results predate `imu_gaps.json` (see the finding above).

---

# Part 3: live ROS 2 / MAVLink adapter (started 2026-10-08, coding only, no simulator)

The C++ counterpart of `fgo_node.py` + `fgo_node_core.py` is `fgo_cpp::LiveAdapter` (`live_adapter.{h,cpp}`).
It has no ROS dependency. Two thin shells sit around it:
- the ROS 2 node `fgo_cpp_node` (subscriptions as `fgo_node.py`, with a worker thread so callbacks never
  block, `/fgo/pose` and `/fgo/valid`, and ODOMETRY over `mavlink_out`);
- the deterministic bag-replay harness `fgo_cpp_live_replay`. It feeds a "message tape" — the bag's
  messages in receipt order with their header stamps, written by `tools/make_tape.py` — through the
  same calls the node's callbacks make.

What the adapter does:
- **Reorder buffer**, default delay 0.20 s (the bags showed lateness ≤ 0.185 s).
- **IMU stamps**, three options:
  - `time_ref` (live default): HIGHRES_IMU `time_usec` paired by header stamp and mapped to the header
    clock by the D25 lower envelope, slew-limited to 50 µs per sample;
  - `causal`: the Python node's running fit;
  - `header`: the stamp as given.
- **Causal IMU-gap rule**: before take-off a gap re-initialises the estimator and keeps the queue;
  after take-off it makes the output invalid for the rest of the flight.
- **Validity rule**: `valid_now`.
- **Clock map**: D25 settle, envelope and `_sitl_us`.
- **ODOMETRY**: `LOCAL_NED`, `MAV_ESTIMATOR_TYPE_NAIVE`, quality 100/0, gyro bias in the rates and
  accel bias in `pose_covariance[0:3]`, as `fgo_node._send_state`. It is encoded by a built-in
  MAVLink 2 encoder (`mavlink_io.h`).
- **UDP**: pymavlink `udp:` listen semantics. HEARTBEAT armed flag → D15 arming time.
- **Heading**: gated as `fgo_node._hdg`.
- **Tag fixes**: experiment T anchoring, in an ENU navigation frame.

## Pre-registration 3 (written and committed BEFORE any part-3 comparison was run)

**Band L (= band C).** The reference is the export-driven C++ result on the same bag (`fgo_cpp_replay`
on the part-2 export). Requirements:
- the same keyframe count;
- per keyframe, |Δp| ≤ 1 mm and |Δyaw| ≤ 0.01°, for (a) every adapter keyframe state and (b) every
  ODOMETRY message actually produced, decoded by pymavlink and converted back from NED to the
  navigation frame;
- in addition, every ODOMETRY `time_usec` must EQUAL an independent Python re-implementation of
  `fgo_node._sitl_us` over the time_ref messages that had arrived;
- in addition, every frame must parse with a valid CRC in pymavlink.

| row | bag | adapter configuration |
|---|---|---|
| L1 | dsn_tex_r1 | tape with the offline dejittered IMU stamps substituted (`--imu-stamp header`); arming time = the export's (`--arm-source param`); delay 0.20 s; everything else live: receipt order, reorder buffer, interval-averaged gyro, init, keyframing, gap rule, validity, clock map, ODOMETRY encoding |
| L2 | fwdc_tex_r1 | as L1, plus the heading input: the export's frozen forward headings written as the heading bridge's sent message (NED yaw = −psi, quality 100, angErr 0) at their capture stamp, with heading sigma = the offline heading arm's (0.148°) and gate 9 |

**Also reported, with no band:**
- The live configurations on the same bags: `--imu-stamp time_ref` (the default) and `--imu-stamp causal`
  (the Python node's choice). Both use the raw receipt stamps, with arming from the export time.
  These differ from the reference by construction (different IMU time base), so they are a report.
- Whether the adapter's ODOMETRY frames are byte-identical to pymavlink's encoding of the same values.
- Step time.

**Cannot be tested without SITL** (left for the main session's live ground test):
- message arrival timing and latency;
- the ROS 2 executor and queueing under load;
- UDP delivery to and from SITL SERIAL3;
- HEARTBEAT-derived arming;
- whether AP_NavFGO accepts and flies the state.
