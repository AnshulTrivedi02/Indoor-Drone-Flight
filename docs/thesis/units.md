# Units of the thesis tables and figures

User ruling, 2026-10-23 (verbatim): "Thesis tables use SI units, converted at generation time only; numbers.md stays exactly
as is. Use one unit per quantity, the same in a table as in its matching figure. SI prefixes are fine where they read better
(e.g. drift in mm, position error in m); pick the unit that keeps values readable and use it consistently. Keep the exact
cross-check against the stored values."

This file records the unit chosen for each quantity, the reason, and where the quantity appears. The choices are applied only
when a generator renders a table or figure. `docs/thesis/numbers.md`, the frozen results pack and the stored result files are
unchanged, and so are their units.

## How a value is converted

- Every converted value is an exact decimal shift of the stored full-precision value, then rounded once at the printed
  precision: `rd_si(v, n, k)` in `eval/figs_thesis.py` and `eval/figs_thesis_summary.py`, and `mm_()` in `eval/figs_thesis.py`
  for the stored m → mm drift values. A float multiply is never used.
- Every check compares the displayed string with the source string after the same exact shift (`si_str(s, k)`), by string
  equality. The check label states the factor, for example "numbers.md km × 10^3". `eval/figs_thesis_results.py` has a `scheck()`
  for this case.
- The printed precision is never increased: 1 dp cm becomes 3 dp m, and 0 dp km becomes metres to the nearest 1000 m.
- Numbers of five or more digits are grouped with a narrow no-break space (U+202F), the SI digit-group separator, for example
  `29 000–40 000 m`. LaTeX output maps it to `\,`.

## Unit per quantity

| quantity | unit | reason |
|---|---|---|
| Position error: cruise ATE, horizontal RMSE (Experiments 2, 3 and 4), blank-floor error after flow loss, error 10 s after GNSS returns, the Experiment 4 return jump, R5 unaligned error | **m** | This quantity runs from 0.010 m (Experiment 2 hindsight) through 0.1–5 m (most results) to 41 000 m (blank-floor runaway). No single prefix keeps every value between 0.1 and 1000. mm would print the corridor results as thousands and the runaways as tens of millions, and km would print most results as 0.00x. m reads best for the main results (cruise ATE, indoor RMSE), and the smallest values still need only three decimals (0.010–0.131 m). It is also the user's own example. |
| Cross-track / sideways (lateral) offset, including the heading-driven end-of-cruise cross-track of Table 4.1 | **m** | 0.03–46 m. It is the sideways component of the position error, so it uses the same unit. The with-heading values become 0.063–0.068 m (they were 6.3–6.8 cm). |
| Distances, positions, heights, corridor and room geometry | **m** | 0.1–160 m. km is not used: the blank-floor end-of-cruise errors (29–40 km, 23–41 km) print as 29 000–40 000 m and 23 000–41 000 m, as summary page 02 already does. |
| Experiment 5 tag-hold quantities: hold error (window mean and maximum), tag-loss drift, re-lock jump, the drift bands and hold limits, and the effective − end-of-loss difference | **mm** | 1–31 mm for the results and 50–400 mm for the bands. In m they would be 0.0049–0.0090, with two leading zeros, which breaks the readability rule. Hold error and drift sit side by side in Tables 6.1, 7.1, 7.3, 7.5 and A.2, and Table 7.5 divides one by the other, so both take one unit. It is also the user's example ("drift in mm"). It reverses the 2026-10-22 SI pass for A.2 and summary pages 10 and 11, which had used m. |
| 5S safety landing drift (horizontal displacement from the failure to touchdown) | **m** | 0.21–1.45 m, compared against the registered 0.5 m prediction. This is a vehicle displacement during a failure landing, not the Experiment 5 tag-loss drift, and in mm it would read 210–1450. |
| Compute time and the period of one estimator step or sensor sample: step and solve times, predict and update times, latency percentiles, keyframe period, prediction period, synthetic-yaw interval, sensor delay | **ms** | 0.25–94 ms. In s these values would read 0.00025–0.094. Table A.3's Experiment 3 step times return from s (2026-10-22) to ms, so they match Tables 3.1 and 8.1. |
| Flight times and durations: cruise times, wall-contact times, invalid periods, loss durations, windows, timeouts, the position-lost declaration delay, re-lock delays, the Experiment 3 wall time | **s** | 0.00–9583 s. These quantities sit on the flight's time axis, while ms is used for per-step compute and sampling. The two roles are physically different, so they are kept as two quantities. A short delay (for example 0.002–0.032 s for re-lock) stays in s, because its registered band is in s (≤ 0.1 s). |
| Speeds | **m/s** | 0.004–0.5 m/s. Table 7.3's "4 mm/s inside" the lateral-speed band becomes "0.004 m/s inside", so the margin uses the same unit as the speed and the band. |
| Angles, heading error | **°** | Unchanged. |
| Angular rates, flow | **rad/s** | Unchanged. |
| Frequencies | **Hz** | Unchanged. |
| Ratios, percentages, counts | **×, %, n** | Unitless, so unchanged. |

### Exempt: quoted registered wording

Verbatim quotations of pre-registered hypotheses and bands (from METHODOLOGY.md or `docs/tag_hold_design.md`) keep the units
they were written in, because changing them would misquote the registration. These quotations are:
- in Table 7.3 (R1), "Band: ≤ 0.1 s for both (UKF: VISO_DELAY_MS 31 ms plus one step; FGO: ≤ one keyframe of 33 ms plus the
  node latency)", "drifted ≤ 30 mm over the 15 s loss (≤ 0.3 m)" and "… (3–31 mm)";
- in Table A.2 and Table 7.3, the H5.1 and H5.5 bands "≤ 0.05 m and max ≤ 0.15 m" and "≤ 0.05 / 0.10 / 0.20 m".

The surrounding prose uses the chosen unit: "inside 50 mm mean and 150 mm max", and on summary page 10 "at most 50 mm …
150 mm", which is checked as an exact × 10^3 shift of the registered 0.05 m / 0.15 m.

## Where each quantity appears (after the pass)

The line numbers are from the commit of this pass, and they move as the files change. ID = thesis number (internal id).

**Position error, cross-track, distances (m)**
- `eval/figs_thesis.py`:
  - Table 4.1 (T2): the row builder at 1109–1116, and `save_tab` at 1117. The with-heading cross-track changes cm → m, and
    the column header gains "(m)".
  - Table 4.2 (T3): the rows at 1176–1179, and `save_tab` at 1180. The end of cruise changes km → m, via `BLK` at 732.
  - Table 4.3 (T4): `save_tab` at 1058, cross-track in m.
  - Table 5.1 (T6): 1339.
  - Table 5.2 (T8): the rows at 1907–1915, and `save_tab` at 1925. The RMSE columns change cm → m.
  - Table 7.1 (T1): `CELLS` at 761–787. The Experiment 2 cells (765 ff.) and the Experiment 3 cell (783) change cm → m, and the
    blank-floor cells change km → m. Footnote [e] is `ob_h23` (544), which changes cm → m.
  - Table 7.2 (T7): the rows at 1864, and `save_tab` at 1874. The end of cruise changes km → m.
  - Table A.1 (A1): m and m/s, unchanged.
  - Figures 4.1 (F2), 5.1 (F5), 5.2 (F7) and 5.3 (F6): already in m (2026-10-22), unchanged.
- `eval/figs_thesis_results.py`:
  - Table 7.5 (R4): the Experiment 2 rows (921, 929) change cm → m, and the Experiment 4 return error (944) changes cm → m.
  - Figure R3: m.
- `eval/figs_thesis_drift.py`: Figure R5, m.
- `eval/figs_thesis_summary.py`: summary pages 01–09 are in m. Page 02's end of cruise is now checked against Table 4.2's
  grouped metres.
- `eval/figs_walkthrough_flights.py`: every `fl_*` plot is in m.
- `eval/figs_results_walkthrough.py`: the captions say metres.

**Experiment 5 hold quantities (mm)**
- `eval/figs_thesis.py`:
  - Table 6.1 (T5): `save_tab` at 1411, mm. Its caption changes "about 3 cm" → "about 30 mm". `drifts()` now converts by
    `mm_()` (127), an exact shift.
  - Table 7.1 (T1): the hold cells (768 ff.), and footnote [i] `ob_h5` (656).
  - Table A.2 (A2): page 1 is `hsum` (1490) and `rowsH` (1501). The note `H5A2NOTE` (1637) and page 3 `hcomp`/`hctxt`
    (1594, 1606) change m → mm, and so does the footnote `ob_h5` (`A2FN`, 1674).
  - Table A.3 (A3): the build ablations (`ABL`, 1709) and footnote [b] (1704) change m → mm.
- `eval/figs_thesis_results.py`, Table 7.3 (R1): the H5 rows and notes, mm, unchanged.
- `eval/figs_thesis_results.py`, Table 7.5 (R4): the Experiment 5 row (970), mm, unchanged.
- `eval/figs_thesis_summary.py`:
  - Page 10 (697–742; axis 734) changes m → mm.
  - Page 11 (744–789; axis 781) changes m → mm.
  - `drifts()` (221) now uses an exact shift.
- `eval/figs_results_walkthrough.py`: pages 24–26 place summary pages 10 and 11 and quote their text.

**Compute time and step periods (ms)**
- `eval/figs_thesis.py`, Table A.3 (A3), Experiment 3 compute cost: the cell at 1795 changes s → ms, with its checks at 1687 ff.
- `eval/figs_thesis_methods.py`, Tables 3.1–3.3 and 8.1: ms, unchanged. The predict period now converts by an exact shift (467, 594).

**Flight times and durations (s)**
- Tables 4.2, 4.3, 7.2, 7.3, A.1 and A.2 (page 2): s, unchanged.
- Figures 4.1, 4.1b, 5.1 and 5.3: s, unchanged.
- Summary pages 05 and 12: s, unchanged.

**Speeds (m/s)**
- `eval/figs_thesis_results.py`, Table 7.3: "0.004 m/s inside" (357), checked by `scheck` (109, 550) against numbers.md:480
  "4 mm/s" × 10^-3.
- Tables 4.3 and A.3: m/s, unchanged.
