# Item 2f: the C++ FGO on ARM64, cross-built and run under emulation (2026-10-11)

This is VERIFICATION, not result data. The pre-statement was written before any qemu run: `PRE_STATEMENT.md`.

## Toolchain (nothing installed by this stage)
- **Cross compiler:** `g++-aarch64-linux-gnu` 13.3, already installed on 2026-10-02 for the heading build.
- **Emulator:** `qemu-aarch64` 8.2.2 (user mode), with binfmt registered.
- **Docker/podman:** not used and not needed.
- **Boost 1.83 arm64** (`1.83.0-2.1ubuntu3.2`, the host x86 version):
  - 21 Ubuntu noble debs fetched from ports.ubuntu.com;
  - unpacked with `dpkg-deb -x` into a scratch sysroot (no apt, no sudo);
  - sha256 in `boost_arm64_debs.sha256`.

## Build (`scripts/step.sh`, `scripts/aarch64.toolchain.cmake`, each step through `heavy.py`)
- **GTSAM 4.2.1:**
  - The same source tree as the x86 build (`~/opt/src/gtsam-4.2.1`).
  - The same flags as `~/opt/src/configure_gtsam.sh`: Release `-O3`, no TBB, bundled Eigen 3.3.7, no
    `-march=native`, unstable on, no Python, tests or examples.
  - **Plus `-ffp-contract=off`.**
  - Installed to scratch `arm64/gtsam-4.2.1`.
  - libgtsam md5 `d2b9039d…`, libgtsam_unstable `d31b08b8…`, libmetis-gtsam `10350ada…`. The libraries total 9.4 MB.
- **fgo_cpp:**
  - Built from this worktree's source, which is identical to `cca8e90`, the source of the 2d x86 scratch build.
  - `-DFGO_CPP_BUILD_ROS=OFF -DCMAKE_SKIP_RPATH=ON`, with `GTSAM_DIR` pointed at the arm prefix.
  - md5s: replay `d86da22e…`, live_replay `667e820a…`, frontend `68c7d11e…`, probe `50bb2b17…`.
  - **`fgo_cpp_node` was NOT built:** there is no ROS 2 Jazzy arm64 here.
- **Checks** (`build_inspect.txt`):
  - all objects are ELF aarch64, with no RPATH/RUNPATH;
  - the CMake cache shows GTSAM taken from the arm prefix;
  - **no scalar FMA** was emitted (the `-ffp-contract=off` effect).
  - **Vector `fmla`/`fmls` remain** (about 11.7k in libgtsam). These are Eigen's explicit NEON `pmadd` intrinsics,
    which the flag does not affect.

## Emulated correctness against the x86 scratch build of 2d (replay `0981e455`; node `28636bf9`)
| check | result |
|---|---|
| probe: every factor `[A\|b]` (flow, range, yaw, heading, yaw-rate, tag, GNSS), R, yaw, rpy | **bit-identical** to the x86 C++ |
| probe: preintegration (ΔR, Δp, Δv, cov), retract, predict | differ at the last bit: rel ≤ 2e-16 (cov 7.7e-13) |
| probe: keyframe solves kf1–kf4, gate3/gate4 | rel ≤ 1.4e-9 / 2.5e-11 |
| dsn_tex_r1_baseline (whole flight, 10197 kf) | count and every decision flag identical; **0/2039 gate decision mismatches** (63/63 fired); max / p99 \|Δp\| **0.074 / 0.0083 mm**, max \|Δyaw\| 4.3e-5° |
| fwdc_tex_r1_heading (whole flight, 10118 kf; heading 9184 accepted) | identical decisions; 0/2023 gate mismatches; max \|Δp\| **1.3e-4 mm**, \|Δyaw\| 3e-10° |
| the same runs against the Python export | dsn_tex max \|Δp\| 0.205 mm, fwdc 1.3e-4 mm (inside the 1 mm / 0.01° band) |

- **dsn_tex is the band A/C bag.** Its closest yaw-cap check came within 2.4e-6 of the 0.04 threshold
  (t = 84.6 s), and the arm64 trace differed from x86 by up to 5.97e-6 (rel 1.5e-4). **This run did not flip, but the
  tie mechanism of band C applies to ARM as well:** a different bag or segment could flip a decision.
  This is stated, not tested further.
- **Cause of the residual:** most likely Eigen NEON against SSE2 (reduction order and fused vector multiply-add) and
  libm. qemu-user emulates aarch64 FP exactly, so a real Pi should reproduce these arm64 outputs [U].

## Timing
- **qemu (RELATIVE ONLY):** arm64 under qemu runs at a median of 22.0 / 28.3 ms per keyframe (dsn_tex / fwdc), which
  is 42× / 31× the x86 run.
  - The slowdown differs by workload, which shows that qemu time does not predict Pi time.
  - Peak RSS under qemu was 42.9 / 47.9 MB, including the emulator: an upper bound only.
- **Pi estimate:** ESTIMATED, not measured (`pi_estimate.txt`, `scripts/pi_estimate.py`). It uses the x86 step times
  × the Geekbench 6 single-core ratios in `docs/fgo_cpp_port.md`: Pi 5 1.9–2.0×, Pi 4 4.5–5.2×.

| case (x86 median / p99) | Pi 5 median / p99 | Pi 4 median / p99 | budget |
|---|---|---|---|
| dsn_tex replay (0.53 / 0.92 ms) | 1.0–1.1 / 1.8 ms | 2.4–2.7 / 4.1–4.8 ms | 33 ms |
| fwdc heading replay (0.91 / 1.68 ms), the worst case | 1.7–1.8 / 3.2–3.4 ms | 4.1–4.7 / 7.5–8.7 ms | 33 ms |
| live L2 heading (0.96 / 1.69 ms) | 1.8–1.9 / 3.2–3.4 ms | 4.3–5.0 / 7.6–8.8 ms | 33 ms |
| worst single spike seen, 12.9 ms | ~25 ms | **~58–67 ms (over budget once)** | 33 ms |

- **Reading:** the p99 fits the 33 ms keyframe on both boards, with a margin of about 4× on a Pi 4 and about 10× on a
  Pi 5.
  - A rare Pi 4 spike would exceed one keyframe. The live node must tolerate a late keyframe, and the stage-3
    self-stop is on p99 over 2 s, not on a single spike.
  - Caveats:
    - Geekbench is a composite and not this workload;
    - the x86 medians varied ±40% with load;
    - NEON may help ARM relative to the generic x86-64 build (no AVX);
    - thermal throttling is not included.
