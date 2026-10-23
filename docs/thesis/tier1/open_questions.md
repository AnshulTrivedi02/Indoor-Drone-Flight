# Tier-1 extension experiments: open questions for the user

These are non-blocking questions collected under the standing decision rules (2026-10-23). They go into the morning
digest. Each one says what is being done meanwhile. STOP items, if any, are listed first and marked **STOP**.

| # | raised (AEDT) | question | default being followed meanwhile | blocks anything? |
|---|---|---|---|---|

**Answered:**
- **Q1 (user, 2026-10-23):** yes. Thesis tables use SI units, converted at generation time only; numbers.md stays exactly as is. Use one unit per quantity, the same in a table as in its matching figure. SI prefixes are fine where they read better (e.g. drift in mm, position error in m): pick the readable unit and use it consistently. Keep the exact cross-check against the stored values. → done: units pass merged 2026-10-23 (2dcee76); decisions D7, D8.
- **Q2 (user, 2026-10-24):** "scope the claim: "In the corridor configuration, 0.25 s was the largest window within the 33 ms budget; on the tag-room flights 0.5 s also fitted (27-28 ms)." No general claim." → done: `methodology_factsheets/3.3_estimators.md` (en dash, D20); see `claims_applied.md`.
- **Q3 (user, 2026-10-24):** add to limitations.md: "The FGO as configured (plain least squares, tag readings ungated) is not robust to wrong tag IDs: at 1% wrong IDs, 6 of 9 runs diverged and the remaining 3 ended 51-85x the clean error (H-E3.1 FAIL, 0/9). A robust-weighted variant avoided divergence in all 21 runs, though one collapsed. The landmark UKF (E5) was not tested with wrong IDs." → done verbatim as limitation 3, with a scope note: 51–85× is the range over all 12 non-diverged plain runs (1% and 5%); the 3 at 1% are 51.26–75.23× (D19).
- **C1–C5 (user, 2026-10-24):** "accepted as proposed. Apply to the thesis files at the listed lines; the existing claims table and frozen documents are not edited (apply to thesis-facing outputs only, with a mapping note)." → done: `claims_applied.md`.
- **D17 / claims_update open point 4 (user, 2026-10-24):** the T1 Experiment 3 UKF cell names the variant: "UKF with landmark states (extension E5): bounded; ~2x FGO error", footnoted [k] as an extension variant, not the UKF used elsewhere (measured 1.76–2.08×, LC live, descriptive) → done.
- **D16 (claims_update open point 1):** accepted with C2 as proposed (no claim that the robust arm keeps the loop-closure advantage).
- No further experiment stages are planned (user, 2026-10-24).
- **Q4 (user, 2026-10-24):** yes: limitations.md item 3 now reads "51-75x" (the 3 non-diverged 1% runs: 51.26, 65.59, 75.23); the scope note keeps 51.26–85.49× for all 12 non-diverged runs at 1% and 5%. Searched all thesis-facing material for "51-85"/"51–85": limitations.md item 3 was the only instance describing only the 1% runs (see claims_applied.md §Q4). check_claims_update.py pinned to 181f156.
