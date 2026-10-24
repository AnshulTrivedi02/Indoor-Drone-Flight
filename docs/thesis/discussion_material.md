# Discussion material for the thesis (ruled items only)

*Created 2026-10-25. No discussion-material file existed in `docs/thesis/` before this one. Like `limitations.md`, it holds only
paragraphs a user ruling has placed in the thesis discussion. Every number is traced to its source and checked by
`docs/thesis/ablation/check_discussion.py`. "M" is `METHODOLOGY.md`.*

## 1. Exploratory attribution ablation (FGO vs UKF with heading)

**Paragraph (thesis wording, verbatim from the user's rulings; the last sentence is the user's correction of 2026-10-25, A-Q12):**

> An exploratory ablation reduced the FGO to a one-keyframe window and varied its iteration count. On line-textured
> walls it retained essentially all of its advantage over the UKF (retention 0.97-1.01), so the advantage is not
> explained by window length, retained history or iteration count; it lies in the remaining structural differences
> between the estimators, which were not separated. Without a heading source, however, the window did affect results:
> beyond the noise band on one flight (by about 0.4 m), and by up to 1.3 m on another, within that flight's wide noise
> band.

**Ruling.** The user's answer to A-Q10 on 2026-10-25, with the last sentence corrected by the user's A-Q12 ruling the same day: it replaces "the window did affect results on one flight (by about 0.4 m)" (`tier1/open_questions.md`; appended M entries of 2026-10-25).

**Where the values live (all in `docs/thesis/ablation/ablation_numbers.md`, EXPLORATORY):**

| text | value | source |
|---|---|---|
| "retention 0.97-1.01" | R(r3) on the three line-textured (`fwdc`) bags: 1.01 / 0.97 / 0.98, giving the range 0.97–1.01 | T2 (rows `fwdc_tex_r1..r3`); P2 row ("R(r3) on `fwdc`: 1.01, 0.97, 0.98") |
| "one keyframe … iteration count" | rungs r1–r3: one keyframe (window 0.01 s), LM cap 1 / 2 / 100; cap 100 means convergence was not confirmed, because iteration counts are not logged | pre-registration (`ablation/preregistration.md`) |
| "beyond the noise band on one flight (by about 0.4 m)" | no-heading control on `fwdplainc_tex_r3`: Δ −0.399 / −0.365 / −0.403 m at r1 / r2 / r3, beyond its 0.223 m band. This is P1's failure (5/6 at each rung) | P1 rows r1–r3 |
| "by up to 1.3 m on another, within that flight's wide noise band" | no-heading control on `fwdc_tex_r2`: Δ +0.304 / +0.300 / +0.300 / −0.758 / −1.283 m at r1–r5; the largest, 1.283 m (r5, 2 s), rounds to 1.3 m. All are within that bag's 2.282 m band, the pre-registered weak test. At 1 s and 2 s the FGO moves from behind the stored UKF to ahead of it (2.262 → 1.504 / 0.979 m, against 1.783 m) | T3 (control) row `fwdc_tex_r2` |

**Labels.** Exploratory. Simulation only; n = 3 per wall type; deterministic replays; checkerboard floor only; the plain-wall
heading failed its Phase 3 validation. Not in `numbers.md`, which is content-frozen.
