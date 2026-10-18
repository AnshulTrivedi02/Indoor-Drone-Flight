# Handover 2026-10-18: reader summary pages (one page per experiment)

**User request (verbatim):** "can you just generate the plots with the essential information only, it is hard to parse any
meaning from the tables and plots due to lots of extra stuff, just give the comparison numbers, the experiment, and simply
state the metrics which were used to identify if the flight passed or failed". Added: "make sure everything is easy to
understand and simple, it should be easy to understand for someone looking at it for the first time".

## What was made

- `eval/figs_thesis_summary.py` (new; numpy + matplotlib only; `python3 eval/figs_thesis_summary.py`). No other generator,
  numbers.md, METHODOLOGY.md or frozen pack file was touched. `tools/check_numbers_frozen.py` passes.
- `docs/thesis/summary/`: `summary_00_how_to_read.png`, `summary_01…12_*.png`, `summary_plots.pdf` (14 pages: contents,
  how to read, then the 12 pages in experiment order) and `index_summary.md` (all provenance and every check, per page).
- The detailed thesis tables and figures are unchanged; this is a separate reader layer.

## Pages

| page | experiment | metric | result on the page |
|---|---|---|---|
| 01 | 1A, checkerboard (textured) floor | cruise ATE, median (range) of 9 flights | H1.1 NOT MET (5 of 7, CI includes 0): no ranking |
| 02 | 1A, blank floor (1A and 1B blank flights pooled, as Table 4.2) | error at +10 / +30 s (medians), end of cruise (km) | no rule registered; none kept a usable position |
| 03 | 1B, heading-measurement check | flights passing the pre-registered accuracy bar | textured walls 9/9 PASS; plain walls 6/9 (checkerboard floor 0/3) |
| 04 | 1B, offline accuracy with/without heading | cruise ATE range over 6 bags | no decision rule (C1.a): UKF 0.13–0.25, FGO 0.06–0.22 m with heading; not ranked |
| 05 | 1C without heading (RTF 0.5) | wall-contact time vs the predicted window | UKF, FGO PASS; EKF3 NOT MET (+242.1 s, window 155–215 s) |
| 06 | 1C with heading (RTF 0.5) | five closed-loop criteria; worst max cross-track | 3/3 each PASS |
| 07 | 2, known tags | live RMSE, mean of 3 flights, 4 tag counts | H2.1 PASS; H2.3 NOT MET (FAIL as worded) |
| 08 | 3, loop closure (FGO only) | live and hindsight RMSE ranges, with/without LC | H3.1–H3.4 PASS 3/3 (ordering words allowed: rule met) |
| 09 | 4, outdoor–indoor | indoor RMSE ranges, 3 live + 2 hindsight tracks | H4.1 PASS 3/3, H4.3 PASS, H4.2 NOT MET |
| 10 | 5, hold accuracy | mean hold error range, 3 flights each | inside 0.05 m for all three (recorded PASS for EKF3 and FGO); comparatives NOT MET |
| 11 | 5, tag-loss drift | worst effective drift over all losses vs the tightest band | bands and no-lockout PASS; S2/S3 directional prediction NOT MET |
| 12 | 5S, safety tests (final runs) | the four safety criteria per test | FGO both PASS; UKF forced-invalid PASS, inputs-cut FAIL as worded (5.69 s vs 5.50 s) |

## Cross-checks

96/96 numbers EXACT (stored value rounded once by `rd()`, parsed from figs_thesis.py with its SHA asserted; equal to the
typed string; the typed string found in the thesis display file; where cited, found in the numbers.md line, the blank floor
on the Errata lines 1448/1455/1462), 40/40 rule lines (every printed bound read from its METHODOLOGY line at build time),
6/6 counts. A number guard scans each page's text and stops the build if any printed number is not covered by that page's
checks (axis tick labels excluded).

## Decisions taken (for the user to confirm)

1. **Split pages.** 1A, 1B, 1C and 5 have two pages each (one message per page, per the added requirement): 1A textured /
   blank; 1B heading check / accuracy; 1C without / with heading; 5 hold / tag loss.
2. **Units kept as displayed.** Experiment 2 live errors are in m (3 dp, as Figure 5.1), Experiment 3 in m (3 dp, as Table
   7.3 and the Figure 5.2 checks), not converted to cm.
3. **Experiment 5 hold, EKF3** is the far-spawn EKF3-flying set and UKF/FGO are the comparative run means (6.4–7.1 mm, not
   the per-window 6.1–7.4 mm), exactly as Table 7.1. The tag-loss page pools EKF3 near + far spawn (24 losses), exactly as
   Table 6.1. So EKF3's flights differ between the two Experiment 5 pages; noted in the index.
4. **H5.1 for the UKF:** no recorded verdict exists for the UKF-flying set; the page says it is "also inside" the limit
   (6.4–7.1 mm against 50 mm), not "PASS".
5. **5S final runs:** the FGO runs shown are the corrected-priors node (a different build from the FGO flown in 1C and 5);
   this is stated in the index only, not on the page. UKF (a)'s bound shown is the registered 0.1 s (score file has 0.75 s).
6. **"FAIL (as worded)"** is used only on the 5S page (Table 7.2's wording) and explained on the how-to page; on the other
   pages a failed rule or prediction is written NOT MET (Table 7.3 labels H2.3 and H4.2 FAIL AS WORDED; the summary does
   not distinguish the two).

## Left out, and why

- **1A transition floor:** no current thesis table or figure displays a transition-floor value, so there is nothing to
  cross-check; not computed from the result files.
- **1B sub-studies H1.3–H1.7** (heading-fusion prediction, robust weighting, hindsight heading correction, large initial
  heading error, replication): mixed verdicts and too much jargon for a first-time reader; in Table 7.3.
- **H2.2, H2.4, H5.6, V3, X1.b, dataset-quality bands, yaw-rate validation, EKF3 real-time contact (+186.2 s PASS), the
  Experiment 4 return jump (4.10 m), heading-error p95/max and lateral speed (Table 4.3), 5S landing drifts and earlier
  runs:** not essential to the pass/fail message of each page; listed in the index.

## Not done

- Not merged; not added to the thesis combined PDF.
- No estimator runs, no simulations.
