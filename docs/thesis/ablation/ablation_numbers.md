# Attribution ablation: numbers (EXPLORATORY)

**EXPLORATORY: every value in this file is exploratory, not a thesis result.** No thesis claim changes on these values
without a separate ruling. `docs/thesis/numbers.md` is not touched.

**Status: STRUCTURE ONLY. No results yet.** The pre-registration is SIGNED OFF by the user 2026-10-24 with edits
(`preregistration.md`; committed before any run). The runs have not started at this commit.

**Rules for this file:**
- Every value traces to a json key, under `~/thesis_data/ablation/scores/<rung>_<arm>.json` or
  `eval/results/phase4_<ds>_arms.json` for the stored rows.
- Every value is rounded once, from the unrounded stored value.
- Units: m (position error), ms (step time), s (wall time).
- Each row has the columns: quantity | value | unit | status (EXPLORATORY / DESCRIPTIVE / DIAGNOSTIC) | source key.

## 0. Run record (EXPLORATORY)

- Sign-off of the pre-registration: date, commit — *(empty)*
- Checks before (guard verify, check_numbers_frozen, code_pre.json, scorer gate) — *(empty)*
- r0 identity gate (12/12 byte-identical required) — *(empty)*
- Jobs: completed / retried / crashed / NOT RUN, from `~/thesis_data/ablation/timing.tsv` — *(empty)*
- Checks after — *(empty)*

## 1. Stored reference rows (EXPLORATORY context; values as stored, not re-run)

- UKF and EKF3, with heading and control — *(to be filled from `phase4_<ds>_arms.json`)*
- Thesis FGO (0.25 s, cap 2) — *(to be filled; equals r0 by the identity gate)*

## 2. FGO ladder, with heading: evo -a (cruise), m (EXPLORATORY)

| bag | r0 0.25 s cap 2 | r1 1 kf cap 1 | r2 1 kf cap 2 | r3 1 kf cap 100 | r4 1 s | r5 2 s | UKF (stored) |
|---|---|---|---|---|---|---|---|
| *(no results yet)* | | | | | | | |

## 3. Gap retention R_i = (U_i − F_ρ,i) / (U_i − F_0,i) (EXPLORATORY; DESCRIPTIVE)

| bag | R(r1) | R(r2) | R(r3) | R(r4) | R(r5) |
|---|---|---|---|---|---|
| *(no results yet)* | | | | | |

## 4. Control (no heading): evo -a (cruise), m, and paired Δ vs r0 (EXPLORATORY)

| bag | r0 | r1 | r2 | r3 | r4 | r5 | band |
|---|---|---|---|---|---|---|---|
| *(no results yet)* | | | | | | | |

## 5. Robust kernel replacing the heading gate (EXPLORATORY; DESCRIPTIVE)

| bag | r0 | r6 Huber 0.25 s | r3 | r7 Huber 1 kf | r6s stored Cauchy | band |
|---|---|---|---|---|---|---|
| *(no results yet)* | | | | | | |

## 6. Compute per step, ms (EXPLORATORY; DIAGNOSTIC: workstation Python, serial, 1 thread, nice 19)

| bag, arm | r0 median / p95 | r1 | r2 | r3 | r4 | r5 | r6 | r7 |
|---|---|---|---|---|---|---|---|---|
| *(no results yet)* | | | | | | | | |

## 7. Descriptive context (EXPLORATORY): headings valid / fused, keyframe failures, wall time

*(no results yet)*

## 8. Verdicts (EXPLORATORY; scored as worded in the signed pre-registration)

| prediction | verdict | count |
|---|---|---|
| P1 (control within band, per rung) | *(not run)* | |
| P2 (R_i(r3) ≥ 0.5 on 3/3 `fwdc`) | *(not run)* | |
| P3 (kernel within band, r6 and r7) | *(not run)* | |

## 9. Plain-language reading (EXPLORATORY)

*(after the run)*

## 10. Limitations (EXPLORATORY)

*(after the run; the list in `preregistration_draft.md` §12)*
