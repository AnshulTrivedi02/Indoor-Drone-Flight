# FGO gate-count diagnostic: per-set numbers (thesis-facing addendum)

DIAGNOSTIC. No verdict.

Read-only extraction from `eval/results/fgo_gate_count/per_set.json` (written by `eval/fgo_gate_count_aggregate.py`, itself reading the stored per-run `~/thesis_data/diagnostics/fgo_gate_count/*_gate_summary.json` files written by `eval/fgo_gate_count.py --run ...`; see `docs/thesis/diagnostics/fgo_gate_count.md` for the method and `docs/thesis/diagnostics/fgo_gate_count_results.md` for the discussion). Nothing here is re-run or re-scored; percentages are `rd()`-rounded once from the stored counts. "Reject" means "would have been rejected by this gate, evaluated against the as-built factor and the IMU-only predictive covariance" -- see the conditioning and fusion-order caveats in the results file. A rejection would change later states; this is not a replay of a gated FGO.

**dagger (floor-level, not per-row): transition and blank are, in every one of the 60 runs checked, in `numbers.md`'s own documented "Diverging (unaided) FGO results" category (km-scale ATE once flow aiding is lost) -- only textured stays bounded.** Low rejection counts on transition/blank reflect a hugely inflated `P_pred` at least as much as flow-factor quality; see the results file Section 6a before reading those rows as "the sensor is fine on this floor". `1B all achievable` sums flow/range factors across baseline/heading/heading_yawrate for the SAME trial, which share the same underlying flow/range measurements (Section 4 of the results file: the factor count is identical per arm) -- it is a sum of three passes over the same measurements under three different trajectories/covariances, not a count of 3x as many distinct factors.

## Set 1A (`dsn_*`, no forward-camera arm, 15 runs)

| group | n runs | n flow factors | reject axis-0 (x) | reject axis-1 (y) | reject joint (naive 9) | reject joint (chi2(2)=11.83) | FLOW_MAX one-sided | FLOW_MAX two-sided |
|---|---|---|---|---|---|---|---|---|
| 1A textured (n=9) | 9 | 89490 | 2 (0.00%) | 5 (0.01%) | 5 (0.01%) | 5 (0.01%) | 0 (0.00%) | 0 (0.00%) |
| 1A blank (n=3) | 3 | 1366 | 7 (0.51%) | 8 (0.59%) | 10 (0.73%) | 10 (0.73%) | 0 (0.00%) | 0 (0.00%) |
| 1A transition (n=3) | 3 | 16058 | 37 (0.23%) | 19 (0.12%) | 53 (0.33%) | 37 (0.23%) | 0 (0.00%) | 0 (0.00%) |
| 1A all (n=15) | 15 | 106914 | 46 (0.04%) | 32 (0.03%) | 68 (0.06%) | 52 (0.05%) | 0 (0.00%) | 0 (0.00%) |

| group | n runs | n range factors | reject (NIS>25, `HGT_I_GATE`) | n flow factors GP-replaced (pre-takeoff, synthetic) | byte-identical to stored |
|---|---|---|---|---|---|
| 1A textured (n=9) | 9 | 91025 | 0 (0.00%) | 4488 | PASS |
| 1A blank (n=3) | 3 | 29995 | 22 (0.07%) | 1135 | PASS |
| 1A transition (n=3) | 3 | 30154 | 87 (0.29%) | 1326 | PASS |
| 1A all (n=15) | 15 | 151174 | 109 (0.07%) | 6949 | PASS |

**Near-threshold counts** (within ±0.1% of the stated gate; FGO_DESIGN.md / design-note Section 7b conditioning caveat -- the count of decisions late-flight round-off growth could plausibly flip):

| group | axis-0 near 9 | axis-1 near 9 | joint near 9 | joint near 11.83 | range near 25 |
|---|---|---|---|---|---|
| 1A textured (n=9) | 0 | 0 | 0 | 0 | 0 |
| 1A blank (n=3) | 0 | 0 | 0 | 0 | 0 |
| 1A transition (n=3) | 0 | 0 | 0 | 0 | 0 |
| 1A all (n=15) | 0 | 0 | 0 | 0 | 0 |

## Set 1B (Phase 4 forward-camera arms, 18 trials x up to 3 arms = 54 registered, 45 achievable)

| wall | floor | arm | n runs | n flow factors | reject axis-0 (x) | reject axis-1 (y) | reject joint (naive 9) | reject joint (chi2(2)=11.83) | FLOW_MAX one-sided | FLOW_MAX two-sided |
|---|---|---|---|---|---|---|---|---|---|---|
| line-textured walls | textured | baseline | 3 | 29865 | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) |
| line-textured walls | textured | heading | 3 | 29865 | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) |
| line-textured walls | textured | heading+yawrate | 3 | 29865 | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) |
| line-textured walls | transition | baseline | 3 | 16168 | 65 (0.40%) | 23 (0.14%) | 69 (0.43%) | 63 (0.39%) | 1 (0.01%) | 1 (0.01%) |
| line-textured walls | transition | heading | 3 | 16168 | 11 (0.07%) | 32 (0.20%) | 51 (0.32%) | 36 (0.22%) | 1 (0.01%) | 1 (0.01%) |
| line-textured walls | transition | heading+yawrate | 3 | 16168 | 63 (0.39%) | 71 (0.44%) | 103 (0.64%) | 93 (0.58%) | 1 (0.01%) | 1 (0.01%) |
| line-textured walls | blank | baseline | 3 | 1770 | 9 (0.51%) | 9 (0.51%) | 10 (0.56%) | 10 (0.56%) | 0 (0.00%) | 0 (0.00%) |
| line-textured walls | blank | heading | 3 | 1770 | 24 (1.36%) | 8 (0.45%) | 27 (1.53%) | 11 (0.62%) | 0 (0.00%) | 0 (0.00%) |
| line-textured walls | blank | heading+yawrate | 3 | 1770 | 47 (2.66%) | 8 (0.45%) | 50 (2.82%) | 36 (2.03%) | 0 (0.00%) | 0 (0.00%) |
| plain walls | textured | baseline | 3 | 29721 | 0 (0.00%) | 0 (0.00%) | 2 (0.01%) | 2 (0.01%) | 0 (0.00%) | 0 (0.00%) |
| plain walls | textured | heading | 3 | 29721 | 0 (0.00%) | 0 (0.00%) | 2 (0.01%) | 2 (0.01%) | 0 (0.00%) | 0 (0.00%) |
| plain walls | transition | baseline | 3 | 16072 | 17 (0.11%) | 17 (0.11%) | 20 (0.12%) | 20 (0.12%) | 0 (0.00%) | 0 (0.00%) |
| plain walls | transition | heading | 3 | 16072 | 16 (0.10%) | 19 (0.12%) | 26 (0.16%) | 24 (0.15%) | 0 (0.00%) | 0 (0.00%) |
| plain walls | blank | baseline | 3 | 1634 | 8 (0.49%) | 7 (0.43%) | 9 (0.55%) | 9 (0.55%) | 0 (0.00%) | 0 (0.00%) |
| plain walls | blank | heading | 3 | 1634 | 61 (3.73%) | 8 (0.49%) | 62 (3.79%) | 38 (2.33%) | 0 (0.00%) | 0 (0.00%) |
| **all 1B achievable (n=45)** | 45 | 238263 | 321 (0.13%) | 202 (0.08%) | 431 (0.18%) | 344 (0.14%) | 3 (0.00%) | 3 (0.00%) |

| wall | floor | arm | n runs | n range factors | reject (NIS>25) | n flow factors GP-replaced | byte-identical to stored |
|---|---|---|---|---|---|---|---|
| line-textured walls | textured | baseline | 3 | 30360 | 0 (0.00%) | 1586 | PASS |
| line-textured walls | textured | heading | 3 | 30360 | 0 (0.00%) | 1586 | PASS |
| line-textured walls | textured | heading+yawrate | 3 | 30360 | 0 (0.00%) | 1586 | PASS |
| line-textured walls | transition | baseline | 3 | 30233 | 108 (0.36%) | 1495 | PASS |
| line-textured walls | transition | heading | 3 | 30233 | 48 (0.16%) | 1495 | PASS |
| line-textured walls | transition | heading+yawrate | 3 | 30233 | 83 (0.27%) | 1495 | PASS |
| line-textured walls | blank | baseline | 3 | 30296 | 35 (0.12%) | 1546 | PASS |
| line-textured walls | blank | heading | 3 | 30296 | 25 (0.08%) | 1546 | PASS |
| line-textured walls | blank | heading+yawrate | 3 | 30296 | 33 (0.11%) | 1546 | PASS |
| plain walls | textured | baseline | 3 | 30216 | 0 (0.00%) | 1487 | PASS |
| plain walls | textured | heading | 3 | 30216 | 0 (0.00%) | 1487 | PASS |
| plain walls | transition | baseline | 3 | 30125 | 84 (0.28%) | 1362 | PASS |
| plain walls | transition | heading | 3 | 30125 | 19 (0.06%) | 1362 | PASS |
| plain walls | blank | baseline | 3 | 30209 | 22 (0.07%) | 1364 | PASS |
| plain walls | blank | heading | 3 | 30209 | 26 (0.09%) | 1364 | PASS |
| **all 1B achievable (n=45)** | 45 | 453767 | 483 (0.11%) | 22307 | PASS |

**Set 1B near-threshold counts** (within +/-0.1% of the stated gate; see the Section 6 conditioning caveat in the results file):

| wall | floor | arm | axis-0 near 9 | axis-1 near 9 | joint near 9 | joint near 11.83 | range near 25 |
|---|---|---|---|---|---|---|---|
| line-textured walls | textured | baseline | 0 | 0 | 0 | 0 | 0 |
| line-textured walls | textured | heading | 0 | 0 | 0 | 0 | 0 |
| line-textured walls | textured | heading+yawrate | 0 | 0 | 0 | 0 | 0 |
| line-textured walls | transition | baseline | 0 | 0 | 0 | 0 | 0 |
| line-textured walls | transition | heading | 0 | 0 | 0 | 0 | 0 |
| line-textured walls | transition | heading+yawrate | 0 | 0 | 0 | 0 | 0 |
| line-textured walls | blank | baseline | 0 | 0 | 0 | 0 | 0 |
| line-textured walls | blank | heading | 0 | 0 | 0 | 0 | 0 |
| line-textured walls | blank | heading+yawrate | 0 | 0 | 1 | 0 | 0 |
| plain walls | textured | baseline | 0 | 0 | 0 | 0 | 0 |
| plain walls | textured | heading | 0 | 0 | 0 | 0 | 0 |
| plain walls | transition | baseline | 0 | 0 | 0 | 0 | 0 |
| plain walls | transition | heading | 0 | 0 | 0 | 0 | 0 |
| plain walls | blank | baseline | 0 | 0 | 0 | 0 | 0 |
| plain walls | blank | heading | 0 | 0 | 0 | 0 | 0 |
| **all 1B achievable (n=45)** | 0 | 0 | 1 | 0 | 0 |

*Checks (EXACT, string equality after one `rd()` rounding, both against `rd()` of the JSON value directly and against an independently-recomputed decimal rounding, per the brief): {{N_OK}}/{{N_TOT}} against `eval/results/fgo_gate_count/per_set.json`.*

## Appendix: every registered run (set 1A + set 1B, 69 combinations, 60 ran / 9 N/A)

Per-RUN (not aggregated) counts, one row per registered trial x arm combination. The 9 `fwdplainc_*` x `heading_yawrate` combinations are N/A (do not exist in the production code; `docs/thesis/diagnostics/fgo_gate_count_results.md` Section 3) and carry no counts.

| trial | arm | n flow factors | reject axis-0 | reject axis-1 | reject joint-9 | reject joint-11.83 | FLOW_MAX 1-sided | FLOW_MAX 2-sided | n range factors | range reject-25 | GP-replaced | byte-identical |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dsn_blank_r1 | - | 501 | 3 (0.60%) | 4 (0.80%) | 5 (1.00%) | 5 (1.00%) | 0 (0.00%) | 0 (0.00%) | 10047 | 0 (0.00%) | 436 | PASS |
| dsn_blank_r2 | - | 427 | 2 (0.47%) | 3 (0.70%) | 3 (0.70%) | 3 (0.70%) | 0 (0.00%) | 0 (0.00%) | 9966 | 10 (0.10%) | 355 | PASS |
| dsn_blank_r3 | - | 438 | 2 (0.46%) | 1 (0.23%) | 2 (0.46%) | 2 (0.46%) | 0 (0.00%) | 0 (0.00%) | 9982 | 12 (0.12%) | 344 | PASS |
| dsn_tex_r1 | - | 10018 | 2 (0.02%) | 2 (0.02%) | 2 (0.02%) | 2 (0.02%) | 0 (0.00%) | 0 (0.00%) | 10196 | 0 (0.00%) | 584 | PASS |
| dsn_tex_r2 | - | 9952 | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 10143 | 0 (0.00%) | 533 | PASS |
| dsn_tex_r3 | - | 9903 | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 10062 | 0 (0.00%) | 457 | PASS |
| dsn_tex_r4 | - | 9853 | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 10019 | 0 (0.00%) | 424 | PASS |
| dsn_tex_r5 | - | 10084 | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 10242 | 0 (0.00%) | 607 | PASS |
| dsn_tex_r6 | - | 9900 | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 10077 | 0 (0.00%) | 489 | PASS |
| dsn_tex_r7 | - | 10051 | 0 (0.00%) | 2 (0.02%) | 2 (0.02%) | 2 (0.02%) | 0 (0.00%) | 0 (0.00%) | 10210 | 0 (0.00%) | 578 | PASS |
| dsn_tex_r8 | - | 9943 | 0 (0.00%) | 1 (0.01%) | 1 (0.01%) | 1 (0.01%) | 0 (0.00%) | 0 (0.00%) | 10125 | 0 (0.00%) | 472 | PASS |
| dsn_tex_r9 | - | 9786 | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 9951 | 0 (0.00%) | 344 | PASS |
| dsn_trans_r1 | - | 5340 | 10 (0.19%) | 3 (0.06%) | 22 (0.41%) | 9 (0.17%) | 0 (0.00%) | 0 (0.00%) | 10030 | 37 (0.37%) | 419 | PASS |
| dsn_trans_r2 | - | 5338 | 16 (0.30%) | 6 (0.11%) | 18 (0.34%) | 15 (0.28%) | 0 (0.00%) | 0 (0.00%) | 10040 | 32 (0.32%) | 435 | PASS |
| dsn_trans_r3 | - | 5380 | 11 (0.20%) | 10 (0.19%) | 13 (0.24%) | 13 (0.24%) | 0 (0.00%) | 0 (0.00%) | 10084 | 18 (0.18%) | 472 | PASS |
| fwdc_tex_r1 | baseline | 9960 | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 10117 | 0 (0.00%) | 505 | PASS |
| fwdc_tex_r1 | heading | 9960 | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 10117 | 0 (0.00%) | 505 | PASS |
| fwdc_tex_r1 | heading_yawrate | 9960 | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 10117 | 0 (0.00%) | 505 | PASS |
| fwdc_tex_r2 | baseline | 9978 | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 10160 | 0 (0.00%) | 577 | PASS |
| fwdc_tex_r2 | heading | 9978 | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 10160 | 0 (0.00%) | 577 | PASS |
| fwdc_tex_r2 | heading_yawrate | 9978 | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 10160 | 0 (0.00%) | 577 | PASS |
| fwdc_tex_r3 | baseline | 9927 | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 10083 | 0 (0.00%) | 504 | PASS |
| fwdc_tex_r3 | heading | 9927 | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 10083 | 0 (0.00%) | 504 | PASS |
| fwdc_tex_r3 | heading_yawrate | 9927 | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 10083 | 0 (0.00%) | 504 | PASS |
| fwdc_trans_r1 | baseline | 5492 | 9 (0.16%) | 0 (0.00%) | 13 (0.24%) | 9 (0.16%) | 1 (0.02%) | 1 (0.02%) | 10198 | 17 (0.17%) | 593 | PASS |
| fwdc_trans_r1 | heading | 5492 | 6 (0.11%) | 24 (0.44%) | 34 (0.62%) | 29 (0.53%) | 1 (0.02%) | 1 (0.02%) | 10198 | 20 (0.20%) | 593 | PASS |
| fwdc_trans_r1 | heading_yawrate | 5492 | 6 (0.11%) | 9 (0.16%) | 14 (0.25%) | 11 (0.20%) | 1 (0.02%) | 1 (0.02%) | 10198 | 16 (0.16%) | 593 | PASS |
| fwdc_trans_r2 | baseline | 5350 | 41 (0.77%) | 20 (0.37%) | 41 (0.77%) | 39 (0.73%) | 0 (0.00%) | 0 (0.00%) | 10032 | 61 (0.61%) | 456 | PASS |
| fwdc_trans_r2 | heading | 5350 | 2 (0.04%) | 2 (0.04%) | 3 (0.06%) | 2 (0.04%) | 0 (0.00%) | 0 (0.00%) | 10032 | 14 (0.14%) | 456 | PASS |
| fwdc_trans_r2 | heading_yawrate | 5350 | 53 (0.99%) | 29 (0.54%) | 54 (1.01%) | 54 (1.01%) | 0 (0.00%) | 0 (0.00%) | 10032 | 53 (0.53%) | 456 | PASS |
| fwdc_trans_r3 | baseline | 5326 | 15 (0.28%) | 3 (0.06%) | 15 (0.28%) | 15 (0.28%) | 0 (0.00%) | 0 (0.00%) | 10003 | 30 (0.30%) | 446 | PASS |
| fwdc_trans_r3 | heading | 5326 | 3 (0.06%) | 6 (0.11%) | 14 (0.26%) | 5 (0.09%) | 0 (0.00%) | 0 (0.00%) | 10003 | 14 (0.14%) | 446 | PASS |
| fwdc_trans_r3 | heading_yawrate | 5326 | 4 (0.08%) | 33 (0.62%) | 35 (0.66%) | 28 (0.53%) | 0 (0.00%) | 0 (0.00%) | 10003 | 14 (0.14%) | 446 | PASS |
| fwdc_blank_r1 | baseline | 708 | 6 (0.85%) | 7 (0.99%) | 7 (0.99%) | 7 (0.99%) | 0 (0.00%) | 0 (0.00%) | 10220 | 0 (0.00%) | 626 | PASS |
| fwdc_blank_r1 | heading | 708 | 2 (0.28%) | 3 (0.42%) | 3 (0.42%) | 3 (0.42%) | 0 (0.00%) | 0 (0.00%) | 10220 | 0 (0.00%) | 626 | PASS |
| fwdc_blank_r1 | heading_yawrate | 708 | 41 (5.79%) | 4 (0.56%) | 43 (6.07%) | 31 (4.38%) | 0 (0.00%) | 0 (0.00%) | 10220 | 0 (0.00%) | 626 | PASS |
| fwdc_blank_r2 | baseline | 558 | 2 (0.36%) | 1 (0.18%) | 2 (0.36%) | 2 (0.36%) | 0 (0.00%) | 0 (0.00%) | 10051 | 8 (0.08%) | 487 | PASS |
| fwdc_blank_r2 | heading | 558 | 2 (0.36%) | 2 (0.36%) | 3 (0.54%) | 3 (0.54%) | 0 (0.00%) | 0 (0.00%) | 10051 | 10 (0.10%) | 487 | PASS |
| fwdc_blank_r2 | heading_yawrate | 558 | 2 (0.36%) | 2 (0.36%) | 3 (0.54%) | 2 (0.36%) | 0 (0.00%) | 0 (0.00%) | 10051 | 13 (0.13%) | 487 | PASS |
| fwdc_blank_r3 | baseline | 504 | 1 (0.20%) | 1 (0.20%) | 1 (0.20%) | 1 (0.20%) | 0 (0.00%) | 0 (0.00%) | 10025 | 27 (0.27%) | 433 | PASS |
| fwdc_blank_r3 | heading | 504 | 20 (3.97%) | 3 (0.60%) | 21 (4.17%) | 5 (0.99%) | 0 (0.00%) | 0 (0.00%) | 10025 | 15 (0.15%) | 433 | PASS |
| fwdc_blank_r3 | heading_yawrate | 504 | 4 (0.79%) | 2 (0.40%) | 4 (0.79%) | 3 (0.60%) | 0 (0.00%) | 0 (0.00%) | 10025 | 20 (0.20%) | 433 | PASS |
| fwdplainc_tex_r1 | baseline | 9939 | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 10095 | 0 (0.00%) | 543 | PASS |
| fwdplainc_tex_r1 | heading | 9939 | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 10095 | 0 (0.00%) | 543 | PASS |
| fwdplainc_tex_r1 | heading_yawrate | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| fwdplainc_tex_r2 | baseline | 9869 | 0 (0.00%) | 0 (0.00%) | 1 (0.01%) | 1 (0.01%) | 0 (0.00%) | 0 (0.00%) | 10043 | 0 (0.00%) | 448 | PASS |
| fwdplainc_tex_r2 | heading | 9869 | 0 (0.00%) | 0 (0.00%) | 1 (0.01%) | 1 (0.01%) | 0 (0.00%) | 0 (0.00%) | 10043 | 0 (0.00%) | 448 | PASS |
| fwdplainc_tex_r2 | heading_yawrate | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| fwdplainc_tex_r3 | baseline | 9913 | 0 (0.00%) | 0 (0.00%) | 1 (0.01%) | 1 (0.01%) | 0 (0.00%) | 0 (0.00%) | 10078 | 0 (0.00%) | 496 | PASS |
| fwdplainc_tex_r3 | heading | 9913 | 0 (0.00%) | 0 (0.00%) | 1 (0.01%) | 1 (0.01%) | 0 (0.00%) | 0 (0.00%) | 10078 | 0 (0.00%) | 496 | PASS |
| fwdplainc_tex_r3 | heading_yawrate | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| fwdplainc_trans_r1 | baseline | 5379 | 3 (0.06%) | 4 (0.07%) | 5 (0.09%) | 5 (0.09%) | 0 (0.00%) | 0 (0.00%) | 10027 | 0 (0.00%) | 468 | PASS |
| fwdplainc_trans_r1 | heading | 5379 | 2 (0.04%) | 4 (0.07%) | 4 (0.07%) | 4 (0.07%) | 0 (0.00%) | 0 (0.00%) | 10027 | 0 (0.00%) | 468 | PASS |
| fwdplainc_trans_r1 | heading_yawrate | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| fwdplainc_trans_r2 | baseline | 5340 | 1 (0.02%) | 2 (0.04%) | 2 (0.04%) | 2 (0.04%) | 0 (0.00%) | 0 (0.00%) | 10055 | 0 (0.00%) | 437 | PASS |
| fwdplainc_trans_r2 | heading | 5340 | 2 (0.04%) | 3 (0.06%) | 3 (0.06%) | 3 (0.06%) | 0 (0.00%) | 0 (0.00%) | 10055 | 0 (0.00%) | 437 | PASS |
| fwdplainc_trans_r2 | heading_yawrate | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| fwdplainc_trans_r3 | baseline | 5353 | 13 (0.24%) | 11 (0.21%) | 13 (0.24%) | 13 (0.24%) | 0 (0.00%) | 0 (0.00%) | 10043 | 84 (0.84%) | 457 | PASS |
| fwdplainc_trans_r3 | heading | 5353 | 12 (0.22%) | 12 (0.22%) | 19 (0.35%) | 17 (0.32%) | 0 (0.00%) | 0 (0.00%) | 10043 | 19 (0.19%) | 457 | PASS |
| fwdplainc_trans_r3 | heading_yawrate | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| fwdplainc_blank_r1 | baseline | 584 | 3 (0.51%) | 2 (0.34%) | 3 (0.51%) | 3 (0.51%) | 0 (0.00%) | 0 (0.00%) | 10128 | 0 (0.00%) | 505 | PASS |
| fwdplainc_blank_r1 | heading | 584 | 43 (7.36%) | 4 (0.68%) | 44 (7.53%) | 28 (4.79%) | 0 (0.00%) | 0 (0.00%) | 10128 | 0 (0.00%) | 505 | PASS |
| fwdplainc_blank_r1 | heading_yawrate | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| fwdplainc_blank_r2 | baseline | 487 | 5 (1.03%) | 4 (0.82%) | 5 (1.03%) | 5 (1.03%) | 0 (0.00%) | 0 (0.00%) | 10003 | 7 (0.07%) | 391 | PASS |
| fwdplainc_blank_r2 | heading | 487 | 16 (3.29%) | 4 (0.82%) | 16 (3.29%) | 8 (1.64%) | 0 (0.00%) | 0 (0.00%) | 10003 | 10 (0.10%) | 391 | PASS |
| fwdplainc_blank_r2 | heading_yawrate | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| fwdplainc_blank_r3 | baseline | 563 | 0 (0.00%) | 1 (0.18%) | 1 (0.18%) | 1 (0.18%) | 0 (0.00%) | 0 (0.00%) | 10078 | 15 (0.15%) | 468 | PASS |
| fwdplainc_blank_r3 | heading | 563 | 2 (0.36%) | 0 (0.00%) | 2 (0.36%) | 2 (0.36%) | 0 (0.00%) | 0 (0.00%) | 10078 | 16 (0.16%) | 468 | PASS |
| fwdplainc_blank_r3 | heading_yawrate | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
