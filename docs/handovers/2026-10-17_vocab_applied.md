# Handover 2026-10-17: thesis vocabulary applied to the thesis figures, tables and world pack

*One stage. Text-only regeneration with the names and numbering of `docs/thesis/thesis_vocabulary.md`. **No number changed.**
Not edited: `numbers.md` (CONTENT-FROZEN; `tools/check_numbers_frozen.py` PASS), METHODOLOGY, results, the frozen pack,
`thesis_vocabulary.md`.*

## What was done

**Generators edited (display strings only; data keys, JSON lookups and checks untouched):**
- `eval/figs_thesis.py`
  - `TNUM` holds the §6 numbering, by chapter. The items are ordered in thesis order: chapter, then figures before tables, then number, with the appendix last.
  - Captions, titles, headers, cells, notes, legends, check labels, the cover and the index use the vocabulary.
  - The index gains a generated **appendix mapping** in three parts:
    - figures and tables: thesis label → internal id → output files;
    - 46 experiment, dataset, criterion, label and build rows (thesis label → internal code → "used in" → vocabulary row);
    - 23 hypothesis rows.
  - "Used in" is found by searching each item's printed text. Nothing in it is typed by hand.
- `sim/tools/world_docs_pack.py`
  - `TH`/`IDX` now print thesis numbers ("thesis Table 7.1 (Experiment 1A row)…").
  - The note is new, and the status/flown/caption strings use the experiment names.
  - The `write_index()` note marker accepts the old and the new note, so it is idempotent.
  - Its assert now rejects any internal F/T/A id in the world index.
- `docs/thesis/world_images/index.md` (the hand-written parts): status cells, and the method lines in sections 2–4. The bare T/L/O/H and "Phase 3" are now experiment names.

**Numbering scheme:** by chapter, as in vocabulary §6:

| internal id | thesis number |
|---|---|
| F2 | Figure 4.1 |
| T2 / T3 / T4 | Table 4.1 / 4.2 / 4.3 |
| F5 / F7 / F6 | Figure 5.1 / 5.2 / 5.3 |
| T6 / T8 | Table 5.1 / 5.2 |
| T5 | Table 6.1 |
| T1 / T7 | Table 7.1 / 7.2 |
| A1–A3 | Table A.1–A.3 |

**The files were NOT renamed.** §6 says "The repository files keep their names. Only the printed captions take the new numbers." The output file list is identical to before; A2 still has 3 pages, after a column-width rebalance. The LaTeX `\label{tab:Tn}` keys also keep the internal ids.

**Main renames:**

| internal | thesis wording |
|---|---|
| Experiment T / L / O / H | Experiment 2 (known tags) / 3 (loop closure) / 4 (outdoor–indoor) / 5 (tag hold); 1A, 1B, 1C, 5S |
| H-T1…P-T4 | H2.1–H2.4 |
| H-L1…P-L4, V-L | H3.1–H3.4, V3 |
| H-O1…P-O3 | H4.1–H4.3 |
| H-H2, P-H3, H-H4 (15 s / 5 s), P-H5, P-H7 | H5.2, H5.3, H5.4a/b, H5.5, H5.7 |
| C0 | C1.a |
| F1 | H1.4 (robust-weighting test) |
| r4–r10 test | H1.1 |
| Phase 3 | H1.2 |
| B1–B5 | mission completion, cross-track / heading-error / lateral-speed / oscillation bounds ("all five closed-loop criteria") |
| +S2 | estimator-validity criterion |
| S-A1–S-A4 | attitude criterion / position-lost declaration / safe landing / single landing |
| safety (a) PARAM / (b) KILL | forced-invalid / node-kill test |
| v1/v2/v3/v4 | earlier build / final UKF port / final FGO node / ablation build / corrected-priors node |
| OLD/NEW priors | original / corrected priors |
| S1/S1 far/S2/S2v2/S3/S3v2 | EKF3-, UKF-, FGO-flying hold sets (near/far spawn; earlier/final/ablation build) |
| RTS-UKF | smoothed UKF |
| FGO batch | FGO whole-flight batch |
| LC/no-LC | with/without loop closure |
| FGO_hard/UKF_hard/FGO_robust | hard-gated FGO / hard-gated UKF / robust FGO |
| dsn/fwdc/fwdplainc/p1c | standard-sensor dataset / textured-wall / plain-wall camera dataset / camera calibration flights |
| evo -a (cruise) | cruise ATE |
| Python/C++ bridge | Python/C++ heading node |
| shadow | passive estimator (world pack) |

## Verification

**Cross-check: 129/129 exact**, unchanged in count. Every computed and expected string in the index is byte-identical to the
committed version; only the labels changed.

**Numeric-token diff.** Scope:
- 69 units: every table `.md`/`.tex`, every per-figure and appendix `.pdf`, the combined PDF per item and its cover, the worlds PDF per page, the world index and the shots table;
- the figure index's 15 caption, computed and expected sets.

The new labels (Figure/Table n.m, Experiment n) were stripped before tokenising. **No data value changed.** The only token differences are label numerals:
- "Phase 3" / "Phase 5" removed: T2 `.md`/`.tex`, the combined T2 page, the T2 index caption, and 2 in the world index;
- the chapter key "4 / 5 / 6 / 7" added on the combined-PDF cover;
- "§6" / "§1" (vocabulary sections) in the new world-index note.

The scripts are in the session scratchpad (`numdiff.py`, `idxdiff.py`, `resid.py`) and are not committed.

## Residual internal-code hits (grep of every regenerated output, PDFs via pdftotext), each with its reason

| where | hits | reason |
|---|---|---|
| captions, titles, headers, cells, notes in tables / figures / both PDFs | **0** for Experiment [THOL], P-/H-codes, S-A*, C0, F1–F4, B*, G*, v1–v4, RTS-UKF, OLD/NEW | — |
| `condition A–D`: Figure 5.1 x-label, its caption (combined PDF), Table 5.2 rows (`.md`/`.tex`) | 1 + 2 + 4 + 4 | **kept by the vocabulary** (§8.1 row 29, §10 row 21 "condition A–D … adopted unchanged"). The tag counts (8 / 4 / 2 / 1 tags) are printed beside the letters |
| each table `.md` (HTML comment) and `.tex` (`%` comment + `\label{tab:Tn}`) | 1 / 2 each | non-printing; the internal id is kept for traceability |
| figure index: appendix mapping section | ~70 | intended: thesis label → internal code |
| figure index: Inputs, numbers.md-rows and check-source columns | ~90 | the data statement; they quote the record's own codes (e.g. "numbers.md §16.1 P-T3") so each value can be found. Vocabulary §8.2 puts sources here |
| figure index: the T7 check's computed/expected text `- **S-A4:** not applicable (an (a) run).` | 8 | a verbatim METHODOLOGY quote checked at build time; changing it would break the check. Table 7.2's note now paraphrases it |
| figure index: section headings "(internal F5, figure)", summary-table id column, preamble and revision history (F1/F3/F4/F8 → tables) | ~35 | intended traceability |
| world index: `dsn` / `fwdc` / `fwdplainc` in the "flown in it" and "reported in" cells and the onboard table | 18 | appendix world table beside trial names (vocabulary §8.2 rows 16, 18, 20 keep trial and world names there) |
| worlds PDF | **0** | — |

## Vocabulary gaps and ambiguities: listed, not resolved

1. **Phase 5 decomposition** (heading-driven cross-track).
   - The vocabulary names the Phase 5 *prediction* (H1.3) but not the decomposition analysis.
   - It is written in plain words: "a decomposition of the cross-track"; "from the analysis of the heading-fusion prediction (H1.3)".
2. **Blank-floor results.**
   - The blank-floor flights pool 1A (`dsn`) with 1B-side datasets (`p1c`, `fwdc`, `fwdplainc`). The vocabulary assigns blank-floor results to no sub-study.
   - The Table 7.1 row reads "Experiment 1: blank floor".
3. **"thesis-nav"** (EKF3 has no thesis-nav position-lost path) has no vocabulary name and is kept.
4. **Safety *run* labels.**
   - The labels "v2/v3" (UKF) and "v3/v4" (FGO) are run versions, not build names. UKF v2 and v3 are both the final UKF port; FGO v4 is the corrected-priors node.
   - They are written as "final UKF port" / "final UKF port, re-test (FINAL)" / "corrected-priors node, re-test (FINAL)". The mapping is a choice, not a vocabulary term.
5. **FGO forced-invalid test.**
   - Per the term 46 note, the FGO's forced-invalid test is also a node kill.
   - Stated in the Table 7.2 and Table A.2 notes. Column header: "forced-invalid test (FGO: node kill)".
6. **Hold-set stage codes.**
   - Vocabulary §8.1 row 18 writes the stages as "characterisation (S0a)" etc. It is ambiguous whether the code stays in parentheses.
   - Here the stage codes were dropped from captions and cells. They are in the index mapping.
7. **Chapter plan.** It is provisional (§6, "the user's to set"). If it changes, only `TNUM` in `eval/figs_thesis.py` needs editing, and the world pack's `TH`/`IDX` follow by hand.
8. **The world pages** stay unnumbered (§6: Chapter 3 figures are "chosen when Chapter 3 is drafted").
9. **"pre-registered" and "CLOSED"** are not yet drafted in `methodology_definitions_draft.md` (vocabulary §10 row 20). This is not a rename blocker.
10. **The task's "T conditions A–D → 8 tags … 1 tag"** was not applied as a replacement, because the vocabulary keeps the letters (see the `condition A–D` row of the residual table).

## State

- **Branch:** `worktree-agent-a3fe138cb0bc4302f`, based on `fwd-camera` at `6bb231b`. One commit. **Not merged.**
- **Regenerate:**
  - `/home/makerspace/venv-evo/bin/python eval/figs_thesis.py`, then `python3 sim/tools/world_docs_pack.py`.
  - No Gazebo is needed and nothing is re-rendered.
  - The outputs carry the generator's pre-commit HEAD (`6bb231b`).
