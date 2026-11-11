# FGO gate-count diagnostic: per-set numbers (thesis-facing addendum)

DIAGNOSTIC. No verdict.

Read-only extraction from `eval/results/fgo_gate_count/per_set.json` (written by `eval/fgo_gate_count_aggregate.py`, itself reading the stored per-run `~/thesis_data/diagnostics/fgo_gate_count/*_gate_summary.json` files written by `eval/fgo_gate_count.py --run ...`; see `docs/thesis/diagnostics/fgo_gate_count.md` for the method and `docs/thesis/diagnostics/fgo_gate_count_results.md` for the discussion). Nothing here is re-run or re-scored; percentages are `rd()`-rounded once from the stored counts. "Reject" means "would have been rejected by this gate, evaluated against the as-built factor and the IMU-only predictive covariance" -- see the conditioning and fusion-order caveats in the results file. A rejection would change later states; this is not a replay of a gated FGO.

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

## Set 1B (Phase 4 forward-camera arms, 18 trials x 3 arms = 54 runs)

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
| **all 1B (n=54)** | 45 | 238263 | 321 (0.13%) | 202 (0.08%) | 431 (0.18%) | 344 (0.14%) | 3 (0.00%) | 3 (0.00%) |

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
| **all 1B (n=54)** | 45 | 453767 | 483 (0.11%) | 22307 | PASS |

*Checks (EXACT, string equality after one `rd()` rounding): 301/301 against `eval/results/fgo_gate_count/per_set.json`.*
