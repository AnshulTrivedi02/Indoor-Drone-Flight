# Tier-1 extension experiments: open questions for the user

These are non-blocking questions collected under the standing decision rules (2026-10-23). They go into the morning
digest. Each one says what is being done meanwhile. STOP items, if any, are listed first and marked **STOP**.

| # | raised (AEDT) | question | default being followed meanwhile | blocks anything? |
|---|---|---|---|---|
| Q1 | 2026-10-23 10:35 | Convert the main thesis tables (T1–T8, R1, R2, R4, methods tables) from cm/mm/ms to SI as well? Plots and the walkthrough are already SI (merge 8249802). | Tables stay in their original units, matching the frozen numbers.md. | no |

**Answered:**
- **Q1 (user, 2026-10-23):** yes. Thesis tables use SI units, converted at generation time only; numbers.md stays exactly as is. Use one unit per quantity, the same in a table as in its matching figure. SI prefixes are fine where they read better (e.g. drift in mm, position error in m): pick the readable unit and use it consistently. Keep the exact cross-check against the stored values. → being implemented (units pass).
