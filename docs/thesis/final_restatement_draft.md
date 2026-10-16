# Final consolidated re-run: old → new restatement (DRAFT for the user's review)

**Status: DRAFT.** Nothing here has been copied into `numbers.md` or METHODOLOGY. Every number below was read from the
JSON files named, not from `final_old_vs_new.md`, unless stated otherwise.

**What is compared.**
- **Old:** `eval/results_pre_final/` (the snapshot taken when the run started; it equals the committed results at
  `07f9f56`). For H and O, the old side is the same-scorer pre-score `~/thesis_data/batches/final_rerun/prescore/`.
  For every value read here it is identical to the snapshot (checked for all five H files and three O files).
- **New:** `eval/results/` at `425e824` (the final consolidated re-run, completed 2026-10-10 05:15).
- **Corrections in the new code:** UKF bias-corrected derotation; UKF jitter only on Cholesky failure; FGO
  `setBiasAccOmegaInit = 0`; FGO variance-gated yaw cap. EKF3 is unchanged: 9 hard gates, 0 differences.
- **Attribution caveat.** "REAL" below means *produced by today's corrected code on the same inputs*. Which of the
  four corrections causes a given change is NOT established: the ruled attribution study was not run. The derotation
  handover also found that today's UKF does not reproduce the stored UKF outputs even with derotation off; that was
  attributed to the jitter fix but not proven.

---

## 1. Flag verification (step 1)

`final_old_vs_new.md` has 95 flagged rows: 86 DIRECTION and 9 VERDICT. The header calls all 95 "direction flags".

| class | flags | which |
|---|---|---|
| **REAL** | **88** | everything except the seven below. Of these: 10 are verdict flips (O P-O3 ×8 rows, F2, F3c (b)); 38 are real but carry no ordering (33 H mm-level differences, 4 F4 fwdc sub-noise differences, 1 difference of diverged blank magnitudes); 1 is trivial (a NEES crossing 3 by 0.05) |
| **ARTEFACT** | **7** | #3–#6 (6.4 transition displacement ratios) and #7–#9 (section 8 per-trial verdicts) |
| **UNCLEAR** | **0** | — |

The full flag-by-flag table, with evidence for each row, is in the Appendix.

### 1.1 The artefact: `rerun_compare.py` reads the wrong "old" files for sections 6.4, 7 and 8

- **What the script reads.** In those sections the old side is `fwdc_evo.json`, `fwdplainc_evo.json`, `p1c_evo.json`
  and `*_score.json`, all dated 2026-09-24, together with the hard-coded `ob` bands in section 7. These are the
  superseded flights from before the consolidated re-fly. The current results are in `rerun_*` files, which exist on
  both sides.
- **Proof that these are different flights.** EKF3 differs between those files and the new ones. For example, the
  fwdc transition EKF3 evo is 21.4–22.1 m in `fwdc_evo.json` against 41.5 m in `rerun_fwdc_evo.json`. Yet all
  nine EKF3 gates show 0 differences. Different EKF3 values therefore mean a different dataset.
- **The script itself is wrong for these sections, not the results.** The self-test excluded them because "OLD = NEW
  is not an identity there", so the problem was never caught. The script was NOT edited in this stage.
- **What is wrong besides the 7 flags.** Every row of 6.4, 7 and 8, flagged or not, shows the wrong old value. For 6.1,
  `dsn_dejitter_baseline.json` equals `rerun_dsn_evo.json` in the old snapshot, so section 6.1 is sound.

**Corrected values, same file on both sides (`results_pre_final/rerun_*` → `results/rerun_*`):**

| quantity | as printed in the md (wrong old) | correct old → new | crossing? |
|---|---|---|---|
| fwdc trans FGO displacement ratio, mean of 3 | 0.71 → 19.38 | **50.24 → 19.38** | none (both ≫ 1) |
| fwdc trans UKF ratio | 0.81 → 6.70 | **49.55 → 6.70** | none |
| fwdplainc trans FGO ratio | 0.71 → 19.32 | **49.92 → 19.32** | none |
| fwdplainc trans UKF ratio | 0.74 → 6.41 | **44.04 → 6.41** | none |
| fwdc textured FGO r1/r2/r3 | 4.68/4.42/4.97 → … | **4.58/4.68/4.58 → 4.46/2.39/4.53** | — |
| fwdc textured UKF r1/r2/r3 | 14.60/20.94/7.30 → … | **5.13/2.27/5.13 → 4.96/1.78/4.96** | — |
| fwdplainc textured FGO | 4.67/4.82/4.64 → … | **4.57/4.54/4.56 → 4.52/4.51/4.72** | — |
| fwdplainc textured UKF | 15.81/9.97/8.71 → … | **5.17/11.51/11.09 → 5.02/11.19/10.82** | — |
| p1c textured FGO (fwdc; fwdplainc) | — | **4.57; 4.60 → 5.20; 4.59** | — |
| `fwdc_tex_r2` verdict (#7) | PASS → FAIL | **FAIL → FAIL** (EKF3 0.01 m outside its band; unchanged) | none |
| `fwdc_trans_r1` verdict (#8) | FAIL → PASS | **PASS → PASS** | none |
| `p1c_fwdplainc_trans` verdict (#9) | FAIL → PASS | **PASS → PASS** | none |
| **fwdc primary pass count** | 8/9 → 8/9 | **6/9 → 8/9** (`fwdc_blank_r1`, `r2` FGO ratio/onset now pass) | **yes, unflagged** |
| **fwdplainc primary pass count** | 9/9 → 9/9 | **8/9 → 9/9** (`fwdplainc_blank_r2` FGO ratio now passes) | **yes, unflagged** |
| p1c primary | 5/6 → 6/6 | **6/6 → 6/6** | none |
| section 7 "old" bands | hard-coded pre-re-fly bands (e.g. FGO tex [4.17, 5.14]) | see §5 | — |

**The suspicious magnitudes named in the brief:**

| row | verdict | evidence |
|---|---|---|
| "FGO ratio, mean of 3 0.71 → 19.38" | **ARTEFACT** | correct old 50.24 (`rerun_fwdc_evo`). The FGO transition runaway shrinks (ratio 51.1/50.2/49.4 → 17.4/23.2/17.6), but there is no side-of-1 change |
| "FGO_baseline 57.11 → 1.67" (P5b fwdc tex NEES) | **REAL** | same file on both sides (`phase5b_consistency.json`). Per bag 56.1/58.9/56.4 → 2.3/0.2/2.5. The FGO's predicted yaw σ falls 0.476° → 0.057° (`checker_S`), so its covariance is no longer ~57× over-confident. This is the expected effect of removing the extra IMU noise |
| "fwdplainc FGO_heading 17/48 → 0/48" (end wall) | **REAL, mixed cause** | old 17 = blank 6 + transition 11 (textured 0). **Blank (6 → 0):** a genuine gain; the FGO fuses normally there (8,609–8,631 headings) and now rejects the wrong ones. **Transition (11 → 0):** the FGO is locked out by a yaw-bias runaway (19–26 headings fused in the whole flight; see §2.1), so 0 there is not a gate win |
| "FGO −1060 → 1337" (P4 fwdplainc blank heading-arm effect) | **REAL but not interpretable** | the difference of two diverged blank-floor evo values (baseline 7.0–7.9 km, heading 8.2–9.7 km). Under the † rule this is evidence of divergence, not a value, so its sign means nothing |
| "O P-O3 0/3 FAIL → 3/3 PASS" | **REAL verdict flip** | same scorer and same inputs (pre-score = snapshot). **The FGO batch got WORSE:** 0.328/0.332/0.330 → 0.589/0.590/0.588 m. RTS-UKF (capped) moved 0.641/0.611/0.602 → 0.575/0.582/0.599; cap-free 0.979/0.972/0.970 → 0.597/0.604/0.620. Ratios 1.83–1.95 → 1.01–1.02 |

---

## 2. The most important real changes

### 2.1 NEW FAILURE: with the hard (EKF3-style) innovation gate, the corrected FGO diverges in yaw on plain walls
- **Where.** `phase4_fwdplainc_arms.json`, FGO +heading.
  - On the **textured and transition** floors, the gyro-z bias estimate runs away: −267 … −480 / +447 deg/min,
    against a true +8.9 deg/min. Yaw-error RMS is 838–1,497°.
  - It fuses 19–28 of 6,197–8,431 valid headings. Median heading NIS is 1,740–13,121 (99.6–99.8 % over the gate).
  - textured evo: 0.20/0.61/0.22 → **43.5/42.7/43.1 m**.
- **Where it does not happen.**
  - **Blank floor:** bgz −8.3, 8.6 k headings fused.
  - **fwdc** (textured walls): FGO bgz −8.2 deg/min, now the UKF's value.
  - **The FGO baseline** (no heading): bgz ≈ 0.
- **The same failure in the F tests.** `f1_test`/`f4_test` FGO_hard on all 8 plain-wall bags: yaw max 179.9–180.0°,
  rms 105–110°, 4,346–4,452 correct headings rejected, 4–6 lockouts.
- **The robust (Cauchy) FGO is now the best arm there:** yaw max 1.06–2.22°, 0 wrong headings accepted.
- **What follows from it:**
  - #10–#11 and #15;
  - the P5b FGO_heading NEES 0.05 → 24.8;
  - the end-wall `fwdplainc/FGO` yaw-prediction NEES 4.15 → 3.7 × 10⁶ (unflagged; both values are above 3);
  - the F1/F4 plain-wall rows;
  - **C0 reverses on plain walls** (§3, §6.6).
- **Mechanism: NOT TRACED** (report only; no replay was run in this stage).
  - The pattern: early heading fusions with a now-tight yaw σ (0.06°), then lockout, then the bias diverges.
  - It matters for any real flight with plain walls and the hard-gated FGO.

### 2.2 The confirmatory EKF3-vs-FGO test no longer claims an ordering (§4)
- The verdict goes from "EKF3 lower" to **"no ordering claimed"**.
- The FGO's textured `dsn` results are now bimodal, like the UKF's: r2 1.93 m and r6 1.43 m; the others 4.07–4.60 m.
  These are the same two flights on which the UKF is lowest (1.61, 1.17) and EKF3's r6 is lowest (3.11).
- The FGO noise-floor SD rises from 0.05 to 1.23 m.

### 2.3 The H shadows now drift at EKF3's scale; the S1→S2/S3 shadow-vs-flying gap closes
- 30 s tag loss, UKF shadow 0.27–0.29 m → **3–25 mm**; FGO shadow 0.10–0.13 m → **0.5–25 mm**. EKF3 (flying) is
  3–26 mm.
- The flying UKF/FGO in S2/S3 had already drifted at EKF3's scale. The offline-shadow vs flying discrepancy has
  therefore gone.
- The 33 H ordering flags are this effect: mm-level differences with no ordering.

### 2.4 Verdict flips
| test | old verdict | new verdict |
|---|---|---|
| **F2** (hindsight correction) | NOT met | **MET**. Batch off-interval yaw RMS 0.063–0.066° against live 0.32–0.36° on all 3 bags |
| **F3c (b)** (advantage grows) | TRUE | **FALSE**. Ratio decreasing on 1/3 bags (was 3/3) |
| **O P-O3** | FAIL 0/3 | **PASS 3/3**. The FGO batch worsened to the RTS-UKF's level; the "FGO batch ≈ 2× better than RTS-UKF" statement no longer holds |
| **Confirmatory test** | EKF3 lower | **no ordering claimed** |

**Near-flips, with the verdict unchanged:**
- **F1:** still NOT met, but now only through a lockout tie (FGO_robust 3 = UKF_hard 3). Its second criterion (robust
  lower yaw max than UKF_hard on ≥ 4 of 6) now passes 6/6 (was 0/6).
- **F3:** still NOT met, but the reason changes. The FGO's Δ30 prior-induced lockout is gone (convergence 176–182 s →
  0.0–0.1 s); at Δ60 both lock out.
- **T P-T3:** still FAIL, but condition C now passes its band (1.80 → 1.43).

### 2.5 Other large real shifts
- **T:** FGO live in condition D, 0.122 → 0.082 m, now below EKF3 live (0.096). The RTS-UKF in C/D improves 2.3×
  (0.091 → 0.039, 0.258 → 0.109 m).
- **The UKF with heading** improves about 5× in position on fwdc (0.61 → 0.13 m) and on plain walls (0.73–0.94 →
  0.15–0.25 m). Its plain-wall NEES worsens (6.11 → 13.41).
- **Transition and blank runaways** shrink (UKF transition +60 s 31–307 → 129–139 m; FGO 939–1,049 → 223–231 m).
  Both remain divergence, not accuracy.
- **The degenerate band (§5).** The recomputed P4 FGO textured band is [−0.614, 7.017] m.

---

## 3. Headline UKF/FGO numbers, old → new (pipeline handover §5 and `numbers.md`)

Legend: ⚑ = a verdict, ordering or wording change. Plain = a magnitude only.

### §6.1 Textured `dsn`, evo -a (cruise) (`rerun_dsn_evo.json`, `dsn_extra_evo.json`, `dsn_paired_test.json`, `d15_*.json`)
| quantity | old | new | flag | plain explanation |
|---|---|---|---|---|
| FGO r1 / r2 / r3 | 4.59 / 4.72 / 4.60 | 4.07 / 1.93 / 4.47 | ⚑ | FGO now low on r2, as the UKF already was |
| FGO mean / range | 4.64 / 0.13 | 3.49 / 2.54 | ⚑ | mean EKF3 − FGO −0.64 → +0.51 m; n = 3, driven by r2 |
| UKF r1 / r2 / r3 | 4.23 / 2.14 / 5.38 | 3.98 / 1.61 / 5.17 | ⚑ | mean UKF − FGO −0.72 → +0.10 m |
| EKF3 r1 / r2 / r3 | 4.03 / 3.86 / 4.10 | unchanged | | gated |
| **Confirmatory test** | EKF3 lower | **no ordering claimed** | ⚑ | see §4 |
| Noise-floor SD: EKF3 / FGO / d (χ² 95 %) | 0.31 [0.22, 0.57] / 0.05 [0.03, 0.10] / 0.37 [0.25, 0.71] | 0.31 [0.22, 0.57] / **1.23 [0.83, 2.36]** / **0.96 [0.65, 1.83]** | ⚑ | the FGO is no longer the "tight" estimator |
| UKF r1–r9 median / range / SD | 5.34 / 1.71–5.96 / 1.55 | 5.13 / 1.17–5.85 / 1.70 | | instability rule (> 3× median): 0/9 in both, so "stable on all 9" holds |
| Wording "UKF above EKF3 4.10 and FGO 4.61" (medians) | 5.34 vs 4.10 / 4.61 | 5.13 vs 4.10 / **4.45** | | still above both |
| UKF cruise yaw drift r1–r9 (deg/min) | −7.6, −2.7, −10.0, −10.1, −9.7, −1.3, −9.9, −11.2, −10.0 | −7.6, −2.3, −10.0, −10.1, −9.9, −0.7, −10.1, −11.4, −9.8 | | essentially unchanged |
| UKF cruise yaw drift, transition | −10.3, −13.0, −10.2 | −10.3, −12.9, −10.2 | | unchanged |
| FGO cruise yaw drift r1–r9 (deg/min; `d15_drift`) | −9.1 … −9.4 (all) | −8.0, −3.6, −8.9, −8.8, −9.1, −2.5, −9.1, −9.0, −8.4 | | FGO now bias-tracks on r2/r6 too |
| UKF take-off yaw change \|Δ\|, r1–r9 | ≤ 0.79° | **≤ 0.82°** (r8 −0.82) | ⚑ wording | the "≤ 0.79°" bound is exceeded by 0.03° |
| FGO take-off yaw change \|Δ\| | ≤ 0.08° | ≤ 0.09° | | |

### §6.2 Blank / transition (`blank_behaviour.json`; † = divergence, cite the order of magnitude only)
| quantity | old | new | flag | plain explanation |
|---|---|---|---|---|
| UKF baseline error +10 / +30 / +60 s after loss, blank (n = 11) | 6.4–9.0 / 20.5–33.0 / 112–288 m | 6.4–8.2 / 27.3–36.5 / 60–108 m | | slower late growth |
| FGO baseline, same | 4.2–18.3 / 27–142 / 172–574 m | 6.4–8.2 / 28.0–37.0 / 155–204 m | | tighter spread |
| UKF / FGO baseline error at end of cruise, blank † | 13–58 / 22–31 km | 29–40 / 19–41 km | | still km-scale divergence |
| UKF / FGO baseline +60 s, transition (n = 11) † | 31–307 / 939–1,049 m | 129–139 / 223–231 m | | |
| Heading arms, blank +60 s, UKF / FGO (n = 6) † | 88–323 / 299–904 m | 40–89 / 132–193 m | | the heading still does not bound position without flow |
| dsn transition displacement ratio, UKF / FGO (mean of 3) | 45.9 / 50.0 | 6.8 / 26.8 | | |

### §6.4 Forward-camera textured (corrected old side; see §1.1)
| quantity | old | new | flag | plain explanation |
|---|---|---|---|---|
| fwdc FGO r1/r2/r3 | 4.58 / 4.68 / 4.58 | 4.46 / 2.39 / 4.53 | ⚑ | mean 4.61 → 3.79, now 0.13 m below EKF3's 3.92 (n = 3, driven by r2) |
| fwdc UKF r1/r2/r3 | 5.13 / 2.27 / 5.13 | 4.96 / 1.78 / 4.96 | | mean 4.18 → 3.90, equal to EKF3's 3.92 within 0.02 m (n = 3, driven by r2) |
| fwdplainc FGO | 4.57 / 4.54 / 4.56 | 4.52 / 4.51 / 4.72 | | |
| fwdplainc UKF | 5.17 / 11.51 / 11.09 | 5.02 / 11.19 / 10.82 | | r2/r3 take-off kick remains |
| p1c FGO (fwdc; fwdplainc) | 4.57; 4.60 | **5.20**; 4.59 | ⚑ | p1c_fwdc 5.20 lies outside the OLD FGO band [4.189, 5.117] and passes only because the band widened (§5) |

### §6.5 Distance scale (`scale_check.json`, textured fwdc)
| quantity | old | new | flag |
|---|---|---|---|
| FGO baseline / +heading speed ratio | 0.997 / 0.998 | 0.998–0.999 / 0.998–0.999 | |
| UKF +heading speed / along-track ratio | 0.987–0.990 / 0.987–0.990 | 0.996–0.997 / 0.996–0.997 | | 

The UKF's residual 1 % under-scale with heading is gone; it now matches the FGO.

### §6.6 Phase 4 (`phase4_*_arms.json`, `phase5b_consistency.json`)
| quantity | old | new | flag | plain explanation |
|---|---|---|---|---|
| fwdc UKF +heading r1/r2/r3 | 0.61 / 0.62 / 0.62 | 0.13 / 0.13 / 0.14 | | about 5× better |
| fwdc FGO +heading r1/r2/r3 | 0.08 / 0.09 / 0.09 | 0.06 / 0.06 / 0.06 | | |
| fwdc +heading+yaw rate | = +heading to 0.01 m | = +heading to 0.01 m | | |
| fwdplainc UKF +heading | 0.88 / 0.94 / 0.73 | 0.19 / 0.15 / 0.25 | | |
| **fwdplainc FGO +heading** | 0.20 / 0.61 / 0.22 | **43.5 / 42.7 / 43.1** | ⚑ | the plain-wall FGO yaw runaway (§2.1) |
| Heading-arm yaw RMS, fwdc, UKF / FGO | 0.08 / 0.18–0.19° | 0.07–0.08 / 0.07–0.08° | ⚑ wording | "the UKF has the lower yaw error (about 2×)" no longer holds on fwdc: they are equal |
| fwdplainc yaw RMS, UKF / FGO | 1.46–3.13 / 1.36–4.22° | 3.08–3.39 / **838–1,014°** | ⚑ | |
| **C0** (FGO vs UKF with heading) | FGO lower on all 6 bags | FGO lower on 3/3 fwdc; **UKF lower on 3/3 fwdplainc** | ⚑ | reversal caused by §2.1 |
| UKF +heading fwdplainc NEES, mean r1–r3 | 6.11 (10.42 / 6.79 / 1.12) | **13.41** (14.39 / 12.75 / 13.10) | | more over-confident on plain walls |
| FGO baseline cross-track NEES (fwdc tex, mean) | 57.1 | 1.67 | | the FGO is now consistent |

### §7 / §8 Bands and counts: see §5.

### F tests (`f1_test` … `f3c_test.json`)
| test | old verdict | new verdict | flag | plain explanation |
|---|---|---|---|---|
| F1 (k = 2.385 kept, ruling 3) | NOT met (robust lower yaw max on 0/6; lockouts 4 < 6) | **NOT met** (6/6; lockouts 3 = 3) | near-flip | fails only on the lockout tie |
| F2 | NOT met | **MET** | ⚑ | the batch's off-interval yaw RMS is now 5× below both live arms |
| F3 | NOT met (gate lockout at Δ30) | **NOT met**, lockout gone | ⚑ reason | ratios r1 1.75/1.22/1.02 (decreasing), r2/r3 not monotone; 1/3 < 2/3 needed |
| F3b | (a) TRUE, (b) FALSE | (a) TRUE, (b) FALSE | | the UKF still diverges numerically at every Δ (cross-track ~10⁸–10⁹ m) |
| F3c | (a) FALSE, (b) TRUE | (a) FALSE, **(b) FALSE** | ⚑ | |

### §15.1 2(a) (`f4_test.json`)
| quantity | old | new | flag | plain explanation |
|---|---|---|---|---|
| P1 robust < hard yaw max | 9/12 FAIL | 7/12 FAIL | | on fwdc the two arms are now equal (Δ ≤ 0.05°) |
| S1 fewer wrong accepted, plain | 5/6 PASS | 5/6 PASS | | |
| S2 x-track ≤ hard | 6/12 FAIL | 5/12 FAIL | | |
| Robust lower than UKF (yaw max / rms / x-track) | 0 / 3 / 10 of 10 | **8 / 9 / 10** of 10 | ⚑ wording | "UKF lower yaw max 10/10" reverses: the robust FGO now has the lower yaw max on 8/10 |
| Lockout total UKF_hard / FGO_hard / FGO_robust | 7 / 3 / 5 | 6 / **23** / 6 | | plain-wall hard-gate runaway |

### §15 Closed loop: §6 (contact prediction) and §7 (D27 item 3) below.

The closed-loop scores themselves use no offline replay, so they are unchanged. The yaw-cap ABLATION pairs listed in
the pipeline handover §5 (`H_s3_r*` vs `H_s3v2_r*`; `cl_fgo_*_v2` vs `_v3`; `H_safety_fgo_*_v2` vs `_v3`) are flight
results outside this offline re-run. They are already recorded in METHODOLOGY and are not restated here.

### §16.1 T (`expT/t_aggregate.json`), mean horizontal RMSE (m), conditions A / B / C / D
| track | old | new | flag |
|---|---|---|---|
| UKF live | 0.037 / 0.064 / 0.104 / 0.189 | 0.037 / 0.061 / 0.076 / 0.131 | |
| FGO live | 0.018 / 0.028 / 0.058 / 0.121 | 0.020 / 0.026 / 0.053 / 0.082 | ⚑ D now below EKF3's 0.096 |
| RTS-UKF | 0.014 / 0.031 / 0.091 / 0.258 | 0.014 / 0.031 / 0.039 / 0.109 | |
| FGO batch | 0.011 / 0.013 / 0.021 / 0.033 | 0.011 / 0.015 / 0.019 / 0.028 | |

| verdict | old | new | flag |
|---|---|---|---|
| H-T1 (medians A–D; ρ; p) | PASS (0.005 / 0.015 / 0.025 / 0.050; +0.47; 3e-13) | PASS (0.010 / 0.011 / 0.023 / 0.052; +0.30; 6e-6) | |
| P-T2 | FAIL (+0.021 / +0.036 / −0.007 / −0.126; ρ −0.16) | FAIL (+0.020 / +0.032 / +0.037 / +0.029; ρ +0.11, p 0.11) | gains now all positive, still not increasing |
| P-T3 ratios | FAIL 2.15 / 2.34 / 1.80 / 1.97 | FAIL 1.97 / 2.36 / **1.43** / 1.59 | C inside the band |
| P-T4 ratios | FAIL 1.23 / 2.35 / 4.26 / 7.76 | FAIL 1.31 / 2.14 / 2.07 / 3.89 | |

### §16.2 O (`expO/O_r1, O_r2, O_r3b`)
| track | indoor RMSE old → new | error at return old → new | largest step old → new |
|---|---|---|---|
| UKF live | 0.63–0.64 → **0.77–0.84** m | 1.69–1.75 → 2.37–2.51 m | 1.66–1.71 → 2.30–2.44 m |
| FGO live | 0.97–1.17 → 0.83–0.89 m | 2.83–3.31 → 2.50–2.66 m | 2.47–2.88 → 2.14–2.27 m |
| RTS-UKF (capped; cap-free) | 0.60–0.64; 0.97–0.98 → 0.58–0.60; 0.60–0.62 m | 0.02 → 0.02 m | — |
| **FGO batch** | **0.33 → 0.59 m** | 0.005–0.006 → 0.018–0.019 m | — |

- H-O1: PASS 3/3 → PASS 3/3.
- H-O2: FAIL (2.2×) → FAIL (1.72–1.84×).
- **P-O3: FAIL → PASS** ⚑.
- **Wording changes:**
  - "the FGO batch is about 1.9–2× better than the better RTS-UKF" no longer holds; they are equal within 1–5 %;
  - "the cap-free RTS-UKF is worse (0.97–0.98)" no longer holds; it is 0.60–0.62, within 0.02 m of the capped one;
  - "live ordering UKF < FGO" (O_r1) is now a tie.

### §16.3 L (`expL/T_A_r*_t245.json`)
| quantity | old | new | flag |
|---|---|---|---|
| lc live / hindsight RMSE | 0.041–0.047 / 0.020–0.029 m | 0.049–0.076 / 0.017–0.027 m | |
| nolc live / hindsight | 0.200–0.312 / 0.236–0.298 m | 0.281–0.362 / 0.221–0.271 m | |
| lap 5 ÷ lap 1, lc / nolc | 0.27–0.58 / 4.6–5.5 | 0.16–0.43 / 3.0–5.0 | |
| H-L1, H-L2, H-L3, P-L4 | PASS 3/3 each | PASS 3/3 each | |
| V-L | 4.63 vs 4.59 m, PASS | **NOT re-scorable** (ruling 6). The new `lvl__dsn_tex_r1` output exists, but no labels were defined and none are created after the fact | |
| cost: median step lc / nolc; nolc p99 | 33–43 / 36–55 ms; 1.3–2.2 s | 36–41 / 47–54 ms; 1.3–1.7 s | see §9 for the wall-time slowdown |

### §17 H (`expH/s1_r*.json`, `s1far_r*.json`), drift at the end of loss (effective), mm
| loss | EKF3 (flying, unchanged) | UKF shadow old → new | FGO shadow old → new |
|---|---|---|---|
| S1 r1–r3, 5 s | 13–27 | 32–49 → 11–19 | 14–25 → 9–18 |
| S1, 15 s | 6–25 | 120–145 → 5–22 | 50–63 → 4–20 |
| S1, 30 s | 3–11 | 282–292 → 4–9 | 107–114 → 1–8 |
| S1, ~7 s move | 7–31 | 40–57 → 8–19 | 1–7 → 0.5–8 |
| S1-far r1, r2 (5/15/30/move) | — | 31,41 / 127,118 / 288,267 / 70,51 → 12,10 / 9,11 / 6,25 / 13,16 | 7,21 / 71,58 / 136,114 / 37,19 → 7,11 / 5,12 / 0.5,26 / 22,4 |
| S1-far **r3b** (new only) | 11 / 17 / 11 / 13 | — → 7 / 10 / 10 / 10 | — → 7 / 6 / 12 / 1 |

- P-H5 PASS 20/20 for each estimator, old and new; r3b 4/4.
- P-H7 (no lockout) PASS.
- Re-lock (effective) 0 ms, unchanged.
- The S1-far bands (UKF ≤ 100/200/400/300, FGO ≤ 50/100/200/150 mm) pass old and new.
- **⚑ Wording:** the shadows now drift at EKF3's scale, so "the S1→S2/S3 gap closes" becomes "there is no gap
  between shadow and flying".

---

## 4. Confirmatory EKF3-vs-FGO test (step 2)

**Sign convention, from `eval/dsn_paired_test.py`.** `d_i = evo(EKF3) − evo(FGO)` (evo -a cruise), i = r4…r10.
Negative d means EKF3 is lower.

**Original decision rule (unchanged):**
- "EKF3 lower" iff (a) d < 0 on ≥ 6 of 7 AND (b) the 95 % t-interval (df = n − 1) of mean d excludes 0.
- "FGO lower" by the mirror rule; otherwise "no ordering claimed".
- r10 has no FGO value (IMU-gap rule) and counts against both orderings.

| | old (pre-correction FGO) | new (corrected FGO) |
|---|---|---|
| d per flight (r4…r9) | −0.506, −0.494, −1.607, −0.500, −0.506, −0.501 | −0.347, −0.478, **+1.681**, −0.484, −0.450, −0.165 |
| d < 0 / d > 0 (of 7) | 6 / 0 | 5 / 1 |
| mean d, 95 % CI | −0.686 m [−1.159, −0.212] | −0.040 m [−0.934, +0.853] |
| one-sided sign-test p (EKF3 lower / FGO lower) | 0.0625 / 1.0 | 0.227 / 0.992 |
| **verdict as worded** | **EKF3 lower (both (a) and (b) met)** | **no ordering claimed**: (a) fails (5 of 7) and (b) fails (the CI contains 0) |

- **The df detail does not change the verdict.** The registered text says df 6; the code uses n − 1 = 5, because r10
  has no FGO value (as in the old run). (a) fails at 5/7 regardless, and with df 6 the interval is still about
  ±0.85 m around −0.04, so it contains 0. The verdict holds against the original rule either way.
- **The driver is r6.** On r6 the FGO is 1.43 m against EKF3's 3.11. Excluding r6 would be post hoc and is not done.
- The original result came from an FGO with a mis-specified noise model.

---

## 5. Phase 4/5 bands recomputed from the corrected `dsn` (`rerun_p4_bands.json`)

The EKF3 bands are unchanged. The FGO bands follow the same formula on the corrected r1–r3:

| band | old | new | note |
|---|---|---|---|
| FGO textured evo | [4.189, 5.117] m | **[−0.614, 7.017] m** | ⚑ degenerate: the n = 3 range 1.93–4.47 widened by one range-width gives a negative lower bound. It cannot fail any plausible textured value |
| FGO transition ratio | [42.136, 56.507] | [1.406, 49.073] | † runaway size |
| FGO transition onset | [84.534, 94.662] m | [88.25, 98.315] m | |
| FGO blank ratio | [168.038, 212.519] | [18.009, 342.823] | † |
| FGO blank onset | [0.232, 11.58] m | [12.099, 23.679] m | |

**Consequence for §8.**
- fwdc goes 6/9 → 8/9 and fwdplainc 8/9 → 9/9. p1c stays 6/6.
- Part of this comes from the wider bands, not from better estimates:
  - `fwdc_tex_r2` FGO (2.39) and `p1c_fwdc_tex` FGO (5.20) would both fail the old textured band;
  - every transition and blank FGO ratio and onset now sits in a band moved by the FGO's own change.
- The remaining fwdc miss, `fwdc_tex_r2` EKF3 (0.01 m outside [3.613, 4.340]), is unchanged.

---

## 6. Closed-loop FGO contact: registered prediction (scored as worded) and the POST-HOC recomputation

**Registered (pre-flight) prediction, scored as worded.**
- U3: west-wall contact inside [+145, +196] s (open-loop method, median of 10 realisations, +169.6 s).
- The final corrected FGO flight `cl_fgo_a_tex_half_v3` reached the west wall at **+169.9 s → U3 PASS**, with U1/U2
  PASS (METHODOLOGY).
- The registered prediction and its band stand (ruling 2).

**POST-HOC consistency check. This is NOT a prediction: the flight had already flown.** Source:
`fgo_contact_prediction_half_final.json`, the corrected FGO replayed open loop on the same realisations.

| realisation | old (registered input) | new (corrected FGO) |
|---|---|---|
| `cl_a_tex_half` | +169.9 west | +215.5 **east** |
| `cl_bcpp_tex_r1_half` | +170.8 west | +139.1 **east** |
| `cl_bcpp_tex_r2_half` | +160.1 west | +154.0 west |
| `cl_bcpp_tex_r3_half` | +167.0 west | +162.9 west |
| `cl_ukf_a_tex_half` | +165.9 west | **no contact** (East error +3.6 m at end) |
| `cl_ukf_b_tex_r1_half` | +169.6 west | +182.2 west |
| `cl_ukf_b_tex_r2_half` | +168.5 west | +197.8 west |
| `cl_ukf_b_tex_r3_half` | +170.0 west | +116.3 **east** |
| `fgo_shadow_half_a` offline; live `XFGO` | +169.7; +169.4 west | **not recomputed** (not in the job list) |

- n = 8 against the original 10.
- Walls: 4 west, 3 east, 1 none. The west contacts are +154 … +198 s; the median of the 7 contacts is +162.9 s.
- **Reading:** with the corrected FGO, the open-loop drift direction is no longer consistent across realisations, so
  the method would not have produced a tight west cluster. The flown result (+169.9 west) sits inside the
  registered window, which was set from the old, consistent cluster.

---

## 7. D27 item 3: FGO side on the `_v3` re-flights (UKF side OPEN)

*Not reported in the thesis (ruling 2026-10-16, item 6: the UKF per-heading weight comparison is dropped from all thesis-facing material). Kept here and in `numbers.md` §15, marked "not reported".*

Sources:
- `~/thesis_data/batches/final_rerun/d26gate_cl_fgo_b_tex_r{1,3}_half_v3.txt`;
- `core_*.txt` (node-core replay of the flown `_v3` heading flights, `--save-npz`, `d26_fgo_gate.py`).

| | D26 (original flight r3, pre-correction FGO) | `_v3` r1 | `_v3` r3 |
|---|---|---|---|
| headings evaluated / accepted / gated | 2,359 / 2,359 / 0 | 2,394 / 2,394 / 0 | 2,382 / 2,382 / 0 |
| predicted heading σ at the gate | 2.17° | median 0.57° (290–320 s windows) | median 0.57–0.59° |
| largest innovation in the end-wall windows | 11.6° (NIS 4.55) | 5.65° (NIS 1.26) | 10.10° (NIS 4.03) |
| per-heading weight σ²/(σ² + R²), R = 5° | 15.9 % | **≈ 1.3 %** | **≈ 1.3–1.4 %** |
| FGO yaw swing across that outlier | 1.6–1.9° | — | ≈ 0.14° (−0.29 → −0.43° within the 302–305 s window) |

- **How the weight was derived.** It comes from the window MEDIAN predicted σ, because the log has no per-heading σ
  for the outlier itself. It is consistent with the observed swing: 10.1° × 1.3 % ≈ 0.13°.
- **R = 5° confirmed from the log, not assumed.** The heading bridge's `HEADING_SIGMA_DEG 0.148` is not the R used at
  the gate. The logged NIS fixes it: 10.10² / (0.57² + 5²) = 4.03 matches r3's logged NIS 4.03, and
  5.65² / 25.3 = 1.26 matches r1's logged 1.26.
- **The structural 15.9 % FGO weighting is gone** on the corrected FGO.
- **No FGO/UKF ratio is restated.** The UKF figure (2.9 %, σ 0.86°) is from the OLD UKF on a different flight.
  **The UKF side is OPEN** (ruling 4: it needs the port's SITL Replay).
- **F3 prior-induced lockout re-measurement** (`f3_test.json`): the FGO's Δ30 lockout is gone (convergence 176–182 s
  → 0.0–0.1 s). At Δ60 both estimators still converge late or not at all.

---

## 8. Sensitivity rows (`eval/results/*_final.json`)

**These are NOT like-for-like with the old `numbers.md` rows.**
- The old rows (M:L76-77, M:L93) were computed on the pre-re-fly `dsn` bags.
- EKF3, which is byte-identical in the re-run, also changes between the old rows and the new ones (clock shift
  0.002–0.009 → 0.012 m). That shows a different bag set.
- The new values are therefore given on their own, with no correction delta.

| row | old (`numbers.md`, pre-re-fly bags) | new (`*_final.json`, re-flown `dsn_tex` r1–r3) |
|---|---|---|
| clock shift ±0.25/±0.5 s, max \|Δ evo -a (cruise)\|, textured EKF3 / UKF / FGO | 0.002–0.009 / 0.007–0.009 / 0.014–0.015 m | **0.012 / 0.009–0.013 / 0.012–0.013 m** (`phase0_cruise_pinned_final.json`) |
| speed threshold 0.20 m/s, max \|Δ\| vs 0.30 | 0.005 / 0.038 / 0.009 m | **0.009 / 0.009 / 0.008 m** (`threshold_0.20_final.json`) |
| speed threshold 0.40 m/s | 0.008 / 0.043 / 0.011 m | **0.009 / 0.010 / 0.008 m** (`threshold_0.40_final.json`) |

- All three estimators are now ≤ 0.013 m on textured flights, against between-estimator gaps of 0.1–2.5 m.
- Transition and blank shifts are large (UKF/FGO 4–58 m), but these are runaway magnitudes (†).
- The old, non-`_final` `threshold_*.json` and `phase0_cruise_pinned.json` are still in `eval/results`. Do not cite
  them against the new baseline.

---

## 9. L job slowdown (report only)

| job | old wall (`results_pre_final/expL/logs`) | new wall (`batches/final_L/logs`) | keyframes / landmarks / landmark factors | step median / p99 old → new |
|---|---|---|---|---|
| nolc T_A_r1 | 2,996 s | **11,175 s** | 7,351 / 41 / 2,145 (same) | 35.9 ms / 1.32 s → 46.9 ms / 1.67 s |
| nolc T_A_r2 | 1,728 s | **9,903 s** | 7,351 / 41 / 2,057 (same) | 54.5 / 1.58 → 54.3 / 1.34 |
| nolc T_A_r3 | 1,044 s | **9,868 s** | 7,351 / 41 / 2,038 (same) | 52.5 / 2.15 → 52.9 / 1.59 |
| lc T_A_r1–r3 | 301–382 s | 303–511 s | identical | 33–43 → 36–41 ms |

- **The graph is the same size.** Keyframes, landmarks and factors are identical, and the median and p99 step times
  are similar.
- **The extra time sits in rare steps beyond p99.**
  - The mean step is 1.34–1.52 s new against 0.14–0.41 s old.
  - It starts at about keyframe 3,000–4,000 (≥ 17–23 landmarks). The worst 1,000-keyframe block takes 3,500–7,100 s
    per job, against at most ~1,400 s before.
- **The old wall times already varied about 3×** (1,044–2,996 s), so the cost of those rare steps was already erratic.
- **Load is not an obvious cause.** The three nolc jobs ran in parallel with the lc/V-L jobs only until 02:23 (14 min
  in) and alone thereafter.
- **No per-step timing log exists**, so the slow steps cannot be located from the stored output. **Cause untraced.**
- **Results are unaffected:** all H-L verdicts are unchanged.
- **By contrast, the F3c FGO jobs got much faster.** The `ftests` stage took 64 min against an estimated 2.5–4 h.

---

## 10. Questions that need a user ruling

1. **Plain-wall FGO divergence (§2.1).**
   - The corrected, hard-gated FGO with heading diverges in yaw on fwdplainc textured and transition (bgz runs away;
     ~20 headings fused). C0 reverses on plain walls, and the F1/F4 FGO_hard plain-wall arms reach 180°.
   - Options:
     - (a) report it as a property of the corrected FGO;
     - (b) a bounded trace (offline, no flights) before the freeze;
     - (c) both.
   - It also bears on any real plain-wall flight with the hard-gated FGO.
2. **Confirmatory test.** As worded, the verdict flips from "EKF3 lower" to "no ordering claimed" (d = EKF3 − FGO;
   5/7 negative; CI [−0.93, +0.85]). Confirm that the new verdict replaces the old one, with the original result
   labelled as computed with the mis-specified noise model.
3. **Degenerate P4 FGO textured band [−0.614, 7.017].** Is it kept as computed by the registered formula, with the
   fwdc 8/9, fwdplainc 9/9 and p1c 6/6 counts reported with that caveat? Or is it flagged as uninformative, which
   would put `fwdc_tex_r2` and `p1c_fwdc_tex` FGO at FAIL under the old band?
4. **F2 NOT met → MET, and F3c (b) TRUE → FALSE.** Accept both flips as worded?
5. **O.**
   - P-O3 FAIL → PASS, because the FGO batch worsened (0.33 → 0.59 m) to the RTS-UKF's level.
   - The "FGO batch ≈ 2× better than RTS-UKF" and "cap-free RTS-UKF worse" statements are withdrawn.
   - Accept? Should the FGO batch's worsening be explained before it is quoted (no trace was done)?
6. **H narrative.** The UKF/FGO shadows now drift at EKF3's scale (mm). Restate §17 and the S1→S2/S3 comparison as "no
   shadow-vs-flying gap"?
7. **T.** FGO live in condition D (0.082) is now below EKF3 live (0.096). Is this mentioned as an ordering (n = 3,
   repeats agree within 8 mm), or as descriptive only?
8. **F1 near-flip.** F1 is still NOT met, but only through a lockout tie (3 = 3); the robust FGO now has the lower yaw
   max on 6/6. Report it as "NOT met (lockout tie)"?
9. **Wording drift.**
   - The UKF take-off kick bound "≤ 0.79°" becomes ≤ 0.82°.
   - "UKF lower yaw error than FGO with heading (about 2×)" no longer holds on fwdc (they are equal).
   - 2(a)'s "UKF lower yaw max 10/10" reverses (robust FGO lower on 8/10).
   - Update these wordings?
10. **`rerun_compare.py`.** Fix the 6.4/7/8 old-file mapping (`rerun_*` on both sides; bands from
    `results_pre_final/rerun_p4_bands.json`) and regenerate the md? This would also remove the 7 artefact flags.
    It was not edited in this stage.
11. **Contact prediction.** The post-hoc recomputation covers 8 of the 10 original realisations (no `fgo_shadow_half_a`
    and no live `XFGO`). Is that enough for the consistency statement?
12. **Attribution.** The attribution study (ruled, "only if time allows") was not run, so no change here is attributed
    to a single correction. Run it, at least on the plain-wall divergence and the O FGO batch?

---

## Appendix: flag-by-flag classification (all 95 rows of `final_old_vs_new.md`, in file order)

| # | section | quantity | old → new | class | evidence |
|---|---|---|---|---|---|
| 1 | 6.1 dsn textured evo -a (cruise), m | ordering: mean EKF3 − mean FGO | -0.641 → 0.505 (DIRECTION) | REAL | Same data on both sides (`dsn_dejitter_baseline` = `rerun_dsn_evo` in the old snapshot). FGO r1–r3 4.59/4.72/4.60 → 4.07/1.93/4.47; UKF 4.23/2.14/5.38 → 3.98/1.61/5.17; EKF3 unchanged. Driven by r2. |
| 2 | 6.1 dsn textured evo -a (cruise), m | ordering: mean UKF − mean FGO | -0.723 → 0.098 (DIRECTION) | REAL | Same data on both sides (`dsn_dejitter_baseline` = `rerun_dsn_evo` in the old snapshot). FGO r1–r3 4.59/4.72/4.60 → 4.07/1.93/4.47; UKF 4.23/2.14/5.38 → 3.98/1.61/5.17; EKF3 unchanged. Driven by r2. |
| 3 | 6.4 fwdc trans failure metrics | FGO ratio, mean of 3 | 0.71 → 19.38 (DIRECTION) | ARTEFACT | Old side read `fwdc_evo.json`/`fwdplainc_evo.json` (2026-09-24, the superseded pre-re-fly flights; EKF3 trans evo 21.4–22.1 m there against 41.5 m in the re-flown set, although every EKF3 gate shows 0 differences). Same-file old (`results_pre_final/rerun_*_evo.json`) → new: see the corrected-value table; no crossing of 1. |
| 4 | 6.4 fwdc trans failure metrics | UKF ratio, mean of 3 | 0.81 → 6.70 (DIRECTION) | ARTEFACT | Old side read `fwdc_evo.json`/`fwdplainc_evo.json` (2026-09-24, the superseded pre-re-fly flights; EKF3 trans evo 21.4–22.1 m there against 41.5 m in the re-flown set, although every EKF3 gate shows 0 differences). Same-file old (`results_pre_final/rerun_*_evo.json`) → new: see the corrected-value table; no crossing of 1. |
| 5 | 6.4 fwdplainc trans failure metrics | FGO ratio, mean of 3 | 0.71 → 19.32 (DIRECTION) | ARTEFACT | Old side read `fwdc_evo.json`/`fwdplainc_evo.json` (2026-09-24, the superseded pre-re-fly flights; EKF3 trans evo 21.4–22.1 m there against 41.5 m in the re-flown set, although every EKF3 gate shows 0 differences). Same-file old (`results_pre_final/rerun_*_evo.json`) → new: see the corrected-value table; no crossing of 1. |
| 6 | 6.4 fwdplainc trans failure metrics | UKF ratio, mean of 3 | 0.74 → 6.41 (DIRECTION) | ARTEFACT | Old side read `fwdc_evo.json`/`fwdplainc_evo.json` (2026-09-24, the superseded pre-re-fly flights; EKF3 trans evo 21.4–22.1 m there against 41.5 m in the re-flown set, although every EKF3 gate shows 0 differences). Same-file old (`results_pre_final/rerun_*_evo.json`) → new: see the corrected-value table; no crossing of 1. |
| 7 | 8 dataset primary pass counts | fwdc_tex_r2 verdict | PASS [] → FAIL ['P4 EKF3 evo -a (cruise)'] (DIRECTION) | ARTEFACT | Old side read `*_score.json` (pre-re-fly flights). Same-file old (`rerun_*_score.json`): this trial's verdict is unchanged (see the corrected-value table). |
| 8 | 8 dataset primary pass counts | fwdc_trans_r1 verdict | FAIL ['P3 flow_y_raw'] → PASS [] (DIRECTION) | ARTEFACT | Old side read `*_score.json` (pre-re-fly flights). Same-file old (`rerun_*_score.json`): this trial's verdict is unchanged (see the corrected-value table). |
| 9 | 8 dataset primary pass counts | p1c_fwdplainc_trans verdict | FAIL ['P3 flow_y_raw'] → PASS [] (DIRECTION) | ARTEFACT | Old side read `*_score.json` (pre-re-fly flights). Same-file old (`rerun_*_score.json`): this trial's verdict is unchanged (see the corrected-value table). |
| 10 | P4 fwdplainc tex: heading arm effect (heading − baseline evo, mean), m | FGO | -4.21 → 38.53 (DIRECTION) | REAL | FGO +heading on plain walls now diverges in yaw: bgz −267…−319 deg/min (true +8.9), 21–28 of 6,197–6,333 headings fused, NIS median 1,740–2,581; evo 0.20/0.61/0.22 → 43.5/42.7/43.1 m. |
| 11 | P4 fwdplainc tex: ordering FGO_heading − EKF3 (evo mean), m | FGO | -3.73 → 39.04 (DIRECTION) | REAL | FGO +heading on plain walls now diverges in yaw: bgz −267…−319 deg/min (true +8.9), 21–28 of 6,197–6,333 headings fused, NIS median 1,740–2,581; evo 0.20/0.61/0.22 → 43.5/42.7/43.1 m. |
| 12 | P4 fwdplainc blank: heading arm effect (heading − baseline evo, mean), m | FGO | -1060.02 → 1337.23 (DIRECTION) | REAL (not interpretable) | Difference of two diverged blank-floor magnitudes (baseline 7.0–7.9 km, heading 8.2–9.7 km evo); †-rule: evidence of divergence only, no ordering. |
| 13 | P5 end wall (GT y > 140 m): wrong (> 3°) valid headings fused / wrong | fwdc FGO_heading | 2 / 11 → 0 / 11 (DIRECTION) | REAL | FGO predicted yaw σ at the gate 0.476° → 0.057° (`phase5b` checker_S), now the UKF's; the 2 wrong end-wall headings it used to fuse (fwdc_tex_r1, fwdc_trans_r1) are rejected, as the UKF always did. |
| 14 | P5 end wall (GT y > 140 m): wrong (> 3°) valid headings fused / wrong | fwdc FGO_heading_yawrate | 2 / 11 → 0 / 11 (DIRECTION) | REAL | FGO predicted yaw σ at the gate 0.476° → 0.057° (`phase5b` checker_S), now the UKF's; the 2 wrong end-wall headings it used to fuse (fwdc_tex_r1, fwdc_trans_r1) are rejected, as the UKF always did. |
| 15 | P5 fwdplainc tex: heading share of lateral velocity error, mean of 3 | UKF_heading | 0.36 → 1.03 (DIRECTION) | REAL | UKF +heading share per bag 1.41/1.67/−1.99 → 1.06/1.01/1.01; the old mean (0.36) was pulled below 0.5 by the r3 outlier, so the 'crossing' is that outlier going away. |
| 16 | P5 end wall (GT y > 140 m): wrong (> 3°) valid headings fused / wrong | fwdplainc FGO_heading | 17 / 48 → 0 / 48 (DIRECTION) | REAL (mixed cause) | Old 17 fused = blank 6 + trans 11 (tex 0). New 0: on blank the FGO fuses normally (8,609–8,631 headings) and now rejects the wrong ones (genuine, predicted yaw σ 0.48° → 0.06°); on trans the FGO is locked out by the yaw-bias runaway (19–26 fused in total), so 0 there is not a gate win. |
| 17 | P5b fwdc tex: cross-track mean 1-D NEES (consistent ≈ 1; flagged across 3) | UKF_baseline | 4.35 → 2.35 (DIRECTION) | REAL | UKF baseline NEES falls (derotation/jitter fixes); per bag e.g. fwdc blank 3.1/5.3/21.3 → 1.7/2.7/0.5. |
| 18 | P5b fwdc tex: cross-track mean 1-D NEES (consistent ≈ 1; flagged across 3) | FGO_baseline | 57.11 → 1.67 (DIRECTION) | REAL | FGO baseline cross-track NEES per bag 55–59 → 0.2–3.0 (textured, both datasets); the noise-model fix makes the FGO covariance consistent (it was ~57× over-confident). |
| 19 | P5b fwdc blank: cross-track mean 1-D NEES (consistent ≈ 1; flagged across 3) | UKF_baseline | 9.87 → 1.62 (DIRECTION) | REAL | UKF baseline NEES falls (derotation/jitter fixes); per bag e.g. fwdc blank 3.1/5.3/21.3 → 1.7/2.7/0.5. |
| 20 | P5b fwdplainc tex: cross-track mean 1-D NEES (consistent ≈ 1; flagged across 3) | FGO_baseline | 55.90 → 2.65 (DIRECTION) | REAL | FGO baseline cross-track NEES per bag 55–59 → 0.2–3.0 (textured, both datasets); the noise-model fix makes the FGO covariance consistent (it was ~57× over-confident). |
| 21 | P5b fwdplainc tex: cross-track mean 1-D NEES (consistent ≈ 1; flagged across 3) | FGO_heading | 0.05 → 24.83 (DIRECTION) | REAL | Plain-wall FGO +heading runaway (see P4): NEES 0.02–0.09 → 16.9–30.3. |
| 22 | P5b fwdplainc trans: cross-track mean 1-D NEES (consistent ≈ 1; flagged across 3) | UKF_heading | 0.54 → 3.94 (DIRECTION) | REAL | UKF +heading NEES on plain-wall transition 1.45/0.10/0.06 → 2.09/6.87/2.86. |
| 23 | P5b fwdplainc blank: cross-track mean 1-D NEES (consistent ≈ 1; flagged across 3) | UKF_baseline | 10.14 → 2.03 (DIRECTION) | REAL | UKF baseline NEES falls (derotation/jitter fixes); per bag e.g. fwdc blank 3.1/5.3/21.3 → 1.7/2.7/0.5. |
| 24 | P5b endwall_S: yaw-prediction NEES mean | fwdc/FGO | 1.69 → 12.92 (DIRECTION) | REAL | Consequence of the narrower FGO yaw σ (0.48° → 0.06°): the FGO's end-wall yaw-prediction NEES now equals the UKF's (12.9 vs 13.4). |
| 25 | P5b endwall_S: yaw-prediction NEES mean | fwdplainc/UKF | 2.97 → 3.02 (DIRECTION) | REAL (trivial) | UKF end-wall NEES 2.97 → 3.02 crosses 3 by 0.05. |
| 26 | T (§16.1) orderings (mean RMSE difference), m | D: FGO live − EKF3 live | 0.0254 → -0.0139 (DIRECTION) | REAL | FGO live D 0.122 → 0.082 m, now below EKF3 live 0.096 m (EKF3 unchanged). |
| 27 | T (§16.1) P-T2 hindsight gain (median), m | C | -0.0069 → 0.0373 (DIRECTION) | REAL | RTS-UKF improves in C/D (0.091 → 0.039, 0.258 → 0.109 m), so its hindsight gain turns positive; P-T2 still FAILS (medians not strictly increasing: 0.020/0.032/0.037/0.029; p = 0.11). |
| 28 | T (§16.1) P-T2 hindsight gain (median), m | D | -0.1256 → 0.0291 (DIRECTION) | REAL | RTS-UKF improves in C/D (0.091 → 0.039, 0.258 → 0.109 m), so its hindsight gain turns positive; P-T2 still FAILS (medians not strictly increasing: 0.020/0.032/0.037/0.029; p = 0.11). |
| 29 | T (§16.1) P-T2 hindsight gain (median), m | Spearman rho | -0.164 → 0.110 (DIRECTION) | REAL | RTS-UKF improves in C/D (0.091 → 0.039, 0.258 → 0.109 m), so its hindsight gain turns positive; P-T2 still FAILS (medians not strictly increasing: 0.020/0.032/0.037/0.029; p = 0.11). |
| 30 | T (§16.1) P-T3 max/min ratio (band ≤ 1.5) | C | 1.803 → 1.427 (VERDICT) | REAL | C live ratio 1.80 → 1.43 (UKF live 0.104 → 0.076). P-T3 still FAILS (A 1.97, B 2.36, D 1.59). |
| 31 | O (§16.2) orderings (indoor RMSE difference), m | O_r1: FGO batch − RTS-UKF | -0.313 → 0.014 (DIRECTION) | REAL | FGO batch 0.328/0.332/0.330 → 0.589/0.590/0.588 m (worse) while RTS-UKF 0.641/0.611/0.602 → 0.575/0.582/0.599; they now agree to ~1–2 %. |
| 32 | O (§16.2) orderings (indoor RMSE difference), m | O_r1: FGO live − UKF live | 0.342 → -0.010 (DIRECTION) | REAL | UKF live worse (0.633 → 0.838 m) and FGO live better (0.975 → 0.828 m) on O_r1; difference −0.010 m is within flight-to-flight spread (O_r2 +0.029, O_r3b +0.119). |
| 33 | O (§16.2) P-O3 FGO batch vs RTS-UKF max/min (band ≤ 1.5) | O_r1 (capped) | 1.954 → 1.024 (VERDICT) | REAL (verdict flip) | P-O3 0/3 FAIL → 3/3 PASS, because the FGO batch got WORSE (0.33 → 0.59 m), not because the RTS-UKF improved much; cap-free RTS-UKF 0.97–0.98 → 0.60–0.62 m. |
| 34 | O (§16.2) P-O3 FGO batch vs RTS-UKF max/min (band ≤ 1.5) | O_r1 (cap-free) | 2.985 → 1.015 (VERDICT) | REAL (verdict flip) | P-O3 0/3 FAIL → 3/3 PASS, because the FGO batch got WORSE (0.33 → 0.59 m), not because the RTS-UKF improved much; cap-free RTS-UKF 0.97–0.98 → 0.60–0.62 m. |
| 35 | O (§16.2) orderings (indoor RMSE difference), m | O_r2: FGO batch − RTS-UKF | -0.280 → 0.008 (DIRECTION) | REAL | FGO batch 0.328/0.332/0.330 → 0.589/0.590/0.588 m (worse) while RTS-UKF 0.641/0.611/0.602 → 0.575/0.582/0.599; they now agree to ~1–2 %. |
| 36 | O (§16.2) P-O3 FGO batch vs RTS-UKF max/min (band ≤ 1.5) | O_r2 (capped) | 1.843 → 1.013 (VERDICT) | REAL (verdict flip) | P-O3 0/3 FAIL → 3/3 PASS, because the FGO batch got WORSE (0.33 → 0.59 m), not because the RTS-UKF improved much; cap-free RTS-UKF 0.97–0.98 → 0.60–0.62 m. |
| 37 | O (§16.2) P-O3 FGO batch vs RTS-UKF max/min (band ≤ 1.5) | O_r2 (cap-free) | 2.932 → 1.025 (VERDICT) | REAL (verdict flip) | P-O3 0/3 FAIL → 3/3 PASS, because the FGO batch got WORSE (0.33 → 0.59 m), not because the RTS-UKF improved much; cap-free RTS-UKF 0.97–0.98 → 0.60–0.62 m. |
| 38 | O (§16.2) P-O3 FGO batch vs RTS-UKF max/min (band ≤ 1.5) | O_r3b (capped) | 1.826 → 1.018 (VERDICT) | REAL (verdict flip) | P-O3 0/3 FAIL → 3/3 PASS, because the FGO batch got WORSE (0.33 → 0.59 m), not because the RTS-UKF improved much; cap-free RTS-UKF 0.97–0.98 → 0.60–0.62 m. |
| 39 | O (§16.2) P-O3 FGO batch vs RTS-UKF max/min (band ≤ 1.5) | O_r3b (cap-free) | 2.944 → 1.054 (VERDICT) | REAL (verdict flip) | P-O3 0/3 FAIL → 3/3 PASS, because the FGO batch got WORSE (0.33 → 0.59 m), not because the RTS-UKF improved much; cap-free RTS-UKF 0.97–0.98 → 0.60–0.62 m. |
| 40 | O verdicts | P-O3 batch vs RTS-UKF ≤ 1.5 (capped), flights | 0/3 (FAIL) → 3/3 (PASS) (VERDICT) | REAL (verdict flip) | P-O3 0/3 FAIL → 3/3 PASS, because the FGO batch got WORSE (0.33 → 0.59 m), not because the RTS-UKF improved much; cap-free RTS-UKF 0.97–0.98 → 0.60–0.62 m. |
| 41 | O verdicts | P-O3 batch vs RTS-UKF ≤ 1.5 (cap-free), flights | 0/3 (FAIL) → 3/3 (PASS) (VERDICT) | REAL (verdict flip) | P-O3 0/3 FAIL → 3/3 PASS, because the FGO batch got WORSE (0.33 → 0.59 m), not because the RTS-UKF improved much; cap-free RTS-UKF 0.97–0.98 → 0.60–0.62 m. |
| 42 | H (§17) orderings (drift at end of loss, difference), m | s1_r1 loss 1 (5 s) UKF − EKF3 | 0.0140 → -0.0032 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 43 | H (§17) orderings (drift at end of loss, difference), m | s1_r1 loss 2 (15 s) UKF − EKF3 | 0.1112 → -0.0016 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 44 | H (§17) orderings (drift at end of loss, difference), m | s1_r1 loss 2 (15 s) FGO − EKF3 | 0.0427 → -0.0017 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 45 | H (§17) orderings (drift at end of loss, difference), m | s1_r1 loss 3 (30 s) UKF − EKF3 | 0.2778 → -0.0046 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 46 | H (§17) orderings (drift at end of loss, difference), m | s1_r1 loss 3 (30 s) FGO − EKF3 | 0.0994 → -0.0049 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 47 | H (§17) orderings (drift at end of loss, difference), m | s1_r1 loss 4 (move) UKF − EKF3 | 0.0011 → -0.0227 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 48 | H (§17) orderings (drift at end of loss, difference), m | s1_r2 loss 1 (5 s) FGO − UKF | -0.0211 → 0.0011 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 49 | H (§17) orderings (drift at end of loss, difference), m | s1_r2 loss 1 (5 s) UKF − EKF3 | 0.0168 → -0.0077 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 50 | H (§17) orderings (drift at end of loss, difference), m | s1_r2 loss 2 (15 s) UKF − EKF3 | 0.1131 → -0.0029 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 51 | H (§17) orderings (drift at end of loss, difference), m | s1_r2 loss 2 (15 s) FGO − EKF3 | 0.0352 → -0.0048 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 52 | H (§17) orderings (drift at end of loss, difference), m | s1_r2 loss 3 (30 s) UKF − EKF3 | 0.2738 → -0.0007 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 53 | H (§17) orderings (drift at end of loss, difference), m | s1_r2 loss 3 (30 s) FGO − EKF3 | 0.1024 → -0.0020 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 54 | H (§17) orderings (drift at end of loss, difference), m | s1_r2 loss 4 (move) UKF − EKF3 | 0.0456 → -0.0032 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 55 | H (§17) orderings (drift at end of loss, difference), m | s1_r3 loss 1 (5 s) UKF − EKF3 | 0.0121 → -0.0100 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 56 | H (§17) orderings (drift at end of loss, difference), m | s1_r3 loss 2 (15 s) FGO − EKF3 | 0.0428 → -0.0033 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 57 | H (§17) orderings (drift at end of loss, difference), m | s1_r3 loss 3 (30 s) FGO − EKF3 | 0.1011 → -0.0024 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 58 | H (§17) orderings (drift at end of loss, difference), m | s1_r3 loss 4 (move) UKF − EKF3 | 0.0317 → -0.0067 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 59 | H (§17) orderings (drift at end of loss, difference), m | s1far_r1 loss 1 (5 s) FGO − UKF | -0.0077 → 0.0013 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 60 | H (§17) orderings (drift at end of loss, difference), m | s1far_r1 loss 1 (5 s) UKF − EKF3 | 0.0088 → -0.0033 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 61 | H (§17) orderings (drift at end of loss, difference), m | s1far_r1 loss 1 (5 s) FGO − EKF3 | 0.0010 → -0.0020 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 62 | H (§17) orderings (drift at end of loss, difference), m | s1far_r1 loss 2 (15 s) UKF − EKF3 | 0.1075 → -0.0024 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 63 | H (§17) orderings (drift at end of loss, difference), m | s1far_r1 loss 2 (15 s) FGO − EKF3 | 0.0554 → -0.0060 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 64 | H (§17) orderings (drift at end of loss, difference), m | s1far_r1 loss 3 (30 s) FGO − EKF3 | 0.1282 → -0.0029 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 65 | H (§17) orderings (drift at end of loss, difference), m | s1far_r1 loss 4 (move) FGO − UKF | -0.0260 → 0.0101 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 66 | H (§17) orderings (drift at end of loss, difference), m | s1far_r2 loss 1 (5 s) FGO − UKF | -0.0165 → 0.0004 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 67 | H (§17) orderings (drift at end of loss, difference), m | s1far_r2 loss 1 (5 s) UKF − EKF3 | 0.0151 → -0.0080 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 68 | H (§17) orderings (drift at end of loss, difference), m | s1far_r2 loss 2 (15 s) FGO − UKF | -0.0559 → 0.0010 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 69 | H (§17) orderings (drift at end of loss, difference), m | s1far_r2 loss 2 (15 s) UKF − EKF3 | 0.0977 → -0.0006 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 70 | H (§17) orderings (drift at end of loss, difference), m | s1far_r2 loss 3 (30 s) FGO − UKF | -0.1477 → 0.0005 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 71 | H (§17) orderings (drift at end of loss, difference), m | s1far_r2 loss 3 (30 s) UKF − EKF3 | 0.2331 → -0.0012 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 72 | H (§17) orderings (drift at end of loss, difference), m | s1far_r2 loss 3 (30 s) FGO − EKF3 | 0.0854 → -0.0007 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 73 | H (§17) orderings (drift at end of loss, difference), m | s1far_r2 loss 4 (move) UKF − EKF3 | 0.0246 → -0.0139 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 74 | H (§17) orderings (drift at end of loss, difference), m | s1far_r2 loss 4 (move) FGO − EKF3 | 0.0005 → -0.0179 (DIRECTION) | REAL (not interpretable as ordering) | UKF/FGO shadow drift now at EKF3's scale: e.g. 30 s loss UKF 0.27–0.29 m → 3–25 mm, FGO 0.10–0.13 m → 0.5–25 mm (EKF3 3–26 mm, unchanged). Differences of a few mm carry no ordering. |
| 75 | F1 orderings: FGO_robust − FGO_hard yaw max, deg | fwdplainc_tex_r1 | 0.714 → -178.499 (DIRECTION) | REAL | FGO_hard on plain walls diverges (yaw max 179.9–180.0°, rms 106–110°, 4,393–4,445 correct headings rejected, 4–5 lockouts); FGO_robust is now good (1.4–2.2°). |
| 76 | F2 orderings (off-region cross-track RMS difference), m | fwdc_tex_r1 FGO batch − FGO live | -0.102 → 0.026 (DIRECTION) | REAL (descriptive, not the criterion) | Off-region cross-track differences of 2.5–10 cm; the F2 criterion is yaw RMS, not cross-track. |
| 77 | F2 orderings (off-region cross-track RMS difference), m | fwdc_tex_r2 FGO live − UKF live | -0.248 → 0.097 (DIRECTION) | REAL (descriptive, not the criterion) | Off-region cross-track differences of 2.5–10 cm; the F2 criterion is yaw RMS, not cross-track. |
| 78 | F2 orderings (off-region cross-track RMS difference), m | fwdc_tex_r3 FGO batch − FGO live | -0.102 → 0.025 (DIRECTION) | REAL (descriptive, not the criterion) | Off-region cross-track differences of 2.5–10 cm; the F2 criterion is yaw RMS, not cross-track. |
| 79 | F2 verdict | hindsight_correction (F2 met) | no → yes (DIRECTION) | REAL (verdict flip) | Decision is OFF-interval yaw RMS of the batch below both live arms on all 3 bags: batch 0.063–0.066° vs live 0.32–0.36° (old batch 1.12–1.27° vs UKF 0.21–0.53°). F2 NOT met → MET. |
| 80 | F3 orderings (FGO − UKF cross-track integral), m·s | fwdc_tex_r1 Δ10 | -1.756 → 0.555 (DIRECTION) | REAL | The FGO's Δ30 prior-induced lockout is gone: convergence 176–182 s → 0.0–0.1 s, cross-track integral 434–450 → 0.4–22 m·s. Δ10/Δ30 differences are now ~1 m·s either way. F3 verdict unchanged (NOT met). |
| 81 | F3 per flight | fwdc_tex_r1 ratio_decreasing | no → yes (DIRECTION) | REAL | The FGO's Δ30 prior-induced lockout is gone: convergence 176–182 s → 0.0–0.1 s, cross-track integral 434–450 → 0.4–22 m·s. Δ10/Δ30 differences are now ~1 m·s either way. F3 verdict unchanged (NOT met). |
| 82 | F3 orderings (FGO − UKF cross-track integral), m·s | fwdc_tex_r2 Δ30 | 428.280 → -0.933 (DIRECTION) | REAL | The FGO's Δ30 prior-induced lockout is gone: convergence 176–182 s → 0.0–0.1 s, cross-track integral 434–450 → 0.4–22 m·s. Δ10/Δ30 differences are now ~1 m·s either way. F3 verdict unchanged (NOT met). |
| 83 | F3 orderings (FGO − UKF cross-track integral), m·s | fwdc_tex_r2 Δ60 | -27.731 → 7.472 (DIRECTION) | REAL | The FGO's Δ30 prior-induced lockout is gone: convergence 176–182 s → 0.0–0.1 s, cross-track integral 434–450 → 0.4–22 m·s. Δ10/Δ30 differences are now ~1 m·s either way. F3 verdict unchanged (NOT met). |
| 84 | F3 orderings (FGO − UKF cross-track integral), m·s | fwdc_tex_r3 Δ30 | 431.462 → -0.329 (DIRECTION) | REAL | The FGO's Δ30 prior-induced lockout is gone: convergence 176–182 s → 0.0–0.1 s, cross-track integral 434–450 → 0.4–22 m·s. Δ10/Δ30 differences are now ~1 m·s either way. F3 verdict unchanged (NOT met). |
| 85 | F3c orderings (FGO − UKF cross-track integral), m·s | fwdc_tex_r1 Δ10 | -2.747 → 0.307 (DIRECTION) | REAL | UKF cross-track integral falls ~3× (derotation fix: Δ10 3.11 → 0.82 m·s on r1) while the FGO's rises slightly (0.36 → 1.13); the FGO/UKF ratio is now >1 on r1. |
| 86 | F3c orderings (FGO − UKF cross-track integral), m·s | fwdc_tex_r1 Δ30 | -2.578 → 1.103 (DIRECTION) | REAL | UKF cross-track integral falls ~3× (derotation fix: Δ10 3.11 → 0.82 m·s on r1) while the FGO's rises slightly (0.36 → 1.13); the FGO/UKF ratio is now >1 on r1. |
| 87 | F3c per flight | fwdc_tex_r1 ratio_decreasing | yes → no (DIRECTION) | REAL | UKF cross-track integral falls ~3× (derotation fix: Δ10 3.11 → 0.82 m·s on r1) while the FGO's rises slightly (0.36 → 1.13); the FGO/UKF ratio is now >1 on r1. |
| 88 | F3c orderings (FGO − UKF cross-track integral), m·s | fwdc_tex_r2 Δ30 | 1.959 → -0.399 (DIRECTION) | REAL | UKF cross-track integral falls ~3× (derotation fix: Δ10 3.11 → 0.82 m·s on r1) while the FGO's rises slightly (0.36 → 1.13); the FGO/UKF ratio is now >1 on r1. |
| 89 | F3c per flight | fwdc_tex_r3 ratio_decreasing | yes → no (DIRECTION) | REAL | UKF cross-track integral falls ~3× (derotation fix: Δ10 3.11 → 0.82 m·s on r1) while the FGO's rises slightly (0.36 → 1.13); the FGO/UKF ratio is now >1 on r1. |
| 90 | F3c verdict | b_advantage_grows | yes → no (DIRECTION) | REAL (verdict flip) | F3c (b) 'advantage grows' TRUE → FALSE: ratio decreasing on 1/3 bags (r2) instead of 3/3. (a) unchanged FALSE. |
| 91 | 2(a) (F4) orderings: FGO_robust − FGO_hard | f4_fwdc_tex_r2 yaw_max_deg | -0.165 → 0.002 (DIRECTION) | REAL (not interpretable as ordering) | On fwdc both arms now ~0.3° / 1–13 cm and equal to within 0.05° / 5 cm; the sign of a sub-noise difference. |
| 92 | 2(a) (F4) orderings: FGO_robust − FGO_hard | f4_fwdc_tex_r3 yaw_max_deg | -0.431 → 0.043 (DIRECTION) | REAL (not interpretable as ordering) | On fwdc both arms now ~0.3° / 1–13 cm and equal to within 0.05° / 5 cm; the sign of a sub-noise difference. |
| 93 | 2(a) (F4) orderings: FGO_robust − FGO_hard | f4_fwdc_tex_r3 xtrack_max_m | -0.002 → 0.027 (DIRECTION) | REAL (not interpretable as ordering) | On fwdc both arms now ~0.3° / 1–13 cm and equal to within 0.05° / 5 cm; the sign of a sub-noise difference. |
| 94 | 2(a) (F4) orderings: FGO_robust − FGO_hard | f4_fwdc_tex_r4 xtrack_max_m | -0.003 → 0.047 (DIRECTION) | REAL (not interpretable as ordering) | On fwdc both arms now ~0.3° / 1–13 cm and equal to within 0.05° / 5 cm; the sign of a sub-noise difference. |
| 95 | 2(a) (F4) orderings: FGO_robust − FGO_hard | f4_fwdplainc_tex_r6 xtrack_max_m | 0.163 → -9.028 (DIRECTION) | REAL | Plain-wall FGO_hard divergence (yaw max ~180°, x-track 4.1–10.7 m); FGO_robust 0.19–0.36 m. |
