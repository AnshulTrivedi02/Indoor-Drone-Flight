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
| verify, after Stage 1c (verification flight) | 2026-10-31 22:38 AEDT | **IDENTICAL**, exit 0 | `frozen_manifest_20261022T002851_verify_e6_stage1c_post_20261031T2238.json` |
| verify, after Stage 1d/1e (mapping flights, map replays) | 2026-10-31 23:10 AEDT | **IDENTICAL**, exit 0 | `frozen_manifest_20261022T002851_verify_e6_stage1e_post_20261031T2310.json` |

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

## §Flights (Stage 1c, 1d; `docs/thesis/tier1/e6/flights.log`)

Flown 2026-10-31 22:32–22:56 AEDT through `e6_flight.sh` / `fly_queue.sh` (FLIGHT_LOCK, batch state under
`~/thesis_data/tier1/e6/batches`, idle check before each flight logged). All landed, run_trial exit 0.

| trial | role | route | wall | IMU gap check | route / coverage (V-F rule) | used |
|---|---|---|---|---|---|---|
| `E6V_fig8_check` | verification (NOT result data) | 1 circuit, 72 s | 139 s | ok | PASS: cross-track at mid-leg ≤ 0.022 m; central detections per tag 15–93 | gate V-F only |
| `E6M_fig8_r1` | mapping | 3 circuits, 216 s | 4 min 58 s | **unusable** (receipt bunch at stream start, 8.5 s stationary before arming < 10 s) | not checked | **no** (D83; kept) |
| `E6M_fig8_r1b` | mapping (re-fly of r1) | 3 circuits | 5 min 24 s incl. queue | ok | PASS, every tag ≥ 31 central detections in every circuit | → T_A_r1 |
| `E6M_fig8_r2` | mapping | 3 circuits | 4 min 57 s | ok | PASS (tag 5: 14–39 per circuit, the fewest) | → T_A_r2 |
| `E6M_fig8_r3` | mapping | 3 circuits | 4 min 57 s | ok | PASS (tag 5: 16–39 per circuit) | → T_A_r3 |

Sources: `json:scores/e6_gate_V-F_E6V_fig8_check.json`, `json:scores/e6_route_E6M_fig8_r{1b,2,3}.json`,
`~/thesis_data/trials/<trial>/imu_gaps.json`.

## §Maps (Stage 1e: map replays and map error against truth)

Map replays serial under `heavy.py`, 2026-10-31 22:57–23:09 AEDT (`docs/thesis/tier1/e6/stage1e_timing.tsv`): LC FGO
114.5–116.4 s per run, exit 0, 0 keyframe failures; landmark UKF 110.1–111.8 s, exit 3 by design (D75, reason "no
stored FGO stats"; Cholesky retries 0). **MAP-INV PASS 3/3:** `t_anchor` 28.744 s in both replays and from `/tags/raw`;
8 landmarks in both; FGO index → tag mapping equal to the UKF's; tag measurements used FGO = UKF (1819 / 1701 / 1795).
Map files (world frame): `~/thesis_data/tier1/e6/maps/<m>/`, copies in `docs/thesis/tier1/e6/maps/<m>/`.

Landmark error against the surveyed map, 7 non-gauge tags (status CURRENT; source `json:e6/maps/<m>/map_errors.json:
errors.{fgo,ukf}`):

| mapping flight | map | position RMS (m) | max (m) | mean (m) | yaw RMS (°) | yaw max (°) | UKF ÷ FGO (position RMS) |
|---|---|---|---|---|---|---|---|
| E6M_fig8_r1b | FGO (a) | 0.0455 | 0.0677 | 0.0412 | 0.257 | 0.303 | 0.98 |
| E6M_fig8_r1b | UKF (b) | 0.0448 | 0.0590 | 0.0434 | 0.266 | 0.331 | |
| E6M_fig8_r2 | FGO (a) | 0.0342 | 0.0533 | 0.0310 | 0.178 | 0.221 | 1.17 |
| E6M_fig8_r2 | UKF (b) | 0.0401 | 0.0527 | 0.0387 | 0.162 | 0.208 | |
| E6M_fig8_r3 | FGO (a) | 0.0275 | 0.0369 | 0.0268 | 0.159 | 0.177 | 1.73 |
| E6M_fig8_r3 | UKF (b) | 0.0476 | 0.0568 | 0.0472 | 0.185 | 0.263 | |

- **P1 inputs are complete** (all three mapping flights). Mechanical reading on the unrounded values: FGO < UKF on
  r2 (0.03421 < 0.04005) and r3 (0.02746 < 0.04758), NOT on r1b (0.04553 > 0.04480). As worded (3/3) that reads
  **FAIL**; the formal verdict is written by `eval/e6_verdicts.py` in Stage 2 (pre-registered there, D82).
- **Descriptive, not diagnosed:** the yaw error has the same sign on every tag of a flight (+0.10…+0.30°) and the
  out-of-sample maps are worse than the in-sample T_A maps (FGO 0.0275–0.0455 m against 0.0152–0.0269 m; yaw RMS 0.16–0.27° against ≤ 0.08°; §1.4 of the
  pre-registration). A common rotation of the map about tag 0 would show this signature. No verdict depends on the
  cause and none is claimed (rule 4).

## §Results

(Stage 2)

## §Deviations

(none yet)
