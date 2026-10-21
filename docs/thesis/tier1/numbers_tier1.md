# numbers_tier1: extension experiments E2–E5 (pre-registered)

**Template: no results yet.** Every result in this file is labelled **"extension experiment, pre-registered
(2026-10-21)"**. The pre-registration is `docs/thesis/tier1/preregistration.md` and the E5 design is
`docs/thesis/tier1/e5_design.md`.

## Provenance rules (the same convention as `docs/thesis/numbers.md`)

- **Separate from numbers.md.** This file is never merged into `docs/thesis/numbers.md`, and no value here is copied
  into `numbers.md`, `METHODOLOGY.md`, the frozen pack or `eval/figs_thesis*.py`.
- **Columns.** Every row has quantity | value | unit | status | source.
  - **Status** is one of CURRENT, DIAGNOSTIC (timing on the workstation), DESCRIPTIVE (no verdict) or NOT RUN
    (missed the 2026-11-04 23:59 AEDT lock).
  - **Source** is a `json:` path *and key* under `docs/thesis/tier1/scores/`, or a `tier1:` run directory under
    `~/thesis_data/tier1/` plus a file and key.
- **Exact cross-check.** Every value is re-computed from its cited source by a check script before it is typed here.
  The script and its output are recorded in the handover that adds the value. A value that does not match its source
  to the printed precision is not entered.
- **Precision.** Positions are printed to 4 dp in m; ratios to 2 dp. Comparisons use the unrounded json values.
- **Verdicts.** PASS, FAIL or NOT MET, exactly as `preregistration.md` §0.5 defines them, judged on the pre-registered
  counts. No re-tuning.
- **Deviations.** Any departure from the pre-registration is recorded in §Deviations *before* the affected result is
  read.

## Guard

| check | when | result | source |
|---|---|---|---|
| snapshot | before the first run | — | `frozen_manifest_<ts>.json` |
| verify after E2 / E3 / E4 / E5 / final | after each experiment | — | `frozen_verify_<ts>.json` |
| E5 code snapshot / verify | before V-E5a / after the last E5 run | — | `e5_code_manifest_<ts>.json` |

## Gates

| gate | result | source |
|---|---|---|
| G0-L (i) default redirected, (ii) neutral new flags: byte-identical to the frozen `T_A_r1/lc_fgo_lc_t245` | — | — |
| G0-UKF: 12/12 byte-identical to the stored `room_ukf` | — | — |
| G-E4: 0.25 s `fgo_live.tum` byte-identical to the stored `room_fgo`, 12/12 | — | — |
| V-E5a / V-E5b / V-E5c | — | — |

## E2: loop closure with fewer tags (B, C, D)

| quantity | value | unit | status | source |
|---|---|---|---|---|

Verdicts: H-E2.1 (PRIMARY) per condition, H-E2.2, H-E2.3, P-E2.4, P-E2.5. Known-map comparison (DESCRIPTIVE).

## E3: wrong re-identification (T_A, 1% / 5%, seeds 0–2)

### Arm (a): FGO as-is (PRIMARY)

| quantity | value | unit | status | source |
|---|---|---|---|---|

Verdicts: H-E3.1 (PRIMARY), H-E3.2, H-E3.3, P-E3.4, P-E3.5, P-E3.6.

### Arm (b): robust tag factors, Cauchy k = 2.385 (ESTIMATOR VARIANT)

| quantity | value | unit | status | source |
|---|---|---|---|---|

Verdicts: P-E3b.1, P-E3b.2.

## E4: live window sweep (12 T bags; W = 0.25 / 0.5 / 1 / 2 / 5 s)

| quantity | value | unit | status | source |
|---|---|---|---|---|

Verdicts: P-E4.1, P-E4.2. Accuracy against W and the gap to the batch: DESCRIPTIVE. LM-cap convergence flags.

## E5: UKF with tag landmark states (T_A, LC / no-LC)

| quantity | value | unit | status | source |
|---|---|---|---|---|

Verdicts: H-E5.1 (PRIMARY), H-E5.2, H-E5.3, P-E5.4, P-E5.5, P-E5.6.

## Not run by the lock (future work)

| run | experiment | reason |
|---|---|---|

## Deviations

| date | deviation | affected | recorded before reading results? |
|---|---|---|---|
