# Tier-1 extension experiments: open questions for the user

These are non-blocking questions collected under the standing decision rules (2026-10-23). They go into the morning
digest. Each one says what is being done meanwhile. STOP items, if any, are listed first and marked **STOP**.

| # | raised (AEDT) | question | default being followed meanwhile | blocks anything? |
|---|---|---|---|---|
| Q1 | 2026-10-23 10:35 | Convert the main thesis tables (T1–T8, R1, R2, R4, methods tables) from cm/mm/ms to SI as well? Plots and the walkthrough are already SI (merge 8249802). | Tables stay in their original units, matching the frozen numbers.md. | no |
| Q2 | 2026-10-24 04:55 | claims_update.md C4: should the "0.25 s is the largest window meeting the 33 ms budget" wording (`methodology_factsheets/3.3_estimators.md:66`; M:708-709, :720-721) be scoped to the corridor sweep (DIAGNOSTIC, pre-thread-fix)? On the room world (E4, serial, post-fix), 0.5 s also fitted the budget on 12/12 flights (descriptive under P-E4.2). | Proposal only; nothing edited. The proposed wording in claims_update.md C4 scopes it. | no |
| Q3 | 2026-10-24 04:55 | claims_update.md C2: add a ruled limitation "loop closure assumes correct re-identification; the plain keyframe FGO is not robust to 1% wrong ids (H-E3.1 FAIL 0/9)" to `limitations.md`, which lists ruled items only? | Not added. | no |

**Answered:**
- **Q1 (user, 2026-10-23):** yes. Thesis tables use SI units, converted at generation time only; numbers.md stays exactly as is. Use one unit per quantity, the same in a table as in its matching figure. SI prefixes are fine where they read better (e.g. drift in mm, position error in m): pick the readable unit and use it consistently. Keep the exact cross-check against the stored values. → being implemented (units pass).
