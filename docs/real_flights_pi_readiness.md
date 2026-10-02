# Pi readiness (real-flight plan, tooling item 2)

Status: built and checked without a Pi, 2026-10-02. [V] = done and verified here; [E] = estimate; [U] = needs a real Pi.

## 1. Cross-build of the C++ heading program for ARM64 [V]

- **Toolchain:** `g++-aarch64-linux-gnu` 13.3 (Ubuntu 24.04 package; installed 2026-10-02).
- **OpenCV:** **4.6.0** core + imgproc cross-built from the official 4.6.0 source into `~/cross/opencv-4.6.0-aarch64`.
  - OpenCV's `platforms/linux/aarch64-gnu.toolchain.cmake`.
  - Release; shared libraries; no IPP, TBB, OpenMP or OpenCL.
  - The version is pinned, because the frozen heading calibration used OpenCV 4.6's LSD.
- **Build:** `src/forward_camera/cpp/build_aarch64.sh`. It produces `cpp/aarch64/libheading.so`, the two OpenCV
  libraries (`$ORIGIN` rpath, so the folder is self-contained) and the test driver `heading_test`.
  - The flags are the same as the x86 build, including **`-ffp-contract=off`**. On aarch64, GCC fuses multiply-adds by
    default, which would change the rounding.
- **Check:** `tools/pi/heading_arm_check.py` → `eval/results/heading_aarch64_check.json`.
  - 205 frames of `fwdc_tex_r1`, every 50th frame across the whole flight including the end wall, with Phase 3 seeds.
  - The ARM64 build ran under `qemu-aarch64` against the x86 build, through the same driver (`heading_test_main.cpp`).

| result | value |
|---|---|
| integer outputs (VP found, inlier/left/right counts, valid, quality) identical | **205 of 205** |
| all outputs bit-identical | 6 of 205 |
| max \|Δψ\| | **1.25 × 10⁻⁵ °** |
| max \|Δ support\| | 9.7 × 10⁻⁵ px |

- **Reading:**
  - The ARM build makes the **same decisions on every frame** (validity, quality, counts).
  - Its heading differs from x86 by ≤ 1.25 × 10⁻⁵°. That is about 12× the 10⁻⁶° band used for the x86-vs-numpy
    equivalence (C2), and about 10⁴× below the measurement noise (σ ≈ 0.1°).
  - Most likely source: OpenCV's NEON against SSE code paths inside LSD, and libm differences. qemu-user emulates ARM
    floating point exactly, so a real Pi is expected to reproduce these ARM outputs [U: confirm with `--native`].
- **Implication:** the ARM heading is **not** bit-identical to the simulation's x86 measurement. Its effect on any
  result is far below noise, but it is stated. Real-camera validation runs on the Pi build in any case.

## 2. Still to test on a real Pi [U]

1. **Native ARM run:** `python3 tools/pi/heading_arm_check.py --native` on the Pi. This gives the same comparison plus
   the true ARM timing (median, p99).
2. **Timing under load:** the heading, flow tracker, UKF and FGO together, with cores pinned (`taskset`), under the
   thermal steady state. Measure throttling with active cooling (`vcgencmd measure_temp`, `get_throttled`).
3. **Camera capture:**
   - libcamera/V4L2 frame timestamps, using sensor timestamps rather than receipt;
   - exposure and motion blur at 0.5 m/s;
   - the rolling-shutter effect on line segments;
   - a 30 Hz sustained frame rate for both cameras together.
4. **Serial link to the FC:**
   - 921 600 baud on a dedicated port;
   - a sustained 333 Hz `HIGHRES_IMU` with no drops, plus `OPTICAL_FLOW`, heading `ODOMETRY` and the route-1 state
     stream;
   - the measured round-trip latency, the D25 clock map's settle time and drift on real crystals.
5. **Python stack:** ARM64 wheels for Python 3.12 exist at the exact versions used (checked against PyPI, 2026-10-02):
   gtsam 4.2.1, opencv-python-headless 4.6.0.66, numpy 1.26.4, rosbags. ROS 2 Jazzy has Tier-1 support on Ubuntu 24.04
   arm64. Still to do: install them and run the offline replays on a Pi (same results as x86 within float tolerance).
6. **Python heading against C++ on ARM:** the bridge uses the C++ build by default. Re-run the Python ↔ C++
   equivalence there.

## 3. Compute budget: heading + UKF + FGO (+ flow) on a Pi 4 / Pi 5 [E unless marked]

The Pi factors are typical single-thread ratios against the i7-8700: Pi 4 (Cortex-A72) about 3–5× slower, Pi 5
(Cortex-A76) about 1.5–2.5× slower (Part C §6.5; not measured [U]).

| Workload (period) | i7-8700 measured [V] | Pi 4 [E] | Pi 5 [E] | Fits? |
|---|---|---|---|---|
| Heading, C++ (133 ms at 7.5 Hz) | 15.3 ms median (p99 20.4) | 46–77 ms | 23–38 ms | yes on both, at 7.5 Hz |
| UKF, Python, predict (12.5 ms) | 1.5–1.6 ms (+ updates) | 4.5–8 ms (36–64% of a core) | 2.3–4 ms | yes; Pi 4 tight |
| FGO node, Python GTSAM (33 ms keyframes) | median 28.4, p95 53.1, p99 58.7 ms (with heading) | 85–140 ms | 43–71 ms | **no, on either** |
| Flow tracker, Python (33 ms) | [U on x86 under the node; to measure] | [U] | [U] | to measure |

- **The FGO is the only workload that does not fit.** Options:
  - **(a) The D11 speed-up:** a C++ GTSAM node with analytic Jacobians. The Python `CustomFactor` with
    central-difference Jacobians dominates now. Expected 5–15× faster [E, Part C §5.4], i.e. ~2–6 ms on the i7 and
    ~6–30 ms on a Pi 4: fits at 30 Hz. Effort: about 1–2 person-weeks for factors, node and equivalence tests [E].
    - **The equivalence against the Python FGO must be re-run** (the FG1-type checks), since that is what the
      simulation results used.
  - **(b) A lower keyframe rate** (e.g. 10 Hz → a 100 ms budget): fits a Pi 5 at the measured per-step cost. But it
    **changes the estimator** relative to every simulation result (window contents, IMU preintegration span), and would
    need its own simulation check.
  - **(c) No real-time FGO:** in shadow flights (route 3), log every input on the Pi and run the FGO after the flight.
    It cannot then be claimed to run onboard in real time.
- **Cores:** with 4 cores, one each for the heading program, flow, UKF and FGO; ROS and logging share. Active cooling
  is required.

## 4. Files

- `src/forward_camera/cpp/build_aarch64.sh`: the cross-build.
- `src/forward_camera/cpp/heading_test_main.cpp`: the test driver.
- `tools/pi/heading_arm_check.py`: the x86 against ARM64 check.
- `eval/results/heading_aarch64_check.json`: its result.
- Build outputs (untracked; rebuild with the scripts): `cpp/aarch64/`, `cpp/heading_test_x86`, `cpp/libheading.so`.
- x86 driver build: `cd src/forward_camera/cpp && ./build.sh && g++ -O2 -std=c++17 -ffp-contract=off -o heading_test_x86 heading_test_main.cpp -L. -lheading -Wl,-rpath,'$ORIGIN'`.
