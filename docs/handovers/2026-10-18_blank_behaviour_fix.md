# Handover 2026-10-18: `eval/blank_behaviour.py` axis fix (user rulings 2026-10-18, item 7)

Stage: analysis + script fix only. No estimator was run, no simulation, nothing touching numbers.md, METHODOLOGY.md,
the frozen pack files or `eval/figs_thesis*.py`.

## 1. What was done

- **Fix** (`eval/blank_behaviour.py`, l.99-103): the UKF/FGO trajectory is relabelled into ENU before `err_growth()`,
  `x, y = -y, x`, i.e. (E, N) = (−y, x) as `eval/phase5_analysis.py:12-14`, with a comment citing METHODOLOGY "FINDING
  (2026-10-17): axis mislabel in eval/blank_behaviour.py" and this ruling. The EKF3 path (NED vs NED) is untouched; the
  flow-loss point, cruise window and every other piece of logic are unchanged.
- **Audit copy:** `eval/results/blank_behaviour_pre_axisfix.json` = the json as it stood at `0726900` (byte copy).
- **Regeneration:** `eval/results/blank_behaviour.json`, with the same arguments as `eval/final_rerun_pipeline.sh:372-376`
  (stage `d15_bb`), i.e. the two `blank_behaviour.py` invocations (`--arms ukf,fgo` for `dsn_blank_r1-3 dsn_trans_r1-3
  p1c_fwdc_blank p1c_fwdc_trans p1c_fwdplainc_blank p1c_fwdplainc_trans`; `--arms ukf_baseline,fgo_baseline,ukf_heading,fgo_heading`
  for `fwdc/fwdplainc_{blank,trans}_r1-3`), then `eval/final_rerun_merge_bb.py OLD PLAIN ARMS OUT` with OLD = the pre-fix copy.
  - The bags are stored packed (`bag_0.db3.zst`), so each trial was staged into a scratch base (copies, not symlinks; bag
    decompressed and its sha256 checked against `PACKED.txt`) and run with `--base <scratch>`, one trial at a time.
    `~/thesis_data` was only read. Scripts: session scratchpad `bbfix/run_one.sh`, `run_all.sh`, `concat.py`, `compare.py`.
  - The six compass-active `ds_*` trials have no UKF/FGO arms and are kept from the snapshot by the merge script, as in
    the pipeline.

## 2. Checks

- **EKF3 / windows / flow-loss identity:** `final_rerun_merge_bb.py` passed ("all non-UKF/FGO fields identical": every
  `EKF3_*` field, `window_s`, `t_loss_s`, `takeoff_s`, `case`, valid-frame counts, recomputed from the bags and logs).
  Full leaf diff old vs new: 2,212 leaves; 748 changed, **all** under `ukf*`/`fgo*`; 0 changed elsewhere; the 1,352
  EKF3/window/t_loss leaves are bit-identical.
- **Agreement with the trace:** the regenerated UKF/FGO values equal the trace's corrected values (`forkC/bb.pkl`,
  68 arms, 748 values incl. `disp_ratio_after_loss`): **max |diff| = 0**.

## 3. Verdict check (step 2): NO VERDICT CHANGES

Every use of a `blank_behaviour.json` value that carries a verdict, outcome, ordering, pass/fail or footnote case,
re-scored with the corrected values against its own rule:

| where | rule / wording | old values | new values | verdict old → new |
|---|---|---|---|---|
| claims table row 10 (`headline_claims_before_after.md:26`) | "without flow no estimator bounds position; the heading does not either" | end 29–40 / 22–41 km; heading +60 s 40–89 / 135–190 m | 29–40 / 23–41 km; 21–71 / 130–172 m | HOLDS → HOLDS |
| claims row 5 (`:21`), plain-wall blank sub-clause | "a yaw benefit only … position still runs away" | +60 s 51–78 / 137–166 m | 21–57 / 130–157 m | holds → holds (value text changes) |
| numbers.md:252 parenthetical | "the heading still does not bound position without flow" | 40–89 / 135–190 m | 21–71 / 130–172 m | holds → holds |
| numbers.md:302 | "Position is NOT bounded (no flow)" | UKF 73/51/78, FGO 158/137/166 m | UKF 54/21/57, FGO 151/130/157 m | holds → holds |
| T1 scorecard, blank row (`figs_thesis.py:718,726`; footnote [d] `ob_blank`, l.483-494) | status FAILED (does not bound position); footnote case (iii), "no ordering is formed" (ruling "Not accuracy comparisons", M:5551) | 29–40 / 22–41 km at end | 29–40 / 23–41 km | FAILED / case (iii) → unchanged |
| T3 (`figs_thesis.py:1093-1120`) caption + footnote [a] (`ob_blank`) | "nothing bounds position … km-scale errors by the end of the cruise"; case (iii) | as numbers.md:248-250 | as corrected | unchanged |
| T7 (`figs_thesis.py:1760-1764`) | "position runs away" (no criterion) | +60 s 60–108 / 154–204 m | 30–100 / 145–201 m | unchanged |
| R4 blank row (`figs_thesis_results.py:781-800`) | descriptive ("numbers reported without a conclusion beyond them"); "(the heading holds yaw, not position)" | FGO÷UKF +30 s 1.01–1.03; with÷without UKF 0.93–1.03, FGO 0.92–1.09 | 1.03–1.08; 0.88–1.03, 0.88–1.15 | no rule; wording still true (heading changes +30 s error by ≤12 %, vs ~30× on textured) → unchanged |
| METHODOLOGY:13389 (restatement rulings applied, blank floor "reported separately") | "Position is still unbounded" | 51–78 / 137–166 m | 21–57 / 130–157 m | unchanged (value text changes) |
| implicit ordering (not claimed anywhere) | FGO > UKF at +60 s per flight | blank 11/11, transition 11/11 | 11/11, 11/11 | unchanged |
| T3 / F06 "†" policy | +60 s and end are runaway magnitudes; no ratio formed | — | — | unchanged |

Not verdict-bearing, checked: `disp_ratio_after_loss` is quoted only in `docs/thesis/d27_old_vs_new.md` (a historical
D27 diff, superseded); the P4 bands and claim 34 use `rerun_dsn_evo.json`/phase-4 evo files, not this json;
numbers.md:253 (dsn transition displacement ratio) is from `rerun_dsn_evo.json` (unaffected). EKF3 rows (numbers.md:245,
T3/T7 EKF3 cells, "301–310 s", "0 valid frames") are unaffected (bit-identical).

**Additional items the trace missed (flag for the integrator):** numbers.md:302 (plain-wall blank heading/baseline +60 s
per flight), claims row 5 (`51–78 / 137–166 m`), METHODOLOGY.md:13389 (same values), and
`docs/handovers/2026-10-10_final2_rulings_applied.md` (same values; a handover, not to be edited). All are from
`fwdplainc_blank_r1-3` `ukf_heading`/`fgo_heading`/`*_baseline` "+60s" in this json. None changes a verdict.

## 4. DRAFT numbers.md errata (NOT applied; numbers.md is owned by another process)

Values: `eval/results/blank_behaviour.json` after this fix; magnitude = hypot(along_m, cross_m); ranges over the sets the
rows define (blank n = 11: `dsn_blank_r1-3` `ukf`/`fgo`, `p1c_fwdc_blank`, `p1c_fwdplainc_blank`, `fwdc_blank_r1-3` and
`fwdplainc_blank_r1-3` `*_baseline`; transition likewise; heading arms n = 6: `fwdc/fwdplainc_blank_r1-3` `*_heading`).
Full precision: UKF blank +10 0.71–1.81, +30 15.31–26.84, +60 29.94–100.00 m, end 29.16–40.03 km; FGO blank +10
0.69–1.76, +30 16.58–27.72, +60 144.99–200.83 m, end 22.55–40.85 km; transition +60 UKF 128.04–141.67, FGO 225.44–232.17 m;
heading +60 UKF 20.72–71.20, FGO 129.99–171.77 m.

```
### E4 (2026-10-18): §6.2, line 248 (as frozen)
- Frozen text (verbatim): | UKF baseline position error magnitude at +10 / +30 / +60 s after loss, blank (n = 11: `dsn`, `fwdc`, `fwdplainc`, `p1c`) | 6.4–8.2 / 27.3–36.5 / 60–108 | m | CURRENT (final re-run 2026-10-10) | json:blank_behaviour.json |
- Corrected text: | UKF baseline position error magnitude at +10 / +30 / +60 s after loss, blank (n = 11: `dsn`, `fwdc`, `fwdplainc`, `p1c`) | 0.7–1.8 / 15.3–26.8 / 30–100 | m | CURRENT (final re-run 2026-10-10; axis relabel 2026-10-18) | json:blank_behaviour.json |
- Reason: `eval/blank_behaviour.py` differenced the UKF trajectory (take-off-heading frame, x = North, y = West) against ground truth in ENU with no relabel (METHODOLOGY "FINDING (2026-10-17): axis mislabel in eval/blank_behaviour.py"). Fixed with (E, N) = (−y, x); recomputed from the stored trajectory files with the stored flow-loss time and window; no estimator re-run. The early error is about 1 m, not 6–8 m. No verdict changes.
- Source: eval/results/blank_behaviour.json: {dsn_blank_r1-3, p1c_fwdc_blank, p1c_fwdplainc_blank}.ukf and {fwdc,fwdplainc}_blank_r1-3.ukf_baseline, "+10s"/"+30s"/"+60s" hypot(along_m, cross_m); pre-fix values in eval/results/blank_behaviour_pre_axisfix.json.
- Ruling: user rulings 2026-10-18, item 7.

### E5 (2026-10-18): §6.2, line 249 (as frozen)
- Frozen text (verbatim): | FGO baseline, same | 6.4–8.2 / 28.0–37.0 / 154–204 | m | CURRENT (FGO-only re-run 2026-10-10) | same |
- Corrected text: | FGO baseline, same | 0.7–1.8 / 16.6–27.7 / 145–201 | m | CURRENT (FGO-only re-run 2026-10-10; axis relabel 2026-10-18) | same |
- Reason: as E4 (FGO trajectory, same mislabel). No verdict changes.
- Source: eval/results/blank_behaviour.json: same trials, fgo / fgo_baseline, "+10s"/"+30s"/"+60s".
- Ruling: user rulings 2026-10-18, item 7.

### E6 (2026-10-18): §6.2, line 250 (as frozen)
- Frozen text (verbatim): | UKF / FGO baseline error at the end of cruise, blank †| 29–40 / 22–41 | km | CURRENT (FGO-only re-run 2026-10-10) | same |
- Corrected text: | UKF / FGO baseline error at the end of cruise, blank †| 29–40 / 23–41 | km | CURRENT (FGO-only re-run 2026-10-10; axis relabel 2026-10-18) | same |
- Reason: as E4. Only the FGO lower bound moves (22.49 → 22.55 km); the km-scale runaway stands.
- Source: eval/results/blank_behaviour.json: blank set as E4/E5, "end" hypot(along_m, cross_m).
- Ruling: user rulings 2026-10-18, item 7.

### E7 (2026-10-18): §6.2, line 251 (as frozen)
- Frozen text (verbatim): | UKF / FGO baseline error at +60 s after loss, transition (n = 11) †| 128–139 / 223–231 | m | CURRENT (final re-run 2026-10-10) | json:blank_behaviour.json |
- Corrected text: | UKF / FGO baseline error at +60 s after loss, transition (n = 11) †| 128–142 / 225–232 | m | CURRENT (final re-run 2026-10-10; axis relabel 2026-10-18) | json:blank_behaviour.json |
- Reason: as E4. No verdict changes.
- Source: eval/results/blank_behaviour.json: {dsn_trans_r1-3, p1c_fwdc_trans, p1c_fwdplainc_trans}.ukf/fgo and {fwdc,fwdplainc}_trans_r1-3.*_baseline, "+60s".
- Ruling: user rulings 2026-10-18, item 7.

### E8 (2026-10-18): §6.2, line 252 (as frozen)
- Frozen text (verbatim): | Heading arms (n = 6, `fwdc`/`fwdplainc`), blank, +60 s: UKF / FGO †| 40–89 / 135–190 | m | CURRENT (FGO-only re-run 2026-10-10) (the heading still does not bound position without flow) | json:blank_behaviour.json |
- Corrected text: | Heading arms (n = 6, `fwdc`/`fwdplainc`), blank, +60 s: UKF / FGO †| 21–71 / 130–172 | m | CURRENT (FGO-only re-run 2026-10-10; axis relabel 2026-10-18) (the heading still does not bound position without flow) | json:blank_behaviour.json |
- Reason: as E4. The parenthetical still holds.
- Source: eval/results/blank_behaviour.json: {fwdc,fwdplainc}_blank_r1-3.ukf_heading/fgo_heading, "+60s".
- Ruling: user rulings 2026-10-18, item 7.

### E9 (2026-10-18): §6.6, line 302 (as frozen)
- Frozen text (verbatim): error at +60 s after flow loss UKF 73 / 51 / 78 m, FGO 158 / 137 / 166 m (baselines 73 / 60 / 80 and 161 / 154 / 170 m)
- Corrected text: error at +60 s after flow loss UKF 54 / 21 / 57 m, FGO 151 / 130 / 157 m (baselines 55 / 31 / 59 and 155 / 145 / 161 m). The rest of the row is unchanged.
- Reason: as E4 (row not in the 2026-10-17 trace's list; found in this stage). "Position is NOT bounded" still holds; yaw values and evo -a (cruise) are from other files and unaffected.
- Source: eval/results/blank_behaviour.json: fwdplainc_blank_r1/r2/r3.ukf_heading, fgo_heading, ukf_baseline, fgo_baseline, "+60s".
- Ruling: user rulings 2026-10-18, item 7.

### E10 (2026-10-18): Superseded by the ruling of 2026-10-16 (numbers.md rounding), line 1259 (as frozen)
- Frozen text (verbatim): Stored values: 128.4931 (`blank_behaviour.json` fwdc_trans_r2 ukf_baseline +60 s, hypot);
- Corrected text: Stored values: 141.6695 after the axis relabel of 2026-10-18 (128.4931 before it) (`blank_behaviour.json` fwdc_trans_r2 ukf_baseline +60 s, hypot); — this value is no longer the minimum of the transition UKF range (now 128.04, `fwdplainc_trans_r2`), so the double-rounding note no longer bears on the current row (E7).
- Reason: as E4.
- Source: eval/results/blank_behaviour.json: fwdc_trans_r2.ukf_baseline."+60s"; pre-fix: blank_behaviour_pre_axisfix.json.
- Ruling: user rulings 2026-10-18, item 7.

### E11 (2026-10-18): Superseded by the ruling of 2026-10-16 (numbers.md rounding), line 1268 (as frozen)
- Frozen text (verbatim): | §6.2 | ¦ UKF / FGO baseline error at +60 s after loss, transition (n = 11) †¦ 129–139 / 223–231 ¦ m ¦ CURRENT (final re-run 2026-10-10) ¦ json:blank_behaviour.json ¦ |
- Corrected text: values 128–142 / 225–232 (same trajectories as the current row; see E7). Method affected; superseded status unchanged.
- Reason: as E4.
- Source: as E7.
- Ruling: user rulings 2026-10-18, item 7.

### E12 (2026-10-18): Superseded by the FGO-only re-run, line 1151 (as frozen)
- Frozen text (verbatim): | §6.2 | ¦ FGO baseline, same ¦ 6.4–8.2 / 28.0–37.0 / 155–204 ¦ m ¦ CURRENT (final re-run 2026-10-10) ¦ same ¦ |
- Corrected text: method affected, not recomputable (the FGO trajectories of the first final re-run were overwritten by the FGO-only re-run). Superseded status unchanged.
- Reason: computed with the eval/blank_behaviour.py axis mislabel (METHODOLOGY "FINDING (2026-10-17)").
- Source: eval/results/blank_behaviour.json history (commit 425e824).
- Ruling: user rulings 2026-10-18, item 7 (b).

### E13 (2026-10-18): Superseded by the FGO-only re-run, line 1152 (as frozen)
- Frozen text (verbatim): | §6.2 | ¦ UKF / FGO baseline error at the end of cruise, blank †¦ 29–40 / 19–41 ¦ km ¦ CURRENT (final re-run 2026-10-10) ¦ same ¦ |
- Corrected text: UKF 29–40 km (the UKF trajectories are unchanged since; recomputed, as E6); FGO: method affected, not recomputable (trajectories overwritten). Superseded status unchanged.
- Reason: as E12; the UKF part is recomputable.
- Source: eval/results/blank_behaviour.json (UKF, "end"); commit 425e824 (FGO).
- Ruling: user rulings 2026-10-18, item 7 (b).

### E14 (2026-10-18): Superseded by the FGO-only re-run, line 1153 (as frozen)
- Frozen text (verbatim): | §6.2 | ¦ Heading arms (n = 6, `fwdc`/`fwdplainc`), blank, +60 s: UKF / FGO †¦ 40–89 / 132–193 ¦ m ¦ CURRENT (final re-run 2026-10-10) (the heading still does not bound position without flow) ¦ json:blank_behaviour.json ¦ |
- Corrected text: UKF 21–71 m (recomputed, as E8); FGO: method affected, not recomputable (trajectories overwritten). Superseded status unchanged.
- Reason: as E13.
- Source: eval/results/blank_behaviour.json (ukf_heading "+60s"); commit 425e824 (FGO).
- Ruling: user rulings 2026-10-18, item 7 (b).
```

E15–E24 follow the same pattern, one per row, each with Corrected text "method affected, not recomputable (the
trajectories of that run were overwritten by later re-runs). Superseded status unchanged.", Reason as E12, Ruling
"user rulings 2026-10-18, item 7 (b)":

| entry | section (as frozen) | line | frozen text (verbatim) | source (results file of that era) |
|---|---|---|---|---|
| E15 | Superseded by D27 | 1027 | `\|  UKF baseline position error magnitude at +10 / +30 / +60 s after loss, blank (n = 11: `dsn`, `fwdc`, `fwdplainc`, `p1c`) ¦ 6.4–9.2 / 20.5–34.1 / 96–313 ¦ m ¦ CURRENT ¦ json:blank_behaviour.json  \|` | blank_behaviour.json at 2004dda |
| E16 | Superseded by D27 | 1028 | `\|  UKF / FGO baseline error at the end of cruise, blank ¦ 10–63 / 22–31 ¦ km ¦ CURRENT (D15) ¦ same  \|` | same |
| E17 | Superseded by D27 | 1029 | `\|  UKF / FGO baseline error at +60 s after loss, transition (n = 11) ¦ 83–315 / 939–1,049 ¦ m ¦ CURRENT (D15) ¦ json:blank_behaviour.json  \|` | same |
| E18 | Superseded by D27 | 1030 | `\|  Heading arms (n = 6, `fwdc`/`fwdplainc`), blank, +60 s: UKF / FGO ¦ 61–176 / 299–904 ¦ m ¦ CURRENT (D15; the heading does not bound position without flow) ¦ json:blank_behaviour.json  \|` | same |
| E19 | Superseded by D15 | 1048 | `\| Blank behaviour: UKF / FGO transition +60 s; end-of-cruise blank; FGO blank +60 s; FGO heading blank +60 s \| 67–378 / 895–1,080; 9–63 / 23–32 km; 171–574; 299–898 \| m \| SUPERSEDED \| results_pre_d15/blank_behaviour.json \| D15 \|` | eval/results_pre_d15/blank_behaviour.json |
| E20 | Superseded by the final consolidated re-run | 1077 | `\| §6.2 \| ¦ UKF baseline position error magnitude at +10 / +30 / +60 s after loss, blank (n = 11: `dsn`, `fwdc`, `fwdplainc`, `p1c`) ¦ 6.4–9.0 / 20.5–33.0 / 112–288 ¦ m ¦ CURRENT (D27) ¦ json:blank_behaviour.json ¦ \|` | blank_behaviour.json at 232be91 |
| E21 | same | 1078 | `\| §6.2 \| ¦ FGO baseline, same ¦ 4.2–18.3 / 27–142 / 172–574 ¦ m ¦ CURRENT (D15) ¦ same ¦ \|` | same |
| E22 | same | 1079 | `\| §6.2 \| ¦ UKF / FGO baseline error at the end of cruise, blank †¦ 13–58 / 22–31 ¦ km ¦ CURRENT (D15 + D27) ¦ same ¦ \|` | same |
| E23 | same | 1080 | `\| §6.2 \| ¦ UKF / FGO baseline error at +60 s after loss, transition (n = 11) †¦ 31–307 / 939–1,049 ¦ m ¦ CURRENT (D15 + D27) ¦ json:blank_behaviour.json ¦ \|` | same |
| E24 | same | 1081 | `\| §6.2 \| ¦ Heading arms (n = 6, `fwdc`/`fwdplainc`), blank, +60 s: UKF / FGO †¦ 88–323 / 299–904 ¦ m ¦ CURRENT (D15 + D27; the heading does not bound position without flow) ¦ json:blank_behaviour.json ¦ \|` | same |

(When pasting E15–E24, write the frozen text without the escaping backslashes; it is the numbers.md line verbatim.)

**Draft count: 21 entries (E4–E24):** 8 with recomputed values (248, 249, 250, 251, 252, 302, 1259, 1268), 3 partial
(1151 none recomputable; 1152, 1153 UKF recomputed, FGO not), 10 not recomputable (1027-1030, 1048, 1077-1081).

### Other wording changes (outside numbers.md; for the owners of those files)
- **Claim 10** (`headline_claims_before_after.md:26`), evidence cell: "UKF/FGO end-of-cruise 29–40 / 22–41 km, heading
  arms +60 s 40–89 / 135–190 m (†)" → "UKF/FGO end-of-cruise 29–40 / 23–41 km, heading arms +60 s 21–71 / 130–172 m (†)".
  Status HOLDS unchanged.
- **Claim 5** (`:21`), plain-wall blank clause: "+60 s 51–78 / 137–166 m, †" → "+60 s 21–57 / 130–157 m, †". Status unchanged.
- **Restatement draft** (`final_restatement_draft.md`): l.137 "UKF transition +60 s 31–307 → 129–139 m; FGO 939–1,049 →
  223–231 m" (new side → 128–142 / 225–232; old side not recomputable); l.167-171 "new" column (first final re-run): UKF
  6.4–8.2/27.3–36.5/60–108 → 0.7–1.8/15.3–26.8/30–100; FGO 6.4–8.2/28.0–37.0/155–204 not recomputable; end 29–40/19–41 km →
  UKF 29–40, FGO not recomputable; transition 129–139/223–231 → 128–142/225–232; heading 40–89/132–193 → UKF 21–71, FGO not
  recomputable. The "old" column (D27/D15) is not recomputable throughout. The plain-explanation "slower late growth" is a
  comparison of mislabelled values on both sides; mark it "method affected".
- **Early-error wording:** wherever the early error is described (the "~6–8 m at +10 s" of METHODOLOGY:14361; T3 +10 s
  column; F06 caption; index.md/index_results.md check rows), the early error is about 1 m (0.7–1.8 m, median 1.1 m, UKF
  and FGO) at +10 s. The 6–8 m was ≈ 5 m of travel rotated by 90°.
- **T3 medians** (rendered from the json): UKF 1.1 / 19.4 / 56, FGO 1.1 / 20.4 / 166 (were 6.6 / 29.9 / 78 and 6.7 / 30.4 / 170).
- **R4 blank row** (rendered): UKF +30 s 15.3–26.8, FGO 16.6–27.7; FGO ÷ UKF 1.03–1.08; with ÷ without UKF 0.88–1.03,
  FGO 0.88–1.15.
- METHODOLOGY.md:13389 ("UKF 51–78 m, FGO 137–166 m") → 21–57 / 130–157 m (METHODOLOGY owner).
- The frozen final pack F06 (`figs_final_pack.py:391,393,405,407`; `final_results_pack_index.md:92-93,274`) carries the old
  values; per METHODOLOGY 14362 it stays frozen and the errata govern.

## 5. Generator cross-checks that compare blank_behaviour values against numbers.md (do not edit here)

With the new json, these `check()` calls will now FAIL against the frozen expected strings; point them at the
errata-corrected text:

| file:line | check | expected now (frozen) | corrected expected |
|---|---|---|---|
| eval/figs_thesis.py:680 | blank end-of-cruise UKF / FGO (km) † | 29–40 / 22–41 | 29–40 / 23–41 (E6) |
| eval/figs_thesis.py:1094 | UKF +10/+30/+60 s ranges (m) | 6.4–8.2 / 27.3–36.5 / 60–108 | 0.7–1.8 / 15.3–26.8 / 30–100 (E4) |
| eval/figs_thesis.py:1095 | FGO +10/+30/+60 s ranges (m) | 6.4–8.2 / 28.0–37.0 / 154–204 | 0.7–1.8 / 16.6–27.7 / 145–201 (E5) |
| eval/figs_thesis.py:1097 | end of cruise UKF / FGO (km) † | 29–40 / 22–41 | 29–40 / 23–41 (E6) |
| eval/figs_thesis.py:1118 | T3 note, hard-coded text (not a check) "+60 s: UKF 40–89 m, FGO 135–190 m †" | — | 21–71 / 130–172 (E8) |
| eval/figs_thesis_results.py:789 | R4 blank UKF +10 / +30 s (m), numbers.md 248 | 6.4–8.2 / 27.3–36.5 | 0.7–1.8 / 15.3–26.8 (E4) |
| eval/figs_thesis_results.py:790 | R4 blank FGO +10 / +30 s (m), numbers.md 249 | 6.4–8.2 / 28.0–37.0 | 0.7–1.8 / 16.6–27.7 (E5) |
| eval/figs_final_pack.py:391, 393 | F06 (frozen pack) | as numbers.md 248/249 | E4/E5 (only if the pack is ever regenerated) |

Unaffected checks (still pass): `figs_thesis.py:485, 486, 681, 1096, 1098, 1100, 1733` (n flights, EKF3 invalid period,
valid frames), `figs_thesis_results.py:788` (n = 11).

## 6. Needing a ruling / notes
- No verdict changes, so per item 7 the (a)+(b) path applies; the errata above are drafts for the numbers.md owner.
- numbers.md:302, claim 5 and METHODOLOGY:13389 were outside the trace's 40-item list (found here): E9 drafted for 302;
  claim 5 and M:13389 listed as wording changes. Same mechanism, no verdict effect.
- Regenerating T1/T3/T7/R4 and the index check tables is for the generator owner (after the cross-check expectations above
  are updated); until then `figs_thesis*.py` will report mismatches on the lines in §5.
