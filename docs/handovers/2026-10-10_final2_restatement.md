# Handover, 2026-10-10: FGO-only re-run restated (flags classified, numbers.md, claims table, 0.1 rad check)

**Stage:** analysis and doc editing only. No replays, no heavy jobs, no estimator or METHODOLOGY edits. Worktree branch
reset to `fwd-camera` `819caab` at the start (it had been made from the unrelated root). Inputs: OLD =
`~/thesis_ws/eval/results_pre_final2` (first final re-run, FGO with 1e-3 rad initial yaw; read by absolute path, untracked,
no symlink), NEW = `eval/results`, raw comparison `eval/results/final2_old_vs_new.md` (1272 rows, 12 DIRECTION flags).

## 1. The 12 DIRECTION flags (checked against the JSONs)

| # | flag | old → new | class | evidence |
|---|---|---|---|---|
| 1–3 | §8 `fwdc_trans_r3`, `fwdplainc_trans_r2`, `fwdplainc_trans_r3` verdict PASS → FAIL ("P4 FGO ratio") | ratios 19.876 / 20.75 / 21.64 | **ARTEFACT** (formula-faithful) | `rerun_p4_bands.json`: the FGO transition band is built from the three `dsn` FGO runaway ratios, which went 30.0 / 17.3 / 33.2 → 18.0 / 18.1 / 17.0, so the band shrank [1.406, 49.073] → [15.908, 19.159]. The fwd ratios are runaway sizes (†, not BLAS-reproducible), spread 16.4–21.6. Counts: `fwdc` 8/9 → 7/9, `fwdplainc` 9/9 → 7/9 (`p1c` 6/6). |
| 4 | P4 `fwdc` trans FGO heading arm effect −17.47 → +19.40 | 609 − 627 → 606 − 587 m | **MEANINGLESS** | difference of two diverged (~600 m) values |
| 5 | P4 `fwdplainc` tex FGO heading arm effect +38.53 → −4.44 | | **REAL** | divergence gone: heading arm 43.1 → 0.16 m mean |
| 6 | P4 `fwdplainc` tex FGO_heading − EKF3 +39.04 → −3.92 | | **REAL** | same cause |
| 7 | P4 `fwdplainc` trans FGO heading arm effect −579 → +11 | | **MEANINGLESS** (sign) | both arms run away. Underlying: textured-half yaw divergence gone (onset 19–22 m → 94 m, as the UKF); the heading arm now runs away on the blank half (43 → 638 m mean), like the baseline. The old 43 m was the yaw-spinning divergent FGO |
| 8 | P4 `fwdplainc` blank FGO heading arm effect +1337 → −1822 | | **MEANINGLESS** | km-scale runaways |
| 9 | P5 end wall, `fwdplainc` FGO_heading wrong (> 3°) headings fused 0/48 → 2/48 | | **REAL (small)** | `phase5_analysis.json`: one each on `fwdplainc_trans_r1` (max 4.30°) and `trans_r3` (4.21°). The old 0 came from the lockout (FGO fused ~20 headings per bag). UKF 0/48 |
| 10 | P5b end-wall yaw-prediction NEES `fwdplainc/FGO` 6,486,370 → 2.99 | | **REAL** (old value meaningless) | the old value was the divergence; new 2.99 vs UKF 3.02 (the flag is the side of 3; both sit at it) |
| 11 | F3c `fwdc_tex_r3` ratio_decreasing no → yes | ratios 0.147 / 0.165 → 0.250 / 0.100 | **REAL by the rule, FRAGILE** | FGO integrals 0.32 / 0.34 → 0.55 / 0.21 m·s vs UKF ~2.2 / 2.0 m·s |
| 12 | F3c `b_advantage_grows` no → yes | | **REAL by the rule, FRAGILE** (verdict flip) | follows from #11 (needs ≥ 2/3: now r2, r3). Reverses the TRUE → FALSE flip accepted under ruling 4 |

**Counts:** real 6 (of which 2 fragile), artefact 3, meaningless 3.

**Plain-wall FGO with heading (all six bags):** the divergence is GONE.
- Textured r1–r3: evo 0.150 / 0.094 / 0.221 m (UKF 0.188 / 0.151 / 0.250); yaw rms 3.41 / 3.38 / 3.07°; yaw max 5.03 /
  4.94 / 4.59°; headings fused 747 / 647 / 778 (UKF 752 / 653 / 781); bias −8.0 / −8.4 / −7.6 deg/min (= UKF).
- Transition r1–r3: yaw rms 1.56 / 3.65 / 1.83°; yaw max 3.91 / 6.24 / 4.16°; fused 5,911 / 3,582 / 5,471 (UKF 5,968 /
  3,612 / 5,517). Position 640 / 717 / 557 m: the blank-half runaway, as the FGO baseline (547–682 m).
- Yaw max taken from the sensitivity file's 1° column after checking all 28 of its 1° evo values equal the pipeline's
  stored values (0 mismatches; the two `dsn` rows have no Phase 4 counterpart).
- **C0 reverses back:** FGO lower on 3/3 `fwdplainc` (margin 0.03–0.06 m), so 6/6 overall, the original wording.

**Unflagged changes that alter prose** (all restated): FGO_hard lockout total 23 → 61 (8–18 per plain-wall flight vs
UKF 1–2; cause untraced); F1 FGO_hard plain-wall yaw max 180° → 4.6–5.0°; FGO +heading `fwdplainc` NEES 24.8 → 13.95
(UKF 13.41); checker gate acceptance FGO 0.4 → 11.6 % (UKF 11.5 %); contact median 162.9 → 163.2 s; `dsn` transition FGO
ratio 26.8 → 17.7; noise floor FGO SD 1.23 → 1.30, d 0.96 → 1.02; FGO median r1–r9 4.45 → 4.46; T condition D FGO
0.082 → 0.083; L no-LC live 0.281–0.362 → 0.262–0.361 m, lap ratio 3.0–5.0 → 2.9–4.5; O FGO batch unchanged (< 0.001 m).

## 2. `docs/thesis/numbers.md`
- **47 rows restated** plus the header note; every replaced row is kept verbatim in a new last block, "Superseded by the
  FGO-only re-run (2026-10-10): FGO rows of the first final re-run (FGO with 1e-3 rad initial yaw)".
- Sections: §2 (clock shift FGO), §6.1 (FGO r1–r3, mean/range, confirmatory test with the new d values, noise floor,
  D15 wording median, FGO drift, textured standing), §6.2, §6.4, §6.6 (plain-wall rows, divergence row → RESOLVED with
  the direct trace, C0, claim wording, NEES), §7 bands, §8 counts (7/9, 7/9, "wording awaits a ruling"), §15 contact
  median and an old-priors note in the §15 header, §15.1 (S1 values, lockout totals, conclusion), §15.2 (F1, F3c),
  §16.1 (D, P-T3), §16.2 (O step, batch row, WITHDRAWN bullet re-worded, partial-attribution bullet), §16.3 (no-LC row,
  L/V-L note), flags (noise floor).
- **New §18** "Attribution, the FGO initial-uncertainty correction, and the 0.1 rad sensitivity check": the joint
  wording; the plain-wall direct trace; the O partial attribution (~93 % / ~7 % / +0.03 m; yaw cap +0.22–0.30 m on the
  live track), stated as computed on the PRE-initial-yaw code (`b7a3aca`); "about 2× better" withdrawn as largely an
  artefact of the mis-specified noise model; the 2.5 m `dsn_tex_r2` mismatch caused by the jitter fix (by elimination);
  the unanswered list; the confirmatory test "no ordering claimed" (mean −0.021, CI [−0.989, +0.947]); the initial σ
  values; the sensitivity result.
- The header now notes that the flown FGO results (S3, `_v3`, the FGO safety tests) and the installed C++ binary used
  the OLD priors.
- Not restated (no change at printed precision): §5 thresholds, §6.5 FGO scale, `fwdc` heading arms, F2, F3, F3b, H, O
  live indoor/return, T A–C.

## 3. 0.1 rad sensitivity (`eval/results/sensitivity_yaw0_0p1/`)
- `fwdc_tex_r1` heading arms unchanged (0.127 / 0.057 m); baselines move ≤ 0.05 m; `dsn_tex_r1` UKF 3.98 → 3.67, FGO
  4.05 → 3.78 m (order unchanged; inside the FGO noise floor).
- `fwdplainc_tex` heading arms, UKF / FGO: r1 0.19 / 0.15 → 0.21 / 0.17 m (fused 752 → 3,961); r2 0.15 / 0.09 → 0.75 /
  0.73 m (yaw max 4.9 → 14.5°); **r3 0.25 / 0.22 → 5.705 / 5.695 m** (yaw max 4.6 → 61.3°; fused 781 → 232), worse
  than the FGO's own baseline (4.85 m). Transition values are runaway sizes (†).
- **Verdict:** no UKF-vs-FGO ordering changes, and `fwdc`/`dsn` conclusions stand. **One conclusion changes:**
  "heading fusion bounds plain-wall position" holds at the shared 1° initial yaw but not at 0.1 rad on r3, for both
  estimators together (gate lockout depends on the initial σ).

## 4. Claims table (`docs/thesis/headline_claims_before_after.md`)
- **HOLDS 17 · CHANGED 16 · WITHDRAWN 3 · PENDING 0** (36 rows; counted by regex).
- Row 8 (plain-wall divergence) PENDING → WITHDRAWN (a D18 model error, corrected). Row 22 (O batch) PENDING → CHANGED
  (partial attribution). Row 7 (C0) → HOLDS (back to 6/6). Row 31 (F3c (b)) → HOLDS against the original (TRUE again).
- UKF textured standing: mean r1–r3 FGO 3.44 < UKF 3.59 < EKF3 4.00; median r1–r9 UKF 5.13 > FGO 4.46 > EKF3 4.10.
- **L:** the L FGO changed (V-L start takes the corrected yaw σ), but all four L verdicts PASS 3/3; L's result HOLDS.

## 5. Questions for a user ruling (verdict flips only)
1. **§8 counts** `fwdc` 7/9 and `fwdplainc` 7/9 (were 8/9, 9/9): the three new misses are FGO transition ratios outside
   a band that collapsed to [15.908, 19.159] because the three `dsn` runaway ratios happened to agree. Report as
   computed with an artefact note (as drafted), or treat as not informative like the textured band (ruling 3)?
2. **F3c (b) FALSE → TRUE** (as computed), reversing the flip accepted under ruling 4; fragile (r3 integrals 0.2–0.5
   m·s).
3. **C0 back to "FGO lower on all 6"** (plain-wall margin 0.03–0.06 m), replacing the 1st re-run's "UKF lower on
   `fwdplainc`".

**For the daily summary (no ruling needed now):** the FGO_hard lockout rise 23 → 61 (cause untraced; the FGO_hard now
equals the UKF in yaw); the end-wall 2/48 wrong headings fused (UKF 0/48); the 0.1 rad r3 result (plain-wall heading
benefit not robust to the initial yaw σ); the stale "13–26 vs 49–91" S1 parenthetical, which predates the final re-run.

## State
- No flight running at commit (`pgrep -fa '[a]rducopter'` empty; no `~/thesis_data/FLIGHT_LOCK`).
- Committed on the worktree branch; not merged. Scratch scripts (`p4.py`, `x1.py`–`x3.py`, `restate.py`) are in this
  session's scratchpad and are not committed.
