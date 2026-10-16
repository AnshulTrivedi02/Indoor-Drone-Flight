# Handover 2026-10-16: the rulings on the pending items and captions, applied

**Stage:** one stage. It applies METHODOLOGY "RULINGS (user, 2026-10-16): the pending items (`docs/thesis/pending_items.md`)
and captions" (M:14176-14196), items 1–6 and the captions item. **No result value changed.** The edits are wording,
placement, one rounding rule at table generation, and the `numbers.md` corrections the rulings order. METHODOLOGY.md and
the result files were not edited. The frozen pack (`final_results_pack.pdf`, its index, `eval/figs_final_pack.py`) is
untouched.

## Per ruling

1. **H comparative (item 1).** `numbers.md` §17.2 is restated: the re-flown final-build sets (S2v2, S3v2) are PRIMARY,
   "identical to the original-build verdicts". The old heading and the "Not adopted" paragraph are kept verbatim in a new
   block, "Superseded by the rulings of 2026-10-16". T1 (H cells and note) and T5 (caption and note) give the final-build
   verdicts with that wording. **Appendix A2 has a new page** (p3) with the two sets side by side: the S2/S3 column is
   labelled "superseded builds". It is reduced from the stored `expH/h_comparative_2026-10-11.json`, with 5 new
   cross-checks against §17.2. PENDING is removed everywhere for this item.
2. **Scale-cause check 5a dropped (item 2).** No limitations list existed, so **`docs/thesis/limitations.md` was created**.
   It holds two ruled items: 5a, in the ruling's words, and the partial-attribution questions (M:13300, already ruled
   "listed in the thesis"). 5a is marked dropped in `numbers.md` (flags, resolved 4) and in `methodology_index.md` (two
   places). The `numbers.md` row inside "Former sections 6–9" is a verbatim superseded block, so it was left as it was.
3. **Rounding (item 3).** A new `rd()` in `eval/figs_thesis.py` rounds every printed number once, half away from zero,
   from the shortest decimal form of the file value. All 124 format sites go through it. `numbers.md` keeps full
   precision; its flag 8 is restated as ADOPTED (thesis tables only). The rule is in `methodology_definitions_draft.md`.
   - **Display changes from the rule.** These were isolated by a run with the rule only, diffed against an unchanged run:
     - T condition A, FGO batch: 1.1 → **1.0** cm, in the T1 FGO cell ("batch 1.0–2.8 cm") and the F5 caption. These were
       hand-typed strings and are now computed.
     - L no-loop-closure live, lower bound: 26.2 → **26.3** cm, in the F7 caption (now computed).
     - The other two of the four, T condition C FGO live (0.0535) and the confirmatory r5 d (−0.4885), are displayed in
       no table or caption.
     - **No other cell or check string changed** (the f-strings already single-rounded).
   - The checks still compare against the numbers.md strings, so these stay "last-digit rounding" matches (index.md).
4. **Rung-1 first leg (item 4).** A grep finds it only in `docs/rung1_flight_cards.md` (sortie step 3) and in METHODOLOGY,
   not in any thesis results file. It is removed from the thesis list in `pending_items.md`, with a note, and the
   vocabulary's chapter note is reworded. The flight card was not edited.
5. **Final safety runs (item 5).**
   - **`numbers.md` §15 safety row** is now the latest run of each test on the final build:
     - UKF (a) v3: ALL PASS, 0.00 s, 0.58 m.
     - UKF (b) v3: S-A2 FAILS AS WORDED, 5.69 s against 5.5 s; 0.69 s of relay drain; trigger 5.00 s after the last flow;
       watcher LAND +1.71 s; drift 1.07 m.
     - FGO (a) v4: ALL PASS, 0.60 s, 1.45 m, near its 1.5 m bound.
     - FGO (b) v4: ALL PASS, 0.62 s, 0.21 m.
     - Both FGO runs are marked NEW priors.
     - Sources: the four score JSONs, M:13633-13635 and M:13689-13692.
   - **History row.** The v2 (UKF) and v3 (FGO) runs moved here, values unchanged.
   - **Old rows.** Both old rows are verbatim in the new superseded block.
   - **OLD-priors statements.** The two statements in the `numbers.md` header and the §15 intro were corrected. v4 used
     the NEW priors; the originals are kept verbatim.
   - **Captions.** The T7, A2 and A3 captions, plus the A2 notes and the T5 caption, carry: "The FGO safety re-tests (v4)
     used the NEW initial priors, while the flown FGO hold (S3v2) and corridor (v3) results used the OLD priors."
   - **T7/A2.** These no longer say "numbers.md still lists v2/v3"; their checks now cite §15.
   - **New check.** The final-run drifts are checked against the restated row.
6. **UKF per-heading weight (item 6).** Claim 15 is removed from `headline_claims_before_after.md`. The counts are
   restated as CHANGED 15, 35 rows, with a note; the other claim numbers are kept. The `numbers.md` §15 row is marked
   **NOT REPORTED (ruling 2026-10-16)**, and the old row is kept verbatim. `final_restatement_draft.md` §7 is annotated.
   The comparison was in no thesis table, figure or caption, and not in the vocabulary.
7. **Captions.**
   - **"half speed".** It became "half real-time (RTF 0.5)" in the T4 title, the T1 notes, the F2 caption, the A1 rows
     and notes, the worlds PDF (status and caption), the world index (5 lines), `numbers.md` (3 live lines; originals
     verbatim), and the claims row 14.
     - "Full speed" in the A1 rows became "real time (RTF 1.0)". The world file sets `real_time_factor` 1.0; this is not
       ordered by the ruling, and it is noted here.
     - The one-line explanation was added to vocabulary term 45 and to a new "Half real-time (RTF 0.5)" section in the
       methodology draft. It also appears in the T1, T4, A1 and F2 captions, the PDF title page and the worlds PDF.
   - **The 24 code families**, removed in the same pass:
     - D-numbers, claim/ruling numbers and ⚑ (now ‡, with a TeX mapping) are gone from the captions, notes and cells.
     - So are JSON keys, result-file and script names, commit hashes and repeat indices: "r1 / r2 / r3" became
       "flights 1 / 2 / 3", O_r1 became "flight 1", T_A_r1–r3 became "flights 1–3", and dataflash SIM became "simulator
       truth".
     - S-A2b is now "a supplementary criterion".
     - MAVProxy and SIGKILL are glossed at first use.
     - The F2 annotation "after it, D21" and the F7 panel titles were fixed inside the plots.
   - **Where the sources live now.** The table `.md`/`.tex` files no longer print a "Sources:" line: the `.md` has an HTML
     comment and the `.tex` a `%` comment pointing to the index. The combined-PDF caption pages print only the check
     count, "sources … in the figure index". The title page has no script or commit. The sources stay in
     `figures_thesis/index.md`.
   - **Worlds PDF.** Claim numbers and "pack F…" codes are stripped from the "reported in" line, along with the page-footer
     commit hash, a script name and a JSON name.
8. **Regenerated:** T1–T8 (`.md`/`.tex`/`.png`); F2/F5/F6/F7; A1–A3 (A2 is now 3 pages); `thesis_figures_combined.pdf`;
   `figures_thesis/index.md`; `worlds_combined.pdf` and world index section 1 (`sim/tools/world_docs_pack.py`, no
   re-render); `pending_items.md` (rewritten: closed / still open / excluded).

## Cross-check

**123/123 match** (final run at `bf97f66`; baseline 117/117; +6 new checks, all in A2: 5 for the H comparative page and 1 for the final safety
drifts). Rounding run: 117/117. No mismatch, none forced.

## Residual grep (thesis-facing outputs)

**Scope:**
- the table `.md`/`.tex` files;
- the index caption and title lines;
- the text of `thesis_figures_combined.pdf` (its figures are embedded rasters, so this is the caption text);
- `worlds_combined.pdf`;
- the vector figure PDFs.

| family | hits | where; why they remain |
|---|---|---|
| half speed, PENDING, D-numbers, claim/ruling n, pack codes, ⚑, OI-2/P5b, log-message names, JSON keys, result files, scripts, S-A2b, record pointers (`numbers.md`, METHODOLOGY, `*.md`, § numbers) | **0** | — (the worlds PDF's "reported in" line now prints only the thesis references; the record pointers stay in the world index) |
| commit hashes | 7 | A2 image p1/p2, build column only (vocabulary §8.2 row 15: "appendix build table only") |
| trial names | 22 | A2 p2 trial column (17); worlds PDF "flown:" lines (5). The appendix and the world table are allowed by rows 16 and 20 |
| repeat indices | 2 | worlds PDF "flown:" lines only |
| world names | 78 | worlds PDF only: page titles, flown lists, captions. It IS the appendix world table (row 18: "keep file names in a world table") |
| MAVProxy / SIGKILL | 4 | T7 note and A2 note, glossed at first use (row 22) |
| k = 2.385 | 1 | A3 F1 row, a parameter kept with its meaning (row 23) |

**In the thesis docs:**
- **"half speed".** It remains only where a file names the banned phrase: vocabulary term 45, its §8.1 row 24 and
  departures row 11, and its mapping table; the methodology draft rule; `pending_items.md`; and verbatim superseded
  copies in `numbers.md`.
- **PENDING.** It remains only as a label definition, as counts or history (claims "PENDING 0"), in verbatim superseded
  blocks, and in `pending_items.md`'s own excluded list. All of these are listed in its "Excluded" table.

## Scope readings (stated for the user)

- **Rounding scope.** `rd()` applies to every number the generator prints, the F5 and F7 figure captions included, not
  literally to the tables only. This keeps the T1 cell and the F5 caption in agreement ("1.0–2.8 cm"). It is reversible
  if the user wants "tables only" read literally.
- **The frozen pack is excluded.** `final_results_pack_index.md` and `final_results_pack.pdf` still contain PENDING and
  "half-speed". They are the frozen pack (not regenerated), superseded for the thesis by `figures_thesis/`.
- **Provenance.** The generator changes were committed first (`bf97f66`); the outputs were then regenerated, so their
  stamp names a commit that contains the code that produced them, and committed after.

## Not done / for the user

- The vocabulary-named families (§8.1: `dsn`, `fwdc`, `fwdplainc`, v-labels, S-stage codes, C0, conditions A–D) were not
  renamed. They were not in this ruling.
- Still open (see `pending_items.md`):
  - item 6, the T2 Phase 5 column;
  - item 7, the T5 far-spawn rows;
  - item 9, the not-recomputed rows, including the ceiling effect size;
  - item 10, the S-A4 display;
  - the stale `numbers.md` §10 heading.
- `.tex` was not compiled (no TeX here); the self-check passed (ASCII, braces, column counts).
