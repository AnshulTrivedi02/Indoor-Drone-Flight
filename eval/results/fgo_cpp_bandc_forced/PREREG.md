# Band C with the yaw-cap gate decisions forced: PRE-REGISTRATION (written and committed BEFORE any forced run)

Ruling: METHODOLOGY "RULINGS (user, 2026-10-11): Band C; UKF safety (b) S-A2; records", item 1 (option (ii)).
Stage branch `worktree-agent-a77df11041902ee58`, based on `fwd-camera` `b908abf`. Verification only; not result data.

## What is already done (before this file)
- The switch (commit `2610bdb`): CMake option `FGO_CPP_FORCED_GATE`, **OFF by default**. With it ON (and only then),
  the yaw-cap gate decision at keyframe k is read from a recorded Python gate log (env `FGO_CPP_FORCED_GATE_LOG`,
  rows t, k, trace, fired) instead of `trace > 0.04`. The trace is still computed and logged. It aborts if the variable
  is unset or a check falls on a keyframe that the Python log never checked.
- Switch-OFF byte-identity: `ident_switch_off.txt` (all outputs of the OFF build byte-identical to the 2d build's, on
  the four Band C bags and L1; timing fields excluded). The OFF build's replay / front end / live replay / probe
  binaries are byte-identical to the 2d build (`0981e455`, `ed058257`, `9e4648b0`, `9511c13a`); the node `8c116954`
  differs from `28636bf9` only in the embedded worktree path string and the GNU build-id (`md5_builds.txt`).

## The forced-decision comparison (fixed now, before seeing any number)
- **Build:** this branch's source, `-DFGO_CPP_FORCED_GATE=ON -DFGO_CPP_BUILD_ROS=OFF`, Release, scratch only
  (`scripts/step.sh build_forced`). Never installed.
- **Bags (the Band C set of the 2d install gate):** `dsn_tex_r1` baseline, `fwdc_tex_r1` heading, `T_A_r1`,
  `T_D_r1`. Inputs are the 2d stage's Python exports (`d18/dump`, read only; sha256 below).
- **Forcing:** BOTH the export-driven C++ replay (`fgo_cpp_replay`) and the native front end (`fgo_cpp_frontend`)
  follow the Python replay's own gate log for that bag (`<prefix>.yawgate.f64`, exported by `fgo_replay.py` /
  `room_fgo_replay.py` in the 2d stage).
- **Comparison:** `compare_kf.py <forced replay> <forced front end>` (all rows, as in 2d band C), i.e. band C with
  the decisions forced equal.

### PASS rule (all must hold; any failure = FAIL: stop, report, do NOT install, do NOT fly)
1. **max |Δp| ≤ 1 mm on every Band C bag** (the ruling's criterion; per-keyframe position, forced replay vs forced
   front end).
2. **The forced decisions equal Python's, by construction, and checked:** for every forced run (replay and front end,
   all four bags) `construct_check.py` PASSES: same number of checks, identical keyframe-index sequence, identical
   fired flags.
3. The band's standing conditions (2026-10-09 definition, as in the 2d INSTALL_GATE): same keyframe count and
   |Δyaw| ≤ 0.01° on every bag. Factor-decision mismatches (flow / range / heading / tag / GNSS flags) are reported;
   any nonzero count is a FAIL.

### Switch validity control (required; a failure means the switch is defective: FAIL)
- On each bag the 2d run showed 0 Python–C++ gate mismatches for the export-driven replay, so forcing it to Python's
  decisions must change nothing: the forced replay's `kf.f64` must be **byte-identical** to the unforced 2d
  `cpp_<prefix>.kf.f64` (sha256 below).

### Reported, not pass criteria
- The number of decisions the forcing overrides (C++ trace on the other side of 0.04) per run; the first |Δp| > 1e-9 m
  onset; the batch bands for the room bags; p99 |Δp|.

## Inputs (sha256, `d18/dump`)
```
3f44f0a05ba26486abed929e568bfb08c2e61cb4136e71a04610d099f847d9e2  dsn_tex_r1_baseline.init.json
07d9bb27a3848dde40abe472bc56763fbdc95d7e44c9aa97619f090b9e62cf9a  dsn_tex_r1_baseline.events.f64
543a379bfb35ccf4509295a438d4929182d1a3cbb687929c2e9b5794f0633f40  dsn_tex_r1_baseline.raw.f64
4edb8e5c7fa28867fb7105ac6ee7152d1e3387ce58db03b425a605ddb6c038a9  dsn_tex_r1_baseline.yawgate.f64
e9ff3046b713c175b79f5eb83485e4a7889d5ded27e3d457271d54b5c5847d72  fwdc_tex_r1_heading.init.json
a00c7a4458cf28707a65194915c0dfffa50b000f0e3893cab41801e89217ea1f  fwdc_tex_r1_heading.events.f64
5af92df12839e77fb537c0df9ad39140f37a3a53118148aa4394ce0aa9eb8d77  fwdc_tex_r1_heading.raw.f64
0f5cac2243c79838d185551731f57d9611a82ee6edb94f3a37149ce5d7787337  fwdc_tex_r1_heading.yawgate.f64
573b084f75b49f7fe3b92288c5b9f208641986a74755f6da41ae7654beecc28c  T_A_r1.init.json
e40c0660238cab86f7739791ecaa5387d71fce571dd6db3e5f703871309d80ec  T_A_r1.events.f64
e71e6e782f3576ff54cd089d38d3fce8e30d1d853ac0288e640b88ab261f26d8  T_A_r1.raw.f64
8b28ebb05cb3827c0b9c0f7616b4cd0358c2309650bcacbc0ae85d76ac717f17  T_A_r1.yawgate.f64
d4dbb94b01ab0361fe3ac243a3fe724a0201e77fae355be176493dfe7ff574b9  T_D_r1.init.json
918eb30b6d7543e81c47f8ce6d765bdc9fdf80da34f5d4ca4aa9b322169f59ac  T_D_r1.events.f64
44a1de6ad435092e5a2ef5fdd847a3efe0ecc3f4a82dcf15e56687b7eb93ab7c  T_D_r1.raw.f64
31d86c0c483e6bf74b6cef2d337a90b33597a741df9de72f34e5ffa0ffa8ced7  T_D_r1.yawgate.f64
f13c3b9c5c61ba790c0d89c350a05987fdb60d4f133dbda7415cc2c25289adea  cpp_dsn_tex_r1_baseline.kf.f64
662b01443de42c971200c185755b739412ddbf00ab80529bf1a7098401754740  cpp_fwdc_tex_r1_heading.kf.f64
8d957b7232ef6bca69e0cfe842c206b64e1e684d7d902fb0b5630722f8d54954  cpp_T_A_r1.kf.f64
4f9a7eac46706918cc5e6df991b35f1feaab113f3b002436a7650c86d700ef6b  cpp_T_D_r1.kf.f64
```

## If it PASSES
Install the switch-OFF build (default cmake line, no `FGO_CPP_FORCED_GATE`) to `~/opt/fgo_cpp` by the established
recipe: back up the old binaries first (old node `f642cd37…`), new acceptance set in a NEW directory, replay / live
`cmp` acceptance; then fly `H_safety_fgo_a_v4` / `H_safety_fgo_b_v4` (`tools/run_fgo_refly.sh sa4 sb4`), scored with
`eval/h_safety_score.py --from-effect --a2-bound 0.75` against S-A1–S-A4 as worded, plus the supplementary S-A2b
(pre-registered 2026-10-11: trigger time from the last flow message received by the FC, bound 5.5 s) for (b).
