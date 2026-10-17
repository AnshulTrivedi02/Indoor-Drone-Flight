# Handover, 2026-10-17: methodology fact sheets (§3.1–3.8)

**What was done**
- Nine new files were written in `docs/thesis/methodology_factsheets/`: the eight section sheets `3.1_…` to `3.8_…`, and
  `README.md` (the index, the counts, the missing numbers and the key flags).
- No existing file was edited. The worktree branch was first reset to `fwd-camera` `337c931`.
- Every line number refers to `337c931`.

**Counts.** These are counted by script. Totals: 282 facts, 91 appendix candidates, 78 (a) flags and 51 (b) flags, which
is 502 bullets. The per-section counts are in the README.

**Method**
- Five parallel forks wrote the sheets, one or two sections each, to fixed conventions:
  - four headings only;
  - numbers only from numbers.md, cited by its line in this worktree;
  - the tag `[NOT IN numbers.md: …]` for anything missing.
- Checks run afterwards:
  - **Bullet counts and headings.** These were checked by script.
  - **Numbers against their cited lines.** A digit-string check matched each bullet's numbers against its cited numbers.md
    lines: 187 decimals in total.
    - The genuine misses were fixed with a tag or a corrected line. There were six, in 3.3 and 3.8.
    - The rest are context: the CLAUDE.md side of a conflict, or hypothesis labels such as "H5.4".
  - **Freeze check.** `tools/check_numbers_frozen.py` returned PASS.

**Open for the user, from the flags**
- **`LOG_REPLAY`.** numbers.md:409 conflicts with `consolidated_rerun.parm`. numbers.md is frozen, so this would need an
  erratum if ruled.
- **S-A2 bound for the UKF forced-invalid test.** It was pre-registered at 0.1 s and scored at 0.75 s, and no amendment was
  found.
- **Tag-hold hypotheses.** H5.1, H5.2–H5.4 and H5.5 have competing or design-draft-only wordings. These were left
  unresolved, as instructed.
- **FGO_DESIGN.md:529-541.** It still calls `biasAccOmegaInt` "matched".
- **Stale CLAUDE.md lines:** "GTSAM planned", "FGO 4.65 vs EKF3 4.66", "320 s cruise", and the manual launch chain without
  `consolidated_rerun.parm`.
- **thesis_values_provenance.md rows 21 and 42.** They are now slightly stale: the line for the UKF's 5 s timeout, and the
  "126 inputs" wording in pending_items.
- **Criterion bounds.** These are expected to be absent from numbers.md (the README lists them). The user should decide
  whether the thesis may cite METHODOLOGY's pre-registration lines directly for bounds.

**Not done:** no chapter prose was written, nothing was merged, and the vocabulary and definitions files were not touched,
because other agents are editing them.
