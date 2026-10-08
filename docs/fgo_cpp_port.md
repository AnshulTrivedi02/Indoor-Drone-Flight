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
