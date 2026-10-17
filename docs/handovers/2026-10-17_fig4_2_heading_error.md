# Handover 2026-10-17: heading-error figure (internal F9, provisional "Figure 4.1b")

**Stage:** add the closed-loop heading-error figure to `eval/figs_thesis.py`. Done; committed on the worktree branch, not merged.

## What was added
- **`eval/figs_thesis.py`, new item F9** (`docs/thesis/figures_thesis/F9_heading_error_closed_loop.{png,pdf}`).
  - It has ONE linear main panel: heading error (estimate minus truth, °) against **time since cruise start (s)**.
  - Time was chosen over distance because it matches the stored contact times (cruise +) and the scorer's cruise window. Distance would need along-track handling on the drifting no-heading paths.
  - Colour = estimator (Okabe–Ito). Dashed = without heading, drawn to the wall contact (X). Solid = with the camera heading.
  - Grey band ±2.0° = the heading-error bound.
  - There is a **linear inset (y ±1°, same time axis)** of the 9 with-heading flights only, per the user ruling relayed mid-stage. No log or second axis.
- **Data:** the same half real-time (RTF 0.5) closed-loop flights as Figure 4.1 (`HALF` in the script). Trials:
  - without heading, 1 flight each: `cl_a_tex_half`, `cl_ukf_a_tex_half_v2`, `cl_fgo_a_tex_half_v3`;
  - with heading, 3 flights each: `cl_bcpp_tex_r1–r3_half` (EKF3), `cl_ukf_b_tex_r1–r3_half_v2`, `cl_fgo_b_tex_r1–r3_half_v3`.
  - **EKF3 DOES have the 3 with-heading flights** (the brief said otherwise; the user ruling corrected it).
- **Loader:** the B3 computation of `eval/closed_loop_score.py` is COPIED, not imported (importing it would rewrite the results). The pack's `log_yaw` was not used, because it zeroes on a dataflash-clock cruise start and is off by up to 0.006° from the stored B3.
  - The yaw comes from dataflash XKF1 (core 0) / XUKO / XFGO, minus SIM yaw, wrapped to ±180°.
  - The SITL clock is mapped to sim time with the scorer's own clock map, rebuilt from bag `/imu/time_ref`.
  - The curves are cut to the stored `cruise_s` (with heading) or to the stored `contact.t_rel_cruise_s` (without heading).
  - **Packed bags** (`bag_0.db3.zst`: the four EKF3 trials) are decompressed to a temporary directory, which is then deleted. The trial directories are not touched.
  - The reproduction is exact: curve against stored B3 p95/max |Δ| = 0 on all 9 flights, and clock map |Δ| = 0 on all 12.
- **Values shown:**
  - contact times +242.1 / +165.9 / +169.9 s;
  - with heading, all 9 flights: p95 ≤ 0.38° and max ≤ 0.68° (worst cases UKF flight 1 p95 0.382 and FGO flight 3 max 0.682), quoted from **Table 4.3**;
  - the bound p95 ≤ 1.0°, max ≤ 2.0° (cited from METHODOLOGY.md:4958, read at build time).
- **Caption:** gives the mechanism, in thesis vocabulary. A heading error turns the forward motion, and a positive error (estimate clockwise of truth) turns the vehicle west, which gives the wall contacts of Figure 4.1. The sign is checked against the stored contact wall. The footnote is `ob_cl("a")` + `OCASE_KEY`: descriptive, case (iii), with n in flights.
- **Figure 4.1's caption** now also points to the new figure. No number changed.

## Numbering (user ruling: do NOT renumber now)
- `TNUM["F9"] = "Figure 4.1b (provisional)"`, and `tkey()` sorts the suffix directly after 4.1. Every existing figure and table number is unchanged.
- index.md has a paragraph "Added 2026-10-17: F9, PROVISIONAL label" for this figure.
- The vocabulary §6 table and `sim/tools/world_docs_pack.py` were NOT edited. Nothing shifted, and world_docs_pack cites no shifted number. When the final numbering is done, add F9 to vocabulary §6, and to world_docs_pack's `corridor_textured_half_fwdc` row, which lists the thesis items using that world.
- **Collision to resolve then:** R3 (`eval/figs_thesis_results.py`, `index_results.md`) also proposes "Figure 4.2" provisionally.
- **Brief slip:** the brief said the heading-error bound is in "Table 4.2". It is in **Table 4.3** (T4). T3 = Table 4.2 is the blank-floor table. The figure cites Table 4.3.

## Checks
- **Cross-check total 307/307**, up from 287/287. F9 adds 20, all of which match, including:
  - the contact times;
  - the 0.38 / 0.68 bound;
  - the per-flight B3 rows for UKF and FGO and the EKF3 range;
  - the cited rule line;
  - the flight counts;
  - the curve-vs-B3, clock-map and contact-end checks;
  - the drift side against the contact wall.
- **Numeric diff against HEAD** (index.md plus all tables `.md`/`.tex`, F9 text removed, commit hashes masked): the only numeric change is the total 287 → 307. No previously displayed number changed.
- `tools/check_numbers_frozen.py`: PASS. numbers.md, METHODOLOGY, the results files and the frozen pack were not edited.
- I viewed the figure PNG and the caption page of the combined PDF (page 3).

## Not done / for the next stage
- Final numbering pass, covering F9 and R3 together.
- Note: the UKF and FGO no-heading curves rise steeply in the last ~1 s before contact (UKF up to ~20°). That is real data inside the cut, not an artefact. It is left as plotted and not quoted.
