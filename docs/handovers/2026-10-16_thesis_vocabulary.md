# Handover 2026-10-16: thesis vocabulary, methodology definitions draft, PENDING list

**Stage:** one stage, read-only with respect to the project. **No file was renamed or edited.** Three new files and this
handover were created:

- **`docs/thesis/thesis_vocabulary.md`** is the reduced set of names for the thesis text. It contains:
  - the experiment numbering 1–5 and the placement decisions;
  - the hypotheses numbered within each experiment, mapped to their internal codes and operative pre-registration lines;
  - criteria named in words;
  - figure and table numbering by chapter, with a provisional chapter plan;
  - 34 abbreviations, each marked as either repo-sourced or "standard expansion, not in the repo";
  - an appendix mapping table;
  - the inventory of internal codes in thesis-facing material;
  - 22 departures from `glossary_flags.md` §c, each with its reason.
- **`docs/thesis/methodology_definitions_draft.md`** (DRAFT) gives one-paragraph definitions of: as worded, post hoc,
  descriptive, confirmatory, exploratory, withdrawn, and PENDING. Each cites the rulings that used the term and states where
  usage varied.
- **`docs/thesis/pending_items.md`** has three tiers:
  - Tier 1: 4 literal PENDING items (14 locations);
  - Tier 2: 7 OPEN, NOT RESTATED or flagged thesis-facing items;
  - 6 excluded superseded locations.

## Decisions taken (for the user to confirm)

- **Experiment 1 (corridor)** includes three parts:
  - 1A, the standard-sensor comparison;
  - 1B, the camera-heading studies (Phase 3–5, F tests, plan step 2);
  - 1C, the closed-loop corridor flights.
- **The safety tests are Experiment 5S** (flown in the H configuration; tabulated with H in Appendix A2). They carry
  criteria, not hypotheses.
- **Real-flight readiness is unnumbered.** It gets a closing chapter, "Towards real flights": no results, simulation is
  frozen (M:13396-13399).
- **Order:** 2 T, 3 L, 4 O, 5 H, as instructed.
- **No D-numbers in the thesis text.** Rulings are described by their content.
- **Figures and tables are numbered by chapter.**

## Counts

| item | count |
|---|---|
| vocabulary terms | 47 (≤ 50) |
| methodological labels | 7 |
| hypothesis labels | 32, plus C1.a, X1.b and V3 |
| abbreviations | 34 |
| code families in thesis-facing material, none with a thesis name in the repo | 66 |
| — of these, named by the vocabulary | 41 |
| — of these, left unnamed on purpose (file names, JSON keys, hashes, trial names, ruling/claim numbers; to be removed from captions) | 25 |

## Top rulings needed

1. Experiment H comparative criteria (H-H2/P-H3/H-H4) on the re-flown sets (numbers.md §17.2).
2. Scale-cause check "5a", never defined.
3. The last-digit rounding rule (numbers.md:741).
4. The rung-1 first-leg length (supervisor's room size; real-flight chapter only).

Also: whether "confirmatory" covers only H1.1, and which safety runs are "final" (v2/v3 in numbers.md, against v3/v4 in
T7/A2).

## Limits

- **The code inventory is a token sweep, not a full reading.**
  - Covered: the table markdown, the figure index captions and checks, both PDFs (text, by page), the cited numbers.md
    sections, and the figure and appendix images (read visually).
  - The `.tex` table files were not swept separately, because they mirror the `.md` files.
- **"Standard expansion, not in the repo" rests on a grep.** It covered CLAUDE.md, METHODOLOGY.md, FGO_DESIGN.md, `docs/`,
  `src/` and `eval/`, for each long form.
- **"pre-registered" and "CLOSED" are not drafted in the definitions file.** They were outside this stage's list, and they
  are the next to add.

## Next stage (suggested, a fresh agent)

1. The user rules on the open choices in the three files.
2. Then a caption-rewrite stage regenerates the thesis figures and tables with the new numbers and names. It would:
   - apply "half real-time factor";
   - drop the D-numbers, claim numbers and ruling numbers from captions;
   - regenerate `worlds_combined.pdf` with the current figure numbers.
