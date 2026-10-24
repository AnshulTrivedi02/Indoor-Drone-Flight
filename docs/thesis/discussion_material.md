# Discussion material for the thesis (ruled items only)

*Created 2026-10-25. No discussion-material file existed in `docs/thesis/` before this one. Like `limitations.md`, it holds only
paragraphs a user ruling has placed in the thesis discussion. Every number is traced to its source and checked by
`docs/thesis/ablation/check_discussion.py`. "M" is `METHODOLOGY.md`.*

## 1. Exploratory attribution ablation (FGO vs UKF with heading)

**Paragraph (thesis wording, verbatim from the user's ruling):**

> An exploratory ablation reduced the FGO to a one-keyframe window and varied its iteration count. On line-textured
> walls it retained essentially all of its advantage over the UKF (retention 0.97-1.01), so the advantage is not
> explained by window length, retained history or iteration count; it lies in the remaining structural differences
> between the estimators, which were not separated. Without a heading source, however, the window did affect results
> on one flight (by about 0.4 m).

**Ruling.** The user's answer to A-Q10 on 2026-10-25 (`tier1/open_questions.md`), recorded in an appended M entry with the same date.

**Where the values live (all in `docs/thesis/ablation/ablation_numbers.md`, EXPLORATORY):**

| text | value | source |
|---|---|---|
| "retention 0.97-1.01" | R(r3) on the three line-textured (`fwdc`) bags: 1.01 / 0.97 / 0.98, giving the range 0.97–1.01 | T2 (rows `fwdc_tex_r1..r3`); P2 row ("R(r3) on `fwdc`: 1.01, 0.97, 0.98") |
| "one keyframe … iteration count" | rungs r1–r3: one keyframe (window 0.01 s), LM cap 1 / 2 / 100; cap 100 means convergence was not confirmed, because iteration counts are not logged | pre-registration (`ablation/preregistration.md`) |
| "on one flight (by about 0.4 m)" | no-heading control on `fwdplainc_tex_r3`: Δ −0.399 / −0.365 / −0.403 m at r1 / r2 / r3, beyond its 0.223 m band. This is P1's failure (5/6 at each rung) | P1 rows r1–r3 |

**Scope note (coordinator, 2026-10-25; the paragraph itself is unchanged).**
- "On one flight" is the one flight where the change exceeded the pre-registered noise band, which is P1's failure.
- The window also moved the no-heading control on `fwdc_tex_r2`: by +0.304 / +0.300 / +0.300 m at one keyframe (r1–r3), and by −0.758 / −1.283 m at 1 s and 2 s (r4 / r5).
  - These changes count as P1 passes only because that bag's band is 2.282 m, the pre-registered "weak test".
  - At 1 s and at 2 s the FGO moves from behind the UKF to ahead of it on that bag (FGO 2.262 → 1.504 / 0.979 m, against the stored UKF 1.783 m).
- Source: `ablation_numbers.md` control table, row `fwdc_tex_r2`.
- This note is raised with the user as a wording question.

**Labels.** Exploratory. Simulation only; n = 3 per wall type; deterministic replays; checkerboard floor only; the plain-wall
heading failed its Phase 3 validation. Not in `numbers.md`, which is content-frozen.
