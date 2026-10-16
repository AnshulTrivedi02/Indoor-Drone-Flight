# Handover 2026-10-16: the three mismatched rows, thesis-facing provenance, and the numbers.md content-freeze

**Stage:** one stage, applying METHODOLOGY "RULINGS (user, 2026-10-16): the three mismatched numbers.md rows;
thesis-facing untraceable values; numbers.md CONTENT-FROZEN".
- **Nothing was recomputed.** Stored values were read, and min/max/differences were taken over them.
- **Not touched:** METHODOLOGY, the result files and the frozen pack.
- **Branch:** `worktree-agent-ae768afcb39bfafb6`. It was created from the unrelated `main` root and was reset to
  `fwd-camera` `8e5d116` first.

## 1. The three rows: the same quantity in all three cases, so each was corrected to its stored value

Each row was edited in place on its own line, so the change is line-neutral. Each old row is kept verbatim in a new
block, "Superseded by the ruling of 2026-10-16 (the three mismatched rows)". That block sits after the rounding block
and before the provenance record. Each entry gives the reason "transcription corrected (ruling 2026-10-16)", explains
why the quantity is the same, and names the METHODOLOGY line where the sentence originated.

| line | was | now | same quantity because | origin of the wrong text |
|---|---|---|---|---|
| 522 (§16.1) | "repeats agree within 8 mm" | the max − min of the 3 repeats' RMSE over every track: A–C ≤ 9.1 mm (C UKF live); D ≤ 18.6 mm (FGO live 18.6, EKF3 live 16.9) | "Agree within" is the repeat range of `horiz_err_m.rmse` (json:expT/T_*_r*.json), every condition and every track: the same metric, flights and statistic. 3 of the 20 condition–track pairs exceed 8 mm | METHODOLOGY.md:10279. It was written on the pre-re-run table at :10240–10253, whose own D EKF3 values (0.093 / 0.106 / 0.089) already span 17 mm. EKF3 is unchanged by the re-runs, so 8 mm never held |
| 565 (§16.2) | "OFF + 4.3 s and ON + 4.4 s" | OFF + 4.3–4.4 s (4.37 / 4.37 / 4.34) and ON + 4.3 s (4.32 / 4.32 / 4.28) | Both are the time of the `XKFS.SS` change after the marker. `eval/o_score.py` stores it as `ekf3.source_set_changes`, in bag time, as are `markers_bag_s`; the 3 flights are O_r1 / O_r2 / O_r3b | METHODOLOGY.md:10402 transposed the two. The `o_check1` disclosure at :10372 has OFF 4.4 / ON 4.3 |
| 647 (§17.1 S3) | "EKF3 shadow 10–20" | "EKF3 shadow 6–20" (`drift_end_m`, all 12 losses) | It is the end-of-loss metric that §17.1 names, over 4 losses × 3 flights. The S2v2 cell "3–28" reproduces under exactly this convention (3.3–27.6). Stored: 6.3–20.1 (effective 5.1–18.9) | METHODOLOGY.md:12221; how its lower bound 10 arose is not recorded |

- **`posTimeout` 92 % on l.565** was checked as well. The stored value is 0.9179, and the row is unchanged.
- **Reliance on "8 mm" (task 1, l.522): none.** A search for "8 mm", "0.8 cm", "0.008", "agree within", "repeat",
  "4.3 s", "4.4 s", "source set", "10–20" and "EKF3 shadow" found no hits for any of the three rows. The search
  covered:
  - `eval/figs_thesis.py`;
  - the thesis-facing material: figures index and captions, T1–T8 `.md`, the combined-PDF text, the claims table, the
    vocabulary, the methodology and limitations drafts, `pending_items.md` and the world-images index.

  The only "repeat" hits are unrelated: "mean of 3 repeats" in the T8 caption (`figs_thesis.py:1231`), and vocabulary
  wording. `headline_claims_before_after.md:41` carries "EKF3 3–11 mm" at 30 s for S1, which is a different quantity.
  **No figs_thesis check reads any of the three rows** (its expected strings are hard-coded), so the check count
  could not move.

## 2. Thesis-facing untraceable values: `docs/thesis/thesis_values_provenance.md`

- **Method.** All numerals in the thesis-facing material were paired, by digit string and surrounding words, with the
  769 class-U tokens (`cmp_s1–s4.tsv`). The pairs were then reviewed by hand, by quantity. Most pairs were coincidences:
  repeat indices, run numbers, and `rd()` table cells.
  - Scratch: `tf2.py`, `tf2_dump.py`, `compact.py`, `tf2_strong.txt` and `weak_c.txt`.
- **Result: 43 quantities.**

  | written source | quantities |
  |---|---|
  | a results file, METHODOLOGY line, pre-registration line or parameter file | 41 |
  | **CLAUDE.md only** (not a ruled source type) | 1: the measured transition crossing y = 80.01 m, `world_images/index.md:24` → `CLAUDE.md:1827` |
  | **no written source at all** | 0 |
  | **flagged** (its source contradicts the wording) | 1: `pending_items.md:17` says "all 126 inputs written ≤ …", but `docs/handovers/2026-10-16_phase5_provenance_rounding.md:27` records that timing as inaccurate. pending_items is a dated record, so it was not edited |

- **Read from a results file at the first-final-re-run commit `425e824`:** three historical "was" values.
  - 838–1,014° yaw RMS. The 43 m was not re-read.
  - L no-LC 0.281–0.362 m.
  - FGO SD 1.23.
- **Limits:**
  - pairing works on digit strings, so a value written with other digits could be missed;
  - thesis numerals that match no numbers.md token are out of the ruled scope (the 769) and were not chased. These are
    mostly criterion bounds in the vocabulary.

## 3. numbers.md CONTENT-FROZEN

- **Notice:** a bold prefix on line 3, so no cited line moved. It reads: "CONTENT-FROZEN 2026-10-16 (user ruling): no
  in-place edits; any change is a dated erratum entry in the Errata section at the end." It also gives the frozen
  commit and the check command.
- **Errata section:** at the end of the file, with the entry format and "(No entries yet.)".
- **Line shifts:** none at or before line 1295. The highest numbers.md line cited by any doc is 1017. The provenance
  record moved down 14 lines; it is cited by name only.
- **Check:** `tools/check_numbers_frozen.py`, standalone, so the figs_thesis tally stays at 129.
  - It hashes everything above `## Errata` (sha256 `6a77b9ab…`), with the frozen-commit token in the notice masked.
  - It fails if the hash changes or if `## Errata` is missing or duplicated.
  - The git SHA in the notice is provenance only. If the commit is not found (e.g. after a squash merge), the check
    warns and does not fail.
  - Self-test on temp copies (`selftest.py`): unchanged → pass; a one-character change at l.522 → FAIL; an erratum
    appended → pass; the SHA filled in → pass; Errata missing → FAIL; Errata duplicated → FAIL.
- **Frozen commit:** the first commit of this stage. Its SHA was then written into the notice in a second commit,
  which the hash ignores by design.

## 4. Exact cross-check: 129/129

`eval/figs_thesis.py` was re-run after the edits and gave **129/129**. The regenerated `index.md`, the tables and the
PDFs differed from `8e5d116` only in the "generated … (commit …)" stamps and in PDF metadata. They were **reverted and
not committed**, so that this stage changes no thesis output.

## For the user

- **Row 2 of the provenance list (y = 80.01 m) has only `CLAUDE.md` as its source.** The options are:
  - accept CLAUDE.md:1827 as the citation;
  - write the design value y = 80 m in the world index.
- **`pending_items.md:17` "all 126 inputs written ≤ …"** is contradicted by the provenance handover. It is left as a
  dated record unless you rule otherwise.
- **From now on, any numbers.md change is an Errata entry.** Run `python3 tools/check_numbers_frozen.py` before
  committing.
