# E6 numbers: map reuse ("map once, fly again")

**Extension experiment E6, pre-registered (2026-10-31)** in `docs/thesis/tier1/e6_preregistration.md`. This file holds
the E6 numbers during the run (user ruling: they move into `numbers_tier1.md` only at merge time). Convention as
`numbers_tier1.md`: a value, its unit, a status and a source (`json:` path and key, or a run directory). Positions in
m at 4 dp, angles in °, times in s (wall times DIAGNOSTIC).

## §Guard (checksum guard, `frozen_manifest_20261022T002851.json`, 13,253 files)

| check | when | result | report |
|---|---|---|---|
| verify, before Stage 1 | 2026-10-31 21:16 AEDT, before any E6 code or run | **IDENTICAL**, exit 0 | `frozen_manifest_20261022T002851_verify_e6_stage1_pre_20261031T211642.json` |
| verify, after Stage 1b (gates) | 2026-10-31 22:31 AEDT | **IDENTICAL**, exit 0 | `frozen_manifest_20261022T002851_verify_e6_stage1b_post_20261031T223114.json` |

## §Gates

Code: branch `e6-map-reuse` at `6c0365b` (pre-registration commit), run from the worktree; 30 jobs serial under
`heavy.py`, threads 1, 2026-10-31 21:28–22:31 AEDT; all exited 0. Driver `docs/thesis/tier1/e6/stage1b_gates.sh`,
timing `docs/thesis/tier1/e6/stage1b_timing.tsv`, logs `~/thesis_data/tier1/e6/logs/`. Idle checks logged in
`~/thesis_data/tier1/e6/logs/idle.log` (the driver waited while a plot job ran).

| gate | result | detail | source |
|---|---|---|---|
| G0-UKF (flag unset) | **PASS 24/24** byte-identical | `ukf_live.tum`, `ukf_rts.tum`, 12 flights; wall 50.6–54.7 s per run | `json:scores/e6_gate_G0-UKF_G-E4p.json` |
| G-E4′ (flag unset) | **PASS 12/12** byte-identical | `fgo_live.tum`; `t_anchor`, `n_tag_factors` equal 12/12; wall 132.0–155.7 s | `json:scores/e6_gate_G0-UKF_G-E4p.json` |
| V-E6 (flag = true map) | **PASS 9/9 tracks** (3 flights × UKF live, UKF RTS, FGO live) | rows 1:1, `t_anchor` and tag count equal; UKF worst RMS in window 0.086 µm, worst max 1.414 µm (≤ 1000 / 2000 µm; the 6-dp TUM quantum); FGO byte-identical 3/3; 2,423 fixes remapped on T_A_r1, every per-tag shift 0.0 m | `json:scores/e6_gate_V-E6_T_A_r{1,2,3}.json` |
| S-E6 (scorer) | **PASS 3/3** | arms (i), (iv) reproduce the stored RMSE (expT), RMSE/max/per-lap (expL, E5) and windows; max \|diff\| 4.1e-16 m (tolerance 1e-9 m) | `json:scores/e6_gate_S-E6_T_A_r{1,2,3}.json` |

## §Maps (mapping flights and map error against truth)

(filled in Stage 1e)

## §Results

(Stage 2)

## §Deviations

(none yet)
