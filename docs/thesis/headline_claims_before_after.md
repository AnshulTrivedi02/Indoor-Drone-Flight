# Headline claims: before vs after the final re-runs (2026-10-10)

"Before" is the claim as stated up to `07f9f56` (old FGO noise model; pre-correction UKF). "After" is the final
consolidated re-run (`425e824`) **plus the FGO-only re-run** (completed 2026-10-10 21:35: FGO initial yaw σ 1e-3 rad → 1°,
roll/pitch 2° → 5°, both the UKF's; D18). Values: `docs/thesis/numbers.md`. EKF3 and the UKF are unchanged by the
FGO-only re-run (18 hard gates, 0 differences). Rulings: METHODOLOGY "RULINGS (user, 2026-10-10)". Old → new:
`eval/results/final_old_vs_new.md` (first final re-run), `eval/results/final2_old_vs_new.md` (FGO-only re-run).
**Status:** HOLDS (claim stands as worded) · CHANGED (stands only re-worded, or the verdict flipped) · WITHDRAWN (no
longer made). **Attribution:** the corrections were applied jointly and are not attributed individually, except the
directly traced plain-wall case and the ruled O partial attribution (numbers.md §18). evo = evo -a (cruise), m.
"1st re-run" = the first final re-run (FGO with the 1e-3 rad initial yaw).

| # | claim before | status | evidence now |
|---|---|---|---|
| 1a | **Corridor ranking, textured `dsn`, mean of r1–r3** (`rerun_dsn_evo.json`): UKF 3.91 < EKF3 4.00 < FGO 4.64 | CHANGED | now **FGO 3.44 < UKF 3.59 < EKF3 4.00**: the UKF is NOT last; **EKF3 is highest**. Driven by the bimodal r2 flight (FGO 1.80, UKF 1.61). Descriptive; no ordering claimed (n = 3) |
| 1b | **UKF textured standing, median of r1–r9** (D15 wording): UKF 5.34, above EKF3 4.10 and FGO 4.61 | HOLDS | `rerun_dsn_evo.json` + `dsn_extra_evo.json`: UKF 5.13 > FGO 4.46 > EKF3 4.10; the UKF is highest by median and highest on 6/9 flights (lowest on r1, r2, r6). Descriptive. Unchanged by the FGO-only re-run except FGO 4.45 → 4.46 |
| 2 | **EKF3 beats the FGO on standard sensors** (confirmatory: "EKF3 lower", 6/7, d −0.69 m, CI [−1.16, −0.21]) | WITHDRAWN | `dsn_paired_test.json`, same rule: **"no ordering claimed"**, 5/7, mean d −0.021 m, CI [−0.989, +0.947] (1st re-run −0.040, [−0.934, +0.853]); driven by r6 (FGO 1.27 vs EKF3 3.11). The old verdict used the mis-specified FGO noise model (ruling 2) |
| 3 | The FGO is the "tight" textured estimator (noise-floor SD 0.05–0.13 m) | CHANGED | FGO SD **1.30 m** [0.88, 2.49] (n = 9; 1st re-run 1.23); EKF3 0.31 (unchanged) |
| 4 | **Camera heading measurement** (Phase 3): heading valid on `fwdc` 9/9, `fwdplainc` 6/9 (checker floor fails); yaw rate `fwdc` only | HOLDS | `fwd_validation.json`: estimator-independent, not re-run |
| 5 | Heading fusion collapses textured position error on `fwdc` (UKF +heading 0.61, FGO 0.08–0.09 m vs ~4 m baseline) | HOLDS | `phase4_fwdc_arms.json`: UKF 0.13–0.14, FGO 0.06 m (both better; FGO unchanged by the initial-yaw fix). Plain walls (1° initial yaw): UKF 0.15–0.25, FGO 0.09–0.22 m. **Caveat:** at a 0.1 rad initial yaw σ the plain-wall heading arms degrade for both (r3 5.70 m, worse than the FGO baseline 4.85; numbers.md §18); `fwdc` is unaffected |
| 6 | With heading, the UKF has about 2× lower yaw error than the FGO | CHANGED | yaw RMS UKF ≈ FGO on both wall types: `fwdc` 0.07–0.08° each (ruling 9); `fwdplainc` 3.08–3.39° vs 3.07–3.41° |
| 7 | **C0:** FGO lower than the UKF with heading on all 6 textured bags | HOLDS | FGO lower on 3/3 `fwdc` (0.06 vs 0.13 m) **and again on 3/3 `fwdplainc`** (0.09–0.22 vs 0.15–0.25 m; margin 0.03–0.06 m). The 1st re-run's reversal (UKF lower on `fwdplainc`, FGO 43 m) was row 8's model error. **Flip back: ruling requested** |
| 8 | (1st re-run) Plain-wall, hard-gated FGO with heading diverges (gyro-z bias runaway, evo 43 m, yaw RMS 838–1,014°) | WITHDRAWN | Trace found a D18 model error (initial yaw σ 1e-3 rad), the exception in ruling 1; corrected. Now on all six plain-wall bags the FGO matches the UKF: yaw max 4.59–5.03° tex / 3.91–6.24° trans, headings fused 647–778 / 3,582–5,911 (UKF within ~1%), bias −7.6 … −8.4 deg/min. Transition position still runs away on the blank half (557–717 m), as the FGO baseline |
| 9 | **Consistency:** the FGO is ~57× over-confident (fwdc baseline NEES 57.1); UKF plain-wall NEES 6.11 | CHANGED | `phase5b_consistency.json`: FGO `fwdc` baseline NEES **1.70** (consistent); +heading `fwdplainc` UKF **13.41** and FGO **13.95**: both equally over-confident on plain walls (1st re-run FGO 24.8, the divergence) |
| 10 | **Blank floor:** without flow no estimator bounds position; the heading does not either (EKF3 output invalid; UKF/FGO km-scale) | HOLDS | `blank_behaviour.json`: UKF/FGO end-of-cruise 29–40 / 22–41 km, heading arms +60 s 40–89 / 135–190 m (†) |
| 11 | Transition: EKF3 freezes (invalid), UKF/FGO dead-reckon then diverge | HOLDS | ratios UKF 6.8, FGO 17.7 (1st re-run 26.8; before 45.9 / 50.0), still divergence (†); not ranked by evo |
| 12 | Distance scale: FGO ≈ 1; UKF +heading ~1% under-scale; EKF3 along-track 0.97–0.98 | CHANGED | `scale_check.json`: UKF +heading 0.996–0.997 (under-scale gone); FGO 0.998–0.999 (unchanged by the FGO-only re-run); EKF3 unchanged |
| 13 | UKF take-off yaw kick \|Δ\| ≤ 0.79° (`dsn_tex` r1–r9) | CHANGED | `d15_kick.json`: **≤ 0.82°** (r8; ruling 9). UKF, unchanged by the FGO-only re-run |
| 14 | **Closed loop:** the flight scores of numbers.md §15 (contact windows, B1–B5 counts, incl. the EKF3 half-speed MISS) | HOLDS | flights, not offline replays, so unchanged. **The flown FGO results (S3, `_v3`, the FGO safety tests) used the OLD priors (1e-3 rad yaw, 2° roll/pitch); no re-fly before the freeze** (ruling, item 4) |
| 15 | Closed loop: the FGO weights each heading ~5× more than the UKF (15.9 % vs 2.9 %) | CHANGED | FGO ≈ 1.3–1.4 % (`_v3`, flown with the OLD initial priors; window-median σ 0.57°); **UKF side OPEN**; no ratio stated |
| 16 | Open-loop contact prediction: a tight west cluster (+160 … +171 s) | CHANGED | post-hoc, `fgo_contact_prediction_half_final.json`, n = 8 of 10: 4 west (+154 … +198 s) / 3 east / 1 none, median +163.2 s (1st re-run 162.9). Missing: `fgo_shadow_half_a`, live XFGO (ruling 11) |
| 17 | **T:** H-T1 PASS; P-T2, P-T3, P-T4 FAIL | HOLDS | `expT/t_aggregate.json`: same verdicts (H-T1 ρ +0.30, p 6e-6) |
| 18 | T condition D: EKF3 live is the best live estimator (0.096 vs FGO 0.121) | CHANGED | FGO live **0.083** < EKF3 0.096: **descriptive only, n = 3** (ruling 7) |
| 19 | **O:** H-O1 PASS 3/3; H-O2 FAIL | HOLDS | `expO/O_*.json`: H-O1 3/3; H-O2 ratio 1.72–1.84 (was ~2.2) |
| 20 | O: P-O3 FAIL | CHANGED | **PASS 3/3** (batch/RTS ratio 1.01–1.05); flip accepted (ruling 5) |
| 21 | O: the FGO batch is ~2× better than the RTS-UKF (0.33 vs 0.60–0.64 m) | WITHDRAWN | FGO batch 0.59 m ≈ RTS-UKF 0.58–0.60; the old result was **largely an artefact of the mis-specified FGO noise model** (ruling "O attribution") |
| 22 | O: why the FGO batch worsened (0.33 → 0.59 m) | CHANGED | **Resolved as a PARTIAL attribution** (ruled): ~93 % noise fix, ~7 % yaw cap, +0.03 m interaction; the yaw cap improves the live track by 0.22–0.30 m. Computed on the code BEFORE the initial-yaw correction; that correction moves the O batch by < 0.001 m |
| 23 | **L:** loop closure keeps live error bounded; H-L1, H-L2, H-L3, P-L4 PASS 3/3 | HOLDS | `expL/T_A_r*_t245.json`: **all PASS 3/3 in both re-runs**. The L FGO **did change** in the FGO-only re-run, with the initial-uncertainty correction (its `FGO.init` priors and the V-L start's yaw σ; not attributed individually): lc live 0.049–0.076 m (unchanged to printed precision), nolc live 0.281–0.362 → **0.262–0.361 m**, nolc lap ratio 3.0–5.0 → **2.9–4.5**. L's result did not change |
| 24 | L, V-L: keyframe FGO matches the thesis FGO (4.63 vs 4.59 m, PASS) | CHANGED | not re-scorable on the corrected FGO (ruling 6, 2026-10-09: labels never recorded); the old PASS was for the old FGO and is listed, not restated |
| 25 | **H:** hold H-H1 PASS; P-H5, P-H7 PASS | HOLDS | `expH/*.json`: P-H5 20/20 each estimator (+ `s1far_r3b` 4/4); P-H7 PASS. FGO shadow unchanged to printed precision |
| 26 | H: offline shadows drift more than the flying estimators (UKF 30 s 282–292 mm); "the S1 → S2/S3 gap closes" | CHANGED | shadows now 4–9 (UKF) / 1–8 mm (FGO) at 30 s vs EKF3 3–11 mm: **"no gap between shadow and flying estimators"** (ruling 6) |
| 27 | **F1** NOT met | HOLDS | `f1_test.json`: **"NOT met (lockout tie)"** (ruling 8): robust lower yaw max on 6/6, lockouts 3 = 3. FGO_hard plain-wall yaw max now 4.59–5.03° (1st re-run ~180°) |
| 28 | **F2** NOT met | CHANGED | **MET**: batch off-interval yaw RMS 0.063–0.066° vs live 0.32–0.36° (ruling 4) |
| 29 | **F3** NOT met (FGO Δ30 lockout) | HOLDS | still NOT met; Δ30 lockout gone (convergence 0.0–0.1 s); ratio decreasing 1/3 |
| 30 | **F3b** (a) TRUE, (b) FALSE | HOLDS | unchanged |
| 31 | **F3c** (a) FALSE, (b) TRUE | HOLDS | as computed now (b) **TRUE** again (ratio decreasing 2/3: r2, r3). It flipped TRUE → FALSE in the 1st re-run (accepted, ruling 4) and back now. **Fragile:** r3 rests on FGO integrals of 0.2–0.5 m·s against UKF ~2 m·s. **Ruling requested** |
| 32 | **2(a):** P1 FAIL, S1 PASS, S2 FAIL | HOLDS | `f4_test.json`: P1 7/12, S1 5/6, S2 5/12. FGO_hard lockout total 23 → 61 (cause untraced; no longer the divergence) |
| 33 | 2(a): the UKF has the lower yaw max than the robust FGO, 10/10 | CHANGED | **robust FGO lower on 8/10** (ruling 9) |
| 34 | Dataset counts / P4 band: `fwdc` 6/9, `fwdplainc` 8/9; FGO textured band [4.189, 5.117] | CHANGED | as computed `fwdc` **7/9**, `fwdplainc` **7/9** (1st re-run 8/9, 9/9), `p1c` 6/6. The 3 new misses are FGO transition ratios outside a band that collapsed to [15.908, 19.159] (runaway sizes †, an artefact). **Ruling requested.** FGO textured band **[−0.889, 7.168]**, too wide to be informative (ruling 3) |
| 35 | Window/clock/threshold sensitivity is small on textured flights | HOLDS | `*_final.json`: all ≤ 0.013 m (not like-for-like with old rows) |

**Counts:** HOLDS 17 · CHANGED 16 · WITHDRAWN 3 · PENDING 0 (36 rows; claim 1 is split into 1a/1b; row 8 is the 1st
re-run's plain-wall claim). Against the first version of this table: row 7 CHANGED → HOLDS, row 31 CHANGED → HOLDS
(both await a ruling, as flips back), row 8 PENDING → WITHDRAWN, row 22 PENDING → CHANGED.

**0.1 rad initial-yaw sensitivity (ruled check; numbers.md §18):** no UKF-vs-FGO ordering changes, and `fwdc` and
`dsn` are unaffected beyond the FGO noise floor. One conclusion does change: on plain walls the heading arms of BOTH
estimators depend strongly on the initial yaw σ (r3: 0.25 / 0.22 m → 5.70 / 5.70 m, the FGO heading arm worse than its
own baseline), so "the heading bounds plain-wall position" holds at 1° but not at 0.1 rad on r3.
