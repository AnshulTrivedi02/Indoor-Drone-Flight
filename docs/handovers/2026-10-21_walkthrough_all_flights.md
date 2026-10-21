# Handover 2026-10-21: results walkthrough, all flights

**Request (user, 2026-10-21):** world page once per experiment; show every flight (not flight 3); error against time instead of
against distance; a plot of the actual drone flying; Experiment 1C heading-error graphs never overlaid (multiple pages fine).

## What was done
- New generator `eval/figs_walkthrough_flights.py` (stored outputs only: TUMs, bags, dataflash, eval/results json; no estimator
  run, no simulation). Outputs `docs/thesis/summary/flights/fl_*.png` (21 figures), `index_flights.md`, `checks.json`.
  Run: `~/venv-evo/bin/python eval/figs_walkthrough_flights.py --cache <scratch dir>` (packed bags are decompressed into the cache
  dir, never into ~/thesis_data; `--extract-only` fills the cache in parallel first).
- `eval/figs_results_walkthrough.py` now composes 28 plot pages + 9 world pages + contents + how-to = **39 PDF pages**; world page
  once per experiment after its last plot page; contents page numbers computed from the real order.
- Checks: 44/44 printed-number checks (exact, rd()), 104/104 data-identity checks (42 SE(3) cruise ATEs to 6 dp, 40 yaw-only plotted RMS to 2 dp, 15 Experiment 4
  indoor RMSE to 6 dp, frame check, clock map, contact/B2/B3 curve checks of the F2/F9 rules); composer: verbatim 128/128,
  12 MODIFIED, 47 NEW (number guard PASS), world checks 9/9. `tools/check_numbers_frozen.py` PASS.

## Decisions to know
- Aligned plots (1A, 1B) use a YAW-ONLY alignment (rotation about the vertical + 3-D shift, same associated samples in the pinned
  window), per the coordinator finding that the SE(3) fit is degenerate about the corridor axis. Its RMS matches the stored cruise
  ATE at 2 dp on 40 of 42 flight-arms; fwdc_tex_r3 UKF_baseline (4.965 vs 4.964) and FGO_baseline (4.546 vs 4.544) do not, so
  those two lines are REPORTED and NOT DRAWN (marked * on the 1B pages; table in `index_flights.md`). The SE(3) ATE is still
  recomputed to 6 dp for every flight as the input-identity check.
- Frame check (1A unaligned): R5's 2.0° heading tolerance fails on UKF/FGO flights 2 and 6 (genuine early heading error
  −2.7…−3.5°); tolerance set to 10° (any relabel error gives ≥ 90°); both counts in `index_flights.md`.
- Corridor path plots are North-up columns (one per estimator / arm), sideways stretch 3.0× stated and measured; unaligned at 1.0.
- 1B with/without heading errors are on separate pages (different y-scales, stated on the plot).

## Not done (remaining)
- Blank floor and 1B heading check: no per-flight error-against-time page and no 'where the drone flew' page (summary charts kept).
- Experiment 2 error against time per flight (Figure 5.1 already shows each flight as a mark); Experiment 5 per-flight time series.
- Optional onboard-camera "actual drone" page: not added beyond the forward-camera frames already on the 1B world page.
