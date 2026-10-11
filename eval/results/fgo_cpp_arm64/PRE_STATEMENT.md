# Item 2f: arm64 FGO build, emulated check: what is compared (written BEFORE any qemu run, 2026-10-11)

VERIFICATION only (ruling 2026-10-11, item 2f). Nothing here is result data. There is no pass/fail band, because
bit-identity across architectures is not expected. The comparison is stated in advance so it cannot be read as
tuned after the fact.

- **Reference:** the x86 C++ outputs of item 2d (scratch build replay md5 `0981e455…`, probe `9511c13a…`; node
  `28636bf9…`, built from `cca8e90`; `git diff cca8e90 HEAD -- src/estimators` is empty). Files are
  `d18/dump/cpp_<p>.{kf,yawgate,step_ns}` and `probe_cpp.txt`.
- **Test:** the aarch64 cross-build of the same source. GTSAM 4.2.1 uses the same flags as the x86 build, plus
  `-ffp-contract=off` for GTSAM and fgo_cpp. Boost 1.83 is the same Ubuntu version (arm64 debs, unpacked with
  dpkg-deb, not installed). It runs under `qemu-aarch64` 8.2.2 user mode.
- **Runs, in order:**
  1. The probe, compared line by line with the x86 C++ probe.
  2. `dsn_tex_r1_baseline`, the whole flight (the band A/C bag).
  3. `fwdc_tex_r1_heading`, the whole flight (gate recursion every keyframe).
  - blank and trans are not run, because the Python FGO itself diverges on them.
- **Reported, per run:**
  - the keyframe count and the decision-flag mismatches;
  - whether the export is bit-identical;
  - the yaw-cap gate decision mismatches;
  - the max and p99 |Δp| and max |Δyaw|, **before the first gate decision mismatch and over the whole run,
    separately**. A threshold tie at 0.04 (as in band C, 2d) flips decisions on 1e-13-level differences, so a
    post-flip number is not an architecture difference in itself.
- **Expected remaining differences (not removed):**
  - bundled Eigen 3.3.7 uses NEON on aarch64 and SSE2 on x86-64, which changes the reduction orders;
  - aarch64 against x86 glibc libm.
  - qemu-user emulates the aarch64 FP exactly, so a real Pi should reproduce the emulated arm64 outputs
    (to be confirmed natively).
- **Timing:** the qemu step times are a RELATIVE measure only (the emulation slowdown). The Pi numbers are ESTIMATES
  from the x86 step times, scaled by the Geekbench 6 single-core ratios already cited in `docs/fgo_cpp_port.md`
  (Pi 5 ≈ 1.9–2.0×, Pi 4 ≈ 4.5–5.2×).
