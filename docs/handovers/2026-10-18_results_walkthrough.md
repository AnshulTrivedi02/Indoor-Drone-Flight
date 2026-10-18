# Handover 2026-10-18: results walkthrough (detailed plots + worlds + metric/pass/result)

**User request (verbatim):** "keep the original plots with distance vs time and error over time etc but still keep the metric pass
rule and result descriptions for each of those plots, also combine the world screenshots into the results so I can see the results
and the world the screenshot was part of". Earlier: "make sure everything is easy to understand and simple".

## What was built

- `eval/figs_results_walkthrough.py` (new). Composition only: places existing images; no re-plotting, no recomputation, no estimator
  run, no simulation. Reads `~/thesis_data/trials/*/metadata.yaml` / `run_trial.log` read-only for the world check.
- `docs/thesis/summary/results_walkthrough.pdf`: 16 pages, A4 landscape: contents, the summary's "How to read these pages" page
  (unchanged PNG), then 14 result pages.
- `docs/thesis/summary/walkthrough/wt_*.png` (one per page, 200 dpi).
- `docs/thesis/summary/index_walkthrough.md`: per page, every source image with its sha256 and crop box, and every text line with
  its source and its check.

No other generator, numbers.md, METHODOLOGY.md or frozen file was edited. `tools/check_numbers_frozen.py`: PASS.

## Pages

| page | experiment | world image(s) | plot |
|---|---|---|---|
| 01 | 1A (1 of 3) | corridor_textured: interior, angled | R3 panel (a): aligned paths, flight 3 (Fig 4.2a) |
| 02 | 1A (2 of 3) | same | R5 panel (a): unaligned paths (Fig 4.1c a) |
| 03 | 1A (3 of 3) | same | R5 panels (b, c): along/sideways error vs distance |
| 04 | blank floor (1A and 1B) | corridor_blank, corridor_blank_fwdc, corridor_blank_fwdplainc (interiors) | summary chart 02 (table) |
| 05 | 1B heading check | onboard forward-camera frames: painted-line/checker, plain/checker, plain/blank | summary chart 03 (table) |
| 06 | 1B accuracy | corridor_textured_fwdc: interior, cutaway | R3 panel (b): with/without heading, flight 3 |
| 07 | 1C without heading | corridor_textured_half_fwdc: interior, cutaway | F2 (Fig 4.1), paths to wall contact |
| 08 | 1C with heading | same | F9 (Fig 4.1b), heading error vs time |
| 09 | 2 known tags | room_tags: angled, top | F5 (Fig 5.1) |
| 10 | 3 loop closure | room_tags: angled, top | F7 (Fig 5.2), error per lap |
| 11 | 4 outdoor–indoor | outdoor_indoor: entrance, indoor | F6 (Fig 5.3), error vs time |
| 12 | 5 hold | room_wall_tag_far: angled, wall tag | summary chart 10 |
| 13 | 5 tag loss | same | summary chart 11 |
| 14 | 5S safety | same | summary chart 12 (table) |

## Text sources

- Title, "What this tests", Metric, Pass rule, Result: verbatim from `docs/thesis/summary/index_summary.md` (64/64 equal). That file
  is written by `eval/figs_thesis_summary.py`; a scratch copy re-run at 441e97c (output folder redirected, nothing written to the
  repo) gave an identical index (commit line only) and byte-identical PNGs, and supplied the footer-rule rows used for cropping.
- **MODIFIED (6), each listed with its original in the index:** summary 01 metric ×3 pages (dropped "(the vertical lines show the
  range over the flights)", the summary chart is not shown); summary 05 pass rule ("(grey)" → "(written next to each wall contact
  on the plot)"); summary 06 metric (dropped the clause about the bars); summary 06 pass rule ("listed on the right" → the five
  check phrases inline, each asserted to be in `figs_thesis_summary.py`).
- **NEW (41):** one "About this plot" line per detailed plot (7 figure pages + 2 continuation pages), world captions, the page 05
  note on the orange cross, and the contents note. Number guard: every number in a NEW/MODIFIED line occurs in the figure's own
  index entry or that page's summary strings (PASS).

## Crops (all recorded in the index)

- R3 split into its two panels and R5 into (a) and (b+c); separator rows asserted blank.
- Detailed figures: outer white margin trimmed; internal blank-row runs > 36 px shortened to 24 px (whitespace only).
- Summary charts: cropped between the "What this tests" text and the footer rule (rule row asserted).
- Onboard frames: rows 0–30 (white strip carrying the trial id and an internal measurement label) removed.

## World check

11/11 page groups: every trial behind each page was flown in a pictured world (or `room_wall_tag`, which differs from
`room_wall_tag_far` only in the start spot; pages 12–13 say so in the caption). No mismatch between figures and the world index.
Notes: `cl_a_tex_half`, `cl_ukf_a_tex_half_v2`, `cl_fgo_a_tex_half_v3`, `H_safety_ukf_b_v3`, `H_safety_fgo_b_v4` have no
metadata.yaml; their world was read from the SDF path in `run_trial.log`/`logs/`.

## Not included / gaps

- Figure 3.1 (architecture): method, not a result. Tables A.1–A.3 and the other tables: not plots.
- No detailed time-series/path plot exists for: blank floor, 1B heading check, 5 hold, 5 tag loss, 5S; their summary chart is used.
- No onboard frame exists for plain walls over the half-and-half floor; page 05 says the half-and-half floor is not pictured.
- 1A transition floor: no thesis figure (as in the summary).

## Legibility

Detailed plots display at 0.76–1.19× their native 200 dpi size (lowest: F9 at 0.76, F2 0.81, R5 b+c 0.83). Rendered and inspected every page:
nothing cropped, no overlaps. Rebuild: `python3 eval/figs_results_walkthrough.py` (needs ~/thesis_data for the world check).
