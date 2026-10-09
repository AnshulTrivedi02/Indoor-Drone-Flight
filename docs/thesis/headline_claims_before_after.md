# Headline claims: before vs after the final consolidated re-run (2026-10-10)

"Before" is the claim as stated up to `07f9f56` (old FGO noise model; pre-correction UKF). "After" is the final re-run
(`eval/results/` at `425e824`, restated in `docs/thesis/numbers.md`). EKF3 is unchanged (9 hard gates, 0 differences).
Rulings: METHODOLOGY "RULINGS (user, 2026-10-10)". Old → new detail: `docs/thesis/final_restatement_draft.md`,
`eval/results/final_old_vs_new.md`. **Status:** HOLDS (claim stands as worded) · CHANGED (stands only re-worded, or the
verdict flipped) · WITHDRAWN (no longer made) · PENDING (awaiting the plain-wall trace or the attribution study).
Which correction causes a change is not yet attributed (attribution study running). evo = evo -a (cruise), m.

| # | claim before | status | evidence now |
|---|---|---|---|
| 1 | **Corridor ranking, textured `dsn`:** the UKF is the worst textured estimator (median r1–r9 5.34 m, above EKF3 4.10 and FGO 4.61) | CHANGED | `rerun_dsn_evo.json`: **mean of r1–r3 FGO 3.49 < UKF 3.59 < EKF3 4.00, so on r1–r3 the UKF is NOT last** (old r1–r3: UKF 3.91 < EKF3 4.00 < FGO 4.64). With `dsn_extra_evo.json`, median r1–r9: UKF 5.13 > FGO 4.45 > EKF3 4.10, so the UKF is still highest by median and on 6/9 flights. Both FGO and UKF are bimodal (low on r2, r6). Descriptive; no ordering claimed |
| 2 | **EKF3 beats the FGO on standard sensors** (confirmatory: "EKF3 lower", 6/7, d −0.69 m, CI [−1.16, −0.21]) | WITHDRAWN | `dsn_paired_test.json`, same rule: **"no ordering claimed"**, 5/7, d −0.040 m, CI [−0.934, +0.853]; driven by r6 (FGO 1.43 vs EKF3 3.11). The old verdict used the mis-specified FGO noise model (ruling 2) |
| 3 | The FGO is the "tight" textured estimator (noise-floor SD 0.05–0.13 m) | CHANGED | FGO SD **1.23 m** [0.83, 2.36] (n = 9); EKF3 0.31 (unchanged) |
| 4 | **Camera heading measurement** (Phase 3): heading valid on `fwdc` 9/9, `fwdplainc` 6/9 (checker floor fails); yaw rate `fwdc` only | HOLDS | `fwd_validation.json`: estimator-independent, not re-run |
| 5 | Heading fusion collapses textured position error on `fwdc` (UKF +heading 0.61, FGO 0.08–0.09 m vs ~4 m baseline) | HOLDS | `phase4_fwdc_arms.json`: UKF 0.13–0.14, FGO 0.06 m (both better) |
| 6 | With heading, the UKF has about 2× lower yaw error than the FGO | CHANGED | `fwdc` yaw RMS UKF 0.07–0.08° = FGO 0.07–0.08°: **UKF ≈ FGO** (ruling 9) |
| 7 | **C0:** FGO lower than the UKF with heading on all 6 textured bags | CHANGED | FGO lower on 3/3 `fwdc`; **UKF lower on 3/3 `fwdplainc`** (FGO 43 m). Cause: row 8 |
| 8 | (new) Plain-wall, hard-gated FGO with heading | PENDING | `phase4_fwdplainc_arms.json`: gyro-z bias runaway, ~20 headings fused, evo 43 m, yaw RMS 838–1,014°; also F1/F4 FGO_hard yaw max ~180°. Robust FGO best there. **Mechanism: trace pending** (ruling 1) |
| 9 | **Consistency:** the FGO is ~57× over-confident (fwdc baseline NEES 57.1); UKF plain-wall NEES 6.11 | CHANGED | `phase5b_consistency.json`: FGO NEES **1.67** (consistent); UKF +heading `fwdplainc` **13.41** (more over-confident) |
| 10 | **Blank floor:** without flow no estimator bounds position; the heading does not either (EKF3 output invalid; UKF/FGO km-scale) | HOLDS | `blank_behaviour.json`: UKF/FGO end-of-cruise 29–40 / 19–41 km, heading arms +60 s 40–89 / 132–193 m (†) |
| 11 | Transition: EKF3 freezes (invalid), UKF/FGO dead-reckon then diverge | HOLDS | ratios UKF 6.8, FGO 26.8 (was 45.9 / 50.0), still divergence (†); not ranked by evo |
| 12 | Distance scale: FGO ≈ 1; UKF +heading ~1% under-scale; EKF3 along-track 0.97–0.98 | CHANGED | `scale_check.json`: UKF +heading 0.996–0.997 (under-scale gone); FGO 0.998–0.999; EKF3 unchanged |
| 13 | UKF take-off yaw kick \|Δ\| ≤ 0.79° (`dsn_tex` r1–r9) | CHANGED | `d15_kick.json`: **≤ 0.82°** (r8; ruling 9) |
| 14 | **Closed loop:** the flight scores of numbers.md §15 (contact windows, B1–B5 counts, incl. the EKF3 half-speed MISS) | HOLDS | flights, not offline replays, so unchanged; the corrected-FGO `_v3` re-flight reached the west wall at +169.9 s (U3 PASS) |
| 15 | Closed loop: the FGO weights each heading ~5× more than the UKF (15.9 % vs 2.9 %) | CHANGED | FGO now ≈ 1.3–1.4 % (`_v3`, window-median σ 0.57°); **UKF side OPEN**; no ratio stated |
| 16 | Open-loop contact prediction: a tight west cluster (+160 … +171 s) | CHANGED | post-hoc, `fgo_contact_prediction_half_final.json`, n = 8 of 10: 4 west / 3 east / 1 none. Missing: `fgo_shadow_half_a`, live XFGO (ruling 11) |
| 17 | **T:** H-T1 PASS; P-T2, P-T3, P-T4 FAIL | HOLDS | `expT/t_aggregate.json`: same verdicts (H-T1 ρ +0.30, p 6e-6) |
| 18 | T condition D: EKF3 live is the best live estimator (0.096 vs FGO 0.121) | CHANGED | FGO live **0.082** < EKF3 0.096: **descriptive only, n = 3** (ruling 7) |
| 19 | **O:** H-O1 PASS 3/3; H-O2 FAIL | HOLDS | `expO/O_*.json`: H-O1 3/3; H-O2 ratio 1.72–1.84 (was ~2.2) |
| 20 | O: P-O3 FAIL | CHANGED | **PASS 3/3** (batch/RTS ratio 1.01–1.05); flip accepted (ruling 5) |
| 21 | O: the FGO batch is ~2× better than the RTS-UKF (0.33 vs 0.60–0.64 m) | WITHDRAWN | FGO batch 0.59 m ≈ RTS-UKF 0.58–0.60 (ruling 5) |
| 22 | O: why the FGO batch worsened (0.33 → 0.59 m) | PENDING | attribution study running (ruling 12) |
| 23 | **L:** loop closure keeps live error bounded; H-L1, H-L2, H-L3, P-L4 PASS 3/3 | HOLDS | `expL/T_A_r*_t245.json`: **all PASS 3/3, unchanged**; lc live 0.049–0.076 m, nolc 0.281–0.362 m; lap ratio lc 0.16–0.43, nolc 3.0–5.0. L's result did not change; only magnitudes moved (no-LC wall time ~3–10× longer, cause untraced) |
| 24 | L, V-L: keyframe FGO matches the thesis FGO (4.63 vs 4.59 m, PASS) | WITHDRAWN | NOT re-scorable (ruling 6, 2026-10-09): its labels were never recorded; the PASS was on the old FGO |
| 25 | **H:** hold H-H1 PASS; P-H5, P-H7 PASS | HOLDS | `expH/*.json`: P-H5 20/20 each estimator (+ `s1far_r3b` 4/4); P-H7 PASS |
| 26 | H: offline shadows drift more than the flying estimators (UKF 30 s 282–292 mm); "the S1 → S2/S3 gap closes" | CHANGED | shadows now 4–9 (UKF) / 1–8 mm (FGO) at 30 s vs EKF3 3–11 mm: **"no gap between shadow and flying estimators"** (ruling 6) |
| 27 | **F1** NOT met | HOLDS | `f1_test.json`: **"NOT met (lockout tie)"** (ruling 8): robust lower yaw max on 6/6 (was 0/6), but lockouts 3 = 3 |
| 28 | **F2** NOT met | CHANGED | **MET**: batch off-interval yaw RMS 0.063–0.066° vs live 0.32–0.36° (ruling 4) |
| 29 | **F3** NOT met (FGO Δ30 lockout) | HOLDS | still NOT met; Δ30 lockout gone (convergence 0.0–0.1 s); ratio decreasing 1/3 |
| 30 | **F3b** (a) TRUE, (b) FALSE | HOLDS | unchanged |
| 31 | **F3c** (a) FALSE, (b) TRUE | CHANGED | (b) **FALSE** (ratio decreasing 1/3, was 3/3) (ruling 4) |
| 32 | **2(a):** P1 FAIL, S1 PASS, S2 FAIL | HOLDS | `f4_test.json`: P1 7/12, S1 5/6, S2 5/12 |
| 33 | 2(a): the UKF has the lower yaw max than the robust FGO, 10/10 | CHANGED | **robust FGO lower on 8/10** (ruling 9) |
| 34 | Dataset counts / P4 band: `fwdc` 6/9, `fwdplainc` 8/9; FGO textured band [4.189, 5.117] | CHANGED | `fwdc` **8/9**, `fwdplainc` **9/9**, `p1c` 6/6; FGO band **[−0.614, 7.017]**, too wide to be informative (ruling 3) |
| 35 | Window/clock/threshold sensitivity is small on textured flights | HOLDS | `*_final.json`: all ≤ 0.013 m (not like-for-like with old rows) |

**Counts:** HOLDS 14 · CHANGED 16 · WITHDRAWN 3 · PENDING 2 (35 claims).
