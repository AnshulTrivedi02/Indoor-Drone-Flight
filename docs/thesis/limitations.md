# Limitations list for the thesis (ruled items only)

*Created 2026-10-16. No limitations list existed in `docs/thesis/` before this file, so it was created. It lists only items
that a user ruling has explicitly placed in the thesis as a limitation or an unanswered question. Nothing unruled is added
here. "M" is `METHODOLOGY.md`, followed by its line number.*

| # | limitation (thesis wording) | ruling | where the value lives |
|---|---|---|---|
| 1 | **Cause of EKF3's residual along-track scale (0.97–0.98) not investigated.** The scale-cause check ("bounded check 5a") was never defined and is DROPPED; the scale itself is reported, its cause is not | M:14182-14183 (RULINGS 2026-10-16, item 2) | `numbers.md` §6.5 (distance scale) and flags, resolved 4; claim 12 (`headline_claims_before_after.md`) |
| 2 | **Questions the partial attribution study did not answer** (the study was stopped by ruling): the `dsn_tex_r6` flip; the main corridor (r1–r3) changes; the textured-wall UKF heading gain; the textured-wall FGO baseline. The corrections were applied jointly and are not attributed individually, apart from the directly traced plain-wall case and the O partial attribution | M:13300-13304 ("NOT answered by the partial study (listed in the thesis)") | `numbers.md` §18 (row "NOT answered by the partial study") |
